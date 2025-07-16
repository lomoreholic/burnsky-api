#!/usr/bin/env python3
"""
計算具體總分示例

根據ML分數65分和當前權重配置計算最終分數

作者: BurnSky Team  
日期: 2025-07-16
"""

def calculate_final_scores():
    """計算不同情況下的最終分數"""
    
    print("🔥 總分計算示例 🔥")
    print("=" * 40)
    
    ml_score = 65
    traditional_weight = 0.35  # 35%
    ml_weight = 0.65          # 65%
    
    print(f"ML分數: {ml_score}分")
    print(f"權重配置: 傳統{traditional_weight*100}% + ML{ml_weight*100}%")
    print()
    
    # 不同傳統算法分數的情況
    scenarios = [
        {"name": "傳統算法偏低", "traditional": 50},
        {"name": "傳統算法中等", "traditional": 65},
        {"name": "傳統算法良好", "traditional": 75},
        {"name": "傳統算法優秀", "traditional": 85},
        {"name": "傳統算法極佳", "traditional": 95}
    ]
    
    print("不同傳統算法分數的最終結果:")
    print(f"{'情境':<12} {'傳統分數':<8} {'ML分數':<8} {'最終分數':<10} {'等級'}")
    print("-" * 55)
    
    for scenario in scenarios:
        traditional_score = scenario["traditional"]
        final_score = traditional_score * traditional_weight + ml_score * ml_weight
        
        # 判斷等級
        if final_score >= 85:
            level = "極高"
        elif final_score >= 70:
            level = "高"
        elif final_score >= 55:
            level = "中等"
        elif final_score >= 40:
            level = "輕微"
        else:
            level = "低"
        
        print(f"{scenario['name']:<12} {traditional_score:<8} {ml_score:<8} {final_score:<10.1f} {level}")
    
    print()
    
    # 分析ML影響力
    print("ML模型影響力分析:")
    base_traditional = 75  # 假設傳統算法75分
    base_final = base_traditional * traditional_weight + ml_score * ml_weight
    
    print(f"  基準情況 (傳統75分): 最終 {base_final:.1f}分")
    
    # ML分數變化的影響
    ml_variations = [55, 60, 65, 70, 75, 80]
    print(f"\n  ML分數變化對最終分數的影響 (傳統固定75分):")
    for ml_var in ml_variations:
        final_var = base_traditional * traditional_weight + ml_var * ml_weight
        diff = final_var - base_final
        print(f"    ML{ml_var}分 → 最終{final_var:.1f}分 (差異{diff:+.1f})")
    
    return base_final

def analyze_current_weighting():
    """分析當前權重配置的優缺點"""
    
    print("\n📊 當前權重配置分析:")
    print("=" * 40)
    
    print("優點:")
    print("  ✅ ML權重較高(65%)，充分利用AI能力")
    print("  ✅ 仍保留傳統算法影響力(35%)，平衡風險")
    print("  ✅ 對於ML高信心度預測給予足夠重視")
    
    print("\n潛在問題:")
    print("  ⚠️ ML模型可能過度自信 (65分配98%信心)")
    print("  ⚠️ 傳統算法權重較低，可能遺漏重要因子")
    print("  ⚠️ 固定權重不能適應不同情境")
    
    print("\n改進建議:")
    print("  💡 實施動態權重機制:")
    print("     - ML高信心度時(>90%): 當前權重 65%/35%")
    print("     - ML中信心度時(70-90%): 調整為 55%/45%") 
    print("     - ML低信心度時(<70%): 調整為 45%/55%")
    
    print("  💡 加入信心度調節:")
    print("     - ML信心度作為權重調節因子")
    print("     - 避免過度依賴不確定的ML預測")

def main():
    """主函數"""
    print("🎯 回答您的問題:")
    print("=" * 50)
    
    # 計算具體總分
    final_score = calculate_final_scores()
    
    print(f"\n📋 直接回答:")
    print(f"  如果ML分數是65分，傳統算法分數約75分")
    print(f"  最終總分 = 75 × 35% + 65 × 65% = {75*0.35 + 65*0.65:.1f}分")
    print(f"  最終總分 = 26.25 + 42.25 = 68.5分")
    
    print(f"\n🔍 權重合理性:")
    print(f"  65%的ML權重對於98%信心度是合理的")
    print(f"  但需要注意65分配98%信心可能過於樂觀")
    print(f"  建議監控ML模型的實際準確率")
    
    # 分析權重配置
    analyze_current_weighting()

if __name__ == "__main__":
    main()
