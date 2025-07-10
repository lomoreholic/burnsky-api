# 🔥 燒天預測系統 - Google AdSense 設置指南

## 📋 概述
本指南將幫助您完成 Google AdSense 的申請和網站驗證過程。

## 🚀 網站資訊
- **網站 URL**: https://burnsky-api.onrender.com
- **網站類型**: 天氣預測服務
- **主要功能**: 香港燒天（火燒雲）機率預測
- **目標用戶**: 香港市民和攝影愛好者

## 📝 AdSense 申請前準備

### ✅ 已完成項目
1. **網站內容**: ✅ 原創天氣預測服務
2. **隱私政策**: ✅ 已設置 `/privacy`
3. **使用條款**: ✅ 已設置 `/terms`
4. **ads.txt 文件**: ✅ 已設置 `/ads.txt`
5. **網站驗證路由**: ✅ 支援動態 Google 驗證
6. **AdSense meta tag**: ✅ 已在模板中準備

### ⏳ 需要完成的項目
1. **發布商 ID**: 需要從 AdSense 獲取
2. **網站驗證**: 需要在 AdSense 後台完成
3. **廣告位置規劃**: 需要決定廣告顯示位置

## 🔧 驗證方法

### 方法 1: HTML Meta Tag 驗證 (推薦)

#### 🔧 方法 A 設置（推薦）
1. 複製 Google 提供的 meta tag
2. 運行設置腳本：
```bash
./setup_adsense.sh "ca-pub-您的發布商ID"
```

#### 🔧 方法 B 設置
1. 從 Google AdSense 下載驗證文件
2. 將文件放在項目根目錄
3. 運行：
```bash
./setup_adsense.sh verification "google1234567890abcdef.html"
```

### 3. 部署並驗證

1. 推送更新到服務器：
```bash
./update.sh
```

2. 等待部署完成（3-5分鐘）

3. 測試驗證URL：
   - Meta tag 方法：直接檢查 https://burnsky-api.onrender.com
   - 文件方法：檢查 https://burnsky-api.onrender.com/google您的驗證碼.html

4. 回到 Google AdSense 點擊「驗證」

### 4. 驗證成功後的設置

#### ads.txt 文件
我們已經為您準備了 ads.txt 路由：
- URL: https://burnsky-api.onrender.com/ads.txt
- 內容會自動包含您的發布商 ID

#### SEO 優化
我們也準備了：
- robots.txt: https://burnsky-api.onrender.com/robots.txt
- sitemap.xml: https://burnsky-api.onrender.com/sitemap.xml

## 🚨 重要注意事項

1. **發布商 ID 格式**：必須是 `ca-pub-` 開頭的16位數字
2. **驗證時間**：Google 通常需要幾分鐘到幾小時來驗證
3. **網站內容**：確保您的網站有足夠的原創內容
4. **隱私政策**：AdSense 要求有隱私政策頁面（我們已準備）

## 🎯 下一步

驗證成功後：
1. 等待 Google 審核您的網站（通常需要1-14天）
2. 審核通過後，您就可以開始在網站上顯示廣告
3. 可以使用我們預留的廣告位置

---

## 📞 需要幫助？
如果遇到問題，請檢查：
1. 網站是否正常運行
2. 驗證碼是否正確複製
3. 是否等待足夠的時間讓更改生效

*最後更新: 2025年7月10日*
