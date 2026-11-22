"""Score the selected forecast instant even when providers return much later."""
from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import Mock

import pytz

from test_scorer_missing_inputs import isolated_class, readings


class ClockMeta(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, datetime)


class Clock(datetime, metaclass=ClockMeta):
    instant = None

    @classmethod
    def now(cls, tz=None):
        return cls.instant.astimezone(tz) if tz else cls.instant.replace(tzinfo=None)


class TargetTimeTests(unittest.TestCase):
    def predictor(self, clock):
        cls = isolated_class('advanced_predictor.py', 'AdvancedBurnskyPredictor')
        cls.calculate_advanced_time_factor.__globals__.update(
            datetime=clock, timedelta=timedelta, pytz=pytz)
        model = object.__new__(cls)
        def solar(day):
            return dict(sunrise=datetime.combine(day, datetime.min.time()).replace(hour=7),
                        sunrise_str='07:00',
                        sunset=datetime.combine(day, datetime.min.time()).replace(hour=18),
                        sunset_str='18:00')
        model.get_sunrise_info = Mock(side_effect=solar)
        model.get_sunset_info = Mock(side_effect=solar)
        return model

    def test_explicit_target_survives_latency_at_scoring_boundary(self):
        target = datetime(2026, 12, 1, 9, 29, tzinfo=timezone.utc)  # 17:29 HKT
        Clock.instant = target + timedelta(minutes=2) - timedelta(hours=3)
        model = self.predictor(Clock)
        result = model.calculate_advanced_time_factor('sunset', 3, evaluated_at=target)
        self.assertEqual(result['score'], 15)  # 31 minutes before sunset, not 29.
        self.assertEqual(result['prediction_time'], '17:29')
        self.assertEqual(datetime.fromisoformat(result['evaluated_at']), target)
        self.assertEqual(result['time_diff_minutes'], 31)
        Clock.instant += timedelta(minutes=10)
        self.assertEqual(model.calculate_advanced_time_factor('sunset', 3, evaluated_at=target)['score'], 15)

    def test_sunrise_uses_target_hong_kong_date_across_new_year(self):
        target = datetime(2026, 12, 31, 22, 30, tzinfo=timezone.utc)
        model = self.predictor(datetime)
        result = model.calculate_advanced_time_factor('sunrise', 3, evaluated_at=target)
        model.get_sunrise_info.assert_called_once_with(datetime(2027, 1, 1).date())
        self.assertEqual(result['score'], 18)
        self.assertEqual(result['prediction_time'], '06:30')

    def test_legacy_time_call_still_adds_requested_lead(self):
        Clock.instant = datetime(2026, 12, 1, 14, 30, tzinfo=timezone.utc)
        result = self.predictor(Clock).calculate_advanced_time_factor('sunrise', 3)
        self.assertEqual(result['prediction_time'], '01:30')

    def test_scorer_uses_same_target_for_time_and_season(self):
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        scorer.advanced_predictor.calculate_advanced_time_factor.return_value = {'score': 18}
        scorer.advanced_predictor.predict_burnsky_intensity.return_value = {}
        scorer.advanced_predictor.predict_burnsky_colors.return_value = {}
        for instant, adjustment in (('2026-05-31T16:30:00+00:00', 3),
                                    ('2026-11-30T16:30:00+00:00', -2),
                                    ('2026-08-31T16:30:00+00:00', 0)):
            with self.subTest(instant=instant):
                data = dict(readings(), forecast_target_at=instant)
                result = scorer.calculate_unified_score(data, {'forecastDesc': '多雲'}, {}, advance_hours=3)
                self.assertNotIn('error', result)
                self.assertEqual(result['adjustments']['numeric_total'], adjustment)
                evaluated = datetime.fromisoformat(instant)
                self.assertEqual(datetime.fromisoformat(result['prediction_info']['evaluated_at']), evaluated)
                scorer.advanced_predictor.calculate_advanced_time_factor.assert_called_with(
                    prediction_type='sunset', advance_hours=3, evaluated_at=evaluated)

    def test_invalid_explicit_targets_do_not_fall_back_to_another_time(self):
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        for invalid in (None, '', 'not-a-date', '2026-12-01T17:30:00', 123):
            result = scorer.calculate_unified_score(dict(readings(), forecast_target_at=invalid), {}, {})
            self.assertIsNone(result['final_score'])
            self.assertIn('error', result)
            self.assertIn('forecast_target_at', result['error'])
        scorer.advanced_predictor.calculate_advanced_time_factor.assert_not_called()
        model = self.predictor(datetime)
        with self.assertRaises(ValueError):
            model.calculate_advanced_time_factor(evaluated_at=datetime(2026, 12, 1))

    def test_real_time_factor_and_season_share_selected_target_in_scorer(self):
        Clock.instant = datetime(2026, 11, 30, 12, 0, tzinfo=timezone.utc)
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        model = self.predictor(Clock)
        model.predict_burnsky_intensity = Mock(return_value={})
        model.predict_burnsky_colors = Mock(return_value={})
        scorer.advanced_predictor = model
        data = dict(readings(), forecast_target_at='2026-11-30T22:29:00+00:00')
        result = scorer.calculate_unified_score(data, {'forecastDesc': '多雲'}, {},
                                                prediction_type='sunrise', advance_hours=3)
        self.assertNotIn('error', result)
        self.assertEqual(result['factor_scores']['time'], 15)
        self.assertEqual(result['time_factor']['prediction_time'], '06:29')
        self.assertEqual(result['adjustments']['numeric_total'], -2)
        self.assertEqual(datetime.fromisoformat(result['prediction_info']['evaluated_at']),
                         datetime.fromisoformat(result['time_factor']['evaluated_at']))

    def test_direct_scorer_call_without_metadata_still_resolves_one_aware_target(self):
        Clock.instant = datetime(2026, 11, 30, 15, 30, tzinfo=timezone.utc)
        scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        scorer.calculate_unified_score.__globals__['datetime'] = Clock
        scorer.advanced_predictor.calculate_advanced_time_factor.return_value = {'score': 18}
        scorer.advanced_predictor.predict_burnsky_intensity.return_value = {}
        scorer.advanced_predictor.predict_burnsky_colors.return_value = {}
        result = scorer.calculate_unified_score(readings(), {'forecastDesc': '多雲'}, {}, advance_hours=3)
        self.assertNotIn('error', result)
        self.assertEqual(datetime.fromisoformat(result['prediction_info']['evaluated_at']),
                         Clock.instant + timedelta(hours=3))
        self.assertEqual(result['adjustments']['numeric_total'], -2)


if __name__ == '__main__':
    unittest.main()
