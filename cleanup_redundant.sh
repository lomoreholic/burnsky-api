#!/bin/bash
# 清理冗餘文件腳本

echo "🧹 清理冗餘文件"
echo "======================================"

# 創建備份目錄（如果需要保留）
BACKUP_DIR="old_backups"
# mkdir -p "$BACKUP_DIR"

# 要刪除的舊備份和測試文件
FILES_TO_REMOVE=(
    "app_backup_20260119.py"
    "app_modular.py"
    "app_new.py"
    "app_simple_test.py"
    "server.log"
    "server_env.log"
    "server_error_handler.log"
    "server_final.log"
    "server_new.log"
    "server_rate_limited.log"
    "test_core_functions.py"
    "test_error_handling.py"
    "test_logging.py"
    "test_modules.py"
    "test_sunset_algorithm.py"
    "test_app.log"
)

# 統計
TOTAL=0
REMOVED=0
FAILED=0

for file in "${FILES_TO_REMOVE[@]}"; do
    TOTAL=$((TOTAL + 1))
    if [ -f "$file" ]; then
        SIZE=$(du -h "$file" | cut -f1)
        echo "🗑️  刪除: $file ($SIZE)"
        rm "$file"
        if [ $? -eq 0 ]; then
            REMOVED=$((REMOVED + 1))
        else
            FAILED=$((FAILED + 1))
            echo "   ❌ 刪除失敗"
        fi
    else
        echo "⏭️  跳過: $file (不存在)"
    fi
done

echo ""
echo "======================================"
echo "📊 清理統計:"
echo "   總計: $TOTAL 個文件"
echo "   已刪除: $REMOVED 個"
echo "   失敗: $FAILED 個"
echo "   跳過: $((TOTAL - REMOVED - FAILED)) 個"
echo "======================================"
echo "✅ 清理完成"
