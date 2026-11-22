"""Exercise the real prediction orchestration without model or scheduler startup."""
import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from modules.prediction_presentation import HK_TIMEZONE, get_condition_level
from modules.prediction_response import PredictionResponseBuilder


def load_functions(path, names, scope):
    tree = ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    exec(compile(ast.Module(body=functions, type_ignores=[]), path, 'exec'), scope)
    return scope


class ScoreAdjustmentTests(unittest.TestCase):
    def test_legacy_photo_helpers_never_award_unvalidated_points(self):
        clock = Mock(now=Mock(return_value=datetime(2026, 11, 19, 18, 50)))
        scope = load_functions('app.py', {
            'apply_burnsky_photo_corrections', 'analyze_cloud_quality_for_burnsky',
            'analyze_atmospheric_conditions', 'analyze_color_potential'}, {'datetime': clock, 'print': Mock()})
        for weather in ({}, {'humidity': {'data': [{'value': 95}]}},
                        {'humidity': {'value': 60}, 'cloud': {'amount': 50, 'type': 'high'},
                         'visibility': {'value': 10}}):
            for mode in ('sunrise', 'sunset'):
                self.assertEqual(scope['apply_burnsky_photo_corrections'](95, weather, mode), 0)
        patterns = Mock(return_value={'successful_cases': [{'weather_conditions': {}}]})
        scope = load_functions('modules/photo_analyzer.py', {'apply_burnsky_photo_corrections'}, {
            'BURNSKY_PHOTO_CASES': {'unverified': {}}, 'analyze_photo_case_patterns': patterns,
            'extract_weather_conditions': Mock(return_value={}),
            'calculate_condition_similarity': Mock(return_value=1), 'print': Mock()})
        self.assertEqual(scope['apply_burnsky_photo_corrections'](95, {}, 'sunset'), 0)
        patterns.assert_not_called()

    def run_core(self, base, immediate=0, risk=0, mode='sunset'):
        generated = datetime(2026, 11, 19, 15, 50, tzinfo=HK_TIMEZONE)
        builder = PredictionResponseBuilder(get_condition_level,
            lambda _: {'sunrise': '06:38', 'sunset': '17:40'}, lambda value: value,
            now=lambda _: generated)
        weather = {'humidity': {'data': [{'value': 95}]}}
        unified = dict(final_score=base, traditional_normalized=base, traditional_score=base * 1.5,
            weighted_score=base, weights_used={'ml': 0, 'traditional': 1}, ml_score=None, analysis={},
            adjustments={'numeric_total': 0}, input_coverage={'missing_max_score': 0,
                'total_max_score': 150, 'weighted_percent': 100, 'missing_factors': []})
        predictor = Mock()
        predictor.predict_burnsky_intensity.side_effect = lambda value: {'score': value}
        predictor.predict_burnsky_colors.side_effect = lambda w, f, value: {'score': value}
        scope = dict(print=Mock(), flask_cache=Mock(get=Mock(return_value=None)),
            weather_input_service=Mock(prepare=Mock(return_value=SimpleNamespace(
                observed_weather=weather, target_weather=weather, forecast_data={}, ninday_data={}, warning_data={}))),
            require_prediction_inputs=Mock(return_value={'confidence': 'moderate', 'summary': 'test', 'limitations': []}),
            calculate_burnsky_score_unified=Mock(return_value=unified),
            warning_assessment_service=Mock(assess=Mock(return_value=(immediate, [], {}))),
            warning_risk_service=Mock(assess=Mock(return_value=(risk, []))),
            apply_burnsky_photo_corrections=Mock(return_value=28),
            warning_analysis_available=True, warning_analyzer=Mock(),
            prediction_response_builder=builder, assessment_store=Mock(save=Mock(return_value='snapshot')))
        load_functions('app.py', {'predict_burnsky_core'}, scope)
        with patch.dict('sys.modules', {'advanced_predictor': SimpleNamespace(
                AdvancedBurnskyPredictor=Mock(return_value=predictor))}):
            result = scope['predict_burnsky_core'](mode, 3)
        return result, scope

    def test_api_score_history_intensity_snapshot_and_cache_agree_after_warnings(self):
        for mode in ('sunrise', 'sunset'):
            for base, warning, risk, expected in ((95, 0, 0, 95), (95, 8, 8, 85), (3, 5, 0, 0)):
                with self.subTest(mode=mode, base=base, warning=warning, risk=risk):
                    result, scope = self.run_core(base, warning, risk, mode)
                    self.assertEqual(result['burnsky_score'], expected)
                    self.assertEqual(result['analysis_details']['score_breakdown']['final_score'], expected)
                    self.assertEqual(result['analysis_details']['score_breakdown']['photo_correction'], 0)
                    self.assertEqual(result['analysis_details']['score_breakdown']['photo_correction_status'],
                                     'disabled_unvalidated')
                    self.assertEqual(result['intensity_prediction']['score'], expected)
                    self.assertEqual(result['color_prediction']['score'], expected)
                    self.assertEqual(result['score_sensitivity']['upper'], expected)
                    self.assertEqual(scope['warning_analyzer'].record_prediction.call_args.args[0]['final_score'], expected)
                    scope['apply_burnsky_photo_corrections'].assert_not_called()
                    scope['assessment_store'].save.assert_called_once_with(result)
                    self.assertEqual(scope['flask_cache'].set.call_args.args[1], result)
                    self.assertEqual(result['scoring_method'], 'unified_v1.12_cloud_time_validation')


if __name__ == '__main__':
    unittest.main()
