#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
警告數據收集器 - 與燒天預測API整合
功能：
1. 自動收集天氣警告數據
2. 整合到現有預測流程
3. 實時數據存儲
4. 定期分析和報告
"""

import json
import sqlite3
import schedule
import time
from datetime import datetime, timedelta
import threading
from typing import Dict, List
import logging

# 導入現有模組
from hko_fetcher import fetch_warning_data
from warning_history_analyzer import WarningHistoryAnalyzer

class WarningDataCollector:
    """警告數據收集器"""
    
    def __init__(self, db_path="warning_history.db", collection_interval=30):
        """
        初始化收集器
        
        Args:
            db_path: 數據庫路徑
            collection_interval: 收集間隔(分鐘)
        """
        self.db_path = db_path
        self.collection_interval = collection_interval
        self.analyzer = WarningHistoryAnalyzer(db_path)
        self.is_running = False
        self.last_collection_time = None
        
        # 設置日誌
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        print(f"🤖 警告數據收集器已初始化")
        print(f"   📁 數據庫: {db_path}")
        print(f"   ⏰ 收集間隔: {collection_interval}分鐘")
    
    def collect_current_warnings(self) -> Dict:
        """收集當前警告數據"""
        try:
            # 使用現有的HKO數據獲取功能
            warning_data = fetch_warning_data()
            
            if not warning_data or 'details' not in warning_data:
                self.logger.info("📭 當前無天氣警告")
                return {"status": "no_warnings", "warnings": []}
            
            warnings_list = warning_data.get('details', [])
            collection_result = {
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "warnings_count": len(warnings_list),
                "warnings": warnings_list,
                "raw_data": warning_data
            }
            
            # 記錄每個警告
            warning_ids = []
            for warning in warnings_list:
                try:
                    # 構建標準化的警告數據
                    warning_record = {
                        "warning_text": warning if isinstance(warning, str) else str(warning),
                        "source": "HKO_API",
                        "collection_time": datetime.now().isoformat()
                    }
                    
                    # 添加天氣上下文（如果需要）
                    weather_context = {
                        "data_source": "HKO",
                        "collection_method": "automated",
                        "api_response": warning_data
                    }
                    
                    warning_id = self.analyzer.record_warning(warning_record, weather_context)
                    warning_ids.append(warning_id)
                    
                except Exception as e:
                    self.logger.error(f"❌ 記錄警告失敗: {warning} - {e}")
            
            collection_result["recorded_ids"] = warning_ids
            self.last_collection_time = datetime.now()
            
            self.logger.info(f"✅ 成功收集 {len(warnings_list)} 個警告")
            return collection_result
            
        except Exception as e:
            self.logger.error(f"❌ 警告數據收集失敗: {e}")
            return {"status": "error", "error": str(e)}
    
    def start_automated_collection(self):
        """啟動自動化收集"""
        if self.is_running:
            self.logger.warning("⚠️ 自動收集已在運行中")
            return
        
        self.is_running = True
        
        # 設置定期任務
        schedule.every(self.collection_interval).minutes.do(self.collect_current_warnings)
        
        # 設置每日分析報告（早上8點）
        schedule.every().day.at("08:00").do(self.generate_daily_report)
        
        # 設置每週深度分析（週一早上9點）
        schedule.every().monday.at("09:00").do(self.generate_weekly_analysis)
        
        def run_scheduler():
            """運行調度器"""
            self.logger.info("🚀 啟動自動化警告數據收集")
            # 立即執行一次收集
            self.collect_current_warnings()
            
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # 每分鐘檢查一次
        
        # 在後台線程中運行
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info(f"✅ 自動化收集已啟動 (間隔: {self.collection_interval}分鐘)")
    
    def stop_automated_collection(self):
        """停止自動化收集"""
        self.is_running = False
        schedule.clear()
        self.logger.info("⏹️ 自動化收集已停止")
    
    def generate_daily_report(self):
        """生成每日報告"""
        try:
            self.logger.info("📊 生成每日警告分析報告...")
            
            # 分析過去24小時的警告
            analysis = self.analyzer.analyze_warning_patterns(1)
            
            # 生成簡化報告
            daily_report = {
                "report_type": "daily_warning_summary",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "summary": {
                    "total_warnings": analysis.get('total_warnings', 0),
                    "categories": analysis.get('category_distribution', {}),
                    "severities": analysis.get('severity_distribution', {}),
                    "peak_hours": analysis.get('temporal_patterns', {}).get('hourly_distribution', {})
                },
                "generated_at": datetime.now().isoformat()
            }
            
            # 保存報告
            report_filename = f"daily_warning_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(daily_report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📄 每日報告已生成: {report_filename}")
            
        except Exception as e:
            self.logger.error(f"❌ 每日報告生成失敗: {e}")
    
    def generate_weekly_analysis(self):
        """生成每週深度分析"""
        try:
            self.logger.info("📈 生成每週警告深度分析...")
            
            # 執行完整分析
            insights = self.analyzer.generate_warning_insights()
            patterns = self.analyzer.analyze_warning_patterns(7)
            seasonal = self.analyzer.analyze_seasonal_trends()
            
            # 生成週報
            weekly_report = {
                "report_type": "weekly_warning_analysis",
                "week_ending": datetime.now().strftime("%Y-%m-%d"),
                "insights": insights,
                "patterns": patterns,
                "seasonal_analysis": seasonal,
                "generated_at": datetime.now().isoformat()
            }
            
            # 保存報告
            report_filename = f"weekly_warning_analysis_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(weekly_report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"📊 每週分析已生成: {report_filename}")
            
        except Exception as e:
            self.logger.error(f"❌ 每週分析生成失敗: {e}")
    
    def get_collection_status(self) -> Dict:
        """獲取收集器狀態"""
        return {
            "is_running": self.is_running,
            "collection_interval": self.collection_interval,
            "last_collection": self.last_collection_time.isoformat() if self.last_collection_time else None,
            "database_path": self.db_path,
            "scheduled_tasks": len(schedule.jobs),
            "uptime": (datetime.now() - self.last_collection_time) if self.last_collection_time else None
        }
    
    def manual_analysis(self, days_back: int = 7) -> str:
        """手動觸發分析"""
        try:
            self.logger.info(f"🔍 手動觸發 {days_back} 天警告分析...")
            report_file = self.analyzer.export_analysis_report()
            self.logger.info(f"✅ 手動分析完成: {report_file}")
            return report_file
        except Exception as e:
            self.logger.error(f"❌ 手動分析失敗: {e}")
            raise

def integrate_with_app():
    """與主應用程序整合的示例代碼"""
    
    # 全局收集器實例
    global warning_collector
    warning_collector = None
    
    def init_warning_collection():
        """初始化警告收集器"""
        global warning_collector
        try:
            warning_collector = WarningDataCollector(
                db_path="warning_history.db",
                collection_interval=30  # 30分鐘收集一次
            )
            warning_collector.start_automated_collection()
            print("✅ 警告數據收集器已啟動")
            return True
        except Exception as e:
            print(f"❌ 警告收集器啟動失敗: {e}")
            return False
    
    def record_prediction_with_warnings(prediction_data: Dict, warning_data: Dict):
        """記錄預測時同時記錄警告數據"""
        global warning_collector
        if warning_collector and warning_collector.analyzer:
            try:
                # 記錄預測
                prediction_id = warning_collector.analyzer.record_prediction(prediction_data)
                
                # 記錄關聯的警告
                if warning_data and 'details' in warning_data:
                    for warning in warning_data['details']:
                        warning_record = {
                            "warning_text": warning,
                            "prediction_context": prediction_data,
                            "prediction_id": prediction_id
                        }
                        warning_collector.analyzer.record_warning(warning_record)
                
                return prediction_id
            except Exception as e:
                print(f"⚠️ 記錄預測和警告失敗: {e}")
        return None
    
    def get_warning_statistics():
        """獲取警告統計信息（供API使用）"""
        global warning_collector
        if warning_collector and warning_collector.analyzer:
            try:
                # 獲取過去7天的統計
                patterns = warning_collector.analyzer.analyze_warning_patterns(7)
                return {
                    "status": "success",
                    "statistics": patterns
                }
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }
        return {"status": "not_initialized"}
    
    return {
        "init_warning_collection": init_warning_collection,
        "record_prediction_with_warnings": record_prediction_with_warnings,
        "get_warning_statistics": get_warning_statistics
    }

def demo_collection_system():
    """演示收集系統"""
    print("🤖 警告數據收集系統 - 演示")
    print("=" * 50)
    
    # 初始化收集器
    collector = WarningDataCollector(collection_interval=1)  # 1分鐘間隔用於演示
    
    print("\n📊 獲取收集器狀態...")
    status = collector.get_collection_status()
    print(f"   運行狀態: {status['is_running']}")
    print(f"   收集間隔: {status['collection_interval']}分鐘")
    
    print("\n📡 執行手動警告收集...")
    result = collector.collect_current_warnings()
    print(f"   收集狀態: {result['status']}")
    print(f"   警告數量: {result.get('warnings_count', 0)}")
    
    if result.get('warnings'):
        print("   收集到的警告:")
        for i, warning in enumerate(result['warnings'], 1):
            print(f"      {i}. {warning}")
    
    print("\n🔍 執行手動分析...")
    try:
        report_file = collector.manual_analysis(7)
        print(f"   分析報告: {report_file}")
    except Exception as e:
        print(f"   分析失敗: {e}")
    
    print("\n✅ 收集系統演示完成！")
    print("💡 提示: 在生產環境中使用 collector.start_automated_collection() 啟動自動收集")
    
    return collector

if __name__ == "__main__":
    demo_collection_system()
