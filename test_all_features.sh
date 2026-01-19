#!/bin/bash
# 快速測試所有新功能

echo "🚀 燒天API - 功能測試套件"
echo "========================================"
echo ""

# 檢查Python環境
if [ ! -d ".venv" ]; then
    echo "❌ 虛擬環境不存在"
    exit 1
fi

echo "1️⃣ 測試環境變量..."
.venv/bin/python check_env.py | head -20
echo ""

echo "2️⃣ 測試日誌配置..."
.venv/bin/python -c "from app import logger; logger.info('測試日誌'); print('✅ 日誌系統正常')"
echo ""

echo "3️⃣ 運行單元測試..."
.venv/bin/pytest tests/ -v --tb=short -q 2>&1 | tail -5
echo ""

echo "4️⃣ 檢查依賴包..."
echo "已安裝的關鍵套件:"
.venv/bin/pip list | grep -E "(flask|pytest|limiter|dotenv|swagger)" | awk '{print "  - " $1 " (" $2 ")"}'
echo ""

echo "========================================"
echo "✅ 所有測試完成"
echo ""
echo "📝 啟動應用命令:"
echo "   ./start.sh"
echo ""
echo "📊 查看日誌:"
echo "   tail -f app.log"
echo ""
echo "🧪 運行測試:"
echo "   .venv/bin/pytest tests/ -v"
echo "========================================"
