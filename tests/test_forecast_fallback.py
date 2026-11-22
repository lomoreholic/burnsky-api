"""Fallback forecasts preserve target dates, real observations and missing inputs."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import Mock

from forecast_extractor import ForecastExtractor
from modules.prediction_quality import assess_prediction_quality
from modules.prediction_response import PredictionResponseBuilder
from modules.weather_inputs import WeatherInputService
from modules.weather_presentation import build_weather_presentation


class ForecastFallbackTests(unittest.TestCase):
    def setUp(self):
        self.extractor = ForecastExtractor()
        self.observed = {
            'updateTime': '2026-11-30T22:30:00+08:00',
            'temperature': {'data': [{'place': '香港天文台', 'value': 10}]},
            'humidity': {'data': [{'place': '香港天文台', 'value': 0}]},
            'uvindex': {'data': [{'value': 0}]},
            'rainfall': {'data': [{'max': 0}]}}
        self.target = datetime(2026, 11, 30, 17, 30, tzinfo=timezone.utc)  # Dec 1 HKT.

    def extract(self, observed=None, daily=None, target=None):
        return self.extractor.extract_future_weather_data(
            self.observed if observed is None else observed, {}, daily or {}, 3,
            evaluated_at=target or self.target)

    def test_explicit_target_selects_hong_kong_date_and_keeps_observation_time(self):
        daily = {'weatherForecast': [
            {'forecastDate': '20261130', 'forecastMintemp': {'value': 25}},
            {'forecastDate': '20261201', 'forecastMintemp': {'value': 5}}]}
        result = self.extract(daily=daily)
        expected = self.extract(daily={'weatherForecast': [daily['weatherForecast'][1]]})
        self.assertEqual(result['temperature'], expected['temperature'])
        self.assertLess(result['temperature']['data'][0]['value'], self.extract()['temperature']['data'][0]['value'])
        self.assertEqual(result['updateTime'], self.observed['updateTime'])
        self.assertEqual(datetime.fromisoformat(result['forecast_target_at']), self.target)
        self.assertEqual(result['forecast_estimation']['method'], 'heuristic_observation_adjustment')

    def test_winter_temperature_is_not_forced_up_to_fifteen(self):
        result = self.extract()
        self.assertLess(result['temperature']['data'][0]['value'], 10)
        self.assertEqual(result['humidity']['data'][0]['value'], 0)
        self.assertEqual(result['rainfall']['data'][0]['max'], 0)

    def test_missing_daily_extrema_do_not_invent_twenty_five_or_thirty_degrees(self):
        baseline = self.extract()
        for daily in ({'forecastDate': '20261201'},
                      {'forecastDate': '20261201', 'forecastMintemp': {}},
                      {'forecastDate': '20261201', 'forecastMintemp': {'value': None}},
                      {'forecastDate': '20261201', 'forecastMintemp': {'value': '25'}}):
            with self.subTest(daily=daily):
                result = self.extract(daily={'weatherForecast': [daily]})
                self.assertEqual(result['temperature'], baseline['temperature'])

    def test_invalid_or_empty_station_rows_do_not_break_valid_readings(self):
        observed = deepcopy(self.observed)
        observed['temperature']['data'] += [{}, None, {'value': 'bad'}, {'value': True}]
        observed['humidity']['data'] += [{}, None, {'value': 'bad'}]
        original = deepcopy(observed)
        result = self.extract(observed, daily={'weatherForecast': [
            {'forecastDate': '20261201', 'forecastMintemp': {'value': 5}, 'forecastWeather': '天晴'}]})
        self.assertIsInstance(result['temperature']['data'][0]['value'], (int, float))
        self.assertEqual(result['humidity']['data'][0]['value'], 0)
        result['rainfall']['data'][0]['max'] = 99
        result['uvindex']['data'][0]['value'] = 99
        self.assertEqual(observed, original)
        empty = dict(self.observed, temperature={'data': []})
        self.assertEqual(self.extract(empty)['temperature']['data'], [])

    def test_inverted_daily_extrema_do_not_change_the_fallback(self):
        invalid = {'weatherForecast': [{'forecastDate': '20261201',
                    'forecastMintemp': {'value': 30}, 'forecastMaxtemp': {'value': 5}}]}
        self.assertEqual(self.extract(daily=invalid)['temperature'], self.extract()['temperature'])

    def test_missing_daily_maximum_never_uses_an_invented_afternoon_maximum(self):
        target = self.target.replace(hour=6)  # 14:30 HKT, same UTC date Nov 30.
        daily = {'weatherForecast': [{'forecastDate': '20261130', 'forecastMintemp': {'value': 5}}]}
        self.assertEqual(self.extract(daily=daily, target=target)['temperature'],
                         self.extract(target=target)['temperature'])

    def test_real_input_service_passes_initial_target_and_preserves_fallback_provenance(self):
        started = self.target - timedelta(hours=3)
        clock = Mock(side_effect=[started, started + timedelta(minutes=5)])
        values = {'weather': self.observed, 'forecast': {'forecastDesc': '多雲'},
                  'ninday': {}, 'wind': {}, 'warning': {}}
        extractor = Mock(wraps=self.extractor)
        service = WeatherInputService(lambda key, _: values[key], Mock(), Mock(), Mock(), Mock(), Mock(),
                                      extractor, now=clock, fetch_cloud_forecast=lambda: None)
        bundle = service.prepare(3)
        self.assertEqual(extractor.extract_future_weather_data.call_args.kwargs['evaluated_at'], self.target)
        clock.assert_called_once()
        self.assertEqual(bundle.target_weather['updateTime'], self.observed['updateTime'])
        self.assertEqual(datetime.fromisoformat(bundle.target_weather['forecast_estimation']['valid_at']), self.target)
        quality = assess_prediction_quality(bundle.target_weather, bundle.observed_weather, bundle.forecast_data, 3)
        self.assertTrue(quality['score_usable'])
        self.assertIn('尚未校準', ''.join(quality['limitations']))
        presentation = build_weather_presentation(bundle.target_weather, bundle.observed_weather, 3,
                                                   {'evaluated_at': self.target.isoformat()})
        temperature = next(card for card in presentation['cards'] if card['key'] == 'temperature')
        self.assertEqual(temperature['source_kind'], 'estimated')
        self.assertEqual(temperature['updated_at'], self.observed['updateTime'])
        self.assertEqual(datetime.fromisoformat(temperature['valid_at']), self.target)
        factor = PredictionResponseBuilder(None, None, None)._factor(
            'temperature', 3, 15, 'sunrise', 3, bundle.target_weather)
        self.assertEqual(factor['source_kind'], 'estimated')
        self.assertEqual(factor['updated_at'], self.observed['updateTime'])
        self.assertIn('尚未校準', factor['description'])

    def test_uv_stays_an_observation_even_if_a_legacy_top_level_value_is_present(self):
        observed = deepcopy(self.observed)
        observed['uvindex']['value'] = 7
        self.assertEqual(self.extract(observed)['uvindex'], observed['uvindex'])

    def test_invalid_explicit_target_is_not_replaced_by_server_clock(self):
        for invalid in ('2026-12-01', datetime(2026, 12, 1)):
            with self.assertRaises(ValueError):
                self.extract(target=invalid)


if __name__ == '__main__':
    unittest.main()
