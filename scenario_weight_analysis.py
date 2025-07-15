#!/usr/bin/env python3
"""
燒天預測權重深度分析工具

測試不同權重配置在各種模擬情境下的表現

作者: BurnSky Team  
日期: 2025-01-27
"""

import sys
sys.path.append('.')

from predictor import calculate_burnsky_score
from weight_optimization_test import calculate_optimized_burnsky_score, CURRENT_WEIGHTS, OPTIMIZED_WEIGHTS
import json
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_scenarios():
    """創建各種測試情境"""
    
    # 基礎天氣數據模板
    base_weather = {
        "temperature": {"data": [{"place": "香港天文台", "unit": "C", "value": 28}], "recordTime": "2025-01-27T18:00:00+08:00"},
        "humidity": {"data": [{"place": "香港天文台", "unit": "percent", "value": 60}], "recordTime": "2025-01-27T18:00:00+08:00"},
        "wind": {"description": "東南風2至3級。", "direction": "SE", "speed_beaufort_min": 2, "speed_beaufort_max": 3},
        "rainfall": {"data": [{"place": "中西區", "max": 0, "unit": "mm"}]},
        "uvindex": {"data": [{"value": 5}]},
        "warningMessage": [],
        "updateTime": "2025-01-27T18:00:00+08:00"
    }
    
    # 基礎預報數據模板
    base_forecast = {
        "forecastDesc": "大致天晴。",
        "updateTime": "2025-01-27T18:00:00+08:00"
    }
    
    scenarios = {
        "ideal_sunset": {
            "name": "理想日落條件",
            "description": "雲層適中、濕度低、能見度高、黃金時段",
            "weather": {
                **base_weather,
                "humidity": {"data": [{"place": "香港天文台", "unit": "percent", "value": 45}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "temperature": {"data": [{"place": "香港天文台", "unit": "C", "value": 30}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "wind": {"description": "西南風1至2級。", "direction": "SW", "speed_beaufort_min": 1, "speed_beaufort_max": 2},
                "uvindex": {"data": [{"value": 8}]}
            },
            "forecast": {
                **base_forecast,
                "forecastDesc": "大致天晴，間中多雲。晚間雲層增加。"
            }
        },
        
        "cloudy_conditions": {
            "name": "多雲條件",
            "description": "厚雲層、高濕度、低能見度",
            "weather": {
                **base_weather,
                "humidity": {"data": [{"place": "香港天文台", "unit": "percent", "value": 85}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "temperature": {"data": [{"place": "香港天文台", "unit": "C", "value": 26}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "wind": {"description": "東風4至5級。", "direction": "E", "speed_beaufort_min": 4, "speed_beaufort_max": 5},
                "uvindex": {"data": [{"value": 2}]},
                "warningMessage": ["能見度較低"]
            },
            "forecast": {
                **base_forecast,
                "forecastDesc": "多雲，間中有雨。雲層較厚，能見度一般。"
            }
        },
        
        "high_cloud_ideal": {
            "name": "高空雲理想條件",
            "description": "高空雲層、低濕度、強陽光",
            "weather": {
                **base_weather,
                "humidity": {"data": [{"place": "香港天文台", "unit": "percent", "value": 40}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "temperature": {"data": [{"place": "香港天文台", "unit": "C", "value": 32}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "wind": {"description": "西風2級。", "direction": "W", "speed_beaufort_min": 2, "speed_beaufort_max": 2},
                "uvindex": {"data": [{"value": 9}]}
            },
            "forecast": {
                **base_forecast,
                "forecastDesc": "天晴，有高空雲。陽光充足，雲層稀薄。"
            }
        },
        
        "poor_air_quality": {
            "name": "空氣污染條件",
            "description": "空氣品質差、低能見度、霧霾",
            "weather": {
                **base_weather,
                "humidity": {"data": [{"place": "香港天文台", "unit": "percent", "value": 70}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "temperature": {"data": [{"place": "香港天文台", "unit": "C", "value": 29}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "wind": {"description": "北風1級。", "direction": "N", "speed_beaufort_min": 1, "speed_beaufort_max": 1},
                "uvindex": {"data": [{"value": 3}]},
                "warningMessage": ["空氣污染警告"]
            },
            "forecast": {
                **base_forecast,
                "forecastDesc": "部分時間有陽光。空氣污染影響能見度。"
            }
        },
        
        "windy_conditions": {
            "name": "大風條件",
            "description": "強風、雲層快速移動",
            "weather": {
                **base_weather,
                "humidity": {"data": [{"place": "香港天文台", "unit": "percent", "value": 55}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "temperature": {"data": [{"place": "香港天文台", "unit": "C", "value": 27}], "recordTime": "2025-01-27T19:00:00+08:00"},
                "wind": {"description": "東北風6至7級。", "direction": "NE", "speed_beaufort_min": 6, "speed_beaufort_max": 7},
                "uvindex": {"data": [{"value": 4}]},
                "warningMessage": ["強風警告"]
            },
            "forecast": {
                **base_forecast,
                "forecastDesc": "多雲，間中有陽光。風勢頗大，雲層移動快速。"
            }
        }
    }
    
    return scenarios

def run_scenario_analysis():
    """運行各種情境的權重分析"""
    
    print("🔥 燒天預測權重情境分析 🔥")
    print("=" * 70)
    
    scenarios = create_test_scenarios()
    ninday_data = []  # 空的九天預報
    
    results = {}
    
    print(f"{'情境':<20} {'當前權重':<12} {'優化權重':<12} {'差異':<10} {'勝出':<8}")
    print("-" * 70)
    
    total_current_wins = 0
    total_optimized_wins = 0
    total_ties = 0
    
    for scenario_key, scenario in scenarios.items():
        weather_data = scenario['weather']
        forecast_data = scenario['forecast']
        
        try:
            # 當前權重計算
            current_score, current_details = calculate_burnsky_score(weather_data, forecast_data, ninday_data)
            
            # 優化權重計算
            optimized_score, optimized_details = calculate_optimized_burnsky_score(weather_data, forecast_data, ninday_data)
            
            # 計算差異
            diff = optimized_score - current_score
            
            # 判斷勝出方
            if diff > 1:
                winner = "優化"
                total_optimized_wins += 1
            elif diff < -1:
                winner = "當前"
                total_current_wins += 1
            else:
                winner = "持平"
                total_ties += 1
            
            results[scenario_key] = {
                'name': scenario['name'],
                'current_score': current_score,
                'optimized_score': optimized_score,
                'difference': diff,
                'winner': winner,
                'current_details': current_details,
                'optimized_details': optimized_details
            }
            
            print(f"{scenario['name']:<20} {current_score:<12.1f} {optimized_score:<12.1f} {diff:<+10.1f} {winner:<8}")
            
        except Exception as e:
            print(f"{scenario['name']:<20} 錯誤: {str(e)}")
            results[scenario_key] = {'error': str(e)}
    
    print("-" * 70)
    print(f"{'統計':<20} {'當前勝出':<12} {'優化勝出':<12} {'持平':<10}")
    print(f"{'次數':<20} {total_current_wins:<12} {total_optimized_wins:<12} {total_ties:<10}")
    
    # 詳細分析
    print("\n📊 詳細情境分析:")
    analyze_scenario_results(results)
    
    return results

def analyze_scenario_results(results):
    """分析各情境結果"""
    
    for scenario_key, result in results.items():
        if 'error' in result:
            continue
            
        print(f"\n🎯 {result['name']}:")
        print(f"   當前權重: {result['current_score']:.1f}分")
        print(f"   優化權重: {result['optimized_score']:.1f}分") 
        print(f"   差異: {result['difference']:+.1f}分")
        
        # 分析主要因子貢獻
        if 'current_details' in result and 'optimized_details' in result:
            analyze_factor_contributions(result['current_details'], result['optimized_details'])

def analyze_factor_contributions(current_details, optimized_details):
    """分析因子貢獻度變化"""
    
    significant_changes = []
    
    # 檢查各因子的變化
    factors = ['time_factor', 'temperature_factor', 'humidity_factor', 'visibility_factor', 
               'cloud_analysis_factor', 'uv_factor', 'wind_factor', 'air_quality_factor']
    
    for factor in factors:
        if factor in current_details and factor in optimized_details:
            current_score = current_details[factor].get('score', 0)
            optimized_score = optimized_details[factor].get('score', 0)
            diff = optimized_score - current_score
            
            if abs(diff) >= 2:  # 顯著變化閾值
                factor_name = factor.replace('_factor', '').replace('_', '')
                significant_changes.append(f"{factor_name}: {diff:+.1f}")
    
    if significant_changes:
        print(f"   主要變化: {', '.join(significant_changes)}")

def generate_weight_recommendations(results):
    """基於情境分析生成權重建議"""
    
    print("\n💡 權重優化建議:")
    
    # 統計優化權重在哪些情境下表現更好
    optimized_better_scenarios = []
    current_better_scenarios = []
    
    for scenario_key, result in results.items():
        if 'error' in result:
            continue
            
        if result['winner'] == '優化':
            optimized_better_scenarios.append(result['name'])
        elif result['winner'] == '當前':
            current_better_scenarios.append(result['name'])
    
    print(f"\n✅ 優化權重適用情境:")
    for scenario in optimized_better_scenarios:
        print(f"   • {scenario}")
    
    print(f"\n⚠️ 當前權重更適用情境:")
    for scenario in current_better_scenarios:
        print(f"   • {scenario}")
    
    # 生成總體建議
    optimized_count = len(optimized_better_scenarios)
    current_count = len(current_better_scenarios)
    
    if optimized_count > current_count:
        print(f"\n🎯 總體建議: 採用優化權重")
        print(f"   優化權重在 {optimized_count}/{optimized_count + current_count} 個情境中表現更好")
    elif current_count > optimized_count:
        print(f"\n🎯 總體建議: 保持當前權重")
        print(f"   當前權重在 {current_count}/{optimized_count + current_count} 個情境中表現更好")
    else:
        print(f"\n🎯 總體建議: 兩種權重平分秋色，建議季節性調整")
    
    # 動態權重建議
    print(f"\n🔄 動態權重策略建議:")
    print(f"   1. 理想燒天條件時：使用優化權重（強調雲層和時間）")
    print(f"   2. 極端天氣條件時：使用當前權重（平衡各因子影響）")
    print(f"   3. 空氣污染嚴重時：降低空氣品質因子權重")
    print(f"   4. 強風天氣時：提高風速因子權重")

def main():
    """主函數"""
    print("🔥 燒天預測權重深度分析工具 🔥")
    print("=" * 50)
    
    # 運行情境分析
    results = run_scenario_analysis()
    
    # 生成建議
    generate_weight_recommendations(results)
    
    print("\n✅ 深度權重分析完成")
    print("建議根據實際使用情境選擇合適的權重配置")

if __name__ == "__main__":
    main()
