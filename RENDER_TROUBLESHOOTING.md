# 🔥 燒天預測系統 - Render 故障排除指南

## 📋 檢查清單

### 1. 檢查 Render Dashboard
1. 前往 [Render Dashboard](https://dashboard.render.com/)
2. 登入您的帳戶
3. 查看您的服務列表

### 2. 服務狀態檢查
- ✅ **Live**: 服務正常運行
- 🔄 **Building**: 正在部署中
- ⏸️ **Suspended**: 服務已暫停（免費方案30分鐘無活動會自動暫停）
- ❌ **Failed**: 部署失敗

### 3. 常見問題及解決方案

#### 問題 A: 服務被暫停 (Suspended)
**解決方案**: 
- 點擊服務名稱
- 點擊 "Resume Service" 按鈕
- 等待 3-5 分鐘讓服務重新啟動

#### 問題 B: 部署失敗 (Failed)
**解決方案**:
1. 檢查部署日誌:
   - 點擊服務名稱 → Events 標籤
   - 查看錯誤訊息
2. 常見錯誤:
   - 缺少依賴包: 檢查 `requirements.txt`
   - Python 版本不兼容: 檢查 `runtime.txt`
   - 代碼語法錯誤: 檢查最新的 commit

#### 問題 C: 服務不存在
**解決方案**: 重新創建服務
1. 點擊 "New +" → "Web Service"
2. 連接您的 GitHub repository
3. 配置設置:
   - **Name**: `burnsky-api`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Plan**: Free

### 4. 檢查正確的服務 URL
您的實際服務 URL 可能是:
- `https://burnsky-api.onrender.com`
- `https://[你的服務名稱].onrender.com`

在 Render Dashboard 中，您可以在服務頁面的頂部找到正確的 URL。

### 5. 重新部署步驟
1. 在 Render Dashboard 中找到您的服務
2. 點擊 "Manual Deploy" → "Deploy latest commit"
3. 等待部署完成（通常需要 3-5 分鐘）

### 6. 驗證部署
使用我們的診斷工具:
```bash
python diagnose.py https://[您的實際URL].onrender.com
```

## 🚨 緊急情況：完全重新部署

如果以上步驟都無效，請按照以下步驟完全重新部署:

1. **備份代碼** (已經在 GitHub 上)
2. **刪除現有服務** (在 Render Dashboard)
3. **重新創建服務**:
   - 連接 GitHub repository: `lomoreholic/burnsky-api`
   - 使用上述配置設置

## 📞 需要幫助？
如果問題持續存在，請檢查:
1. Render 服務狀態頁面
2. GitHub repository 是否正確連接
3. 最新的 commit 是否包含所有必要文件

---
*最後更新: 2025年7月10日*
