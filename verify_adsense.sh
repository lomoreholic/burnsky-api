#!/bin/bash

# 燒天預測系統 - Google AdSense 網站驗證腳本
# 用於 AdSense 申請時的網站所有權驗證

echo "🔐 燒天預測系統 - AdSense 網站驗證工具"
echo "======================================="
echo ""

# 顯示幫助信息
show_help() {
    echo "📋 使用方法："
    echo ""
    echo "1. Meta Tag 驗證："
    echo "   $0 meta ca-pub-1234567890123456"
    echo ""
    echo "2. HTML 文件驗證："
    echo "   $0 file google1234567890abcdef.html"
    echo ""
    echo "3. 查看當前狀態："
    echo "   $0 status"
    echo ""
    echo "💡 從 Google AdSense 獲取驗證信息："
    echo "   1. 登入 AdSense 控制台"
    echo "   2. 點擊 '新增網站'"
    echo "   3. 輸入網址: https://burnsky-api.onrender.com"
    echo "   4. 選擇驗證方法並複製驗證碼"
}

# 檢查參數
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

METHOD=$1

case $METHOD in
    "meta")
        if [ $# -ne 2 ]; then
            echo "❌ 錯誤：請提供 Publisher ID"
            echo "例如：$0 meta ca-pub-1234567890123456"
            exit 1
        fi
        
        PUBLISHER_ID=$2
        
        # 驗證 Publisher ID 格式
        if [[ ! $PUBLISHER_ID =~ ^ca-pub-[0-9]{16}$ ]]; then
            echo "❌ 錯誤：Publisher ID 格式不正確"
            echo "正確格式：ca-pub- 後接16位數字"
            echo "例如：ca-pub-1234567890123456"
            exit 1
        fi
        
        echo "🔧 設置 Meta Tag 驗證..."
        echo "Publisher ID: $PUBLISHER_ID"
        echo ""
        
        # 備份現有文件
        cp templates/index.html templates/index.html.backup
        echo "📦 已備份原始文件"
        
        # 更新 Meta Tag
        sed -i.tmp "s/ca-pub-XXXXXXXXXXXXXXXX/$PUBLISHER_ID/g" templates/index.html
        rm templates/index.html.tmp
        
        # 更新 ads.txt
        sed -i.tmp "s/ca-pub-XXXXXXXXXXXXXXXX/$PUBLISHER_ID/g" app.py
        rm app.py.tmp
        
        echo "✅ Meta Tag 驗證已設置"
        echo "🔗 驗證 URL: https://burnsky-api.onrender.com"
        ;;
        
    "file")
        if [ $# -ne 2 ]; then
            echo "❌ 錯誤：請提供 HTML 驗證文件名"
            echo "例如：$0 file google1234567890abcdef.html"
            exit 1
        fi
        
        VERIFICATION_FILE=$2
        
        # 驗證文件名格式
        if [[ ! $VERIFICATION_FILE =~ ^google[a-f0-9]+\.html$ ]]; then
            echo "❌ 錯誤：驗證文件名格式不正確"
            echo "正確格式：google 後接16進制字符，以 .html 結尾"
            echo "例如：google1234567890abcdef.html"
            exit 1
        fi
        
        echo "📁 設置 HTML 文件驗證..."
        echo "驗證文件: $VERIFICATION_FILE"
        echo ""
        
        # 從文件名提取驗證碼
        VERIFICATION_CODE=${VERIFICATION_FILE#google}
        VERIFICATION_CODE=${VERIFICATION_CODE%.html}
        
        echo "📝 驗證碼: $VERIFICATION_CODE"
        echo "🔗 驗證 URL: https://burnsky-api.onrender.com/$VERIFICATION_FILE"
        echo ""
        echo "✅ HTML 文件驗證已設置（透過動態路由）"
        ;;
        
    "status")
        echo "📊 當前驗證狀態："
        echo ""
        
        # 檢查 Meta Tag
        if grep -q "ca-pub-[0-9]" templates/index.html; then
            CURRENT_PUB_ID=$(grep -o "ca-pub-[0-9]*" templates/index.html | head -1)
            echo "✅ Meta Tag 驗證: 已設置"
            echo "   Publisher ID: $CURRENT_PUB_ID"
        else
            echo "❌ Meta Tag 驗證: 未設置"
        fi
        
        # 檢查備份文件
        if [ -f "templates/index.html.backup" ]; then
            echo "📦 備份文件: 存在"
        else
            echo "📦 備份文件: 不存在"
        fi
        
        echo ""
        echo "🌐 網站 URL: https://burnsky-api.onrender.com"
        echo "📋 ads.txt: https://burnsky-api.onrender.com/ads.txt"
        echo "🤖 robots.txt: https://burnsky-api.onrender.com/robots.txt"
        ;;
        
    "restore")
        echo "🔄 恢復原始設定..."
        if [ -f "templates/index.html.backup" ]; then
            cp templates/index.html.backup templates/index.html
            echo "✅ 已恢復原始設定"
        else
            echo "❌ 找不到備份文件"
        fi
        ;;
        
    *)
        echo "❌ 未知的方法: $METHOD"
        echo ""
        show_help
        exit 1
        ;;
esac

echo ""
echo "📤 下一步："
echo "1. 運行部署: ./update.sh"
echo "2. 等待部署完成 (3-5 分鐘)"
echo "3. 測試驗證 URL 是否正常"
echo "4. 在 AdSense 控制台點擊 '驗證'"
echo ""
echo "🧪 測試驗證："
echo "python diagnose.py https://burnsky-api.onrender.com"
