import requests
import pandas as pd
from datetime import datetime

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

if __name__ == "__main__":
    test_apis()
