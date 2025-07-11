#!/bin/bash

# 燒天預測系統 - 快速更新腳本
# 用於快速推送更新到生產環境

echo "🔄 燒天預測系統 - 快速更新工具"
echo "=============================="
echo ""

# 檢查是否有未提交的變更
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 發現未提交的變更："
    git status --short
    echo ""
    
    read -p "📋 請輸入提交訊息: " commit_message
    
    if [ -z "$commit_message" ]; then
        echo "❌ 提交訊息不能為空！"
        exit 1
    fi
    
    echo "📦 正在提交變更..."
    git add .
    git commit -m "$commit_message"
    
    if [ $? -ne 0 ]; then
        echo "❌ 提交失敗！"
        exit 1
    fi
else
    echo "✅ 沒有需要提交的變更"
fi

echo ""
echo "🚀 正在推送到 GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ 成功推送到 GitHub！"
    echo ""
    echo "⏳ Render.com 正在自動部署更新..."
    echo "   預計需要 3-5 分鐘完成部署"
    echo ""
    echo "🔗 你可以在以下網址查看部署狀態："
    echo "   https://dashboard.render.com/"
    echo ""
    
    read -p "🧪 是否要等待部署完成並測試？(y/n): " test_after_deploy
    
    if [ "$test_after_deploy" = "y" ] || [ "$test_after_deploy" = "Y" ]; then
        echo ""
        echo "⏳ 等待部署完成..."
        echo "   (通常需要 3-5 分鐘)"
        
        read -p "📱 請輸入你的應用網址 (留空使用預設): " app_url
        
        if [ -z "$app_url" ]; then
            app_url="https://burnsky-api.onrender.com"
            echo "🔗 使用預設網址: $app_url"
        fi
        
        echo ""
        echo "🧪 正在測試更新後的應用..."
        python test_deployment.py "$app_url"
    fi
    
    echo ""
    echo "🎉 更新完成！"
    echo "📱 你的燒天預測系統已自動更新"
    echo ""
    echo "🔍 如果網站仍然無法載入，請檢查："
    echo "   1. Render Dashboard: https://dashboard.render.com/"
    echo "   2. 等待 3-5 分鐘讓部署完成"
    echo "   3. 檢查部署日誌是否有錯誤"
    echo "   4. 確認服務狀態為 'Live'"
    echo "   5. 確認服務 URL 正確"
    echo ""
    echo "💡 防止網站休眠 (Render 免費方案30分鐘會自動暫停):"
    echo "   🛠️  啟動保活服務: ./keep_alive.sh &"
    echo "   📖 詳細指南: cat WEBSITE_UPTIME_GUIDE.md"
    echo ""
    echo "📖 其他指南:"
    echo "   • 故障排除: cat RENDER_TROUBLESHOOTING.md"
    echo "   • 診斷工具: python diagnose.py [您的實際URL]"
    echo "   • AdSense 設置: cat ADSENSE_READY.md"
    
else
    echo "❌ 推送失敗！請檢查："
    echo "   1. 網路連接是否正常"
    echo "   2. GitHub 認證是否有效"
    echo "   3. Repository 權限是否正確"
    echo ""
    echo "🔧 常見解決方案："
    echo "   • 重新設定 GitHub 認證: git config --global user.email 'your-email@example.com'"
    echo "   • 檢查遠端 URL: git remote -v"
    echo "   • 強制推送 (小心使用): git push --force-with-lease origin main"
fi
