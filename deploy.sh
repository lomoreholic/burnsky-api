#!/bin/bash

# 燒天預測系統 - 快速部署腳本
# 此腳本會指導你完成從本地到生產環境的完整部署流程

echo "🔥 燒天預測系統 - 快速部署腳本 🔥"
echo "=================================="
echo ""

# 步驟 1: 檢查 git 狀態
echo "📋 步驟 1: 檢查 git 狀態..."
git status

echo ""
echo "✅ 如果有未提交的變更，請先運行："
echo "   git add . && git commit -m \"Update before deployment\""
echo ""

# 提示用戶設定 GitHub repository
echo "📋 步驟 2: 設定 GitHub Repository"
echo "================================"
echo "請按照以下步驟操作："
echo ""
echo "1. 前往 https://github.com"
echo "2. 點擊右上角 '+' 按鈕，選擇 'New repository'"
echo "3. Repository 設定："
echo "   - Name: burnsky-api"
echo "   - Description: 香港燒天預測系統 - 基於香港天文台數據的智能天氣預測 API"
echo "   - Visibility: Public"
echo "   - 不要勾選任何額外選項"
echo "4. 點擊 'Create repository'"
echo ""

read -p "✋ 按 Enter 繼續（當你完成 GitHub repository 創建後）..."

echo ""
echo "📋 步驟 3: 連接並推送到 GitHub"
echo "============================="
echo "請輸入你的 GitHub 用戶名："
read -p "GitHub 用戶名: " github_username

if [ -z "$github_username" ]; then
    echo "❌ 用戶名不能為空！"
    exit 1
fi

echo ""
echo "🔗 正在連接 GitHub repository..."

# 添加遠程 repository
git remote add origin https://github.com/$github_username/burnsky-api.git

echo "📤 正在推送代碼到 GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ 代碼已成功推送到 GitHub！"
    echo ""
    echo "🌐 GitHub Repository URL: https://github.com/$github_username/burnsky-api"
else
    echo "❌ 推送失敗！請檢查："
    echo "   1. GitHub 用戶名是否正確"
    echo "   2. 是否已登入 GitHub（可能需要設定 Personal Access Token）"
    echo "   3. Repository 是否已正確創建"
    exit 1
fi

echo ""
echo "📋 步驟 4: 部署到 Render.com"
echo "========================="
echo "現在請按照以下步驟在 Render.com 部署："
echo ""
echo "1. 前往 https://render.com"
echo "2. 註冊/登入帳號"
echo "3. 點擊 'New +' 按鈕"
echo "4. 選擇 'Web Service'"
echo "5. 連接你的 GitHub 帳號"
echo "6. 選擇 '$github_username/burnsky-api' repository"
echo "7. 配置設定："
echo "   - Name: burnsky-api"
echo "   - Environment: Python 3"
echo "   - Build Command: pip install -r requirements.txt"
echo "   - Start Command: gunicorn app:app --bind 0.0.0.0:\$PORT"
echo "   - Plan: Free"
echo "8. 點擊 'Create Web Service'"
echo ""

read -p "✋ 按 Enter 繼續（當你完成 Render.com 部署後）..."

echo ""
echo "📋 步驟 5: 測試部署"
echo "================"
echo "請輸入你的 Render.com 應用網址："
echo "（通常格式為: https://your-app-name.onrender.com）"
read -p "應用網址: " app_url

if [ -z "$app_url" ]; then
    echo "❌ 網址不能為空！"
    echo "📝 你可以稍後運行測試腳本："
    echo "   python test_deployment.py YOUR_APP_URL"
else
    echo ""
    echo "🧪 正在測試部署..."
    python test_deployment.py "$app_url"
fi

echo ""
echo "🎉 部署完成！"
echo "============"
echo "📱 你的燒天預測系統現在可以在以下網址訪問："
echo "   $app_url"
echo ""
echo "📊 下一步："
echo "   1. 在手機上測試應用"
echo "   2. 分享給朋友試用"
echo "   3. 收集用戶反饋"
echo "   4. 考慮購買自定義域名"
echo "   5. 啟動移動應用開發計劃"
echo ""
echo "🚀 恭喜！你已成功將燒天預測系統部署到生產環境！"
