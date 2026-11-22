import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from modules import history


class HistoryReportingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = str(Path(self.temp.name) / 'history.db')
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('CREATE TABLE prediction_history (timestamp TEXT, prediction_type TEXT, score REAL)')
            conn.commit()
        self.app = Flask(__name__, template_folder=str(Path(__file__).resolve().parents[1] / 'templates'))
        self.app.register_blueprint(history.history_bp)
        self.client = self.app.test_client()
        self.db_patch = patch.object(history, 'PREDICTION_HISTORY_DB', self.db)
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.feedback_patch = patch.object(history, 'calculate_real_accuracy', return_value={'has_data': False, 'feedback_count': 0})
        self.feedback_patch.start()
        self.addCleanup(self.feedback_patch.stop)

    def test_high_prediction_scores_do_not_claim_actual_sky_or_best_shooting_time(self):
        insights = history.generate_burnsky_insights((1, 90, 90, 90, 1), {}, [{'hour': 1, 'avg_score': 90, 'count': 1}])
        text = ' '.join(insights)
        self.assertNotIn('出現極佳燒天', text)
        self.assertIn('預測產生', text)
        self.assertIn('並非', text)

    def test_utc_records_group_into_hong_kong_generation_hour_and_date(self):
        timestamp = datetime.now(timezone.utc).replace(hour=16, minute=5, second=0).strftime('%Y-%m-%d %H:%M:%S')
        # Use yesterday so this stays in the requested interval in every timezone.
        timestamp = (datetime.fromisoformat(timestamp) - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        with closing(sqlite3.connect(self.db)) as conn:
            conn.execute('INSERT INTO prediction_history VALUES (?, ?, ?)', (timestamp, 'sunset', 90))
            conn.commit()
        data = self.client.get('/api/burnsky/history').get_json()
        self.assertEqual(data['best_hours'][0]['hour'], 0)
        expected_date = (datetime.fromisoformat(timestamp) + timedelta(hours=8)).strftime('%Y-%m-%d')
        self.assertEqual(data['daily_trends'][0]['date'], expected_date)
        self.assertEqual(data['summary']['total_predictions'], 1)
        self.assertEqual(data['time_basis'], 'prediction_generated_at_hong_kong')

    def test_empty_history_keeps_zero_separate_from_unavailable_feedback(self):
        data = self.client.get('/api/burnsky/history').get_json()
        self.assertEqual(data['summary']['total_predictions'], 0)
        self.assertFalse(data['verified_accuracy']['has_data'])
        self.assertEqual(data['best_hours'], [])

    def test_history_page_has_shared_theme_and_link_back_to_three_hour_verification(self):
        response = self.client.get('/prediction-history')
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('site-page', text)
        self.assertIn('/#verificationSection', text)
        self.assertNotIn('最佳拍攝時段', text)


if __name__ == '__main__':
    unittest.main()
