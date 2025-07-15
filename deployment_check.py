#!/usr/bin/env python3
"""
燒天預測系統 - 部署前最終檢查
"""

def final_deployment_check():
    """最終部署檢查"""
    print("🚀 燒天預測系統 - 部署前最終檢查")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 8
    
    # 1. 檢查核心模組
    try:
        from advanced_predictor import AdvancedBurnskyPredictor
        print("✅ 1/8 - AdvancedBurnskyPredictor 模組正常")
        checks_passed += 1
    except Exception as e:
        print(f"❌ 1/8 - AdvancedBurnskyPredictor 失敗: {e}")
    
    # 2. 檢查基礎預測器
    try:
        from predictor import calculate_burnsky_score
        print("✅ 2/8 - 基礎預測器模組正常")
        checks_passed += 1
    except Exception as e:
        print(f"❌ 2/8 - 基礎預測器失敗: {e}")
    
    # 3. 檢查 Flask 應用
    try:
        from app import app
        print("✅ 3/8 - Flask 應用載入正常")
        checks_passed += 1
    except Exception as e:
        print(f"❌ 3/8 - Flask 應用失敗: {e}")
    
    # 4. 檢查 HKO 數據擷取器
    try:
        from hko_fetcher import fetch_weather_data
        print("✅ 4/8 - HKO 數據擷取器正常")
        checks_passed += 1
    except Exception as e:
        print(f"❌ 4/8 - HKO 數據擷取器失敗: {e}")
    
    # 5. 檢查機器學習模型
    try:
        import os
        model_files = ['models/regression_model.pkl', 'models/classification_model.pkl', 'models/scaler.pkl']
        if all(os.path.exists(f) for f in model_files):
            print("✅ 5/8 - 機器學習模型檔案存在")
            checks_passed += 1
        else:
            print("⚠️ 5/8 - 部分模型檔案缺失，將自動重新訓練")
    except Exception as e:
        print(f"❌ 5/8 - 模型檢查失敗: {e}")
    
    # 6. 檢查核心功能
    try:
        advanced = AdvancedBurnskyPredictor()
        result = advanced.analyze_cloud_thickness_and_color_visibility({}, {})
        if 'cloud_thickness_level' in result:
            print("✅ 6/8 - 雲層厚度分析功能正常")
            checks_passed += 1
        else:
            print("❌ 6/8 - 雲層厚度分析功能異常")
    except Exception as e:
        print(f"❌ 6/8 - 核心功能測試失敗: {e}")
    
    # 7. 檢查前端模板
    try:
        import os
        if os.path.exists('templates/index.html'):
            print("✅ 7/8 - 前端模板存在")
            checks_passed += 1
        else:
            print("❌ 7/8 - 前端模板缺失")
    except Exception as e:
        print(f"❌ 7/8 - 前端模板檢查失敗: {e}")
    
    # 8. 檢查依賴檔案
    try:
        import os
        required_files = ['requirements.txt', 'Procfile', 'runtime.txt']
        existing_files = [f for f in required_files if os.path.exists(f)]
        if len(existing_files) >= 2:
            print(f"✅ 8/8 - 部署檔案就緒 ({len(existing_files)}/{len(required_files)})")
            checks_passed += 1
        else:
            print(f"⚠️ 8/8 - 部分部署檔案缺失 ({len(existing_files)}/{len(required_files)})")
    except Exception as e:
        print(f"❌ 8/8 - 部署檔案檢查失敗: {e}")
    
    print("=" * 60)
    print(f"🏁 檢查完成: {checks_passed}/{total_checks} 項目通過")
    
    if checks_passed >= 6:
        print("🎉 系統準備就緒，可以進行部署！")
        print("\n📋 部署步驟：")
        print("1. git add . && git commit -m 'Advanced features complete'")
        print("2. git push origin main")
        print("3. 在 Render.com 觸發重新部署")
        print("4. 測試生產環境 API")
        
        print("\n🔗 測試 URL：")
        print("• 主頁: https://your-app.onrender.com/")
        print("• API: https://your-app.onrender.com/predict")
        print("• 日落: https://your-app.onrender.com/predict/sunset")
        print("• 日出: https://your-app.onrender.com/predict/sunrise")
        
        return True
    else:
        print("⚠️ 系統尚未完全就緒，請修復失敗的檢查項目")
        return False

if __name__ == "__main__":
    final_deployment_check()
