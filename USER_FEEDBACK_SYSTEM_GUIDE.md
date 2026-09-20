# 用戶反饋系統使用指南

## 📋 系統概述

用戶反饋系統讓用戶可以對預測的準確性提供實際反饋,幫助系統計算真實的預測準確率,替代原本硬編碼的估算值(85%)。

---

## 🎯 主要功能

### 1. 用戶反饋提交
- **位置**: 首頁預測結果下方
- **輸入方式**: 滑塊評分 (0-100 分)
- **附加信息**: 可選文字備註

### 2. 準確率統計
- **計算公式**: `準確率 = 100 - 平均誤差`
- **統計範圍**: 最近 30 天的反饋數據
- **誤差分佈**: 10分內、20分內的準確度統計

### 3. 燒天歷史儀表板整合
- **路徑**: `/burnsky-dashboard`
- **顯示**: 基於真實反饋的準確率
- **Fallback**: 無反饋時使用估算值

---

## 🗄️ 數據庫結構

### `user_feedback` 表

```sql
CREATE TABLE user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_timestamp TEXT,           -- 預測時間
    predicted_score INTEGER,             -- 系統預測分數 (0-100)
    user_rating INTEGER,                 -- 用戶實際評分 (0-100)
    location TEXT,                       -- 拍攝地點 (選填)
    photo_url TEXT,                      -- 照片URL (選填)
    comment TEXT,                        -- 用戶備註 (選填)
    feedback_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    weather_conditions TEXT              -- 天氣條件 (選填, JSON格式)
);
```

**設計考量**:
- 不使用外鍵關聯 `prediction_history`,因為用戶可能幾小時後才提交反饋
- `prediction_timestamp` 記錄系統預測的時間
- `feedback_timestamp` 記錄用戶提交反饋的時間

---

## 🔌 API 端點

### 1. 提交反饋

**端點**: `POST /api/submit-feedback`

**請求 Body**:
```json
{
    "predicted_score": 75,              // 必需: 系統預測分數
    "user_rating": 80,                  // 必需: 用戶實際評分
    "comment": "實際顏色更豐富",         // 選填: 用戶備註
    "prediction_timestamp": "2026-01-27T18:30:00",  // 選填: 預測時間
    "location": "維多利亞港"             // 選填: 拍攝地點
}
```

**成功響應**:
```json
{
    "status": "success",
    "message": "感謝您的反饋！",
    "feedback_id": 123,
    "accuracy_stats": {
        "has_data": true,
        "accuracy": 82.5,
        "avg_error": 17.5,
        "feedback_count": 48,
        "within_10_points": 62.5,
        "within_20_points": 87.5,
        "last_updated": "2026-01-27T19:30:00"
    }
}
```

**錯誤響應**:
```json
{
    "status": "error",
    "message": "缺少必需字段"  // 或 "評分必須在 0-100 之間"
}
```

---

### 2. 獲取準確率統計

**端點**: `GET /api/accuracy-stats`

**響應 (有數據)**:
```json
{
    "has_data": true,
    "accuracy": 82.5,                  // 準確率 (100 - 平均誤差)
    "avg_error": 17.5,                 // 平均誤差 (分)
    "feedback_count": 48,              // 反饋數量
    "within_10_points": 62.5,          // 10分內準確度 (%)
    "within_20_points": 87.5,          // 20分內準確度 (%)
    "last_updated": "2026-01-27T19:30:00"
}
```

**響應 (無數據)**:
```json
{
    "has_data": false,
    "message": "暫無用戶反饋數據",
    "estimated_accuracy": 85,          // Fallback 估算值
    "feedback_count": 0
}
```

---

## 🖥️ 前端實現

### 1. 全局變量

```javascript
let currentPredictedScore = null;        // 保存當前預測分數
let currentPredictionTimestamp = null;   // 保存預測時間戳
```

### 2. 預測完成時保存分數

位置: `loadPrediction()` 函數

```javascript
// 保存預測分數以供用戶反饋使用
currentPredictedScore = data.burnsky_score;
currentPredictionTimestamp = new Date().toISOString();
console.log('✅ 預測分數已保存:', {
    score: currentPredictedScore,
    timestamp: currentPredictionTimestamp,
    level: data.prediction_level
});
```

### 3. 反饋表單 HTML

```html
<div id="feedbackSection">
    <!-- 評分滑塊 -->
    <input type="range" id="userRating" min="0" max="100" value="50" 
           oninput="document.getElementById('ratingValue').textContent = this.value">
    <span id="ratingValue">50</span> 分
    
    <!-- 備註文本框 -->
    <textarea id="feedbackComment" placeholder="補充說明..."></textarea>
    
    <!-- 提交按鈕 -->
    <button onclick="submitFeedback()">✅ 提交反饋</button>
</div>
```

### 4. 提交邏輯

```javascript
async function submitFeedback() {
    // 1. 獲取用戶輸入
    const userRating = parseInt(document.getElementById('userRating').value);
    const comment = document.getElementById('feedbackComment').value;
    
    // 2. 驗證預測分數是否存在
    if (currentPredictedScore === null) {
        APIUtils.showToast('請先進行燒天預測', 'warning');
        return;
    }
    
    // 3. 發送 POST 請求
    const response = await fetch('/api/submit-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            predicted_score: currentPredictedScore,
            user_rating: userRating,
            comment: comment,
            prediction_timestamp: currentPredictionTimestamp
        })
    });
    
    const result = await response.json();
    
    // 4. 顯示結果
    if (result.status === 'success') {
        // 更新 UI 為成功提示和準確率統計
    }
}
```

---

## 🧪 測試指南

### 1. 運行測試腳本

```bash
# 確保 Flask 服務器正在運行
python3 app.py

# 在另一個終端運行測試
python3 test_feedback_system.py
```

### 2. 測試覆蓋

- ✅ 數據庫表結構檢查
- ✅ 提交反饋功能
- ✅ 獲取準確率統計
- ✅ 參數驗證 (缺少字段、超出範圍)
- ✅ 數據庫查詢

### 3. 手動測試流程

```bash
# 1. 檢查數據表
sqlite3 prediction_history.db "SELECT * FROM user_feedback ORDER BY id DESC LIMIT 5;"

# 2. 測試提交反饋
curl -X POST http://localhost:5001/api/submit-feedback \
  -H "Content-Type: application/json" \
  -d '{"predicted_score":75,"user_rating":80,"comment":"測試反饋"}'

# 3. 獲取準確率統計
curl http://localhost:5001/api/accuracy-stats

# 4. 查看反饋記錄
sqlite3 prediction_history.db "SELECT COUNT(*) FROM user_feedback;"
```

---

## 📊 準確率計算邏輯

### 核心函數: `calculate_real_accuracy()`

```python
def calculate_real_accuracy():
    """計算基於用戶反饋的真實準確率"""
    
    # 1. 查詢最近30天的反饋
    SELECT predicted_score, user_rating, feedback_timestamp
    FROM user_feedback
    WHERE feedback_timestamp >= datetime('now', '-30 days')
    
    # 2. 計算平均誤差
    total_error = Σ|predicted_score - user_rating|
    avg_error = total_error / feedback_count
    
    # 3. 計算準確率
    accuracy = 100 - avg_error
    
    # 4. 統計誤差分佈
    within_10 = COUNT(誤差 ≤ 10) / total × 100
    within_20 = COUNT(誤差 ≤ 20) / total × 100
    
    return {
        'accuracy': round(accuracy, 1),
        'avg_error': round(avg_error, 1),
        'feedback_count': count,
        'within_10_points': within_10,
        'within_20_points': within_20
    }
```

### 整合到歷史儀表板

```python
# 優先使用真實反饋
accuracy_stats = calculate_real_accuracy()

if accuracy_stats['has_data']:
    accuracy_percentage = accuracy_stats['accuracy']
else:
    # Fallback: 使用預測分數估算
    accuracy_percentage = min(max(avg_accuracy * 1.2, 75), 95)
```

---

## 🎯 使用場景

### 場景 1: 用戶查看預測後拍攝

1. 用戶訪問首頁,查看燒天預測
2. 系統自動保存預測分數到全局變量
3. 用戶實際拍攝後,返回頁面
4. 滾動到反饋區域,拖動滑塊評分
5. 可選填寫備註 (例如: "顏色比預期豐富")
6. 點擊"提交反饋"
7. 系統顯示感謝提示和當前準確率統計

### 場景 2: 管理員查看準確率

1. 訪問 `/burnsky-dashboard`
2. 在 "💡 數據洞察" 區域查看準確率
3. 如果有用戶反饋數據,顯示真實準確率
4. 如果沒有反饋數據,顯示估算值 (標記為估算)

### 場景 3: 數據分析

```bash
# 查詢準確率趨勢
sqlite3 prediction_history.db "
SELECT 
    DATE(feedback_timestamp) as date,
    COUNT(*) as feedback_count,
    AVG(ABS(predicted_score - user_rating)) as avg_error,
    100 - AVG(ABS(predicted_score - user_rating)) as accuracy
FROM user_feedback
GROUP BY DATE(feedback_timestamp)
ORDER BY date DESC;
"
```

---

## 🔒 安全考量

### 1. 輸入驗證

- **評分範圍**: 0-100 (後端強制檢查)
- **必需字段**: predicted_score, user_rating
- **SQL 注入防護**: 使用 parameterized query

### 2. 速率限制

```python
@app.route("/api/submit-feedback", methods=['POST'])
@limiter.limit("30 per hour")  # 可根據需求調整
def submit_feedback():
    ...
```

### 3. 數據清理

```sql
-- 定期清理超過90天的舊反饋 (可選)
DELETE FROM user_feedback 
WHERE feedback_timestamp < datetime('now', '-90 days');
```

---

## 📈 性能優化

### 1. 數據庫索引

```sql
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp 
ON user_feedback(feedback_timestamp);
```

### 2. 快取準確率統計

```python
@flask_cache.cached(timeout=300, key_prefix='accuracy_stats')
def get_accuracy_stats():
    stats = calculate_real_accuracy()
    return jsonify(stats)
```

### 3. 限制查詢範圍

- 只查詢最近 30 天的數據
- 使用 LIMIT 限制返回行數

---

## 🐛 故障排查

### 問題 1: 無法提交反饋 ("請先進行燒天預測")

**原因**: `currentPredictedScore` 為 null

**解決**:
1. 檢查 `loadPrediction()` 函數是否成功執行
2. 檢查瀏覽器控制台是否顯示 "✅ 預測分數已保存"
3. 確認 `data.burnsky_score` 存在於 API 響應中

```javascript
// 檢查預測分數是否保存
console.log('當前預測分數:', currentPredictedScore);
console.log('預測時間戳:', currentPredictionTimestamp);
```

---

### 問題 2: 準確率顯示為估算值

**原因**: 數據庫中沒有用戶反饋數據

**檢查**:
```bash
sqlite3 prediction_history.db "SELECT COUNT(*) FROM user_feedback;"
```

**解決**:
- 至少需要 1 條反饋數據才能計算真實準確率
- 鼓勵用戶提交反饋

---

### 問題 3: API 返回 500 錯誤

**排查步驟**:

1. 檢查 Flask 日誌
```bash
tail -f app.log
```

2. 檢查數據庫連接
```python
import sqlite3
conn = sqlite3.connect('prediction_history.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM user_feedback LIMIT 1")
print(cursor.fetchone())
conn.close()
```

3. 測試 SQL 查詢
```bash
sqlite3 prediction_history.db "
SELECT predicted_score, user_rating
FROM user_feedback
WHERE feedback_timestamp >= datetime('now', '-30 days');
"
```

---

## 📚 相關文件

- [app.py](app.py) - 後端 API 實現 (第5997-6146行)
- [templates/index.html](templates/index.html) - 前端 UI 和邏輯 (第3176-3282行)
- [test_feedback_system.py](test_feedback_system.py) - 測試腳本
- [prediction_history.db](prediction_history.db) - SQLite 數據庫

---

## 🚀 未來改進

### 短期
- [ ] 添加照片上傳功能 (photo_url 字段)
- [ ] 天氣條件自動記錄 (weather_conditions 字段)
- [ ] Email 通知管理員新反饋

### 中期
- [ ] 反饋數據可視化儀表板
- [ ] 按地點統計準確率
- [ ] 按時段統計準確率 (日出 vs 日落)

### 長期
- [ ] 基於用戶反饋自動調整預測算法
- [ ] ML 模型訓練整合
- [ ] 用戶信譽系統 (過濾低質量反饋)

---

## 📞 技術支援

遇到問題? 請檢查:

1. **Flask 日誌**: `tail -f app.log`
2. **瀏覽器控制台**: F12 → Console
3. **數據庫狀態**: `sqlite3 prediction_history.db ".tables"`
4. **API 響應**: 使用 Postman 或 curl 測試

---

**最後更新**: 2026-01-27  
**版本**: 1.0.0  
**作者**: BurnSky Team
