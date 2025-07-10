# GitHub Repository 建立指南

## 步驟 1: 在 GitHub 創建新 Repository

1. 訪問 [GitHub](https://github.com)
2. 點擊右上角的 "+" 按鈕，選擇 "New repository"
3. Repository 設定：
   - Repository name: `burnsky-api`
   - Description: `香港燒天預測系統 - 基於香港天文台數據的智能天氣預測 API`
   - Visibility: Public（免費版需要 public repository）
   - 不要勾選 "Add a README file"、"Add .gitignore"、"Choose a license"（因為我們已經有了）

4. 點擊 "Create repository"

## 步驟 2: 連接本地 Repository 到 GitHub

在創建完 GitHub repository 後，回到終端機執行以下命令：

```bash
# 添加遠程 repository（將 YOUR_USERNAME 替換為你的 GitHub 用戶名）
git remote add origin https://github.com/YOUR_USERNAME/burnsky-api.git

# 推送代碼到 GitHub
git push -u origin main
```

## 步驟 3: 驗證推送成功

推送完成後，回到 GitHub repository 頁面，應該可以看到所有文件都已上傳。

## 下一步

代碼推送到 GitHub 後，請參考 `RENDER_DEPLOY_GUIDE.md` 繼續在 Render.com 部署。

---

**注意**: 如果遇到推送問題，可能需要：
1. 配置 GitHub 個人訪問令牌（Personal Access Token）
2. 使用 SSH 金鑰連接

請根據 GitHub 的最新文檔配置認證方式。
