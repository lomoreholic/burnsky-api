#!/usr/bin/env python3
"""
燒天預測系統 - 網站保活工具
定期 ping 網站以防止 Render 服務休眠
"""

import requests
import time
import schedule
from datetime import datetime
import sys
import signal

class WebsiteKeepAlive:
    def __init__(self, url, interval_minutes=25):
        self.url = url
        self.interval_minutes = interval_minutes
        self.running = True
        
    def ping_website(self):
        """Ping 網站並記錄狀態"""
        try:
            start_time = time.time()
            response = requests.get(self.url, timeout=30)
            response_time = time.time() - start_time
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if response.status_code == 200:
                print(f"[{timestamp}] ✅ 網站正常 - 響應時間: {response_time:.2f}s")
                
                # 如果響應時間超過10秒，表示服務剛被喚醒
                if response_time > 10:
                    print(f"[{timestamp}] 🔄 服務剛從休眠中喚醒")
                    
                return True
            else:
                print(f"[{timestamp}] ❌ 網站異常 - 狀態碼: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"[{timestamp}] ⏰ 請求超時")
            return False
        except requests.exceptions.ConnectionError:
            print(f"[{timestamp}] 🔌 連接失敗")
            return False
        except Exception as e:
            print(f"[{timestamp}] 💥 錯誤: {str(e)}")
            return False
    
    def signal_handler(self, signum, frame):
        """處理中斷信號"""
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🛑 收到停止信號，正在安全退出...")
        self.running = False
        sys.exit(0)
    
    def start(self):
        """開始保活服務"""
        print(f"🔥 燒天預測系統保活工具啟動")
        print(f"🌐 目標網站: {self.url}")
        print(f"⏰ 檢查間隔: {self.interval_minutes} 分鐘")
        print(f"📋 按 Ctrl+C 停止")
        print("=" * 50)
        
        # 註冊信號處理器
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # 立即執行一次檢查
        self.ping_website()
        
        # 設定定期任務
        schedule.every(self.interval_minutes).minutes.do(self.ping_website)
        
        # 主循環
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                self.signal_handler(None, None)

def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://burnsky-api.onrender.com"
    
    # 可選：設定檢查間隔（分鐘）
    interval = 25  # 預設 25 分鐘（Render 30分鐘休眠，我們提前喚醒）
    
    if len(sys.argv) > 2:
        try:
            interval = int(sys.argv[2])
        except ValueError:
            print("❌ 間隔時間必須是數字（分鐘）")
            sys.exit(1)
    
    keeper = WebsiteKeepAlive(url, interval)
    keeper.start()

if __name__ == "__main__":
    main()
