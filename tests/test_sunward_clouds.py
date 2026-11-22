"""Validate time, bearing, directional data completeness and downside-only scoring."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import Mock

import requests

from modules.cloud_forecast import CloudForecastClient, FIELDS, select_cloud_forecast
from modules.prediction_quality import assess_prediction_quality
from modules.prediction_response import PredictionResponseBuilder
from modules.sunward_clouds import SunwardCloudService, destination, solar_position, sunward_multiplier
from modules.weather_inputs import WeatherInputService
from modules.weather_presentation import build_weather_presentation


HK = timezone(timedelta(hours=8))
TARGET = datetime(2026, 11, 18, 17, 30, tzinfo=HK)
NOW = TARGET - timedelta(hours=3)


def model(low=60):
    return {'properties': {'meta': {'updated_at': (NOW - timedelta(hours=2)).isoformat(),
                                     'units': {field: '%' for field in FIELDS.values()}},
                           'timeseries': [
        {'time': (TARGET.replace(minute=0) + timedelta(hours=i)).isoformat(),
         'data': {'instant': {'details': dict(zip(FIELDS.values(), [max(60, low), low, 40, 60]))}}}
        for i in (0, 1)]}}


def service(low=60, position=None):
    factory = Mock(side_effect=lambda *_: Mock(fetch=Mock(return_value=model(low))))
    return SunwardCloudService(factory, position=position or Mock(return_value={
        'azimuth_deg': 249.7, 'elevation_deg': 1.0})), factory


class GeometryTests(unittest.TestCase):
    def test_sunrise_and_sunset_have_seasonal_bearings_and_respect_timezones(self):
        dawn = datetime(2026, 11, 18, 6, 38, tzinfo=HK)
        dusk = datetime(2026, 11, 18, 17, 39, tzinfo=HK)
        self.assertTrue(100 < solar_position(dawn)['azimuth_deg'] < 120)
        self.assertTrue(240 < solar_position(dusk)['azimuth_deg'] < 260)
        self.assertTrue(-2 < solar_position(dawn)['elevation_deg'] < 2)
        for key in ('azimuth_deg', 'elevation_deg'):
            self.assertAlmostEqual(solar_position(dawn)[key], solar_position(dawn.astimezone(timezone.utc))[key], places=9)
        summer = solar_position(datetime(2026, 6, 21, 19, 0, tzinfo=HK))
        self.assertGreater(summer['azimuth_deg'], solar_position(dusk)['azimuth_deg'] + 30)

    def test_destinations_have_known_equatorial_offsets_and_wrap_longitude(self):
        north = destination(0, 0, 0, 100)
        east = destination(0, 0, 90, 100)
        self.assertAlmostEqual(north[0], .8993, places=4)
        self.assertAlmostEqual(north[1], 0, places=4)
        self.assertAlmostEqual(east[0], 0, places=4)
        self.assertAlmostEqual(east[1], .8993, places=4)
        self.assertLess(destination(0, 179.9, 90, 100)[1], -179)


class DirectionalDataTests(unittest.TestCase):
    def test_two_sunward_points_use_target_time_and_actual_coordinates(self):
        position = Mock(return_value={'azimuth_deg': 249.7, 'elevation_deg': 1.0})
        provider, factory = service(position=position)
        result = provider.assess(TARGET, NOW)
        position.assert_called_once_with(TARGET)
        self.assertEqual(result['status'], 'available')
        self.assertEqual(result['sampling_bearing_deg'], 250)
        self.assertEqual(result['azimuth_deg'], 249.7)
        self.assertEqual([sample['distance_km'] for sample in result['samples']], [50, 100])
        self.assertEqual(factory.call_count, 2)
        for sample in result['samples']:
            cloud = sample['cloud_forecast']
            self.assertLess(sample['longitude'], 114.17)
            self.assertEqual(cloud['valid_at'], TARGET.isoformat())
            self.assertEqual(cloud['latitude'], sample['latitude'])
            self.assertEqual(cloud['longitude'], sample['longitude'])
            self.assertIn(f"lat={sample['latitude']:.4f}", cloud['source_url'])

    def test_nearby_bearings_reuse_cached_clients_and_north_wraps(self):
        position = Mock(side_effect=[{'azimuth_deg': 249, 'elevation_deg': 0},
                                     {'azimuth_deg': 251, 'elevation_deg': 0},
                                     {'azimuth_deg': 359, 'elevation_deg': 0}])
        provider, factory = service(position=position)
        provider.assess(TARGET, NOW)
        provider.assess(TARGET, NOW)
        self.assertEqual(factory.call_count, 2)
        self.assertEqual(provider.assess(TARGET, NOW)['sampling_bearing_deg'], 0)
        self.assertEqual(factory.call_count, 4)

    def test_one_missing_or_stale_sample_keeps_directional_adjustment_unavailable(self):
        for second in (None, model()):
            if second:
                second['properties']['meta']['updated_at'] = (NOW - timedelta(hours=24)).isoformat()
            factory = Mock(side_effect=[Mock(fetch=Mock(return_value=model())), Mock(fetch=Mock(return_value=second))])
            provider = SunwardCloudService(factory, position=lambda _: {'azimuth_deg': 250, 'elevation_deg': 0})
            result = provider.assess(TARGET, NOW)
            self.assertEqual(result['status'], 'partial')
            self.assertIsNone(sunward_multiplier(result))
            self.assertIsNone(result['score_multiplier'])

    def test_provider_timeouts_failsoft_without_assuming_clear_sky(self):
        factory = Mock(side_effect=lambda *_: Mock(fetch=Mock(side_effect=requests.Timeout('offline'))))
        provider = SunwardCloudService(factory, position=lambda _: {'azimuth_deg': 250, 'elevation_deg': 0})
        result = provider.assess(TARGET, NOW)
        self.assertEqual(result['status'], 'unavailable')
        self.assertIsNone(result['score_multiplier'])

    def test_daytime_nighttime_and_invalid_geometry_do_not_fetch_directional_weather(self):
        for elevation in (-40, -8.001, 8.001, 70, float('nan'), None):
            provider, factory = service(position=lambda _: {'azimuth_deg': 250, 'elevation_deg': elevation})
            result = provider.assess(TARGET, NOW)
            self.assertNotEqual(result['status'], 'available')
            factory.assert_not_called()
        provider, factory = service(position=Mock(side_effect=ImportError('astral unavailable')))
        self.assertEqual(provider.assess(TARGET, NOW)['status'], 'unavailable')
        factory.assert_not_called()

    def test_spatial_http_request_uses_its_own_point_and_cache(self):
        response = Mock(status_code=200, headers={})
        response.json.return_value = model()
        session = Mock(get=Mock(return_value=response))
        client = CloudForecastClient(session, lambda: NOW, latitude=22.12345, longitude=113.67891)
        client.fetch()
        client.fetch()
        self.assertEqual(session.get.call_count, 1)
        self.assertTrue(session.get.call_args.args[0].endswith('lat=22.1234&lon=113.6789'))


class DirectionalScoreTests(unittest.TestCase):
    def test_equivalent_utc_and_hong_kong_times_can_apply_directional_adjustment(self):
        provider, _ = service()
        result = provider.assess(TARGET, NOW)
        expected = sunward_multiplier(result)
        self.assertIsNotNone(expected)
        self.assertEqual(sunward_multiplier(result, TARGET.astimezone(timezone.utc).isoformat()), expected)
        result['samples'][0]['cloud_forecast']['valid_at'] = TARGET.astimezone(timezone.utc).isoformat()
        self.assertEqual(sunward_multiplier(result, TARGET.isoformat()), expected)

    def test_valid_at_alone_cannot_hide_wrong_directional_sample_times(self):
        provider, _ = service()
        result = provider.assess(TARGET, NOW)
        result['samples'][0]['cloud_forecast']['sample_times'] = [NOW.isoformat()]
        self.assertIsNone(sunward_multiplier(result, TARGET.isoformat()))

    def test_directional_cover_can_only_reduce_cloud_points(self):
        last = 1.0
        for low in (0, 20, 50, 100):
            provider, _ = service(low)
            multiplier = sunward_multiplier(provider.assess(TARGET, NOW), TARGET.isoformat())
            self.assertLessEqual(multiplier, last)
            self.assertGreaterEqual(multiplier, .4)
            last = multiplier
        self.assertEqual(last, .4)

    def test_wrong_times_missing_layers_and_partial_payloads_never_adjust(self):
        provider, _ = service()
        original = provider.assess(TARGET, NOW)
        self.assertIsNone(sunward_multiplier(original, (TARGET + timedelta(hours=1)).isoformat()))
        for mutation in ('sample_time', 'layer', 'distance', 'missing_sample', 'night', 'missing_time'):
            result = deepcopy(original)
            if mutation == 'sample_time':
                result['samples'][0]['cloud_forecast']['valid_at'] = NOW.isoformat()
            elif mutation == 'layer':
                result['samples'][0]['cloud_forecast']['low'] = None
            elif mutation == 'distance':
                result['samples'][0]['distance_km'] = 100
            elif mutation == 'missing_sample':
                result['samples'].pop()
            elif mutation == 'night':
                result['elevation_deg'] = -30
            else:
                result['valid_at'] = None
                for sample in result['samples']:
                    sample['cloud_forecast']['valid_at'] = None
            self.assertIsNone(sunward_multiplier(result))


class DirectionalIntegrationTests(unittest.TestCase):
    def test_directional_metadata_reaches_target_and_display_without_observation_mutation(self):
        observed = {'temperature': {'data': [{'place': '香港天文台', 'value': 25}]},
                    'humidity': {'data': [{'place': '香港天文台', 'value': 60}]},
                    'rainfall': {'data': [{'max': 0}]}}
        values = {'weather': observed, 'forecast': {'forecastDesc': '多雲'}, 'ninday': {}, 'wind': {}, 'warning': {}}
        direction, _ = service()
        extractor = Mock(extract_future_weather_data=Mock(side_effect=lambda weather, *_, **kwargs: weather))
        inputs = WeatherInputService(lambda key, _: values[key], Mock(), Mock(), Mock(), Mock(), Mock(), extractor,
                                     lambda: model(0), lambda: NOW, sunward_service=direction).prepare(3)
        self.assertEqual(inputs.target_weather['sunward_cloud_forecast']['status'], 'available')
        self.assertNotIn('sunward_cloud_forecast', inputs.observed_weather)
        presentation = build_weather_presentation(inputs.target_weather, inputs.observed_weather, 3,
                                                   {'evaluated_at': TARGET.isoformat()})
        cards = {card['key']: card for card in presentation['cards']}
        self.assertEqual(cards['sunward_low_50']['value'], 60)
        self.assertEqual(cards['solar_azimuth_deg']['source_kind'], 'calculated')
        quality = assess_prediction_quality(inputs.target_weather, inputs.observed_weather, {}, 3)
        self.assertTrue(quality['score_usable'])
        self.assertTrue(any('50及100公里' in note for note in quality['limitations']))
        builder = PredictionResponseBuilder(Mock(), Mock(), lambda data: data)
        detail = builder._factor('cloud', 22.4, 35, 'sunset', 3, inputs.target_weather)
        self.assertTrue(detail['sunward_adjustment_applied'])
        self.assertEqual(detail['sunward_multiplier'], .64)

    def test_missing_central_clouds_do_not_request_directional_samples(self):
        values = {'weather': {}, 'forecast': {}, 'ninday': {}, 'wind': {}, 'warning': {}}
        direction = Mock()
        WeatherInputService(lambda key, _: values[key], Mock(), Mock(), Mock(), Mock(), Mock(), Mock(),
                            lambda: None, lambda: NOW, sunward_service=direction).prepare(0)
        direction.assess.assert_not_called()

    def test_partial_direction_stays_visible_and_preserves_base_scoring(self):
        provider, _ = service()
        direction = provider.assess(TARGET, NOW)
        direction['status'] = 'partial'
        direction['samples'][1]['cloud_forecast'] = None
        target = {'cloud_forecast': select_cloud_forecast(model(), TARGET, NOW),
                  'forecast_target_at': TARGET.isoformat(),
                  'sunward_cloud_forecast': direction}
        result = build_weather_presentation(target, {}, 3, {'evaluated_at': TARGET.isoformat()})
        cards = {card['key']: card for card in result['cards']}
        self.assertEqual(cards['sunward_low_50']['value'], 60)
        self.assertIsNone(cards['sunward_low_100']['value'])
        self.assertEqual(cards['sunward_low_100']['source_kind'], 'unavailable')
        self.assertIn('沒有當作光路暢通', result['summary'])


if __name__ == '__main__':
    unittest.main()
