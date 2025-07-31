# 🕐 每小時預測系統與數據管理指南

## 📋 系統概覽

### 新增功能
1. **每小時自動預測保存** - 自動記錄預測數據用於後續分析
2. **照片與預測交叉檢查** - 比較用戶上傳照片與歷史預測的準確性
3. **數據管理與清理** - 完整的數據清理和管理功能
4. **時間因子考慮** - 日期時間作為重要考慮因素

## 🔧 功能詳情

### 1. 每小時預測保存系統

#### 工作原理
- **自動觸發**: 每小時第5分鐘自動執行
- **預測範圍**: sunset/sunrise × 提前0,1,2,3,6,12小時 = 共12個預測
- **數據豐富**: 包含完整的時間因子、天氣數據、警告信息

#### 保存的數據
```json
{
  "prediction_type": "sunset/sunrise",
  "advance_hours": 0-12,
  "score": 17.0,
  "factors": {
    "time_factors": {
      "hour": 1,
      "day_of_week": 0,
      "day_of_month": 28,
      "month": 7,
      "season": "summer",
      "is_weekend": false,
      "time_category": "late_night"
    },
    "weather_timing": {
      "prediction_datetime": "2025-07-28T01:02:18",
      "target_datetime": "2025-07-28T03:02:18",
      "advance_hours": 2
    }
  },
  "weather_data": { /* 完整天氣數據 */ },
  "warnings": { /* 警告數據 */ }
}
```

#### 控制配置
```python
HOURLY_SAVE_ENABLED = True  # 啟用/停用自動保存
PREDICTION_HISTORY_DB = 'prediction_history.db'  # 數據庫文件
```

### 2. 照片與預測交叉檢查

#### API端點
```bash
POST /api/photo-accuracy-check
Content-Type: application/json

{
  "datetime": "2025-07-27 17:02:18",  # 支持多種格式
  "location": "香港中環",
  "quality": 7,  # 1-10分
  "type": "sunset"
}
```

#### 支持的時間格式
- `"2025-07-27_19-10"` (原始格式)
- `"2025-07-27 17:02:18"` (標準格式)
- `"2025-07-27T17:02:18"` (ISO格式)
- `"2025-07-27 17:02"` (簡化格式)

#### 返回結果
```json
{
  "status": "success",
  "average_accuracy": 99.5,
  "predictions_analyzed": 1,
  "best_prediction": {
    "accuracy_percentage": 99.5,
    "predicted_score": 50.5,
    "actual_quality": 50,
    "advance_hours": 2
  },
  "improvement_suggestions": [
    "預測準確性良好，繼續維持當前算法"
  ]
}
```

#### 自動集成
照片上傳時會自動進行交叉檢查：
```json
{
  "status": "success",
  "photo_analysis": { /* 照片分析 */ },
  "accuracy_check": { /* 自動交叉檢查結果 */ }
}
```

### 3. 數據管理與清理

#### 查看數據狀態
```bash
GET /api/data-management
```

返回：
```json
{
  "data_summary": {
    "photo_cases": {
      "count": 3,
      "in_memory_cases": 3,
      "database_file": "burnsky_photos.db"
    },
    "prediction_history": {
      "count": 12,
      "date_range": ["2025-07-27 17:02:18", "2025-07-28 01:05:00"],
      "database_file": "prediction_history.db"
    },
    "uploaded_files": {
      "count": 0,
      "total_size": 0,
      "folder": "uploads"
    }
  }
}
```

#### 清理數據
```bash
POST /api/data-cleanup
Content-Type: application/json

{
  "operation": "clear_prediction_history",  # 清理操作
  "confirm": true,  # 必須確認
  "days_old": 30    # 清理N天前的數據（僅用於clear_old_data）
}
```

#### 可用的清理操作
- `clear_photo_cases` - 清理照片案例數據
- `clear_prediction_history` - 清理預測歷史
- `clear_uploaded_files` - 清理上傳檔案
- `clear_old_data` - 清理N天前的數據
- `clear_all` - 清理所有數據

### 4. 時間因子考慮

#### 新增的時間維度
每次預測和照片記錄都會包含：
- **時間**: 具體小時 (0-23)
- **星期**: 週一到週日 (0-6)
- **日期**: 月份中的日期 (1-31)
- **月份**: 年份中的月份 (1-12)
- **季節**: spring/summer/autumn/winter
- **週末**: 是否為週末
- **時間類別**: early_morning/morning/afternoon/evening/night/late_night

#### 用途
1. **預測改進**: 分析時間模式對燒天的影響
2. **準確性分析**: 了解不同時間段的預測準確性
3. **學習優化**: 基於時間維度優化預測算法

## 🚀 部署與使用

### 啟動系統
```bash
python3 app.py
```

系統啟動時會：
1. ✅ 初始化預測歷史數據庫
2. ⏰ 啟動每小時預測保存排程
3. 📸 載入現有照片案例

### 監控日誌
```
📊 預測歷史數據庫已初始化
⏰ 每小時預測保存排程已啟動
🕐 開始自動保存每小時預測...
💾 已保存預測歷史: sunset (分數: 17.0, 01:05)
✅ 每小時預測保存完成
```

### 手動觸發保存
```python
# 在Python中手動觸發
import app
app.auto_save_current_predictions()
```

## 📊 數據分析建議

### 1. 準確性分析
定期檢查預測準確性：
```bash
# 比較照片質量與預測分數
curl -X POST -H "Content-Type: application/json" \
  -d '{"datetime": "2025-07-27 19:10:00", "quality": 8, "type": "sunset"}' \
  http://localhost:8080/api/photo-accuracy-check
```

### 2. 時間模式分析
分析不同時間段的預測表現：
- 早上 vs 晚上的預測準確性
- 週末 vs 工作日的差異
- 季節性影響

### 3. 數據清理計劃
建議的清理頻率：
- **每週**: 清理上傳檔案
- **每月**: 清理30天前的舊數據
- **按需**: 清理特定類型數據

## ⚠️ 注意事項

### 性能考量
- 每小時保存會執行12次預測計算
- 建議在低負載時間（如凌晨）執行
- 大量歷史數據可能影響查詢性能

### 儲存空間
- 每小時約產生12條預測記錄
- 每天約288條記錄
- 建議定期清理舊數據

### 準確性分析
- 需要足夠的歷史數據才能進行有意義的比較
- 建議系統運行至少1週後再開始分析準確性
- 考慮天氣變化的影響

## 🔄 升級與維護

### 數據庫升級
如需修改數據庫結構，記得備份現有數據：
```bash
cp prediction_history.db prediction_history_backup.db
```

### 監控建議
1. 檢查磁碟空間使用量
2. 監控預測保存成功率
3. 定期檢查準確性趨勢

---

*系統版本: 2025年7月28日*
*自動預測保存功能已完全集成並測試*
