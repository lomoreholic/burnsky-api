#!/bin/bash
# 🔥 Burnsky API - 快速 AdSense ads.txt 檢查

echo "🔍 檢查 AdSense ads.txt 狀態..."
echo "================================"

# 檢查線上 ads.txt
echo "📡 線上檢查:"
curl -s -I https://burnsky-api.onrender.com/ads.txt | head -1
echo "📄 內容:"
curl -s https://burnsky-api.onrender.com/ads.txt
echo ""

# 檢查本地文件
echo "💻 本地檢查:"
if [ -f "static/ads.txt" ]; then
    echo "✅ 本地 ads.txt 文件存在"
    echo "📄 內容:"
    cat static/ads.txt
else
    echo "❌ 本地 ads.txt 文件不存在"
fi

echo ""
echo "🎯 如果看到 'google.com, ca-pub-3552699426860096, DIRECT, f08c47fec0942fa0'"
echo "   表示設置正確 ✅"
echo ""
echo "⏰ Google 通常需要 24-48 小時更新 AdSense 狀態"
