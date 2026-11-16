"""Immutable condition assessments beside dated, direction-matched webcam images."""
import base64
from contextlib import closing
from datetime import datetime, timedelta
import hashlib
import io
import json
import sqlite3

import numpy as np

from .prediction_presentation import HK_TIMEZONE
from .weather_presentation import number


def instant(value):
    try:
        value = datetime.fromisoformat(value) if isinstance(value, str) else value
        return value.astimezone(HK_TIMEZONE) if isinstance(value, datetime) and value.tzinfo else None
    except ValueError:
        return None


class AssessmentStore:
    def __init__(self, path):
        self.path = path

    @staticmethod
    def _table(conn):
        conn.execute('CREATE TABLE IF NOT EXISTS assessment_snapshots (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')

    def save(self, prediction):
        # Store exactly the assessment shown to the user, without recomputing it later.
        snapshot = {key: prediction.get(key) for key in (
            'burnsky_score', 'prediction_type', 'advance_hours', 'prediction_timing',
            'data_quality', 'scoring_method', 'weather_updated_at')}
        payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True)
        identifier = hashlib.sha256(payload.encode()).hexdigest()
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                self._table(conn)
                conn.execute('INSERT OR IGNORE INTO assessment_snapshots VALUES (?, ?)', (identifier, payload))
        return identifier

    def get(self, identifier):
        with closing(sqlite3.connect(self.path)) as conn:
            self._table(conn)
            row = conn.execute('SELECT payload FROM assessment_snapshots WHERE id = ?', (identifier,)).fetchone()
        return json.loads(row[0]) if row else None


def image_observation(camera, now, timing):
    """Describe pixels, not a time-weighted burnsky score or measured cloud cover."""
    image = camera['image'].convert('RGB')
    image.thumbnail((640, 480))
    pixels = np.asarray(image, dtype=float)
    sky = pixels[:max(1, pixels.shape[0] // 2)]
    red, green, blue = sky[:, :, 0], sky[:, :, 1], sky[:, :, 2]
    brightness = float(sky.mean())
    warm = (red > blue * 1.15) & (red >= green * .95) & (red > 60) & ((sky.max(axis=2) - sky.min(axis=2)) > 25)
    warm_percent = round(float(warm.mean()) * 100, 1) if brightness >= 40 else None
    updated = instant(camera.get('source_updated_at'))
    start, end = instant(timing['window_start']), instant(timing['window_end'])
    evaluated = instant(timing['evaluated_at'])
    generated = instant(timing['generated_at'])
    earliest = generated if timing.get('mode') == 'forecast' else generated - timedelta(minutes=15)
    aligned = bool(updated and start <= updated <= end and earliest <= updated <= now
                   and abs(updated - evaluated) <= timedelta(minutes=15)
                   and now - updated <= timedelta(minutes=15))
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=75)
    return {
        'camera_id': camera['location_id'], 'location': camera['location_name'],
        'direction': camera['direction'], 'source': '香港天文台網絡攝影機',
        'source_updated_at': updated.isoformat() if updated else None,
        'retrieved_at': instant(camera.get('retrieved_at')).isoformat() if instant(camera.get('retrieved_at')) else None,
        'captured_at': None, 'analyzed_at': now.isoformat(),
        'time_source': 'http_last_modified' if updated else 'unknown',
        'aligned_reference': aligned, 'warm_pixel_percent': warm_percent,
        'description': ('光線不足，無法判讀暖色像素；不當作沒有燒天。' if warm_percent is None else
                        f'圖片上半部暖色像素約 {warm_percent}%；受建築物、燈光、曝光及白平衡影響。'),
        'image_data_url': 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode(),
        'note': '來源更新時間不是經核實的拍攝時間；像素比例並非燒天強度、機率或實測雲量。',
    }


def build_comparison(prediction, fetcher, now, clock=None):
    now = now.astimezone(HK_TIMEZONE)
    timing = prediction.get('prediction_timing') or {}
    start, end, evaluated = (instant(timing.get(key)) for key in ('window_start', 'window_end', 'evaluated_at'))
    generated = instant(timing.get('generated_at'))
    response = {'status': 'success', 'prediction': prediction, 'observations': [],
                'generated_at': now.isoformat(), 'score_difference': None, 'accuracy': None}
    if not all((start, end, evaluated, generated)) or not start <= evaluated <= end or number(prediction.get('burnsky_score')) is None:
        response.update(comparison_state='out_of_window', message='原評估不在觀賞參考時段內，不能用來驗證這次日出或日落。')
    elif now < start:
        response.update(comparison_state='pending', message='尚未到目標觀賞時段；先保留這次評估，時段內再更新實況。')
    elif now > end:
        response.update(comparison_state='ended', message='目標時段已結束；未保存該時段影像，不能用現在的圖片補作當時實況。')
    elif not (prediction.get('data_quality') or {}).get('score_usable'):
        response.update(comparison_state='insufficient', message='原評估資料不足，不能用作條件對照。')
    else:
        directions = {'East', 'Northeast', 'Southeast'} if timing['event_type'] == 'sunrise' else {'West', 'Northwest', 'Southwest'}
        locations = [key for key, info in fetcher.WEBCAM_LOCATIONS.items() if info['direction'] in directions][:3]
        cameras = fetcher.fetch_multiple_webcams(locations)
        analyzed_at = clock().astimezone(HK_TIMEZONE) if clock else now
        response['generated_at'] = analyzed_at.isoformat()
        for camera in cameras.values():
            try:
                response['observations'].append(image_observation(camera, analyzed_at, timing))
            except (KeyError, TypeError, ValueError, OSError):
                continue
        aligned = any(item['aligned_reference'] for item in response['observations'])
        response.update(comparison_state='aligned_reference' if aligned else 'unmatched',
                        message=('有同時段及方向的影像更新參考；拍攝時間未經核實，只供並排判讀，不計準確率。' if aligned else
                                 '未取得時間相符的影像；可能缺少來源時間、影像過舊或攝影機未回應。'))
    return response
