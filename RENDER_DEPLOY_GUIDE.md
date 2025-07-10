# 🚀 Render.com 快速部署指南

## 📋 準備清單

### ✅ 第一步：GitHub Repository 設置

1. **前往 GitHub.com 創建新 repository**
   - Repository name: `burnsky-predictor`
   - Description: `🔥 香港燒天預測系統 - 千始創意`
   - Public repository (免費)
   - 不要初始化 README (我們已有)

2. **連接本地代碼到 GitHub**
   ```bash
   # 在終端執行以下命令:
   git remote add origin https://github.com/YOUR_USERNAME/burnsky-predictor.git
   git branch -M main
   git push -u origin main
   ```

### ✅ 第二步：Render.com 部署

1. **註冊 Render.com 帳戶**
   - 前往 https://render.com
   - 點擊 "Get Started for Free"
   - 使用 GitHub 帳戶登入

2. **創建 Web Service**
   - 點擊 "New +" → "Web Service"
   - 選擇 "Connect a repository"
   - 找到並選擇 `burnsky-predictor`

3. **配置部署設定**
   ```yaml
   Name: burnsky-predictor
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   Instance Type: Free
   ```

4. **環境變數 (可選)**
   ```
   FLASK_ENV=production
   PORT=10000
   ```

### ✅ 第三步：驗證部署

部署完成後，您的網站將在以下網址上線：
```
https://burnsky-predictor.onrender.com
```

---

## 🔧 部署故障排除

### 常見問題

#### 1. 部署失敗
- 檢查 `requirements.txt` 是否包含所有依賴
- 確認 `Procfile` 格式正確
- 查看 Render.com 部署日誌

#### 2. 應用無法啟動
- 確認 `app.py` 中的 PORT 配置
- 檢查機器學習模型文件是否上傳

#### 3. API 無法訪問
- 測試網址: `https://your-app.onrender.com/test`
- 檢查防火牆設置

### Debug 命令
```bash
# 本地測試
python app.py

# 檢查依賴
pip install -r requirements.txt

# 測試 API
curl https://your-app.onrender.com/predict
```

---

## 📊 部署後檢查清單

### ✅ 功能測試
- [ ] 首頁載入正常
- [ ] 燒天預測功能工作
- [ ] API 端點響應正確
- [ ] 手機版本顯示正常

### ✅ 性能監控
- [ ] 頁面載入時間 < 3秒
- [ ] API 響應時間 < 2秒
- [ ] 無 JavaScript 錯誤

### ✅ SEO 優化
- [ ] 設置自定義域名 (可選)
- [ ] 添加 Google Analytics
- [ ] 提交 Google Search Console

---

## 🎯 下一步計劃

### 立即可做 (本週)
1. **GitHub + Render.com 部署**: 30分鐘內上線
2. **基本測試**: 確保所有功能正常
3. **分享連結**: 發送給朋友測試

### 短期目標 (1個月)
1. **域名購買**: burnsky.app 或 burnsky.hk
2. **Google Analytics**: 追蹤用戶行為
3. **社交媒體**: 開始在香港攝影社群推廣

### 中期目標 (3個月)
1. **移動應用開發**: React Native 版本
2. **用戶反饋收集**: 改進預測算法
3. **付費功能**: 高級預測功能

---

## 💰 成本預估

### 免費階段 (推薦)
- **Render.com 免費版**: $0/月
- **GitHub**: $0 (公開 repository)
- **總成本**: **$0/月**

### 升級版本
- **Render.com Pro**: $7/月
- **自定義域名**: $15/年
- **總成本**: $8.25/月

---

## 📞 支援聯絡

如果在部署過程中遇到問題：

1. **檢查 Render.com 部署日誌**
2. **參考 GitHub Issues**
3. **聯絡千始創意技術支援**

---

**準備好開始部署了嗎？** 

👉 **下一步**: 前往 GitHub.com 創建 repository！
