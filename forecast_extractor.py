"""
未來時段天氣數據提取模組
解決香港天文台 API 不提供小時級未來數據的問題
"""

import json
from datetime import datetime, timedelta
import pytz
import re

class ForecastExtractor:
    """處理未來時段天氣數據的提取和推算"""
    
    def __init__(self):
        self.hk_tz = pytz.timezone('Asia/Hong_Kong')
    
    def extract_future_weather_data(self, weather_data, forecast_data, ninday_data, advance_hours):
        """
        提取或推算未來時段的天氣數據
        
        Args:
            weather_data: 即時天氣數據
            forecast_data: 天氣預報數據  
            ninday_data: 九天預報數據
            advance_hours: 提前小時數
            
        Returns:
            dict: 未來時段的天氣數據（模擬結構）
        """
        if advance_hours <= 0:
            return weather_data
        
        current_time = datetime.now(self.hk_tz).replace(tzinfo=None)
        target_time = current_time + timedelta(hours=advance_hours)
        target_date = target_time.strftime('%Y%m%d')
        
        # 基礎天氣數據複製（保持結構一致性）
        future_data = {
            'updateTime': target_time.strftime('%Y-%m-%dT%H:%M:%S+08:00'),
            'temperature': weather_data.get('temperature', {}),
            'humidity': weather_data.get('humidity', {}),
            'rainfall': weather_data.get('rainfall', {}),
            'uvindex': weather_data.get('uvindex', {}),
            'icon': weather_data.get('icon', []),
            'wind': weather_data.get('wind', {})  # 保留風速數據
        }
        
        # 1. 從九天預報獲取對應日期的天氣資訊
        daily_forecast = self._find_daily_forecast(ninday_data, target_date)
        
        # 2. 調整溫度數據
        future_data['temperature'] = self._adjust_temperature_data(
            weather_data.get('temperature', {}), 
            daily_forecast,
            advance_hours,
            target_time
        )
        
        # 3. 調整濕度數據
        future_data['humidity'] = self._adjust_humidity_data(
            weather_data.get('humidity', {}),
            daily_forecast,
            advance_hours
        )
        
        # 4. 調整 UV 指數
        future_data['uvindex'] = self._adjust_uv_data(
            weather_data.get('uvindex', {}),
            target_time,
            daily_forecast
        )
        
        # 5. 保持降雨數據不變（短期預測）
        future_data['rainfall'] = weather_data.get('rainfall', {})
        
        # 6. 保持圖標數據（可能會根據預報調整）
        future_data['icon'] = weather_data.get('icon', [])
        
        return future_data
    
    def _find_daily_forecast(self, ninday_data, target_date):
        """從九天預報中找到目標日期的預報"""
        if not ninday_data or 'weatherForecast' not in ninday_data:
            return None
            
        for forecast in ninday_data['weatherForecast']:
            if forecast.get('forecastDate') == target_date:
                return forecast
        return None
    
    def _adjust_temperature_data(self, current_temp_data, daily_forecast, advance_hours, target_time):
        """調整溫度數據"""
        if not current_temp_data or 'data' not in current_temp_data:
            return current_temp_data
        
        # 複製現有溫度數據結構
        adjusted_temp = json.loads(json.dumps(current_temp_data, ensure_ascii=False))
        
        # 時間因子調整（基於小時變化的溫度趨勢）
        hour = target_time.hour
        time_adjustment = 0
        
        # 根據時間計算基本溫度變化趨勢
        if 6 <= hour <= 12:  # 上午升溫期
            time_adjustment = (hour - 6) * 0.3  # 每小時升溫 0.3°C
        elif 12 < hour <= 15:  # 中午高溫期
            time_adjustment = 2.0  # 高溫期
        elif 15 < hour <= 18:  # 下午降溫期
            time_adjustment = 2.0 - (hour - 15) * 0.4  # 逐漸降溫
        elif 18 < hour <= 22:  # 晚上降溫期
            time_adjustment = -0.5 - (hour - 18) * 0.2
        else:  # 夜間和清晨
            time_adjustment = -1.5  # 夜間較涼
        
        # 如果有九天預報數據，進一步調整
        if daily_forecast:
            min_temp = daily_forecast.get('forecastMintemp', {}).get('value', 25)
            max_temp = daily_forecast.get('forecastMaxtemp', {}).get('value', 30)
            
            # 根據預報的溫度範圍，額外調整
            forecast_adjustment = 0
            if hour >= 12 and hour <= 16:  # 下午時段使用最高溫
                target_temp = max_temp
                current_avg = sum(d['value'] for d in adjusted_temp['data']) / len(adjusted_temp['data'])
                forecast_adjustment = (target_temp - current_avg) * 0.3  # 30% 調整
            elif hour <= 6 or hour >= 22:  # 清晨/夜間使用最低溫
                target_temp = min_temp
                current_avg = sum(d['value'] for d in adjusted_temp['data']) / len(adjusted_temp['data'])
                forecast_adjustment = (target_temp - current_avg) * 0.3
            
            time_adjustment += forecast_adjustment
        
        # 調整所有地點的溫度數據
        for location_data in adjusted_temp['data']:
            if 'value' in location_data:
                new_temp = location_data['value'] + time_adjustment
                # 限制在合理範圍內
                location_data['value'] = round(max(15, min(40, new_temp)), 1)
        
        return adjusted_temp
    
    def _adjust_humidity_data(self, current_humidity_data, daily_forecast, advance_hours):
        """調整濕度數據"""
        if not current_humidity_data or 'data' not in current_humidity_data:
            return current_humidity_data
        
        # 複製現有濕度數據
        adjusted_humidity = json.loads(json.dumps(current_humidity_data, ensure_ascii=False))
        
        # 簡單的濕度趨勢調整
        # 如果預報顯示雨天，濕度可能上升
        if daily_forecast and daily_forecast.get('forecastWeather'):
            weather_desc = daily_forecast['forecastWeather']
            humidity_adjustment = 0
            
            if any(keyword in weather_desc for keyword in ['雨', '雷暴', '陣雨']):
                humidity_adjustment = 5  # 雨天濕度上升
            elif any(keyword in weather_desc for keyword in ['晴', '天晴']):
                humidity_adjustment = -3  # 晴天濕度下降
            
            # 調整所有地點的濕度
            for location_data in adjusted_humidity['data']:
                if 'value' in location_data:
                    new_humidity = max(30, min(95, location_data['value'] + humidity_adjustment))
                    location_data['value'] = new_humidity
        
        return adjusted_humidity
    
    def _adjust_uv_data(self, current_uv_data, target_time, daily_forecast):
        """調整 UV 指數數據"""
        if not current_uv_data:
            return current_uv_data
        
        adjusted_uv = dict(current_uv_data)
        
        # 根據時間調整 UV 指數
        hour = target_time.hour
        if 6 <= hour <= 18:  # 白天
            # UV 指數在正午最高
            time_factor = 1.0 - abs(12 - hour) / 6.0  # 12點為峰值
            
            # 根據天氣預報調整
            cloud_factor = 1.0
            if daily_forecast and daily_forecast.get('forecastWeather'):
                weather_desc = daily_forecast['forecastWeather']
                if any(keyword in weather_desc for keyword in ['雲', '陰', '雨']):
                    cloud_factor = 0.6  # 多雲/雨天 UV 降低
                elif '晴' in weather_desc:
                    cloud_factor = 1.2  # 晴天 UV 較高
            
            if 'value' in adjusted_uv:
                base_uv = adjusted_uv['value']
                adjusted_uv['value'] = max(0, round(base_uv * time_factor * cloud_factor))
        else:  # 夜間
            adjusted_uv['value'] = 0
        
        return adjusted_uv

# 全域實例
forecast_extractor = ForecastExtractor()
