# Google Search Console 設置指南

## 📋 步驟 1: 驗證網站所有權

1. 前往 [Google Search Console](https://search.google.com/search-console/)
2. 點擊「新增資源」
3. 選擇「網址前置字元」
4. 輸入: `https://burnsky-api.onrender.com`
5. 選擇驗證方法：

### 方法 A: HTML 檔案上傳
- 下載 Google 提供的 HTML 驗證檔案
- 將檔案放到網站根目錄
- 我們的網站已支援動態驗證路由: `/google<verification_code>.html`

### 方法 B: HTML 標籤 (推薦)
我們的網站已在 `<head>` 中包含:
```html
<meta name="google-site-verification" content="YOUR_GOOGLE_VERIFICATION_CODE">
```
將 Google 提供的驗證碼替換 `YOUR_GOOGLE_VERIFICATION_CODE`

## 📋 步驟 2: 提交 Sitemap

1. 在 Search Console 中，選擇已驗證的網站
2. 前往「Sitemaps」頁面
3. 提交 sitemap URL: `https://burnsky-api.onrender.com/sitemap.xml`

我們的 sitemap.xml 包含:
- 主頁 (/)
- 私隱政策 (/privacy)
- 使用條款 (/terms)
- API 文檔 (/api)

## 📋 步驟 3: 設置 Google Analytics

1. 前往 [Google Analytics](https://analytics.google.com/)
2. 創建新的媒體資源
3. 選擇「網站」
4. 輸入網站資訊:
   - 網站名稱: "BurnSky 燒天預測系統"
   - 網站 URL: https://burnsky-api.onrender.com
   - 行業類別: "科學與教育"
   - 時區: "香港"

5. 獲取追蹤 ID (GA4 或 Universal Analytics)
6. 將追蹤代碼添加到網站 `<head>` 中

### GA4 追蹤代碼範例:
```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## 📋 步驟 4: 設置 Google AdSense (可選)

我們的網站已準備好 AdSense:
- ✅ ads.txt 文件: `/ads.txt`
- ✅ 私隱政策: `/privacy`
- ✅ 使用條款: `/terms`
- ✅ 優質內容和用戶體驗

1. 前往 [Google AdSense](https://www.google.com/adsense/)
2. 添加網站: `https://burnsky-api.onrender.com`
3. 等待審核 (通常需要 24-48 小時)

## 📊 SEO 優化完成清單

### ✅ 已完成
- [x] HTML5 語義化標籤 (header, main, nav, section, footer)
- [x] 完整的 meta 標籤 (title, description, keywords)
- [x] Open Graph 標籤 (Facebook, LinkedIn)
- [x] Twitter Card 標籤
- [x] 結構化數據 (JSON-LD, Schema.org)
- [x] Canonical URLs
- [x] robots.txt 文件
- [x] sitemap.xml 文件
- [x] 響應式設計 (移動端友好)
- [x] 無障礙設計 (ARIA labels)
- [x] 多語言支援 (zh-TW)
- [x] AdSense 準備

### 🔄 進行中
- [ ] Google Search Console 驗證
- [ ] Sitemap 提交
- [ ] Google Analytics 設置

### 📈 建議下一步
1. **內容 SEO**:
   - 撰寫關於燒天攝影的教學文章
   - 創建香港熱門拍攝地點指南
   - 添加天氣知識科普內容

2. **技術優化**:
   - 優化圖片 ALT 標籤
   - 實施圖片懶加載
   - 增加頁面載入速度優化

3. **連結建設**:
   - 增加內部連結
   - 聯繫攝影相關網站進行友情連結
   - 在社交媒體分享內容

4. **監控與分析**:
   - 設置 Google Search Console 監控
   - 定期檢查 SEO 表現
   - 分析用戶行為數據

## 🎯 SEO 目標

短期目標 (1-3 個月):
- 在 Google 搜尋 "香港燒天預測" 排名前 10
- 有機流量達到每月 1000+ 次訪問
- 搜尋引擎收錄所有主要頁面

長期目標 (6-12 個月):
- 在 "燒天預測"、"火燒雲預測" 等關鍵詞排名前 3
- 成為香港攝影社群的權威資源
- 有機流量達到每月 5000+ 次訪問

## 📞 聯繫與支援

如需協助設置或有任何問題，請聯繫:
- 技術支援: 通過 GitHub Issues
- 網站反饋: 通過網站聯繫表單
- SEO 諮詢: 歡迎提出改進建議
