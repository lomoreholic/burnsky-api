"""Offline HKO CSV, freshness, score isolation and provenance checks."""
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import Mock

import requests

from modules.prediction_response import PredictionResponseBuilder
from modules.visibility_observations import (HEADERS, VisibilityClient, parse_visibility_csv,
                                             select_visibility, visibility_score_cap)
from modules.weather_inputs import WeatherInputService
from modules.weather_presentation import build_weather_presentation
from test_scorer_missing_inputs import isolated_class, readings


NOW = datetime.now(timezone.utc).replace(second=0, microsecond=0)


def csv_text(value='800 m', station='Central', now=NOW):
    from modules.prediction_presentation import HK_TIMEZONE
    stamp = now.astimezone(HK_TIMEZONE).strftime('%Y%m%d%H%M')
    return '\ufeff' + ','.join('"' + heading + '"' for heading in HEADERS) + f'\n{stamp},"{station}","{value}"\n'


def observation(value='800 m', station='Central', now=NOW):
    return parse_visibility_csv(csv_text(value, station, now), now)


class VisibilityTests(unittest.TestCase):
    def test_actual_csv_headers_bom_hong_kong_time_units_and_zero(self):
        for raw, expected in (('800 m', .8), ('30 km', 30), ('0 m', 0)):
            data = select_visibility(observation(raw), NOW)
            reading = data['data'][0]
            self.assertEqual(reading['value'], expected)
            self.assertEqual(reading['unit'], 'km')
            self.assertEqual(datetime.fromisoformat(reading['observed_at']), NOW)
            self.assertEqual(reading['station_name'], '中環')

    def test_invalid_units_dates_values_and_headers_never_become_zero(self):
        for raw in ('N/A', '', '-1 km', 'NaN km', '>50 km', '500 mph', '101 km'):
            self.assertIsNone(observation(raw))
        self.assertIsNone(parse_visibility_csv(csv_text().replace('Date time', 'Date'), NOW))
        self.assertIsNone(parse_visibility_csv(csv_text().replace(NOW.astimezone(
            timezone(timedelta(hours=8))).strftime('%Y%m%d%H%M'), '202613010000'), NOW))

    def test_stale_future_naive_and_malformed_payloads_are_unavailable(self):
        payload = observation()
        self.assertIsNotNone(select_visibility(payload, NOW + timedelta(minutes=30)))
        for now in (NOW + timedelta(minutes=31), NOW - timedelta(minutes=3)):
            self.assertIsNone(select_visibility(payload, now))
        for data in ({}, {'data': None}, {'retrieved_at': NOW.isoformat(), 'data': None}):
            self.assertIsNone(select_visibility(data, NOW))
        payload['data'][0]['observed_at'] = NOW.replace(tzinfo=None).isoformat()
        self.assertIsNone(select_visibility(payload, NOW))

    def test_duplicate_rows_are_rejected_and_stations_remain_separate(self):
        text = csv_text()
        self.assertIsNone(parse_visibility_csv(text + text.splitlines()[1], NOW))
        payload = observation('500 m', 'Waglan Island')
        payload['data'].extend(observation('30 km')['data'])
        data = select_visibility(payload, NOW)
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['reference_station'], 'Central')

    def test_fetch_timeout_cache_backoff_and_expiry(self):
        clock = Mock(return_value=NOW)
        session = Mock()
        response = Mock(content=csv_text().encode('utf-8'))
        session.get.return_value = response
        client = VisibilityClient(session, clock)
        original = client.fetch()
        self.assertEqual(client.fetch(), original)
        session.get.assert_called_once()
        clock.return_value += timedelta(minutes=6)
        session.get.side_effect = requests.Timeout('offline')
        self.assertEqual(client.fetch(), original)
        self.assertEqual(client.fetch(), original)
        self.assertEqual(session.get.call_count, 2)
        clock.return_value += timedelta(minutes=31)
        self.assertIsNone(select_visibility(client.fetch(), clock()))
        self.assertIsNone(VisibilityClient(session, clock).fetch())

    def test_visibility_can_only_limit_current_factor_not_future_or_other_stations(self):
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        weather = readings()
        weather['visibility_observations'] = observation()
        self.assertEqual(scorer._calculate_visibility_factor(weather), 1)
        self.assertEqual(scorer._calculate_visibility_factor(weather, 3), 20)
        weather['visibility_observations'] = observation('50 km')
        self.assertEqual(scorer._calculate_visibility_factor(weather), 20)
        weather['visibility_observations'] = observation('100 m', 'Waglan Island')
        self.assertEqual(scorer._calculate_visibility_factor(weather), 20)
        weather['visibility_observations'] = observation(now=NOW-timedelta(hours=1))
        self.assertEqual(scorer._calculate_visibility_factor(weather), 20)
        del weather['rainfall']
        weather['visibility_observations'] = observation()
        self.assertIsNone(scorer._calculate_visibility_factor(weather))
        self.assertEqual(visibility_score_cap(0), 0)
        self.assertIsNone(visibility_score_cap(True))

    def test_inputs_presentation_and_factor_preserve_observation_not_forecast(self):
        original = readings()
        sources = {'weather': original, 'forecast': {}, 'ninday': {}, 'wind': {}, 'warning': {}}
        extractor = Mock()
        extractor.extract_future_weather_data.side_effect = lambda weather, *_, **kwargs: weather
        service = WeatherInputService(lambda key, _: sources[key], Mock(), Mock(), Mock(), Mock(), Mock(),
            extractor, now=lambda: NOW, fetch_visibility=Mock(return_value=observation()))
        bundle = service.prepare(3)
        self.assertNotIn('visibility_observations', original)
        self.assertEqual(bundle.observed_weather['visibility_observations'], bundle.target_weather['visibility_observations'])
        view = build_weather_presentation(bundle.target_weather, bundle.observed_weather, 3, {'evaluated_at': NOW.isoformat()})
        card = next(card for card in view['cards'] if card['key'] == 'visibility_Central')
        self.assertEqual(card['source_kind'], 'observed')
        self.assertEqual(card['station'], '中環')
        self.assertEqual(card['updated_at'], observation()['data'][0]['observed_at'])
        self.assertIsNone(card['valid_at'])
        self.assertIn('未用作未來分數扣分', card['note'])
        builder = PredictionResponseBuilder(None, None, None)
        future = builder._factor('visibility', 20, 20, 'sunset', 3, bundle.target_weather)
        self.assertFalse(future['visibility_cap_considered'])
        current = builder._factor('visibility', 1, 20, 'sunset', 0, bundle.target_weather)
        self.assertEqual(current['visibility_cap'], 1)
        self.assertEqual(current['visibility_observation']['station'], 'Central')
        self.assertTrue(current['visibility_cap_considered'])


if __name__ == '__main__':
    unittest.main()
