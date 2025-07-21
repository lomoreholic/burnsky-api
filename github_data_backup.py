#!/usr/bin/env python3
"""
警告歷史數據 GitHub 自動備份系統
自動將 SQLite 數據庫備份到 GitHub repository
"""

import os
import json
import sqlite3
import subprocess
from datetime import datetime
import shutil

class GitHubDataBackup:
    def __init__(self, db_path="warning_history.db"):
        self.db_path = db_path
        self.backup_dir = "data_backups"
        self.ensure_backup_directory()
        
    def ensure_backup_directory(self):
        """確保備份目錄存在"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
    def export_to_json(self):
        """將 SQLite 數據庫導出為 JSON 格式"""
        if not os.path.exists(self.db_path):
            print("❌ 警告歷史數據庫不存在")
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 導出所有表的數據
            tables = ['warning_records', 'prediction_records', 'warning_impact_analysis']
            backup_data = {
                'backup_timestamp': datetime.now().isoformat(),
                'database_info': {
                    'file_size_kb': os.path.getsize(self.db_path) / 1024,
                    'tables': tables
                },
                'data': {}
            }
            
            for table in tables:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                # 獲取列名
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [column[1] for column in cursor.fetchall()]
                
                # 轉換為字典格式
                table_data = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    table_data.append(row_dict)
                    
                backup_data['data'][table] = {
                    'count': len(table_data),
                    'columns': columns,
                    'records': table_data
                }
                
            conn.close()
            
            # 保存 JSON 文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_filename = f"{self.backup_dir}/warning_history_backup_{timestamp}.json"
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ 數據成功導出到: {json_filename}")
            return json_filename
            
        except Exception as e:
            print(f"❌ 導出數據時發生錯誤: {e}")
            return None
    
    def copy_database(self):
        """複製數據庫文件到備份目錄"""
        if not os.path.exists(self.db_path):
            print("❌ 警告歷史數據庫不存在")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.backup_dir}/warning_history_{timestamp}.db"
        
        try:
            shutil.copy2(self.db_path, backup_filename)
            print(f"✅ 數據庫已備份到: {backup_filename}")
            return backup_filename
        except Exception as e:
            print(f"❌ 備份數據庫時發生錯誤: {e}")
            return None
    
    def create_summary_report(self):
        """創建數據摘要報告"""
        if not os.path.exists(self.db_path):
            return None
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 統計數據
            cursor.execute("SELECT COUNT(*) FROM warning_records")
            warning_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM prediction_records") 
            prediction_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT category, COUNT(*) FROM warning_records GROUP BY category")
            category_stats = dict(cursor.fetchall())
            
            cursor.execute("SELECT severity, COUNT(*) FROM warning_records GROUP BY severity")
            severity_stats = dict(cursor.fetchall())
            
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM warning_records")
            date_range = cursor.fetchone()
            
            conn.close()
            
            # 創建報告
            report = {
                'generated_at': datetime.now().isoformat(),
                'database_summary': {
                    'total_warnings': warning_count,
                    'total_predictions': prediction_count,
                    'date_range': {
                        'first_record': date_range[0],
                        'last_record': date_range[1]
                    },
                    'category_distribution': category_stats,
                    'severity_distribution': severity_stats
                }
            }
            
            # 保存報告
            report_filename = f"{self.backup_dir}/data_summary.json"
            with open(report_filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
                
            print(f"✅ 數據摘要報告已生成: {report_filename}")
            return report_filename
            
        except Exception as e:
            print(f"❌ 生成摘要報告時發生錯誤: {e}")
            return None
    
    def git_add_and_commit(self, message=None):
        """將備份文件添加到 git 並提交"""
        try:
            if message is None:
                message = f"自動備份警告歷史數據 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # 添加備份目錄到 git
            subprocess.run(['git', 'add', self.backup_dir], check=True)
            
            # 提交變更
            subprocess.run(['git', 'commit', '-m', message], check=True)
            
            print(f"✅ Git 提交成功: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git 操作失敗: {e}")
            return False
    
    def push_to_github(self):
        """推送到 GitHub"""
        try:
            subprocess.run(['git', 'push', 'origin', 'main'], check=True)
            print("✅ 成功推送到 GitHub!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 推送到 GitHub 失敗: {e}")
            return False
    
    def full_backup(self):
        """執行完整備份流程"""
        print("🚀 開始執行警告歷史數據 GitHub 備份...")
        
        # 1. 導出 JSON 格式
        json_file = self.export_to_json()
        
        # 2. 複製數據庫文件
        db_file = self.copy_database()
        
        # 3. 創建摘要報告
        summary_file = self.create_summary_report()
        
        if json_file or db_file or summary_file:
            # 4. Git 提交
            if self.git_add_and_commit():
                # 5. 推送到 GitHub
                self.push_to_github()
                print("🎉 備份完成！數據已保存到 GitHub")
            else:
                print("⚠️ 備份文件已創建，但 Git 提交失敗")
        else:
            print("❌ 備份失敗，沒有文件被創建")

def main():
    """主函數"""
    backup_system = GitHubDataBackup()
    backup_system.full_backup()

if __name__ == "__main__":
    main()
