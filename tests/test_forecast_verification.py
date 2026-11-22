from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from flask import Flask

from modules.forecast_verification import ForecastVerification, create_verification_blueprint
from modules.prediction_comparison import AssessmentStore
from modules.prediction_presentation import HK_TIMEZONE, build_prediction_timing
from modules.scheduler_service import HourlyPredictionScheduler


NOW = datetime(2026, 11, 19, 3, 40, tzinfo=HK_TIMEZONE)


def sun(_):
    return {'sunrise': '06:40', 'sunset': '17:40'}


def prediction(now=NOW, score=75, kind='sunrise', version='test_v1'):
    timing, _ = build_prediction_timing(now, kind, 3, sun)
    return dict(burnsky_score=score, prediction_type=kind, advance_hours=3,
                prediction_timing=timing, data_quality={'score_usable': True},
                scoring_method=version, weather_data={'cloud_forecast': {'issued_at': now.isoformat(), 'low': 12}},
                original_weather_data={'humidity': 70}, analysis_details={'cloud': {'score': 15}})


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.store = AssessmentStore(str(Path(self.folder.name) / 'history.db'))
        self.clock = NOW
        self.predict = Mock(return_value=prediction())
        self.service = ForecastVerification(self.store, self.predict, sun, now=lambda: self.clock)
        app = Flask(__name__)
        app.register_blueprint(create_verification_blueprint(self.service))
        self.client = app.test_client()

    def record(self):
        self.service.capture_due()
        return self.service.report()['records'][0]

    def outcome(self, result='strong'):
        return dict(result=result, observed_at='2026-11-19T06:45:00+08:00',
                    location='西環海濱', confirmed=True)

    def test_capture_is_immutable_and_preserves_input_provenance(self):
        first = self.record()
        self.predict.return_value['weather_data']['cloud_forecast']['low'] = 99
        self.predict.return_value['burnsky_score'] = 2
        self.service.capture_due()
        second = self.service.report()['records'][0]
        self.assertEqual(second, first)
        self.assertEqual(second['prediction']['weather_data']['cloud_forecast']['low'], 12)
        self.assertEqual(second['lead_minutes'], 180)
        self.predict.assert_called_once_with('sunrise', 3)
        # A restart does not replace the first issued forecast.
        restarted = ForecastVerification(self.store, self.predict, sun, now=lambda: self.clock)
        restarted.capture_due()
        self.predict.assert_called_once()

    def test_no_hindsight_backfill_or_wrong_time_calls(self):
        for minutes in (-6, 6, 90, 180):
            self.clock = NOW + timedelta(minutes=minutes)
            self.service.capture_due()
        self.predict.assert_not_called()
        self.assertEqual(self.service.report()['records'], [])

    def test_fresh_computation_finishing_after_start_is_accepted(self):
        def delayed(*_):
            self.clock += timedelta(seconds=2)
            return prediction(self.clock)
        self.predict.side_effect = delayed
        self.assertEqual(self.record()['lead_minutes'], 180)

    def test_stale_future_wrong_event_target_and_missing_scores_rejected(self):
        invalid = []
        for delta in (-10, 1):
            p = prediction()
            p['prediction_timing']['generated_at'] = (NOW + timedelta(minutes=delta)).isoformat()
            invalid.append(p)
        p = prediction(); p['prediction_timing']['evaluated_at'] = (NOW + timedelta(hours=2)).isoformat(); invalid.append(p)
        p = prediction(); p['prediction_timing']['event_type'] = 'sunset'; invalid.append(p)
        p = prediction(); p['prediction_timing']['event_at'] = '2026-11-20T06:40:00+08:00'; invalid.append(p)
        p = prediction(); p['data_quality']['score_usable'] = False; invalid.append(p)
        for score in (None, float('nan'), True, -1, 101):
            invalid.append(prediction(score=score))
        for p in invalid:
            self.predict.return_value = p
            self.service.capture_due()
            self.assertEqual(self.service.report()['records'], [])

    def test_capture_retries_after_temporary_unusable_data(self):
        self.predict.return_value = {'data_quality': {'score_usable': False}}
        self.service.capture_due()
        self.predict.return_value = prediction()
        self.assertEqual(self.record()['state'], 'awaiting_event')

    def test_zero_score_sunset_and_timezone_are_valid(self):
        self.clock = NOW.replace(hour=14)
        self.predict.return_value = prediction(self.clock, score=0, kind='sunset')
        record = self.record()
        self.assertEqual(record['prediction']['burnsky_score'], 0)
        self.assertIn('sunset', record['event_key'])

    def test_labels_require_actual_event_window_and_end_before_submission(self):
        record = self.record()
        identifier = record['assessment_id']
        with self.assertRaises(ValueError):
            self.service.submit(identifier, self.outcome())
        self.clock = NOW.replace(hour=8)
        for change in ({'observed_at': NOW.isoformat()}, {'observed_at': '2026-11-19T06:45:00'},
                       {'observed_at': 'invalid'}, {'confirmed': False}, {'location': ''},
                       {'result': 'photo_verified'}):
            data = self.outcome(); data.update(change)
            with self.assertRaises(ValueError):
                self.service.submit(identifier, data)
        self.service.submit(identifier, self.outcome())
        saved = self.service.report()['records'][0]
        self.assertEqual(saved['state'], 'reported')
        self.assertFalse(saved['outcome']['independently_verified'])
        with self.assertRaises(ValueError):
            self.service.submit(identifier, self.outcome('weak_or_none'))

    def test_future_observation_rejected_even_for_malformed_snapshot_window(self):
        self.record()
        self.clock = NOW.replace(hour=8)
        data = self.outcome(); data['observed_at'] = '2026-11-20T06:45:00+08:00'
        with self.assertRaises(ValueError):
            self.service.submit(self.service.report()['records'][0]['assessment_id'], data)

    def test_regular_untracked_snapshot_cannot_be_submitted(self):
        identifier = self.store.save(prediction())
        self.clock = NOW.replace(hour=8)
        with self.assertRaises(ValueError):
            self.service.submit(identifier, self.outcome())

    def test_empty_and_pending_are_never_counted_as_no_burnsky(self):
        report = self.service.report()
        self.assertIsNone(report['accuracy'])
        self.assertEqual(report['by_version'], {})
        self.record()
        self.clock = NOW.replace(hour=8)
        report = self.service.report()
        self.assertEqual(report['records'][0]['state'], 'awaiting_report')
        stats = report['by_version']['test_v1']
        self.assertEqual(stats['labeled'], 0)
        self.assertIsNone(stats['precision'])
        self.assertIsNone(stats['recall'])

    def test_confusion_counts_and_versions_do_not_mix(self):
        for offset, score, outcome, version in ((0, 70, 'strong', 'v1'),
                (1, 80, 'weak_or_none', 'v1'), (2, 20, 'strong', 'v1'),
                (3, 0, 'weak_or_none', 'v1'), (4, 90, 'unsure', 'v1'),
                (5, 90, 'weak_or_none', 'v2')):
            self.clock = NOW + timedelta(days=offset)
            self.predict.return_value = prediction(self.clock, score=score, version=version)
            record = self.record()
            day = self.clock.date().isoformat()
            self.clock += timedelta(hours=5)
            data = self.outcome(outcome); data['observed_at'] = day+'T06:45:00+08:00'
            self.service.submit(record['assessment_id'], data)
        report = self.service.report()
        stats = report['by_version']['v1']
        for category in ('hits', 'false_alarms', 'misses', 'correct_negatives', 'unsure'):
            self.assertEqual(stats[category], 1)
        self.assertEqual(stats['labeled'], 4)
        self.assertEqual(stats['precision'], .5)
        self.assertEqual(stats['recall'], .5)
        self.assertEqual(report['by_version']['v2']['false_alarms'], 1)
        self.assertIsNone(report['accuracy'])

    def test_routes_validate_payload_and_do_not_accept_client_predicted_score(self):
        self.assertEqual(self.client.get('/api/verification/three-hour').status_code, 200)
        identifier = self.record()['assessment_id']
        self.clock = NOW.replace(hour=8)
        url = '/api/verification/three-hour/'+identifier+'/outcome'
        for payload in (None, [], {}, {'confirmed': True}):
            self.assertEqual(self.client.post(url, json=payload).status_code, 400)
        data = self.outcome(); data['predicted_score'] = 0
        self.assertEqual(self.client.post(url, json=data).status_code, 200)
        stats = self.service.report()['by_version']['test_v1']
        self.assertEqual(stats['hits'], 1)
        self.assertEqual(self.client.post(url, json=data).status_code, 400)
        self.assertEqual(self.client.post('/api/verification/three-hour/bad/outcome', json=data).status_code, 400)

    def test_event_groups_score_bands_and_pending_keep_their_own_denominators(self):
        cases = ((0, 'sunrise', 70, 'strong'), (1, 'sunrise', 85, 'weak_or_none'),
                 (2, 'sunset', 44.9, 'strong'), (3, 'sunset', 45, 'weak_or_none'),
                 (4, 'sunset', 100, 'unsure'), (5, 'sunrise', 69.9, None),
                 (6, 'sunset', 84.9, None))
        for offset, kind, score, outcome in cases:
            self.clock = NOW + timedelta(days=offset, hours=11 if kind == 'sunset' else 0)
            self.predict.return_value = prediction(self.clock, score=score, kind=kind)
            identifier = self.record()['assessment_id']
            if outcome:
                day = self.clock.date().isoformat()
                self.clock += timedelta(hours=5)
                data = self.outcome(outcome)
                data['observed_at'] = day + ('T17:45:00+08:00' if kind == 'sunset' else 'T06:45:00+08:00')
                self.service.submit(identifier, data)
        stats = self.service.report()['by_version']['test_v1']
        self.assertEqual(stats['awaiting_event'], 1)
        self.assertEqual(stats['awaiting_report'], 1)
        self.assertEqual(stats['forecasts'], stats['labeled'] + stats['unsure'] +
                         stats['awaiting_event'] + stats['awaiting_report'])
        self.assertEqual(stats['predicted_positive'], 2)
        self.assertEqual(stats['observed_positive'], 2)
        sunrise, sunset = stats['by_event']['sunrise'], stats['by_event']['sunset']
        self.assertEqual((sunrise['hits'], sunrise['false_alarms'], sunrise['misses']), (1, 1, 0))
        self.assertEqual((sunset['hits'], sunset['false_alarms'], sunset['misses']), (0, 0, 1))
        self.assertIsNone(sunset['precision'])
        self.assertEqual(sunset['recall'], 0)
        bands = stats['score_bands']
        self.assertEqual([b['forecasts'] for b in bands], [1, 2, 2, 2])
        self.assertEqual([b['labeled'] for b in bands], [1, 1, 1, 1])
        self.assertEqual([b['strong'] for b in bands], [1, 0, 1, 0])
        self.assertEqual([b['unsure'] for b in bands], [0, 0, 0, 1])
        self.assertEqual([b['awaiting_event'] + b['awaiting_report'] for b in bands], [0, 1, 1, 0])
        self.assertEqual(sunrise['score_bands'][0]['labeled'], 0)
        self.assertEqual(sunset['score_bands'][0]['strong'], 1)

    def test_unlabeled_event_groups_do_not_publish_zero_success_rates(self):
        self.record()
        stats = self.service.report()['by_version']['test_v1']
        for event in ('sunrise', 'sunset'):
            group = stats['by_event'][event]
            self.assertIsNone(group['precision'])
            self.assertIsNone(group['recall'])
            self.assertEqual(group['predicted_positive'], 0)
            self.assertEqual(group['observed_positive'], 0)
            self.assertTrue(all(b['labeled'] == 0 for b in group['score_bands']))

    def test_scheduler_checks_immediately_and_retries_after_callback_failure(self):
        capture = Mock(side_effect=[RuntimeError('temporary outage'), None])
        scheduler = HourlyPredictionScheduler(Mock(), Mock(), Mock(), capture_due=capture)
        with patch('modules.scheduler_service.schedule.run_pending') as pending, \
                patch('modules.scheduler_service.time.sleep', side_effect=[None, RuntimeError('stop')]), \
                redirect_stdout(StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'stop'):
                scheduler._run()
        self.assertEqual(capture.call_count, 2)
        self.assertEqual(pending.call_count, 2)


if __name__ == '__main__':
    unittest.main()
