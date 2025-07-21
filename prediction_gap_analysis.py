#!/usr/bin/env python3
"""
傳統預測 vs 機器學習預測差距分析工具
分析兩種預測方法的差異原因
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from unified_scorer import get_unified_scorer
from advanced_predictor import AdvancedBurnskyPredictor
from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast
import json

def analyze_prediction_gap():
    """分析傳統預測與機器學習預測的差距"""
    
    print("🔍 傳統預測 vs 機器學習預測差距分析")
    print("=" * 70)
    
    try:
        # 獲取實際天氣數據
        weather_data = fetch_weather_data()
        forecast_data = fetch_forecast_data()
        ninday_data = fetch_ninday_forecast()
        
        # 獲取統一計分器
        scorer = get_unified_scorer()
        
        # 計算完整結果
        result = scorer.calculate_unified_score(
            weather_data, forecast_data, ninday_data, 'sunset', 0
        )
        
        traditional_raw = result['traditional_score']
        traditional_normalized = result['traditional_normalized']
        ml_score = result['ml_score']
        
        print("📊 基本分數對比:")
        print(f"   傳統算法原始分數: {traditional_raw:.1f}/140分")
        print(f"   傳統算法標準化: {traditional_normalized:.1f}%")
        print(f"   機器學習分數: {ml_score:.1f}%")
        print(f"   絕對差距: {abs(traditional_normalized - ml_score):.1f}%")
        
        gap_percentage = abs(traditional_normalized - ml_score)
        if gap_percentage > 30:
            print("   🚨 差距非常大！")
        elif gap_percentage > 20:
            print("   ⚠️ 差距較大")
        elif gap_percentage > 10:
            print("   🔔 差距中等")
        else:
            print("   ✅ 差距正常")
        
        # 分析傳統算法的計算過程
        print("\\n📈 傳統算法詳細分析:")
        factors = result['factor_scores']
        factor_max_scores = {
            'time': 25, 'temperature': 15, 'humidity': 20, 'visibility': 15,
            'cloud': 25, 'uv': 10, 'wind': 15, 'air_quality': 15
        }
        
        for factor, score in factors.items():
            max_score = factor_max_scores.get(factor, 100)
            percentage = (score / max_score) * 100 if max_score > 0 else 0
            performance = '🔴' if percentage < 40 else '🟡' if percentage < 70 else '🟢'
            print(f"   {factor:<15}: {score:>5.1f}/{max_score} = {percentage:>5.1f}% {performance}")
        
        # 分析機器學習的特徵
        print("\\n🤖 機器學習模型分析:")
        predictor = AdvancedBurnskyPredictor()
        ml_result = predictor.predict_ml(weather_data, forecast_data)
        
        print(f"   ML預測分數: {ml_result['ml_burnsky_score']}%")
        print(f"   ML分類結果: {ml_result['ml_class']}")
        
        # 特徵重要性
        if 'feature_importance' in ml_result:
            print("\\n🔍 機器學習特徵重要性:")
            importance = ml_result['feature_importance']
            sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            
            for feature, imp in sorted_features:
                bar_length = int(imp * 20)  # 0-1轉換為0-20的條形圖
                bar = '█' * bar_length + '░' * (20 - bar_length)
                print(f"   {feature:<15}: {imp:.3f} {bar}")
        
        # 輸入特徵值對比
        if 'input_features' in ml_result:
            print("\\n📋 機器學習輸入特徵:")
            ml_features = ml_result['input_features']
            for feature, value in ml_features.items():
                print(f"   {feature:<15}: {value}")
        
        # 差距原因分析
        print("\\n💡 差距原因分析:")
        
        if traditional_normalized > ml_score:
            diff = traditional_normalized - ml_score
            print(f"   📈 傳統算法較樂觀 (+{diff:.1f}%)")
            print("   可能原因:")
            print("      1️⃣ 傳統算法基於理想化的氣象條件")
            print("      2️⃣ 機器學習基於歷史失敗案例學習，更加保守")
            print("      3️⃣ ML模型考慮了更多隱藏的負面因素")
            print("      4️⃣ 傳統算法可能高估了某些因子的影響")
        else:
            diff = ml_score - traditional_normalized
            print(f"   📈 機器學習較樂觀 (+{diff:.1f}%)")
            print("   可能原因:")
            print("      1️⃣ ML發現了傳統算法忽略的正面模式")
            print("      2️⃣ 傳統算法過於保守或懲罰某些條件")
            print("      3️⃣ ML基於成功案例學習到隱藏規律")
            print("      4️⃣ 傳統算法的權重配置可能需要調整")
        
        # 檢查特定條件的影響
        print("\\n🔍 特定條件影響分析:")
        
        # 雲層條件影響
        cloud_score = factors.get('cloud', 0)
        cloud_desc = forecast_data.get('forecastDesc', '')
        print(f"   雲層條件: {cloud_desc}")
        print(f"   傳統雲層分數: {cloud_score}/25分")
        
        # 時間因子影響 
        time_score = factors.get('time', 0)
        print(f"   時間因子分數: {time_score}/25分")
        
        # UV和能見度
        uv_score = factors.get('uv', 0)
        visibility_score = factors.get('visibility', 0)
        print(f"   UV指數分數: {uv_score}/10分")
        print(f"   能見度分數: {visibility_score}/15分")
        
        # 建議和改進方向
        print("\\n🎯 建議和改進方向:")
        
        if gap_percentage > 20:
            print("   ⚠️ 差距較大，建議:")
            print("      1️⃣ 檢查傳統算法的權重配置")
            print("      2️⃣ 重新訓練機器學習模型")
            print("      3️⃣ 增加更多歷史數據樣本")
            print("      4️⃣ 調整加權比例，減少差距影響")
        else:
            print("   ✅ 差距在合理範圍內")
            print("      💡 不同算法的差異是正常的，反映了不同的預測思路")
        
        # 信任度建議
        print("\\n🎲 使用建議:")
        weights = result.get('weights_used', {})
        trad_weight = weights.get('traditional', 0.5)
        ml_weight = weights.get('ml', 0.5)
        
        print(f"   當前權重: 傳統{trad_weight*100:.0f}% + AI{ml_weight*100:.0f}%")
        
        if gap_percentage > 25:
            print("   建議調整權重，減少差距影響")
        elif traditional_normalized > 80 and ml_score < 40:
            print("   傳統算法過於樂觀，建議增加ML權重")
        elif ml_score > 80 and traditional_normalized < 40:
            print("   ML模型過於樂觀，建議增加傳統權重")
        else:
            print("   當前權重配置合理")
        
        return True
        
    except Exception as e:
        print(f"❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def compare_multiple_scenarios():
    """對比多種天氣情況下的預測差距"""
    
    print("\\n" + "=" * 70)
    print("🌦️ 多場景預測差距分析")
    print("=" * 70)
    
    # 這裡可以添加模擬不同天氣條件的測試
    # 由於需要實際天氣數據，暫時跳過
    print("💡 此功能需要歷史天氣數據，建議在生產環境中實施")

def main():
    """主函數"""
    print("🚀 開始分析預測差距...")
    
    success = analyze_prediction_gap()
    
    if success:
        compare_multiple_scenarios()
    
    print("\\n" + "=" * 70)
    print("📋 分析完成")
    print("=" * 70)
    
    print("\\n🎯 總結:")
    print("   預測差距是正常現象，反映了不同算法的特點")
    print("   傳統算法：基於氣象學原理，邏輯清晰")
    print("   機器學習：基於歷史數據，發現隱藏模式")
    print("   統一系統：結合兩者優勢，提供更可靠的預測")

if __name__ == "__main__":
    main()
