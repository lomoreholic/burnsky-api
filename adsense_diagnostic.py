#!/usr/bin/env python3
"""
AdSense ads.txt 診斷工具
檢查 ads.txt 文件是否正確配置
"""

import requests
import sys
from urllib.parse import urljoin

def check_ads_txt(domain):
    """檢查指定域名的 ads.txt 文件"""
    
    # 確保域名格式正確
    if not domain.startswith('http'):
        domain = f"https://{domain}"
    
    ads_txt_url = urljoin(domain, '/ads.txt')
    
    print(f"🔍 檢查 AdSense ads.txt 文件")
    print(f"📍 URL: {ads_txt_url}")
    print("=" * 50)
    
    try:
        # 發送請求
        response = requests.get(ads_txt_url, timeout=10)
        
        print(f"✅ HTTP 狀態碼: {response.status_code}")
        print(f"✅ Content-Type: {response.headers.get('Content-Type', 'Not set')}")
        
        if response.status_code == 200:
            content = response.text.strip()
            print(f"✅ 文件內容:")
            print(f"   {content}")
            
            # 檢查內容格式
            if 'google.com' in content and 'ca-pub-' in content:
                print("✅ ads.txt 格式正確")
                
                # 提取 Publisher ID
                if 'ca-pub-3552699426860096' in content:
                    print("✅ Publisher ID 匹配")
                else:
                    print("⚠️  請確認 Publisher ID 是否正確")
                    
                if 'DIRECT' in content:
                    print("✅ 關係類型為 DIRECT")
                else:
                    print("⚠️  關係類型不是 DIRECT")
                    
            else:
                print("❌ ads.txt 格式可能有問題")
        else:
            print(f"❌ 無法訪問 ads.txt 文件 (狀態碼: {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 請求失敗: {e}")
    
    print("\n" + "=" * 50)
    print("📋 AdSense 排除故障建議:")
    print("1. 確保在 AdSense 中設定的網站 URL 與實際域名一致")
    print("2. 等待 24-48 小時讓 Google 重新爬取")
    print("3. 檢查是否有防火牆或 CDN 阻止 Google 爬蟲")
    print("4. 確認沒有 robots.txt 阻止爬取 /ads.txt")

def main():
    domains_to_check = [
        "burnsky-api.onrender.com",
        "127.0.0.1:8080"  # 本地測試
    ]
    
    for domain in domains_to_check:
        check_ads_txt(domain)
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
