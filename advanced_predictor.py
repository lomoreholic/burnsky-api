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
            
            # 修復 astral 庫的日期錯誤：確保時間在正確的日期
            if sunset_time.date() != date:
                correct_sunset = datetime.combine(date, sunset_time.time())
                sunset_time = correct_sunset
            
            if sunrise_time.date() != date:
                correct_sunrise = datetime.combine(date, sunrise_time.time())
                sunrise_time = correct_sunrise
            
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
            
            # 修復 astral 庫的日期錯誤：確保日出時間在正確的日期
            if sunrise_time.date() != date:
                # 如果 astral 返回的日期不對，手動調整到正確日期
                correct_sunrise = datetime.combine(date, sunrise_time.time())
                sunrise_time = correct_sunrise
            
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
            
            # 修復 astral 庫的日期錯誤：確保時間在正確的日期
            if sunrise_time.date() != date:
                # 如果 astral 返回的日期不對，手動調整到正確日期
                correct_sunrise = datetime.combine(date, sunrise_time.time())
                sunrise_time = correct_sunrise
            
            if sunset_time.date() != date:
                # 如果 astral 返回的日期不對，手動調整到正確日期
                correct_sunset = datetime.combine(date, sunset_time.time())
                sunset_time = correct_sunset
            
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
        prediction_date = prediction_time.date()
        
        if prediction_type == 'sunrise':
            time_info = self.get_sunrise_info(prediction_date)
            target_time = time_info['sunrise']
            time_label = '日出'
            time_str = time_info['sunrise_str']
        else:  # sunset
            time_info = self.get_sunset_info(prediction_date)
            target_time = time_info['sunset']
            time_label = '日落'
            time_str = time_info['sunset_str']
        
        # 確保target_time是在預測日期的正確時間
        if target_time.date() != prediction_date:
            # 如果日期不匹配，手動校正
            correct_time = datetime.combine(prediction_date, target_time.time())
            target_time = correct_time
        
        # 計算預測時間與目標時間的差距（分鐘）
        time_diff_signed = (target_time - prediction_time).total_seconds() / 60  # 正數表示還未到時間，負數表示已過時間
        time_diff_minutes = abs(time_diff_signed)
        
        # 生成清楚的時間描述
        if time_diff_signed > 0:
            hours = int(time_diff_signed // 60)
            minutes = int(time_diff_signed % 60)
            if hours > 0:
                time_desc = f"還有 {hours}小時{minutes}分鐘 到{time_label}"
            else:
                time_desc = f"還有 {minutes}分鐘 到{time_label}"
        else:
            hours = int(time_diff_minutes // 60)
            minutes = int(time_diff_minutes % 60)
            if hours > 0:
                time_desc = f"{time_label}已過 {hours}小時{minutes}分鐘"
            else:
                time_desc = f"{time_label}已過 {minutes}分鐘"
        
        # 評分邏輯 - 調整為18分滿分（降低時間因子權重）
        if time_diff_minutes <= 30:  # 目標時間前後30分鐘
            score = 15
            description = f"黃金時段！{time_desc}({time_str})"
        elif time_diff_minutes <= 60:  # 目標時間前後1小時
            score = 12
            description = f"良好時段，{time_desc}({time_str})"
        elif time_diff_minutes <= 120:  # 目標時間前後2小時
            score = 8
            description = f"可接受時段，{time_desc}({time_str})"
        else:
            score = 4
            description = f"非理想時段，{time_desc}({time_str})"
        
        # 額外加分：最佳時段 - 優化日落前1小時預測
        if prediction_type == 'sunset':
            # 日落前1小時到日落後45分鐘為最佳，日落前1小時特別加分
            if -90 <= -time_diff_signed <= 45:  
                if -90 <= -time_diff_signed <= -45:  # 日落前1.5小時到45分鐘，黃金預測時段
                    score += 3  # 適度加分（降低至18分滿分範圍）
                    description += " ⭐黃金預測時段⭐"
                elif -45 <= -time_diff_signed <= 0:  # 日落前45分鐘到日落
                    score += 3  # 降低加分（18分滿分）
                    description += " (最佳燒天時段)"
                else:  # 日落後
                    score += 2  # 降低加分（18分滿分）
                    description += " (燒天持續時段)"
        else:  # sunrise
            # 日出前1小時到日出後15分鐘為最佳，日出前1小時特別加分
            if -90 <= -time_diff_signed <= 15:  
                if -90 <= -time_diff_signed <= -45:  # 日出前1.5小時到45分鐘，黃金預測時段
                    score += 3  # 降低加分（18分滿分）
                    description += " ⭐黃金預測時段⭐"
                elif -45 <= -time_diff_signed <= 0:  # 日出前45分鐘到日出
                    score += 3  # 降低加分（18分滿分）
                    description += " (最佳燒天時段)"
                else:  # 日出後
                    score += 2  # 降低加分（18分滿分）
                    description += " (燒天持續時段)"
        
        # 早晨專屬加分 - 日出前特殊條件（移除額外加分，保持18分上限）
        if prediction_type == 'sunrise':
            # 日出前1小時15分鐘到45分鐘是最理想的預測時段（移除額外加分）
            pass
        
        return {
            'score': round(min(18, score)),  # 限制最高分數為18分（已調整）
            'description': description,
            'target_time': time_str,
            'target_type': time_label,
            'current_time': current_time.strftime('%H:%M'),
            'prediction_time': prediction_time.strftime('%H:%M'),
            'time_diff_minutes': int(time_diff_minutes),
            'advance_hours': advance_hours
        }
    
    def analyze_cloud_types(self, weather_description):
        """從天氣描述中分析雲層類型 - 增強版，考慮雲層厚度對燒天可見度的實際影響"""
        if not weather_description:
            return {'score': 0, 'description': '無天氣描述'}
        
        description = weather_description
        detected_types = []
        total_score = 0
        cloud_thickness_penalty = 0  # 新增：雲層厚度懲罰
        
        # 檢測關鍵詞
        for keyword, info in self.cloud_types.items():
            if keyword in description:
                detected_types.append({
                    'type': keyword,
                    'cloud_type': info['type'],
                    'score': round(info['score'])  # 確保分數是整數
                })
                total_score += info['score']
        
        # 分析雲層厚度對燒天的實際影響
        thickness_analysis = self._assess_cloud_thickness_impact(description)
        cloud_thickness_penalty = thickness_analysis['penalty']
        visibility_warning = thickness_analysis['warning']
        
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
        
        # 應用雲層厚度懲罰
        total_score -= cloud_thickness_penalty
        if visibility_warning:
            unfavorable.append(visibility_warning)
        
        # 計算最終分數
        if detected_types:
            avg_score = total_score / len(detected_types)
        else:
            avg_score = 10  # 預設分數
        
        final_score = max(0, min(30, avg_score))  # 限制在0-30分，符合前端設定
        
        analysis = f"檢測到雲層類型: {', '.join([t['type'] for t in detected_types])}"
        if burnsky_favorable:
            analysis += f" | 有利條件: {', '.join(burnsky_favorable)}"
        if unfavorable:
            analysis += f" | 不利條件: {', '.join(unfavorable)}"
        
        return {
            'score': round(final_score),  # round成整數
            'description': analysis,
            'detected_types': detected_types,
            'favorable_conditions': burnsky_favorable,
            'unfavorable_conditions': unfavorable,
            'cloud_thickness_impact': thickness_analysis  # 新增：雲層厚度影響詳情
        }
    
    def _assess_cloud_thickness_impact(self, weather_description):
        """評估雲層厚度對燒天可見度的實際影響"""
        penalty = 0
        warning = None
        visibility_level = "good"  # good, limited, poor, blocked
        
        description = weather_description.lower()
        
        # 檢測厚雲層關鍵詞
        thick_cloud_indicators = [
            ('密雲', 8, "dense_overcast"),
            ('陰天', 6, "overcast"), 
            ('陰雲', 6, "overcast"),
            ('大致多雲', 4, "mostly_cloudy"),
            ('多雲', 2, "cloudy"),
            ('雲層厚', 10, "thick_layers"),
            ('低雲', 5, "low_clouds"),
            ('霧', 12, "fog_mist"),
            ('薄霧', 8, "light_fog")
        ]
        
        detected_thickness = []
        for indicator, penalty_value, cloud_type in thick_cloud_indicators:
            if indicator in description:
                penalty += penalty_value
                detected_thickness.append(indicator)
        
        # 根據懲罰程度評估可見度和建議
        if penalty >= 15:
            visibility_level = "blocked"
            warning = "厚雲層嚴重阻擋，燒天幾乎不可見"
        elif penalty >= 10:
            visibility_level = "poor"  
            warning = "厚雲層阻擋，燒天色彩極微弱"
        elif penalty >= 6:
            visibility_level = "limited"
            warning = "雲層較厚，燒天色彩受限"
        elif penalty >= 3:
            visibility_level = "reduced"
            warning = "雲層影響，燒天強度減弱"
        
        return {
            'penalty': penalty,
            'warning': warning,
            'visibility_level': visibility_level,
            'detected_indicators': detected_thickness,
            'recommendation': self._generate_thickness_recommendation(visibility_level)
        }
    
    def _generate_thickness_recommendation(self, visibility_level):
        """根據雲層厚度生成建議"""
        recommendations = {
            "good": "雲層條件良好，預期正常燒天效果",
            "reduced": "建議調高相機曝光，捕捉微弱色彩",
            "limited": "主要拍攝雲層輪廓和明暗對比",
            "poor": "建議改拍剪影效果或等待天氣改善", 
            "blocked": "不建議燒天攝影，考慮改期或其他拍攝主題"
        }
        return recommendations.get(visibility_level, "請根據實際情況判斷")
    
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
        # 缺失輸入必須在訓練／推論前拒絕，不能生成補值預測。
        features = self.extract_features(weather_data, forecast_data)
        # 如果模型不存在，先訓練
        if self.regression_model is None or self.classification_model is None:
            print("🤖 模型不存在，正在訓練...")
            self.train_models()
        
        
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
            'ml_burnsky_score': round(max(0, min(100, regression_pred))),  # round成整數
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
        from modules.prediction_quality import station_value, highest_rainfall
        from modules.weather_presentation import number
        temperature = station_value(weather_data or {}, 'temperature')
        humidity = station_value(weather_data or {}, 'humidity')
        uv = (weather_data or {}).get('uvindex', {})
        entries = uv.get('data') if isinstance(uv, dict) else None
        uv_value = number(entries[0].get('value')) if isinstance(entries, list) and entries and isinstance(entries[0], dict) else None
        wind = (weather_data or {}).get('wind', {})
        wind_min = number(wind.get('speed_beaufort_min')) if isinstance(wind, dict) else None
        wind_max = number(wind.get('speed_beaufort_max')) if isinstance(wind, dict) else None
        desc = (forecast_data or {}).get('forecastDesc')
        if (temperature is None or not -50 <= temperature <= 60 or
                humidity is None or not 0 <= humidity <= 100 or
                uv_value is None or not 0 <= uv_value <= 30 or
                highest_rainfall(weather_data or {}) is None or
                wind_min is None or wind_max is None or not 0 <= wind_min <= wind_max <= 12 or
                not isinstance(desc, str) or not any(key in desc for key in self.cloud_types)):
            raise ValueError('ML特徵資料不足或雲層描述未能識別；不使用預設值')
        # 保留現有七特徵的單位與順序；模型仍只供研究，不參與正式評分。
        features = {
            'temperature': temperature,
            'humidity': humidity,
            'uv_index': uv_value,
            'rainfall': sum(max(0, number(item.get('max', item.get('value'))) or 0)
                            for item in weather_data['rainfall']['data'] if isinstance(item, dict)),
            'wind_speed': (wind_min + wind_max) / 2,
            'time_factor': self.calculate_time_factor_advanced()['score'] / 25,
            'cloud_score': self.analyze_cloud_types(desc)['score'],
        }
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
    
    def analyze_cloud_thickness_and_color_visibility(self, weather_data, forecast_data):
        """
        分析雲層厚度和顏色可見度 - 增強版
        區分「顏色燒天」vs「明暗燒天」
        整合衛星雲圖分析技術
        """
        # 首先使用原有邏輯作為基礎
        analysis = {
            'cloud_thickness_level': 'unknown',
            'color_visibility_percentage': 50,
            'visibility_type': 'mixed',
            'photography_type': 'standard',
            'specific_recommendations': [],
            'color_expectations': [],
            'technical_details': {},
            'satellite_analysis': None,  # 新增衛星分析結果
            'enhanced_accuracy': False   # 是否使用了增強分析
        }
        
        try:
            # 1. 嘗試載入衛星雲圖分析器
            try:
                from satellite_cloud_analyzer import SatelliteCloudAnalyzer
                satellite_analyzer = SatelliteCloudAnalyzer()
                
                # 執行深度衛星分析
                satellite_result = satellite_analyzer.analyze_real_time_cloud_conditions(
                    weather_data, forecast_data
                )
                
                if satellite_result and satellite_result.get('data_confidence', 0) > 60:
                    # 衛星數據可信度足夠，使用增強分析
                    analysis = self._integrate_satellite_analysis(analysis, satellite_result)
                    analysis['enhanced_accuracy'] = True
                    analysis['satellite_analysis'] = satellite_result
                else:
                    # 回退到原有分析方法
                    analysis = self._perform_basic_cloud_analysis(analysis, weather_data, forecast_data)
                    
            except ImportError:
                # 衛星分析模組不可用，使用原有方法
                analysis = self._perform_basic_cloud_analysis(analysis, weather_data, forecast_data)
                
        except Exception as e:
            analysis['error'] = f'雲層厚度分析失敗: {str(e)}'
            # 提供基本預設值
            analysis.update({
                'cloud_thickness_level': 'moderate',
                'color_visibility_percentage': 50,
                'visibility_type': 'mixed',
                'photography_type': 'standard',
                'specific_recommendations': ['⚠️ 分析系統暫時不可用，建議結合實際觀察'],
                'color_expectations': ['請參考實時天空狀況'],
                'technical_details': {'error': str(e)}
            })
        
        return analysis
    
    def _integrate_satellite_analysis(self, base_analysis, satellite_result):
        """整合衛星分析結果到基礎分析中"""
        # 從衛星分析獲取更準確的數據
        visibility_prediction = satellite_result.get('visibility_prediction', {})
        cloud_analysis = satellite_result.get('cloud_analysis', {})
        burnsky_suitability = satellite_result.get('burnsky_suitability', {})
        photography_guidance = satellite_result.get('photography_guidance', {})
        
        # 更新顏色可見度
        color_visibility = visibility_prediction.get('color_visibility_percentage', 50)
        base_analysis['color_visibility_percentage'] = color_visibility
        
        # 根據衛星數據確定雲層厚度等級
        cloud_coverage = cloud_analysis.get('coverage_estimate', 50)
        dominant_type = cloud_analysis.get('dominant_type', 'unknown')
        
        if cloud_coverage <= 20 and dominant_type in ['clear', 'cirrus']:
            base_analysis['cloud_thickness_level'] = 'clear_to_thin'
            base_analysis['visibility_type'] = 'excellent_colors'
            base_analysis['photography_type'] = 'color_focused'
        elif cloud_coverage <= 50 and dominant_type in ['cumulus', 'mixed']:
            base_analysis['cloud_thickness_level'] = 'moderate'
            base_analysis['visibility_type'] = 'good_colors'
            base_analysis['photography_type'] = 'color_with_drama'
        elif cloud_coverage <= 80:
            base_analysis['cloud_thickness_level'] = 'thick'
            base_analysis['visibility_type'] = 'limited_colors'
            base_analysis['photography_type'] = 'contrast_focused'
        else:
            base_analysis['cloud_thickness_level'] = 'very_thick_overcast'
            base_analysis['visibility_type'] = 'brightness_only'
            base_analysis['photography_type'] = 'silhouette_only'
        
        # 從攝影指導獲取建議
        if photography_guidance.get('composition_tips'):
            base_analysis['specific_recommendations'] = photography_guidance['composition_tips'][:4]
        
        # 從可見度預測獲取顏色期望
        if visibility_prediction.get('dominant_colors_expected'):
            base_analysis['color_expectations'] = visibility_prediction['dominant_colors_expected']
        
        # 詳細技術資訊
        base_analysis['technical_details'] = {
            'satellite_confidence': satellite_result.get('data_confidence', 0),
            'cloud_coverage': cloud_coverage,
            'dominant_cloud_type': dominant_type,
            'atmospheric_transparency': satellite_result.get('visibility_prediction', {}).get('transparency_percentage', 50),
            'analysis_method': 'satellite_enhanced'
        }
        
        # 根據適宜度添加特殊建議
        suitability_level = burnsky_suitability.get('suitability_level', 'moderate')
        if suitability_level == 'excellent':
            base_analysis['specific_recommendations'].insert(0, '🌟 衛星數據顯示絕佳條件！')
        elif suitability_level == 'poor':
            base_analysis['specific_recommendations'].insert(0, '📡 衛星分析建議等待更好時機')
        
        return base_analysis
    
    def _perform_basic_cloud_analysis(self, analysis, weather_data, forecast_data):
        """執行基礎雲層分析（原有邏輯的重構版本）"""
        try:
            # 1. 基於天氣描述判斷雲層厚度
            cloud_analysis = self._analyze_weather_description_for_thickness(forecast_data)
            
            # 2. 基於氣象數據推斷雲層密度  
            density_analysis = self._analyze_meteorological_density(weather_data)
            
            # 3. 綜合評估
            combined_score = (cloud_analysis['score'] + density_analysis['score']) / 2
            
            # 4. 確定雲層厚度等級（沿用原有邏輯）
            if combined_score >= 80:
                analysis.update({
                    'cloud_thickness_level': 'clear_to_thin',
                    'color_visibility_percentage': 90,
                    'visibility_type': 'excellent_colors',
                    'photography_type': 'color_focused',
                    'color_expectations': ['金色', '橙色', '紅色', '紫色', '粉紅色'],
                    'specific_recommendations': [
                        '🎨 絕佳顏色燒天條件！',
                        '📸 建議拍攝：全彩色漸變、雲彩細節、倒影效果',
                        '⏰ 可預期：持續15-30分鐘的豐富色彩變化',
                        '🌈 色溫變化：3000K → 2000K → 1800K'
                    ]
                })
            elif combined_score >= 60:
                analysis.update({
                    'cloud_thickness_level': 'moderate',
                    'color_visibility_percentage': 65,
                    'visibility_type': 'good_colors',
                    'photography_type': 'color_with_drama',
                    'color_expectations': ['橙色', '紅色', '深紅色'],
                    'specific_recommendations': [
                        '🌅 良好顏色燒天條件',
                        '📸 建議拍攝：主要色彩、雲層輪廓、剪影效果',
                        '⏰ 可預期：10-20分鐘的明顯色彩',
                        '🎭 適合：戲劇性構圖'
                    ]
                })
            elif combined_score >= 40:
                analysis.update({
                    'cloud_thickness_level': 'thick',
                    'color_visibility_percentage': 30,
                    'visibility_type': 'limited_colors',
                    'photography_type': 'contrast_focused',
                    'color_expectations': ['淡橙色', '暗紅色'],
                    'specific_recommendations': [
                        '🌫️ 厚雲條件，以明暗對比為主',
                        '📸 建議拍攝：剪影、雲層紋理、明暗層次',
                        '⏰ 可預期：微弱色彩，強烈明暗變化',
                        '🖤 適合：黑白攝影、情緒氛圍'
                    ]
                })
            else:
                analysis.update({
                    'cloud_thickness_level': 'very_thick_overcast',
                    'color_visibility_percentage': 10,
                    'visibility_type': 'brightness_only',
                    'photography_type': 'silhouette_only',
                    'color_expectations': ['極微弱色彩'],
                    'specific_recommendations': [
                        '☁️ 密雲天氣，主要為明暗變化',
                        '📸 建議拍攝：純剪影、雲層動態、光線穿透',
                        '⏰ 可預期：5-10分鐘的亮度變化',
                        '🌆 適合：極簡構圖、形狀表現'
                    ]
                })
            
            # 5. 技術細節
            analysis['technical_details'] = {
                'weather_score': cloud_analysis['score'],
                'density_score': density_analysis['score'],
                'combined_score': combined_score,
                'factors': cloud_analysis['factors'] + density_analysis['factors'],
                'analysis_method': 'basic_meteorological'
            }
            
        except Exception as e:
            analysis['error'] = f'基礎雲層分析失敗: {str(e)}'
        
        return analysis

    def _analyze_weather_description_for_thickness(self, forecast_data):
        """分析天氣描述以評估雲層厚度"""
        analysis = {
            'score': 50,  # 預設中等分數
            'factors': [],
            'keywords_found': []
        }
        
        if not forecast_data or 'forecastDesc' not in forecast_data:
            analysis['factors'].append('天氣描述資料不可用')
            return analysis
        
        description = forecast_data['forecastDesc'].lower()
        
        # 雲層相關關鍵詞與分數
        cloud_keywords = {
            # 晴朗天氣 (高分數)
            '晴朗': 95, '天晴': 90, '晴天': 88,
            
            # 部分雲層 (中高分數)
            '部分時間有陽光': 75, '短暫時間有陽光': 65, '間中有陽光': 70,
            
            # 多雲 (中等分數)
            '多雲': 45, '大致多雲': 35, '主要多雲': 30,
            
            # 密雲與惡劣天氣 (低分數)
            '密雲': 15, '陰天': 20, '大致陰天': 25,
            '雷暴': 10, '雨': 10, '大雨': 5, '暴雨': 5,
            '薄霧': 30, '霧': 20, '濃霧': 10
        }
        
        # 檢查關鍵詞
        matched_scores = []
        for keyword, score in cloud_keywords.items():
            if keyword in description:
                matched_scores.append(score)
                analysis['keywords_found'].append(keyword)
                analysis['factors'].append(f'檢測到: {keyword} (分數: {score})')
        
        # 計算最終分數
        if matched_scores:
            # 如果找到多個關鍵詞，取平均值但偏向較低分數（保守預測）
            analysis['score'] = (min(matched_scores) * 0.6 + max(matched_scores) * 0.4)
        else:
            analysis['factors'].append('未檢測到明確雲層關鍵詞，使用預設分數')
        
        return analysis
    
    def _analyze_meteorological_density(self, weather_data):
        """基於氣象數據分析雲層密度"""
        analysis = {
            'score': 50,  # 預設分數
            'factors': [],
            'measurements': {}
        }
        
        factors_scores = []
        
        try:
            # 1. UV指數分析 (反映雲層遮蔽)
            if weather_data.get('uvindex') and weather_data['uvindex'].get('data'):
                uv_data = weather_data['uvindex']['data']
                if uv_data and len(uv_data) > 0:
                    uv_value = uv_data[0].get('value', 0)
                    # UV指數越高，雲層遮蔽越少
                    uv_score = min(100, uv_value * 12)  # UV8+ = 96分
                    factors_scores.append(uv_score)
                    analysis['measurements']['uv_index'] = uv_value
                    analysis['factors'].append(f'UV指數: {uv_value} (雲層透明度分數: {uv_score:.1f})')
            
            # 2. 濕度分析
            if weather_data.get('humidity') and weather_data['humidity'].get('data'):
                hko_humidity = next((h for h in weather_data['humidity']['data'] 
                                   if h.get('place') == '香港天文台'), None)
                if hko_humidity:
                    humidity = hko_humidity.get('value', 70)
                    # 濕度影響能見度與雲層形成
                    humidity_score = max(10, 110 - humidity)  # 濕度越低分數越高
                    factors_scores.append(humidity_score)
                    analysis['measurements']['humidity'] = humidity
                    analysis['factors'].append(f'濕度: {humidity}% (能見度分數: {humidity_score:.1f})')
            
            # 3. 降雨量分析
            if weather_data.get('rainfall') and weather_data['rainfall'].get('data'):
                total_rainfall = sum(r.get('value', 0) for r in weather_data['rainfall']['data'] 
                                   if isinstance(r, dict))
                if total_rainfall > 0:
                    # 降雨表示有厚雲層
                    rain_score = max(5, 60 - total_rainfall * 10)
                    factors_scores.append(rain_score)
                    analysis['measurements']['rainfall'] = total_rainfall
                    analysis['factors'].append(f'降雨量: {total_rainfall}mm (雲層分數: {rain_score:.1f})')
                else:
                    # 無降雨是好徵象
                    factors_scores.append(75)
                    analysis['factors'].append('無降雨 (有利於燒天)')
            
            # 4. 計算綜合分數
            if factors_scores:
                analysis['score'] = sum(factors_scores) / len(factors_scores)
            else:
                analysis['factors'].append('氣象數據不完整，使用預設分數')
                
        except Exception as e:
            analysis['factors'].append(f'氣象數據分析錯誤: {str(e)}')
        
        return analysis
