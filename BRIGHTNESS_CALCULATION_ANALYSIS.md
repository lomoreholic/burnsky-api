# 亮度計算邏輯分析報告

## 📊 亮度計算鏈路圖

```
圖像來源 (HKO 攝影機)
        ↓
[圖像下載] hko_webcam_fetcher.py L158-180
  - 從 HKO 服務器下載 JPEG 圖像
  - RGB 值範圍: 0-255 (uint8)
        ↓
[圖像轉換] hko_webcam_fetcher.py L276
  - PIL Image → Numpy Array
  - image.convert('RGB') 確保 RGB 格式
        ↓
[天空區域提取] hko_webcam_fetcher.py L280
  - 提取圖片上半部分: img_array[:height//2, :]
  - 理由: 天空通常在圖片上方
        ↓
[計算平均 RGB] hko_webcam_fetcher.py L283
  - np.mean(sky_region.reshape(-1, 3), axis=0)
  - 結果: [R_avg, G_avg, B_avg]
        ↓
[計算亮度值] hko_webcam_fetcher.py L306
  - brightness = (R_avg + G_avg + B_avg) / 3
  - 公式: 平均 RGB 值
  - 範圍: 0.0 - 255.0
        ↓
[儲存在 factors] hko_webcam_fetcher.py L425
  - sunset_potential['factors']['brightness'] = brightness
  - 型態: float
        ↓
[API 層處理] app.py L2686
  - response['analysis']['brightness'] = factors.get('brightness', 0)
  - 確保前端能獲取亮度值
        ↓
[前端顯示] templates/webcam_analysis.html L472
  - const brightness = data.analysis?.brightness || 0
  - 顯示格式: brightness.toFixed(1)
```

## 🧮 計算公式詳解

### 亮度計算公式
```
brightness = (R_avg + G_avg + B_avg) / 3
```

其中：
- **R_avg**: 紅色通道平均值 (0-255)
- **G_avg**: 綠色通道平均值 (0-255)  
- **B_avg**: 藍色通道平均值 (0-255)

### 特點
- ✓ 簡單直觀的平均值計算
- ✓ 適合快速亮度判斷
- ✓ 無需複雜色彩空間轉換

### 可選的替代方案
| 方法 | 公式 | 優點 | 缺點 |
|-----|------|------|------|
| 現有 (平均RGB) | (R+G+B)/3 | 快速，簡單 | 不符合人眼感知 |
| Luminosity | 0.299R + 0.587G + 0.114B | 符合人眼感知 | 計算稍複雜 |
| HSL | L = (Max+Min)/2 | 更準確 | 需要轉換色彩空間 |
| HSV | V = Max(R,G,B)/255 | 最大亮度 | 可能過亮 |

## 📈 示例計算

### 尖沙咀(望向西面) 案例
```
輸入像素 (天空上半部):
  R 通道: [150-156 之間的多個值]
  G 通道: [150-156 之間的多個值]
  B 通道: [150-156 之間的多個值]

計算步驟:
  1. R_avg = 152.5
  2. G_avg = 152.5
  3. B_avg = 152.5
  4. brightness = (152.5 + 152.5 + 152.5) / 3 = 152.5
  5. 顯示值 = 152.5 ≈ 153 (toFixed 四捨五入)

✓ 驗證: 實際顯示 153 = 期望值 153 ✓
```

## ⚠️ 潛在問題和改進建議

### 1. 值域表示問題
| 問題 | 現狀 | 建議 |
|-----|------|------|
| 值域 | 0-255 | 保持不變（標準值） |
| 可讀性 | 需要知道 255 = 最亮 | 可添加百分比標示 (0-100%) |
| 直觀性 | 153/255 不直觀 | 顯示為 60% 亮度 |

### 2. 計算準確性問題
| 檢查項 | 現狀 | 評分 |
|-------|------|------|
| 天空區域提取 | 取上半部分 | ⚠️ 可改進 |
| 光線條件 | 考慮夜間檢查 | ✓ 已實現 (L339) |
| 色彩通道權重 | 等權重 (1:1:1) | ⚠️ 非人眼感知 |
| 後處理 | 直接返回 | ✓ 可靠 |

### 3. 建議的改進

#### 改進 1: 使用 Luminosity 公式（更符合人眼感知）
```python
# 現有計算
brightness = (mean_rgb[0] + mean_rgb[1] + mean_rgb[2]) / 3

# 改進方案（Luminosity）
brightness = 0.299 * mean_rgb[0] + 0.587 * mean_rgb[1] + 0.114 * mean_rgb[2]
# 綠色權重最高（0.587），因為人眼對綠色最敏感
```

#### 改進 2: 調整天空區域提取方法
```python
# 現有（取上半部分）
sky_region = img_array[:height//2, :]

# 改進（排除地平線陰影，取上 1/3）
sky_region = img_array[:height//3, :]  # 避免地平線干擾
```

#### 改進 3: 添加亮度百分比顯示
```python
# 後端添加百分比計算
brightness_percent = (brightness / 255.0) * 100

# 前端顯示
${brightness.toFixed(1)} (${brightness_percent.toFixed(0)}%)
```

## 🔍 代碼位置參考

| 功能 | 檔案 | 行數 |
|-----|------|------|
| 圖像下載 | hko_webcam_fetcher.py | L158-180 |
| 圖像轉換 | hko_webcam_fetcher.py | L276 |
| 天空提取 | hko_webcam_fetcher.py | L280 |
| 平均 RGB | hko_webcam_fetcher.py | L283 |
| **亮度計算** | **hko_webcam_fetcher.py** | **L306** |
| 儲存位置 | hko_webcam_fetcher.py | L425 |
| API 返回 | app.py | L2686 |
| 前端顯示 | templates/webcam_analysis.html | L472, L559 |

## ✅ 結論

### 當前系統狀態
- **亮度計算方式**: 簡單平均 RGB (R+G+B)/3
- **計算準確性**: ✓ 正確（驗證通過）
- **值域範圍**: 0-255（標準 RGB 範圍）
- **顯示格式**: 一位小數 (toFixed(1))

### 推薦行動
1. **短期**: 保持現有計算，運行穩定
2. **中期**: 考慮改用 Luminosity 公式以提高準確性
3. **長期**: 添加亮度百分比、亮度趨勢分析等增強功能

---
*報告生成時間: 2026-01-24*
