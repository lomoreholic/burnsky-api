#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
簡化的開發伺服器啟動腳本
"""

if __name__ == '__main__':
    print("🌅 正在啟動燒天預測系統...")
    print("=" * 50)
    
    from app import app
    
    print("✅ App 載入成功")
    print("🚀 啟動開發伺服器於 http://localhost:5001")
    print("=" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        use_reloader=False
    )
