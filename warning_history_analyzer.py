#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
警告歷史數據分析系統
功能：
1. 警告數據收集和存儲
2. 歷史趨勢分析
3. 季節性模式識別
4. 預測準確性評估
5. 警告影響效果評估
"""

import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from collections import defaultdict, Counter
import statistics
from typing import Dict, List, Tuple, Optional

class WarningHistoryAnalyzer:
    """警告歷史數據分析器"""
    
    def __init__(self, db_path="warning_history.db"):
        """初始化分析器"""
        self.db_path = db_path
        self.init_database()
        print(f"📊 警告歷史分析器已初始化 - 數據庫: {db_path}")
    
    def init_database(self):
        """初始化數據庫結構"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 警告記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                warning_text TEXT NOT NULL,
                category TEXT,
                subcategory TEXT,
                severity TEXT,
                level INTEGER,
                impact_score REAL,
                area_specific BOOLEAN,
                duration_hint TEXT,
                time_of_day TEXT,
                season TEXT,
                weather_context TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 預測記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                prediction_type TEXT,
                advance_hours INTEGER,
                original_score REAL,
                warning_impact REAL,
                warning_risk_impact REAL,
                final_score REAL,
                actual_result TEXT,
                accuracy_score REAL,
                warnings_active TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 警告影響評估表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS warning_impact_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warning_id INTEGER,
                prediction_id INTEGER,
                impact_type TEXT,
                expected_impact REAL,
                actual_impact REAL,
                accuracy_rating TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warning_id) REFERENCES warning_records (id),
                FOREIGN KEY (prediction_id) REFERENCES prediction_records (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ 數據庫結構初始化完成")
    
    def record_warning(self, warning_data: Dict, weather_context: Dict = None) -> int:
        """記錄警告數據"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # 解析警告信息（重用app.py中的函數邏輯）
        warning_info = self._parse_warning_for_storage(warning_data)
        
        # 獲取環境信息
        current_hour = datetime.now().hour
        current_month = datetime.now().month
        
        time_of_day = 'day'
        if 17 <= current_hour <= 19:
            time_of_day = 'sunset'
        elif 5 <= current_hour <= 7:
            time_of_day = 'sunrise'
        
        season = 'summer'
        if current_month in [12, 1, 2]:
            season = 'winter'
        elif current_month in [3, 4, 5]:
            season = 'spring'
        elif current_month in [9, 10, 11]:
            season = 'autumn'
        
        cursor.execute('''
            INSERT INTO warning_records 
            (timestamp, warning_text, category, subcategory, severity, level, 
             impact_score, area_specific, duration_hint, time_of_day, season, weather_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            warning_info['warning_text'],
            warning_info['category'],
            warning_info['subcategory'],
            warning_info['severity'],
            warning_info['level'],
            warning_info['impact_score'],
            warning_info['area_specific'],
            warning_info['duration_hint'],
            time_of_day,
            season,
            json.dumps(weather_context) if weather_context else None
        ))
        
        warning_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"📝 已記錄警告: {warning_info['category']}-{warning_info['severity']} (ID: {warning_id})")
        return warning_id
    
    def record_prediction(self, prediction_data: Dict) -> int:
        """記錄預測數據"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO prediction_records 
            (timestamp, prediction_type, advance_hours, original_score, warning_impact, 
             warning_risk_impact, final_score, warnings_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            prediction_data.get('prediction_type', 'sunset'),
            prediction_data.get('advance_hours', 0),
            prediction_data.get('original_score', 0),
            prediction_data.get('warning_impact', 0),
            prediction_data.get('warning_risk_impact', 0),
            prediction_data.get('final_score', 0),
            json.dumps(prediction_data.get('warnings_active', []))
        ))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"📈 已記錄預測: {prediction_data.get('prediction_type')} (ID: {prediction_id})")
        return prediction_id
    
    def analyze_warning_patterns(self, days_back: int = 30) -> Dict:
        """分析警告模式"""
        conn = sqlite3.connect(self.db_path)
        
        # 計算時間範圍
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # 查詢警告數據
        query = '''
            SELECT * FROM warning_records 
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date.isoformat(), end_date.isoformat()))
        conn.close()
        
        if len(df) == 0:
            return {"message": "指定期間內無警告數據", "period": f"{days_back}天"}
        
        analysis = {
            "analysis_period": f"{days_back}天",
            "total_warnings": len(df),
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            }
        }
        
        # 1. 警告類別分布
        category_dist = df['category'].value_counts().to_dict()
        analysis['category_distribution'] = category_dist
        
        # 2. 嚴重度分布
        severity_dist = df['severity'].value_counts().to_dict()
        analysis['severity_distribution'] = severity_dist
        
        # 3. 時間分布分析
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.day_name()
        
        hour_dist = df['hour'].value_counts().sort_index().to_dict()
        dow_dist = df['day_of_week'].value_counts().to_dict()
        
        analysis['temporal_patterns'] = {
            "hourly_distribution": hour_dist,
            "day_of_week_distribution": dow_dist
        }
        
        # 4. 季節性分析
        season_dist = df['season'].value_counts().to_dict()
        analysis['seasonal_patterns'] = season_dist
        
        # 5. 影響分數統計
        impact_stats = {
            "mean": round(df['impact_score'].mean(), 2),
            "median": round(df['impact_score'].median(), 2),
            "max": round(df['impact_score'].max(), 2),
            "min": round(df['impact_score'].min(), 2),
            "std": round(df['impact_score'].std(), 2)
        }
        analysis['impact_score_statistics'] = impact_stats
        
        # 6. 高影響警告識別
        high_impact_threshold = df['impact_score'].quantile(0.8)
        high_impact_warnings = df[df['impact_score'] >= high_impact_threshold]
        
        analysis['high_impact_warnings'] = {
            "threshold": round(high_impact_threshold, 2),
            "count": len(high_impact_warnings),
            "percentage": round(len(high_impact_warnings) / len(df) * 100, 1),
            "most_common_categories": high_impact_warnings['category'].value_counts().head(3).to_dict()
        }
        
        # 7. 地區性警告分析
        area_specific_count = len(df[df['area_specific'] == True])
        analysis['area_specific_analysis'] = {
            "total_area_specific": area_specific_count,
            "percentage": round(area_specific_count / len(df) * 100, 1),
            "hong_kong_wide": len(df) - area_specific_count
        }
        
        return analysis
    
    def analyze_seasonal_trends(self) -> Dict:
        """分析季節性趨勢"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT season, category, severity, impact_score, 
                   COUNT(*) as frequency,
                   AVG(impact_score) as avg_impact
            FROM warning_records 
            GROUP BY season, category, severity
            ORDER BY season, frequency DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) == 0:
            return {"message": "無足夠數據進行季節性分析"}
        
        seasonal_analysis = {}
        
        for season in df['season'].unique():
            season_data = df[df['season'] == season]
            
            seasonal_analysis[season] = {
                "total_warnings": season_data['frequency'].sum(),
                "most_common_categories": season_data.groupby('category')['frequency'].sum().sort_values(ascending=False).head(3).to_dict(),
                "severity_distribution": season_data.groupby('severity')['frequency'].sum().to_dict(),
                "average_impact_by_category": season_data.groupby('category')['avg_impact'].mean().round(2).to_dict(),
                "highest_impact_warnings": season_data.nlargest(3, 'avg_impact')[['category', 'severity', 'avg_impact']].to_dict('records')
            }
        
        # 季節比較
        seasonal_comparison = {
            "most_active_season": df.groupby('season')['frequency'].sum().idxmax(),
            "highest_impact_season": df.groupby('season')['avg_impact'].mean().idxmax(),
            "seasonal_impact_ranking": df.groupby('season')['avg_impact'].mean().sort_values(ascending=False).to_dict()
        }
        
        return {
            "seasonal_breakdown": seasonal_analysis,
            "seasonal_comparison": seasonal_comparison,
            "analysis_note": "基於歷史警告數據的季節性模式分析"
        }
    
    def evaluate_prediction_accuracy(self, days_back: int = 7) -> Dict:
        """評估預測準確性"""
        conn = sqlite3.connect(self.db_path)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # 查詢預測記錄
        query = '''
            SELECT * FROM prediction_records 
            WHERE timestamp >= ? AND timestamp <= ?
            AND actual_result IS NOT NULL
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date.isoformat(), end_date.isoformat()))
        conn.close()
        
        if len(df) == 0:
            return {"message": f"過去{days_back}天內無足夠預測數據進行準確性評估"}
        
        accuracy_analysis = {
            "evaluation_period": f"{days_back}天",
            "total_predictions": len(df),
            "evaluated_predictions": len(df[df['actual_result'].notna()])
        }
        
        # 警告影響準確性
        if 'accuracy_score' in df.columns:
            accuracy_stats = {
                "mean_accuracy": round(df['accuracy_score'].mean(), 2),
                "median_accuracy": round(df['accuracy_score'].median(), 2),
                "accuracy_above_80": len(df[df['accuracy_score'] >= 0.8]),
                "accuracy_below_60": len(df[df['accuracy_score'] < 0.6])
            }
            accuracy_analysis['accuracy_statistics'] = accuracy_stats
        
        # 警告影響效果分析
        warning_impact_analysis = {
            "predictions_with_warnings": len(df[df['warning_impact'] > 0]),
            "average_warning_impact": round(df['warning_impact'].mean(), 2),
            "max_warning_impact": round(df['warning_impact'].max(), 2),
            "warning_risk_predictions": len(df[df['warning_risk_impact'] > 0]),
            "average_risk_impact": round(df['warning_risk_impact'].mean(), 2)
        }
        accuracy_analysis['warning_impact_analysis'] = warning_impact_analysis
        
        # 按預測類型分析
        type_analysis = {}
        for pred_type in df['prediction_type'].unique():
            type_data = df[df['prediction_type'] == pred_type]
            type_analysis[pred_type] = {
                "count": len(type_data),
                "avg_accuracy": round(type_data['accuracy_score'].mean(), 2) if 'accuracy_score' in type_data.columns else None,
                "avg_warning_impact": round(type_data['warning_impact'].mean(), 2)
            }
        
        accuracy_analysis['by_prediction_type'] = type_analysis
        
        return accuracy_analysis
    
    def generate_warning_insights(self) -> Dict:
        """生成警告數據洞察"""
        # 綜合分析
        patterns = self.analyze_warning_patterns(30)
        seasonal = self.analyze_seasonal_trends()
        accuracy = self.evaluate_prediction_accuracy(7)
        
        insights = {
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_warnings_30d": patterns.get('total_warnings', 0),
                "most_common_warning": max(patterns.get('category_distribution', {}).items(), key=lambda x: x[1]) if patterns.get('category_distribution') else None,
                "highest_impact_category": None,
                "seasonal_trend": seasonal.get('seasonal_comparison', {}).get('most_active_season'),
                "prediction_accuracy": accuracy.get('accuracy_statistics', {}).get('mean_accuracy')
            },
            "recommendations": [],
            "data_quality": self._assess_data_quality()
        }
        
        # 生成建議
        recommendations = []
        
        if patterns.get('total_warnings', 0) > 0:
            high_impact = patterns.get('high_impact_warnings', {})
            if high_impact.get('percentage', 0) > 20:
                recommendations.append("建議加強高影響警告的預測模型權重")
            
            category_dist = patterns.get('category_distribution', {})
            if category_dist:
                most_common = max(category_dist.items(), key=lambda x: x[1])
                recommendations.append(f"最常見警告類型為{most_common[0]}，建議優化此類警告的處理邏輯")
        
        if seasonal.get('seasonal_comparison'):
            most_active = seasonal['seasonal_comparison'].get('most_active_season')
            if most_active:
                recommendations.append(f"{most_active}季節警告最頻繁，建議增強該季節的預測敏感度")
        
        if accuracy.get('accuracy_statistics'):
            acc_stats = accuracy['accuracy_statistics']
            if acc_stats.get('mean_accuracy', 0) < 0.7:
                recommendations.append("預測準確性偏低，建議調整警告影響計算算法")
        
        insights['recommendations'] = recommendations
        
        return insights
    
    def export_analysis_report(self, output_file: str = None) -> str:
        """導出分析報告"""
        if output_file is None:
            output_file = f"warning_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 生成完整報告
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "警告歷史數據分析報告",
                "version": "1.0"
            },
            "pattern_analysis": self.analyze_warning_patterns(30),
            "seasonal_analysis": self.analyze_seasonal_trends(),
            "accuracy_evaluation": self.evaluate_prediction_accuracy(7),
            "insights_and_recommendations": self.generate_warning_insights()
        }
        
        # 保存報告
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📊 分析報告已導出: {output_file}")
        return output_file
    
    def _parse_warning_for_storage(self, warning_data: Dict) -> Dict:
        """解析警告數據用於存儲 - 增強版，支持JSON格式警告"""
        import json
        import ast
        
        # 提取警告文本和代碼
        warning_text = ""
        warning_code = ""
        
        if isinstance(warning_data, str):
            # 嘗試解析JSON字符串格式的警告
            try:
                if warning_data.startswith('{') and warning_data.endswith('}'):
                    parsed_data = ast.literal_eval(warning_data)
                    if isinstance(parsed_data, dict):
                        # 提取contents數組並合併
                        if 'contents' in parsed_data and isinstance(parsed_data['contents'], list):
                            warning_text = ' '.join(parsed_data['contents'])
                        else:
                            warning_text = str(parsed_data)
                        warning_code = parsed_data.get('warningStatementCode', '')
                    else:
                        warning_text = warning_data
                else:
                    warning_text = warning_data
            except:
                warning_text = warning_data
        else:
            # 處理字典格式
            if 'contents' in warning_data and isinstance(warning_data['contents'], list):
                warning_text = ' '.join(warning_data['contents'])
            else:
                warning_text = warning_data.get('warning_text', str(warning_data))
            warning_code = warning_data.get('warningStatementCode', '')
        
        # 初始化警告信息
        warning_info = {
            'warning_text': warning_text,
            'category': 'unknown',
            'subcategory': '',
            'severity': 'low',
            'level': 0,
            'impact_score': 0,
            'area_specific': False,
            'duration_hint': '',
            'warning_code': warning_code
        }
        
        text_lower = warning_text.lower()
        
        # 1. 優先使用官方警告代碼分類
        if warning_code:
            if warning_code == 'WTS':
                warning_info['category'] = 'thunderstorm'
                warning_info['subcategory'] = 'general_thunderstorm'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 10
            elif warning_code == 'WHOT':
                warning_info['category'] = 'temperature'
                warning_info['subcategory'] = 'extreme_heat'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 8
            elif warning_code == 'WCOLD':
                warning_info['category'] = 'temperature'
                warning_info['subcategory'] = 'extreme_cold'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 6
            elif warning_code == 'WTCSGNL':
                warning_info['category'] = 'wind_storm'
                warning_info['subcategory'] = 'tropical_cyclone'
                warning_info['severity'] = 'severe'
                warning_info['level'] = 3
                warning_info['impact_score'] = 20
            elif warning_code in ['WFNTSA', 'WL']:
                warning_info['category'] = 'wind_storm'
                warning_info['subcategory'] = 'strong_wind'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 12
            elif warning_code in ['WRAIN', 'WR']:
                warning_info['category'] = 'rainfall'
                warning_info['subcategory'] = 'heavy_rain'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 15
            elif warning_code == 'WFOG':
                warning_info['category'] = 'visibility'
                warning_info['subcategory'] = 'fog'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 12
        
        # 2. 如果沒有警告代碼或代碼未識別，使用文本關鍵詞分析
        if warning_info['category'] == 'unknown':
            if any(keyword in text_lower for keyword in ['黑雨', '紅雨', '黃雨', '暴雨', '大雨', '豪雨']):
                warning_info['category'] = 'rainfall'
                if '黑雨' in text_lower:
                    warning_info['severity'] = 'extreme'
                    warning_info['level'] = 4
                    warning_info['impact_score'] = 35
                elif '紅雨' in text_lower:
                    warning_info['severity'] = 'severe'
                    warning_info['level'] = 3
                    warning_info['impact_score'] = 25
                else:
                    warning_info['severity'] = 'moderate'
                    warning_info['level'] = 2
                    warning_info['impact_score'] = 15
            elif any(keyword in text_lower for keyword in ['風球', '颱風', '熱帶氣旋', '烈風', '強風信號', '十號', '九號', '八號', '三號', '一號']):
                warning_info['category'] = 'wind_storm'
                if any(num in text_lower for num in ['十號', '10號', '颶風']):
                    warning_info['severity'] = 'extreme'
                    warning_info['level'] = 5
                    warning_info['impact_score'] = 40
                elif any(num in text_lower for num in ['九號', '9號', '八號', '8號']):
                    warning_info['severity'] = 'severe'
                    warning_info['level'] = 3
                    warning_info['impact_score'] = 25
                else:
                    warning_info['severity'] = 'moderate'
                    warning_info['level'] = 2
                    warning_info['impact_score'] = 15
            elif any(keyword in text_lower for keyword in ['雷暴', '閃電', '雷電']):
                warning_info['category'] = 'thunderstorm'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 10
            elif any(keyword in text_lower for keyword in ['霧', '能見度', '視野']):
                warning_info['category'] = 'visibility'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 12
            elif any(keyword in text_lower for keyword in ['酷熱', '高溫', '炎熱']):
                warning_info['category'] = 'temperature'
                warning_info['subcategory'] = 'extreme_heat'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 8
            elif any(keyword in text_lower for keyword in ['寒冷', '低溫', '嚴寒']):
                warning_info['category'] = 'temperature'
                warning_info['subcategory'] = 'extreme_cold'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 6
            elif any(keyword in text_lower for keyword in ['海事', '大浪', '海浪', '小艇']):
                warning_info['category'] = 'marine'
                warning_info['subcategory'] = 'marine_warning'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 8
            elif any(keyword in text_lower for keyword in ['空氣污染', 'pm2.5', 'pm10', '臭氧']):
                warning_info['category'] = 'air_quality'
                warning_info['subcategory'] = 'pollution'
                warning_info['severity'] = 'moderate'
                warning_info['level'] = 2
                warning_info['impact_score'] = 6
        
        # 3. 檢查地區特定警告
        if any(region in text_lower for region in ['新界', '港島', '九龍', '離島', '北區', '東區', '大嶼山']):
            warning_info['area_specific'] = True
        
        # 4. 檢查時間相關提示
        if any(time_word in text_lower for time_word in ['持續', '預計', '未來', '即將', '稍後']):
            warning_info['duration_hint'] = '持續性警告'
        elif any(time_word in text_lower for time_word in ['短暫', '間歇', '局部']):
            warning_info['duration_hint'] = '間歇性警告'
        
        return warning_info
    
    def _assess_data_quality(self) -> Dict:
        """評估數據質量"""
        conn = sqlite3.connect(self.db_path)
        
        # 統計各表的數據量
        warning_count = pd.read_sql_query("SELECT COUNT(*) as count FROM warning_records", conn).iloc[0]['count']
        prediction_count = pd.read_sql_query("SELECT COUNT(*) as count FROM prediction_records", conn).iloc[0]['count']
        
        # 檢查數據完整性
        incomplete_warnings = pd.read_sql_query(
            "SELECT COUNT(*) as count FROM warning_records WHERE category = 'unknown'", 
            conn
        ).iloc[0]['count']
        
        conn.close()
        
        quality_score = 100
        issues = []
        
        if warning_count < 10:
            quality_score -= 30
            issues.append("警告數據量不足，建議收集更多歷史數據")
        
        if prediction_count < 5:
            quality_score -= 20
            issues.append("預測數據量不足，建議進行更多預測記錄")
        
        if incomplete_warnings > warning_count * 0.1:
            quality_score -= 25
            issues.append("存在較多未識別的警告類型，建議改進解析邏輯")
        
        return {
            "overall_score": max(0, quality_score),
            "data_counts": {
                "warnings": warning_count,
                "predictions": prediction_count,
                "incomplete_warnings": incomplete_warnings
            },
            "issues": issues,
            "recommendations": [
                "定期執行數據分析以監控數據質量",
                "建立自動化數據收集流程",
                "定期更新警告解析規則"
            ]
        }

def demo_warning_analysis():
    """示範警告分析功能"""
    print("🔍 警告歷史數據分析系統 - 功能演示")
    print("=" * 60)
    
    # 初始化分析器
    analyzer = WarningHistoryAnalyzer()
    
    # 模擬一些歷史警告數據
    sample_warnings = [
        "黑色暴雨警告信號現正生效",
        "八號烈風信號現正生效",
        "雷暴警告",
        "大霧警告",
        "紅色暴雨警告信號現正生效",
        "三號強風信號現正生效"
    ]
    
    print(f"\n📝 模擬記錄 {len(sample_warnings)} 個警告...")
    for warning in sample_warnings:
        analyzer.record_warning({"warning_text": warning})
    
    # 模擬一些預測數據
    sample_predictions = [
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
    
    print(f"\n📈 模擬記錄 {len(sample_predictions)} 個預測...")
    for prediction in sample_predictions:
        analyzer.record_prediction(prediction)
    
    # 執行分析
    print(f"\n🔍 執行警告模式分析...")
    patterns = analyzer.analyze_warning_patterns(30)
    print(f"   - 總警告數: {patterns.get('total_warnings', 0)}")
    print(f"   - 警告類別分布: {patterns.get('category_distribution', {})}")
    
    print(f"\n🌍 執行季節性趨勢分析...")
    seasonal = analyzer.analyze_seasonal_trends()
    if 'seasonal_comparison' in seasonal:
        print(f"   - 最活躍季節: {seasonal['seasonal_comparison'].get('most_active_season', 'N/A')}")
    
    print(f"\n📊 執行預測準確性評估...")
    accuracy = analyzer.evaluate_prediction_accuracy(7)
    print(f"   - 評估期間: {accuracy.get('evaluation_period', 'N/A')}")
    print(f"   - 總預測數: {accuracy.get('total_predictions', 0)}")
    
    print(f"\n💡 生成洞察和建議...")
    insights = analyzer.generate_warning_insights()
    recommendations = insights.get('recommendations', [])
    for i, rec in enumerate(recommendations, 1):
        print(f"   {i}. {rec}")
    
    # 導出報告
    print(f"\n📄 導出分析報告...")
    report_file = analyzer.export_analysis_report()
    
    print(f"\n✅ 警告歷史數據分析演示完成！")
    print(f"📊 詳細報告已保存至: {report_file}")
    
    return analyzer

if __name__ == "__main__":
    demo_warning_analysis()
