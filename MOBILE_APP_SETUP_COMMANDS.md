# 🚀 燒天預測 Mobile App 設置指令

## 📋 開發環境準備

### 1. 安裝必要工具

```bash
# 安裝 Node.js (如果還沒有)
brew install node

# 安裝 Expo CLI
npm install -g expo-cli

# 安裝 EAS CLI (用於構建)
npm install -g @expo/eas-cli

# 驗證安裝
expo --version
node --version
npm --version
```

### 2. 創建新項目

```bash
# 創建項目文件夾
mkdir burnsky-mobile-app
cd burnsky-mobile-app

# 初始化 Expo 項目
expo init BurnSkyApp --template expo-template-blank-typescript

# 進入項目目錄
cd BurnSkyApp

# 安裝額外依賴
npm install @react-navigation/native @react-navigation/bottom-tabs
npm install @react-navigation/stack @react-navigation/native-stack
npm install react-native-maps
npm install @tanstack/react-query
npm install expo-notifications
npm install expo-location
npm install expo-constants
npm install react-native-safe-area-context
npm install react-native-screens
```

### 3. 配置項目

```bash
# 初始化 EAS
eas init

# 配置 app.json
# (我會幫您創建完整的配置)

# 啟動開發服務器
expo start
```

### 4. 在手機上測試

1. **下載 Expo Go app**
   - iOS: App Store 搜索 "Expo Go"
   - Android: Google Play 搜索 "Expo Go"

2. **掃描 QR 碼**
   - 運行 `expo start` 後會顯示 QR 碼
   - 用手機掃描即可在手機上看到應用

## 📱 項目結構預覽

```
BurnSkyApp/
├── App.tsx                 # 主應用入口
├── app.json               # Expo 配置
├── package.json           # 依賴管理
├── src/
│   ├── components/        # 重用組件
│   │   ├── PredictionCard.tsx
│   │   ├── LocationMap.tsx
│   │   └── WeatherChart.tsx
│   ├── screens/          # 應用頁面
│   │   ├── HomeScreen.tsx
│   │   ├── MapScreen.tsx
│   │   ├── SettingsScreen.tsx
│   │   └── CommunityScreen.tsx
│   ├── services/         # API 服務
│   │   ├── api.ts
│   │   ├── location.ts
│   │   └── notifications.ts
│   ├── types/           # TypeScript 類型
│   │   └── index.ts
│   ├── utils/           # 工具函數
│   │   └── helpers.ts
│   └── constants/       # 常量
│       └── Colors.ts
├── assets/              # 圖片資源
└── ios/ & android/      # 原生代碼 (自動生成)
```

## 🎨 首個功能：燒天預測首頁

我會先幫您實現：

1. **📱 主頁面** - 顯示燒天預測評分
2. **🌐 API 整合** - 連接您現有的燒天預測 API
3. **📍 定位功能** - 獲取用戶位置
4. **🎨 UI 設計** - 美觀的燒天預測卡片

## 🚀 準備好了嗎？

請執行以下步驟：

1. **打開終端**，運行上面的安裝指令
2. **創建新文件夾** `burnsky-mobile-app`
3. **在 VS Code 中打開** 該文件夾
4. **告訴我** 您已經準備好，我會立即開始創建應用！

讓我們把您的燒天預測系統變成一個amazing的手機應用！🔥📱
