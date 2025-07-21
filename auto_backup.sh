#!/bin/bash

# 警告歷史數據自動備份腳本
# 使用方法: ./auto_backup.sh [daily|hourly|manual]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKUP_TYPE=${1:-manual}
LOG_FILE="backup.log"

# 記錄日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 執行備份
execute_backup() {
    log "開始執行 $BACKUP_TYPE 備份..."
    
    # 執行 Python 備份腳本
    python3 github_data_backup.py 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        log "✅ $BACKUP_TYPE 備份完成"
    else
        log "❌ $BACKUP_TYPE 備份失敗"
    fi
}

# 檢查是否有數據庫文件
if [ ! -f "warning_history.db" ]; then
    log "⚠️ 警告: warning_history.db 文件不存在"
    exit 1
fi

# 檢查 git 狀態
if ! git status &>/dev/null; then
    log "❌ 錯誤: 不在 git 倉庫中"
    exit 1
fi

case $BACKUP_TYPE in
    "daily")
        log "執行每日備份"
        execute_backup
        ;;
    "hourly")
        log "執行每小時備份"
        execute_backup
        ;;
    "manual")
        log "執行手動備份"
        execute_backup
        ;;
    *)
        log "❌ 無效的備份類型: $BACKUP_TYPE"
        echo "使用方法: $0 [daily|hourly|manual]"
        exit 1
        ;;
esac
