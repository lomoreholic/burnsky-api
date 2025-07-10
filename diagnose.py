#!/usr/bin/env python3
"""
燒天預測系統診斷工具
用於排查網站載入問題
"""

import requests
import time
import sys
from datetime import datetime

def check_url_status(url, timeout=10):
    """檢查 URL 狀態"""
    try:
        print(f"🔍 檢查: {url}")
        start_time = time.time()
        response = requests.get(url, timeout=timeout)
        response_time = time.time() - start_time
        
        print(f"   狀態碼: {response.status_code}")
        print(f"   響應時間: {response_time:.2f}s")
        print(f"   內容長度: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print(f"   ✅ 成功")
            return True
        else:
            print(f"   ❌ 失敗")
            if response.status_code == 404:
                print(f"   💡 404錯誤：路由不存在，可能是部署問題")
            elif response.status_code == 500:
                print(f"   💡 500錯誤：伺服器內部錯誤，檢查日誌")
            elif response.status_code >= 502:
                print(f"   💡 5xx錯誤：服務器連接問題")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏰ 超時")
        return False
    except requests.exceptions.ConnectionError:
        print(f"   🔌 連接失敗")
        return False
    except Exception as e:
        print(f"   💥 錯誤: {str(e)}")
        return False

def main():
    print("🔥 燒天預測系統診斷工具")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 檢查的 URL 列表
    urls_to_check = [
        "https://burnsky-predictor.onrender.com",
        "https://burnsky-predictor.onrender.com/test",
        "https://burnsky-predictor.onrender.com/predict",
        "https://burnsky-predictor.onrender.com/api",
    ]
    
    if len(sys.argv) > 1:
        custom_url = sys.argv[1]
        urls_to_check = [
            custom_url,
            f"{custom_url}/test",
            f"{custom_url}/predict",
            f"{custom_url}/api",
        ]
    
    results = []
    
    for url in urls_to_check:
        result = check_url_status(url)
        results.append((url, result))
        print()
        time.sleep(1)  # 避免請求過快
    
    # 總結
    print("=" * 50)
    print("📋 診斷總結:")
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for url, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {url}")
    
    print(f"\n📊 成功率: {success_count}/{total_count}")
    
    if success_count == 0:
        print("\n🚨 所有測試都失敗了！")
        print("可能的原因：")
        print("1. 服務未啟動或部署失敗")
        print("2. Render 服務被暫停（免費方案30分鐘無活動會暫停）")
        print("3. 代碼有語法錯誤或運行時錯誤")
        print("4. 依賴包缺失或版本不兼容")
        print("\n💡 建議解決步驟：")
        print("1. 檢查 Render Dashboard 的部署日誌")
        print("2. 等待 3-5 分鐘讓服務完全啟動")
        print("3. 重新觸發部署")
    elif success_count < total_count:
        print(f"\n⚠️  部分功能有問題")
        print("某些端點無法訪問，檢查路由配置")
    else:
        print(f"\n🎉 所有測試通過！網站運作正常")

if __name__ == "__main__":
    main()
