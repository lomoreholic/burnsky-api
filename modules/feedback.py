"""Verified user-feedback persistence and accuracy reporting."""

import sqlite3
from datetime import datetime

from flask import Blueprint, jsonify, request

from .config import PREDICTION_HISTORY_DB


feedback_bp = Blueprint('feedback', __name__)
MINIMUM_SAMPLE_SIZE = 10


def calculate_real_accuracy(days_back=30):
    """Calculate accuracy using only submitted user verification data."""
    try:
        conn = sqlite3.connect(PREDICTION_HISTORY_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT predicted_score, user_rating, feedback_timestamp
            FROM user_feedback
            WHERE feedback_timestamp >= datetime('now', ?)
            ORDER BY feedback_timestamp DESC
        ''', (f'-{days_back} days',))
        feedbacks = cursor.fetchall()

        if not feedbacks:
            conn.close()
            return {
                'has_data': False,
                'message': f'最近 {days_back} 天暫無已驗證的用戶反饋',
                'feedback_count': 0,
                'is_statistically_ready': False,
                'minimum_sample_size': MINIMUM_SAMPLE_SIZE,
                'period_days': days_back
            }

        average_error = sum(abs(predicted - actual) for predicted, actual, _ in feedbacks) / len(feedbacks)
        cursor.execute('''
            SELECT
                COUNT(CASE WHEN ABS(predicted_score - user_rating) <= 10 THEN 1 END),
                COUNT(CASE WHEN ABS(predicted_score - user_rating) <= 20 THEN 1 END),
                COUNT(CASE WHEN predicted_score >= 70 AND user_rating >= 70 THEN 1 END),
                COUNT(CASE WHEN predicted_score >= 70 AND user_rating < 70 THEN 1 END),
                COUNT(CASE WHEN predicted_score < 70 AND user_rating >= 70 THEN 1 END),
                COUNT(CASE WHEN verification_source = 'photo' THEN 1 END),
                COUNT(*)
            FROM user_feedback
            WHERE feedback_timestamp >= datetime('now', ?)
        ''', (f'-{days_back} days',))
        within_10, within_20, true_positive, false_positive, false_negative, photo_verified, total = cursor.fetchone()
        conn.close()

        return {
            'has_data': True,
            'accuracy': round(max(0, min(100, 100 - average_error)), 1),
            'avg_error': round(average_error, 1),
            'feedback_count': len(feedbacks),
            'is_statistically_ready': len(feedbacks) >= MINIMUM_SAMPLE_SIZE,
            'minimum_sample_size': MINIMUM_SAMPLE_SIZE,
            'period_days': days_back,
            'within_10_points': round(within_10 / total * 100, 1) if total else 0,
            'within_20_points': round(within_20 / total * 100, 1) if total else 0,
            'high_score_precision': round(true_positive / (true_positive + false_positive) * 100, 1)
            if true_positive + false_positive else None,
            'high_score_recall': round(true_positive / (true_positive + false_negative) * 100, 1)
            if true_positive + false_negative else None,
            'photo_verified_count': photo_verified or 0,
            'manual_verified_count': total - (photo_verified or 0),
            'last_updated': feedbacks[0][2]
        }
    except Exception as error:
        print(f"❌ 計算準確率錯誤: {error}")
        return {
            'has_data': False,
            'message': f'計算錯誤: {error}',
            'feedback_count': 0,
            'is_statistically_ready': False,
            'minimum_sample_size': MINIMUM_SAMPLE_SIZE,
            'period_days': days_back
        }


@feedback_bp.route('/api/submit-feedback', methods=['POST'])
def submit_feedback():
    """Store a manually submitted or photo-backed verification result."""
    try:
        data = request.get_json(silent=True)
        required_fields = ['predicted_score', 'user_rating']
        if not data or not all(field in data for field in required_fields):
            return jsonify({'status': 'error', 'message': '缺少必需字段'}), 400

        predicted_score = int(data['predicted_score'])
        user_rating = int(data['user_rating'])
        verification_source = data.get('verification_source', 'manual')
        if not (0 <= predicted_score <= 100) or not (0 <= user_rating <= 100):
            return jsonify({'status': 'error', 'message': '評分必須在 0-100 之間'}), 400
        if verification_source not in {'manual', 'photo'}:
            return jsonify({'status': 'error', 'message': '不支援的驗證來源'}), 400

        conn = sqlite3.connect(PREDICTION_HISTORY_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_feedback
            (prediction_timestamp, predicted_score, user_rating, location, comment, weather_conditions, verification_source, photo_case_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('prediction_timestamp', datetime.now().isoformat()),
            predicted_score, user_rating, data.get('location', ''), data.get('comment', ''),
            data.get('weather_conditions', ''), verification_source, data.get('photo_case_id')
        ))
        conn.commit()
        feedback_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'status': 'success',
            'message': '感謝您的反饋！',
            'feedback_id': feedback_id,
            'accuracy_stats': calculate_real_accuracy()
        })
    except Exception as error:
        print(f"❌ 提交反饋錯誤: {error}")
        return jsonify({'status': 'error', 'message': str(error)}), 500


@feedback_bp.route('/api/accuracy-stats')
def get_accuracy_stats():
    """Return verified accuracy metrics for the requested reporting period."""
    try:
        days_back = min(max(int(request.args.get('days', 30)), 1), 365)
        return jsonify(calculate_real_accuracy(days_back))
    except Exception as error:
        print(f"❌ 獲取準確率統計錯誤: {error}")
        return jsonify({'status': 'error', 'message': str(error)}), 500