#!/usr/bin/env python3
"""
燒天預測系統本地啟動腳本
使用說明：python3 local_start.py
"""
import os
import sys
import subprocess

def check_requirements():
    """檢查並安裝所需套件"""
    print("🔍 檢查 Python 套件...")
    
    required_packages = [
        'Flask', 'requests', 'pandas', 'scikit-learn', 
        'numpy', 'astral', 'pytz', 'schedule'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower())
            print(f"✅ {package} 已安裝")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 未安裝")
    
    if missing_packages:
        print(f"\n📦 安裝缺少的套件: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("✅ 套件安裝完成")
    else:
        print("✅ 所有套件已準備就緒")

def start_server():
    """啟動本地服務器"""
    print("\n🌅 啟動燒天預測系統...")
    print("=" * 60)
    
    try:
        # 設置環境變數
        os.environ.setdefault('PORT', '8080')
        
        # 導入 Flask 應用
        from app import app
        
        print("✅ Flask 應用載入成功")
        print("\n📱 系統功能：")
        print("   🌅 日出燒天預測")
        print("   🌇 日落燒天預測") 
        print("   🤖 AI 機器學習分析")
        print("   ☁️ 雲層厚度分析")
        print("   🎨 顏色可見度預測")
        print("   📊 詳細天氣數據")
        
        port = 8080
        print(f"\n🚀 服務器啟動於: http://localhost:{port}")
        print(f"🌐 主頁面: http://localhost:{port}")
        print(f"🔗 API 端點: http://localhost:{port}/predict")
        print("\n💡 使用提示：")
        print("   • 在瀏覽器中開啟上述網址")
        print("   • 使用 Ctrl+C 停止服務器")
        print("=" * 60)
        
        # 啟動 Flask 開發服務器
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=False  # 避免重複啟動
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 服務器已停止")
        print("感謝使用燒天預測系統！")
    except Exception as e:
        print(f"\n❌ 啟動失敗: {e}")
        print("\n🔧 故障排除建議：")
        print("   1. 確認 Python 版本 >= 3.7")
        print("   2. 檢查套件是否正確安裝")
        print("   3. 確認端口 8080 未被占用")
        return 1

def main():
    """主函數"""
    print("🌅 BurnSky 燒天預測系統 - 本地啟動器")
    print("=" * 60)
    
    try:
        # 檢查並安裝依賴
        check_requirements()
        
        # 啟動服務器
        return start_server()
        
    except Exception as e:
        print(f"❌ 系統錯誤: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
