#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
警告歷史數據分析系統 - 快速演示
"""

def demo_warning_analysis():
    """警告歷史分析系統演示"""
    print("🎬 警告歷史數據分析系統 - 快速演示")
    print("=" * 50)
    
    try:
        from warning_history_analyzer import WarningHistoryAnalyzer
        print("✅ 成功載入警告分析器")
        
        # 初始化分析器
        analyzer = WarningHistoryAnalyzer()
        print("✅ 分析器初始化完成")
        
        # 模擬記錄一些警告
        warnings = [
            "黑色暴雨警告信號現正生效",
            "八號烈風信號現正生效", 
            "雷暴警告",
            "紅色暴雨警告信號現正生效"
        ]
        
        print(f"\n📝 記錄 {len(warnings)} 個模擬警告...")
        for warning in warnings:
            warning_id = analyzer.record_warning({"warning_text": warning})
            print(f"   ✅ 已記錄: {warning} (ID: {warning_id})")
        
        # 記錄一些預測
        predictions = [
            {
                "prediction_type": "sunset",
                "advance_hours": 0,
                "original_score": 75,
                "warning_impact": 15,
                "warning_risk_impact": 0,
                "final_score": 60,
                "warnings_active": ["八號烈風信號"]
            },
            {
                "prediction_type": "sunset",
                "advance_hours": 2,
                "original_score": 80,
                "warning_impact": 25,
                "warning_risk_impact": 5,
                "final_score": 50,
                "warnings_active": ["黑色暴雨警告"]
            }
        ]
        
        print(f"\n📈 記錄 {len(predictions)} 個模擬預測...")
        for pred in predictions:
            pred_id = analyzer.record_prediction(pred)
            print(f"   ✅ 已記錄: {pred['prediction_type']} 預測 (ID: {pred_id})")
        
        # 執行分析
        print(f"\n🔍 執行警告模式分析...")
        patterns = analyzer.analyze_warning_patterns(30)
        print(f"   📊 總警告數: {patterns.get('total_warnings', 0)}")
        print(f"   📊 警告類別: {list(patterns.get('category_distribution', {}).keys())}")
        
        print(f"\n💡 生成系統洞察...")
        insights = analyzer.generate_warning_insights()
        recommendations = insights.get('recommendations', [])
        print(f"   💡 系統建議數量: {len(recommendations)}")
        for i, rec in enumerate(recommendations[:2], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n📄 導出分析報告...")
        report_file = analyzer.export_analysis_report()
        print(f"   📋 報告已生成: {report_file}")
        
        print(f"\n✅ 演示完成！警告歷史分析系統運作正常")
        print(f"🎯 系統具備以下能力:")
        print(f"   - 自動記錄警告和預測數據")
        print(f"   - 多維度模式分析")
        print(f"   - 季節性趨勢識別")
        print(f"   - 預測準確性評估")
        print(f"   - 智能洞察生成")
        print(f"   - 完整報告導出")
        
        return True
        
    except ImportError:
        print("❌ 警告分析模組未找到，請確保檔案已正確建立")
        return False
    except Exception as e:
        print(f"❌ 演示執行失敗: {e}")
        return False

def show_api_endpoints():
    """顯示新增的API端點"""
    print(f"\n🔌 新增的警告分析API端點:")
    print(f"   GET  /api/warnings/history    - 警告歷史分析")
    print(f"   GET  /api/warnings/seasonal   - 季節性分析")
    print(f"   GET  /api/warnings/insights   - 數據洞察")
    print(f"   GET  /api/warnings/accuracy   - 準確性評估")
    print(f"   POST /api/warnings/record     - 手動記錄警告")
    print(f"   GET  /api/warnings/export     - 導出分析報告")
    print(f"   GET  /api/warnings/collector/status - 收集器狀態")

def show_integration_info():
    """顯示集成信息"""
    print(f"\n🔗 與主應用程序的集成:")
    print(f"   - 每次預測時自動記錄警告和預測數據")
    print(f"   - 警告分析器與現有警告系統整合")
    print(f"   - 新API端點擴展了系統功能")
    print(f"   - 版本號已更新至: v1.3_with_history_analysis")

if __name__ == "__main__":
    print("🚀 啟動警告歷史數據分析系統演示")
    
    # 執行演示
    success = demo_warning_analysis()
    
    # 顯示API信息
    show_api_endpoints()
    
    # 顯示集成信息
    show_integration_info()
    
    if success:
        print(f"\n🎉 警告歷史數據分析系統已成功建立並準備就緒！")
    else:
        print(f"\n⚠️ 演示未能完全成功，請檢查系統配置")
