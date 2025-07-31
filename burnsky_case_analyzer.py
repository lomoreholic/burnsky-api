#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
燒天案例分析器 - 增強版
用於分析實際燒天照片的條件，優化預測算法
整合機器學習模型，實時更新預測準確性
"""

from datetime import datetime, timedelta
import json
import os
import sqlite3
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import warnings
warnings.filterwarnings('ignore')

class BurnskyCase:
    """燒天案例類"""
    def __init__(self, location, time, direction, weather_conditions, visual_rating, notes=""):
        self.location = location
        self.time = time
        self.direction = direction
        self.weather_conditions = weather_conditions
        self.visual_rating = visual_rating  # 1-10分
        self.notes = notes
        self.timestamp = datetime.now().isoformat()

class BurnskyCaseAnalyzer:
    """燒天案例分析器 - 增強版，整合機器學習"""
    
    def __init__(self, case_file="burnsky_cases.json", db_file="prediction_history.db", model_file="burnsky_ml_model.pkl"):
        self.case_file = case_file
        self.db_file = db_file
        self.model_file = model_file
        self.cases = self.load_cases()
        self.ml_model = None
        self.feature_names = [
            'hour', 'cloud_coverage_num', 'visibility_num', 'humidity_num', 
            'temperature_num', 'wind_num', 'air_quality_num', 'season_num'
        ]
        self.load_or_train_model()
    
    def load_cases(self):
        """載入已有案例"""
        if os.path.exists(self.case_file):
            try:
                with open(self.case_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def load_prediction_history(self):
        """從資料庫載入預測歷史"""
        if not os.path.exists(self.db_file):
            return []
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, score, factors, weather_data, created_at
                FROM prediction_history 
                ORDER BY timestamp DESC
            ''')
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                try:
                    factors = json.loads(row[2]) if row[2] else {}
                    weather = json.loads(row[3]) if row[3] else {}
                    history.append({
                        'timestamp': row[0],
                        'score': row[1],
                        'factors': factors,
                        'weather_data': weather,
                        'created_at': row[4]
                    })
                except:
                    continue
            
            return history
        except Exception as e:
            print(f"載入預測歷史失敗: {e}")
            return []
    
    def save_cases(self):
        """保存案例到文件"""
        with open(self.case_file, 'w', encoding='utf-8') as f:
            json.dump(self.cases, f, ensure_ascii=False, indent=2)
    
    def normalize_conditions_to_numbers(self, conditions):
        """將文字條件轉換為數值特徵"""
        # 雲量覆蓋
        cloud_mapping = {
            '晴朗': 0.1, '少雲': 0.3, '適中': 0.5, '適宜': 0.4, 
            '多雲': 0.7, '較厚': 0.8, '陰天': 0.9, '完全覆蓋': 1.0
        }
        
        # 能見度
        visibility_mapping = {
            '極差': 0.1, '差': 0.3, '一般': 0.5, '良好': 0.7, '極佳': 0.9, '完美': 1.0
        }
        
        # 濕度
        humidity_mapping = {
            '低': 0.2, '中等': 0.5, '較高': 0.7, '高': 0.9, '極高': 1.0
        }
        
        # 風力
        wind_mapping = {
            '無風': 0.0, '輕微': 0.2, '微風': 0.4, '適中': 0.6, '強風': 0.8, '暴風': 1.0
        }
        
        # 空氣質量
        air_quality_mapping = {
            '極佳': 1.0, '良好': 0.8, '一般': 0.6, '差': 0.4, '很差': 0.2, '城市環境': 0.5
        }
        
        # 提取數值特徵
        features = {}
        features['cloud_coverage_num'] = cloud_mapping.get(conditions.get('cloud_coverage', ''), 0.5)
        features['visibility_num'] = visibility_mapping.get(conditions.get('visibility', ''), 0.5)
        features['humidity_num'] = humidity_mapping.get(conditions.get('humidity', ''), 0.5)
        features['wind_num'] = wind_mapping.get(conditions.get('wind', ''), 0.2)
        features['air_quality_num'] = air_quality_mapping.get(conditions.get('air_quality', ''), 0.5)
        
        # 溫度處理（假設夏季溫度）
        if 'temperature' in conditions:
            if '夏季' in str(conditions['temperature']):
                features['temperature_num'] = 0.8
            elif '冬季' in str(conditions['temperature']):
                features['temperature_num'] = 0.3
            else:
                features['temperature_num'] = 0.5
        else:
            features['temperature_num'] = 0.5
        
        return features
    
    def extract_features_from_case(self, case):
        """從案例中提取機器學習特徵"""
        features = []
        
        # 時間特徵
        time_str = case.get('time', '18:00')
        try:
            hour = int(time_str.split(':')[0])
            features.append(hour)
        except:
            features.append(18)  # 默認值
        
        # 天氣條件特徵
        conditions = case.get('weather_conditions', {})
        numeric_conditions = self.normalize_conditions_to_numbers(conditions)
        
        features.extend([
            numeric_conditions['cloud_coverage_num'],
            numeric_conditions['visibility_num'], 
            numeric_conditions['humidity_num'],
            numeric_conditions['temperature_num'],
            numeric_conditions['wind_num'],
            numeric_conditions['air_quality_num']
        ])
        
        # 季節特徵（基於時間戳）
        try:
            timestamp = case.get('timestamp', datetime.now().isoformat())
            dt = datetime.fromisoformat(timestamp)
            month = dt.month
            if month in [12, 1, 2]:
                season = 0.0  # 冬季
            elif month in [3, 4, 5]:
                season = 0.25  # 春季
            elif month in [6, 7, 8]:
                season = 0.75  # 夏季
            else:
                season = 0.5  # 秋季
            features.append(season)
        except:
            features.append(0.5)  # 默認秋季
        
        return features
    
    def prepare_training_data(self):
        """準備訓練數據"""
        X = []  # 特徵
        y = []  # 目標值（視覺評分）
        
        # 從用戶案例中提取
        for case in self.cases:
            try:
                features = self.extract_features_from_case(case)
                rating = case.get('visual_rating', 0)
                if len(features) == len(self.feature_names) and rating > 0:
                    X.append(features)
                    y.append(rating)
            except Exception as e:
                print(f"提取案例特徵失敗: {e}")
                continue
        
        # 從預測歷史中提取（如果有的話）
        history = self.load_prediction_history()
        for record in history:
            try:
                # 從預測記錄中構造特徵
                timestamp = record.get('timestamp', '')
                if timestamp:
                    dt = datetime.fromisoformat(timestamp)
                    hour = dt.hour
                    month = dt.month
                    if month in [12, 1, 2]:
                        season = 0.0
                    elif month in [3, 4, 5]:
                        season = 0.25
                    elif month in [6, 7, 8]:
                        season = 0.75
                    else:
                        season = 0.5
                    
                    # 從因子中提取特徵
                    factors = record.get('factors', {})
                    features = [
                        hour,
                        factors.get('cloud_cover', 50) / 100.0,
                        factors.get('visibility', 10) / 20.0,
                        factors.get('humidity', 60) / 100.0,
                        factors.get('temperature', 25) / 40.0,
                        factors.get('wind_speed', 10) / 30.0,
                        0.5,  # 空氣質量默認值
                        season
                    ]
                    
                    # 將預測分數轉換為視覺評分估計
                    score = record.get('score', 0)
                    estimated_rating = min(max(score / 10.0, 1), 10)  # 將0-100分數轉換為1-10評分
                    
                    if len(features) == len(self.feature_names):
                        X.append(features)
                        y.append(estimated_rating)
            except Exception as e:
                continue
        
        return np.array(X), np.array(y)
    
    def load_or_train_model(self):
        """載入或訓練機器學習模型"""
        # 嘗試載入現有模型
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, 'rb') as f:
                    self.ml_model = pickle.load(f)
                print("✅ 成功載入現有ML模型")
                return
            except Exception as e:
                print(f"載入模型失敗: {e}")
        
        # 訓練新模型
        self.train_new_model()
    
    def train_new_model(self):
        """訓練新的機器學習模型"""
        print("🤖 開始訓練新的燒天預測ML模型...")
        
        X, y = self.prepare_training_data()
        
        if len(X) < 5:
            print("⚠️ 訓練數據不足，使用默認模型")
            # 創建一個簡單的默認模型
            self.ml_model = RandomForestRegressor(n_estimators=10, random_state=42)
            # 使用一些默認數據訓練
            default_X = np.array([
                [18, 0.4, 0.7, 0.6, 0.8, 0.2, 0.6, 0.75],  # 好條件
                [19, 0.8, 0.3, 0.8, 0.5, 0.4, 0.4, 0.75],  # 差條件
                [17, 0.3, 0.8, 0.5, 0.7, 0.1, 0.7, 0.0],   # 冬季好條件
            ])
            default_y = np.array([8, 3, 9])
            self.ml_model.fit(default_X, default_y)
        else:
            # 使用真實數據訓練
            self.ml_model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                min_samples_split=2,
                min_samples_leaf=1
            )
            
            if len(X) > 3:
                # 如果數據足夠，進行訓練/驗證分割
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                self.ml_model.fit(X_train, y_train)
                
                # 評估模型
                y_pred = self.ml_model.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                print(f"📊 模型評估 - MSE: {mse:.2f}, R²: {r2:.2f}")
            else:
                # 數據不足，使用全部數據訓練
                self.ml_model.fit(X, y)
                print(f"📊 使用 {len(X)} 個樣本訓練模型")
        
        # 保存模型
        try:
            with open(self.model_file, 'wb') as f:
                pickle.dump(self.ml_model, f)
            print("✅ ML模型已保存")
        except Exception as e:
            print(f"保存模型失敗: {e}")
    
    def predict_with_ml(self, conditions):
        """使用機器學習模型進行預測"""
        if not self.ml_model:
            return None, "ML模型未載入"
        
        try:
            # 提取特徵
            numeric_conditions = self.normalize_conditions_to_numbers(conditions)
            
            # 獲取當前時間特徵
            now = datetime.now()
            hour = now.hour
            month = now.month
            if month in [12, 1, 2]:
                season = 0.0
            elif month in [3, 4, 5]:
                season = 0.25
            elif month in [6, 7, 8]:
                season = 0.75
            else:
                season = 0.5
            
            features = np.array([[
                hour,
                numeric_conditions['cloud_coverage_num'],
                numeric_conditions['visibility_num'], 
                numeric_conditions['humidity_num'],
                numeric_conditions['temperature_num'],
                numeric_conditions['wind_num'],
                numeric_conditions['air_quality_num'],
                season
            ]])
            
            # 預測
            prediction = self.ml_model.predict(features)[0]
            confidence = min(max(self.ml_model.score(features, [prediction]) if hasattr(self.ml_model, 'score') else 0.7, 0.3), 0.95)
            
            return prediction, f"ML預測評分: {prediction:.1f}/10, 置信度: {confidence:.1f}"
            
        except Exception as e:
            return None, f"ML預測失敗: {e}"
    
    def find_similar_cases(self, current_conditions):
        """尋找相似的歷史案例"""
        similar_cases = []
        
        for case in self.cases:
            similarity_score = self.calculate_similarity(current_conditions, case.get('weather_conditions', {}))
            if similarity_score > 0.6:  # 相似度閾值
                case_copy = case.copy()
                case_copy['similarity'] = similarity_score
                similar_cases.append(case_copy)
        
        # 按相似度排序
        similar_cases.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        return similar_cases
    
    def calculate_similarity(self, conditions1, conditions2):
        """計算兩組天氣條件的相似度"""
        if not conditions1 or not conditions2:
            return 0.0
        
        # 條件映射
        condition_mappings = {
            'cloud_coverage': {'晴朗': 1, '少雲': 2, '適中': 3, '適宜': 3, '多雲': 4, '較厚': 5, '陰天': 6},
            'visibility': {'極差': 1, '差': 2, '一般': 3, '良好': 4, '極佳': 5, '完美': 6},
            'humidity': {'低': 1, '中等': 2, '較高': 3, '高': 4, '極高': 5},
            'wind': {'無風': 1, '輕微': 2, '微風': 3, '適中': 4, '強風': 5, '暴風': 6},
            'air_quality': {'極佳': 5, '良好': 4, '一般': 3, '差': 2, '很差': 1, '城市環境': 3}
        }
        
        total_similarity = 0
        compared_factors = 0
        
        for key in condition_mappings.keys():
            if key in conditions1 and key in conditions2:
                val1 = condition_mappings[key].get(conditions1[key], 3)
                val2 = condition_mappings[key].get(conditions2[key], 3)
                max_val = max(condition_mappings[key].values())
                
                # 計算相似度 (1 - 差異/最大可能差異)
                diff = abs(val1 - val2)
                similarity = 1 - (diff / max_val)
                total_similarity += similarity
                compared_factors += 1
        
        return total_similarity / max(compared_factors, 1)
    
    def analyze_conditions(self, current_conditions):
        """分析當前條件並給出燒天可能性評估"""
        print("🔍 開始分析當前燒天條件...")
        
        # 基礎規則分析
        similar_cases = self.find_similar_cases(current_conditions)
        traditional_analysis = self.traditional_analysis(current_conditions)
        
        # ML預測
        ml_prediction, ml_info = self.predict_with_ml(current_conditions)
        
        # 綜合評估
        if ml_prediction is not None and len(similar_cases) > 0:
            # 結合ML預測和歷史案例
            case_avg = sum([case.get('visual_rating', 5) for case in similar_cases]) / len(similar_cases)
            combined_score = (ml_prediction * 0.6 + case_avg * 0.4)
            prediction_method = "AI智能 + 案例分析"
        elif ml_prediction is not None:
            # 僅使用ML預測
            combined_score = ml_prediction
            prediction_method = "AI智能預測"
        elif len(similar_cases) > 0:
            # 僅使用歷史案例
            combined_score = sum([case.get('visual_rating', 5) for case in similar_cases]) / len(similar_cases)
            prediction_method = "歷史案例分析"
        else:
            # 使用傳統規則
            combined_score = traditional_analysis['base_score']
            prediction_method = "基礎規則分析"
        
        # 燒天可能性分級
        if combined_score >= 8.5:
            possibility = "極高 🔥🔥🔥"
            color = "#FF4444"
        elif combined_score >= 7.0:
            possibility = "高 🔥🔥"
            color = "#FF6644"
        elif combined_score >= 5.5:
            possibility = "中等 🔥"
            color = "#FF8844"
        elif combined_score >= 3.5:
            possibility = "低 ☁️"
            color = "#88AAFF"
        else:
            possibility = "極低 ❄️"
            color = "#AACCFF"
        
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'prediction_method': prediction_method,
            'ml_prediction': ml_prediction,
            'ml_info': ml_info,
            'similar_cases_count': len(similar_cases),
            'combined_score': round(combined_score, 1),
            'possibility': possibility,
            'color': color,
            'conditions': current_conditions,
            'recommendations': self.generate_recommendations(combined_score, current_conditions),
            'analysis_details': {
                'traditional': traditional_analysis,
                'similar_cases': similar_cases[:3] if similar_cases else [],
                'feature_importance': self.get_feature_importance() if self.ml_model else None
            }
        }
        
        print(f"✅ 分析完成 - 燒天可能性: {possibility} (評分: {combined_score}/10)")
        return analysis_result
    
    def get_feature_importance(self):
        """獲取ML模型的特徵重要性"""
        if not self.ml_model or not hasattr(self.ml_model, 'feature_importances_'):
            return None
        
        importances = self.ml_model.feature_importances_
        feature_importance = {}
        for i, importance in enumerate(importances):
            if i < len(self.feature_names):
                feature_importance[self.feature_names[i]] = round(importance, 3)
        
        return feature_importance
    
    def traditional_analysis(self, conditions):
        """傳統規則分析"""
        score = 5.0  # 基礎分數
        factors = []
        
        # 雲量分析
        cloud = conditions.get('cloud_coverage', '適中').lower()
        if '晴' in cloud or '少雲' in cloud:
            score += 2
            factors.append("☀️ 雲量條件良好")
        elif '多雲' in cloud or '厚' in cloud:
            score -= 1.5
            factors.append("☁️ 雲量偏多")
        elif '陰' in cloud:
            score -= 3
            factors.append("🌫️ 陰天不利")
        
        # 能見度分析
        visibility = conditions.get('visibility', '一般').lower()
        if '極佳' in visibility or '完美' in visibility:
            score += 1.5
            factors.append("👁️ 能見度極佳")
        elif '良好' in visibility:
            score += 1
            factors.append("👁️ 能見度良好")
        elif '差' in visibility:
            score -= 2
            factors.append("🌫️ 能見度差")
        
        # 空氣質量分析
        air_quality = conditions.get('air_quality', '一般').lower()
        if '極佳' in air_quality:
            score += 1.5
            factors.append("🍃 空氣質量極佳")
        elif '良好' in air_quality:
            score += 1
            factors.append("🍃 空氣質量良好")
        elif '差' in air_quality:
            score -= 1
            factors.append("🏭 空氣質量不佳")
        
        return {
            'base_score': max(1, min(10, score)),
            'factors': factors
        }
    
    def generate_recommendations(self, score, conditions):
        """根據評分生成建議"""
        recommendations = []
        
        if score >= 8:
            recommendations.extend([
                "🎯 建議立即前往最佳觀賞點",
                "📷 準備相機，捕捉最美時刻",
                "⏰ 日落前30分鐘到達現場"
            ])
        elif score >= 6:
            recommendations.extend([
                "👀 值得一試，選擇較高視野點",
                "📱 持續關注雲層變化",
                "🚗 提前規劃路線"
            ])
        elif score >= 4:
            recommendations.extend([
                "🤔 條件一般，可碰運氣",
                "🔄 建議等待更好時機",
                "📊 關注明日天氣預報"
            ])
        else:
            recommendations.extend([
                "❌ 今日不建議追燒天",
                "📅 等待更好的天氣條件",
                "🔍 持續監控天氣變化"
            ])
        
        # 根據具體條件添加針對性建議
        if '多雲' in conditions.get('cloud_coverage', ''):
            recommendations.append("☁️ 注意雲層移動，可能有突破口")
        
        if '差' in conditions.get('visibility', ''):
            recommendations.append("🌫️ 選擇較高海拔觀賞點")
        
        return recommendations
    
    def update_model_with_feedback(self, conditions, actual_rating):
        """用用戶反饋更新模型"""
        # 添加新案例
        new_case = {
            'timestamp': datetime.now().isoformat(),
            'weather_conditions': conditions,
            'visual_rating': actual_rating,
            'feedback_source': 'user'
        }
        
        self.cases.append(new_case)
        self.save_cases()
        
        # 重新訓練模型（如果有足夠數據）
        if len(self.cases) % 5 == 0:  # 每5個新案例重新訓練一次
            print("🔄 基於新數據重新訓練ML模型...")
            self.train_new_model()
        
        return "✅ 感謝反饋！數據已更新到預測系統中"
    
    def add_case(self, case):
        """添加新案例"""
        case_dict = {
            'location': case.location,
            'time': case.time,
            'direction': case.direction,
            'weather_conditions': case.weather_conditions,
            'visual_rating': case.visual_rating,
            'notes': case.notes,
            'timestamp': case.timestamp
        }
        self.cases.append(case_dict)
        self.save_cases()
        print(f"✅ 已添加燒天案例: {case.location} - {case.time} - 評分: {case.visual_rating}/10")
    
    def analyze_successful_patterns(self):
        """分析成功燒天的模式"""
        if not self.cases:
            return {}
        
        # 篩選高評分案例 (7分以上)
        successful_cases = [case for case in self.cases if case.get('visual_rating', 0) >= 7]
        
        if not successful_cases:
            return {}
        
        analysis = {
            'total_cases': len(self.cases),
            'successful_cases': len(successful_cases),
            'success_rate': len(successful_cases) / len(self.cases) * 100,
            'common_conditions': {},
            'optimal_times': [],
            'best_locations': {},
            'weather_patterns': {}
        }
        
        # 分析最佳時間
        times = [case.get('time', '') for case in successful_cases]
        analysis['optimal_times'] = list(set(times))
        
        # 分析最佳地點
        locations = {}
        for case in successful_cases:
            loc = case.get('location', '')
            if loc:
                locations[loc] = locations.get(loc, 0) + 1
        analysis['best_locations'] = locations
        
        # 分析天氣模式
        weather_patterns = {}
        for case in successful_cases:
            conditions = case.get('weather_conditions', {})
            for key, value in conditions.items():
                if key not in weather_patterns:
                    weather_patterns[key] = []
                weather_patterns[key].append(value)
        
        # 計算天氣條件的平均值/常見值
        for key, values in weather_patterns.items():
            if isinstance(values[0], (int, float)):
                weather_patterns[key] = {
                    'avg': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
            else:
                # 對於非數值類型，計算最常見的值
                value_counts = {}
                for v in values:
                    value_counts[v] = value_counts.get(v, 0) + 1
                weather_patterns[key] = value_counts
        
        analysis['weather_patterns'] = weather_patterns
        
        return analysis
    
    def get_prediction_adjustment(self, current_conditions):
        """基於歷史案例給出預測調整建議"""
        analysis = self.analyze_successful_patterns()
        
        if not analysis or not analysis.get('weather_patterns'):
            return 0, "暫無足夠歷史案例數據"
        
        adjustment = 0
        reasons = []
        
        weather_patterns = analysis['weather_patterns']
        
        # 檢查當前條件是否符合成功模式
        for condition, pattern in weather_patterns.items():
            if condition in current_conditions:
                current_value = current_conditions[condition]
                
                if isinstance(pattern, dict) and 'avg' in pattern:
                    # 數值型條件
                    avg_successful = pattern['avg']
                    if abs(current_value - avg_successful) <= abs(avg_successful * 0.2):  # 20%容差
                        adjustment += 5
                        reasons.append(f"{condition}接近成功案例平均值")
                elif isinstance(pattern, dict):
                    # 分類型條件
                    if current_value in pattern:
                        weight = pattern[current_value] / sum(pattern.values())
                        if weight > 0.5:  # 超過50%的成功案例有此條件
                            adjustment += 8
                            reasons.append(f"{condition}={current_value}在成功案例中常見")
        
        return min(adjustment, 15), "; ".join(reasons)  # 最多增加15分

# 創建全局分析器實例
case_analyzer = BurnskyCaseAnalyzer()

def add_todays_cases():
    """添加今天的燒天案例"""
    
    # 流浮山案例 (從用戶提供的信息)
    liufushan_case = BurnskyCase(
        location="流浮山",
        time="18:40",
        direction="西面",
        weather_conditions={
            "cloud_coverage": "適中",
            "visibility": "良好", 
            "temperature": "夏季溫度",
            "humidity": "中等",
            "wind": "輕微",
            "air_quality": "一般"
        },
        visual_rating=8,
        notes="金橙色調豐富，雲層有層次，水面反射明顯，系統預測32%但實際效果很好"
    )
    
    # 橫瀾島案例
    henglai_case = BurnskyCase(
        location="橫瀾島",
        time="18:40",
        direction="西面",
        weather_conditions={
            "cloud_coverage": "適宜",
            "visibility": "極佳",
            "temperature": "夏季溫度", 
            "humidity": "中等",
            "wind": "輕微",
            "air_quality": "良好"
        },
        visual_rating=9,
        notes="強烈橙紅色燒天，雲層厚度完美，典型火燒雲效果，山脈剪影增強視覺"
    )
    
    # 大帽山案例 - 效果不明顯
    damaoshan_case = BurnskyCase(
        location="大帽山",
        time="18:55",
        direction="西南面",
        weather_conditions={
            "cloud_coverage": "較厚",
            "visibility": "一般",
            "temperature": "夏季溫度",
            "humidity": "較高",
            "wind": "輕微",
            "air_quality": "一般"
        },
        visual_rating=3,
        notes="燒天效果不太明顯，雲層較厚，光線被遮擋，時間也較晚(18:55)"
    )
    
    # 尖沙咀天文台總部案例 - 效果不明顯
    tsimshatsui_case = BurnskyCase(
        location="尖沙咀天文台總部",
        time="18:55",
        direction="西面",
        weather_conditions={
            "cloud_coverage": "較厚",
            "visibility": "一般",
            "temperature": "夏季溫度",
            "humidity": "較高",
            "wind": "輕微",
            "air_quality": "城市環境"
        },
        visual_rating=3,
        notes="燒天效果不算明顯，城市環境，雲層較厚，時間較晚(18:55)，光線條件不佳"
    )
    
    case_analyzer.add_case(liufushan_case)
    case_analyzer.add_case(henglai_case)
    case_analyzer.add_case(damaoshan_case)
    case_analyzer.add_case(tsimshatsui_case)
    
    return case_analyzer.analyze_successful_patterns()

if __name__ == "__main__":
    # 添加今天的案例
    analysis = add_todays_cases()
    print("\n📊 燒天案例分析結果:")
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
