#!/usr/bin/env python3
"""
統一計分系統使用示例
展示如何使用新的統一計分系統

作者: BurnSky Team
日期: 2025-07-18
"""

from unified_scorer import calculate_burnsky_score_unified
from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast

def example_basic_usage():
    """基本使用示例"""
    print("🌅 基本使用示例")
    print("=" * 40)
    
    # 獲取天氣數據
    weather_data = fetch_weather_data()
    forecast_data = fetch_forecast_data()
    ninday_data = fetch_ninday_forecast()
    
    # 使用統一計分系統
    result = calculate_burnsky_score_unified(
        weather_data=weather_data,
        forecast_data=forecast_data,
        ninday_data=ninday_data,
        prediction_type='sunset',  # 或 'sunrise'
        advance_hours=2            # 提前2小時預測
    )
    
    # 獲取主要結果
    score = result['final_score']
    level = "極高" if score >= 85 else "高" if score >= 70 else "中等" if score >= 55 else "輕微" if score >= 40 else "低"
    
    print(f"燒天分數: {score:.1f}/100")
    print(f"預測等級: {level}")
    print(f"建議: {result['analysis']['recommendation']}")
    
    return result

def example_detailed_analysis():
    """詳細分析示例"""
    print("\n🔍 詳細分析示例")
    print("=" * 40)
    
    weather_data = fetch_weather_data()
    forecast_data = fetch_forecast_data()
    ninday_data = fetch_ninday_forecast()
    
    result = calculate_burnsky_score_unified(
        weather_data, forecast_data, ninday_data, 'sunset', 0
    )
    
    # 顯示計分明細
    print("📊 計分明細:")
    factor_names = {
        'time': '時間因子', 'temperature': '溫度因子', 'humidity': '濕度因子',
        'visibility': '能見度因子', 'cloud': '雲層因子', 'uv': 'UV指數因子',
        'wind': '風速因子', 'air_quality': '空氣品質因子'
    }
    
    for factor, score in result['factor_scores'].items():
        name = factor_names.get(factor, factor)
        print(f"  {name}: {score}")
    
    # 顯示權重配置
    print(f"\n⚖️ 權重配置: {result['weights_used']}")
    
    # 顯示調整係數
    if result['adjustments']:
        print(f"🔧 調整係數: {result['adjustments']}")
    
    # 顯示最高分因子
    print("\n🏆 得分最高的因子:")
    for factor_info in result['analysis']['top_factors'][:3]:
        print(f"  {factor_info['name']}: {factor_info['score']}/{factor_info['max']}")
    
    return result

def example_comparison():
    """比較不同預測類型"""
    print("\n🆚 預測類型比較")
    print("=" * 40)
    
    weather_data = fetch_weather_data()
    forecast_data = fetch_forecast_data()
    ninday_data = fetch_ninday_forecast()
    
    # 比較即時和提前預測
    immediate = calculate_burnsky_score_unified(
        weather_data, forecast_data, ninday_data, 'sunset', 0
    )
    
    advance_2h = calculate_burnsky_score_unified(
        weather_data, forecast_data, ninday_data, 'sunset', 2
    )
    
    print(f"即時日落預測: {immediate['final_score']:.1f} (權重: {immediate['weights_used']})")
    print(f"2小時後預測: {advance_2h['final_score']:.1f} (權重: {advance_2h['weights_used']})")
    
    # 比較日出和日落
    sunrise = calculate_burnsky_score_unified(
        weather_data, forecast_data, ninday_data, 'sunrise', 0
    )
    
    sunset = calculate_burnsky_score_unified(
        weather_data, forecast_data, ninday_data, 'sunset', 0
    )
    
    print(f"\n日出預測: {sunrise['final_score']:.1f}")
    print(f"日落預測: {sunset['final_score']:.1f}")

def example_error_handling():
    """錯誤處理示例"""
    print("\n🛡️ 錯誤處理示例")
    print("=" * 40)
    
    # 模擬空數據
    empty_data = {}
    
    result = calculate_burnsky_score_unified(
        empty_data, empty_data, empty_data, 'sunset', 0
    )
    
    if 'error' in result:
        print(f"錯誤處理: {result['error']}")
        print(f"保底分數: {result['final_score']}")
    else:
        print("即使空數據也能正常運作")
        print(f"保底分數: {result['final_score']:.1f}")

if __name__ == "__main__":
    print("🎯 統一計分系統使用示例")
    print("=" * 50)
    
    try:
        # 基本使用
        example_basic_usage()
        
        # 詳細分析
        example_detailed_analysis()
        
        # 比較功能
        example_comparison()
        
        # 錯誤處理
        example_error_handling()
        
        print("\n🎊 所有示例執行完成！")
        print("\n💡 使用提示:")
        print("  - 使用 calculate_burnsky_score_unified() 取代所有舊函數")
        print("  - 檢查 result['analysis'] 獲取詳細分析")
        print("  - 利用 result['factor_scores'] 進行自定義分析")
        print("  - 監控 result['adjustments'] 了解分數調整原因")
        
    except Exception as e:
        print(f"❌ 示例執行錯誤: {e}")
        print("請確保已正確設置所有依賴")
