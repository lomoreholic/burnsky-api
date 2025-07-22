#!/usr/bin/env python3
"""
🔧 AdSense ads.txt 更新工具
"""

def update_ads_txt(publisher_id):
    """更新 ads.txt 文件的 Publisher ID"""
    
    # 驗證 Publisher ID 格式
    if not publisher_id.startswith('ca-pub-') or len(publisher_id) != 21:
        print(f"❌ 錯誤的 Publisher ID 格式: {publisher_id}")
        print("✅ 正確格式應該是: ca-pub-XXXXXXXXXXXXXXXXX (21個字符)")
        return False
    
    # 創建新的 ads.txt 內容
    ads_content = f"""# ads.txt file for burnsky-api.onrender.com
# This file identifies authorized sellers of digital advertising inventory

# Google AdSense
google.com, {publisher_id}, DIRECT, f08c47fec0942fa0"""
    
    # 寫入文件
    try:
        with open('static/ads.txt', 'w') as f:
            f.write(ads_content)
        print(f"✅ 已更新 static/ads.txt 使用 Publisher ID: {publisher_id}")
        return True
    except Exception as e:
        print(f"❌ 更新失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 AdSense ads.txt 更新工具")
    print("=" * 40)
    print()
    print("請從您的 AdSense 帳戶中獲取正確的 Publisher ID:")
    print("1. 登入 https://adsense.google.com")
    print("2. 前往 帳戶 > 帳戶資訊") 
    print("3. 複製 Publisher ID (格式: ca-pub-XXXXXXXXXXXXXXXXX)")
    print()
    
    # 顯示當前使用的 ID
    try:
        with open('static/ads.txt', 'r') as f:
            current_content = f.read()
            import re
            match = re.search(r'ca-pub-(\d+)', current_content)
            if match:
                current_id = f"ca-pub-{match.group(1)}"
                print(f"當前使用的 Publisher ID: {current_id}")
            else:
                print("當前文件中沒有找到 Publisher ID")
    except:
        print("無法讀取當前 ads.txt 文件")
    
    print()
    print("如果您有正確的 Publisher ID，請告訴我，我會幫您更新。")
    print("例如: ca-pub-1234567890123456789")
