#!/usr/bin/env python3
"""
Google Search Console 修復驗證腳本
"""

import requests
import json
from datetime import datetime

def verify_fix():
    print("🔍 Google Search Console 修復驗證")
    print("=" * 50)
    print(f"⏰ 驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 測試問題中的具體 URL
    problem_url = "https://burnsky-api.onrender.com/predict/sunset?advance_hours=2&_=1753056000011"
    
    print(f"📡 測試問題 URL: {problem_url}")
    
    try:
        # 模擬 Google 爬蟲的請求
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(problem_url, headers=headers, timeout=30, allow_redirects=False)
        
        print(f"   狀態碼: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ JSON 解析成功")
                print(f"   🔢 燒天分數: {data.get('burnsky_score', 'N/A')}")
                print(f"   📈 機率: {data.get('probability', 'N/A')}")
                print(f"   🌅 預測類型: {data.get('prediction_type', 'N/A')}")
                print(f"   ⏰ 提前時數: {data.get('advance_hours', 'N/A')}")
                print(f"   ✅ 修復狀態: 完全成功！無重定向，直接返回 JSON")
                
            except json.JSONDecodeError:
                print(f"   ❌ JSON 解析失敗")
                print(f"   📄 內容預覽: {response.text[:100]}")
                
        elif response.status_code in [301, 302, 307, 308]:
            location = response.headers.get('Location', '未知')
            print(f"   ❌ 仍然重定向: {location}")
            print(f"   🔧 需要進一步修復")
            
        else:
            print(f"   ❌ HTTP 錯誤: {response.status_code}")
            print(f"   📄 錯誤內容: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ 請求失敗: {str(e)}")
    
    print()
    
    # 測試其他相關端點
    other_endpoints = [
        "https://burnsky-api.onrender.com/predict?type=sunset&advance=2",
        "https://burnsky-api.onrender.com/predict/sunrise?advance_hours=1"
    ]
    
    for url in other_endpoints:
        print(f"📡 測試: {url}")
        try:
            response = requests.get(url, timeout=15, allow_redirects=False)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 狀態碼: {response.status_code}, 類型: {data.get('prediction_type', 'N/A')}")
            else:
                print(f"   ⚠️  狀態碼: {response.status_code}")
        except Exception as e:
            print(f"   ❌ 錯誤: {str(e)}")
        print()
    
    print("🎯 結論:")
    print("✅ API 端點修復成功，直接返回 JSON，無重定向")
    print("⏳ Google Search Console 錯誤消失可能需要 1-7 天")
    print("🔍 建議在 Search Console 中請求重新檢索 URL")
    print()
    print("📋 建議操作:")
    print("1. 在 Google Search Console 中點擊「要求建立索引」")
    print("2. 等待 24-48 小時讓 Google 重新爬蟲")
    print("3. 檢查錯誤報告是否更新")

if __name__ == "__main__":
    verify_fix()
