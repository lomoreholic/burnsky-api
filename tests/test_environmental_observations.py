"""Official formats, dated cache rejection and separation of future inputs."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import unittest
from unittest.mock import Mock

import requests

from modules.environmental_observations import (AIR_URL, PRESSURE_URL, ObservationClient,
    fresh_observation, parse_air, parse_pressure)
from modules.prediction_response import PredictionResponseBuilder
from modules.weather_inputs import WeatherInputService
from modules.weather_presentation import build_weather_presentation
from tests.test_hourly_weather import payload, NOW
from tests.test_scorer_missing_inputs import isolated_class


def pressure_text():
    return ('Date time,Automatic Weather Station,Mean Sea Level Pressure(hPa)\n'
            f"{NOW.strftime('%Y%m%d%H%M')},HK Observatory,1015.2\n")


def air_row(**changes):
    return dict(StationNameEN='Central/Western', type='General Stations', surrogate='false',
                DateTime=NOW.strftime('%Y-%m-%d %H:%M:%S'), aqhi='4', PM25='12.3',
                PM10='-', NO2='25', O3='80', **changes)


def air_text(rows):
    return 'var station_24_data = ' + json.dumps([rows]) + ';\nvar unrelated = [];'


class EnvironmentalTests(unittest.TestCase):
    def test_hko_header_station_units_and_duplicate_validation(self):
        reading = parse_pressure(pressure_text(), NOW)
        self.assertEqual(reading['value'], 1015.2)
        self.assertEqual(reading['unit'], 'hPa')
        self.assertEqual(datetime.fromisoformat(reading['observed_at']).utcoffset(), timedelta(hours=8))
        for text in (pressure_text().replace('hPa', 'Pa'), pressure_text().replace('1015.2', 'NaN'),
                     pressure_text().replace('HK Observatory', 'Other'),
                     pressure_text() + pressure_text().splitlines()[1] + '\n'):
            self.assertIsNone(parse_pressure(text, NOW))

    def test_actual_epd_json_assignment_and_components(self):
        reading = parse_air('\ufeff' + air_text([air_row()]), NOW)
        self.assertEqual(reading['aqhi'], 4)
        self.assertEqual(reading['components']['pm25'], 12.3)
        self.assertNotIn('pm10', reading['components'])
        self.assertEqual(reading['source_url'], AIR_URL)
        row = air_row(); row['aqhi'] = '10+'
        reading = parse_air(air_text([row]), NOW)
        self.assertEqual(reading['aqhi'], 11)
        self.assertEqual(reading['aqhi_display'], '10+')

    def test_epd_rejects_surrogates_roadside_invalid_missing_and_duplicates(self):
        for key, value in [('surrogate', 'true'), ('type', 'Roadside Stations'),
                           ('aqhi', '-'), ('aqhi', '4*'), ('aqhi', '11'), ('DateTime', 'invalid')]:
            row = air_row(); row[key] = value
            self.assertIsNone(parse_air(air_text([row]), NOW))
        for text in ('<html>outage</html>', 'var station_24_data = invalid;',
                     air_text([air_row(), air_row()])):
            self.assertIsNone(parse_air(text, NOW))

    def test_stale_and_future_readings_are_unavailable(self):
        reading = parse_pressure(pressure_text(), NOW)
        self.assertIsNotNone(fresh_observation(reading, NOW + timedelta(minutes=30), 30))
        self.assertIsNone(fresh_observation(reading, NOW + timedelta(minutes=31), 30))
        self.assertIsNone(fresh_observation(reading, NOW - timedelta(minutes=3), 30))
        air = parse_air(air_text([air_row()]), NOW)
        self.assertIsNone(fresh_observation(air, NOW + timedelta(minutes=121), 120))

    def test_client_keeps_dated_cache_on_outage_but_expired_cache_is_rejected(self):
        now = [NOW]
        response = Mock(content=pressure_text().encode())
        session = Mock(); session.get.return_value = response
        client = ObservationClient(PRESSURE_URL, parse_pressure, session, lambda: now[0])
        reading = client.fetch()
        self.assertEqual(reading['value'], 1015.2)
        now[0] += timedelta(minutes=31)
        session.get.side_effect = requests.Timeout()
        self.assertEqual(client.fetch(), reading)
        self.assertIsNone(fresh_observation(client.fetch(), now[0], 30))

    def service(self, model):
        values = {'weather': {}, 'forecast': {}, 'ninday': {}, 'wind': {}, 'warning': {}}
        extractor = Mock()
        extractor.extract_future_weather_data.side_effect = lambda weather, *_, **kwargs: deepcopy(weather)
        return WeatherInputService(lambda key, _: values[key], Mock(), Mock(), Mock(), Mock(), Mock(),
            extractor, fetch_cloud_forecast=lambda: model, now=lambda: NOW,
            fetch_pressure=lambda: parse_pressure(pressure_text(), NOW),
            fetch_air_quality=lambda: parse_air(air_text([air_row()]), NOW))

    def test_current_and_three_hour_sources_are_separate(self):
        service = self.service(payload())
        current = service.prepare(0)
        self.assertEqual(current.target_weather['pressure'], 1015.2)
        self.assertEqual(current.target_weather['air_quality']['aqhi'], 4)
        future = service.prepare(3)
        self.assertEqual(future.target_weather['pressure'], 1017)
        self.assertNotIn('pressure_observation', future.target_weather)
        self.assertNotIn('air_quality', future.target_weather)
        self.assertEqual(future.target_weather['air_quality_reference']['aqhi'], 4)
        # Missing model pressure must not reuse the current observation.
        data = payload(); del data['properties']['meta']['units']['air_pressure_at_sea_level']
        missing = self.service(data).prepare(3)
        self.assertNotIn('pressure', missing.target_weather)

    def test_future_scorer_uses_model_pressure_and_rejects_changed_target(self):
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        future = self.service(payload()).prepare(3)
        self.assertEqual(scorer._calculate_pressure_factor(future.target_weather), 8)
        self.assertIsNone(scorer._calculate_air_quality_factor(future.target_weather))
        future.target_weather['forecast_target_at'] = (NOW+timedelta(hours=4)).isoformat()
        self.assertIsNone(scorer._calculate_pressure_factor(future.target_weather))

    def test_real_extractor_does_not_drop_latest_air_reference(self):
        from forecast_extractor import ForecastExtractor
        service = self.service(payload())
        service._forecast_extractor = ForecastExtractor()
        future = service.prepare(3)
        self.assertEqual(future.target_weather['air_quality_reference']['aqhi'], 4)
        self.assertNotIn('air_quality', future.target_weather)

    def test_stale_official_observations_do_not_score(self):
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        stale = datetime.now(timezone.utc) - timedelta(days=1)
        air = parse_air(air_text([air_row()]), NOW)
        air.update(observed_at=stale.isoformat(), retrieved_at=stale.isoformat())
        pressure = parse_pressure(pressure_text(), NOW)
        pressure.update(observed_at=stale.isoformat(), retrieved_at=stale.isoformat())
        self.assertIsNone(scorer._calculate_air_quality_factor({'air_quality': air}))
        self.assertIsNone(scorer._calculate_pressure_factor({'pressure': 1015, 'pressure_observation': pressure}))

    def test_ui_explains_missing_future_aqhi_but_shows_latest_reference(self):
        future = self.service(payload()).prepare(3)
        factor = PredictionResponseBuilder(None, None, None)._factor('air_quality', None, 15, 'sunset', 3, future.target_weather)
        self.assertIsNone(factor['score'])
        self.assertEqual(factor['aqhi'], 4)
        self.assertEqual(factor['source_kind'], 'observation_reference')
        self.assertIn('不參與此時段計分', factor['description'])
        cards = build_weather_presentation(future.target_weather, future.observed_weather, 3,
                                           {'evaluated_at': (NOW+timedelta(hours=3)).isoformat()})['cards']
        pressure = next(card for card in cards if card['key'] == 'pressure')
        self.assertEqual(pressure['source_kind'], 'hourly_forecast')
        aqhi = next(card for card in cards if card['key'] == 'aqhi')
        self.assertEqual(aqhi['source_kind'], 'observed')
        self.assertIn('不參與未來計分', aqhi['note'])


if __name__ == '__main__':
    unittest.main()
