#!/usr/bin/env python3
"""
前端問題診斷工具
檢查用戶為什麼仍看到26小時錯誤
"""

import requests
import json
from datetime import datetime

def diagnose_frontend_issues():
    """診斷前端可能遇到的問題"""
    print("🔧 前端問題診斷工具")
    print("=" * 50)
    
    ports_to_test = [5000, 5001, 8000, 3000]
    
    print("📡 檢查不同端口上的服務:")
    print("-" * 30)
    
    working_ports = []
    
    for port in ports_to_test:
        try:
            url = f"http://127.0.0.1:{port}/predict/sunrise?advance_hours=4"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                time_factor = data['analysis_details']['time_factor']
                description = time_factor['description']
                
                print(f"端口 {port}: ✅ 運行中")
                print(f"  回應: {description}")
                
                if '26小時' in description or '27小時' in description:
                    print(f"  ❌ 返回錯誤的時間計算！")
                else:
                    print(f"  ✅ 時間計算正確")
                    working_ports.append(port)
                print()
            else:
                print(f"端口 {port}: ❌ HTTP錯誤 {response.status_code}")
                print()
                
        except requests.exceptions.RequestException as e:
            print(f"端口 {port}: ❌ 無法連接")
            print()
    
    if working_ports:
        print("✅ 解決方案:")
        print("-" * 30)
        best_port = working_ports[0]
        print(f"1. 請訪問正確的端口: http://127.0.0.1:{best_port}")
        print("2. 清除瀏覽器緩存 (Ctrl+Shift+Delete 或 Cmd+Shift+Delete)")
        print("3. 使用瀏覽器的強制刷新 (Ctrl+F5 或 Cmd+Shift+R)")
        print("4. 嘗試無痕模式瀏覽")
        print()
        print("📋 如果仍有問題，請複製以下資訊:")
        print(f"- 正確端口: {best_port}")
        print(f"- 測試時間: {datetime.now()}")
        print(f"- 正確API回應: http://127.0.0.1:{best_port}/predict/sunrise?advance_hours=4")
    else:
        print("❌ 沒有找到正常工作的服務")
        print("請重新啟動Flask應用")

if __name__ == "__main__":
    diagnose_frontend_issues()
