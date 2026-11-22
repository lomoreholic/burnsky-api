"""Offline provider, forecast alignment, fallback and cloud scoring regression checks."""

from datetime import datetime, timedelta, timezone
from copy import deepcopy
import unittest
from unittest.mock import Mock

import requests

from modules.cloud_forecast import CloudForecastClient, FIELDS, select_cloud_forecast, score_cloud_layers
from modules.prediction_quality import assess_prediction_quality
from modules.weather_inputs import WeatherInputService
from modules.weather_presentation import build_weather_presentation


NOW = datetime(2026, 11, 18, 14, 30, tzinfo=timezone(timedelta(hours=8)))


def payload():
    return {'properties': {'meta': {'updated_at': (NOW - timedelta(hours=4)).isoformat(),
                                     'units': {field: '%' for field in FIELDS.values()}},
                           'timeseries': [
        {'time': (NOW.replace(minute=0) + timedelta(hours=i)).isoformat(),
         'data': {'instant': {'details': {field: value for field, value in zip(FIELDS.values(), [60, 10 + i * 10, 40, 60])}}}}
        for i in range(5)]}}


class CloudSelectionTests(unittest.TestCase):
    def test_cloud_units_must_be_percentage_for_every_layer(self):
        for field in FIELDS.values():
            for invalid in (None, 'fraction', 'okta', 'percent'):
                data = payload()
                data['properties']['meta']['units'][field] = invalid
                self.assertIsNone(select_cloud_forecast(data, NOW, NOW))
        data = payload()
        del data['properties']['meta']['units']
        self.assertIsNone(select_cloud_forecast(data, NOW, NOW))

    def test_duplicate_times_are_ambiguous_regardless_of_order_or_values(self):
        for duplicate_kind in ('same', 'conflicting', 'malformed'):
            data = payload()
            duplicate = deepcopy(data['properties']['timeseries'][0])
            # Equivalent UTC spelling is still a duplicate timestamp.
            duplicate['time'] = datetime.fromisoformat(duplicate['time']).astimezone(timezone.utc).isoformat()
            if duplicate_kind == 'conflicting':
                duplicate['data']['instant']['details']['cloud_area_fraction_low'] = 99
            elif duplicate_kind == 'malformed':
                duplicate['data'] = None
            for first in (True, False):
                test_data = deepcopy(data)
                test_data['properties']['timeseries'].insert(0 if first else 5, deepcopy(duplicate))
                self.assertIsNone(select_cloud_forecast(test_data, NOW, NOW))
                # Ambiguity at another hour does not invalidate this exact sample.
                self.assertIsNotNone(select_cloud_forecast(test_data, NOW.replace(minute=0) + timedelta(hours=2), NOW))

    def test_interpolation_cannot_skip_a_known_invalid_intermediate_sample(self):
        data = payload()
        data['properties']['timeseries'].append({'time': NOW.isoformat(), 'data': None})
        self.assertIsNone(select_cloud_forecast(data, NOW + timedelta(minutes=15), NOW))
        self.assertIsNotNone(select_cloud_forecast(data, NOW.replace(minute=0) + timedelta(hours=1), NOW))

    def test_three_hour_target_interpolates_real_layers_and_keeps_provenance(self):
        cloud = select_cloud_forecast(payload(), NOW + timedelta(hours=3), NOW)
        self.assertEqual(cloud['low'], 45)
        self.assertEqual(cloud['valid_at'], (NOW + timedelta(hours=3)).isoformat())
        self.assertEqual(cloud['method'], 'linear_interpolation')
        self.assertEqual(cloud['source'], 'MET Norway')
        self.assertEqual(len(cloud['sample_times']), 2)

    def test_exact_hour_does_not_require_following_record(self):
        target = NOW.replace(minute=0) + timedelta(hours=4)
        self.assertEqual(select_cloud_forecast(payload(), target, NOW)['method'], 'hourly_model')

    def test_midnight_and_utc_local_times_are_the_same_instant(self):
        data = payload()
        for entry in data['properties']['timeseries']:
            instant = datetime.fromisoformat(entry['time']) + timedelta(hours=8)
            entry['time'] = instant.astimezone(timezone.utc).isoformat()
        cloud = select_cloud_forecast(data, NOW + timedelta(hours=11), NOW)
        self.assertIsNotNone(cloud)
        self.assertTrue(cloud['valid_at'].startswith('2026-11-19T01:30'))

    def test_no_extrapolation_or_interpolation_across_missing_hours(self):
        self.assertIsNone(select_cloud_forecast(payload(), NOW - timedelta(hours=1), NOW))
        self.assertIsNone(select_cloud_forecast(payload(), NOW + timedelta(hours=5), NOW))
        data = payload()
        del data['properties']['timeseries'][1]
        self.assertIsNone(select_cloud_forecast(data, NOW, NOW))

    def test_stale_future_or_missing_model_runs_are_rejected(self):
        for updated in (None, '', 'not a date', NOW.isoformat()[:19],
                        (NOW - timedelta(hours=19)).isoformat(),
                        (NOW + timedelta(hours=1)).isoformat()):
            data = payload()
            data['properties']['meta']['updated_at'] = updated
            self.assertIsNone(select_cloud_forecast(data, NOW, NOW))

    def test_missing_invalid_layers_are_not_filled_with_zero(self):
        for value in (None, True, '50', -1, 101, float('nan'), float('inf')):
            data = payload()
            data['properties']['timeseries'][0]['data']['instant']['details']['cloud_area_fraction_low'] = value
            self.assertIsNone(select_cloud_forecast(data, NOW, NOW))
        for data in (None, [], {}, {'properties': None}, {'properties': {'meta': []}}):
            self.assertIsNone(select_cloud_forecast(data, NOW, NOW))


class CloudScoreTests(unittest.TestCase):
    def test_low_cloud_obstruction_reduces_same_middle_high_cloud_score(self):
        clear_horizon = dict(total=60, low=0, medium=40, high=60)
        blocked = dict(clear_horizon, low=90, total=100)
        self.assertGreater(score_cloud_layers(clear_horizon), score_cloud_layers(blocked))
        self.assertEqual(score_cloud_layers(clear_horizon), 35)

    def test_cloudless_and_low_cloud_only_do_not_become_ideal(self):
        self.assertEqual(score_cloud_layers(dict(total=0, low=0, medium=0, high=0)), 0)
        self.assertEqual(score_cloud_layers(dict(total=100, low=100, medium=0, high=0)), 0)

    def test_overlapping_layers_are_not_added_or_assumed_optically_thin(self):
        one = dict(total=60, low=10, medium=0, high=60)
        self.assertEqual(score_cloud_layers(one), score_cloud_layers(dict(one, medium=60)))
        self.assertLess(score_cloud_layers(dict(total=100, low=100, medium=100, high=100)), 10)
        self.assertIsNone(score_cloud_layers({'total': 60}))


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.clock = Mock(return_value=NOW)
        self.session = Mock()
        self.response = Mock(status_code=200, headers={'Expires': 'Wed, 18 Nov 2026 07:30:00 GMT',
                                                     'Last-Modified': 'Wed, 18 Nov 2026 02:30:00 GMT'})
        self.response.json.return_value = payload()
        self.session.get.return_value = self.response
        self.client = CloudForecastClient(self.session, self.clock)

    def test_expires_caching_conditional_get_and_304(self):
        original = self.client.fetch()
        self.clock.return_value = NOW + timedelta(minutes=45)
        self.assertEqual(self.client.fetch(), original)
        self.assertEqual(self.session.get.call_count, 1)
        self.clock.return_value = NOW + timedelta(hours=1, minutes=1)
        self.session.get.return_value = Mock(status_code=304, headers={})
        self.assertEqual(self.client.fetch(), original)
        headers = self.session.get.call_args.kwargs['headers']
        self.assertIn('BurnSky', headers['User-Agent'])
        self.assertEqual(headers['If-Modified-Since'], self.response.headers['Last-Modified'])

    def test_timeout_and_bad_json_are_failsoft_and_backed_off(self):
        for error in (requests.Timeout('timeout'), ValueError('invalid JSON')):
            client = CloudForecastClient(self.session, self.clock)
            self.session.get.side_effect = error
            self.assertIsNone(client.fetch())
            self.assertIsNone(client.fetch())
        self.assertEqual(self.session.get.call_count, 2)

    def test_failure_retains_cache_but_selector_rejects_it_when_stale(self):
        original = self.client.fetch()
        self.clock.return_value = NOW + timedelta(hours=20)
        self.session.get.side_effect = requests.ConnectionError('offline')
        cached = self.client.fetch()
        self.assertEqual(cached, original)
        self.assertIsNone(select_cloud_forecast(cached, self.clock(), self.clock()))

    def test_rate_limit_retry_after_is_respected(self):
        response = Mock(status_code=429, headers={'Retry-After': '7200'})
        response.raise_for_status.side_effect = requests.HTTPError('429')
        self.session.get.return_value = response
        self.assertIsNone(self.client.fetch())
        self.clock.return_value = NOW + timedelta(hours=1)
        self.assertIsNone(self.client.fetch())
        self.assertEqual(self.session.get.call_count, 1)


class CloudIntegrationTests(unittest.TestCase):
    def test_wrong_target_clouds_fall_back_consistently_in_score_quality_and_cards(self):
        from test_scorer_missing_inputs import isolated_class
        from modules.prediction_response import PredictionResponseBuilder
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        bundle = self.prepare(payload())
        bundle.target_weather['cloud_forecast']['valid_at'] = NOW.isoformat()
        self.assertEqual(scorer._calculate_cloud_factor(self.forecast, bundle.target_weather), 35)
        self.assertIsNone(scorer._calculate_cloud_factor({}, bundle.target_weather))
        quality = assess_prediction_quality(bundle.target_weather, bundle.observed_weather, self.forecast, 3)
        self.assertTrue(quality['score_usable'])
        self.assertIn('改用天文台文字', ''.join(quality['limitations']))
        quality_without_text = assess_prediction_quality(bundle.target_weather, bundle.observed_weather, {}, 3)
        self.assertFalse(quality_without_text['score_usable'])
        presentation = build_weather_presentation(bundle.target_weather, bundle.observed_weather, 3,
                            {'evaluated_at': (NOW + timedelta(hours=3)).isoformat()})
        self.assertNotIn('cloud_low', {card['key'] for card in presentation['cards']})
        factor = PredictionResponseBuilder(None, None, None)._factor('cloud', 35, 35, 'sunset', 3, bundle.target_weather)
        self.assertEqual(factor['source_kind'], 'text_forecast')

    def test_bad_cloud_sampling_metadata_never_supplies_model_points(self):
        from test_scorer_missing_inputs import isolated_class
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        target = NOW + timedelta(hours=3)
        for patch in (
            {'valid_at': None}, {'valid_at': target.replace(tzinfo=None).isoformat()},
            {'sample_times': None}, {'sample_times': ['bad', target.isoformat()]},
            {'method': 'unknown'}, {'method': 'hourly_model', 'sample_times': [NOW.isoformat()]},
            {'sample_times': [(target - timedelta(hours=2)).isoformat(), (target + timedelta(hours=1)).isoformat()]},
            {'sample_times': [(target + timedelta(hours=1)).isoformat(), (target + timedelta(hours=2)).isoformat()]},
            {'sample_times': [(target + timedelta(minutes=30)).isoformat(), (target - timedelta(minutes=30)).isoformat()]},
        ):
            with self.subTest(patch=patch):
                bundle = self.prepare(payload())
                bundle.target_weather['cloud_forecast'].update(patch)
                self.assertIsNone(scorer._calculate_cloud_factor({}, bundle.target_weather))

    def test_missing_or_invalid_snapshot_target_does_not_accept_cloud(self):
        from test_scorer_missing_inputs import isolated_class
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        for target in (None, 'bad', NOW.replace(tzinfo=None).isoformat(), NOW.isoformat()):
            bundle = self.prepare(payload())
            bundle.target_weather['forecast_target_at'] = target
            self.assertIsNone(scorer._calculate_cloud_factor({}, bundle.target_weather))

    def test_equivalent_timezone_and_exact_samples_keep_model_score(self):
        from test_scorer_missing_inputs import isolated_class
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        bundle = self.prepare(payload())
        bundle.target_weather['forecast_target_at'] = (NOW + timedelta(hours=3)).astimezone(timezone.utc).isoformat()
        self.assertEqual(scorer._calculate_cloud_factor({}, bundle.target_weather), score_cloud_layers(bundle.target_weather['cloud_forecast']))
        exact = NOW.replace(minute=0)
        bundle.target_weather['forecast_target_at'] = exact.isoformat()
        bundle.target_weather['cloud_forecast'] = select_cloud_forecast(payload(), exact, NOW)
        self.assertIsNotNone(scorer._calculate_cloud_factor({}, bundle.target_weather))

    def prepare(self, model):
        self.observed = {'temperature': {'data': [{'place': '香港天文台', 'value': 25}]},
                         'humidity': {'data': [{'place': '香港天文台', 'value': 60}]},
                         'rainfall': {'data': [{'max': 0}]}}
        self.forecast = {'forecastDesc': '部分時間有陽光'}
        values = {'weather': self.observed, 'forecast': self.forecast, 'ninday': {}, 'wind': {}, 'warning': {}}
        extractor = Mock()
        extractor.extract_future_weather_data.side_effect = lambda weather, *_, **kwargs: weather
        service = WeatherInputService(lambda key, _: values[key], Mock(), Mock(), Mock(), Mock(), Mock(),
                                      extractor, fetch_cloud_forecast=Mock(return_value=model), now=lambda: NOW)
        return service.prepare(3)

    def test_target_uses_model_without_mutating_observations(self):
        bundle = self.prepare(payload())
        self.assertIn('cloud_forecast', bundle.target_weather)
        self.assertNotIn('cloud_forecast', bundle.observed_weather)
        self.assertNotIn('cloud_forecast', self.observed)
        quality = assess_prediction_quality(bundle.target_weather, bundle.observed_weather, self.forecast, 3)
        self.assertTrue(quality['score_usable'])
        self.assertTrue(any('MET Norway' in note for note in quality['limitations']))
        presentation = build_weather_presentation(bundle.target_weather, bundle.observed_weather, 3,
                                                   {'evaluated_at': (NOW + timedelta(hours=3)).isoformat()})
        cards = {card['key']: card for card in presentation['cards']}
        self.assertEqual(cards['cloud_low']['value'], 45)
        self.assertEqual(cards['cloud_low']['source_kind'], 'hourly_forecast')
        self.assertEqual(presentation['cloud_attribution']['source'], 'MET Norway')

    def test_provider_outage_retains_usable_hko_fallback(self):
        bundle = self.prepare(None)
        quality = assess_prediction_quality(bundle.target_weather, bundle.observed_weather, self.forecast, 3)
        self.assertTrue(quality['score_usable'])
        self.assertNotIn('cloud_forecast', bundle.target_weather)
        self.assertTrue(any('改用天文台文字' in note for note in quality['limitations']))

    def test_numeric_cloud_forecast_does_not_require_duplicate_text_cloud_input(self):
        bundle = self.prepare(payload())
        quality = assess_prediction_quality(bundle.target_weather, bundle.observed_weather, {}, 3)
        self.assertTrue(quality['score_usable'])
        self.assertEqual(quality['missing_required'], [])
        bundle.target_weather.pop('cloud_forecast')
        self.assertFalse(assess_prediction_quality(bundle.target_weather, bundle.observed_weather, {}, 3)['score_usable'])


if __name__ == '__main__':
    unittest.main()
