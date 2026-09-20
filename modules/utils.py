# utils.py - 工具函數模塊

import numpy as np
from datetime import datetime, timedelta
from .database import get_season, get_time_category

def convert_numpy_types(obj):
    """將 numpy 類型轉換為 Python 原生類型，以便 JSON 序列化"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def get_prediction_level(score):
    """根據分數獲取預測等級"""
    if score >= 80:
        return "極佳燒天機會"
    elif score >= 60:
        return "良好燒天機會"
    elif score >= 40:
        return "中等燒天機會"
    elif score >= 20:
        return "低等燒天機會"
    else:
        return "燒天機會很低"

def get_optimal_sunset_time():
    """獲取最佳日落拍攝時間"""
    # 簡化版：返回當前時間後1小時
    return (datetime.now() + timedelta(hours=1)).strftime('%H:%M')

def get_optimal_burnsky_time():
    """獲取最佳燒天拍攝時間"""
    # 簡化版：返回當前時間後2小時
    return (datetime.now() + timedelta(hours=2)).strftime('%H:%M')

def get_historical_prediction_for_time(target_datetime, prediction_type, tolerance_hours=2):
    """獲取指定時間的歷史預測"""
    try:
        from .config import PREDICTION_HISTORY_DB
        import sqlite3
        from datetime import datetime

        conn = sqlite3.connect(PREDICTION_HISTORY_DB)
        cursor = conn.cursor()

        # 將目標時間轉換為 datetime 對象
        if isinstance(target_datetime, str):
            target_dt = datetime.fromisoformat(target_datetime.replace('Z', '+00:00'))
        else:
            target_dt = target_datetime

        # 查詢指定時間範圍內的預測
        start_time = target_dt - timedelta(hours=tolerance_hours)
        end_time = target_dt + timedelta(hours=tolerance_hours)

        cursor.execute('''
            SELECT score, factors, weather_data, warnings, timestamp
            FROM prediction_history
            WHERE prediction_type = ?
            AND timestamp BETWEEN ? AND ?
            ORDER BY ABS(strftime('%s', timestamp) - strftime('%s', ?)) ASC
            LIMIT 1
        ''', (prediction_type, start_time.isoformat(), end_time.isoformat(), target_dt.isoformat()))

        result = cursor.fetchone()
        conn.close()

        if result:
            score, factors_json, weather_json, warnings_json, timestamp = result
            import json
            try:
                factors = json.loads(factors_json) if factors_json else {}
                weather_data = json.loads(weather_json) if weather_json else {}
                warnings = json.loads(warnings_json) if warnings_json else {}
            except:
                factors = {}
                weather_data = {}
                warnings = {}

            return {
                'score': score,
                'factors': factors,
                'weather_data': weather_data,
                'warnings': warnings,
                'timestamp': timestamp,
                'time_difference_hours': abs((datetime.fromisoformat(timestamp.replace('Z', '+00:00')) - target_dt).total_seconds()) / 3600
            }

        return None

    except Exception as e:
        print(f"⚠️ 獲取歷史預測失敗: {e}")
        return None

def cross_check_photo_with_prediction(photo_datetime, photo_location, photo_quality, prediction_type='sunset'):
    """將照片與預測進行交叉驗證"""
    try:
        # 解析照片時間
        if isinstance(photo_datetime, str):
            if '_' in photo_datetime:
                date_str, time_str = photo_datetime.split('_')
                time_str = time_str.replace('-', ':')
                photo_dt = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            else:
                photo_dt = datetime.fromisoformat(photo_datetime.replace('Z', '+00:00'))
        else:
            photo_dt = photo_datetime

        # 獲取當時的預測
        historical_prediction = get_historical_prediction_for_time(photo_dt, prediction_type)

        if historical_prediction:
            predicted_score = historical_prediction['score']
            actual_quality = photo_quality * 10  # 將1-10轉換為0-100

            # 計算準確性
            accuracy_diff = abs(predicted_score - actual_quality)
            accuracy_percentage = max(0, 100 - accuracy_diff)

            return {
                'photo_datetime': photo_dt.isoformat(),
                'photo_quality': photo_quality,
                'predicted_score': predicted_score,
                'actual_score': actual_quality,
                'accuracy_difference': accuracy_diff,
                'accuracy_percentage': accuracy_percentage,
                'prediction_found': True,
                'time_match_quality': 'excellent' if historical_prediction['time_difference_hours'] < 1 else 'good'
            }
        else:
            return {
                'photo_datetime': photo_dt.isoformat(),
                'photo_quality': photo_quality,
                'predicted_score': None,
                'actual_score': photo_quality * 10,
                'accuracy_difference': None,
                'accuracy_percentage': None,
                'prediction_found': False,
                'message': '未找到對應時間的預測數據'
            }

    except Exception as e:
        print(f"⚠️ 照片預測交叉驗證失敗: {e}")
        return {
            'error': str(e),
            'photo_datetime': str(photo_datetime),
            'prediction_found': False
        }
