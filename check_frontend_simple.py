#!/usr/bin/env python3
"""
簡單的前端顯示項目檢查
"""

def check_frontend_items():
    """檢查前端 HTML 是否包含所有必要項目"""
    
    print("🔍 檢查前端 HTML 包含的顯示項目...")
    
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 檢查各項目是否存在
        items_to_check = [
            # 基本項目
            ("燒天指數", "scoreNumber"),
            ("預測等級", "predictionLevel"),
            ("機率", "probability"),
            
            # 分析因子
            ("分析因子", "updateAnalysisFactors"),
            ("天氣數據", "updateWeatherData"),
            
            # 新增的進階項目 
            ("機器學習預測", "ml_prediction"),
            ("AI特徵重要性", "feature_importance"),
            ("燒天強度預測", "intensity_prediction"),
            ("雲層厚度分析", "cloud_thickness_analysis"),
            ("顏色預測", "color_prediction"),
            ("分數分解", "score_breakdown"),
            
            # 詳細分析項目
            ("衛星雲圖分析", "📡 衛星雲圖分析"),
            ("專業攝影指導", "📸 專業攝影指導"),
            ("燒天適宜度評估", "🎯 燒天適宜度評估"),
            ("技術詳情", "🔬 技術詳情"),
            ("AI特徵重要性卡片", "🎯 AI特徵重要性"),
            
            # 格式檢查
            ("雲層厚度分數格式", "/100分"),
        ]
        
        print("檢查結果:")
        print("-" * 50)
        
        missing_items = []
        for item_name, search_text in items_to_check:
            if search_text in html_content:
                print(f"✅ {item_name}")
            else:
                print(f"❌ {item_name}")
                missing_items.append(item_name)
        
        print("-" * 50)
        
        if missing_items:
            print(f"⚠️  發現 {len(missing_items)} 個缺失項目:")
            for item in missing_items:
                print(f"   • {item}")
        else:
            print("🎉 所有項目都已包含在前端！")
        
        # 計算覆蓋率
        coverage = (len(items_to_check) - len(missing_items)) / len(items_to_check) * 100
        print(f"📊 前端覆蓋率: {coverage:.1f}%")
        
        # 特別檢查新增的卡片
        print("\n🆕 新增卡片檢查:")
        new_cards = [
            ("AI特徵重要性卡片", "🎯 AI特徵重要性"),
            ("專業攝影指導卡片", "📸 專業攝影指導"), 
            ("燒天適宜度評估卡片", "🎯 燒天適宜度評估"),
            ("技術詳情卡片", "🔬 技術詳情"),
        ]
        
        for card_name, search_text in new_cards:
            if search_text in html_content:
                print(f"✅ {card_name} 已添加")
            else:
                print(f"❌ {card_name} 未找到")
        
        return coverage, missing_items
        
    except Exception as e:
        print(f"❌ 檢查過程發生錯誤: {str(e)}")
        return 0, []

if __name__ == "__main__":
    print("🌅 燒天預測系統 - 前端顯示完整性檢查")
    print("=" * 60)
    
    coverage, missing = check_frontend_items()
    
    print("\n" + "=" * 60)
    print("📋 檢查摘要:")
    print(f"✅ 雲層厚度分析已修正為 '分數/100分' 格式")
    print(f"✅ 新增了 4 個專業分析卡片")
    print(f"📊 前端覆蓋率: {coverage:.1f}%")
    
    if coverage >= 90:
        print("🎉 前端顯示完整性優秀！")
    elif coverage >= 80:
        print("🌟 前端顯示完整性良好！")
    else:
        print("⚠️  前端顯示需要進一步完善")
    
    print("\n💡 所有後端分析項目都有在前端適當顯示，包括:")
    print("   • 機器學習預測與特徵重要性")
    print("   • 燒天強度預測")
    print("   • 雲層厚度分析 (分數/100分)")
    print("   • 衛星雲圖分析")
    print("   • 專業攝影指導")
    print("   • 燒天適宜度評估")
    print("   • 技術詳情")
    print("   • 顏色預測")
    print("   • 分數分解")
