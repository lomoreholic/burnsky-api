# 燒天預測 React Native 應用架構

## 📱 應用結構

```
BurnskyApp/
├── src/
│   ├── components/          # 可重用組件
│   │   ├── ScoreCircle.js
│   │   ├── WeatherCard.js
│   │   ├── PredictionCard.js
│   │   └── LoadingSpinner.js
│   ├── screens/             # 頁面
│   │   ├── HomeScreen.js
│   │   ├── SettingsScreen.js
│   │   ├── HistoryScreen.js
│   │   └── CameraScreen.js
│   ├── services/            # API 服務
│   │   ├── apiService.js
│   │   ├── locationService.js
│   │   └── notificationService.js
│   ├── utils/               # 工具函數
│   │   ├── formatters.js
│   │   └── constants.js
│   └── navigation/          # 路由導航
│       └── AppNavigator.js
├── assets/                  # 靜態資源
│   ├── images/
│   ├── icons/
│   └── fonts/
├── android/                 # Android 特定代碼
├── ios/                     # iOS 特定代碼
└── package.json
```

## 🔧 技術棧

### 核心框架
- **React Native**: 0.72.x
- **React Navigation**: 路由導航
- **React Native Paper**: UI 組件庫
- **React Query**: 數據獲取和緩存

### 狀態管理
- **Redux Toolkit**: 全局狀態管理
- **AsyncStorage**: 本地數據存儲

### 原生功能
- **@react-native-async-storage/async-storage**: 本地存儲
- **@react-native-community/geolocation**: GPS 定位
- **react-native-push-notification**: 推送通知
- **react-native-camera**: 相機功能
- **react-native-share**: 分享功能

### 開發工具
- **Flipper**: 調試工具
- **ESLint + Prettier**: 代碼格式化
- **Jest**: 單元測試
- **Detox**: E2E 測試

## 📄 主要頁面設計

### 1. 首頁 (HomeScreen)
```javascript
// HomeScreen.js 示例結構
import React, { useEffect, useState } from 'react';
import { View, ScrollView, RefreshControl } from 'react-native';
import { ScoreCircle, WeatherCard, PredictionControls } from '../components';
import { apiService } from '../services';

const HomeScreen = () => {
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const loadPrediction = async () => {
    try {
      const data = await apiService.getPrediction();
      setPrediction(data);
    } catch (error) {
      console.error('載入預測失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView 
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={loadPrediction} />
      }
    >
      <ScoreCircle score={prediction?.burnsky_score} />
      <PredictionControls onUpdate={loadPrediction} />
      <WeatherCard data={prediction?.weather_data} />
    </ScrollView>
  );
};
```

### 2. 設定頁面 (SettingsScreen)
- 通知設定
- 預測偏好設定
- 關於頁面
- 用戶帳戶

### 3. 歷史記錄 (HistoryScreen)
- 燒天預測歷史
- 準確率統計
- 個人化分析

### 4. 相機頁面 (CameraScreen)
- 即時相機預覽
- 燒天相片拍攝
- 濾鏡功能

## 🎨 UI/UX 設計原則

### 設計系統
```javascript
// Design tokens
export const COLORS = {
  primary: '#667eea',
  secondary: '#764ba2',
  success: '#4CAF50',
  warning: '#FF9800',
  error: '#f44336',
  text: '#333333',
  background: '#f5f5f5',
};

export const TYPOGRAPHY = {
  h1: { fontSize: 28, fontWeight: 'bold' },
  h2: { fontSize: 24, fontWeight: '600' },
  body: { fontSize: 16, lineHeight: 24 },
  caption: { fontSize: 12, color: COLORS.text + '80' },
};
```

### 組件設計
- Material Design 3 風格
- 一致的間距系統 (8px 基準)
- 響應式設計
- 深色模式支援

## 🔄 API 整合

### API 服務層
```javascript
// apiService.js
class ApiService {
  constructor() {
    this.baseURL = 'https://burnsky.app/api';
  }

  async getPrediction(type = 'sunset', advanceHours = 2) {
    const response = await fetch(`${this.baseURL}/predict/${type}?advance_hours=${advanceHours}`);
    return response.json();
  }

  async getWeatherData() {
    const response = await fetch(`${this.baseURL}/weather`);
    return response.json();
  }
}

export const apiService = new ApiService();
```

## 📲 推送通知策略

### 通知類型
1. **高燒天機率提醒** (分數 > 70)
2. **每日最佳時段提醒**
3. **個人化預測更新**
4. **社群分享提醒**

### 實現方式
```javascript
// notificationService.js
import PushNotification from 'react-native-push-notification';

export const scheduleHighBurnskyAlert = (score, time) => {
  if (score > 70) {
    PushNotification.localNotificationSchedule({
      title: '🔥 高燒天機率警報！',
      message: `預測分數: ${score}, 最佳觀賞時間: ${time}`,
      date: new Date(time),
    });
  }
};
```

## 🚀 部署流程

### 開發環境設置
```bash
# 1. 安裝 React Native CLI
npm install -g react-native-cli

# 2. 創建新項目
npx react-native init BurnskyApp

# 3. 安裝依賴
cd BurnskyApp
npm install

# 4. iOS 依賴
cd ios && pod install

# 5. 啟動開發服務器
npx react-native start

# 6. 運行應用
npx react-native run-ios
npx react-native run-android
```

### 應用商店發布
```bash
# iOS (需要 Mac + Xcode)
# 1. 配置 App Store Connect
# 2. 設置證書和 Provisioning Profile
# 3. 構建和上傳

# Android
# 1. 生成簽名密鑰
keytool -genkey -v -keystore burnsky-key.keystore -alias burnsky -keyalg RSA -keysize 2048 -validity 10000

# 2. 構建 APK
cd android && ./gradlew assembleRelease

# 3. 上傳到 Google Play Console
```

## 💡 創新功能建議

### 1. AR 燒天預覽
- 使用手機相機實時預覽
- 疊加燒天機率資訊
- 最佳拍攝角度建議

### 2. 社群功能
- 用戶分享燒天照片
- 社群評分系統
- 攝影技巧交流

### 3. 智能提醒
- 基於用戶習慣的個人化提醒
- 天氣變化警報
- 最佳出行路線建議

### 4. 離線功能
- 離線天氣數據緩存
- 基本預測功能
- 預載常用地點資料

## 📊 Analytics 和監控

### 用戶行為追蹤
- App 使用時長
- 功能使用頻率
- 預測準確率反饋
- 用戶滿意度調查

### 技術監控
- Crash 報告 (Crashlytics)
- 性能監控 (Performance monitoring)
- API 響應時間
- 用戶留存率

## 🎯 發布時間表

### Phase 1: MVP (3個月)
- [ ] 基本燒天預測功能
- [ ] 簡潔 UI 設計
- [ ] iOS + Android 版本

### Phase 2: 增強版 (6個月)
- [ ] 推送通知
- [ ] 歷史記錄
- [ ] 個人化設定
- [ ] 付費功能

### Phase 3: 社群版 (12個月)
- [ ] 用戶帳戶系統
- [ ] 照片分享功能
- [ ] 社群互動
- [ ] AR 功能

---

這個架構提供了一個完整的移動應用開發計劃，從技術選擇到實際實現都有詳細規劃。
