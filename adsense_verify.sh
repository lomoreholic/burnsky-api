#!/bin/bash

# 燒天預測系統 - Google AdSense 驗證設置腳本
# 用於設置 Google AdSense 網站所有權驗證

echo "🔥 燒天預測系統 - AdSense 驗證設置"
echo "================================="
echo ""

# 檢查網站是否正常運行
echo "🔍 檢查網站狀態..."
SITE_URL="https://burnsky-api.onrender.com"

if curl -f -s "$SITE_URL/test" > /dev/null; then
    echo "✅ 網站正常運行: $SITE_URL"
else
    echo "❌ 網站無法訪問，請先確保網站正常運行"
    exit 1
fi

echo ""
echo "📋 AdSense 驗證方法選擇："
echo "1. HTML Meta Tag 驗證 (推薦)"
echo "2. HTML 文件驗證"
echo "3. 檢查當前驗證狀態"
echo ""

read -p "請選擇驗證方法 (1-3): " method

case $method in
    1)
        echo ""
        echo "🔧 HTML Meta Tag 驗證設置"
        echo "========================"
        echo ""
        echo "您需要在 Google AdSense 中："
        echo "1. 添加網站: $SITE_URL"
        echo "2. 選擇 'HTML Meta Tag' 驗證方法"
        echo "3. 複製提供的 meta tag"
        echo ""
        
        read -p "📋 請輸入您的 AdSense 發布商 ID (格式: ca-pub-XXXXXXXXXXXXXXXX): " publisher_id
        
        if [[ $publisher_id =~ ^ca-pub-[0-9]{16}$ ]]; then
            echo "✅ 發布商 ID 格式正確: $publisher_id"
            echo ""
            echo "🔧 正在更新網站配置..."
            
            # 這裡您需要手動更新 templates/index.html 中的 meta tag
            echo "請手動更新以下文件中的 AdSense meta tag:"
            echo "文件: templates/index.html"
            echo "將 content=\"ca-pub-XXXXXXXXXXXXXXXX\" 替換為 content=\"$publisher_id\""
            echo ""
            echo "或者運行以下命令自動更新:"
            echo "sed -i '' 's/ca-pub-XXXXXXXXXXXXXXXX/$publisher_id/g' templates/index.html"
            
        else
            echo "❌ 發布商 ID 格式不正確，應該是 ca-pub-XXXXXXXXXXXXXXXX 格式"
            exit 1
        fi
        ;;
        
    2)
        echo ""
        echo "🔧 HTML 文件驗證設置"
        echo "==================="
        echo ""
        echo "您需要在 Google AdSense 中："
        echo "1. 添加網站: $SITE_URL"
        echo "2. 選擇 'HTML 文件' 驗證方法"
        echo "3. 複製提供的驗證文件名"
        echo ""
        
        read -p "📋 請輸入驗證文件名 (格式: googleXXXXXXXXXXXXXXXX.html): " verification_file
        
        if [[ $verification_file =~ ^google[a-fA-F0-9]+\.html$ ]]; then
            echo "✅ 驗證文件名格式正確: $verification_file"
            echo ""
            echo "🔧 測試驗證 URL..."
            
            # 提取驗證碼
            verification_code=${verification_file#google}
            verification_code=${verification_code%.html}
            
            # 測試動態路由
            test_url="$SITE_URL/google$verification_code.html"
            echo "測試 URL: $test_url"
            
            if curl -f -s "$test_url" > /dev/null; then
                echo "✅ 驗證文件 URL 可以訪問"
                echo "🎉 您可以在 AdSense 中完成驗證了！"
            else
                echo "❌ 驗證文件 URL 無法訪問，請檢查部署"
            fi
            
        else
            echo "❌ 驗證文件名格式不正確，應該是 googleXXXXXXXXXXXXXXXX.html 格式"
            exit 1
        fi
        ;;
        
    3)
        echo ""
        echo "🔍 檢查當前驗證狀態"
        echo "=================="
        echo ""
        
        echo "📊 檢查 ads.txt 文件..."
        if curl -f -s "$SITE_URL/ads.txt" > /dev/null; then
            echo "✅ ads.txt 文件可訪問: $SITE_URL/ads.txt"
            echo "內容預覽:"
            curl -s "$SITE_URL/ads.txt" | head -3
        else
            echo "❌ ads.txt 文件無法訪問"
        fi
        
        echo ""
        echo "📊 檢查 AdSense 狀態頁面..."
        if curl -f -s "$SITE_URL/adsense" > /dev/null; then
            echo "✅ AdSense 狀態頁面可訪問: $SITE_URL/adsense"
        else
            echo "❌ AdSense 狀態頁面無法訪問"
        fi
        
        echo ""
        echo "📊 檢查隱私政策..."
        if curl -f -s "$SITE_URL/privacy" > /dev/null; then
            echo "✅ 隱私政策頁面可訪問: $SITE_URL/privacy"
        else
            echo "❌ 隱私政策頁面無法訪問"
        fi
        
        echo ""
        echo "📊 檢查使用條款..."
        if curl -f -s "$SITE_URL/terms" > /dev/null; then
            echo "✅ 使用條款頁面可訪問: $SITE_URL/terms"
        else
            echo "❌ 使用條款頁面無法訪問"
        fi
        ;;
        
    *)
        echo "❌ 無效選擇"
        exit 1
        ;;
esac

echo ""
echo "🎉 AdSense 驗證設置完成！"
echo ""
echo "📋 下一步驟："
echo "1. 前往 Google AdSense: https://www.google.com/adsense/"
echo "2. 添加您的網站: $SITE_URL"
echo "3. 選擇對應的驗證方法"
echo "4. 完成驗證後等待審核"
echo ""
echo "📚 更多資訊: cat GOOGLE_ADS_SETUP_GUIDE.md"
