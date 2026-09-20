import requests
from datetime import datetime
import re

# 香港天文台 API URL
WEATHER_API_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=tc"
FORECAST_API_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=flw&lang=tc"
NINDAY_FORECAST_API_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=tc"
WARNING_API_URL = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=warningInfo&lang=tc"

# 香港天文台天氣圖標代碼對照表
HKO_WEATHER_ICONS = {
    50: "晴朗",
    51: "部分時間有陽光",
    52: "短暫時間有陽光",
    53: "部分時間有陽光，有一兩陣驟雨",
    54: "短暫時間有陽光，有幾陣驟雨", 
    60: "多雲",
    61: "密雲",
    62: "微雨",
    63: "雨",
    64: "大致多雲，有雷暴",
    65: "雷暴",
    70: "天色良好",
    71: "天色良好",
    72: "天色良好",
    73: "天色良好",
    74: "天色良好",
    75: "薄霧",
    76: "霧",
    77: "薄霧",
    80: "大風",
    81: "乾燥",
    82: "潮濕",
    83: "霜凍",
    90: "熱",
    91: "暖",
    92: "涼",
    93: "冷"
}

def get_weather_icon_description(icon_code):
    """
    根據圖標代碼獲取天氣描述
    
    Args:
        icon_code: 香港天文台天氣圖標代碼
    
    Returns:
        str: 天氣描述
    """
    return HKO_WEATHER_ICONS.get(icon_code, f"未知天氣狀況 (代碼: {icon_code})")

def fetch_weather_data():
    url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=rhrread&lang=tc"
    
    # 添加請求頭來模擬瀏覽器請求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.hko.gov.hk/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP 錯誤：{err}")
        print(f"狀態碼：{response.status_code}")
        return {}
    except requests.exceptions.RequestException as err:
        print(f"請求錯誤：{err}")
        return {}

def fetch_forecast_data():
    """獲取天氣預報數據"""
    url = FORECAST_API_URL
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.hko.gov.hk/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"預報數據 HTTP 錯誤：{err}")
        print(f"狀態碼：{response.status_code}")
        return {}
    except requests.exceptions.RequestException as err:
        print(f"預報數據請求錯誤：{err}")
        return {}

def fetch_ninday_forecast():
    """獲取九天天氣預報"""
    url = NINDAY_FORECAST_API_URL
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.hko.gov.hk/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"九天預報 HTTP 錯誤：{err}")
        print(f"狀態碼：{response.status_code}")
        return {}
    except requests.exceptions.RequestException as err:
        print(f"九天預報請求錯誤：{err}")
        return {}

def fetch_warning_data():
    """獲取天氣警告信息"""
    url = WARNING_API_URL
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.hko.gov.hk/'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"警告數據 HTTP 錯誤：{err}")
        print(f"狀態碼：{response.status_code}")
        return {}
    except requests.exceptions.RequestException as err:
        print(f"警告數據請求錯誤：{err}")
        return {}

def parse_wind_info(wind_text):
    """
    解析香港天文台的風速文字描述
    
    Args:
        wind_text: 風速描述文字，例如 "西南風3至4級"
    
    Returns:
        dict: 包含風向、風級等資訊
    """
    wind_info = {
        'direction': '',
        'speed_beaufort_min': 0,
        'speed_beaufort_max': 0,
        'speed_kmh_min': 0,
        'speed_kmh_max': 0,
        'description': wind_text
    }
    
    if not wind_text:
        return wind_info
    
    # 風向對照表
    direction_map = {
        '北': 'N', '東北': 'NE', '東': 'E', '東南': 'SE',
        '南': 'S', '西南': 'SW', '西': 'W', '西北': 'NW',
        '偏北': 'N', '偏東北': 'NE', '偏東': 'E', '偏東南': 'SE',
        '偏南': 'S', '偏西南': 'SW', '偏西': 'W', '偏西北': 'NW'
    }
    
    # 蒲福風級對應風速（公里/小時）
    beaufort_to_kmh = {
        0: (0, 1), 1: (1, 5), 2: (6, 11), 3: (12, 19), 4: (20, 28),
        5: (29, 38), 6: (39, 49), 7: (50, 61), 8: (62, 74), 9: (75, 88),
        10: (89, 102), 11: (103, 117), 12: (118, 133)
    }
    
    # 提取風向 - 按長度排序，優先匹配較長的風向詞（如"西南"優先於"南"）
    sorted_directions = sorted(direction_map.items(), key=lambda x: len(x[0]), reverse=True)
    for cn_dir, en_dir in sorted_directions:
        if cn_dir in wind_text:
            wind_info['direction'] = en_dir
            break
    
    # 提取風級範圍（例如："3至4級" 或 "4級"）
    wind_level_pattern = r'(\d+)(?:至(\d+))?級'
    match = re.search(wind_level_pattern, wind_text)
    
    if match:
        min_level = int(match.group(1))
        max_level = int(match.group(2)) if match.group(2) else min_level
        
        wind_info['speed_beaufort_min'] = min_level
        wind_info['speed_beaufort_max'] = max_level
        
        # 轉換為公里/小時
        if min_level in beaufort_to_kmh:
            wind_info['speed_kmh_min'] = beaufort_to_kmh[min_level][0]
        if max_level in beaufort_to_kmh:
            wind_info['speed_kmh_max'] = beaufort_to_kmh[max_level][1]
    
    return wind_info

def get_current_wind_data():
    """
    從九天天氣預報中獲取今日風速資訊
    
    Returns:
        dict: 風速資訊
    """
    try:
        forecast_data = fetch_ninday_forecast()
        
        if forecast_data and 'weatherForecast' in forecast_data:
            # 獲取今日或最近的預報
            today_forecast = forecast_data['weatherForecast'][0]
            
            if 'forecastWind' in today_forecast:
                wind_text = today_forecast['forecastWind']
                return parse_wind_info(wind_text)
        
        return {
            'direction': '',
            'speed_beaufort_min': 0,
            'speed_beaufort_max': 0,
            'speed_kmh_min': 0,
            'speed_kmh_max': 0,
            'description': ''
        }
    except Exception as e:
        print(f"獲取風速數據錯誤：{e}")
        return {
            'direction': '',
            'speed_beaufort_min': 0,
            'speed_beaufort_max': 0,
            'speed_kmh_min': 0,
            'speed_kmh_max': 0,
            'description': ''
        }

def test_apis():
    """測試 API 連接"""
    print("正在測試香港天文台 API 連接...")
    
    # 測試天氣數據
    print("\n--- 測試即時天氣數據 API ---")
    weather_data = fetch_weather_data()
    if weather_data:
        print("✅ 即時天氣數據獲取成功")
        print(f"數據鍵值: {list(weather_data.keys())}")
        if 'temperature' in weather_data:
            print(f"溫度數據: {len(weather_data['temperature']['data'])} 個地點")
    else:
        print("❌ 即時天氣數據獲取失敗")
    
    # 測試天氣預報數據
    print("\n--- 測試天氣預報數據 API ---")
    forecast_data = fetch_forecast_data()
    if forecast_data:
        print("✅ 天氣預報數據獲取成功")
        print(f"數據鍵值: {list(forecast_data.keys())}")
        if 'forecastDesc' in forecast_data:
            print(f"預報描述: {forecast_data['forecastDesc']}")
    else:
        print("❌ 天氣預報數據獲取失敗")
    
    # 測試九天預報數據
    print("\n--- 測試九天預報數據 API ---")
    ninday_data = fetch_ninday_forecast()
    if ninday_data:
        print("✅ 九天預報數據獲取成功")
        print(f"數據鍵值: {list(ninday_data.keys())}")
        if 'weatherForecast' in ninday_data:
            print(f"九天預報: {len(ninday_data['weatherForecast'])} 天")
    else:
        print("❌ 九天預報數據獲取失敗")
    
    # 測試警告數據
    print("\n--- 測試天氣警告數據 API ---")
    warning_data = fetch_warning_data()
    if warning_data:
        print("✅ 天氣警告數據獲取成功")
        print(f"數據鍵值: {list(warning_data.keys())}")
    else:
        print("❌ 天氣警告數據獲取失敗")
    
    # 測試風速數據
    print("\n--- 測試風速數據 ---")
    wind_data = get_current_wind_data()
    if wind_data:
        print("✅ 風速數據獲取成功")
        print(f"數據鍵值: {list(wind_data.keys())}")
        print(f"風向: {wind_data['direction']}, 風速: {wind_data['speed_kmh_min']} - {wind_data['speed_kmh_max']} 公里/小時")
    else:
        print("❌ 風速數據獲取失敗")

if __name__ == "__main__":
    test_apis()
