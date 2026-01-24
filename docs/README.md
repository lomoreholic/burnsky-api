# 📚 BurnSky 文檔中心

## 📖 文檔結構

```
docs/
├── README.md                  ← 本文件
├── reports/                   ← 項目報告歸檔
│   ├── INTEGRATION_REPORTS.md ← 整合報告索引
│   ├── ANALYSIS_REPORTS.md    ← 分析報告索引
│   └── STATUS_REPORTS.md      ← 狀態報告索引
├── guides/                    ← 用戶和開發指南
│   ├── USER_GUIDE.md          ← 使用指南
│   ├── DEVELOPMENT.md         ← 開發指南
│   └── DEPLOYMENT.md          ← 部署指南
└── api-docs/                  ← API 文檔
    ├── ENDPOINTS.md           ← 端點參考
    └── MODELS.md              ← 數據模型

```

## 🗂️ 各目錄說明

### `reports/` - 項目報告歸檔

存儲所有開發過程中生成的報告文件，按類型分類：

- **整合報告** (Integration)
  - AdSense 整合
  - 空氣質素整合
  - 多項功能整合驗證

- **分析報告** (Analysis)
  - 因子權重分析
  - 評分系統分析
  - SEO 分析

- **狀態報告** (Status/Complete)
  - 功能完成報告
  - 系統升級報告
  - 重構完成報告

**新增文件**:
- `INTEGRATION_REPORTS.md` - 所有整合報告的索引和摘要
- `ANALYSIS_REPORTS.md` - 所有分析報告的索引和摘要
- `STATUS_REPORTS.md` - 所有狀態報告的索引和摘要

### `guides/` - 用戶和開發指南

實用的操作和開發指南：

- **USER_GUIDE.md** - 最終用戶使用指南
  - 如何訪問預測系統
  - 如何解讀結果
  - FAQ

- **DEVELOPMENT.md** - 開發者指南
  - 環境設置
  - 項目結構
  - 代碼風格
  - 常見任務

- **DEPLOYMENT.md** - 部署指南
  - 環境要求
  - 部署步驟
  - 故障排查
  - 運維檢查清單

### `api-docs/` - API 文檔

API 參考文檔：

- **ENDPOINTS.md** - 完整的 API 端點參考
- **MODELS.md** - 數據模型和結構

## 📝 使用說明

### 查找信息

1. **找報告？** → 查看 `reports/` 中的索引文件
2. **想使用系統？** → 查看 `guides/USER_GUIDE.md`
3. **想開發功能？** → 查看 `guides/DEVELOPMENT.md`
4. **需要 API 文檔？** → 查看 `api-docs/ENDPOINTS.md`

### 添加新文檔

1. 確定文檔類型（報告/指南/API文檔）
2. 放入相應目錄
3. 更新該目錄的 README 或索引文件

## 🔍 快速搜索

```bash
# 查找關鍵詞
grep -r "keyword" docs/

# 列出所有報告
ls -la docs/reports/

# 查看文檔結構
tree docs/ -L 2
```

## 📊 文檔統計

- **報告文件**: 30+ 個（已整理到 reports/）
- **指南**: 3 個（DEVELOPMENT, USER_GUIDE, DEPLOYMENT）
- **API 文檔**: 2 個（ENDPOINTS, MODELS）

## 🚀 後續計劃

- [ ] 自動生成 API 文檔（Swagger/OpenAPI）
- [ ] 添加視頻教程鏈接
- [ ] 創建多語言版本
- [ ] 建立常見問題知識庫
- [ ] 設置文檔版本控制

---

**最後更新**: 2026-01-24  
**維護者**: BurnSky 開發團隊
