#!/bin/bash

# 燒天預測系統 - 網站保活腳本
# 定期 ping 網站以防止 Render 服務休眠

WEBSITE_URL="https://burnsky-api.onrender.com"
PING_INTERVAL=1500  # 25分鐘 (25 * 60 秒)
LOG_FILE="keep_alive.log"

echo "🔥 燒天預測系統保活工具"
echo "======================="
echo "🌐 目標網站: $WEBSITE_URL"
echo "⏰ 檢查間隔: 25 分鐘"
echo "📝 日誌文件: $LOG_FILE"
echo "📋 按 Ctrl+C 停止"
echo ""

# 創建日誌文件
touch "$LOG_FILE"

# 信號處理函數
cleanup() {
    echo ""
    echo "🛑 收到停止信號，正在安全退出..."
    echo "$(date): 保活服務停止" >> "$LOG_FILE"
    exit 0
}

# 註冊信號處理器
trap cleanup SIGINT SIGTERM

# Ping 函數
ping_website() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$timestamp] 🔍 檢查網站狀態..."
    
    # 使用 curl 檢查網站，記錄響應時間
    local response=$(curl -w "時間:%{time_total}s 狀態:%{http_code}" -s -o /dev/null --max-time 60 "$WEBSITE_URL")
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        echo "[$timestamp] ✅ $response" | tee -a "$LOG_FILE"
        
        # 檢查是否是冷啟動（響應時間超過10秒）
        local time_taken=$(echo "$response" | grep -o "時間:[0-9.]*" | cut -d: -f2 | cut -ds -f1)
        if command -v bc >/dev/null 2>&1; then
            if (( $(echo "$time_taken > 10" | bc -l 2>/dev/null || echo 0) )); then
                echo "[$timestamp] 🔄 服務剛從休眠中喚醒" | tee -a "$LOG_FILE"
            fi
        else
            # 如果沒有 bc，使用簡單的字符串比較
            if [[ $(echo "$time_taken" | cut -d. -f1) -gt 10 ]]; then
                echo "[$timestamp] 🔄 服務剛從休眠中喚醒" | tee -a "$LOG_FILE"
            fi
        fi
    else
        echo "[$timestamp] ❌ 網站無法訪問 (錯誤碼: $exit_code)" | tee -a "$LOG_FILE"
    fi
}

# 初始檢查
echo "$(date): 保活服務啟動" >> "$LOG_FILE"
ping_website

# 主循環
while true; do
    echo "⏰ 等待 $((PING_INTERVAL / 60)) 分鐘後下次檢查..."
    sleep $PING_INTERVAL
    ping_website
done
