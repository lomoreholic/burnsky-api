#!/usr/bin/env python3
"""
批量更新所有HTML文件的導航連結
"""

import os
import re

# 正確的導航HTML結構
CORRECT_NAV_HTML = '''            <div class="nav-row">
                <a href="/" class="nav-link">🏠 首頁</a>
                <a href="/warning-dashboard" class="nav-link">⚠️ 警告台</a>
                <a href="/photo-analysis" class="nav-link">📷 照片分析</a>
            </div>
            <div class="nav-row">
                <a href="/best-locations" class="nav-link">🏔️ 最佳位置</a>
                <a href="/photography-guide" class="nav-link">📸 攝影指南</a>
                <a href="/weather-terms" class="nav-link">🌤️ 天氣術語</a>
            </div>
            <div class="nav-row">
                <a href="/faq" class="nav-link">❓ 常見問答</a>
                <a href="/api-docs" class="nav-link">📚 API 文檔</a>
                <a href="/ml-test" class="nav-link">🤖 ML測試</a>
            </div>'''

def update_html_file(filepath):
    """更新單個HTML文件的導航"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尋找 nav-container 開始到結束的區間
        nav_pattern = r'<div class="nav-container">\s*.*?</div>\s*</nav>'
        
        if '<div class="nav-container">' in content:
            # 替換整個nav-container內容
            new_nav = f'<div class="nav-container">\n{CORRECT_NAV_HTML}\n        </div>\n    </nav>'
            content = re.sub(nav_pattern, new_nav, content, flags=re.DOTALL)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ 已更新: {filepath}")
            return True
        else:
            print(f"⏭️  跳過: {filepath} (沒有找到nav-container)")
            return False
            
    except Exception as e:
        print(f"❌ 錯誤: {filepath} - {e}")
        return False

def main():
    """主函數"""
    templates_dir = 'templates'
    updated_count = 0
    total_count = 0
    
    print("🔄 開始批量更新導航連結...")
    print("=" * 50)
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            total_count += 1
            
            if update_html_file(filepath):
                updated_count += 1
    
    print("=" * 50)
    print(f"📊 更新完成！")
    print(f"✅ 成功更新: {updated_count} 個文件")
    print(f"📋 總文件數: {total_count} 個文件")
    print(f"🎯 成功率: {updated_count/total_count*100:.1f}%")

if __name__ == "__main__":
    main()
