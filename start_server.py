#!/usr/bin/env python3
"""
燒天預測系統啟動腳本
"""
import os
import sys

def start_burnsky_server():
    """啟動燒天預測服務器"""
    print("🌅 啟動燒天預測系統...")
    print("=" * 50)
    
    try:
        from app import app
        print("✅ Flask 應用載入成功")
        
        # 獲取端口
        port = int(os.environ.get('PORT', 8080))
        
        print(f"🚀 啟動服務器於 http://localhost:{port}")
        print("📱 功能包括：")
        print("   • 進階燒天預測 (/predict)")
        print("   • 日出預測 (/predict/sunrise)")
        print("   • 日落預測 (/predict/sunset)")
        print("   • 雲層厚度與顏色可見度分析")
        print("   • AI 機器學習分數權重")
        print("   • 黃金時段準確預測")
        print("")
        print("🔧 使用 Ctrl+C 停止服務器")
        print("=" * 50)
        
        # 啟動服務器
        app.run(host='0.0.0.0', port=port, debug=True)
        
    except KeyboardInterrupt:
        print("\n👋 服務器已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_burnsky_server()
