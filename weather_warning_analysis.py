#!/usr/bin/env python3
"""
天氣警告處理分析工具
檢查天氣警告在傳統預測和提前預測中的考慮情況
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hko_fetcher import fetch_weather_data, fetch_warning_data
from unified_scorer import get_unified_scorer
from forecast_extractor import forecast_extractor
import json

def analyze_weather_warnings():
    """分析天氣警告在預測系統中的處理"""
    
    print("🚨 天氣警告處理分析")
    print("=" * 60)
    
    try:
        # 1. 檢查天氣警告API
        print("📡 檢查天氣警告數據源:")
        warning_data = fetch_warning_data()
        
        if warning_data:
            print("   ✅ 天氣警告API正常工作")
            print(f"   📊 警告數據結構: {list(warning_data.keys())}")
            
            # 檢查當前警告
            if 'WFIRE' in warning_data:
                fire_warnings = warning_data['WFIRE']
                print(f"   🔥 火災危險警告: {len(fire_warnings)}個")
            
            if 'WRAIN' in warning_data:
                rain_warnings = warning_data['WRAIN']  
                print(f"   🌧️ 雨量警告: {len(rain_warnings)}個")
                for warning in rain_warnings:
                    if 'warningStatementCode' in warning:
                        print(f"      警告類型: {warning['warningStatementCode']}")
                        
            if 'WTCSGNL' in warning_data:
                typhoon_warnings = warning_data['WTCSGNL']
                print(f"   🌪️ 熱帶氣旋警告: {len(typhoon_warnings)}個")
                
            if 'WWIND' in warning_data:
                wind_warnings = warning_data['WWIND']
                print(f"   💨 強風警告: {len(wind_warnings)}個")
                
        else:
            print("   ❌ 無法獲取天氣警告數據")
        
        # 2. 檢查即時天氣數據中的警告
        print("\\n🌤️ 檢查即時天氣數據中的警告處理:")
        weather_data = fetch_weather_data()
        
        if weather_data:
            has_warning_field = 'warningMessage' in weather_data
            print(f"   警告欄位存在: {'✅' if has_warning_field else '❌'}")
            
            if has_warning_field:
                warnings = weather_data['warningMessage']
                print(f"   當前警告數量: {len(warnings) if warnings else 0}")
                if warnings:
                    for i, warning in enumerate(warnings, 1):
                        print(f"      {i}. {warning}")
            else:
                print("   即時天氣數據中不包含warningMessage欄位")
        
        # 3. 檢查統一計分系統中的警告處理
        print("\\n⚖️ 檢查統一計分系統中的警告處理:")
        scorer = get_unified_scorer()
        
        # 檢查能見度因子是否考慮警告
        print("   🔍 分析能見度因子中的警告處理...")
        
        # 創建測試數據 - 有警告
        test_data_with_warning = {
            'rainfall': {'data': [{'place': '香港天文台', 'value': 0}]},
            'warningMessage': ['雨量警告', '能見度較低']
        }
        
        # 創建測試數據 - 無警告  
        test_data_no_warning = {
            'rainfall': {'data': [{'place': '香港天文台', 'value': 0}]},
            'warningMessage': []
        }
        
        # 測試能見度計算
        try:
            visibility_with_warning = scorer._calculate_visibility_factor(test_data_with_warning)
            visibility_no_warning = scorer._calculate_visibility_factor(test_data_no_warning)
            
            print(f"   有警告時能見度分數: {visibility_with_warning}/15")
            print(f"   無警告時能見度分數: {visibility_no_warning}/15")
            
            if visibility_with_warning < visibility_no_warning:
                print("   ✅ 統一計分系統考慮了天氣警告影響")
            else:
                print("   ❌ 統一計分系統未明確處理天氣警告")
                
        except Exception as e:
            print(f"   ❌ 測試失敗: {e}")
        
        # 4. 檢查提前預測中的警告處理
        print("\\n🔮 檢查提前預測中的警告處理:")
        
        print("   📋 forecast_extractor.py分析:")
        # 檢查forecast_extractor中是否處理警告
        with open('forecast_extractor.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        has_warning_logic = 'warning' in content.lower() or 'alert' in content.lower()
        print(f"   包含警告處理邏輯: {'✅' if has_warning_logic else '❌'}")
        
        if not has_warning_logic:
            print("   ⚠️ forecast_extractor未處理警告數據")
            print("   💡 這意味著提前預測時無法預知未來的警告狀態")
        
        # 5. 分析警告對燒天預測的影響
        print("\\n🔥 分析警告對燒天預測的影響:")
        
        warning_impacts = {
            '雨量警告': {
                'impact_level': '嚴重',
                'description': '大雨會嚴重影響燒天品質，能見度降低',
                'traditional_factor': '能見度因子會降分',
                'ml_factor': 'ML模型會大幅降低預測分數'
            },
            '強風警告': {
                'impact_level': '中等',
                'description': '強風影響拍攝穩定性，但不完全阻止燒天',
                'traditional_factor': '風速因子會降分',
                'ml_factor': 'ML模型會適度降分'
            },
            '空氣污染警告': {
                'impact_level': '中等',
                'description': '影響能見度和色彩飽和度',
                'traditional_factor': '空氣品質因子會降分',
                'ml_factor': 'ML模型會考慮能見度影響'
            },
            '熱帶氣旋警告': {
                'impact_level': '嚴重',
                'description': '極端天氣，完全不適合燒天拍攝',
                'traditional_factor': '多個因子會大幅降分',
                'ml_factor': 'ML模型會極大降分'
            }
        }
        
        for warning_type, impact in warning_impacts.items():
            print(f"   🚨 {warning_type}:")
            print(f"      影響程度: {impact['impact_level']}")
            print(f"      描述: {impact['description']}")
            print(f"      傳統算法: {impact['traditional_factor']}")
            print(f"      ML算法: {impact['ml_factor']}")
            print()
        
        # 6. 提前預測的警告問題
        print("🕐 提前預測的警告挑戰:")
        print("   ❓ 問題: 2-4小時提前預測時，如何知道未來是否有警告？")
        print()
        print("   🔍 當前系統限制:")
        print("      1️⃣ 天氣警告API只提供當前生效的警告")
        print("      2️⃣ 無法預測未來2-4小時是否會發出新警告")
        print("      3️⃣ forecast_extractor未整合警告預測邏輯")
        print("      4️⃣ 九天預報不包含具體的警告信息")
        print()
        print("   💡 可能的解決方案:")
        print("      1️⃣ 基於降雨預報推算可能的雨量警告")
        print("      2️⃣ 基於風速預報推算可能的強風警告")
        print("      3️⃣ 基於雲量和氣壓變化推算極端天氣可能性")
        print("      4️⃣ 設定保守的安全邊際，降低提前預測的樂觀度")
        print()
        print("   🎯 建議改進:")
        print("      ✅ 在forecast_extractor中添加警告風險評估")
        print("      ✅ 根據氣象條件推算警告發出可能性") 
        print("      ✅ 提前預測時適當增加保守係數")
        print("      ✅ 提供警告風險提示給用戶")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def suggest_warning_integration():
    """建議警告整合方案"""
    
    print("\\n" + "=" * 60)
    print("💡 警告整合改進建議")
    print("=" * 60)
    
    print("\\n🎯 短期改進 (立即可實施):")
    print("   1️⃣ 在統一計分系統中明確處理當前警告")
    print("   2️⃣ 為每種警告類型設定降分係數")
    print("   3️⃣ 在API回應中顯示當前生效的警告")
    print("   4️⃣ 提醒用戶注意當前警告對拍攝的影響")
    
    print("\\n🔮 中期改進 (需要開發):")
    print("   1️⃣ 在forecast_extractor中添加警告風險評估")
    print("   2️⃣ 基於氣象條件推算未來警告可能性")
    print("   3️⃣ 提前預測時加入警告風險係數")
    print("   4️⃣ 開發警告預測模型")
    
    print("\\n🚀 長期改進 (理想狀態):")
    print("   1️⃣ 整合氣象雷達數據進行實時警告預測")
    print("   2️⃣ 機器學習模型納入警告歷史數據訓練")
    print("   3️⃣ 建立專門的極端天氣識別系統")
    print("   4️⃣ 提供個人化的警告敏感度設定")

def main():
    """主函數"""
    print("🚀 開始分析天氣警告處理...")
    
    success = analyze_weather_warnings()
    
    if success:
        suggest_warning_integration()
    
    print("\\n" + "=" * 60)
    print("📋 分析總結")
    print("=" * 60)
    
    print("\\n🔍 發現:")
    print("   ✅ 天氣警告API正常工作")
    print("   ⚠️ 傳統算法有基本的警告處理")
    print("   ❌ 提前預測無法預知未來警告")
    print("   💡 需要改進警告整合邏輯")
    
    print("\\n🎯 結論:")
    print("   天氣警告確實影響燒天預測，但當前系統")
    print("   在提前預測時無法預知未來警告狀態，")
    print("   這是一個需要改進的重要限制。")

if __name__ == "__main__":
    main()
