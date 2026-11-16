"""Offline checks for observation provenance and absent data."""
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from unittest.mock import patch

from hko_fetcher import get_current_wind_data
from modules.weather_presentation import build_weather_presentation


class WeatherPresentationTests(unittest.TestCase):
    def setUp(self):
        self.observed = {
            'updateTime': '2026-11-14T15:00:00+08:00',
            'temperature': {'data': [{'place': '香港天文台', 'value': 25}]},
            'humidity': {'data': [{'place': '香港天文台', 'value': 60}]},
            'uvindex': {'data': [{'place': '京士柏', 'value': 0}]},
            'wind': {'description': '東風4至5級', 'forecast_date': '20261114',
                     'source_updated_at': '2026-11-14T11:30:00+08:00'},
            'rainfall': {'data': [{'place': '中西區', 'max': 2}, {'place': '大埔', 'max': 3}],
                         'endTime': '2026-11-14T15:00:00+08:00'},
            'icon': [50],
        }
        self.timing = {'evaluated_at': '2026-11-14T17:00:00+08:00'}

    def cards(self, target=None, hours=0, observed=None):
        result = build_weather_presentation(target if target is not None else self.observed,
                                            self.observed if observed is None else observed, hours, self.timing)
        return {card['key']: card for card in result['cards']}

    def test_current_observations_keep_station_time_and_valid_zero(self):
        cards = self.cards()
        self.assertEqual(cards['temperature']['source_kind'], 'observed')
        self.assertEqual(cards['temperature']['station'], '香港天文台')
        self.assertEqual(cards['temperature']['updated_at'], self.observed['updateTime'])
        self.assertEqual(cards['uvindex']['value'], 0)
        self.assertEqual(cards['wind']['source_kind'], 'forecast')

    def test_future_estimates_do_not_relabel_retained_observations(self):
        target = deepcopy(self.observed)
        target['temperature']['data'][0]['value'] = 27
        target['updateTime'] = self.timing['evaluated_at']
        target['uvindex']['value'] = 0
        cards = self.cards(target, 2)
        self.assertEqual(cards['temperature']['source_kind'], 'estimated')
        self.assertEqual(cards['temperature']['value'], 27)
        self.assertEqual(cards['temperature']['valid_at'], self.timing['evaluated_at'])
        self.assertEqual(cards['temperature']['updated_at'], self.observed['updateTime'])
        for key in ('uvindex', 'rainfall', 'weather_icon'):
            self.assertEqual(cards[key]['source_kind'], 'observed')
            self.assertIn('並非目標時段預報', cards[key]['note'])
        self.assertEqual(cards['wind']['valid_at'], '20261114')

    def test_district_rainfall_is_maximum_instead_of_sum(self):
        rainfall = self.cards()['rainfall']
        self.assertEqual(rainfall['value'], 3)
        self.assertEqual(rainfall['station'], '大埔')
        self.observed['rainfall']['data'] = [{'place': '大埔', 'max': 0}]
        self.assertEqual(self.cards()['rainfall']['value'], 0)

    def test_missing_data_does_not_become_nighttime_uv_or_zero_rain_or_calm_wind(self):
        cards = self.cards({}, observed={})
        for card in cards.values():
            self.assertIsNone(card['value'])
            self.assertEqual(card['source_kind'], 'unavailable')
        self.assertNotIn('夜間', cards['uvindex']['note'])

    def test_invalid_or_unattributed_scalars_are_not_official_readings(self):
        cards = self.cards({'temperature': 25, 'humidity': {'data': [{'place': '香港天文台', 'value': True}]},
                            'uvindex': None, 'wind': {'speed_kmh_min': 0, 'description': ''}})
        self.assertIsNone(cards['temperature']['value'])
        self.assertIsNone(cards['humidity']['value'])
        self.assertIsNone(cards['wind']['value'])

    def test_wind_provider_preserves_publication_time_and_forecast_date(self):
        with patch('hko_fetcher.datetime') as clock, patch('hko_fetcher.fetch_ninday_forecast', return_value={
            'updateTime': '2026-11-14T11:30:00+08:00',
            'weatherForecast': [{'forecastDate': '20261114', 'forecastWind': '東風4至5級。'}],
        }):
            clock.now.return_value = datetime(2026, 11, 14, tzinfo=timezone.utc)
            wind = get_current_wind_data()
        self.assertEqual(wind['source_updated_at'], '2026-11-14T11:30:00+08:00')
        self.assertEqual(wind['forecast_date'], '20261114')

    def test_tomorrows_wind_is_not_substituted_for_todays_missing_forecast(self):
        with patch('hko_fetcher.datetime') as clock, patch('hko_fetcher.fetch_ninday_forecast', return_value={
            'weatherForecast': [{'forecastDate': '20261115', 'forecastWind': '東風4至5級。'}],
        }):
            clock.now.return_value = datetime(2026, 11, 14, tzinfo=timezone.utc)
            wind = get_current_wind_data()
        self.assertEqual(wind['description'], '')
        self.assertNotIn('forecast_date', wind)


if __name__ == '__main__':
    unittest.main()
