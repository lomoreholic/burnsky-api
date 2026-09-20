"""Prediction-history reporting endpoints."""

import sqlite3
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from .config import PREDICTION_HISTORY_DB
from .feedback import calculate_real_accuracy


history_bp = Blueprint('history', __name__)


def generate_burnsky_insights(overall, by_type, best_hours):
    insights = []
    if overall[0] > 0:
        high_score_rate = overall[4] / overall[0] * 100
        insights.append(f"過去期間共進行 {overall[0]} 次預測，高分（≥70分）預測比例為 {high_score_rate:.1f}%")
        if overall[1]:
            insights.append(f"平均燒天評分為 {overall[1]:.1f} 分")
        if overall[2] and overall[2] >= 80:
            insights.append(f"最高評分達到 {overall[2]:.0f} 分，出現極佳燒天條件")

    if 'sunrise' in by_type and 'sunset' in by_type:
        sunrise_rate = by_type['sunrise']['high_score_prediction_rate']
        sunset_rate = by_type['sunset']['high_score_prediction_rate']
        higher_type, higher_rate, lower_rate = (
            ('日出', sunrise_rate, sunset_rate)
            if sunrise_rate > sunset_rate else ('日落', sunset_rate, sunrise_rate)
        )
        insights.append(f"{higher_type}的高分預測比例（{higher_rate}%）高於另一時段（{lower_rate}%）")

    if best_hours:
        best = best_hours[0]
        time_label = '凌晨' if best['hour'] < 6 else '早晨' if best['hour'] < 12 else '下午' if best['hour'] < 18 else '晚間'
        insights.append(f"{time_label}時段（{best['hour']}:00）的燒天評分最高，平均 {best['avg_score']} 分")
    return insights


@history_bp.route('/api/burnsky/history', methods=['GET'])
def get_burnsky_history():
    """Return score distribution and separately reported verified accuracy."""
    try:
        days_back = min(max(int(request.args.get('days', 30)), 1), 365)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_date_str = start_date.strftime('%Y-%m-%d %H:%M:%S')
        end_date_str = end_date.strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(PREDICTION_HISTORY_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*), AVG(score), MAX(score), MIN(score),
                COUNT(CASE WHEN score >= 70 THEN 1 END),
                COUNT(CASE WHEN score >= 50 AND score < 70 THEN 1 END),
                COUNT(CASE WHEN score < 50 THEN 1 END)
            FROM prediction_history WHERE timestamp >= ? AND timestamp <= ?
        ''', (start_date_str, end_date_str))
        overall = cursor.fetchone()

        cursor.execute('''
            SELECT prediction_type, COUNT(*), AVG(score), MAX(score),
                COUNT(CASE WHEN score >= 70 THEN 1 END)
            FROM prediction_history WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY prediction_type
        ''', (start_date_str, end_date_str))
        by_type = {
            prediction_type: {
                'count': count,
                'avg_score': round(avg_score, 1) if avg_score else 0,
                'max_score': max_score or 0,
                'high_score_count': high_score_count,
                'high_score_prediction_rate': round(high_score_count / count * 100, 1) if count else 0
            }
            for prediction_type, count, avg_score, max_score, high_score_count in cursor.fetchall()
        }

        cursor.execute('''
            SELECT DATE(timestamp), AVG(score), MAX(score), COUNT(CASE WHEN score >= 70 THEN 1 END)
            FROM prediction_history WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY DATE(timestamp) ORDER BY DATE(timestamp) DESC LIMIT 30
        ''', (start_date_str, end_date_str))
        daily_trends = [
            {'date': date, 'avg_score': round(avg_score, 1) if avg_score else 0,
             'max_score': max_score or 0, 'high_score_count': high_score_count}
            for date, avg_score, max_score, high_score_count in cursor.fetchall()
        ]

        cursor.execute('''
            SELECT CAST(strftime('%H', timestamp) AS INTEGER), COUNT(*), AVG(score),
                COUNT(CASE WHEN score >= 70 THEN 1 END)
            FROM prediction_history WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY 1 ORDER BY 3 DESC
        ''', (start_date_str, end_date_str))
        best_hours = [
            {'hour': hour, 'count': count, 'avg_score': round(avg_score, 1) if avg_score else 0,
             'high_score_count': high_score_count}
            for hour, count, avg_score, high_score_count in cursor.fetchall()
        ]
        conn.close()

        summary = {
            'total_predictions': overall[0] or 0,
            'avg_score': round(overall[1], 1) if overall[1] else 0,
            'max_score': overall[2] or 0,
            'min_score': overall[3] or 0,
            'high_score_count': overall[4] or 0,
            'medium_score_count': overall[5] or 0,
            'low_score_count': overall[6] or 0,
            'high_score_prediction_rate': round(overall[4] / overall[0] * 100, 1) if overall[0] else 0
        }
        return jsonify({
            'status': 'success',
            'data_source': 'prediction_history',
            'time_range': {'days': days_back, 'start_date': start_date.strftime('%Y-%m-%d'),
                           'end_date': end_date.strftime('%Y-%m-%d')},
            'summary': summary,
            'verified_accuracy': calculate_real_accuracy(days_back),
            'by_type': by_type,
            'daily_trends': daily_trends,
            'best_hours': best_hours[:5],
            'insights': generate_burnsky_insights(overall, by_type, best_hours)
        })
    except Exception as error:
        print(f"❌ 燒天歷史統計錯誤: {error}")
        return jsonify({'status': 'error', 'message': str(error)}), 500