import ast
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from flask import Flask, jsonify, request
from PIL import Image

from hko_webcam_fetcher import HKOWebcamFetcher
from modules.prediction_comparison import AssessmentStore, build_comparison, image_observation
from modules.prediction_presentation import HK_TIMEZONE


NOW = datetime(2026, 11, 16, 6, 36, tzinfo=HK_TIMEZONE)

def assessment():
    return {'burnsky_score': 60, 'prediction_type': 'sunrise', 'advance_hours': 5,
            'scoring_method': 'unified_v1.3_no_default_scores',
            'data_quality': {'status': 'limited', 'score_usable': True},
            'prediction_timing': {'event_type': 'sunrise', 'mode': 'forecast',
                'generated_at': (NOW - timedelta(hours=5)).isoformat(),
                'evaluated_at': NOW.isoformat(), 'window_start': (NOW-timedelta(minutes=30)).isoformat(),
                'window_end': (NOW+timedelta(minutes=30)).isoformat()}}


def camera(updated=NOW):
    return {'location_id': 'east', 'location_name': '東面測試攝影機', 'direction': 'East',
            'source_updated_at': updated.isoformat() if updated else None,
            'retrieved_at': NOW.isoformat(), 'image': Image.new('RGB', (30, 30), (200, 120, 60))}


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.fetcher = SimpleNamespace(WEBCAM_LOCATIONS={'east': {'direction': 'East'}, 'west': {'direction': 'West'}},
                                      fetch_multiple_webcams=Mock(return_value={'east': camera()}))

    def test_original_snapshot_is_saved_and_not_recomputed(self):
        with TemporaryDirectory() as folder:
            store = AssessmentStore(str(Path(folder)/'history.db'))
            original = assessment()
            identifier = store.save(original)
            self.assertEqual(store.save(original), identifier)
            original['burnsky_score'] = 99
            self.assertEqual(store.get(identifier)['burnsky_score'], 60)
            self.assertNotEqual(store.save(original), identifier)
            self.assertIsNone(store.get('missing'))

    def test_future_and_expired_windows_never_fetch_current_images(self):
        for now, state in ((NOW-timedelta(hours=2), 'pending'), (NOW+timedelta(hours=2), 'ended')):
            result = build_comparison(assessment(), self.fetcher, now)
            self.assertEqual(result['comparison_state'], state)
            self.assertEqual(result['observations'], [])
        self.fetcher.fetch_multiple_webcams.assert_not_called()

    def test_out_of_window_score_cannot_become_sunrise_validation(self):
        data = assessment()
        data['prediction_timing']['evaluated_at'] = (NOW-timedelta(hours=2)).isoformat()
        self.assertEqual(build_comparison(data, self.fetcher, NOW)['comparison_state'], 'out_of_window')
        self.fetcher.fetch_multiple_webcams.assert_not_called()

    def test_direction_and_time_matched_reference_has_no_accuracy(self):
        result = build_comparison(assessment(), self.fetcher, NOW)
        self.fetcher.fetch_multiple_webcams.assert_called_once_with(['east'])
        self.assertEqual(result['comparison_state'], 'aligned_reference')
        self.assertIsNone(result['accuracy'])
        self.assertIsNone(result['score_difference'])
        self.assertIsNone(result['observations'][0]['captured_at'])
        self.assertEqual(result['observations'][0]['warm_pixel_percent'], 100)
        self.assertTrue(result['observations'][0]['image_data_url'].startswith('data:image/jpeg;base64,'))

    def test_missing_stale_future_or_different_time_images_are_unmatched(self):
        for updated in (None, NOW-timedelta(minutes=20), NOW+timedelta(minutes=1), NOW-timedelta(days=1)):
            self.fetcher.fetch_multiple_webcams.return_value = {'east': camera(updated)}
            result = build_comparison(assessment(), self.fetcher, NOW)
            self.assertEqual(result['comparison_state'], 'unmatched')
            self.assertFalse(result['observations'][0]['aligned_reference'])

    def test_dark_image_is_unknown_not_zero_burnsky(self):
        data = camera()
        data['image'] = Image.new('RGB', (20,20), (0,0,0))
        result = image_observation(data, NOW, assessment()['prediction_timing'])
        self.assertIsNone(result['warm_pixel_percent'])
        self.assertIn('無法判讀', result['description'])

    def test_current_assessment_can_reference_a_recent_image(self):
        data = assessment()
        data['prediction_timing'].update(mode='current', generated_at=NOW.isoformat())
        self.assertTrue(image_observation(camera(NOW-timedelta(minutes=5)), NOW, data['prediction_timing'])['aligned_reference'])

    def test_no_camera_data_is_unmatched_not_good_agreement(self):
        self.fetcher.fetch_multiple_webcams.return_value = {}
        result = build_comparison(assessment(), self.fetcher, NOW)
        self.assertEqual(result['comparison_state'], 'unmatched')
        self.assertIsNone(result['score_difference'])

    def test_fetcher_never_labels_retrieval_as_source_update(self):
        fetcher = HKOWebcamFetcher()
        fetcher.retry_attempts = 1
        image = Image.effect_noise((100,100), 60).convert('RGB')
        buffer = BytesIO(); image.save(buffer, format='JPEG')
        response = Mock(content=buffer.getvalue(), headers={})
        fetcher.session.get = Mock(return_value=response)
        for headers, expected in (({}, None), ({'Last-Modified': 'invalid'}, None),
                                  ({'Last-Modified': 'Sun, 15 Nov 2026 22:36:00 GMT'}, NOW.isoformat())):
            response.headers = headers
            result = fetcher.fetch_webcam_image('HK_HKO')
            self.assertEqual(result['source_updated_at'], expected)
            self.assertIsNotNone(result['retrieved_at'])

    def test_route_uses_selected_snapshot_and_validates_missing_and_failure(self):
        tree = ast.parse(Path('app.py').read_text(encoding='utf-8-sig'))
        method = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'cross_check_prediction_with_webcam')
        method.decorator_list = []
        store = Mock(get=Mock(return_value=assessment()))
        compare = Mock(return_value={'status': 'success'})
        scope = {'request': request, 'jsonify': jsonify, 'assessment_store': store, 'build_comparison': compare,
                 'datetime': datetime, 'HK_TIMEZONE': HK_TIMEZONE, 'webcam_monitor': SimpleNamespace(fetcher=self.fetcher)}
        exec(compile(ast.Module(body=[method], type_ignores=[]), 'app.py', 'exec'), scope)
        app = Flask(__name__)
        app.add_url_rule('/comparison', view_func=scope['cross_check_prediction_with_webcam'])
        client = app.test_client()
        self.assertEqual(client.get('/comparison').status_code, 400)
        identifier = 'a'*64
        self.assertEqual(client.get('/comparison?assessment_id='+identifier).status_code, 200)
        store.get.assert_called_once_with(identifier)
        self.assertEqual(compare.call_args.args[0], assessment())
        store.get.return_value = None
        self.assertEqual(client.get('/comparison?assessment_id='+identifier).status_code, 404)
        store.get.side_effect = RuntimeError('unavailable')
        self.assertEqual(client.get('/comparison?assessment_id='+identifier).status_code, 503)


if __name__ == '__main__':
    unittest.main()
