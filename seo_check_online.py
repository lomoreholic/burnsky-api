#!/usr/bin/env python3
"""
BurnSky SEO 線上檢查工具
檢查部署在 Render 的燒天預測系統 SEO 優化狀況
"""

import requests
from urllib.parse import urljoin
import re

def check_seo_elements(url):
    """檢查網頁的 SEO 元素"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=15, headers=headers)
        
        if response.status_code != 200:
            return f"❌ 頁面無法訪問 ({response.status_code})"
        
        content = response.text.lower()
        results = []
        
        # 基本 SEO 檢查
        seo_checks = {
            "Title 標籤": "<title>" in content and "燒天預測" in content,
            "Meta Description": 'name="description"' in content and len(re.findall(r'name="description"[^>]*content="[^"]{120,160}"', content)) > 0,
            "Meta Keywords": 'name="keywords"' in content,
            "Viewport": 'name="viewport"' in content,
            "Language": 'lang="zh-tw"' in content,
            "Charset": 'charset="utf-8"' in content
        }
        
        # Open Graph 檢查
        og_checks = {
            "OG Title": 'property="og:title"' in content,
            "OG Description": 'property="og:description"' in content,
            "OG Image": 'property="og:image"' in content,
            "OG URL": 'property="og:url"' in content,
            "OG Type": 'property="og:type"' in content
        }
        
        # Twitter Card 檢查
        twitter_checks = {
            "Twitter Card": 'name="twitter:card"' in content,
            "Twitter Title": 'name="twitter:title"' in content,
            "Twitter Description": 'name="twitter:description"' in content,
            "Twitter Image": 'name="twitter:image"' in content
        }
        
        # 結構化數據檢查
        structured_data_checks = {
            "JSON-LD Script": 'type="application/ld+json"' in content,
            "Schema.org": '"@context": "https://schema.org"' in content,
            "WebApplication Type": '"@type": "webapplication"' in content or '"@type": "webapp"' in content
        }
        
        # 語義化 HTML 檢查
        semantic_checks = {
            "Header Tag": "<header" in content,
            "Main Tag": "<main" in content,
            "Nav Tag": "<nav" in content,
            "Section Tag": "<section" in content,
            "Footer Tag": "<footer" in content,
            "Article Tag": "<article" in content
        }
        
        # 技術 SEO 檢查
        technical_checks = {
            "Canonical URL": 'rel="canonical"' in content,
            "Robots Meta": 'name="robots"' in content,
            "H1 Tag": "<h1" in content,
            "Alt Attributes": 'alt="' in content
        }
        
        # 輸出結果
        print(f"\n🔍 SEO 檢查報告: {url}")
        print("=" * 60)
        
        all_categories = [
            ("📄 基本 SEO", seo_checks),
            ("📱 Open Graph", og_checks),
            ("🐦 Twitter Card", twitter_checks),
            ("📊 結構化數據", structured_data_checks),
            ("🏗️ 語義化 HTML", semantic_checks),
            ("⚙️ 技術 SEO", technical_checks)
        ]
        
        total_checks = 0
        passed_checks = 0
        
        for category_name, checks in all_categories:
            print(f"\n{category_name}:")
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check_name}")
                total_checks += 1
                if passed:
                    passed_checks += 1
        
        # 計算 SEO 分數
        seo_score = round((passed_checks / total_checks) * 100)
        print(f"\n🎯 SEO 分數: {seo_score}/100")
        
        # 性能檢查
        print(f"\n⚡ 性能指標:")
        print(f"  📏 頁面大小: {len(response.content) / 1024:.1f} KB")
        print(f"  ⏱️ 載入時間: {response.elapsed.total_seconds():.2f} 秒")
        
        return seo_score
        
    except Exception as e:
        return f"❌ 檢查失敗: {str(e)}"

def main():
    """主函數"""
    print("🔥 BurnSky SEO 線上檢查工具")
    print("=" * 50)
    
    # 檢查線上版本
    base_url = "https://burnsky-api.onrender.com"
    
    # 檢查主要頁面
    pages = [
        {"url": "/", "name": "主頁"},
        {"url": "/privacy", "name": "私隱政策"},
        {"url": "/terms", "name": "使用條款"}
    ]
    
    for page in pages:
        url = urljoin(base_url, page["url"])
        score = check_seo_elements(url)
        print(f"\n📊 {page['name']} SEO 分數: {score}")
    
    # 檢查技術文件
    print("\n\n🤖 技術文件檢查:")
    print("=" * 30)
    
    tech_files = [
        {"url": "/robots.txt", "name": "Robots.txt"},
        {"url": "/sitemap.xml", "name": "Sitemap.xml"},
        {"url": "/ads.txt", "name": "Ads.txt"}
    ]
    
    for file in tech_files:
        url = urljoin(base_url, file["url"])
        try:
            response = requests.get(url, timeout=10)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {file['name']}: {response.status_code}")
            if response.status_code == 200:
                print(f"    📏 大小: {len(response.text)} 字元")
        except Exception as e:
            print(f"❌ {file['name']}: 檢查失敗 - {str(e)}")
    
    # API 端點檢查
    print("\n\n🔗 API 端點檢查:")
    print("=" * 20)
    
    api_endpoints = [
        {"url": "/predict", "name": "燒天預測"},
        {"url": "/predict/sunset", "name": "日落預測"},
        {"url": "/predict/sunrise", "name": "日出預測"},
        {"url": "/api", "name": "API 資訊"}
    ]
    
    for endpoint in api_endpoints:
        url = urljoin(base_url, endpoint["url"])
        try:
            response = requests.get(url, timeout=15)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"{status} {endpoint['name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint['name']}: 檢查失敗")
    
    print("\n\n🎉 SEO 檢查完成！")
    print("📈 建議下一步:")
    print("1. 提交 sitemap.xml 到 Google Search Console")
    print("2. 設置 Google Analytics")
    print("3. 優化圖片 ALT 標籤")
    print("4. 增加內部連結")
    print("5. 創建更多內容頁面")

if __name__ == "__main__":
    main()
