"""Offline checks for missing inputs, score gating and prediction HTTP errors."""
import ast
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from flask import Flask
from modules.prediction_quality import (InsufficientPredictionData, assess_prediction_quality,
                                        highest_rainfall, require_prediction_inputs)
from modules.prediction_routes import create_prediction_blueprint


def weather():
    return {'temperature': {'data': [{'place': '香港天文台', 'value': 25}]},
            'humidity': {'data': [{'place': '香港天文台', 'value': 60}]},
            'rainfall': {'data': [{'max': 0}]}, 'uvindex': {'data': [{'value': 0}]}}


class PredictionQualityTests(unittest.TestCase):
    def test_three_hour_forecast_is_usable_without_optional_readings(self):
        data = weather()
        del data['uvindex']
        result = require_prediction_inputs(data, data, {'forecastDesc': '多雲'}, 3)
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['score_usable'])
        self.assertEqual(result['confidence'], 'moderate')
        text = ''.join(result['limitations'])
        for label in ('空氣品質', '氣壓', '風速', '間接參考'):
            self.assertIn(label, text)
        self.assertIn('UV因子缺少', text)

    def test_missing_rain_or_longer_horizon_reduces_confidence_without_hiding_score(self):
        for hours, rain in ((3, False), (6, True)):
            data = weather()
            if not rain:
                del data['rainfall']
            result = require_prediction_inputs(data, data, {'forecastDesc': '多雲'}, hours)
            self.assertEqual(result['status'], 'limited')
            self.assertTrue(result['score_usable'])
            self.assertEqual(result['confidence'], 'low')
            self.assertFalse(result['allow_high_score_notification'])

    def test_original_missing_data_cannot_be_concealed_by_forecast_defaults(self):
        with self.assertRaises(InsufficientPredictionData) as error:
            require_prediction_inputs(weather(), {}, {'forecastDesc': '天晴'}, 2)
        self.assertIn('天文台溫度', error.exception.quality['missing_required'])

    def test_invalid_values_and_blank_cloud_text_are_missing(self):
        for value in (True, float('nan'), '25', None):
            data = weather()
            data['temperature']['data'][0]['value'] = value
            result = assess_prediction_quality(data, data, {'forecastDesc': ' '})
            self.assertFalse(result['score_usable'])
            self.assertEqual(len(result['missing_required']), 2)

    def test_zero_readings_are_valid_and_missing_rain_is_not_zero(self):
        data = weather()
        data['humidity']['data'][0]['value'] = 0
        self.assertTrue(require_prediction_inputs(data, data, {'forecastDesc': '多雲'})['score_usable'])
        self.assertEqual(highest_rainfall(data), 0)
        self.assertIsNone(highest_rainfall({'rainfall': {'data': []}}))
        self.assertEqual(highest_rainfall({'rainfall': {'data': [{'max': 2}, {'max': 3}]}}), 3)

    def test_real_core_stops_before_scoring_and_history_write(self):
        tree = ast.parse(Path('app.py').read_text(encoding='utf-8-sig'))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'predict_burnsky_core')
        scorer, recorder = Mock(), Mock()
        scope = {'print': Mock(), 'flask_cache': Mock(get=Mock(return_value=None)),
                 'weather_input_service': Mock(prepare=Mock(return_value=SimpleNamespace(
                     observed_weather={}, target_weather=weather(), forecast_data={'forecastDesc': '多雲'},
                     ninday_data={}, warning_data={}))),
                 'require_prediction_inputs': require_prediction_inputs,
                 'calculate_burnsky_score_unified': scorer, 'warning_analyzer': recorder}
        exec(compile(ast.Module(body=[function], type_ignores=[]), 'app.py', 'exec'), scope)
        with self.assertRaises(InsufficientPredictionData):
            scope['predict_burnsky_core']()
        scorer.assert_not_called()
        recorder.record_prediction.assert_not_called()

    def test_all_prediction_routes_return_actionable_503(self):
        class NoCache:
            def cached(self, **kwargs):
                return lambda fn: fn
        class NoLimiter:
            def limit(self, *args):
                return lambda fn: fn
        def predict(*args):
            require_prediction_inputs({}, {}, {})
        app = Flask(__name__)
        app.register_blueprint(create_prediction_blueprint(predict, NoLimiter(), NoCache()))
        for url in ('/predict', '/predict/sunrise', '/predict/sunset'):
            response = app.test_client().get(url)
            self.assertEqual(response.status_code, 503)
            self.assertIsNone(response.json['burnsky_score'])
            self.assertEqual(response.json['error'], 'insufficient_prediction_data')
            self.assertIn('主要資料不足', response.json['message'])

    def test_scorer_uses_rain_max_and_never_awards_missing_rain_full_points(self):
        tree = ast.parse(Path('unified_scorer.py').read_text(encoding='utf-8-sig'))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'UnifiedBurnskyScorer')
        method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '_calculate_visibility_factor')
        scope = {'highest_rainfall': highest_rainfall}
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'unified_scorer.py', 'exec'), scope)
        score = lambda data: scope['_calculate_visibility_factor'](None, data)
        self.assertIsNone(score({'rainfall': {'data': []}}))
        self.assertEqual(score(weather()), 20)
        self.assertEqual(score({'rainfall': {'data': [{'max': 25}]}}), 1)

    def test_ml_fallback_is_explicit_and_does_not_leak_between_calls(self):
        tree = ast.parse(Path('unified_scorer.py').read_text(encoding='utf-8-sig'))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'UnifiedBurnskyScorer')
        method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '_get_ml_score')
        scope = {'math': math}
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'unified_scorer.py', 'exec'), scope)
        predictor = Mock()
        scorer = SimpleNamespace(advanced_predictor=predictor)
        diagnostics = {}
        self.assertIsNone(scope['_get_ml_score'](scorer, {}, {}, diagnostics))
        self.assertEqual(diagnostics['ml_score_source'], 'unavailable')
        predictor.predict_ml.assert_not_called()



if __name__ == '__main__':
    unittest.main()
