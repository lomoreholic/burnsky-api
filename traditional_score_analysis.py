#!/usr/bin/env python3
"""
傳統算法總分分析

檢查傳統算法是否已經考慮了總分限制以及權重計算是否合理

作者: BurnSky Team  
日期: 2025-07-16
"""

import sys
sys.path.append('.')

from predictor import calculate_burnsky_score
from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast

def analyze_traditional_algorithm_total():
    """分析傳統算法總分配置"""
    
    print("🔍 傳統算法總分分析")
    print("=" * 50)
    
    # 傳統算法各因子的最高分
    factor_max_scores = {
        'time_factor': 18,
        'temperature_factor': 18,
        'humidity_factor': 22,
        'visibility_factor': 18,
        'cloud_analysis_factor': 30,
        'uv_factor': 12,
        'wind_factor': 10,
        'air_quality_factor': 12
    }
    
    theoretical_max = sum(factor_max_scores.values())
    print(f"理論最高分: {theoretical_max}分")
    print()
    
    # 實際測試
    try:
        weather_data = fetch_weather_data()
        forecast_data = fetch_forecast_data()
        ninday_data = fetch_ninday_forecast()
        
        score, details = calculate_burnsky_score(weather_data, forecast_data, ninday_data)
        
        print("當前實際分數:")
        actual_factors = {}
        actual_total = 0
        
        for factor_name, max_score in factor_max_scores.items():
            if factor_name in details:
                actual_score = details[factor_name].get('score', 0)
                actual_factors[factor_name] = actual_score
                actual_total += actual_score
                percentage = (actual_score / max_score) * 100 if max_score > 0 else 0
                print(f"  {factor_name:<20} {actual_score:2d}/{max_score:2d}分 ({percentage:5.1f}%)")
        
        print(f"\n實際因子總分: {actual_total}分")
        
        # 檢查score_breakdown
        if 'score_breakdown' in details:
            breakdown = details['score_breakdown']
            traditional_reported = breakdown.get('traditional_score', 0)
            ml_score = breakdown.get('ml_score', 0)
            final_score = breakdown.get('final_weighted_score', 0)
            
            print(f"\nScore Breakdown分析:")
            print(f"  報告的傳統分數: {traditional_reported:.1f}分")
            print(f"  實際因子總和:   {actual_total}分")
            print(f"  差異:           {traditional_reported - actual_total:.1f}分")
            print(f"  ML分數:         {ml_score:.1f}分")
            print(f"  最終加權分數:   {final_score:.1f}分")
            
            # 驗證加權計算
            expected_final = traditional_reported * 0.35 + ml_score * 0.65
            print(f"  驗證加權計算:   {expected_final:.1f}分")
            print(f"  計算是否正確:   {'✅' if abs(final_score - expected_final) < 0.1 else '❌'}")
        
        # 分析是否需要標準化
        print(f"\n標準化分析:")
        if theoretical_max != 100:
            normalized_factors = {}
            print(f"當前總分上限 {theoretical_max}分 ≠ 100分")
            print(f"建議標準化各因子分數到100分制:")
            
            for factor_name, actual_score in actual_factors.items():
                normalized_score = (actual_score / theoretical_max) * 100
                normalized_factors[factor_name] = normalized_score
                print(f"  {factor_name:<20} {actual_score:2d}分 → {normalized_score:5.1f}分")
            
            normalized_total = sum(normalized_factors.values())
            print(f"\n標準化後總分: {normalized_total:.1f}分")
            
            # 用標準化分數重新計算
            if 'score_breakdown' in details:
                normalized_traditional = (traditional_reported / theoretical_max) * 100
                normalized_final = normalized_traditional * 0.35 + ml_score * 0.65
                print(f"\n使用標準化分數重新計算:")
                print(f"  標準化傳統分數: {normalized_traditional:.1f}分")
                print(f"  重新計算最終分數: {normalized_final:.1f}分")
                print(f"  與當前最終分數差異: {abs(normalized_final - final_score):.1f}分")
        
        return {
            'theoretical_max': theoretical_max,
            'actual_total': actual_total,
            'traditional_reported': traditional_reported if 'score_breakdown' in details else actual_total,
            'needs_normalization': theoretical_max != 100
        }
        
    except Exception as e:
        print(f"分析失敗: {e}")
        return None

def check_algorithm_logic():
    """檢查算法邏輯是否合理"""
    
    print("\n🤔 算法邏輯合理性檢查")
    print("=" * 50)
    
    # 檢查點1: 總分上限
    print("1. 總分上限檢查:")
    print("   當前設計: 140分上限")
    print("   問題: 不是標準的100分制")
    print("   影響: ML模型輸出0-100分，傳統算法0-140分，權重不對等")
    
    # 檢查點2: 權重計算
    print("\n2. 權重計算檢查:")
    print("   當前公式: final = traditional * 35% + ml * 65%")
    print("   問題: 如果traditional > 100分，會導致不公平比較")
    print("   例如: traditional=140分 vs ml=65分")
    print("        final = 140*0.35 + 65*0.65 = 49 + 42.25 = 91.25分")
    print("        但如果traditional標準化: (140/140)*100*0.35 + 65*0.65 = 77.25分")
    
    # 檢查點3: 建議解決方案
    print("\n3. 建議解決方案:")
    print("   選項A: 標準化傳統算法到100分制")
    print("          final = (traditional/140*100) * 35% + ml * 65%")
    print("   選項B: 調整ML模型輸出到140分制")
    print("          final = traditional * 35% + (ml*1.4) * 65%")
    print("   選項C: 重新設計權重，確保公平比較")
    print("          例如基於實際分數範圍動態調整權重")

def main():
    """主函數"""
    result = analyze_traditional_algorithm_total()
    
    if result:
        check_algorithm_logic()
        
        print("\n📋 總結:")
        if result['needs_normalization']:
            print("❌ 發現問題: 傳統算法總分140分，ML模型65分，權重計算不對等")
            print("💡 建議: 實施標準化或調整權重計算方式")
        else:
            print("✅ 總分配置合理")
        
        print(f"   理論最高分: {result['theoretical_max']}分")
        print(f"   實際總分: {result['actual_total']}分")
        print(f"   報告傳統分數: {result['traditional_reported']:.1f}分")

if __name__ == "__main__":
    main()
