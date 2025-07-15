#!/usr/bin/env python3
"""
燒天預測因子權重分析

分析當前各個因子的權重分配是否合理，並提出改進建議

作者: BurnSky Team  
日期: 2025-01-27
"""

import sys
sys.path.append('.')

from predictor import calculate_burnsky_score
from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast
import json
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_factor_weights():
    """分析當前因子權重分配"""
    
    # 當前權重分配
    current_weights = {
        'time_factor': 18,           # 時間因子 (日出日落最佳時間)
        'temperature_factor': 18,    # 溫度因子 (高溫有利燒天)
        'humidity_factor': 22,       # 濕度因子 (低濕度有利)
        'visibility_factor': 18,     # 能見度因子 (高能見度重要)
        'cloud_analysis_factor': 30, # 雲層因子 (最關鍵)
        'uv_factor': 12,            # UV指數因子 (陽光強度)
        'wind_factor': 10,          # 風速因子 (適度風速)
        'air_quality_factor': 12,   # 空氣品質因子 (透明度)
    }
    
    total_weight = sum(current_weights.values())
    
    print("=== 燒天預測因子權重分析 ===")
    print(f"總分: {total_weight} 分")
    print()
    
    print("當前權重分配:")
    for factor, weight in sorted(current_weights.items(), key=lambda x: x[1], reverse=True):
        percentage = (weight / total_weight) * 100
        factor_name = get_factor_chinese_name(factor)
        print(f"  {factor_name:<12} {weight:2d}分 ({percentage:5.1f}%)")
    
    print()
    return current_weights, total_weight

def get_factor_chinese_name(factor):
    """獲取因子中文名稱"""
    names = {
        'time_factor': '時間因子',
        'temperature_factor': '溫度因子', 
        'humidity_factor': '濕度因子',
        'visibility_factor': '能見度因子',
        'cloud_analysis_factor': '雲層因子',
        'uv_factor': 'UV指數因子',
        'wind_factor': '風速因子',
        'air_quality_factor': '空氣品質因子'
    }
    return names.get(factor, factor)

def analyze_factor_importance():
    """分析各因子對燒天的實際重要性"""
    
    print("=== 因子重要性分析 ===")
    
    factor_importance = {
        'cloud_analysis_factor': {
            'importance': '極高',
            'reasoning': '雲層是燒天最關鍵因素，決定光線散射和顏色層次',
            'ideal_weight': '25-35%',
            'current_weight': 30
        },
        'time_factor': {
            'importance': '高',
            'reasoning': '日出日落時間決定太陽角度和光線品質',
            'ideal_weight': '15-20%',
            'current_weight': 18
        },
        'humidity_factor': {
            'importance': '高', 
            'reasoning': '濕度影響大氣透明度和色彩飽和度',
            'ideal_weight': '15-20%',
            'current_weight': 22
        },
        'temperature_factor': {
            'importance': '中高',
            'reasoning': '溫度影響大氣穩定性和熱對流',
            'ideal_weight': '12-18%',
            'current_weight': 18
        },
        'visibility_factor': {
            'importance': '中高',
            'reasoning': '能見度直接影響燒天清晰度',
            'ideal_weight': '12-18%',
            'current_weight': 18
        },
        'air_quality_factor': {
            'importance': '中',
            'reasoning': '空氣品質影響透明度，但與能見度重疊',
            'ideal_weight': '8-12%',
            'current_weight': 12
        },
        'uv_factor': {
            'importance': '中',
            'reasoning': 'UV指數反映陽光強度，影響燒天亮度',
            'ideal_weight': '8-12%',
            'current_weight': 12
        },
        'wind_factor': {
            'importance': '中低',
            'reasoning': '風速影響雲層流動，但影響相對較小',
            'ideal_weight': '5-10%',
            'current_weight': 10
        }
    }
    
    total_current = sum([f['current_weight'] for f in factor_importance.values()])
    
    for factor, info in factor_importance.items():
        factor_name = get_factor_chinese_name(factor)
        current_pct = (info['current_weight'] / total_current) * 100
        print(f"{factor_name}:")
        print(f"  重要性: {info['importance']}")
        print(f"  原因: {info['reasoning']}")
        print(f"  建議權重: {info['ideal_weight']}")
        print(f"  當前權重: {info['current_weight']}分 ({current_pct:.1f}%)")
        print()
    
    return factor_importance

def suggest_weight_optimization():
    """建議權重優化方案"""
    
    print("=== 權重優化建議 ===")
    
    # 建議的新權重分配
    suggested_weights = {
        'cloud_analysis_factor': 35,  # 提高雲層重要性
        'time_factor': 20,           # 保持時間重要性
        'humidity_factor': 20,       # 保持濕度重要性
        'temperature_factor': 15,    # 稍微降低溫度
        'visibility_factor': 15,     # 稍微降低能見度
        'air_quality_factor': 8,     # 降低空氣品質（與能見度重疊）
        'uv_factor': 10,            # 稍微降低UV
        'wind_factor': 7,           # 降低風速
    }
    
    total_suggested = sum(suggested_weights.values())
    
    print(f"建議新的權重分配 (總分: {total_suggested}):")
    for factor, weight in sorted(suggested_weights.items(), key=lambda x: x[1], reverse=True):
        percentage = (weight / total_suggested) * 100
        factor_name = get_factor_chinese_name(factor)
        print(f"  {factor_name:<12} {weight:2d}分 ({percentage:5.1f}%)")
    
    print()
    print("主要調整理由:")
    print("1. 雲層因子 (30→35分): 雲層是燒天最關鍵因素，應該有最高權重")
    print("2. 濕度因子 (22→20分): 保持高重要性，但稍微調整")
    print("3. 溫度/能見度 (18→15分): 重要但不是最關鍵")
    print("4. 空氣品質 (12→8分): 與能見度功能重疊，降低權重")
    print("5. 風速因子 (10→7分): 影響相對較小")
    print()
    
    return suggested_weights

def test_current_prediction():
    """測試當前預測結果"""
    
    print("=== 當前預測結果測試 ===")
    
    try:
        # 獲取天氣數據
        weather_data = fetch_weather_data()
        forecast_data = fetch_forecast_data()
        ninday_data = fetch_ninday_forecast()
        
        # 計算燒天分數
        score, details = calculate_burnsky_score(weather_data, forecast_data, ninday_data)
        
        print(f"當前燒天總分: {score:.1f}")
        print()
        print("各因子得分:")
        
        factor_scores = {}
        for factor_key, factor_data in details.items():
            if factor_key.endswith('_factor') and isinstance(factor_data, dict):
                factor_score = factor_data.get('score', 0)
                factor_scores[factor_key] = factor_score
                factor_name = get_factor_chinese_name(factor_key)
                print(f"  {factor_name:<12} {factor_score:2d}分")
        
        total_factor_score = sum(factor_scores.values())
        print(f"  因子總分:      {total_factor_score:2d}分")
        
        # 檢查是否有ML預測
        if 'ml_prediction' in details:
            ml_score = details['ml_prediction'].get('ml_burnsky_score', 0)
            print(f"  ML預測分數:    {ml_score:.1f}分")
        
        print()
        return factor_scores, score
        
    except Exception as e:
        print(f"測試失敗: {e}")
        return None, None

def main():
    """主函數"""
    print("🔥 燒天預測因子權重分析工具 🔥")
    print("=" * 50)
    
    # 1. 分析當前權重
    current_weights, total_weight = analyze_factor_weights()
    
    # 2. 分析因子重要性
    factor_importance = analyze_factor_importance()
    
    # 3. 建議優化方案
    suggested_weights = suggest_weight_optimization()
    
    # 4. 測試當前預測
    factor_scores, total_score = test_current_prediction()
    
    print("=== 總結建議 ===")
    print("當前權重分配基本合理，但有以下建議:")
    print("1. 雲層因子可以進一步提高權重 (30→35分)")
    print("2. 空氣品質因子可以降低權重，避免與能見度重疊 (12→8分)")
    print("3. 總體而言，高重要性因子(雲層、時間、濕度)已獲得適當權重")
    print("4. 建議進行 A/B 測試來驗證調整後的準確性")

if __name__ == "__main__":
    main()
