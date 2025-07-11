#!/usr/bin/env python3
"""
診斷前端天氣數據顯示問題
"""
import requests
import json

def diagnose_weather_display():
    print("🔍 診斷前端天氣數據顯示...")
    
    try:
        # 測試API
        api_url = "http://127.0.0.1:8080/predict/sunset?advance_hours=1"
        response = requests.get(api_url)
        
        if response.status_code != 200:
            print(f"❌ API錯誤: {response.status_code}")
            return
        
        data = response.json()
        weather_data = data.get('weather_data', {})
        
        print("✅ API 正常回應")
        print(f"🌡️ 燒天分數: {data.get('burnsky_score', 'N/A')}")
        
        # 檢查各項天氣數據
        print("\n📊 天氣數據檢查:")
        
        # 溫度
        if 'temperature' in weather_data and 'data' in weather_data['temperature']:
            hko_temp = None
            for temp in weather_data['temperature']['data']:
                if temp['place'] == '香港天文台':
                    hko_temp = temp['value']
                    break
            if hko_temp:
                print(f"🌡️ 溫度: {hko_temp}°C (天文台)")
            else:
                print("⚠️ 沒有找到天文台溫度數據")
        else:
            print("❌ 沒有溫度數據")
        
        # 濕度
        if 'humidity' in weather_data and 'data' in weather_data['humidity']:
            hko_humidity = None
            for humidity in weather_data['humidity']['data']:
                if humidity['place'] == '香港天文台':
                    hko_humidity = humidity['value']
                    break
            if hko_humidity:
                print(f"💧 濕度: {hko_humidity}% (天文台)")
            else:
                print("⚠️ 沒有找到天文台濕度數據")
        else:
            print("❌ 沒有濕度數據")
        
        # UV指數
        if 'uvindex' in weather_data and 'data' in weather_data['uvindex']:
            uv_value = weather_data['uvindex']['data'][0]['value'] if weather_data['uvindex']['data'] else None
            if uv_value is not None:
                print(f"☀️ UV指數: {uv_value}")
            else:
                print("⚠️ UV指數數據為空")
        else:
            print("❌ 沒有UV指數數據")
        
        # 天氣圖標
        if 'icon' in weather_data and weather_data['icon']:
            icon_code = weather_data['icon'][0] if weather_data['icon'] else None
            if icon_code:
                print(f"🌤️ 天氣圖標代碼: {icon_code}")
            else:
                print("⚠️ 天氣圖標代碼為空")
        else:
            print("❌ 沒有天氣圖標數據")
        
        # 降雨量
        if 'rainfall' in weather_data and 'data' in weather_data['rainfall']:
            total_rainfall = 0
            for rain in weather_data['rainfall']['data']:
                if isinstance(rain, dict) and 'value' in rain and rain['value'] > 0:
                    total_rainfall += rain['value']
            print(f"🌧️ 降雨量: {total_rainfall:.1f}mm")
        else:
            print("❌ 沒有降雨量數據")
        
        # 天氣警告
        if 'warningMessage' in weather_data and weather_data['warningMessage']:
            print(f"⚠️ 天氣警告: {len(weather_data['warningMessage'])}個")
            for warning in weather_data['warningMessage']:
                print(f"   - {warning[:50]}...")
        else:
            print("✅ 沒有天氣警告")
        
        print("\n🎯 前端JavaScript檢查建議:")
        print("1. 開啟瀏覽器開發者工具 (F12)")
        print("2. 檢查 Console 是否有JavaScript錯誤")
        print("3. 確認 weatherData 容器是否存在")
        print("4. 檢查 updateWeatherData() 函數是否正常執行")
        print("5. 驗證天氣卡片的HTML是否正確生成")
        
    except Exception as e:
        print(f"❌ 診斷過程出錯: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_weather_display()
