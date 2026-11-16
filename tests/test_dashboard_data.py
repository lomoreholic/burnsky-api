"""Exercise production handlers without starting the app, scheduler or ML system."""
import ast
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from flask import Flask, jsonify, request


ROOT = Path(__file__).resolve().parents[1]
HANDLERS = (
    'burnsky_dashboard_data', 'get_overview_charts',
    'get_warning_category_distribution', 'get_warning_timeline_simple',
    'get_warning_insights',
)


class DashboardDataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'history.db')
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute('CREATE TABLE prediction_history (timestamp TEXT, score REAL, factors TEXT, warnings TEXT)')
            conn.execute('CREATE TABLE warning_records (timestamp TEXT)')
            conn.commit()
        self.app = Flask(__name__)
        self.namespace = {
            'sqlite3': sqlite3, 'datetime': datetime, 'timedelta': timedelta,
            'jsonify': jsonify, 'request': request,
            'PREDICTION_HISTORY_DB': self.path,
            'calculate_real_accuracy': lambda: {'has_data': False, 'feedback_count': 0},
            'warning_analysis_available': False, 'warning_analyzer': None,
        }
        tree = ast.parse((ROOT / 'app.py').read_text(encoding='utf-8'))
        nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in HANDLERS]
        self.assertEqual(len(nodes), len(HANDLERS))
        for node in nodes:
            node.decorator_list = []
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(ROOT / 'app.py'), 'exec'), self.namespace)

    def call(self, name):
        with self.app.test_request_context('/'):
            result = self.namespace[name]()
            response, status = result if isinstance(result, tuple) else (result, 200)
            return response.get_json(), status

    def add_prediction(self, score, timestamp=None):
        timestamp = timestamp or datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute('INSERT INTO prediction_history VALUES (?, ?, ?, ?)', (timestamp, score, '{}', '{}'))
            conn.commit()

    def test_empty_history_does_not_invent_a_season_time_or_records(self):
        data, status = self.call('burnsky_dashboard_data')
        self.assertEqual(status, 200)
        self.assertFalse(data['has_data'])
        self.assertEqual(data['statistics']['total_warnings'], 0)
        self.assertIsNone(data['time_pattern']['peak_hour'])
        self.assertEqual(data['high_impact_warnings'], [])
        self.assertIn('暫無', data['insights']['peak_time'])
        self.assertNotIn('機率最高', data['insights']['seasonal'])
        self.assertIsNone(data['accuracy']['percentage'])

    def test_all_low_scores_are_counted_including_zero_and_below_thirty(self):
        for score in (0, 20, 42, 60, 85):
            self.add_prediction(score)
        data, status = self.call('burnsky_dashboard_data')
        self.assertEqual(status, 200)
        self.assertEqual(data['statistics']['total_warnings'], 5)
        self.assertEqual(data['statistics']['low_severity'], 3)
        self.assertEqual(sum(month['total_count'] for month in data['monthly_data']), 5)
        self.assertEqual(len(data['high_impact_warnings']), 1)
        self.assertNotIn('覆蓋全港', data['high_impact_warnings'][0]['message'])
        self.assertNotIn('建議', data['high_impact_warnings'][0]['message'])

    def test_record_time_is_converted_from_sqlite_utc_to_hong_kong(self):
        self.add_prediction(95, '2026-11-14 15:00:00')
        data, status = self.call('burnsky_dashboard_data')
        self.assertEqual(status, 200)
        self.assertEqual(data['high_impact_warnings'][0]['timestamp'], '2026-11-14T23:00:00+08:00')
        self.assertEqual(data['time_pattern']['peak_hour'], '23:00-00:00')
        self.assertIn('並非最佳拍攝時間', data['insights']['peak_time'])

    def test_medium_scores_do_not_generate_high_score_time_insights(self):
        self.add_prediction(60)
        data, status = self.call('burnsky_dashboard_data')
        self.assertEqual(status, 200)
        self.assertTrue(data['has_data'])
        self.assertIsNone(data['time_pattern']['peak_hour'])
        self.assertEqual(data['high_impact_warnings'], [])

    def test_database_failure_returns_503_without_fake_statistics(self):
        self.namespace['PREDICTION_HISTORY_DB'] = str(Path(self.temp.name) / 'missing' / 'db')
        data, status = self.call('burnsky_dashboard_data')
        self.assertEqual(status, 503)
        self.assertEqual(data['status'], 'error')
        self.assertIsNone(data['statistics'])
        self.assertIsNone(data['accuracy'])
        self.assertEqual(data['high_impact_warnings'], [])

    def test_unavailable_warning_analysis_never_returns_demo_success(self):
        for name in HANDLERS[1:]:
            with self.subTest(handler=name):
                data, status = self.call(name)
                self.assertEqual(status, 503)
                self.assertEqual(data['data_source'], 'unavailable')

    def test_empty_warning_history_does_not_recurse_or_invent_categories(self):
        self.namespace['warning_analysis_available'] = True
        self.namespace['warning_analyzer'] = SimpleNamespace(
            analyze_warning_patterns=lambda days: {'total_warnings': 0, 'category_distribution': {}},
            db_path=self.path,
        )
        for name in ('get_overview_charts', 'get_warning_category_distribution'):
            with self.subTest(handler=name):
                data, status = self.call(name)
                self.assertEqual(status, 200)
                self.assertFalse(data['has_data'])
                self.assertNotIn('example', data['data_source'])

    def test_daily_warning_counts_come_from_recorded_dates(self):
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        with closing(sqlite3.connect(self.path)) as conn:
            conn.executemany('INSERT INTO warning_records VALUES (?)', [
                (today.isoformat() + ' 12:00:00',), (today.isoformat() + ' 13:00:00',),
                (yesterday.isoformat() + ' 18:00:00',),
            ])
            conn.commit()
        self.namespace['warning_analysis_available'] = True
        self.namespace['warning_analyzer'] = SimpleNamespace(db_path=self.path)
        data, status = self.call('get_warning_timeline_simple')
        self.assertEqual(status, 200)
        self.assertEqual(data['data'][-2:], [1, 2])
        self.assertEqual(sum(data['data']), 3)


if __name__ == '__main__':
    unittest.main()
