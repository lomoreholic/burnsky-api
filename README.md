# 🔥 燒天預測系統 (BurnSky Predictor)

[![部署狀態](https://img.shields.io/badge/部署-準備中-yellow)](https://burnsky-predictor.onrender.com)
[![版本](https://img.shields.io/badge/版本-v1.0.0-green)](https://github.com/your-username/burnsky-predictor)

> 基於香港天文台數據的智能燒天預測系統，結合傳統算法與機器學習技術

## ✨ 功能特色

- 🤖 **智能預測**: 結合傳統氣象分析與 AI 機器學習
- ⏰ **提前預測**: 支援 1-12 小時提前預測  
- 🌄 **日出日落**: 精確的日出/日落燒天分析
- 🎨 **顏色預測**: 預測燒天色彩組合與強度
- 🌬️ **空氣品質整合**: 即時 AQHI 和 PM2.5 數據分析
- 📱 **響應式設計**: 完美支援手機、平板、桌面

### 🧮 評分因子系統 (總分 100 分)
- **時間因子 (0-5分)：** 日落前後30分鐘得分最高
- **溫度因子 (0-18分)：** 理想溫度範圍 26-35°C
- **濕度因子 (0-22分)：** 最佳濕度範圍 60-85%
- **能見度因子 (0-18分)：** 基於降雨量判斷空氣清晰度
- **雲層分析因子 (0-30分)：** 進階天氣描述和雲層類型分析
- **UV指數因子 (0-10分)：** 高UV表示日照充足
- **風速因子 (0-5分)：** 適中風速有利於燒天形成
- **空氣品質因子 (0-12分)：** AQHI、PM2.5 對色彩透明度的影響

### 📊 預測等級分類
- 🔥 **80分以上：** 極高機率燒天
- ☀️ **70-79分：** 高機率燒天
- ⛅ **50-69分：** 中等機率燒天
- ☁️ **30-49分：** 低機率燒天
- 🌫️ **30分以下：** 不太可能燒天

### 🌐 美觀的前端介面
- 響應式設計，支援手機和桌面
- 即時動態更新燒天預測
- 直觀的圓形燒天指數顯示
- 詳細的分析因子展示
- 自動每5分鐘更新數據

## 🚀 快速開始

### 環境要求
- Python 3.8+
- 網路連接（用於獲取香港天文台數據）

### 安裝步驟

1. **克隆專案**
```bash
git clone <your-repo-url>
cd burnsky-api
```

2. **建立虛擬環境**
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\\Scripts\\activate  # Windows
```

3. **安裝依賴**
```bash
pip install -r requirements.txt
```

4. **啟動服務器**
```bash
python app.py
```

5. **開啟瀏覽器**
訪問 `http://127.0.0.1:5000` 查看燒天預測前端

## 📡 API 使用

### 主要端點

#### `GET /`
- **功能：** 燒天預測前端介面
- **回應：** 美觀的網頁介面，即時顯示燒天預測結果

#### `GET /predict`
- **功能：** 取得燒天預測數據
- **回應：** JSON 格式的預測結果

### API 回應範例

```json
{
  "burnsky_score": 65,
  "probability": "65%",
  "prediction_level": "中等機率燒天 ⛅",
  "analysis_details": {
    "time_factor": {
      "score": 5,
      "description": "目前時間是否接近日落時間",
      "current_time": "23:51"
    },
    "temperature_factor": {
      "score": 15,
      "description": "目前溫度: 31°C (理想溫度範圍)",
      "temperature": 31
    },
    "humidity_factor": {
      "score": 15,
      "description": "目前濕度: 80% (良好濕度範圍)",
      "humidity": 80
    },
    "air_quality_factor": {
      "score": 10,
      "description": "AQHI 4 (中)，空氣品質一般",
      "aqhi": 4,
      "level": "中",
      "pm25": 25,
      "impact": "良好",
      "source": "環保署"
    },
    // ... 其他分析因子
    "analysis_summary": [
      "⏰ 非最佳拍攝時間",
      "✅ 濕度條件理想",
      "✅ 溫度條件良好",
      "📸 可以嘗試拍攝，有一定機會"
    ]
  },
  "weather_data": {
    // 香港天文台原始天氣數據
  }
}
```

## 🏗️ 系統架構

```
burnsky-api/
├── app.py                    # Flask 主應用
├── hko_fetcher.py           # 香港天文台數據獲取
├── air_quality_fetcher.py   # 空氣品質數據獲取 (AQHI/PM2.5)
├── predictor.py             # 燒天預測算法
├── advanced_predictor.py    # 進階預測功能 (機器學習/雲層分析)
├── enhanced_prediction_system.py  # 增強預測系統
├── satellite_cloud_analyzer.py    # 衛星雲圖分析
├── templates/
│   ├── index.html           # 主頁前端介面
│   ├── status.html          # 系統狀態頁面
│   ├── privacy.html         # 隱私政策
│   └── terms.html           # 使用條款
├── static/
│   ├── robots.txt           # SEO 優化
│   └── sitemap.xml          # 網站地圖
├── models/                  # 機器學習模型
│   ├── classification_model.pkl
│   ├── regression_model.pkl
│   └── scaler.pkl
├── requirements.txt         # Python 依賴
├── runtime.txt             # Python 版本
├── Procfile               # 部署配置
└── README.md             # 說明文件
```

## 🔧 核心模組

### `hko_fetcher.py`
負責從香港天文台 API 獲取即時天氣數據：
- 即時天氣觀測 (`rhrread`)
- 天氣預報 (`flw`)
- 九天預報 (`fnd`)
- 天氣警告 (`warningInfo`)

### `air_quality_fetcher.py` 🌬️
**新增功能**：空氣品質數據整合系統
- 香港環保署 AQHI 數據獲取
- PM2.5、PM10 等污染物監測
- 多數據源自動切換與 fallback
- 空氣品質對燒天影響評估
- 支援：環保署官方 API、第三方 API、天氣估算、預設值

### `predictor.py`
實現燒天預測算法：
- 多因子權重計算 (8個主要因子)
- 空氣品質因子整合
- 智能分析邏輯
- 預測等級判定
- 機器學習與傳統算法結合

### `advanced_predictor.py`
進階預測功能：
- 機器學習模型預測
- 雲層厚度與顏色可見度分析
- 燒天強度與色彩預測
- 衛星雲圖分析整合
- 進階氣象數據分析

### `app.py`
Flask Web 應用：
- RESTful API 端點
- 前端頁面服務
- 系統狀態監控
- 錯誤處理與日誌

## 🌟 功能特點

### 實時數據
- 香港27個地點的溫度和濕度
- UV指數、降雨量、天氣警告
- 天氣預報和九天預報

### 智能分析
- 基於氣象學原理的預測算法
- 多維度因子綜合評估
- 個人化拍攝建議

### 用戶體驗
- 美觀的漸變色設計
- 圓形燒天指數顯示器
- 響應式布局設計
- 自動更新機制

## 🛠️ 自定義設置

### 調整預測參數
在 `predictor.py` 中可以調整各種預測參數：

```python
# 理想溫度範圍
if 25 <= temperature <= 32:
    score = 15

# 理想濕度範圍
if 50 <= humidity <= 70:
    score = 20

# 日落時間計算
if 4 <= month <= 9:  # 夏季
    sunset_hour = 19
```

### 前端樣式
在 `templates/index.html` 中可以調整前端樣式和布局。

## 📈 系統監控

### 日誌查看
Flask 應用會在控制台輸出詳細日誌：
```bash
python app.py
```

### API 測試
使用 curl 測試 API 端點：
```bash
curl http://127.0.0.1:5000/predict
```

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request 來改進這個系統！

### 開發環境設置
1. Fork 此專案
2. 建立功能分支：`git checkout -b feature/new-feature`
3. 提交更改：`git commit -am 'Add new feature'`
4. 推送分支：`git push origin feature/new-feature`
5. 提交 Pull Request

## 📄 授權條款

本專案採用 MIT 授權條款。

## 🙏 致謝

- 香港天文台提供開放數據 API
- Flask 框架提供 Web 服務支持
- 社群提供的天氣預測算法參考

---

**🔥 享受燒天預測，捕捉最美的天空！**
