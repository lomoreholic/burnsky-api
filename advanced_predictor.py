import numpy as np
import pandas as pd
from datetime import datetime, timedelta, time
from astral import LocationInfo
from astral.sun import sun
import pickle
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, accuracy_score
import warnings
import pytz
warnings.filterwarnings('ignore')

class AdvancedBurnskyPredictor:
    def __init__(self):
        """初始化進階燒天預測器"""
        # 香港地理位置
        self.hong_kong = LocationInfo("Hong Kong", "Hong Kong", "Asia/Hong_Kong", 22.3193, 114.1694)
        
        # 機器學習模型
        self.regression_model = None
        self.classification_model = None
        self.scaler = StandardScaler()
        
        # 雲層類型映射
        self.cloud_types = {
            '晴朗': {'score': 20, 'type': 'clear'},
            '天晴': {'score': 20, 'type': 'clear'},
            '大致天晴': {'score': 18, 'type': 'mostly_clear'},
            '部分時間有陽光': {'score': 16, 'type': 'partly_sunny'},
            '短暫時間有陽光': {'score': 15, 'type': 'brief_sunny'},
            '多雲': {'score': 14, 'type': 'cloudy'},
            '大致多雲': {'score': 12, 'type': 'mostly_cloudy'},
            '密雲': {'score': 8, 'type': 'overcast'},
            '陰天': {'score': 6, 'type': 'overcast'},
            '有雨': {'score': 4, 'type': 'rainy'},
            '大雨': {'score': 2, 'type': 'heavy_rain'},
            '暴雨': {'score': 1, 'type': 'storm'},
            '雷暴': {'score': 3, 'type': 'thunderstorm'}
        }
        
        # 載入已訓練的模型（如果存在）
        self.load_models()
    
    def get_sunset_info(self, date=None):
        """獲取精確的日出日落時間"""
        if date is None:
            # 使用香港時區的當前日期
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            date = datetime.now(hk_tz).date()
        
        try:
            # 設定香港時區
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            s = sun(self.hong_kong.observer, date=date)
            
            # 轉換為香港時間
            sunset_time = s['sunset'].astimezone(hk_tz).replace(tzinfo=None)
            sunrise_time = s['sunrise'].astimezone(hk_tz).replace(tzinfo=None)
            
            return {
                'sunset': sunset_time,
                'sunrise': sunrise_time,
                'sunset_str': sunset_time.strftime('%H:%M'),
                'sunrise_str': sunrise_time.strftime('%H:%M')
            }
        except Exception as e:
            # 如果 astral 失敗，使用估算值
            month = date.month
            if 4 <= month <= 9:  # 夏季
                sunset_time = datetime.combine(date, datetime.min.time().replace(hour=19, minute=15))
                sunrise_time = datetime.combine(date, datetime.min.time().replace(hour=6, minute=0))
            else:  # 冬季
                sunset_time = datetime.combine(date, datetime.min.time().replace(hour=18, minute=0))
                sunrise_time = datetime.combine(date, datetime.min.time().replace(hour=7, minute=0))
            
            return {
                'sunset': sunset_time,
                'sunrise': sunrise_time,
                'sunset_str': sunset_time.strftime('%H:%M'),
                'sunrise_str': sunrise_time.strftime('%H:%M'),
                'note': '使用估算時間'
            }
    
    def get_sunrise_info(self, date=None):
        """獲取精確的日出時間"""
        if date is None:
            # 使用香港時區的當前日期
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            date = datetime.now(hk_tz).date()
        
        try:
            # 設定香港時區
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            s = sun(self.hong_kong.observer, date=date)
            
            # 轉換為香港時間
            sunrise_time = s['sunrise'].astimezone(hk_tz).replace(tzinfo=None)
            
            return {
                'sunrise': sunrise_time,
                'sunrise_str': sunrise_time.strftime('%H:%M')
            }
        except Exception as e:
            # 如果 astral 失敗，使用估算值
            month = date.month
            if 4 <= month <= 9:  # 夏季
                sunrise_time = datetime.combine(date, datetime.min.time().replace(hour=6, minute=0))
            else:  # 冬季
                sunrise_time = datetime.combine(date, datetime.min.time().replace(hour=7, minute=0))
            
            return {
                'sunrise': sunrise_time,
                'sunrise_str': sunrise_time.strftime('%H:%M'),
                'note': '使用估算時間'
            }

    def get_sunrise_sunset_info(self, date=None):
        """獲取詳細的日出日落時間信息"""
        if date is None:
            # 使用香港時區的當前日期
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            date = datetime.now(hk_tz).date()
        
        try:
            # 設定香港時區
            hk_tz = pytz.timezone('Asia/Hong_Kong')
            s = sun(self.hong_kong.observer, date=date)
            
            # 確保時區正確 - 轉換為香港時間
            sunrise_time = s['sunrise'].astimezone(hk_tz).replace(tzinfo=None)
            sunset_time = s['sunset'].astimezone(hk_tz).replace(tzinfo=None)
            
            return {
                'sunrise': sunrise_time,
                'sunset': sunset_time,
                'sunrise_str': sunrise_time.strftime('%H:%M'),
                'sunset_str': sunset_time.strftime('%H:%M'),
                'date': date.strftime('%Y-%m-%d')
            }
        except Exception as e:
            # 備用計算
            month = date.month
            if 4 <= month <= 9:  # 夏季
                sunrise_time = datetime.combine(date, time(6, 0))
                sunset_time = datetime.combine(date, time(19, 15))
            else:  # 冬季
                sunrise_time = datetime.combine(date, time(7, 0))
                sunset_time = datetime.combine(date, time(18, 0))
            
            return {
                'sunrise': sunrise_time,
                'sunset': sunset_time,
                'sunrise_str': sunrise_time.strftime('%H:%M'),
                'sunset_str': sunset_time.strftime('%H:%M'),
                'date': date.strftime('%Y-%m-%d'),
                'error': f'使用備用計算: {str(e)}'
            }
    
    def calculate_time_factor_advanced(self, current_time=None):
        """計算進階時間因子 - 保持向後兼容性"""
        return self.calculate_advanced_time_factor('sunset', 0)
    
    def calculate_advanced_time_factor(self, prediction_type='sunset', advance_hours=2):
        """進階時間因子計算 - 基於實際日落時間"""
        # 強制使用香港時區
        hk_tz = pytz.timezone('Asia/Hong_Kong')
        current_time = datetime.now(hk_tz).replace(tzinfo=None)
        prediction_time = current_time + timedelta(hours=advance_hours)
        
        # 獲取預測時間當天的日出或日落時間
        if prediction_type == 'sunrise':
            time_info = self.get_sunrise_info(prediction_time.date())
            target_time = time_info['sunrise']
            time_label = '日出'
            time_str = time_info['sunrise_str']
        else:  # sunset
            time_info = self.get_sunset_info(prediction_time.date())
            target_time = time_info['sunset']
            time_label = '日落'
            time_str = time_info['sunset_str']
        
        # 計算預測時間與目標時間的差距（分鐘）
        time_diff_minutes = abs((prediction_time - target_time).total_seconds() / 60)
        
        # 評分邏輯 - 基於預測時間是否接近燒天最佳時段
        if time_diff_minutes <= 30:  # 目標時間前後30分鐘
            score = 20
            description = f"黃金時段！預測時間距離{time_label}({time_str}) {int(time_diff_minutes)}分鐘"
        elif time_diff_minutes <= 60:  # 目標時間前後1小時
            score = 15
            description = f"良好時段，預測時間距離{time_label}({time_str}) {int(time_diff_minutes)}分鐘"
        elif time_diff_minutes <= 120:  # 目標時間前後2小時
            score = 10
            description = f"可接受時段，預測時間距離{time_label}({time_str}) {int(time_diff_minutes)}分鐘"
        else:
            score = 5
            description = f"非理想時段，預測時間距離{time_label}({time_str}) {int(time_diff_minutes)}分鐘"
        
        # 額外加分：最佳時段
        time_diff_signed = (prediction_time - target_time).total_seconds() / 60
        if prediction_type == 'sunset':
            # 日落前15分鐘到日落後45分鐘為最佳
            if -15 <= time_diff_signed <= 45:
                score += 5
                description += " (最佳燒天時段)"
        else:  # sunrise
            # 日出前45分鐘到日出後15分鐘為最佳
            if -45 <= time_diff_signed <= 15:
                score += 5
                description += " (最佳燒天時段)"
        
        return {
            'score': min(25, score),  # 最高25分
            'description': description,
            'target_time': time_str,
            'target_type': time_label,
            'current_time': current_time.strftime('%H:%M'),
            'prediction_time': prediction_time.strftime('%H:%M'),
            'time_diff_minutes': int(time_diff_minutes),
            'advance_hours': advance_hours
        }
    
    def analyze_cloud_types(self, weather_description):
        """從天氣描述中分析雲層類型"""
        if not weather_description:
            return {'score': 0, 'description': '無天氣描述'}
        
        description = weather_description
        detected_types = []
        total_score = 0
        
        # 檢測關鍵詞
        for keyword, info in self.cloud_types.items():
            if keyword in description:
                detected_types.append({
                    'type': keyword,
                    'cloud_type': info['type'],
                    'score': info['score']
                })
                total_score += info['score']
        
        # 特殊燒天有利條件
        burnsky_favorable = []
        if '多雲' in description and '部分時間有陽光' in description:
            burnsky_favorable.append('理想雲量配置')
            total_score += 5
        
        if '短暫時間有陽光' in description:
            burnsky_favorable.append('間歇性陽光')
            total_score += 3
        
        if '酷熱' in description or '炎熱' in description:
            burnsky_favorable.append('高溫有利條件')
            total_score += 2
        
        # 不利條件
        unfavorable = []
        if '大雨' in description or '暴雨' in description:
            unfavorable.append('大雨影響')
            total_score -= 10
        
        if '雷暴' in description:
            unfavorable.append('雷暴天氣')
            total_score -= 5
        
        # 計算最終分數
        if detected_types:
            avg_score = total_score / len(detected_types)
        else:
            avg_score = 10  # 預設分數
        
        final_score = max(0, min(25, avg_score))  # 限制在0-25分
        
        analysis = f"檢測到雲層類型: {', '.join([t['type'] for t in detected_types])}"
        if burnsky_favorable:
            analysis += f" | 有利條件: {', '.join(burnsky_favorable)}"
        if unfavorable:
            analysis += f" | 不利條件: {', '.join(unfavorable)}"
        
        return {
            'score': final_score,
            'description': analysis,
            'detected_types': detected_types,
            'favorable_conditions': burnsky_favorable,
            'unfavorable_conditions': unfavorable
        }
    
    def generate_training_data(self, num_samples=1000):
        """生成訓練數據（模擬歷史燒天數據）"""
        np.random.seed(42)  # 確保可重現性
        
        data = []
        
        # 確保每個類別都有足夠的樣本
        samples_per_class = num_samples // 3
        
        for class_type in [0, 1, 2]:  # 低、中、高機率
            for i in range(samples_per_class):
                if class_type == 0:  # 低機率燒天條件
                    temperature = np.random.normal(25, 3)  # 較低溫度
                    humidity = np.random.normal(80, 10)    # 較高濕度
                    uv_index = np.random.gamma(1, 1.5)     # 較低UV
                    rainfall = np.random.exponential(3)    # 較多降雨
                    time_factor = np.random.beta(1, 4)     # 較差時間
                    cloud_score = np.random.normal(8, 3)   # 較差雲層
                    target_score_range = (10, 35)
                    
                elif class_type == 1:  # 中機率燒天條件
                    temperature = np.random.normal(28, 2)  # 適中溫度
                    humidity = np.random.normal(75, 8)     # 適中濕度
                    uv_index = np.random.gamma(2, 2)       # 適中UV
                    rainfall = np.random.exponential(1.5)  # 少量降雨
                    time_factor = np.random.beta(2, 3)     # 一般時間
                    cloud_score = np.random.normal(12, 3)  # 一般雲層
                    target_score_range = (35, 65)
                    
                else:  # 高機率燒天條件
                    temperature = np.random.normal(30, 2)  # 較高溫度
                    humidity = np.random.normal(70, 8)     # 適中偏低濕度
                    uv_index = np.random.gamma(3, 2)       # 較高UV
                    rainfall = np.random.exponential(0.8)  # 很少降雨
                    time_factor = np.random.beta(4, 2)     # 較好時間
                    cloud_score = np.random.normal(16, 3)  # 較好雲層
                    target_score_range = (65, 90)
                
                # 確保值在合理範圍內
                temperature = max(15, min(40, temperature))
                humidity = max(30, min(95, humidity))
                uv_index = max(0, min(15, uv_index))
                rainfall = max(0, rainfall)
                wind_speed = np.random.gamma(1.5, 2)
                time_factor = max(0, min(1, time_factor))
                cloud_score = max(0, min(20, cloud_score))
                
                # 計算燒天指數（基於改良經驗公式）
                # 溫度貢獻：最佳範圍 26-32度
                temp_score = max(0, 25 - abs(temperature - 29) * 1.5)
                
                # 濕度貢獻：最佳範圍 60-80%
                humid_score = max(0, 25 - abs(humidity - 70) * 0.25)
                
                # UV貢獻：適中UV有利
                uv_score = min(uv_index * 1.5, 15)
                
                # 降雨懲罰
                rain_penalty = max(15 - rainfall * 1.5, 0)
                
                # 時間加權
                time_score = time_factor * 20
                
                # 雲層貢獻
                cloud_contribution = cloud_score * 0.8
                
                # 綜合分數計算
                burnsky_score = (
                    temp_score * 0.25 +      # 溫度25%
                    humid_score * 0.2 +      # 濕度20%
                    uv_score * 0.15 +        # UV 15%
                    rain_penalty * 0.15 +    # 降雨15%
                    time_score * 0.15 +      # 時間15%
                    cloud_contribution * 0.1  # 雲層10%
                )
                
                # 調整分數以符合目標範圍
                min_target, max_target = target_score_range
                if burnsky_score < min_target:
                    burnsky_score = np.random.uniform(min_target, min_target + 5)
                elif burnsky_score > max_target:
                    burnsky_score = np.random.uniform(max_target - 5, max_target)
                
                # 添加小量隨機變化
                burnsky_score += np.random.normal(0, 2)
                burnsky_score = max(0, min(100, burnsky_score))
                
                data.append({
                    'temperature': temperature,
                    'humidity': humidity,
                    'uv_index': uv_index,
                    'rainfall': rainfall,
                    'wind_speed': wind_speed,
                    'time_factor': time_factor,
                    'cloud_score': cloud_score,
                    'burnsky_score': burnsky_score,
                    'burnsky_class': class_type
                })
        
        # 添加剩餘樣本
        remaining_samples = num_samples - len(data)
        for i in range(remaining_samples):
            class_type = np.random.choice([0, 1, 2])
            # 重複上述邏輯（簡化版）
            if class_type == 0:
                temperature = np.random.normal(25, 3)
                burnsky_score = np.random.uniform(10, 35)
            elif class_type == 1:
                temperature = np.random.normal(28, 2)
                burnsky_score = np.random.uniform(35, 65)
            else:
                temperature = np.random.normal(30, 2)
                burnsky_score = np.random.uniform(65, 90)
            
            data.append({
                'temperature': max(15, min(40, temperature)),
                'humidity': np.random.normal(75, 10),
                'uv_index': np.random.gamma(2, 2),
                'rainfall': np.random.exponential(1.5),
                'wind_speed': np.random.gamma(1.5, 2),
                'time_factor': np.random.beta(2, 3),
                'cloud_score': np.random.normal(12, 4),
                'burnsky_score': burnsky_score,
                'burnsky_class': class_type
            })
        
        return pd.DataFrame(data)
    
    def train_models(self):
        """訓練機器學習模型"""
        print("🤖 正在生成訓練數據...")
        df = self.generate_training_data(1000)
        
        # 準備特徵
        features = ['temperature', 'humidity', 'uv_index', 'rainfall', 'wind_speed', 'time_factor', 'cloud_score']
        X = df[features]
        y_regression = df['burnsky_score']
        y_classification = df['burnsky_class']
        
        # 標準化特徵
        X_scaled = self.scaler.fit_transform(X)
        
        # 分割數據
        X_train, X_test, y_reg_train, y_reg_test = train_test_split(
            X_scaled, y_regression, test_size=0.2, random_state=42
        )
        
        _, _, y_cls_train, y_cls_test = train_test_split(
            X_scaled, y_classification, test_size=0.2, random_state=42
        )
        
        # 訓練回歸模型
        print("🌲 正在訓練 Random Forest 回歸模型...")
        self.regression_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.regression_model.fit(X_train, y_reg_train)
        
        # 訓練分類模型
        print("📊 正在訓練 Logistic Regression 分類模型...")
        self.classification_model = LogisticRegression(
            random_state=42,
            max_iter=1000
        )
        self.classification_model.fit(X_train, y_cls_train)
        
        # 評估模型
        reg_pred = self.regression_model.predict(X_test)
        cls_pred = self.classification_model.predict(X_test)
        
        reg_mse = mean_squared_error(y_reg_test, reg_pred)
        cls_acc = accuracy_score(y_cls_test, cls_pred)
        
        print(f"✅ 回歸模型 MSE: {reg_mse:.2f}")
        print(f"✅ 分類模型準確率: {cls_acc:.2f}")
        
        # 保存模型
        self.save_models()
        
        return {
            'regression_mse': reg_mse,
            'classification_accuracy': cls_acc,
            'feature_importance': dict(zip(features, self.regression_model.feature_importances_))
        }
    
    def save_models(self):
        """保存訓練好的模型"""
        try:
            with open('models/regression_model.pkl', 'wb') as f:
                pickle.dump(self.regression_model, f)
            
            with open('models/classification_model.pkl', 'wb') as f:
                pickle.dump(self.classification_model, f)
            
            with open('models/scaler.pkl', 'wb') as f:
                pickle.dump(self.scaler, f)
            
            print("💾 模型已保存到 models/ 目錄")
        except Exception as e:
            print(f"❌ 保存模型失敗: {e}")
    
    def load_models(self):
        """載入已訓練的模型"""
        try:
            if not os.path.exists('models'):
                os.makedirs('models')
                return False
            
            with open('models/regression_model.pkl', 'rb') as f:
                self.regression_model = pickle.load(f)
            
            with open('models/classification_model.pkl', 'rb') as f:
                self.classification_model = pickle.load(f)
            
            with open('models/scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
            
            print("✅ 已載入訓練好的模型")
            return True
        except Exception as e:
            print(f"⚠️ 載入模型失敗，將重新訓練: {e}")
            return False
    
    def predict_ml(self, weather_data, forecast_data):
        """使用機器學習模型進行預測"""
        # 如果模型不存在，先訓練
        if self.regression_model is None or self.classification_model is None:
            print("🤖 模型不存在，正在訓練...")
            self.train_models()
        
        # 提取特徵
        features = self.extract_features(weather_data, forecast_data)
        
        # 標準化
        features_scaled = self.scaler.transform([list(features.values())])
        
        # 預測
        regression_pred = self.regression_model.predict(features_scaled)[0]
        classification_pred = self.classification_model.predict(features_scaled)[0]
        classification_proba = self.classification_model.predict_proba(features_scaled)[0]
        
        # 特徵重要性
        feature_names = ['temperature', 'humidity', 'uv_index', 'rainfall', 'wind_speed', 'time_factor', 'cloud_score']
        importance = dict(zip(feature_names, self.regression_model.feature_importances_))
        
        return {
            'ml_burnsky_score': max(0, min(100, regression_pred)),
            'ml_class': classification_pred,
            'ml_class_probabilities': {
                'low': classification_proba[0],
                'medium': classification_proba[1] if len(classification_proba) > 1 else 0,
                'high': classification_proba[2] if len(classification_proba) > 2 else 0
            },
            'feature_importance': importance,
            'input_features': features
        }
    
    def extract_features(self, weather_data, forecast_data):
        """從天氣數據中提取機器學習特徵"""
        features = {}
        
        # 溫度特徵
        if weather_data and 'temperature' in weather_data:
            temp_data = weather_data['temperature']['data']
            hko_temp = next((t['value'] for t in temp_data if t['place'] == '香港天文台'), None)
            if hko_temp:
                features['temperature'] = hko_temp
            else:
                features['temperature'] = np.mean([t['value'] for t in temp_data])
        else:
            features['temperature'] = 28  # 預設值
        
        # 濕度特徵
        if weather_data and 'humidity' in weather_data:
            humidity_data = weather_data['humidity']['data']
            hko_humidity = next((h['value'] for h in humidity_data if h['place'] == '香港天文台'), None)
            if hko_humidity:
                features['humidity'] = hko_humidity
            else:
                features['humidity'] = np.mean([h['value'] for h in humidity_data])
        else:
            features['humidity'] = 70  # 預設值
        
        # UV指數特徵
        if weather_data and 'uvindex' in weather_data:
            if isinstance(weather_data['uvindex'], dict) and 'data' in weather_data['uvindex'] and weather_data['uvindex']['data']:
                features['uv_index'] = weather_data['uvindex']['data'][0]['value']
            else:
                features['uv_index'] = 5  # 預設值
        else:
            features['uv_index'] = 5  # 預設值
        
        # 降雨量特徵
        if weather_data and 'rainfall' in weather_data:
            rainfall_data = weather_data['rainfall']['data']
            total_rainfall = sum([r.get('max', 0) for r in rainfall_data if r.get('max', 0) > 0])
            features['rainfall'] = total_rainfall
        else:
            features['rainfall'] = 0  # 預設值
        
        # 風速特徵（暫時使用預設值）
        features['wind_speed'] = 3  # 預設值
        
        # 時間因子
        time_result = self.calculate_time_factor_advanced()
        features['time_factor'] = time_result['score'] / 25  # 標準化到0-1
        
        # 雲層分數
        if forecast_data and 'forecastDesc' in forecast_data:
            cloud_result = self.analyze_cloud_types(forecast_data['forecastDesc'])
            features['cloud_score'] = cloud_result['score']
        else:
            features['cloud_score'] = 10  # 預設值
        
        return features
    
    def predict_burnsky_intensity(self, burnsky_score):
        """
        預測燒天強度等級
        
        Args:
            burnsky_score: 燒天分數 (0-100)
        
        Returns:
            dict: 包含強度等級、描述、可見度等信息
        """
        if burnsky_score >= 85:
            intensity = {
                'level': 5,
                'name': '極致燒天',
                'description': '天空將呈現絢爛的火紅色彩，層次豐富，持續時間長',
                'visibility': '極佳',
                'duration_estimate': '20-30分鐘',
                'photography_advice': '絕佳拍攝機會，建議多角度拍攝'
            }
        elif burnsky_score >= 70:
            intensity = {
                'level': 4,
                'name': '強烈燒天',
                'description': '天空將呈現明顯的紅橙色彩，色彩飽和度高',
                'visibility': '良好',
                'duration_estimate': '15-25分鐘',
                'photography_advice': '推薦拍攝，建議準備三腳架'
            }
        elif burnsky_score >= 55:
            intensity = {
                'level': 3,
                'name': '中等燒天',
                'description': '天空將出現明顯的暖色調，有一定的色彩層次',
                'visibility': '中等',
                'duration_estimate': '10-20分鐘',
                'photography_advice': '適合拍攝，注意光線變化'
            }
        elif burnsky_score >= 40:
            intensity = {
                'level': 2,
                'name': '輕微燒天',
                'description': '天空可能出現淡淡的暖色調，需要仔細觀察',
                'visibility': '一般',
                'duration_estimate': '5-15分鐘',
                'photography_advice': '可嘗試拍攝，建議調整相機設定'
            }
        else:
            intensity = {
                'level': 1,
                'name': '無明顯燒天',
                'description': '天空色彩變化不明顯，可能只有微弱的色彩變化',
                'visibility': '差',
                'duration_estimate': '0-10分鐘',
                'photography_advice': '不建議專程拍攝，可作為練習'
            }
        
        return intensity
    
    def predict_burnsky_colors(self, weather_data, forecast_data, burnsky_score):
        """
        預測燒天顏色組合
        
        Args:
            weather_data: 天氣數據
            forecast_data: 預報數據
            burnsky_score: 燒天分數
        
        Returns:
            dict: 包含主要顏色、次要顏色、色彩強度等信息
        """
        # 基於天氣條件分析顏色
        primary_colors = []
        secondary_colors = []
        color_intensity = 'low'
        
        # 基於濕度判斷色彩飽和度
        humidity = 70  # 預設值
        if weather_data and 'humidity' in weather_data:
            for h in weather_data['humidity']['data']:
                if h['place'] == '香港天文台':
                    humidity = h['value']
                    break
        
        # 基於雲層分析顏色
        cloud_analysis = self.analyze_cloud_types(
            forecast_data.get('forecastDesc', '') if forecast_data else ''
        )
        
        # 基於分數和條件預測顏色
        if burnsky_score >= 70:
            color_intensity = 'high'
            if humidity < 65:  # 低濕度 = 更鮮豔
                primary_colors = ['深紅', '橙紅', '金橙']
                secondary_colors = ['紫紅', '粉紅', '琥珀']
            else:
                primary_colors = ['橙紅', '紅橙', '暖橙']
                secondary_colors = ['粉橙', '淺紅', '金黃']
        
        elif burnsky_score >= 50:
            color_intensity = 'medium'
            primary_colors = ['橙色', '暖橙', '淺紅']
            secondary_colors = ['金黃', '粉橙', '淺粉']
        
        elif burnsky_score >= 30:
            color_intensity = 'low'
            primary_colors = ['淺橙', '暖黃', '粉橙']
            secondary_colors = ['淡黃', '淺粉', '米白']
        
        else:
            color_intensity = 'minimal'
            primary_colors = ['淡黃', '米白', '淺灰']
            secondary_colors = ['白色', '淺藍', '灰白']
        
        # 基於雲層類型調整顏色
        if 'detected_types' in cloud_analysis:
            for cloud_type in cloud_analysis['detected_types']:
                if cloud_type['cloud_type'] == 'clear':
                    # 晴朗天空 - 更鮮豔的顏色
                    if '深紅' not in primary_colors and burnsky_score >= 60:
                        primary_colors.insert(0, '深紅')
                elif cloud_type['cloud_type'] == 'thunderstorm':
                    # 雷暴 - 更戲劇性的顏色
                    if burnsky_score >= 50:
                        primary_colors.append('紫紅')
                        secondary_colors.append('深紫')
        
        # 色彩分佈預測
        color_distribution = {
            'primary_coverage': '60-80%' if color_intensity in ['high', 'medium'] else '30-50%',
            'secondary_coverage': '20-40%' if color_intensity in ['high', 'medium'] else '10-30%',
            'gradient_type': self._predict_gradient_type(burnsky_score, cloud_analysis)
        }
        
        return {
            'primary_colors': primary_colors[:3],  # 最多3種主要顏色
            'secondary_colors': secondary_colors[:3],  # 最多3種次要顏色
            'color_intensity': color_intensity,
            'color_distribution': color_distribution,
            'color_duration': self._estimate_color_duration(burnsky_score),
            'best_viewing_direction': self._suggest_viewing_direction(),
            'color_hex_codes': self._get_color_hex_codes(primary_colors + secondary_colors)
        }
    
    def _predict_gradient_type(self, burnsky_score, cloud_analysis):
        """預測色彩漸變類型"""
        if burnsky_score >= 70:
            return '放射狀漸變'  # 從地平線向上放射
        elif burnsky_score >= 50:
            return '水平漸變'  # 水平層次分明
        else:
            return '散射漸變'  # 散亂分佈
    
    def _estimate_color_duration(self, burnsky_score):
        """估算色彩持續時間"""
        if burnsky_score >= 80:
            return {'peak': '10-15分鐘', 'total': '25-35分鐘'}
        elif burnsky_score >= 60:
            return {'peak': '8-12分鐘', 'total': '20-30分鐘'}
        elif burnsky_score >= 40:
            return {'peak': '5-10分鐘', 'total': '15-25分鐘'}
        else:
            return {'peak': '3-8分鐘', 'total': '10-20分鐘'}
    
    def _suggest_viewing_direction(self):
        """建議最佳觀賞方向"""
        # 香港地理位置，建議觀賞方向
        return {
            'sunset': '西方至西南方',
            'sunrise': '東方至東南方',
            'best_spots': ['維多利亞港', '太平山頂', '西環海濱', '數碼港']
        }
    
    def _get_color_hex_codes(self, color_names):
        """將顏色名稱轉換為十六進制色碼"""
        color_map = {
            '深紅': '#B22222', '橙紅': '#FF4500', '金橙': '#FF8C00',
            '紫紅': '#DC143C', '粉紅': '#FF69B4', '琥珀': '#FFBF00',
            '橙色': '#FFA500', '暖橙': '#FF7F50', '淺紅': '#FF6347',
            '金黃': '#FFD700', '粉橙': '#FFAB91', '淺粉': '#FFB6C1',
            '淺橙': '#FFDAB9', '暖黃': '#FFF8DC', '淡黃': '#FFFFE0',
            '米白': '#F5F5DC', '淺灰': '#D3D3D3', '白色': '#FFFFFF',
            '淺藍': '#ADD8E6', '灰白': '#F8F8FF', '深紫': '#4B0082'
        }
        
        return {name: color_map.get(name, '#FFFFFF') for name in color_names if name in color_map}
