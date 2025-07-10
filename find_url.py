#!/usr/bin/env python3
"""
快速檢查燒天預測系統可能的 URL
"""

import requests
import time

def check_possible_urls():
    """檢查可能的 Render URL"""
    
    possible_urls = [
        "https://burnsky-predictor.onrender.com",
        "https://burnsky-api.onrender.com", 
        "https://burnsky.onrender.com",
        "https://burnskyapi.onrender.com"
    ]
    
    print("🔍 檢查可能的 Render URL...")
    print("=" * 50)
    
    for url in possible_urls:
        print(f"\n📡 測試: {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ 找到了！這個 URL 有效")
                print(f"📄 回應內容預覽: {response.text[:100]}...")
                return url
            elif response.status_code == 404:
                # 檢查是否是 Render 的 404 還是應用的 404
                if 'x-render-routing' in response.headers:
                    if response.headers['x-render-routing'] == 'no-server':
                        print(f"❌ Render 找不到服務")
                    else:
                        print(f"⚠️  服務存在但路由有問題")
                else:
                    print(f"📱 可能是應用層的 404")
            else:
                print(f"⚠️  狀態碼: {response.status_code}")
        except requests.exceptions.ConnectTimeout:
            print(f"⏰ 連接超時")
        except requests.exceptions.ConnectionError:
            print(f"🔌 連接失敗")
        except Exception as e:
            print(f"💥 錯誤: {str(e)}")
    
    print(f"\n❌ 沒有找到可用的 URL")
    return None

if __name__ == "__main__":
    print("🔥 燒天預測系統 URL 檢測工具")
    print()
    
    found_url = check_possible_urls()
    
    if found_url:
        print(f"\n🎉 成功！您的網站在: {found_url}")
        print(f"💡 請更新診斷腳本和文檔中的 URL")
    else:
        print(f"\n🚨 沒有找到可用的服務")
        print(f"請檢查:")
        print(f"1. 前往 Render Dashboard 確認服務狀態")
        print(f"2. 確認服務沒有被刪除")
        print(f"3. 檢查部署是否成功")
        print(f"4. 可能需要重新創建服務")
