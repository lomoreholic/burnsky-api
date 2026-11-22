"""Offline checks for actual target weather, units, rain periods and provenance."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import Mock

from modules.cloud_forecast import FIELDS as CLOUD_FIELDS
from modules.hourly_weather import model_reading, select_hourly_weather
from modules.prediction_presentation import HK_TIMEZONE
from modules.prediction_quality import assess_prediction_quality, highest_rainfall, station_value, weather_value
from modules.prediction_response import PredictionResponseBuilder
from modules.warning_risk import FutureWarningRiskService
from modules.weather_inputs import WeatherInputService
from modules.weather_presentation import build_weather_presentation


NOW = datetime(2026, 11, 19, 3, 30, tzinfo=HK_TIMEZONE)
TARGET = NOW + timedelta(hours=3)


def payload():
    series = []
    for i in range(5):
        series.append({'time': (NOW.replace(minute=0) + timedelta(hours=i)).astimezone(timezone.utc).isoformat(),
                       'data': {'instant': {'details': dict(air_temperature=20+i*2, relative_humidity=60+i*4,
                            wind_speed=i*2, ultraviolet_index_clear_sky=99,
                            **{field: 50 for field in CLOUD_FIELDS.values()})},
                            'next_1_hours': {'details': {'precipitation_amount': i*2}},
                            'next_6_hours': {'details': {'precipitation_amount': 60}}}})
    return {'properties': {'meta': {'updated_at': (NOW-timedelta(hours=2)).isoformat(),
                'units': {'air_temperature': 'celsius', 'relative_humidity': '%',
                          'wind_speed': 'm/s', 'precipitation_amount': 'mm',
                          **{field: '%' for field in CLOUD_FIELDS.values()}}}, 'timeseries': series}}


def inputs(model, hours=3, observed=None):
    observed = deepcopy(observed) if observed is not None else {
        'updateTime': NOW.isoformat(),
        'temperature': {'data': [{'place': '香港天文台', 'value': 30}]},
        'humidity': {'data': [{'place': '香港天文台', 'value': 60}]},
        'rainfall': {'data': [{'max': 0}]}, 'uvindex': {'data': [{'value': 0}]}}
    values = {'weather': observed, 'forecast': {'forecastDesc': '多雲'}, 'ninday': {}, 'wind': {}, 'warning': {}}
    extractor = Mock()
    extractor.extract_future_weather_data.side_effect = lambda weather, *_, **kwargs: weather
    provider = Mock(return_value=model)
    service = WeatherInputService(lambda key, _: values[key], Mock(), Mock(), Mock(), Mock(), Mock(),
                                  extractor, fetch_cloud_forecast=provider, now=lambda: NOW)
    return service.prepare(hours), provider


class HourlySelectionTests(unittest.TestCase):
    def test_target_instant_values_interpolate_and_wind_converts_to_kmh(self):
        model = select_hourly_weather(payload(), TARGET, NOW)
        fields = model['fields']
        self.assertEqual(fields['temperature']['value'], 27)
        self.assertEqual(fields['humidity']['value'], 74)
        self.assertEqual(fields['wind_speed']['value'], 25.2)
        self.assertEqual(fields['wind_speed']['unit'], 'km/h')
        self.assertEqual(fields['temperature']['method'], 'linear_interpolation')
        self.assertEqual(len(fields['temperature']['sample_times']), 2)
        self.assertEqual(model['valid_at'], TARGET.isoformat())
        self.assertEqual(model['missing_fields'], [])
        self.assertNotIn('uvindex', fields)

    def test_rain_is_entire_containing_hour_not_interpolated_or_divided(self):
        model = select_hourly_weather(payload(), TARGET, NOW)
        rain = model['fields']['rainfall']
        self.assertEqual(rain['value'], 6)  # Not 7 (interpolated), 3 (half-hour) or 10 (6h/6).
        self.assertEqual(datetime.fromisoformat(rain['period_start']).hour, 22)  # UTC, previous day.
        self.assertEqual(datetime.fromisoformat(rain['period_end'])-datetime.fromisoformat(rain['period_start']), timedelta(hours=1))
        boundary = select_hourly_weather(payload(), TARGET.replace(minute=0), NOW)['fields']['rainfall']
        self.assertEqual(boundary['value'], 6)
        self.assertEqual(datetime.fromisoformat(boundary['period_start']), TARGET.replace(minute=0))

    def test_no_one_hour_rain_never_uses_six_hour_amount_or_zero(self):
        data = payload()
        for entry in data['properties']['timeseries']:
            del entry['data']['next_1_hours']
        selected = select_hourly_weather(data, TARGET, NOW)
        self.assertNotIn('rainfall', selected['fields'])
        self.assertIn('rainfall', selected['missing_fields'])

    def test_missing_field_does_not_discard_independent_fields(self):
        for invalid in (None, True, '74', float('nan'), float('inf'), -1, 101):
            data = payload()
            data['properties']['timeseries'][3]['data']['instant']['details']['relative_humidity'] = invalid
            selected = select_hourly_weather(data, TARGET, NOW)
            self.assertNotIn('humidity', selected['fields'])
            self.assertIn('temperature', selected['fields'])
            self.assertIn('rainfall', selected['fields'])

    def test_units_are_required_and_checked_per_field(self):
        for key in ('air_temperature', 'relative_humidity', 'wind_speed', 'precipitation_amount'):
            data = payload(); data['properties']['meta']['units'][key] = 'wrong'
            selected = select_hourly_weather(data, TARGET, NOW)
            self.assertEqual(len(selected['missing_fields']), 1)
            self.assertEqual(len(selected['fields']), 3)
        data = payload(); del data['properties']['meta']['units']
        self.assertIsNone(select_hourly_weather(data, TARGET, NOW))

    def test_no_bridging_extrapolation_or_ambiguous_duplicates(self):
        data = payload(); del data['properties']['timeseries'][3]
        self.assertIsNone(select_hourly_weather(data, TARGET, NOW))
        self.assertIsNone(select_hourly_weather(payload(), NOW-timedelta(hours=1), NOW))
        self.assertIsNone(select_hourly_weather(payload(), NOW+timedelta(hours=5), NOW))
        data = payload(); data['properties']['timeseries'].append(deepcopy(data['properties']['timeseries'][3]))
        self.assertIsNone(select_hourly_weather(data, TARGET, NOW))

    def test_exact_record_and_legitimate_zeroes_remain_available(self):
        model = select_hourly_weather(payload(), NOW.replace(minute=0), NOW)
        self.assertEqual(model['fields']['wind_speed']['value'], 0)
        self.assertEqual(model['fields']['rainfall']['value'], 0)
        self.assertEqual(model['fields']['temperature']['method'], 'hourly_model')
        self.assertEqual(len(model['fields']['temperature']['sample_times']), 1)

    def test_invalid_stale_and_future_runs_are_rejected(self):
        for updated in ((NOW-timedelta(hours=19)).isoformat(), (NOW+timedelta(minutes=16)).isoformat(),
                        NOW.isoformat()[:19], 'invalid', None):
            data = payload(); data['properties']['meta']['updated_at'] = updated
            self.assertIsNone(select_hourly_weather(data, TARGET, NOW))
        for data in (None, [], {}, {'properties': {}}, {'properties': {'meta': []}}):
            self.assertIsNone(select_hourly_weather(data, TARGET, NOW))


class HourlyIntegrationTests(unittest.TestCase):
    def test_bad_cloud_units_preserve_independent_hourly_weather_fields(self):
        data = payload()
        data['properties']['meta']['units'][CLOUD_FIELDS['low']] = 'fraction'
        bundle, _ = inputs(data)
        self.assertNotIn('cloud_forecast', bundle.target_weather)
        for key in ('temperature', 'humidity', 'wind_speed', 'rainfall'):
            self.assertIsNotNone(model_reading(bundle.target_weather, key))
        quality = assess_prediction_quality(bundle.target_weather, bundle.observed_weather, bundle.forecast_data, 3)
        self.assertTrue(quality['score_usable'])

    def test_consumers_reject_wrong_or_missing_target_metadata(self):
        for invalid in (None, 'invalid', TARGET.replace(tzinfo=None).isoformat(),
                        (TARGET + timedelta(hours=1)).isoformat()):
            with self.subTest(target=invalid):
                bundle, _ = inputs(payload())
                bundle.target_weather['forecast_target_at'] = invalid
                for key in ('temperature', 'humidity', 'wind_speed', 'rainfall'):
                    self.assertIsNone(model_reading(bundle.target_weather, key))
        bundle, _ = inputs(payload())
        del bundle.target_weather['forecast_target_at']
        self.assertIsNone(model_reading(bundle.target_weather, 'temperature'))
        bundle.target_weather['forecast_target_at'] = TARGET.astimezone(timezone.utc).isoformat()
        self.assertIsNotNone(model_reading(bundle.target_weather, 'temperature'))

    def test_invalid_model_valid_time_is_not_used(self):
        for invalid in (None, 'invalid', TARGET.replace(tzinfo=None).isoformat(),
                        (TARGET - timedelta(hours=1)).isoformat()):
            bundle, _ = inputs(payload())
            bundle.target_weather['hourly_weather_forecast']['valid_at'] = invalid
            self.assertIsNone(weather_value(bundle.target_weather, 'temperature'))
            self.assertIsNone(highest_rainfall(bundle.target_weather))

    def test_bad_sample_metadata_does_not_break_other_fields(self):
        for invalid in (None, {}, 'invalid', [], [None], ['invalid'],
                        [TARGET.isoformat()] * 3):
            bundle, _ = inputs(payload())
            bundle.target_weather['hourly_weather_forecast']['fields']['humidity']['sample_times'] = invalid
            self.assertIsNone(model_reading(bundle.target_weather, 'humidity'))
            self.assertIsNotNone(model_reading(bundle.target_weather, 'temperature'))
        for key in ('period_start', 'period_end'):
            for invalid in (None, 'invalid', TARGET.replace(tzinfo=None).isoformat()):
                bundle, _ = inputs(payload())
                bundle.target_weather['hourly_weather_forecast']['fields']['rainfall'][key] = invalid
                self.assertIsNone(model_reading(bundle.target_weather, 'rainfall'))

    def test_consumers_accept_exact_samples_zeroes_and_rain_start_boundary(self):
        target = NOW.replace(minute=0)
        model = select_hourly_weather(payload(), target, NOW)
        weather = {'hourly_weather_forecast': model, 'forecast_target_at': target.isoformat()}
        for key in ('temperature', 'humidity', 'wind_speed', 'rainfall'):
            self.assertIsNotNone(model_reading(weather, key))
        self.assertEqual(highest_rainfall(weather), 0)
        self.assertEqual(weather_value(weather, 'wind_speed'), 0)

    def test_instant_samples_must_match_method_and_bracket_target(self):
        for method, samples in (
            ('hourly_model', [TARGET - timedelta(hours=1)]),
            ('linear_interpolation', [TARGET - timedelta(hours=2), TARGET + timedelta(hours=1)]),
            ('linear_interpolation', [TARGET + timedelta(minutes=1), TARGET + timedelta(minutes=31)]),
            ('linear_interpolation', [TARGET + timedelta(minutes=30), TARGET - timedelta(minutes=30)]),
            ('linear_interpolation', [TARGET]), ('unknown', [TARGET]),
            ('hourly_model', [TARGET.replace(tzinfo=None)]),
        ):
            with self.subTest(method=method, samples=samples):
                bundle, _ = inputs(payload())
                field = bundle.target_weather['hourly_weather_forecast']['fields']['temperature']
                field.update(method=method, sample_times=[at.isoformat() for at in samples])
                self.assertIsNone(model_reading(bundle.target_weather, 'temperature'))
                self.assertIsNotNone(model_reading(bundle.target_weather, 'humidity'))

    def test_rain_interval_is_half_open_one_hour_and_matches_sample(self):
        for start, end, samples, method in (
            (TARGET - timedelta(hours=1), TARGET, [TARGET - timedelta(hours=1)], 'hourly_accumulation'),
            (TARGET, TARGET + timedelta(hours=6), [TARGET], 'hourly_accumulation'),
            (TARGET + timedelta(minutes=1), TARGET + timedelta(minutes=61), [TARGET], 'hourly_accumulation'),
            (TARGET, TARGET + timedelta(hours=1), [], 'hourly_accumulation'),
            (TARGET, TARGET + timedelta(hours=1), [TARGET], 'linear_interpolation'),
        ):
            with self.subTest(start=start, end=end, method=method):
                bundle, _ = inputs(payload())
                rain = bundle.target_weather['hourly_weather_forecast']['fields']['rainfall']
                rain.update(period_start=start.isoformat(), period_end=end.isoformat(),
                            sample_times=[at.isoformat() for at in samples], method=method)
                self.assertIsNone(highest_rainfall(bundle.target_weather))
                self.assertIsNotNone(model_reading(bundle.target_weather, 'wind_speed'))

    def test_invalid_copied_wind_and_rain_do_not_bypass_scoring_validation(self):
        from test_scorer_missing_inputs import isolated_class
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        bundle, _ = inputs(payload())
        weather = bundle.target_weather
        weather['hourly_weather_forecast']['fields']['wind_speed']['sample_times'] = []
        weather['hourly_weather_forecast']['fields']['rainfall']['period_end'] = TARGET.isoformat()
        weather['wind']['speed'] = 100
        self.assertIsNone(scorer._calculate_wind_factor(weather))
        self.assertIsNone(scorer._calculate_visibility_factor(weather))
        warnings = []
        self.assertEqual(FutureWarningRiskService._wind_risk(weather, warnings), 0)
        self.assertEqual(warnings, [])
        quality = assess_prediction_quality(weather, bundle.observed_weather, bundle.forecast_data, 3)
        self.assertTrue(quality['score_usable'])
        self.assertIn('風速因子未取得', ''.join(quality['limitations']))
        self.assertEqual(quality['status'], 'limited')
        cards = {c['key']: c for c in build_weather_presentation(weather, bundle.observed_weather, 3,
                                 {'evaluated_at': TARGET.isoformat()})['cards']}
        self.assertEqual(cards['temperature']['source_kind'], 'hourly_forecast')
        self.assertEqual(cards['rainfall']['source_kind'], 'observed')
        factor = PredictionResponseBuilder(None, None, None)._factor('wind', None, 15, 'sunrise', 3, weather)
        self.assertIsNone(factor['wind_speed'])

    def test_scoring_uses_validated_model_value_instead_of_modified_copy(self):
        from test_scorer_missing_inputs import isolated_class
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        bundle, _ = inputs(payload())
        bundle.target_weather['wind']['speed'] = 100
        bundle.target_weather['rainfall']['data'][0]['max'] = 999
        self.assertEqual(scorer._calculate_wind_factor(bundle.target_weather), 2)
        self.assertEqual(highest_rainfall(bundle.target_weather), 6)
        factor = PredictionResponseBuilder(None, None, None)._factor('wind', 2, 15, 'sunrise', 3, bundle.target_weather)
        self.assertEqual(factor['wind_speed'], 25.2)

    def test_single_cached_provider_payload_does_not_mutate_observations(self):
        data = payload(); original = deepcopy(data)
        bundle, provider = inputs(data)
        provider.assert_called_once()
        self.assertEqual(data, original)
        self.assertNotIn('hourly_weather_forecast', bundle.observed_weather)
        self.assertEqual(station_value(bundle.observed_weather, 'temperature'), 30)
        self.assertIsNone(station_value(bundle.target_weather, 'temperature'))
        self.assertEqual(weather_value(bundle.target_weather, 'temperature'), 27)
        self.assertEqual(bundle.target_weather['wind']['speed'], 25.2)
        self.assertEqual(bundle.target_weather['rainfall']['data'][0]['max'], 6)

    def test_hourly_data_can_support_forecast_without_hko_observations(self):
        bundle, _ = inputs(payload(), observed={})
        quality = assess_prediction_quality(bundle.target_weather, bundle.observed_weather, {}, 3)
        self.assertTrue(quality['score_usable'])
        self.assertEqual(quality['status'], 'ready')
        self.assertIn('無雨亦可能有霧或霾', ''.join(quality['limitations']))
        self.assertFalse(quality['allow_high_score_notification'])
        # A missing real model field must not be concealed by fabricated station defaults.
        del bundle.target_weather['hourly_weather_forecast']['fields']['humidity']
        self.assertFalse(assess_prediction_quality(bundle.target_weather, {}, {}, 3)['score_usable'])

    def test_partial_hourly_forecast_and_provider_outage_keep_declared_fallbacks(self):
        data = payload()
        for entry in data['properties']['timeseries']:
            del entry['data']['instant']['details']['relative_humidity']
            del entry['data']['next_1_hours']
        bundle, _ = inputs(data)
        cards = {c['key']: c for c in build_weather_presentation(bundle.target_weather, bundle.observed_weather, 3, {'evaluated_at':TARGET.isoformat()})['cards']}
        self.assertEqual(cards['temperature']['source_kind'], 'hourly_forecast')
        self.assertEqual(cards['humidity']['source_kind'], 'estimated')
        self.assertEqual(cards['rainfall']['source_kind'], 'observed')
        self.assertIn('暫缺', cards['rainfall']['note'])
        bundle, _ = inputs(None)
        self.assertNotIn('hourly_weather_forecast', bundle.target_weather)
        self.assertTrue(assess_prediction_quality(bundle.target_weather, bundle.observed_weather, bundle.forecast_data, 3)['score_usable'])

    def test_model_weather_does_not_require_cloud_layers(self):
        data = payload()
        for entry in data['properties']['timeseries']:
            for key in CLOUD_FIELDS.values():
                del entry['data']['instant']['details'][key]
        bundle, _ = inputs(data)
        self.assertNotIn('cloud_forecast', bundle.target_weather)
        presentation = build_weather_presentation(bundle.target_weather, bundle.observed_weather, 3, {'evaluated_at':TARGET.isoformat()})
        self.assertEqual(presentation['cloud_attribution']['source'], 'MET Norway')
        self.assertIn('逐小時模式', presentation['summary'])

    def test_current_mode_preserves_actual_observations(self):
        bundle, _ = inputs(payload(), hours=0)
        self.assertNotIn('hourly_weather_forecast', bundle.target_weather)
        self.assertEqual(station_value(bundle.target_weather, 'temperature'), 30)
        self.assertEqual(bundle.target_weather['rainfall']['data'][0]['max'], 0)

    def test_cards_and_factor_details_preserve_model_provenance(self):
        bundle, _ = inputs(payload())
        cards = {c['key']: c for c in build_weather_presentation(bundle.target_weather, bundle.observed_weather, 3, {'evaluated_at':TARGET.isoformat()})['cards']}
        for key in ('temperature', 'humidity', 'wind', 'rainfall'):
            self.assertEqual(cards[key]['source_kind'], 'hourly_forecast')
            self.assertEqual(cards[key]['source'], 'MET Norway')
            self.assertEqual(cards[key]['valid_at'], TARGET.isoformat())
        self.assertEqual(cards['uvindex']['value'], 0)  # Clear-sky UV 99 is never an all-sky forecast.
        self.assertEqual(cards['uvindex']['source_kind'], 'observed')
        self.assertIn('period_start', cards['rainfall'])
        builder = PredictionResponseBuilder(None, None, None)
        for key in ('temperature', 'humidity', 'wind', 'visibility'):
            factor = builder._factor(key, 5, 20, 'sunrise', 3, bundle.target_weather)
            self.assertEqual(factor['source_kind'], 'hourly_forecast')
            self.assertIn('forecast_reading', factor)

    def test_future_warning_risk_reuses_selected_model_instead_of_reextracting(self):
        bundle, _ = inputs(payload())
        bundle.target_weather['hourly_weather_forecast']['fields']['humidity']['value'] = 96
        bundle.target_weather['hourly_weather_forecast']['fields']['wind_speed']['value'] = 70
        extractor = Mock()
        service = FutureWarningRiskService(extractor, now=lambda: NOW)
        _, warnings = service.assess(bundle.observed_weather, {}, {}, 3, target_weather=bundle.target_weather)
        extractor.extract_future_weather_data.assert_not_called()
        self.assertTrue(any('風力' in message for message in warnings))
        self.assertTrue(any('極高濕度' in message for message in warnings))

    def test_response_target_does_not_drift_with_provider_latency(self):
        bundle, _ = inputs(payload())
        builder = PredictionResponseBuilder(lambda _: 'test', lambda _: {'sunrise':'06:40', 'sunset':'17:40'}, lambda x:x,
                                            now=lambda _:NOW+timedelta(minutes=2))
        unified = dict(analysis={}, ml_score=None, traditional_normalized=50, traditional_score=75,
                       weighted_score=50, weights_used={'ml':0,'traditional':1},
                       time_factor={'prediction_time':'06:30', 'time_diff_minutes':10,
                                    'evaluated_at':TARGET.isoformat()})
        result = builder.build(score=50, prediction_type='sunrise', advance_hours=3, unified_result=unified,
            intensity_prediction={}, color_prediction={}, target_weather=bundle.target_weather,
            observed_weather=bundle.observed_weather, forecast_data={}, warning_data={}, warning_impact=0,
            warning_risk_score=0, warning_risk_warnings=[], active_warnings=[], warning_analysis={})
        self.assertEqual(result['prediction_timing']['evaluated_at'], TARGET.isoformat())
        self.assertEqual(result['prediction_timing']['generated_at'], (NOW+timedelta(minutes=2)).isoformat())
        self.assertEqual(result['scoring_method'], 'unified_v1.12_cloud_time_validation')
        self.assertEqual(result['analysis_details']['time_factor']['prediction_time'], '06:30')
        self.assertEqual(result['analysis_details']['time_factor']['time_diff_minutes'], 10)
        self.assertEqual(result['analysis_details']['time_factor']['evaluated_at'], TARGET.isoformat())


if __name__ == '__main__':
    unittest.main()
