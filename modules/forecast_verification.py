"""Prospective three-hour regional forecasts and explicitly self-reported outcomes."""

from contextlib import closing
from datetime import datetime, timedelta
import json
import sqlite3
import threading

from flask import Blueprint, jsonify, request

from .prediction_comparison import instant
from .prediction_presentation import HK_TIMEZONE
from .weather_presentation import number


THRESHOLD = 70
TOLERANCE = timedelta(minutes=5)
REGION = 'hong_kong_reference_22.30_114.17'
SCORE_BANDS = ((0, 45, '0–<45'), (45, THRESHOLD, '45–<70'),
               (THRESHOLD, 85, '70–<85'), (85, 101, '85–100'))


def new_summary():
    """Keep missing reports and unsure reports outside every outcome denominator."""
    counts = dict(forecasts=0, labeled=0, unsure=0, awaiting_event=0, awaiting_report=0,
                  hits=0, false_alarms=0, misses=0, correct_negatives=0)
    counts['score_bands'] = [dict(label=label, forecasts=0, labeled=0, strong=0,
                                 weak_or_none=0, unsure=0, awaiting_event=0, awaiting_report=0)
                             for _, _, label in SCORE_BANDS]
    return counts


def add_to_summary(stats, score, outcome, state):
    stats['forecasts'] += 1
    band = next(stats['score_bands'][i] for i, (low, high, _) in enumerate(SCORE_BANDS)
                if low <= score < high)
    band['forecasts'] += 1
    if not outcome:
        stats[state] += 1
        band[state] += 1
        return
    result = outcome['result']
    band[result] += 1
    if result == 'unsure':
        stats['unsure'] += 1
        return
    stats['labeled'] += 1
    band['labeled'] += 1
    positive, strong = score >= THRESHOLD, result == 'strong'
    category = ('hits' if strong else 'false_alarms') if positive else ('misses' if strong else 'correct_negatives')
    stats[category] += 1


def finish_summary(stats):
    # These are self-report fractions, never calibrated probabilities or accuracy.
    stats['predicted_positive'] = stats['hits'] + stats['false_alarms']
    stats['observed_positive'] = stats['hits'] + stats['misses']
    stats['precision'] = (round(stats['hits'] / stats['predicted_positive'], 3)
                          if stats['predicted_positive'] else None)
    stats['recall'] = (round(stats['hits'] / stats['observed_positive'], 3)
                       if stats['observed_positive'] else None)


class ForecastVerification:
    def __init__(self, store, predict, get_sun_times, now=None):
        self.store = store
        self.predict = predict
        self.get_sun_times = get_sun_times
        self.now = now or (lambda: datetime.now(HK_TIMEZONE))
        self._lock = threading.Lock()

    def _connect(self):
        conn = sqlite3.connect(self.store.path, timeout=15)
        conn.execute('''CREATE TABLE IF NOT EXISTS three_hour_forecasts (
            event_key TEXT PRIMARY KEY, assessment_id TEXT NOT NULL,
            recorded_at TEXT NOT NULL, outcome TEXT)''')
        return conn

    def capture_due(self):
        """Never reconstruct a missed forecast from later weather or overwrite one."""
        with self._lock:
            now = self.now().astimezone(HK_TIMEZONE)
            sun = self.get_sun_times(now.date())
            for kind in ('sunrise', 'sunset'):
                event = datetime.combine(now.date(), datetime.strptime(sun[kind], '%H:%M').time(), HK_TIMEZONE)
                if abs(event - timedelta(hours=3) - now) > TOLERANCE:
                    continue
                key = f'{REGION}:{kind}:{event.isoformat()}'
                with closing(self._connect()) as conn:
                    if conn.execute('SELECT 1 FROM three_hour_forecasts WHERE event_key=?', (key,)).fetchone():
                        continue
                prediction = self.predict(kind, 3)
                recorded = self.now().astimezone(HK_TIMEZONE)
                if not isinstance(prediction, dict):
                    continue
                timing = prediction.get('prediction_timing') or {}
                issued, evaluated = instant(timing.get('generated_at')), instant(timing.get('evaluated_at'))
                score = number(prediction.get('burnsky_score'))
                if (not issued or not evaluated or instant(timing.get('event_at')) != event
                        or timing.get('event_type') != kind or prediction.get('prediction_type') != kind
                        or score is None or not 0 <= score <= 100
                        or not (prediction.get('data_quality') or {}).get('score_usable')
                        or not prediction.get('scoring_method')
                        or not timedelta(0) <= recorded - issued <= TOLERANCE
                        or abs(event - issued - timedelta(hours=3)) > TOLERANCE
                        or abs(evaluated - event) > TOLERANCE):
                    continue
                identifier = self.store.save(prediction)
                with closing(self._connect()) as conn, conn:
                    conn.execute('INSERT OR IGNORE INTO three_hour_forecasts VALUES (?, ?, ?, NULL)',
                                 (key, identifier, recorded.isoformat()))

    def report(self):
        with closing(self._connect()) as conn:
            rows = conn.execute('SELECT event_key, assessment_id, recorded_at, outcome '
                                'FROM three_hour_forecasts ORDER BY recorded_at DESC LIMIT 200').fetchall()
        records, versions = [], {}
        now = self.now().astimezone(HK_TIMEZONE)
        for key, identifier, recorded_at, raw_outcome in rows:
            prediction = self.store.get(identifier)
            if not prediction:
                continue
            timing = prediction['prediction_timing']
            outcome = json.loads(raw_outcome) if raw_outcome else None
            end = instant(timing['window_end'])
            state = 'reported' if outcome else ('awaiting_event' if now < end else 'awaiting_report')
            records.append(dict(event_key=key, assessment_id=identifier, recorded_at=recorded_at,
                                region=REGION, prediction=prediction, outcome=outcome, state=state,
                                lead_minutes=round((instant(timing['event_at']) -
                                                    instant(timing['generated_at'])).total_seconds()/60, 1)))
            version = prediction['scoring_method']
            if version not in versions:
                versions[version] = new_summary()
                versions[version]['by_event'] = {kind: new_summary() for kind in ('sunrise', 'sunset')}
            stats = versions[version]
            for group in (stats, stats['by_event'][timing['event_type']]):
                add_to_summary(group, prediction['burnsky_score'], outcome, state)
        for stats in versions.values():
            for group in (stats, *stats['by_event'].values()):
                finish_summary(group)
        return dict(status='success', records=records, by_version=versions, threshold=THRESHOLD,
                    sample_limit=200, evidence='self_reported', accuracy=None,
                    note='僅統計最近 200 次已留底預測，按版本及日出／日落分開；未回報及無法判斷不計入實況分母。'
                         '分數區間只作分組；自報樣本可能偏向有燒天或特定地點，未經獨立核實，不能當作準確率或發生機率。')

    def submit(self, identifier, data):
        if not isinstance(data, dict) or data.get('confirmed') is not True:
            raise ValueError('請確認係親身觀察，並填寫實際觀察時間及地點。')
        result, location = data.get('result'), data.get('location')
        observed = instant(data.get('observed_at'))
        if result not in ('strong', 'weak_or_none', 'unsure') or not isinstance(location, str) or not 1 <= len(location.strip()) <= 120:
            raise ValueError('請填寫有效實況及香港觀察地點（最多 120 字）。')
        prediction = self.store.get(identifier)
        if not prediction:
            raise ValueError('找不到原始預測。')
        timing = prediction['prediction_timing']
        now = self.now().astimezone(HK_TIMEZONE)
        start, end = instant(timing['window_start']), instant(timing['window_end'])
        if not observed or not start <= observed <= end or observed > now or now < end:
            raise ValueError('請在整個參考時段結束後提交；觀察時間須在該次日出／日落前後 30 分鐘內。')
        outcome = dict(result=result, location=location.strip(), observed_at=observed.isoformat(),
                       submitted_at=now.isoformat(), source='self_reported', independently_verified=False)
        with closing(self._connect()) as conn, conn:
            cursor = conn.execute('UPDATE three_hour_forecasts SET outcome=? WHERE assessment_id=? AND outcome IS NULL',
                                  (json.dumps(outcome, ensure_ascii=False), identifier))
            if cursor.rowcount != 1:
                raise ValueError('呢次並非三小時留底預測，或已經有實況紀錄。')
        return outcome


def create_verification_blueprint(service):
    bp = Blueprint('forecast_verification', __name__)

    @bp.get('/api/verification/three-hour')
    def report():
        try:
            return jsonify(service.report())
        except sqlite3.Error:
            return jsonify(status='error', message='暫時無法讀取驗證紀錄。'), 503

    @bp.post('/api/verification/three-hour/<identifier>/outcome')
    def submit(identifier):
        if len(identifier) != 64 or any(c not in '0123456789abcdef' for c in identifier):
            return jsonify(status='error', message='預測編號無效。'), 400
        try:
            return jsonify(status='success', outcome=service.submit(identifier, request.get_json(silent=True)))
        except ValueError as error:
            return jsonify(status='error', message=str(error)), 400
        except sqlite3.Error:
            return jsonify(status='error', message='暫時無法保存實況。'), 503

    return bp
