# 🗺️ Google Search Console Sitemap 提交指南

## 📋 Sitemap 基本資訊

**Sitemap URL**: `https://burnsky-api.onrender.com/sitemap.xml`  
**更新日期**: 2025年7月17日  
**總頁面數**: 11個主要頁面  
**格式**: XML (符合 sitemaps.org 標準)

## 🎯 包含的頁面與優先級

### 🔥 最高優先級 (Priority: 1.0)
- **主頁**: `/` - 燒天預測系統首頁
  - 更新頻率: 每日
  - 描述: 系統主要入口，包含最新燒天預測

### 📊 核心功能 (Priority: 0.8-0.9)
- **預測API**: `/predict` - 通用預測端點 (0.9)
- **日落預測**: `/predict/sunset` - 日落燒天預測 (0.8)  
- **日出預測**: `/predict/sunrise` - 日出燒天預測 (0.8)
  - 更新頻率: 每小時
  - 描述: 系統核心功能，實時天氣數據分析

### 📝 資訊頁面 (Priority: 0.4-0.6)
- **API資訊**: `/api` - API說明文檔 (0.6)
- **系統狀態**: `/status` - 服務狀態監控 (0.4)
- **健康檢查**: `/health` - 系統健康度 (0.3)

### 📄 法律頁面 (Priority: 0.5)
- **隱私政策**: `/privacy` - 用戶隱私保護
- **使用條款**: `/terms` - 服務使用條款
  - 更新頻率: 每月

### 🔧 技術文件 (Priority: 0.1-0.2)
- **廣告配置**: `/ads.txt` - AdSense設定
- **爬蟲規則**: `/robots.txt` - 搜索引擎指令

## 📋 Google Search Console 提交步驟

### 1. 登入 Google Search Console
1. 前往 [Google Search Console](https://search.google.com/search-console/)
2. 使用您的Google帳戶登入
3. 選擇「燒天預測系統」資源

### 2. 驗證網站所有權
1. 在左側選單找到「設定」→「擁有者驗證」
2. 確認HTML標籤驗證方式已啟用
3. 驗證碼：`8nMW3lXIw2vxGw9fqBBcJV27fZQBPLjKnKVZyVVFzJs`

### 3. 提交 Sitemap
1. 在左側選單選擇「索引」→「Sitemap」
2. 點擊「新增Sitemap」
3. 輸入sitemap URL：`sitemap.xml`
4. 點擊「提交」

### 4. 監控索引狀態
1. 等待Google處理（通常需要幾小時到幾天）
2. 在「Sitemap」頁面查看處理狀態
3. 檢查「涵蓋範圍」報告確認頁面被正確索引

## ✅ Sitemap 技術規格

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
```

### 📊 更新頻率說明
- **hourly**: 預測功能（每小時更新天氣數據）
- **daily**: 主頁和狀態頁面（每日內容更新）
- **weekly**: API文檔（功能穩定，偶爾更新）
- **monthly**: 法律頁面（條款政策調整）
- **yearly**: 技術配置文件（很少變動）

### 🎯 優先級說明
- **1.0**: 網站最重要頁面（主頁）
- **0.8-0.9**: 核心功能頁面（預測系統）
- **0.5-0.6**: 重要但非核心頁面（法律、文檔）
- **0.1-0.4**: 技術和輔助頁面

## 🚀 SEO 優化建議

### 1. 定期更新
- Sitemap每月至少更新一次
- 新增功能時記得加入sitemap
- 保持lastmod日期準確

### 2. 監控指標
- **索引涵蓋率**: 目標>90%
- **爬取頻率**: 監控預測頁面爬取
- **錯誤修復**: 及時處理404和重複內容

### 3. 內容優化
- 確保每個頁面有獨特的title和description
- 提供高質量、原創的燒天預測內容
- 保持網站結構清晰和導航友好

## 📞 技術支援

如果在提交過程中遇到問題：

1. **Sitemap格式錯誤**: 檢查XML語法是否正確
2. **頁面無法訪問**: 確認所有URL都能正常載入
3. **索引延遲**: Google通常需要幾天時間處理
4. **驗證失敗**: 確認HTML驗證標籤是否正確安裝

## 📈 預期結果

提交sitemap後，您應該看到：
- ✅ 燒天預測系統在Google搜索結果中顯示
- ✅ 核心關鍵字（燒天預測、火燒雲、香港天氣）排名提升
- ✅ 網站流量和用戶發現度增加
- ✅ 搜索引擎對網站內容的理解改善

---

**更新日期**: 2025年7月17日  
**Sitemap狀態**: ✅ 已生成並部署到生產環境  
**下次更新**: 建議每月檢查和更新
