# 🔥 燒天預測系統 - 快速上線指南

## 📱 30分鐘內將你的燒天預測系統上線！

### 🚀 方法一：使用自動部署腳本（推薦）

```bash
./deploy.sh
```

腳本會逐步指導你完成：
1. GitHub Repository 創建
2. 代碼推送
3. Render.com 部署
4. 自動測試

### ⚡ 方法二：手動快速部署

#### 1. 創建 GitHub Repository
- 前往 [GitHub](https://github.com) → New repository
- Name: `burnsky-api`  
- Visibility: **Public**（免費版要求）
- 點擊 "Create repository"

#### 2. 推送代碼
```bash
# 替換 YOUR_USERNAME 為你的 GitHub 用戶名
git remote add origin https://github.com/YOUR_USERNAME/burnsky-api.git
git push -u origin main
```

#### 3. 部署到 Render.com
- 前往 [Render.com](https://render.com) → 註冊/登入
- New + → Web Service → Connect GitHub
- 選擇你的 `burnsky-api` repository
- 配置：
  - **Name**: `burnsky-api`
  - **Environment**: Python 3
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
  - **Plan**: Free
- 點擊 "Create Web Service"

#### 4. 等待部署完成（約5-10分鐘）

#### 5. 測試你的應用
```bash
python test_deployment.py https://your-app-name.onrender.com
```

---

## 🎯 部署後檢查清單

- [ ] ✅ 首頁可以正常訪問
- [ ] ✅ 即時預測功能正常
- [ ] ✅ 日出預測功能正常  
- [ ] ✅ 日落預測功能正常
- [ ] ✅ 手機瀏覽體驗良好
- [ ] ✅ 預測數據更新正常

## 📞 獲得幫助

- 📋 詳細部署指南：`RENDER_DEPLOY_GUIDE.md`
- 🐛 常見問題：`DEPLOYMENT_PLAN.md`
- 📱 移動應用規劃：`MOBILE_APP_ARCHITECTURE.md`

## 🎉 成功部署後

你的燒天預測系統現在已經可以在互聯網上訪問！

**分享你的成果：**
- 📱 在手機上測試
- 🔗 分享給朋友試用
- 📊 收集用戶反饋
- 🌟 準備下一階段開發

---

*由千始創意開發 | 所有預測僅供參考*
