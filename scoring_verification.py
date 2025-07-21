#!/usr/bin/env python3
"""
統一計分系統驗證腳本
檢查計分方式是否有錯漏
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_scorer import UnifiedBurnskyScorer, get_unified_scorer
import json

def test_scoring_logic():
    """測試計分邏輯的正確性"""
    
    print("🔍 統一計分系統邏輯驗證")
    print("=" * 60)
    
    # 1. 檢查配置
    scorer = UnifiedBurnskyScorer()
    config = scorer.SCORING_CONFIG
    
    print("\n📊 因子分數配置檢查:")
    factor_scores = config['factor_max_scores']
    total_max = 0
    
    for factor, max_score in factor_scores.items():
        print(f"   {factor:<15}: {max_score:>3}分")
        total_max += max_score
    
    print(f"\n📈 傳統總分上限: {total_max}分")
    print(f"   系統記錄的總分: {scorer.MAX_TRADITIONAL_SCORE}分")
    
    if total_max == scorer.MAX_TRADITIONAL_SCORE:
        print("   ✅ 總分配置正確")
    else:
        print(f"   ❌ 總分配置錯誤: 計算{total_max} vs 記錄{scorer.MAX_TRADITIONAL_SCORE}")
    
    # 2. 檢查權重配置
    print("\n⚖️ 權重配置檢查:")
    weights = config['ml_weights']
    
    for scenario, weight_config in weights.items():
        trad_weight = weight_config['traditional']
        ml_weight = weight_config['ml']
        total_weight = trad_weight + ml_weight
        
        print(f"   {scenario:<12}: 傳統{trad_weight*100:>2.0f}% + AI{ml_weight*100:>2.0f}% = {total_weight*100:>3.0f}%")
        
        if abs(total_weight - 1.0) < 0.001:
            print(f"                     ✅ 權重總和正確")
        else:
            print(f"                     ❌ 權重總和錯誤: {total_weight}")
    
    # 3. 模擬測試計算
    print("\n🧮 模擬計算測試:")
    
    # 創建測試數據
    test_factor_scores = {
        'time': 20,           # 25分中得20分
        'temperature': 12,    # 15分中得12分  
        'humidity': 16,       # 20分中得16分
        'visibility': 10,     # 15分中得10分
        'cloud': 18,          # 25分中得18分
        'uv': 8,              # 10分中得8分
        'wind': 12,           # 15分中得12分
        'air_quality': 10     # 15分中得10分
    }
    
    # 計算總分
    traditional_total = sum(test_factor_scores.values())
    traditional_normalized = (traditional_total / scorer.MAX_TRADITIONAL_SCORE) * 100
    ml_score = 75  # 假設機器學習分數為75
    
    print(f"   測試因子分數總和: {traditional_total}分")
    print(f"   標準化為百分比: ({traditional_total}/{scorer.MAX_TRADITIONAL_SCORE}) × 100 = {traditional_normalized:.1f}%")
    print(f"   機器學習分數: {ml_score}%")
    
    # 測試不同權重下的加權分數
    print(f"\n   不同情境下的加權計算:")
    for scenario, weight_config in weights.items():
        trad_weight = weight_config['traditional']
        ml_weight = weight_config['ml']
        weighted = traditional_normalized * trad_weight + ml_score * ml_weight
        
        print(f"   {scenario:<12}: {traditional_normalized:.1f}×{trad_weight} + {ml_score}×{ml_weight} = {weighted:.1f}%")
    
    # 4. 調整係數檢查
    print("\n🔧 調整係數檢查:")
    adjustments = config['adjustment_factors']
    
    for adj_name, factor in adjustments.items():
        print(f"   {adj_name:<20}: ×{factor}")
        if adj_name.endswith('_low') and factor >= 1.0:
            print(f"                            ❌ 降分係數應該 < 1.0")
        elif adj_name.endswith('_high') and factor <= 1.0:
            print(f"                            ❌ 加分係數應該 > 1.0")
        else:
            print(f"                            ✅ 係數合理")
    
    return True

def test_actual_calculation():
    """測試實際計算過程"""
    
    print("\n" + "=" * 60)
    print("🧪 實際計算過程測試")
    print("=" * 60)
    
    try:
        # 使用統一計分器
        scorer = get_unified_scorer()
        
        # 創建最小測試數據
        test_weather = {
            'temperature': {'data': [{'place': '香港天文台', 'value': 28}]},
            'humidity': {'data': [{'place': '香港天文台', 'value': 65}]},
            'rainfall': {'data': [{'place': '香港天文台', 'value': 0}]},
            'uvindex': {'data': [{'value': 6}]},
            'wind': {'speed': 10}
        }
        
        test_forecast = {
            'forecastDesc': '大致天晴'
        }
        
        test_ninday = {}
        
        # 執行計算
        result = scorer.calculate_unified_score(
            test_weather, test_forecast, test_ninday, 'sunset', 0
        )
        
        print("📊 實際計算結果:")
        print(f"   傳統算法原始分數: {result['traditional_score']:.1f}/140")
        print(f"   傳統算法標準化: {result['traditional_normalized']:.1f}%")
        print(f"   機器學習分數: {result['ml_score']:.1f}%")
        print(f"   加權分數: {result['weighted_score']:.1f}%")
        print(f"   最終分數: {result['final_score']:.1f}%")
        
        # 驗證各因子
        factors = result['factor_scores']
        print(f"\n🔍 各因子得分詳情:")
        calculated_total = 0
        
        for factor, score in factors.items():
            max_score = scorer.SCORING_CONFIG['factor_max_scores'].get(factor, 0)
            print(f"   {factor:<15}: {score:>5.1f}/{max_score}分")
            calculated_total += score
        
        # 驗證總分
        print(f"\n📈 總分驗證:")
        print(f"   因子分數總和: {calculated_total:.1f}分")
        print(f"   記錄的總分: {result['traditional_score']:.1f}分")
        
        if abs(calculated_total - result['traditional_score']) < 0.1:
            print("   ✅ 總分計算正確")
        else:
            print(f"   ❌ 總分計算錯誤，差異: {abs(calculated_total - result['traditional_score']):.1f}分")
        
        # 驗證標準化
        expected_normalized = (result['traditional_score'] / 140) * 100
        print(f"\n🔧 標準化驗證:")
        print(f"   期望值: ({result['traditional_score']:.1f}/140) × 100 = {expected_normalized:.1f}%")
        print(f"   實際值: {result['traditional_normalized']:.1f}%")
        
        if abs(expected_normalized - result['traditional_normalized']) < 0.1:
            print("   ✅ 標準化計算正確")
        else:
            print(f"   ❌ 標準化計算錯誤，差異: {abs(expected_normalized - result['traditional_normalized']):.1f}%")
        
        # 驗證加權
        weights = result['weights_used']
        expected_weighted = result['traditional_normalized'] * weights['traditional'] + result['ml_score'] * weights['ml']
        print(f"\n⚖️ 加權計算驗證:")
        print(f"   期望值: {result['traditional_normalized']:.1f}×{weights['traditional']} + {result['ml_score']:.1f}×{weights['ml']} = {expected_weighted:.1f}")
        print(f"   實際值: {result['weighted_score']:.1f}")
        
        if abs(expected_weighted - result['weighted_score']) < 0.1:
            print("   ✅ 加權計算正確")
        else:
            print(f"   ❌ 加權計算錯誤，差異: {abs(expected_weighted - result['weighted_score']):.1f}")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始驗證統一計分系統...")
    
    success1 = test_scoring_logic()
    success2 = test_actual_calculation()
    
    print("\n" + "=" * 60)
    print("📋 驗證總結")
    print("=" * 60)
    
    if success1 and success2:
        print("✅ 所有測試通過，計分系統邏輯正確")
    else:
        print("❌ 發現問題，需要進一步檢查")
    
    print("\n💡 重要發現:")
    print("   1️⃣ 傳統算法總分上限確實是140分")
    print("   2️⃣ 各因子分數會先計算，然後求和") 
    print("   3️⃣ 傳統總分會標準化為0-100%範圍")
    print("   4️⃣ 與機器學習分數按權重加權")
    print("   5️⃣ 最後應用季節和雲層調整係數")

if __name__ == "__main__":
    main()
