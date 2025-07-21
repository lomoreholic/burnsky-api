#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
警告數據可視化儀表板
功能：
1. 警告歷史趨勢圖表
2. 季節性模式分析
3. 影響分數分布
4. 實時警告監控
5. 預測準確性評估
"""

import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Tuple
import warnings as python_warnings

# 設置中文字體和圖表樣式
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
python_warnings.filterwarnings('ignore')

class WarningDashboard:
    """警告數據可視化儀表板"""
    
    def __init__(self, db_path="warning_history.db"):
        """初始化儀表板"""
        self.db_path = db_path
        self.colors = {
            'extreme': '#FF0000',    # 紅色
            'severe': '#FF8C00',     # 橙色  
            'moderate': '#FFD700',   # 金色
            'low': '#90EE90',        # 淺綠色
            'minimal': '#E0E0E0'     # 灰色
        }
        
        self.category_colors = {
            'rainfall': '#4285F4',      # 藍色
            'wind_storm': '#34A853',    # 綠色
            'thunderstorm': '#FBBC05',  # 黃色
            'visibility': '#EA4335',    # 紅色
            'air_quality': '#9AA0A6',   # 灰色
            'temperature': '#FF6D01',   # 橙色
            'marine': '#1A73E8'         # 深藍色
        }
        
        print("📊 警告數據可視化儀表板已初始化")
    
    def load_warning_data(self, days_back: int = 30) -> pd.DataFrame:
        """載入警告數據"""
        conn = sqlite3.connect(self.db_path)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        query = '''
            SELECT * FROM warning_records 
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date.isoformat(), end_date.isoformat()))
        conn.close()
        
        if len(df) > 0:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
        
        return df
    
    def load_prediction_data(self, days_back: int = 30) -> pd.DataFrame:
        """載入預測數據"""
        conn = sqlite3.connect(self.db_path)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        query = '''
            SELECT * FROM prediction_records 
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp
        '''
        
        df = pd.read_sql_query(query, conn, params=(start_date.isoformat(), end_date.isoformat()))
        conn.close()
        
        if len(df) > 0:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
        
        return df
    
    def plot_warning_timeline(self, days_back: int = 30, save_path: str = None) -> str:
        """繪製警告時間線圖"""
        df = self.load_warning_data(days_back)
        
        if len(df) == 0:
            print("⚠️ 無警告數據可繪製")
            return None
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # 圖1: 每日警告數量趨勢
        daily_counts = df.groupby('date').size()
        daily_counts.index = pd.to_datetime(daily_counts.index)
        
        ax1.plot(daily_counts.index, daily_counts.values, marker='o', linewidth=2, markersize=6)
        ax1.fill_between(daily_counts.index, daily_counts.values, alpha=0.3)
        ax1.set_title(f'過去 {days_back} 天警告數量趨勢', fontsize=16, fontweight='bold')
        ax1.set_ylabel('警告數量', fontsize=12)
        ax1.grid(True, alpha=0.3)
        
        # 格式化日期軸
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days_back//10)))
        
        # 圖2: 按嚴重度分類的堆疊面積圖
        severity_by_date = df.groupby(['date', 'severity']).size().unstack(fill_value=0)
        severity_by_date.index = pd.to_datetime(severity_by_date.index)
        
        # 按嚴重度排序
        severity_order = ['minimal', 'low', 'moderate', 'severe', 'extreme']
        available_severities = [s for s in severity_order if s in severity_by_date.columns]
        
        if available_severities:
            severity_by_date = severity_by_date[available_severities]
            colors = [self.colors[s] for s in available_severities]
            
            ax2.stackplot(severity_by_date.index, 
                         *[severity_by_date[col] for col in available_severities],
                         labels=available_severities, colors=colors, alpha=0.8)
            
            ax2.set_title('警告嚴重度分布趨勢', fontsize=16, fontweight='bold')
            ax2.set_ylabel('警告數量', fontsize=12)
            ax2.set_xlabel('日期', fontsize=12)
            ax2.legend(loc='upper right')
            ax2.grid(True, alpha=0.3)
            
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            ax2.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days_back//10)))
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = f"warning_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 警告時間線圖已保存: {save_path}")
        return save_path
    
    def plot_category_distribution(self, days_back: int = 30, save_path: str = None) -> str:
        """繪製警告類別分布圖"""
        df = self.load_warning_data(days_back)
        
        if len(df) == 0:
            print("⚠️ 無警告數據可繪製")
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 圖1: 警告類別圓餅圖
        category_counts = df['category'].value_counts()
        colors = [self.category_colors.get(cat, '#999999') for cat in category_counts.index]
        
        wedges, texts, autotexts = ax1.pie(category_counts.values, labels=category_counts.index, 
                                          autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('警告類別分布', fontsize=14, fontweight='bold')
        
        # 圖2: 嚴重度分布條形圖
        severity_counts = df['severity'].value_counts()
        severity_colors = [self.colors.get(sev, '#999999') for sev in severity_counts.index]
        
        bars = ax2.bar(severity_counts.index, severity_counts.values, color=severity_colors)
        ax2.set_title('警告嚴重度分布', fontsize=14, fontweight='bold')
        ax2.set_ylabel('數量')
        ax2.tick_params(axis='x', rotation=45)
        
        # 在條形圖上添加數值
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # 圖3: 影響分數分布直方圖
        if 'impact_score' in df.columns and not df['impact_score'].isna().all():
            ax3.hist(df['impact_score'].dropna(), bins=20, color='skyblue', alpha=0.7, edgecolor='black')
            ax3.axvline(df['impact_score'].mean(), color='red', linestyle='--', 
                       label=f'平均值: {df["impact_score"].mean():.1f}')
            ax3.set_title('警告影響分數分布', fontsize=14, fontweight='bold')
            ax3.set_xlabel('影響分數')
            ax3.set_ylabel('頻率')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # 圖4: 每小時警告頻率
        if 'hour' in df.columns:
            hourly_counts = df['hour'].value_counts().sort_index()
            ax4.bar(hourly_counts.index, hourly_counts.values, color='lightcoral', alpha=0.7)
            ax4.set_title('每小時警告頻率', fontsize=14, fontweight='bold')
            ax4.set_xlabel('小時')
            ax4.set_ylabel('警告數量')
            ax4.set_xticks(range(0, 24, 3))
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = f"warning_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 警告分布圖已保存: {save_path}")
        return save_path
    
    def plot_seasonal_analysis(self, save_path: str = None) -> str:
        """繪製季節性分析圖"""
        df = self.load_warning_data(365)  # 載入一年數據
        
        if len(df) == 0:
            print("⚠️ 無足夠數據進行季節性分析")
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 圖1: 季節性警告分布
        if 'season' in df.columns:
            season_counts = df['season'].value_counts()
            season_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            
            ax1.pie(season_counts.values, labels=season_counts.index, autopct='%1.1f%%',
                   colors=season_colors[:len(season_counts)], startangle=90)
            ax1.set_title('季節性警告分布', fontsize=14, fontweight='bold')
        
        # 圖2: 月份警告趨勢
        df['month'] = df['timestamp'].dt.month
        monthly_counts = df.groupby('month').size()
        
        ax2.plot(monthly_counts.index, monthly_counts.values, marker='o', linewidth=2, markersize=8)
        ax2.fill_between(monthly_counts.index, monthly_counts.values, alpha=0.3)
        ax2.set_title('月份警告趨勢', fontsize=14, fontweight='bold')
        ax2.set_xlabel('月份')
        ax2.set_ylabel('警告數量')
        ax2.set_xticks(range(1, 13))
        ax2.grid(True, alpha=0.3)
        
        # 圖3: 季節與警告類別的熱力圖
        if 'season' in df.columns:
            season_category = pd.crosstab(df['season'], df['category'])
            sns.heatmap(season_category, annot=True, fmt='d', cmap='YlOrRd', ax=ax3)
            ax3.set_title('季節-警告類別關聯熱力圖', fontsize=14, fontweight='bold')
            ax3.set_xlabel('警告類別')
            ax3.set_ylabel('季節')
        
        # 圖4: 週內警告模式
        if 'day_of_week' in df.columns:
            dow_counts = df['day_of_week'].value_counts()
            # 重新排序為週一到週日
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow_counts = dow_counts.reindex([d for d in day_order if d in dow_counts.index])
            
            bars = ax4.bar(range(len(dow_counts)), dow_counts.values, 
                          color=['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC', '#99CCFF', '#FFB366'])
            ax4.set_title('週內警告模式', fontsize=14, fontweight='bold')
            ax4.set_xlabel('星期')
            ax4.set_ylabel('警告數量')
            ax4.set_xticks(range(len(dow_counts)))
            ax4.set_xticklabels([d[:3] for d in dow_counts.index], rotation=45)
            
            # 在條形圖上添加數值
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = f"seasonal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"🌍 季節性分析圖已保存: {save_path}")
        return save_path
    
    def plot_prediction_accuracy(self, days_back: int = 30, save_path: str = None) -> str:
        """繪製預測準確性分析圖"""
        pred_df = self.load_prediction_data(days_back)
        
        if len(pred_df) == 0:
            print("⚠️ 無預測數據可繪製")
            return None
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 圖1: 警告影響分數分布
        if 'warning_impact' in pred_df.columns:
            ax1.hist(pred_df['warning_impact'].dropna(), bins=15, color='lightblue', 
                    alpha=0.7, edgecolor='black')
            ax1.axvline(pred_df['warning_impact'].mean(), color='red', linestyle='--',
                       label=f'平均值: {pred_df["warning_impact"].mean():.1f}')
            ax1.set_title('警告影響分數分布', fontsize=14, fontweight='bold')
            ax1.set_xlabel('警告影響分數')
            ax1.set_ylabel('頻率')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # 圖2: 原始分數vs最終分數散點圖
        if 'original_score' in pred_df.columns and 'final_score' in pred_df.columns:
            ax2.scatter(pred_df['original_score'], pred_df['final_score'], 
                       alpha=0.6, color='green', s=50)
            
            # 添加45度參考線
            max_score = max(pred_df['original_score'].max(), pred_df['final_score'].max())
            ax2.plot([0, max_score], [0, max_score], 'r--', alpha=0.8, label='無影響線')
            
            ax2.set_title('原始分數 vs 最終分數', fontsize=14, fontweight='bold')
            ax2.set_xlabel('原始分數')
            ax2.set_ylabel('最終分數')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # 圖3: 提前預測時間分布
        if 'advance_hours' in pred_df.columns:
            advance_counts = pred_df['advance_hours'].value_counts().sort_index()
            bars = ax3.bar(advance_counts.index, advance_counts.values, color='orange', alpha=0.7)
            ax3.set_title('提前預測時間分布', fontsize=14, fontweight='bold')
            ax3.set_xlabel('提前小時數')
            ax3.set_ylabel('預測次數')
            ax3.grid(True, alpha=0.3)
            
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom')
        
        # 圖4: 預測類型分布
        if 'prediction_type' in pred_df.columns:
            type_counts = pred_df['prediction_type'].value_counts()
            colors = ['#FFB366', '#66B2FF']
            
            wedges, texts, autotexts = ax4.pie(type_counts.values, labels=type_counts.index,
                                              autopct='%1.1f%%', colors=colors[:len(type_counts)],
                                              startangle=90)
            ax4.set_title('預測類型分布', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path is None:
            save_path = f"prediction_accuracy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"🎯 預測準確性圖已保存: {save_path}")
        return save_path
    
    def generate_dashboard_report(self, days_back: int = 30) -> Dict[str, str]:
        """生成完整的儀表板報告"""
        print(f"📊 生成警告數據可視化儀表板報告 (過去 {days_back} 天)")
        print("=" * 60)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period": f"{days_back}天",
            "charts": {}
        }
        
        # 生成所有圖表
        try:
            print("📈 生成警告時間線圖...")
            timeline_chart = self.plot_warning_timeline(days_back)
            if timeline_chart:
                report["charts"]["timeline"] = timeline_chart
            
            print("📊 生成警告分布圖...")
            distribution_chart = self.plot_category_distribution(days_back)
            if distribution_chart:
                report["charts"]["distribution"] = distribution_chart
            
            print("🌍 生成季節性分析圖...")
            seasonal_chart = self.plot_seasonal_analysis()
            if seasonal_chart:
                report["charts"]["seasonal"] = seasonal_chart
            
            print("🎯 生成預測準確性圖...")
            accuracy_chart = self.plot_prediction_accuracy(days_back)
            if accuracy_chart:
                report["charts"]["accuracy"] = accuracy_chart
            
            # 保存報告摘要
            report_file = f"dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 儀表板報告生成完成！")
            print(f"📄 報告摘要: {report_file}")
            print(f"📊 生成圖表: {len(report['charts'])} 個")
            
            return report
            
        except Exception as e:
            print(f"❌ 儀表板生成失敗: {e}")
            return {"error": str(e)}

def demo_dashboard():
    """演示儀表板功能"""
    print("📊 警告數據可視化儀表板 - 功能演示")
    print("=" * 50)
    
    # 初始化儀表板
    dashboard = WarningDashboard()
    
    # 生成完整報告
    report = dashboard.generate_dashboard_report(30)
    
    print(f"\n📊 生成的圖表:")
    for chart_type, file_path in report.get("charts", {}).items():
        print(f"   - {chart_type}: {file_path}")
    
    print(f"\n💡 提示:")
    print(f"   - 圖表已保存為PNG格式，可在瀏覽器或圖片查看器中打開")
    print(f"   - 可將圖表整合到網頁儀表板或報告中")
    print(f"   - 支持自定義時間範圍和圖表樣式")
    
    return dashboard

if __name__ == "__main__":
    demo_dashboard()
