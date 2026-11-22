# photo_analyzer.py - 照片分析模塊

import base64
import io
from PIL import Image
import numpy as np
import cv2
from datetime import datetime
from .config import BURNSKY_PHOTO_CASES, LAST_CASE_UPDATE

def analyze_photo_quality(image_data):
    """分析照片品質"""
    try:
        # 解碼 base64 圖片
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            # 處理 base64 數據
            header, encoded = image_data.split(',', 1)
            image_data = base64.b64decode(encoded)

        # 打開圖片
        image = Image.open(io.BytesIO(image_data))
        img_array = np.array(image)

        # 轉換為 HSV 色彩空間進行分析
        if len(img_array.shape) == 3:
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        else:
            # 灰度圖片
            hsv = cv2.cvtColor(cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB), cv2.COLOR_RGB2HSV)

        # 分析色彩
        hue, saturation, value = cv2.split(hsv)

        # 計算各種指標
        avg_hue = np.mean(hue)
        avg_saturation = np.mean(saturation)
        avg_value = np.mean(value)

        # 檢測橙色/紅色區域（燒天特徵色彩）
        orange_mask = ((hue >= 5) & (hue <= 25) & (saturation > 50) & (value > 100))
        orange_pixels = np.sum(orange_mask)
        total_pixels = hue.size
        orange_ratio = orange_pixels / total_pixels

        # 計算對比度
        contrast = np.std(value) / np.mean(value) if np.mean(value) > 0 else 0

        # 計算顏色多樣性
        unique_colors = len(np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0))
        color_diversity = unique_colors / (img_array.shape[0] * img_array.shape[1])

        # 計算天空區域（假設上半部分是天空）
        height = img_array.shape[0]
        sky_region = img_array[:height//2, :, :]
        sky_hsv = cv2.cvtColor(sky_region, cv2.COLOR_RGB2HSV) if len(sky_region.shape) == 3 else cv2.cvtColor(cv2.cvtColor(sky_region, cv2.COLOR_GRAY2RGB), cv2.COLOR_RGB2HSV)

        sky_hue, sky_saturation, sky_value = cv2.split(sky_hsv)
        sky_brightness = np.mean(sky_value)

        # 雲層分析（基於亮度和對比）
        cloud_score = min(1.0, (sky_brightness / 200) * (np.std(sky_value) / 50))

        # 大氣條件評估
        atmospheric_score = min(1.0, (avg_saturation / 100) * (contrast / 0.5))

        # 顏色潛力評估
        color_potential = min(1.0, orange_ratio * 2 + color_diversity * 0.5)

        # 綜合品質評分 (0-10)
        quality_score = (
            orange_ratio * 3 +          # 橙色比例 (0-3分)
            contrast * 2 +              # 對比度 (0-2分)
            color_diversity * 2 +       # 顏色多樣性 (0-2分)
            cloud_score * 2 +           # 雲層品質 (0-2分)
            atmospheric_score * 1       # 大氣條件 (0-1分)
        )

        # 限制在 0-10 範圍
        quality_score = min(10.0, max(0.0, quality_score))

        # 生成分析詳情
        analysis = {
            'quality_score': round(quality_score, 1),
            'color_analysis': {
                'orange_ratio': round(orange_ratio, 3),
                'avg_hue': round(avg_hue, 1),
                'avg_saturation': round(avg_saturation, 1),
                'color_diversity': round(color_diversity, 3)
            },
            'cloud_analysis': {
                'cloud_score': round(cloud_score, 2),
                'sky_brightness': round(sky_brightness, 1),
                'variation': round(np.std(sky_value) / 255, 3)
            },
            'lighting_analysis': {
                'contrast': round(contrast, 3),
                'avg_brightness': round(avg_value, 1),
                'golden_ratio': round(min(1.0, quality_score / 8), 2)
            },
            'atmospheric_conditions': {
                'visibility_score': round(atmospheric_score, 2),
                'haze_level': round(1 - atmospheric_score, 2)
            },
            'recommendations': generate_photo_recommendations(quality_score, orange_ratio, contrast)
        }

        return analysis

    except Exception as e:
        print(f"照片分析錯誤: {e}")
        return {
            'quality_score': 5.0,
            'error': str(e),
            'color_analysis': {'orange_ratio': 0, 'avg_hue': 0, 'avg_saturation': 0},
            'cloud_analysis': {'cloud_score': 0.5, 'sky_brightness': 128},
            'lighting_analysis': {'contrast': 0.3, 'avg_brightness': 128},
            'atmospheric_conditions': {'visibility_score': 0.5, 'haze_level': 0.5}
        }

def generate_photo_recommendations(quality_score, orange_ratio, contrast):
    """生成照片改進建議"""
    recommendations = []

    if quality_score >= 8:
        recommendations.append("極佳的燒天照片！色彩和光線條件都非常理想")
    elif quality_score >= 6:
        recommendations.append("不錯的燒天照片，基本條件都滿足了")
    elif quality_score >= 4:
        recommendations.append("普通的燒天照片，可以通過後期處理提升效果")
    else:
        recommendations.append("燒天條件一般，建議等待更好的天氣和光線")

    if orange_ratio < 0.1:
        recommendations.append("橙紅色調不足，可以嘗試在日落時段拍攝")
    if contrast < 0.3:
        recommendations.append("對比度可以更高，建議在有雲層的天氣拍攝")
    if orange_ratio > 0.3:
        recommendations.append("色彩非常豐富，這是很好的燒天條件")

    return recommendations

def record_burnsky_photo_case(date, time, location, weather_conditions, visual_rating, prediction_score=None, photo_analysis=None, saved_path=None):
    """記錄燒天照片案例"""
    global BURNSKY_PHOTO_CASES, LAST_CASE_UPDATE

    case_id = f"{date}_{time}_{len(BURNSKY_PHOTO_CASES)}"

    case = {
        'id': case_id,
        'date': date,
        'time': time,
        'location': location,
        'weather_conditions': weather_conditions,
        'visual_rating': visual_rating,
        'prediction_score': prediction_score,
        'photo_analysis': photo_analysis,
        'saved_path': saved_path,
        'recorded_at': datetime.now().isoformat()
    }

    BURNSKY_PHOTO_CASES[case_id] = case
    LAST_CASE_UPDATE = datetime.now()

    print(f"📸 已記錄照片案例: {case_id}")
    return case_id

def analyze_photo_case_patterns():
    """分析照片案例模式"""
    if not BURNSKY_PHOTO_CASES:
        return {
            'total_cases': 0,
            'successful_conditions': [],
            'patterns': {}
        }

    successful_cases = []
    weather_patterns = {}
    time_patterns = {}

    for case_id, case in BURNSKY_PHOTO_CASES.items():
        rating = case.get('visual_rating', 0)
        if rating >= 7:  # 視為成功案例
            successful_cases.append(case)

            # 分析天氣模式
            weather = case.get('weather_conditions', {})
            for key, value in weather.items():
                if key not in weather_patterns:
                    weather_patterns[key] = {}
                weather_patterns[key][str(value)] = weather_patterns[key].get(str(value), 0) + 1

            # 分析時間模式
            time_str = case.get('time', '')
            if ':' in time_str:
                hour = int(time_str.split(':')[0])
                time_patterns[hour] = time_patterns.get(hour, 0) + 1

    return {
        'total_cases': len(BURNSKY_PHOTO_CASES),
        'successful_cases': successful_cases,
        'patterns': {
            'weather_patterns': weather_patterns,
            'time_patterns': time_patterns,
            'success_rate': len(successful_cases) / len(BURNSKY_PHOTO_CASES) if BURNSKY_PHOTO_CASES else 0
        }
    }

def apply_burnsky_photo_corrections(base_score, weather_data, prediction_type):
    """Compatibility helper: photo case similarity has not been validated."""
    return 0


def extract_weather_conditions(weather_data):
    """從天氣數據中提取關鍵條件"""
    conditions = {}

    if weather_data:
        conditions['temperature'] = weather_data.get('temperature')
        conditions['humidity'] = weather_data.get('humidity')
        conditions['visibility'] = weather_data.get('visibility')

        wind = weather_data.get('wind', {})
        if isinstance(wind, dict):
            conditions['wind_speed'] = wind.get('speed')

    return conditions

def calculate_condition_similarity(cond1, cond2):
    """計算兩個條件集合的相似度"""
    if not cond1 or not cond2:
        return 0

    similarities = []
    for key in set(cond1.keys()) & set(cond2.keys()):
        val1 = cond1[key]
        val2 = cond2[key]

        if val1 is not None and val2 is not None:
            try:
                # 數值型比較
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # 計算相似度（越接近1越相似）
                    diff = abs(val1 - val2)
                    if key == 'temperature':
                        similarity = max(0, 1 - diff/10)  # 溫差10度內完全相似
                    elif key == 'humidity':
                        similarity = max(0, 1 - diff/20)  # 濕度差20%內完全相似
                    elif key == 'wind_speed':
                        similarity = max(0, 1 - diff/5)   # 風速差5級內完全相似
                    elif key == 'visibility':
                        similarity = max(0, 1 - diff/5)   # 能見度差5km內完全相似
                    else:
                        similarity = max(0, 1 - diff/max(val1, val2, 1))
                    similarities.append(similarity)
                else:
                    # 字符串比較
                    similarities.append(1.0 if str(val1) == str(val2) else 0.0)
            except:
                similarities.append(0.0)

    return sum(similarities) / len(similarities) if similarities else 0

def is_similar_to_successful_cases(current_conditions):
    """檢查當前條件是否與成功案例相似"""
    patterns = analyze_photo_case_patterns()
    successful_cases = patterns.get('successful_cases', [])

    if not successful_cases:
        return False, 0

    max_similarity = 0
    for case in successful_cases:
        case_conditions = case.get('weather_conditions', {})
        similarity = calculate_condition_similarity(current_conditions, case_conditions)
        max_similarity = max(max_similarity, similarity)

    return max_similarity > 0.6, max_similarity

def initialize_photo_cases():
    """初始化照片案例系統（從數據庫載入）"""
    try:
        import sqlite3
        conn = sqlite3.connect('burnsky_photos.db')
        cursor = conn.cursor()
        
        # 創建照片表（如果不存在）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id TEXT PRIMARY KEY,
                date TEXT,
                time TEXT,
                location TEXT,
                weather_conditions TEXT,
                visual_rating REAL,
                prediction_score REAL,
                photo_analysis TEXT,
                saved_path TEXT,
                recorded_at TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        print("📸 照片案例數據庫已初始化")
        return True
    except Exception as e:
        print(f"⚠️ 初始化照片案例系統失敗: {e}")
        return False
