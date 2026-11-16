"""Offline regression tests; run with unittest to avoid booting the production app."""

import unittest
import ast
from pathlib import Path
from datetime import datetime, timezone

from modules.prediction_presentation import (
    HK_TIMEZONE, build_prediction_timing, build_viewing_windows, get_condition_level,
)
from modules.prediction_response import PredictionResponseBuilder


def sun_times(date):
    # Distinct dates deliberately use different times to catch reusing today's event.
    return {'sunrise': '06:35' if date.day == 14 else '06:34',
            'sunset': '17:39' if date.day == 14 else '17:40', 'method': 'fixture'}


class PredictionTimingTests(unittest.TestCase):
    def test_solar_endpoint_uses_hong_kong_midnight_independently_of_host_timezone(self):
        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime.fromisoformat('2026-12-31T20:00:00+00:00').astimezone(tz)

        def solar(day):
            result = sun_times(day)
            for event in ('sunrise', 'sunset'):
                result[event + '_dt'] = datetime.fromisoformat(f"{day.isoformat()}T{result[event]}:00+08:00")
            return result

        tree = ast.parse(Path('app.py').read_text(encoding='utf-8-sig'))
        route = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'get_sun_times_api')
        route.decorator_list = []
        scope = {'datetime': Clock, 'HK_TIMEZONE': HK_TIMEZONE, 'build_viewing_windows': build_viewing_windows,
                 'get_seasonal_sun_times': solar, 'jsonify': lambda value: value}
        exec(compile(ast.Module(body=[route], type_ignores=[]), 'app.py', 'exec'), scope)
        result = scope['get_sun_times_api']()
        self.assertEqual(result['today']['date'], '2027-01-01')
        self.assertEqual(result['tomorrow']['date'], '2027-01-02')
        self.assertTrue(result['generated_at'].endswith('+08:00'))
        self.assertTrue(result['viewing_windows'][0]['event_at'].startswith('2027-01-01'))

    def test_viewing_windows_use_hong_kong_dates_and_include_tomorrow(self):
        windows = build_viewing_windows(datetime.fromisoformat('2026-11-13T20:00:00+00:00'), sun_times)
        self.assertEqual(len(windows), 4)
        self.assertEqual(windows[0]['event_at'], '2026-11-14T06:35:00+08:00')
        self.assertTrue(windows[2]['event_at'].startswith('2026-11-15'))
        self.assertEqual(windows[0]['window_start'], '2026-11-14T06:05:00+08:00')
        self.assertEqual(windows[0]['window_end'], '2026-11-14T07:05:00+08:00')

    def test_viewing_windows_roll_into_next_year_without_a_weather_score(self):
        windows = build_viewing_windows(datetime.fromisoformat('2026-12-31T23:00:00+08:00'), sun_times)
        self.assertTrue(windows[2]['event_at'].startswith('2027-01-01'))
        self.assertNotIn('burnsky_score', windows[2])

    def timing(self, at, event='sunrise', hours=0):
        return build_prediction_timing(datetime.fromisoformat(at), event, hours, sun_times)[0]

    def test_night_current_score_is_not_tomorrow_sunrise_forecast(self):
        timing = self.timing('2026-11-13T23:00:00+08:00')
        self.assertEqual(timing['evaluated_at'], '2026-11-13T23:00:00+08:00')
        self.assertEqual(timing['event_at'], '2026-11-13T06:34:00+08:00')
        self.assertEqual(timing['mode'], 'current')
        self.assertFalse(timing['within_reference_window'])

    def test_forecast_crossing_midnight_uses_target_dates_solar_times(self):
        timing = self.timing('2026-11-13T23:00:00+08:00', hours=6)
        self.assertEqual(timing['evaluated_at'], '2026-11-14T05:00:00+08:00')
        self.assertEqual(timing['event_at'], '2026-11-14T06:35:00+08:00')
        self.assertEqual(timing['mode'], 'forecast')
        self.assertFalse(timing['within_reference_window'])

    def test_utc_input_is_converted_before_selecting_solar_date(self):
        timing = self.timing('2026-11-13T20:00:00+00:00')
        self.assertEqual(timing['generated_at'], '2026-11-14T04:00:00+08:00')
        self.assertEqual(timing['event_at'], '2026-11-14T06:35:00+08:00')

    def test_year_rollover(self):
        timing = self.timing('2026-12-31T23:30:00+08:00', hours=2)
        self.assertEqual(timing['evaluated_at'], '2027-01-01T01:30:00+08:00')
        self.assertTrue(timing['event_at'].startswith('2027-01-01T'))

    def test_reference_window_boundaries_for_both_modes(self):
        for event, start, end in [('sunrise', '06:04', '07:04'), ('sunset', '17:10', '18:10')]:
            for time in (start, end):
                with self.subTest(event=event, time=time):
                    timing = self.timing(f'2026-11-13T{time}:00+08:00', event)
                    self.assertTrue(timing['within_reference_window'])
        self.assertFalse(self.timing('2026-11-13T18:10:01+08:00', 'sunset')['within_reference_window'])

    def test_all_score_thresholds_use_condition_labels(self):
        for score, expected in [(0, '條件很低'), (29, '條件很低'), (30, '條件偏低'),
                                (44, '條件偏低'), (45, '條件一般'), (64, '條件一般'),
                                (65, '條件良好'), (79, '條件良好'), (80, '條件極佳'), (100, '條件極佳')]:
            with self.subTest(score=score):
                self.assertEqual(get_condition_level(score), expected)

    def test_response_exposes_time_and_observation_age_without_probability(self):
        generated_at = datetime(2026, 11, 13, 23, tzinfo=HK_TIMEZONE)
        builder = PredictionResponseBuilder(get_condition_level, sun_times, lambda value: value,
                                            now=lambda tz: generated_at.astimezone(tz))
        result = builder.build(
            score=65, prediction_type='sunrise', advance_hours=6,
            unified_result={'analysis': {}, 'ml_score': 65, 'traditional_normalized': 65,
                            'traditional_score': 65, 'weighted_score': 65, 'weights_used': {}},
            intensity_prediction={}, color_prediction={}, target_weather={},
            observed_weather={'updateTime': '2026-11-13T22:40:00+08:00'}, forecast_data={},
            warning_data={}, warning_impact=0, warning_risk_score=0, warning_risk_warnings=[],
            active_warnings=[], warning_analysis={},
        )
        self.assertIsNone(result['probability'])
        self.assertEqual(result['score_type'], 'condition_index')
        self.assertEqual(result['burnsky_score'], 65)
        self.assertEqual(result['prediction_level'], '條件良好')
        self.assertEqual(result['weather_updated_at'], '2026-11-13T22:40:00+08:00')
        self.assertIn('cards', result['weather_presentation'])
        air = result['analysis_details']['air_quality_factor']
        self.assertIsNone(air['aqhi'])
        self.assertIsNone(air['pm25'])
        self.assertEqual(air['source_kind'], 'unavailable')
        self.assertEqual(result['sun_times']['date'], '2026-11-14')
        factor = result['analysis_details']['time_factor']
        self.assertEqual(factor['target_time'], '06:35')
        self.assertEqual(factor['evaluated_at'], '2026-11-14T05:00:00+08:00')
        self.assertEqual(result['prediction_timing']['generated_at'], generated_at.isoformat())


if __name__ == '__main__':
    unittest.main()
