# database.py - 數據庫操作模塊

import sqlite3
from datetime import datetime, timedelta
from .config import PREDICTION_HISTORY_DB

def init_prediction_history_db():
    """初始化預測歷史數據庫"""
    conn = sqlite3.connect(PREDICTION_HISTORY_DB)
    cursor = conn.cursor()

    # 創建預測歷史表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            prediction_type TEXT NOT NULL,
            advance_hours INTEGER,
            score REAL,
            factors TEXT,  -- JSON格式儲存所有因子
            weather_data TEXT,  -- JSON格式儲存天氣數據
            warnings TEXT,  -- JSON格式儲存警告數據
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 創建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON prediction_history(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON prediction_history(prediction_type)')

    conn.commit()
    conn.close()
    print("📊 預測歷史數據庫已初始化")

def save_prediction_to_history(prediction_type, advance_hours, score, factors, weather_data, warnings):
    """保存預測到歷史數據庫"""
    try:
        conn = sqlite3.connect(PREDICTION_HISTORY_DB)
        cursor = conn.cursor()

        # 增加更多時間相關的因子
        enhanced_factors = factors.copy() if factors else {}
        current_time = datetime.now()

        # 添加時間因子
        enhanced_factors.update({
            'time_factors': {
                'hour': current_time.hour,
                'day_of_week': current_time.weekday(),
                'day_of_month': current_time.day,
                'month': current_time.month,
                'season': get_season(current_time.month),
                'is_weekend': current_time.weekday() >= 5,
                'time_category': get_time_category(current_time.hour)
            },
            'weather_timing': {
                'prediction_datetime': current_time.isoformat(),
                'target_datetime': (current_time + timedelta(hours=advance_hours)).isoformat(),
                'advance_hours': advance_hours
            }
        })

        # 將數據轉換為JSON字符串
        import json
        factors_json = json.dumps(enhanced_factors, default=str)
        weather_json = json.dumps(weather_data, default=str) if weather_data else None
        warnings_json = json.dumps(warnings, default=str) if warnings else None

        cursor.execute('''
            INSERT INTO prediction_history
            (prediction_type, advance_hours, score, factors, weather_data, warnings)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (prediction_type, advance_hours, score, factors_json, weather_json, warnings_json))

        conn.commit()
        prediction_id = cursor.lastrowid
        conn.close()

        print(f"📈 已記錄預測: {prediction_type} (ID: {prediction_id})")
        return prediction_id

    except Exception as e:
        print(f"⚠️ 保存預測歷史失敗: {e}")
        return None

def get_season(month):
    """根據月份獲取季節"""
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

def get_time_category(hour):
    """根據小時獲取時間類別"""
    if 6 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 18:
        return 'afternoon'
    elif 18 <= hour < 22:
        return 'evening'
    else:
        return 'night'
