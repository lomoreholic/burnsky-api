#!/usr/bin/env python3
"""
分析機器學習權重配置

根據用戶提供的ML分數和機率分布分析權重是否合理

作者: BurnSky Team  
日期: 2025-07-16
"""

def analyze_ml_weighting():
    """分析ML權重配置"""
    
    print("🔥 機器學習權重分析 🔥")
    print("=" * 50)
    
    # 用戶提供的數據
    ml_score = 65
    ml_probabilities = {"低": 0, "中": 2, "高": 98}
    
    print(f"ML預測分數: {ml_score}分")
    print(f"ML機率分布: {ml_probabilities}")
    print()
    
    # 當前權重配置
    traditional_weight = 0.35  # 35%
    ml_weight = 0.65           # 65%
    
    print(f"當前權重配置:")
    print(f"  傳統算法權重: {traditional_weight*100}%")
    print(f"  機器學習權重: {ml_weight*100}%")
    print()
    
    # 假設傳統算法分數範圍
    traditional_scores = [60, 70, 80, 90, 100]
    
    print("不同傳統算法分數下的最終分數:")
    print(f"{'傳統分數':<10} {'ML分數':<8} {'最終分數':<10} {'分析'}")
    print("-" * 50)
    
    for trad_score in traditional_scores:
        final_score = trad_score * traditional_weight + ml_score * ml_weight
        
        # 分析合理性
        if final_score > trad_score and final_score > ml_score:
            analysis = "偏高"
        elif final_score < min(trad_score, ml_score):
            analysis = "偏低"
        elif abs(final_score - (trad_score + ml_score)/2) < 5:
            analysis = "平衡"
        else:
            analysis = "合理"
        
        print(f"{trad_score:<10} {ml_score:<8} {final_score:<10.1f} {analysis}")
    
    print()
    
    # 分析ML機率分布的含義
    print("ML機率分布分析:")
    high_prob = ml_probabilities["高"]
    if high_prob >= 90:
        print(f"  🔥 極高信心度 ({high_prob}%) - ML強烈看好燒天")
        confidence_level = "極高"
    elif high_prob >= 70:
        print(f"  📈 高信心度 ({high_prob}%) - ML看好燒天")
        confidence_level = "高"
    elif high_prob >= 50:
        print(f"  ⚖️ 中等信心度 ({high_prob}%) - ML謹慎樂觀")
        confidence_level = "中等"
    else:
        print(f"  📉 低信心度 ({high_prob}%) - ML不太看好")
        confidence_level = "低"
    
    # 基於ML信心度建議權重調整
    print("\n權重調整建議:")
    
    if confidence_level == "極高" and ml_score >= 60:
        print("  ✅ 當前65%的ML權重合理")
        print("  💡 ML極度看好且分數不錯，高權重有道理")
        recommended_ml_weight = 0.65
    elif confidence_level == "極高" and ml_score < 60:
        print("  ⚠️ ML極度看好但分數偏低，可能需要檢查")
        print("  💡 建議稍微降低ML權重到55-60%")
        recommended_ml_weight = 0.6
    elif confidence_level == "高":
        print("  ✅ 當前65%的ML權重偏高但可接受")
        print("  💡 建議ML權重在55-65%之間")
        recommended_ml_weight = 0.6
    else:
        print("  ❌ 當前65%的ML權重過高")
        print("  💡 建議降低ML權重到45-55%")
        recommended_ml_weight = 0.5
    
    # 計算建議權重下的結果
    print(f"\n建議權重配置 (ML: {recommended_ml_weight*100}%, 傳統: {(1-recommended_ml_weight)*100}%):")
    print(f"{'傳統分數':<10} {'調整後分數':<12} {'差異'}")
    print("-" * 35)
    
    for trad_score in [70, 80, 90]:
        current_final = trad_score * traditional_weight + ml_score * ml_weight
        recommended_final = trad_score * (1-recommended_ml_weight) + ml_score * recommended_ml_weight
        diff = recommended_final - current_final
        
        print(f"{trad_score:<10} {recommended_final:<12.1f} {diff:+.1f}")
    
    return {
        'ml_score': ml_score,
        'ml_confidence': confidence_level,
        'current_ml_weight': ml_weight,
        'recommended_ml_weight': recommended_ml_weight,
        'analysis': confidence_level
    }

def analyze_score_distribution():
    """分析分數分布的合理性"""
    
    print("\n📊 分數分布合理性分析:")
    print("=" * 40)
    
    ml_score = 65
    high_confidence = 98
    
    # 65分配98%高信心度是否合理？
    print(f"ML分數 {ml_score}分 配 {high_confidence}% 高信心度分析:")
    
    if ml_score >= 80 and high_confidence >= 90:
        print("  ✅ 高分高信心 - 非常合理")
    elif ml_score >= 70 and high_confidence >= 80:
        print("  ✅ 良好分數配高信心 - 合理")
    elif ml_score >= 60 and high_confidence >= 90:
        print("  ⚠️ 中等分數配極高信心 - 需要關注")
        print("  💭 可能原因:")
        print("     1. ML模型對此情境特別有信心")
        print("     2. 傳統算法可能低估了某些因子")
        print("     3. ML發現了傳統算法未考慮的模式")
    elif ml_score < 60 and high_confidence >= 80:
        print("  ❌ 低分高信心 - 不太合理")
        print("  💭 建議檢查ML模型是否過度自信")
    else:
        print("  ✅ 分數與信心度匹配")
    
    # 具體建議
    print(f"\n💡 針對 {ml_score}分/{high_confidence}%信心 的建議:")
    print("  1. 檢查傳統算法是否有遺漏的有利因子")
    print("  2. 分析ML模型為何如此有信心")
    print("  3. 考慮動態調整權重機制")
    print("  4. 收集更多實際燒天案例驗證")

def main():
    """主函數"""
    print("🔥 ML權重合理性分析工具 🔥")
    print("=" * 50)
    
    # 分析權重配置
    result = analyze_ml_weighting()
    
    # 分析分數分布
    analyze_score_distribution()
    
    print("\n📋 總結:")
    print(f"  ML分數: 65分")
    print(f"  ML信心度: 極高 (98%高機率)")
    print(f"  當前ML權重: 65%")
    print(f"  建議ML權重: {result['recommended_ml_weight']*100}%")
    
    if result['recommended_ml_weight'] == 0.65:
        print("  ✅ 當前權重配置合理")
    else:
        print(f"  💡 建議調整ML權重到 {result['recommended_ml_weight']*100}%")

if __name__ == "__main__":
    main()
