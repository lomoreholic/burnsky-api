"""Exercise actual scorer methods without importing model/scheduler side effects."""
import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from modules.prediction_quality import highest_rainfall, station_value
from modules.prediction_response import PredictionResponseBuilder
from modules.weather_presentation import number


def isolated_class(file, name):
    tree = ast.parse(Path(file).read_text(encoding='utf-8-sig'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)
    scope = {'datetime': datetime, 'number': number, 'highest_rainfall': highest_rainfall,
             'station_value': station_value, 'AdvancedBurnskyPredictor': Mock,
             'AirQualityFetcher': Mock}
    exec(compile(ast.Module(body=[cls], type_ignores=[]), file, 'exec'), scope)
    return scope[name]


def readings():
    return {'temperature': {'data': [{'place': '香港天文台', 'value': 28}]},
            'humidity': {'data': [{'place': '香港天文台', 'value': 60}]},
            'rainfall': {'data': [{'max': 0}]}, 'uvindex': {'data': [{'value': 0}]},
            'wind': {'speed': 10}, 'pressure': 1015, 'air_quality': {'aqhi': 3}}


class MissingScoreTests(unittest.TestCase):
    def setUp(self):
        self.scorer = isolated_class('unified_scorer.py', 'UnifiedBurnskyScorer')()
        self.scorer.advanced_predictor.calculate_advanced_time_factor.return_value = {'score': 18}
        self.scorer.advanced_predictor.predict_burnsky_intensity.return_value = {}
        self.scorer.advanced_predictor.predict_burnsky_colors.return_value = {}

    def calculate(self, data):
        result = self.scorer.calculate_unified_score(data, {'forecastDesc': '多雲'}, {}, use_seasonal_adjustment=False)
        self.assertNotIn('error', result)
        return result

    def test_missing_optional_factors_add_no_points_and_do_not_raise_score(self):
        full = self.calculate(readings())
        for key in ('pressure', 'uvindex', 'rainfall', 'wind', 'air_quality'):
            data = readings()
            del data[key]
            partial = self.calculate(data)
            self.assertLessEqual(partial['final_score'], full['final_score'])
            self.assertLess(partial['input_coverage']['weighted_percent'], 100)
            self.assertEqual(partial['input_coverage']['total_max_score'], 150)
            self.assertAlmostEqual(partial['traditional_normalized'], partial['traditional_score'] / 150 * 100)
        self.assertEqual(full['input_coverage']['weighted_percent'], 100)

    def test_absent_and_invalid_readings_are_unavailable(self):
        for method in ('temperature', 'humidity', 'visibility', 'pressure', 'uv', 'wind', 'air_quality'):
            self.assertIsNone(getattr(self.scorer, '_calculate_' + method + '_factor')({}))
        for value in (None, True, '5', float('nan'), float('inf'), -1):
            self.assertIsNone(self.scorer._calculate_uv_factor({'uvindex': {'data': [{'value': value}]}}))
            self.assertIsNone(self.scorer._calculate_wind_factor({'wind': {'speed': value}}))
        self.assertIsNone(self.scorer._calculate_cloud_factor({'forecastDesc': '未有描述'}))
        self.assertIsNone(self.scorer._calculate_wind_factor({'wind': {'speed_kmh_min': 6, 'speed_kmh_max': 12}}))

    def test_valid_zero_does_not_become_missing(self):
        self.assertEqual(self.scorer._calculate_uv_factor(readings()), .5)
        self.assertEqual(self.scorer._calculate_visibility_factor(readings()), 20)
        self.assertEqual(self.scorer._calculate_wind_factor({'wind': {'speed': 0}}), 5)

    def test_ml_never_blends_default_50_or_runs_synthetic_model(self):
        result = self.calculate(readings())
        self.assertIsNone(result['ml_score'])
        self.assertEqual(result['weights_used'], {'traditional': 1, 'ml': 0})
        self.assertEqual(result['final_score'], result['traditional_normalized'])
        self.scorer.advanced_predictor.predict_ml.assert_not_called()
        self.scorer.advanced_predictor.analyze_cloud_thickness_and_color_visibility.assert_not_called()

    def test_response_keeps_missing_score_null(self):
        builder = PredictionResponseBuilder(None, None, None)
        factor = builder._factor('pressure', None, 10, 'sunset', 0, {})
        self.assertIsNone(factor['score'])
        self.assertFalse(factor['available'])
        self.assertIn('不參與', factor['description'])

    def test_direct_scorer_failure_is_not_a_zero_score(self):
        result = self.scorer.calculate_unified_score({}, {'forecastDesc': '多雲'}, {})
        self.assertIn('error', result)
        self.assertIsNone(result['final_score'])

    def test_direct_ml_requires_features_before_training(self):
        cls = isolated_class('advanced_predictor.py', 'AdvancedBurnskyPredictor')
        model = object.__new__(cls)
        model.cloud_types = {'多雲': {}}
        model.train_models = Mock()
        with self.assertRaises(ValueError):
            model.predict_ml({}, {})
        model.train_models.assert_not_called()
        data = readings()
        data['temperature']['data'][0]['value'] = 0
        data['wind'].update(speed_beaufort_min=0, speed_beaufort_max=0)
        model.calculate_time_factor_advanced = Mock(return_value={'score': 0})
        model.analyze_cloud_types = Mock(return_value={'score': 14})
        features = model.extract_features(data, {'forecastDesc': '多雲'})
        self.assertEqual(features['temperature'], 0)
        self.assertEqual(features['uv_index'], 0)
        self.assertEqual(features['rainfall'], 0)
        self.assertEqual(features['wind_speed'], 0)
        data['rainfall'] = {'data': [{'value': 4}]}
        self.assertEqual(model.extract_features(data, {'forecastDesc': '多雲'})['rainfall'], 4)
        for key in ('temperature', 'humidity', 'uvindex', 'rainfall', 'wind'):
            incomplete = dict(data)
            del incomplete[key]
            with self.assertRaises(ValueError):
                model.extract_features(incomplete, {'forecastDesc': '多雲'})


if __name__ == '__main__':
    unittest.main()
