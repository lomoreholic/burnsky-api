#!/usr/bin/env python3
"""
環境變量配置驗證工具
檢查所有必要的環境變量是否正確設置
"""

import os
from dotenv import load_dotenv

# 載入環境變量
load_dotenv()

# 定義必需和可選的環境變量
REQUIRED_VARS = []  # 目前沒有強制要求的變量

OPTIONAL_VARS = {
    'FLASK_ENV': 'development',
    'FLASK_DEBUG': 'True',
    'SECRET_KEY': '隨機生成',
    'PORT': '5001',
    'HOST': '0.0.0.0',
    'CACHE_DURATION': '300',
    'RATE_LIMIT_ENABLED': 'True',
    'RATE_LIMIT_DEFAULT': '200 per hour, 50 per minute',
    'UPLOAD_FOLDER': 'uploads',
    'MAX_FILE_SIZE': '16777216',
    'PREDICTION_HISTORY_DB': 'prediction_history.db',
}

def check_env_vars():
    """檢查環境變量配置"""
    print("🔍 環境變量配置檢查")
    print("=" * 60)
    
    # 檢查必需變量
    if REQUIRED_VARS:
        print("\n📋 必需變量:")
        missing = []
        for var in REQUIRED_VARS:
            value = os.getenv(var)
            if value:
                print(f"  ✅ {var} = {value[:20]}..." if len(value) > 20 else f"  ✅ {var} = {value}")
            else:
                print(f"  ❌ {var} = 未設置")
                missing.append(var)
        
        if missing:
            print(f"\n⚠️  缺少必需變量: {', '.join(missing)}")
            return False
    
    # 檢查可選變量
    print("\n📋 可選變量 (當前值 | 默認值):")
    for var, default in OPTIONAL_VARS.items():
        value = os.getenv(var)
        if value:
            display_value = value[:30] + "..." if len(value) > 30 else value
            print(f"  ✅ {var:<25} = {display_value}")
        else:
            print(f"  ⚪ {var:<25} = (使用默認: {default})")
    
    # 顯示配置摘要
    print("\n" + "=" * 60)
    print("📊 配置摘要:")
    print(f"  環境模式: {os.getenv('FLASK_ENV', 'development')}")
    print(f"  Debug: {os.getenv('FLASK_DEBUG', 'True')}")
    print(f"  端口: {os.getenv('PORT', '5001')}")
    print(f"  速率限制: {os.getenv('RATE_LIMIT_ENABLED', 'True')}")
    print(f"  快取時長: {os.getenv('CACHE_DURATION', '300')}秒")
    
    print("\n✅ 環境變量配置檢查完成！")
    return True

if __name__ == "__main__":
    check_env_vars()
