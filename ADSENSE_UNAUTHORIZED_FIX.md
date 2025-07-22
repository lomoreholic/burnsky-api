# 🚨 AdSense "Unauthorized" 問題解決指南

## 🎯 問題: "You publisher ID wasn't found in the ads.txt file"

### 📋 可能原因分析

1. **Publisher ID 不匹配** (最常見)
   - ads.txt 中的 ID 與您實際的 AdSense 帳戶 ID 不同
   - 解決: 需要使用您真實的 AdSense Publisher ID

2. **網站未在 AdSense 中添加**
   - 您的網站還沒有在 AdSense 帳戶中添加和驗證
   - 解決: 需要在 AdSense 中添加 burnsky-api.onrender.com

3. **AdSense 帳戶未完全設置**
   - AdSense 帳戶還在審核中或未完成設置
   - 解決: 等待帳戶批准或完成必要步驟

### 🔧 立即解決步驟

#### Step 1: 確認您的 Publisher ID
1. 登入 [Google AdSense](https://adsense.google.com)
2. 前往 **帳戶** > **帳戶資訊**
3. 尋找 **發布商 ID** (格式: ca-pub-XXXXXXXXXXXXXXXXX)
4. 複製這個 ID

#### Step 2: 添加網站到 AdSense (如果還沒做)
1. 在 AdSense 中點擊 **網站** > **添加網站**
2. 輸入: `https://burnsky-api.onrender.com`
3. 選擇網站類型和地區
4. 點擊 **繼續**

#### Step 3: 驗證網站所有權
1. 選擇 **HTML Meta Tag** 驗證方式
2. 複製提供的 meta tag 代碼
3. 告訴我這個代碼，我會幫您添加到網站

#### Step 4: 更新 ads.txt
告訴我您的正確 Publisher ID，我會立即更新 ads.txt 文件。

### 📊 當前狀態檢查

```bash
當前 ads.txt 內容:
https://burnsky-api.onrender.com/ads.txt
google.com, ca-pub-3552699426860096, DIRECT, f08c47fec0942fa0
```

**可能問題**: `ca-pub-3552699426860096` 可能不是您實際的 Publisher ID。

### 🎯 需要您提供的資訊

1. **您的真實 AdSense Publisher ID** (從 AdSense 帳戶中複製)
2. **AdSense 帳戶狀態** (已批准/審核中/剛創建)
3. **是否已添加 burnsky-api.onrender.com 到 AdSense**

### 💡 額外提醒

- **不要使用測試或示例 Publisher ID**
- **確保網域名稱完全一致**: burnsky-api.onrender.com
- **等待時間**: 更新後需要 24-48 小時 Google 才會重新檢查

---

**請告訴我您的正確 Publisher ID，我會立即幫您修復！** 🔧
