# 🔥 燒天預測系統 - 網站載入問題解決指南

## 🔍 問題分析

### 為什麼網站會載入不到？

**主要原因**: Render 免費方案限制
- ⏰ **自動休眠**: 30分鐘無訪問自動暫停服務
- 🐌 **冷啟動**: 休眠後首次訪問需要 30-60 秒啟動
- 💾 **資源限制**: 免費方案 CPU/記憶體有限

### 症狀識別
- 網站有時正常，有時載入很慢或失敗
- 第一次訪問很慢（30-60秒），之後正常
- 長時間未訪問後需要重新等待

## 💡 解決方案

### 方案 1: 自動保活系統 (推薦)

運行保活腳本：
```bash
# 後台運行保活工具
./keep_alive.sh &

# 或使用 nohup 確保不會因終端關閉而停止
nohup ./keep_alive.sh > /dev/null 2>&1 &
```

這會每 25 分鐘自動 ping 您的網站，防止休眠。

### 方案 2: 手動喚醒

當網站載入不到時：
```bash
# 手動喚醒網站
curl https://burnsky-api.onrender.com/test

# 檢查狀態
python diagnose.py https://burnsky-api.onrender.com
```

### 方案 3: 升級到付費方案

**Render 付費方案優勢**:
- 🚀 無休眠，24/7 運行
- ⚡ 更快的 CPU 和記憶體
- 📊 更好的性能監控
- 💰 費用: $7/月

## 🛠️ 保活工具使用指南

### 啟動保活服務
```bash
# 基本使用
./keep_alive.sh

# 後台運行
nohup ./keep_alive.sh &

# 檢查是否在運行
ps aux | grep keep_alive
```

### 停止保活服務
```bash
# 如果在前台運行，按 Ctrl+C

# 如果在後台運行，找到進程 ID 並終止
pkill -f keep_alive.sh
```

### 查看保活日誌
```bash
# 查看日誌文件
tail -f keep_alive.log

# 查看最近的記錄
tail -20 keep_alive.log
```

## 📊 性能優化建議

### 1. 減少冷啟動時間
已在應用中實現：
- 輕量化路由 `/test`
- 快速響應端點
- 最小化初始化時間

### 2. 緩存策略
```python
# 已實現的快取機制
- 天氣數據緩存
- 預測結果緩存
- 靜態資源優化
```

### 3. 監控和告警
```bash
# 使用診斷工具定期檢查
python diagnose.py https://burnsky-api.onrender.com

# 檢查網站健康狀態
./adsense_verify.sh  # 選擇選項 3
```

## 🚨 緊急故障排除

### 網站完全無法訪問
1. 檢查 Render Dashboard: https://dashboard.render.com/
2. 查看部署日誌是否有錯誤
3. 確認服務狀態為 "Live"
4. 運行診斷工具: `python diagnose.py`

### 網站很慢但可以訪問
1. 這是正常的冷啟動，等待 30-60 秒
2. 啟動保活服務防止再次發生
3. 考慮升級到付費方案

### 部分功能無法使用
1. 檢查最新部署是否成功
2. 查看應用日誌
3. 重新部署: `./update.sh`

## 📱 快速檢查工具

### 網站狀態檢查
```bash
# 快速檢查
curl -w "響應時間: %{time_total}s\n" -s -o /dev/null https://burnsky-api.onrender.com

# 詳細診斷
python diagnose.py https://burnsky-api.onrender.com

# 功能測試
python test_deployment.py https://burnsky-api.onrender.com
```

### 自動化解決方案
```bash
# 一鍵啟動保活
./keep_alive.sh &

# 一鍵診斷和修復
./diagnose_and_fix.sh  # (如需要可創建)
```

## 💰 升級建議

如果您的網站使用量增加，建議升級到 Render 付費方案：

**何時升級**:
- 每日訪問量 > 100
- 需要 24/7 可用性
- AdSense 收入足以覆蓋成本

**升級步驟**:
1. 前往 Render Dashboard
2. 選擇您的服務
3. 點擊 "Settings" → "Plan"
4. 選擇 "Starter" 或更高方案

---

**記住**: 免費方案的限制是正常的，我們提供的保活工具可以大大減少問題發生！
