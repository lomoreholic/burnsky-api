#!/usr/bin/env python3
"""
🔍 AdSense Publisher ID 診斷工具
幫助確定正確的 Publisher ID 並修復 ads.txt 問題
"""

import requests
import re

def diagnose_adsense_publisher_id():
    """診斷 AdSense Publisher ID 問題"""
    
    print("🔍 AdSense Publisher ID 診斷")
    print("=" * 50)
    
    # 1. 檢查當前 ads.txt
    print("\n📋 1. 當前 ads.txt 文件分析")
    try:
        response = requests.get("https://burnsky-api.onrender.com/ads.txt", timeout=10)
        if response.status_code == 200:
            content = response.text.strip()
            print(f"✅ 文件可訪問")
            print(f"📄 當前內容:")
            for line in content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    print(f"   {line}")
            
            # 提取 Publisher ID
            pub_match = re.search(r'ca-pub-(\d+)', content)
            if pub_match:
                current_pub_id = f"ca-pub-{pub_match.group(1)}"
                print(f"\n🆔 檢測到的 Publisher ID: {current_pub_id}")
            else:
                print("\n❌ 未找到有效的 Publisher ID")
        else:
            print(f"❌ 無法訪問 ads.txt (狀態碼: {response.status_code})")
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
    
    # 2. 檢查網站 meta tag
    print("\n🏠 2. 網站 Meta Tag 檢查")
    try:
        response = requests.get("https://burnsky-api.onrender.com", timeout=10)
        if response.status_code == 200:
            html = response.text
            meta_match = re.search(r'name="google-adsense-account" content="(ca-pub-\d+)"', html)
            if meta_match:
                meta_pub_id = meta_match.group(1)
                print(f"✅ Meta tag Publisher ID: {meta_pub_id}")
            else:
                print("⚠️  未找到 AdSense Meta Tag")
        else:
            print(f"❌ 無法訪問主頁")
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
    
    # 3. 常見問題和解決方案
    print("\n🔧 3. 常見問題診斷")
    
    problems_solutions = [
        {
            "problem": "Publisher ID 不匹配",
            "solution": "確保 ads.txt 中的 ID 與 AdSense 帳戶中顯示的完全一致",
            "action": "登入 AdSense > 帳戶 > 帳戶資訊，複製正確的 Publisher ID"
        },
        {
            "problem": "AdSense 帳戶未完全設置",
            "solution": "需要先在 AdSense 中添加和驗證網站",
            "action": "前往 AdSense > 網站 > 添加網站 > 輸入 burnsky-api.onrender.com"
        },
        {
            "problem": "網站驗證未完成",
            "solution": "需要完成網站所有權驗證",
            "action": "在 AdSense 中選擇 HTML Meta Tag 方式驗證"
        },
        {
            "problem": "ads.txt 格式錯誤",
            "solution": "確保格式完全符合 Google 標準",
            "action": "使用格式: google.com, ca-pub-XXXXXXXXXX, DIRECT, f08c47fec0942fa0"
        }
    ]
    
    for i, item in enumerate(problems_solutions, 1):
        print(f"\n❓ 問題 {i}: {item['problem']}")
        print(f"💡 解決方案: {item['solution']}")
        print(f"🔧 行動: {item['action']}")
    
    # 4. 操作指南
    print("\n📝 4. 修復步驟指南")
    print("請按照以下步驟操作:")
    print()
    print("Step 1: 確認您的 AdSense Publisher ID")
    print("   1. 登入 Google AdSense (https://adsense.google.com)")
    print("   2. 前往 帳戶 > 帳戶資訊")
    print("   3. 複製顯示的 Publisher ID (格式: ca-pub-XXXXXXXXXX)")
    print()
    print("Step 2: 添加/驗證網站 (如果還沒做)")
    print("   1. 在 AdSense 中點擊 '網站' > '添加網站'")
    print("   2. 輸入: https://burnsky-api.onrender.com")
    print("   3. 選擇 'HTML Meta Tag' 驗證方式")
    print("   4. 複製提供的 meta tag")
    print()
    print("Step 3: 更新 ads.txt 文件")
    print("   1. 告訴我您的正確 Publisher ID")
    print("   2. 我會幫您更新 ads.txt 文件")
    print("   3. 推送更新到伺服器")
    print()
    print("Step 4: 等待驗證")
    print("   1. 等待 24-48 小時")
    print("   2. 檢查 AdSense 狀態更新")
    
    print("\n" + "=" * 50)
    print("🎯 請告訴我您從 AdSense 帳戶中看到的正確 Publisher ID")
    print("格式應該是: ca-pub-XXXXXXXXXXXXXXXXX")

if __name__ == "__main__":
    diagnose_adsense_publisher_id()
