#!/usr/bin/env python3
"""
檢查問題中提到的 API 端點
"""

import requests
import json
from datetime import datetime

def test_api_endpoints():
    print("🔍 API 端點問題檢查")
    print("=" * 50)
    print(f"⏰ 檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 測試本地和遠端 URL
    base_urls = [
        "http://localhost:5000",
        "https://burnsky-api.onrender.com"
    ]
    
    # 有問題的端點
    problematic_endpoints = [
        "/predict/sunset?advance_hours=2",
        "/predict?type=sunset&advance=2"
    ]
    
    for base_url in base_urls:
        print(f"🌐 測試伺服器: {base_url}")
        print("-" * 40)
        
        for endpoint in problematic_endpoints:
            full_url = base_url + endpoint
            print(f"📡 測試: {endpoint}")
            
            try:
                response = requests.get(full_url, timeout=30, allow_redirects=True)
                print(f"   ✅ 狀態碼: {response.status_code}")
                print(f"   📍 最終 URL: {response.url}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   📊 回應類型: JSON")
                        print(f"   🔢 燒天分數: {data.get('burnsky_score', 'N/A')}")
                        print(f"   📈 機率: {data.get('probability', 'N/A')}")
                    except json.JSONDecodeError:
                        print(f"   ⚠️  回應不是 JSON 格式")
                        print(f"   📄 內容長度: {len(response.text)} 字符")
                        print(f"   📝 前100字符: {response.text[:100]}")
                elif response.status_code in [301, 302, 307, 308]:
                    print(f"   🔄 重定向到: {response.headers.get('Location', '未知')}")
                else:
                    print(f"   ❌ 錯誤狀態")
                    print(f"   📄 回應內容: {response.text[:200]}")
                    
            except requests.exceptions.ConnectionError:
                print(f"   🔌 連線失敗 - 伺服器可能未運行")
            except requests.exceptions.Timeout:
                print(f"   ⏱️  請求超時")
            except Exception as e:
                print(f"   ❌ 其他錯誤: {str(e)}")
            
            print()
        
        print()

if __name__ == "__main__":
    test_api_endpoints()
