#!/bin/bash
# 燒天預測系統啟動腳本

echo "🌅 燒天預測系統"
echo "======================================"

# 檢查 .env
if [ ! -f ".env" ]; then
    echo "⚠️  找不到 .env，使用 .env.example"
    cp .env.example .env
    echo "✅ 請編輯 .env 後重新啟動"
    exit 0
fi

# 檢查環境配置
echo "🔍 檢查環境配置..."
.venv/bin/python check_env.py

echo ""
echo "🚀 啟動服務器..."
.venv/bin/python app.py
