#!/usr/bin/env python3
"""
用戶反饋系統測試腳本
測試反饋提交和準確率計算功能
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5001"

def test_submit_feedback():
    """測試提交反饋功能"""
    print("\n" + "="*60)
    print("🧪 測試 1: 提交用戶反饋")
    print("="*60)

    test_data = {
        "predicted_score": 75,
        "user_rating": 80,
        "comment": "實際顏色比預測的更豐富，雲層層次也很好",
        "prediction_timestamp": datetime.now().isoformat(),
        "location": "維多利亞港"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/submit-feedback",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"HTTP 狀態碼: {response.status_code}")
        result = response.json()

        print("\n📋 響應數據:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get('status') == 'success':
            print("\n✅ 測試通過：反饋提交成功")
            if 'accuracy_stats' in result:
                stats = result['accuracy_stats']
                print(f"\n📊 準確率統計:")
                print(f"  - 有數據: {stats.get('has_data')}")
                if stats.get('has_data'):
                    print(f"  - 準確率: {stats.get('accuracy')}%")
                    print(f"  - 平均誤差: {stats.get('avg_error')} 分")
                    print(f"  - 反饋數量: {stats.get('feedback_count')} 個")
                    print(f"  - 10分內準確度: {stats.get('within_10_points')}%")
                    print(f"  - 20分內準確度: {stats.get('within_20_points')}%")
        else:
            print(f"\n❌ 測試失敗：{result.get('message')}")
            return False

    except Exception as e:
        print(f"\n❌ 請求失敗：{e}")
        return False

    return True

def test_get_accuracy_stats():
    """測試獲取準確率統計"""
    print("\n" + "="*60)
    print("🧪 測試 2: 獲取準確率統計")
    print("="*60)

    try:
        response = requests.get(f"{BASE_URL}/api/accuracy-stats")

        print(f"HTTP 狀態碼: {response.status_code}")
        result = response.json()

        print("\n📋 響應數據:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get('has_data'):
            print("\n✅ 測試通過：成功獲取準確率統計")
            print(f"\n📊 統計摘要:")
            print(f"  - 準確率: {result.get('accuracy')}%")
            print(f"  - 反饋數量: {result.get('feedback_count')} 個")
            print(f"  - 最後更新: {result.get('last_updated')}")
        else:
            print("\n⚠️ 測試通過但無數據")
            print(f"  訊息: {result.get('message')}")

    except Exception as e:
        print(f"\n❌ 請求失敗：{e}")
        return False

    return True

def test_validation():
    """測試參數驗證"""
    print("\n" + "="*60)
    print("🧪 測試 3: 參數驗證")
    print("="*60)

    # 測試1: 缺少必需字段
    print("\n測試 3.1: 缺少必需字段")
    try:
        response = requests.post(
            f"{BASE_URL}/api/submit-feedback",
            json={"comment": "只有備註"},
            headers={"Content-Type": "application/json"}
        )
        print(f"HTTP 狀態碼: {response.status_code}")
        if response.status_code == 400:
            print("✅ 正確拒絕：缺少必需字段")
        else:
            print(f"❌ 驗證失敗：應返回 400，實際返回 {response.status_code}")
    except Exception as e:
        print(f"❌ 請求失敗：{e}")

    # 測試2: 評分超出範圍
    print("\n測試 3.2: 評分超出範圍")
    try:
        response = requests.post(
            f"{BASE_URL}/api/submit-feedback",
            json={
                "predicted_score": 150,  # 超出範圍
                "user_rating": 80
            },
            headers={"Content-Type": "application/json"}
        )
        print(f"HTTP 狀態碼: {response.status_code}")
        if response.status_code == 400:
            print("✅ 正確拒絕：評分超出範圍")
        else:
            print(f"❌ 驗證失敗：應返回 400，實際返回 {response.status_code}")
    except Exception as e:
        print(f"❌ 請求失敗：{e}")

    return True

def check_database():
    """檢查數據庫表結構"""
    print("\n" + "="*60)
    print("🧪 測試 4: 檢查數據庫")
    print("="*60)

    import sqlite3

    try:
        conn = sqlite3.connect('prediction_history.db')
        cursor = conn.cursor()

        # 檢查表是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='user_feedback'
        """)

        if cursor.fetchone():
            print("✅ user_feedback 表存在")

            # 檢查表結構
            cursor.execute("PRAGMA table_info(user_feedback)")
            columns = cursor.fetchall()

            print("\n📋 表結構:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

            # 查詢記錄數量
            cursor.execute("SELECT COUNT(*) FROM user_feedback")
            count = cursor.fetchone()[0]
            print(f"\n📊 當前反饋數量: {count} 個")

            # 查詢最新的5條反饋
            if count > 0:
                cursor.execute("""
                    SELECT predicted_score, user_rating, feedback_timestamp
                    FROM user_feedback
                    ORDER BY feedback_timestamp DESC
                    LIMIT 5
                """)
                recent = cursor.fetchall()

                print("\n📝 最新反饋:")
                for i, (pred, actual, ts) in enumerate(recent, 1):
                    error = abs(pred - actual)
                    print(f"  {i}. 預測:{pred} 實際:{actual} 誤差:{error} ({ts})")
        else:
            print("❌ user_feedback 表不存在")
            return False

        conn.close()

    except Exception as e:
        print(f"❌ 數據庫檢查失敗：{e}")
        return False

    return True

def main():
    """運行所有測試"""
    print("\n" + "="*60)
    print("🚀 用戶反饋系統測試套件")
    print("="*60)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"服務器地址: {BASE_URL}")

    # 檢查數據庫
    db_ok = check_database()

    # 測試 API
    print("\n⚠️ 請確保 Flask 服務器正在運行...")
    input("按 Enter 繼續測試...")

    submit_ok = test_submit_feedback()
    stats_ok = test_get_accuracy_stats()
    validation_ok = test_validation()

    # 最終結果
    print("\n" + "="*60)
    print("📊 測試結果摘要")
    print("="*60)
    print(f"數據庫檢查: {'✅ 通過' if db_ok else '❌ 失敗'}")
    print(f"提交反饋: {'✅ 通過' if submit_ok else '❌ 失敗'}")
    print(f"獲取統計: {'✅ 通過' if stats_ok else '❌ 失敗'}")
    print(f"參數驗證: {'✅ 通過' if validation_ok else '❌ 失敗'}")

    all_passed = db_ok and submit_ok and stats_ok and validation_ok

    if all_passed:
        print("\n🎉 所有測試通過！用戶反饋系統運作正常")
    else:
        print("\n⚠️ 部分測試失敗，請檢查系統配置")

    print("="*60 + "\n")

if __name__ == "__main__":
    main()
