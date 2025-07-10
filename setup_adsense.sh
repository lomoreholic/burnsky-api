#!/bin/bash

# 燒天預測系統 - Google AdSense 整合腳本
# 用於在 AdSense 審核通過後快速整合廣告代碼

echo "🎯 燒天預測系統 - Google AdSense 整合工具"
echo "========================================="
echo ""

# 檢查是否提供了 Publisher ID
if [ $# -eq 0 ]; then
    echo "📋 使用方法："
    echo "   $0 <YOUR_PUBLISHER_ID>"
    echo ""
    echo "例如："
    echo "   $0 ca-pub-1234567890123456"
    echo ""
    echo "💡 提示："
    echo "   1. 先申請 Google AdSense 並獲得審核通過"
    echo "   2. 在 AdSense 後台獲取您的 Publisher ID"
    echo "   3. 運行此腳本來自動整合廣告代碼"
    exit 1
fi

PUBLISHER_ID=$1

echo "🔧 準備整合 AdSense..."
echo "Publisher ID: $PUBLISHER_ID"
echo ""

# 備份原始檔案
echo "📦 備份原始檔案..."
cp templates/index.html templates/index.html.backup
echo "✅ 已備份為 templates/index.html.backup"
echo ""

# 在 <head> 中添加 AdSense 代碼
echo "🎯 添加 AdSense 自動廣告代碼..."

# 創建臨時檔案
cat > /tmp/adsense_head.html << EOF
    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=$PUBLISHER_ID"
         crossorigin="anonymous"></script>
    <meta name="google-adsense-account" content="$PUBLISHER_ID">
EOF

# 在 </head> 前插入 AdSense 代碼
sed -i.tmp '/<\/head>/i\
    <!-- Google AdSense -->\
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client='$PUBLISHER_ID'"\
         crossorigin="anonymous"></script>\
    <meta name="google-adsense-account" content="'$PUBLISHER_ID'">' templates/index.html

# 清理臨時檔案
rm templates/index.html.tmp

echo "✅ AdSense 代碼已添加到 <head> 部分"
echo ""

# 替換廣告位置佔位符
echo "🎨 設置廣告位置..."

# 頂部廣告
cat > /tmp/top_ad.html << EOF
        <!-- 頂部橫幅廣告 -->
        <div id="top-ad" style="text-align: center; margin: 20px 0;">
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="$PUBLISHER_ID"
                 data-ad-slot="1234567890"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
EOF

# 替換頂部廣告佔位符
sed -i.tmp '/<!-- 頂部廣告位置 -->/,/div>/c\
        <!-- 頂部橫幅廣告 -->\
        <div id="top-ad" style="text-align: center; margin: 20px 0;">\
            <ins class="adsbygoogle"\
                 style="display:block"\
                 data-ad-client="'$PUBLISHER_ID'"\
                 data-ad-slot="1234567890"\
                 data-ad-format="auto"\
                 data-full-width-responsive="true"></ins>\
            <script>\
                 (adsbygoogle = window.adsbygoogle || []).push({});\
            </script>\
        </div>' templates/index.html

rm templates/index.html.tmp

echo "✅ 頂部廣告位置已設置"
echo ""

# 添加底部廣告
echo "📱 添加底部廣告..."

# 在免責聲明前添加底部廣告
sed -i.tmp '/免責聲明測試/i\
            <!-- 底部廣告 -->\
            <div style="text-align: center; margin: 30px 0;">\
                <ins class="adsbygoogle"\
                     style="display:block"\
                     data-ad-client="'$PUBLISHER_ID'"\
                     data-ad-slot="0987654321"\
                     data-ad-format="auto"\
                     data-full-width-responsive="true"></ins>\
                <script>\
                     (adsbygoogle = window.adsbygoogle || []).push({});\
                </script>\
            </div>' templates/index.html

rm templates/index.html.tmp

echo "✅ 底部廣告位置已設置"
echo ""

# 更新隱私政策
echo "📋 更新隱私政策..."
sed -i.tmp 's/privacy@burnsky.app/privacy@burnsky.app/g' templates/privacy.html
rm templates/privacy.html.tmp

echo "✅ 隱私政策已更新"
echo ""

echo "🎉 AdSense 整合完成！"
echo ""
echo "📝 下一步："
echo "   1. 在 AdSense 後台創建廣告單元並獲取正確的 data-ad-slot 值"
echo "   2. 替換模板中的 '1234567890' 和 '0987654321' 為實際的廣告單元 ID"
echo "   3. 測試廣告顯示效果"
echo "   4. 提交更新: ./update.sh"
echo ""
echo "💡 重要提醒："
echo "   - 不要點擊自己的廣告"
echo "   - 確保網站內容符合 AdSense 政策"
echo "   - 監控廣告效果和收益"
echo ""
echo "🔄 如需恢復原始版本："
echo "   cp templates/index.html.backup templates/index.html"

# 清理臨時檔案
rm -f /tmp/adsense_head.html /tmp/top_ad.html
