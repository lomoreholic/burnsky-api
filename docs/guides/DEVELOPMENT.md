# 🛠️ 開發者指南

完整的 BurnSky 項目開發指南。

## 📖 目錄

1. [環境設置](#環境設置)
2. [項目結構](#項目結構)
3. [代碼風格](#代碼風格)
4. [常見任務](#常見任務)
5. [故障排查](#故障排查)

---

## 🖥️ 環境設置

### 系統要求

- **OS**: macOS / Linux / Windows
- **Python**: 3.8+
- **Node.js**: 14+ (可選，前端開發)

### 初始化步驟

```bash
# 1. 克隆項目
git clone https://github.com/lomoreholic/burnsky-api.git
cd burnsky-api-1

# 2. 創建虛擬環境
python -m venv .venv

# 3. 激活虛擬環境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

# 4. 安裝依賴
pip install -r requirements.txt

# 5. 配置環境變數
cp .env.example .env
# 編輯 .env 填入必要信息

# 6. 啟動開發伺服器
python app.py
```

### 驗證安裝

```bash
# 檢查 Flask
python -c "import flask; print(f'Flask {flask.__version__}')"

# 檢查依賴
pip list | grep -E "Flask|scikit-learn|numpy"

# 訪問應用
curl http://localhost:5000/health
```

---

## 📁 項目結構

```
burnsky-api-1/
├── app.py                      ← 主應用入口
├── requirements.txt            ← 依賴列表
├── .env.example                ← 環境配置模板
│
├── modules/                    ← 核心模塊
│   ├── __init__.py
│   ├── predictor.py            ← 預測引擎【核心】
│   └── ... (其他模塊)
│
├── hko_webcam_fetcher.py       ← 攝像頭分析【新增智能混合】
├── hko_fetcher.py              ← 氣象數據獲取
├── air_quality_fetcher.py      ← 空氣質素數據
│
├── static/                     ← 靜態資源
│   └── (CSS/JS/圖片)
│
├── templates/                  ← HTML 模板 (26 個)
│   ├── index.html              ← 首頁
│   ├── webcam_analysis.html    ← 攝像頭分析
│   └── ... (其他頁面)
│
├── docs/                       ← 文檔中心【新增】
│   ├── README.md
│   ├── reports/                ← 報告索引
│   ├── guides/                 ← 指南
│   └── api-docs/               ← API 文檔
│
├── models/                     ← ML 模型
│   ├── classification_model.pkl
│   ├── regression_model.pkl
│   └── scaler.pkl
│
├── tests/                      ← 測試
│   └── test_*.py
│
└── README.md                   ← 主文檔
```

### 關鍵模塊詳解

#### `predictor.py` - 預測引擎

```python
# 核心類
BunskyPredictor
  └─ predict(hours_ahead=0)    # 預測指定時間
  └─ analyze_details()         # 詳細分析
  └─ get_probability()         # 概率計算

# 使用示例
from predictor import BunskyPredictor
predictor = BunskyPredictor()
result = predictor.predict(hours_ahead=1)
```

#### `hko_webcam_fetcher.py` - 攝像頭分析【已升級】

```python
# 核心類
WebcamImageAnalyzer            # 圖像分析
  └─ analyze_sky_conditions()  # 天空分析【支持全天候】
  └─ _evaluate_sunset_potential()  # 【新】智能混合模式
  └─ _get_time_period()        # 【新】時段分類

RealTimeWebcamMonitor          # 實時監控
  └─ get_current_conditions()  # 當前狀況
```

---

## 📝 代碼風格

### Python 風格指南

遵循 PEP 8:

```python
# ✅ 正確
def analyze_sky_conditions(image):
    """分析天空狀況"""
    result = process_image(image)
    return result

# ❌ 錯誤
def analyzeSkyConditions(image):
    result=process_image(image)
    return result
```

### 命名慣例

```python
# 類名: PascalCase
class WebcamImageAnalyzer:
    pass

# 函數/方法: snake_case
def analyze_sky_conditions():
    pass

# 常數: UPPER_SNAKE_CASE
SUNSET_TIME_RANGE = (16, 19)

# 私有方法: _snake_case
def _get_time_period():
    pass
```

### 註釋規範

```python
def _evaluate_sunset_potential(self, mean_rgb, cloud_coverage, visibility):
    """
    評估燒天潛力（智能混合模式）
    
    Args:
        mean_rgb: RGB 平均值
        cloud_coverage: 雲覆蓋度 (0-100)
        visibility: 能見度 (0-100)
        
    Returns:
        dict: 評分和詳細信息
        {
            'score': float,
            'level': str,
            'factors': dict
        }
    """
```

---

## 🔧 常見任務

### 添加新的 API 端點

```python
# 在 app.py 中

@app.route("/api/new-endpoint", methods=["GET"])
@flask_cache.cached(timeout=120)
def new_endpoint():
    """
    新端點說明
    
    Returns:
        JSON 格式的數據
    """
    try:
        result = {
            'status': 'success',
            'data': {}
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### 修改預測算法

```python
# 在 predictor.py 中

def analyze_details(self):
    """分析詳細因子"""
    details = {
        'time_factor': self._calculate_time_factor(),      # 修改這裡
        'temperature_factor': self._calculate_temp_factor(),
        # ...
    }
    return details
```

### 添加新的特徵提取

```python
# 在 hko_webcam_fetcher.py 中

def analyze_sky_conditions(self, image):
    """分析天空狀況"""
    # 現有特徵
    mean_rgb = np.mean(sky_region.reshape(-1, 3), axis=0)
    
    # 添加新特徵
    new_feature = extract_new_feature(sky_region)
    
    return {
        'mean_color': {...},
        'new_feature': new_feature,  # 新增
    }
```

### 運行測試

```bash
# 運行所有測試
pytest

# 運行特定測試文件
pytest tests/test_predictor.py

# 生成覆蓋率報告
pytest --cov

# 查看覆蓋率詳情
coverage report
coverage html  # 生成 HTML 報告
```

### 提交代碼

```bash
# 檢查更改
git status

# 添加文件
git add hko_webcam_fetcher.py

# 提交
git commit -m "feat: 智能混合模式 - 全天候相片分析

- 支持日出和早晨分析
- 動態時間權重調整
- 基於特徵評分
"

# 推送
git push origin main
```

---

## 🐛 故障排查

### 常見問題

#### Q1: 伺服器無法啟動

```bash
# 檢查端口是否被佔用
lsof -i :5000

# 殺死進程
kill -9 <PID>

# 更改端口
python app.py --port 5001
```

#### Q2: 導入錯誤

```bash
# 確保在虛擬環境中
which python
# 應該輸出: /path/to/.venv/bin/python

# 重新安裝依賴
pip install -r requirements.txt --force-reinstall
```

#### Q3: 攝像頭無法連接

```python
# 檢查 HKO 服務器狀態
import requests
response = requests.get('https://www.hko.gov.hk/wxinfo/aws/hko_mica/hko/latest_HKO.jpg')
print(response.status_code)  # 應該是 200
```

#### Q4: ML 模型錯誤

```bash
# 重新訓練模型
python -c "from app import ml_predictor; ml_predictor.train()"

# 檢查模型文件
ls -la models/*.pkl
```

### 調試技巧

```python
# 打印調試信息
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"分析結果: {result}")

# 使用 pdb 調試
import pdb; pdb.set_trace()

# 檢查環境
import os
print(os.environ.get('FLASK_ENV'))
```

---

## 📚 相關資源

- 📖 [Flask 文檔](https://flask.palletsprojects.com/)
- 🤖 [Scikit-learn 文檔](https://scikit-learn.org/)
- 📷 [OpenCV 文檔](https://opencv.org/)
- 🌐 [HKO API](https://www.hko.gov.hk/)

---

## 🎯 開發檢查清單

新功能完成時：

- [ ] 代碼風格符合 PEP 8
- [ ] 添加適當的註釋和文檔
- [ ] 編寫單元測試
- [ ] 測試覆蓋率 > 80%
- [ ] 通過所有測試
- [ ] 更新 README/文檔
- [ ] 提交 PR 並經過審查
- [ ] 合併到主分支
- [ ] 部署到測試環境
- [ ] 驗證功能正常

---

**最後更新**: 2026-01-24  
**維護者**: BurnSky 開發團隊
