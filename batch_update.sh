#!/bin/bash

# 新的導航結構
NEW_NAV='        <div class="nav-container">
            <div class="nav-row">
                <a href="/">🏠 首頁</a>
                <a href="/photo-analysis">📸 照片分析</a>
                <a href="/warning-dashboard">⚠️ 警告台</a>
                <a href="/ml-test">🤖 ML測試</a>
            </div>
            <div class="nav-row">
                <a href="/api-docs">📚 API 文檔</a>
                <a href="/photography-guide">📸 攝影指南</a>
                <a href="/best-locations">📍 最佳地點</a>
                <a href="/faq">❓ FAQ</a>
            </div>
            <div class="nav-row">
                <a href="/weather-terms">📚 天氣術語</a>
                <a href="/terms">📄 條款</a>
                <a href="/privacy">🔒 私隱</a>
            </div>
        </div>'

# 要更新的頁面
pages=("faq.html" "weather_terms.html" "terms.html" "ml_test.html")

echo "開始批量更新導航結構..."

for page in "${pages[@]}"; do
    if [ -f "templates/$page" ]; then
        echo "更新 $page..."
        # 這裡手動替換會比較複雜，我們用手動方式
    fi
done
