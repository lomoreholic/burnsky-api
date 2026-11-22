"""
統一燒天預測計分系統
整合所有計分方式，提供標準化的預測介面

作者: BurnSky Team
日期: 2025-07-18
"""

import math
import numpy as np
from datetime import datetime, time
import pytz
from advanced_predictor import AdvancedBurnskyPredictor
from air_quality_fetcher import AirQualityFetcher
from modules.prediction_quality import highest_rainfall, station_value
from modules.weather_presentation import number
import warnings
warnings.filterwarnings('ignore')

class UnifiedBurnskyScorer:
    """統一燒天預測計分器"""
    
    def __init__(self):
        """初始化統一計分器"""
        self.advanced_predictor = AdvancedBurnskyPredictor()
        self.air_quality_fetcher = AirQualityFetcher()
        
        # 評分系統配置（已修正）
        self.SCORING_CONFIG = {
            # 配置各因子的最大分數
            'factor_max_scores': {
                'time': 18,           # 時間因子 (12% - 從16.7%降低)
                'temperature': 15,    # 溫度因子 (10% - 不變)
                'humidity': 20,       # 濕度因子 (13.3% - 不變)
                'visibility': 20,     # 能見度因子 (13.3% - 從10%提高)
                'cloud': 35,          # 雲層因子 (23.3% - 從16.7%提高，最重要)
                'pressure': 10,       # 氣壓因子 (6.7% - 不變)
                'uv': 2,              # UV指數因子 (1.3% - 從6.7%大幅降低)
                'wind': 15,           # 風速因子 (10% - 不變)
                'air_quality': 15     # 空氣品質因子 (10% - 不變)
            },
            
            # 權重配置
            'ml_weights': {
                'immediate': {'traditional': 0.45, 'ml': 0.55},      # 即時預測
                'golden_hour': {'traditional': 0.35, 'ml': 0.65},    # 黃金時段(1-2小時)
                'advance': {'traditional': 0.40, 'ml': 0.60}         # 其他提前預測
            },
            
            # 調整係數 - 改為加減分數而非乘數  
            'adjustment_factors': {
                'cloud_visibility_low': -5,     # 厚雲扣5分 (原-10分太嚴厲)
                'cloud_visibility_high': +8,    # 極佳條件加8分
                'seasonal_summer': +3,          # 夏季加3分
                'seasonal_winter': -2           # 冬季扣2分
            }
        }
        
        # 總分上限
        self.MAX_TRADITIONAL_SCORE = sum(self.SCORING_CONFIG['factor_max_scores'].values())  # 150分
    
    def calculate_unified_score(self, weather_data, forecast_data, ninday_data, 
                              prediction_type='sunset', advance_hours=0, 
                              use_seasonal_adjustment=True):
        """
        統一計分方法 - 整合所有計分邏輯
        
        Args:
            weather_data: 天氣數據
            forecast_data: 預報數據
            ninday_data: 九天預報數據
            prediction_type: 'sunset' 或 'sunrise'
            advance_hours: 提前預測小時數 (0-24)
            use_seasonal_adjustment: 是否使用季節調整
            
        Returns:
            dict: 完整的計分結果
        """
        
        from datetime import timezone
        result = {
            'prediction_info': {
                'type': prediction_type,
                'advance_hours': advance_hours,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            'factor_scores': {},
            'traditional_score': 0,
            'ml_score': None,
            'final_score': None,
            'adjustments': {},
            'analysis': {}
        }
        
        try:
            evaluated_at = self._resolve_evaluated_at(weather_data, advance_hours)
            result['prediction_info']['evaluated_at'] = evaluated_at.isoformat()
            time_result = self.advanced_predictor.calculate_advanced_time_factor(
                prediction_type=prediction_type, advance_hours=advance_hours, evaluated_at=evaluated_at
            )
            result['time_factor'] = time_result
            # 1. 計算各個因子分數
            factor_scores = self._calculate_all_factors(
                weather_data, forecast_data, ninday_data, prediction_type, advance_hours,
                time_result=time_result
            )
            result['factor_scores'] = factor_scores
            if factor_scores['temperature'] is None or factor_scores['humidity'] is None:
                raise ValueError('主要溫度或濕度資料不足，暫停評分')
            
            # 2. 計算傳統算法總分
            available = {key: value for key, value in factor_scores.items() if value is not None}
            traditional_total = sum(available.values())
            available_max = sum(self.SCORING_CONFIG['factor_max_scores'][key] for key in available)
            result['input_coverage'] = {
                'available_factors': list(available),
                'missing_factors': [key for key, value in factor_scores.items() if value is None],
                'available_max_score': available_max,
                'missing_max_score': self.MAX_TRADITIONAL_SCORE - available_max,
                'total_max_score': self.MAX_TRADITIONAL_SCORE,
                'weighted_percent': round(available_max / self.MAX_TRADITIONAL_SCORE * 100, 1),
                'normalization': 'fixed_total_no_missing_points',
            }
            result['traditional_score'] = traditional_total
            
            # 3. 標準化傳統算法分數 (150分 → 100分)
            traditional_normalized = (traditional_total / self.MAX_TRADITIONAL_SCORE) * 100
            result['traditional_normalized'] = traditional_normalized
            
            # 4. 獲取機器學習分數
            ml_score = self._get_ml_score(weather_data, forecast_data, result)
            result['ml_score'] = ml_score
            
            # 5. 確定權重並計算加權分數
            weights = self._determine_weights(advance_hours) if ml_score is not None else {'traditional': 1.0, 'ml': 0.0}
            weighted_score = traditional_normalized * weights['traditional'] + (ml_score or 0) * weights['ml']
            result['weighted_score'] = weighted_score
            result['weights_used'] = weights
            
            # 6. 應用調整係數
            adjusted_score = self._apply_adjustments(
                weighted_score, weather_data, forecast_data, 
                use_seasonal_adjustment, result
            )
            result['final_score'] = max(0, min(100, adjusted_score))
            
            # 7. 生成分析結果
            result['analysis'] = self._generate_analysis(result, weather_data, forecast_data, advance_hours)
            
            # 8. 預測強度和顏色
            result['intensity_prediction'] = self.advanced_predictor.predict_burnsky_intensity(result['final_score'])
            result['color_prediction'] = self.advanced_predictor.predict_burnsky_colors(
                weather_data, forecast_data, result['final_score']
            )
            
            return result
            
        except Exception as e:
            # 錯誤處理
            result['error'] = str(e)
            result['final_score'] = None
            return result
    
    def _resolve_evaluated_at(self, weather_data, advance_hours):
        """Use the instant selected before provider requests; retain legacy direct calls."""
        from datetime import timedelta, timezone
        from modules.cloud_forecast import utc_time
        if isinstance(weather_data, dict) and 'forecast_target_at' in weather_data:
            evaluated_at = utc_time(weather_data['forecast_target_at'])
            if evaluated_at is None:
                raise ValueError('forecast_target_at must be a timezone-aware ISO datetime')
            return evaluated_at
        return datetime.now(timezone.utc) + timedelta(hours=advance_hours)

    def _calculate_all_factors(self, weather_data, forecast_data, ninday_data, prediction_type, advance_hours,
                               *, time_result=None):
        """計算所有因子分數"""
        
        factors = {}
        
        # 1. 時間因子
        if time_result is None:
            time_result = self.advanced_predictor.calculate_advanced_time_factor(
                prediction_type=prediction_type, advance_hours=advance_hours,
                evaluated_at=self._resolve_evaluated_at(weather_data, advance_hours)
            )
        factors['time'] = time_result['score']
        
        # 2. 溫度因子
        factors['temperature'] = self._calculate_temperature_factor(weather_data)
        
        # 3. 濕度因子
        factors['humidity'] = self._calculate_humidity_factor(weather_data)
        
        # 4. 能見度因子
        factors['visibility'] = self._calculate_visibility_factor(weather_data, advance_hours)
        
        # 5. 氣壓因子
        factors['pressure'] = self._calculate_pressure_factor(weather_data)
        
        # 6. 雲層因子
        factors['cloud'] = self._calculate_cloud_factor(forecast_data, weather_data)
        
        # 7. UV指數因子
        factors['uv'] = self._calculate_uv_factor(weather_data)
        
        # 8. 風速因子
        factors['wind'] = self._calculate_wind_factor(weather_data)
        
        # 9. 空氣品質因子
        factors['air_quality'] = self._calculate_air_quality_factor(weather_data)
        
        return factors
    
    def _calculate_temperature_factor(self, weather_data):
        """計算溫度因子 (0-15分)"""
        if not weather_data or 'temperature' not in weather_data:
            return None
        
        try:
            # 獲取香港天文台溫度
            from modules.prediction_quality import weather_value
            hko_temp = weather_value(weather_data, 'temperature')
            if hko_temp is None or not -50 <= hko_temp <= 60:
                return None
            
            # 溫度評分邏輯（收緊標準）
            if 26 <= hko_temp <= 31:
                return 15  # 理想溫度（最佳燒天溫度）
            elif 24 <= hko_temp <= 33:
                return 12  # 適合溫度
            elif 20 <= hko_temp <= 35:
                return 7   # 可接受溫度
            elif 15 <= hko_temp <= 38:
                return 3   # 邊緣條件
            else:
                return 1   # 過高或過低
                
        except:
            return None
    
    def _calculate_humidity_factor(self, weather_data):
        """計算濕度因子 (0-20分)"""
        if not weather_data or 'humidity' not in weather_data:
            return None
        
        try:
            # 獲取香港天文台濕度
            from modules.prediction_quality import weather_value
            hko_humidity = weather_value(weather_data, 'humidity')
            if hko_humidity is None or not 0 <= hko_humidity <= 100:
                return None
            
            # 濕度評分邏輯（收緊標準）
            if 55 <= hko_humidity <= 70:
                return 20  # 理想濕度（最佳燒天濕度）
            elif 50 <= hko_humidity <= 75:
                return 16  # 良好濕度
            elif 45 <= hko_humidity <= 80:
                return 12  # 可接受濕度
            elif 40 <= hko_humidity <= 85:
                return 7   # 邊緣條件
            elif 30 <= hko_humidity <= 90:
                return 3   # 過高或過低
            else:
                return 1   # 極端濕度
                
        except:
            return None
    
    def _calculate_visibility_factor(self, weather_data, advance_hours=0):
        """Rain proxy (0–20), capped by reference-station visibility in current mode."""
        try:
            score = None
            
            # 檢查降雨量
            if 'rainfall' in weather_data and 'data' in weather_data['rainfall']:
                total_rainfall = highest_rainfall(weather_data)
                if total_rainfall is None:
                    return score
                
                if total_rainfall == 0:
                    score = 20  # 無雨只代表降雨遮擋部分滿分。
                elif total_rainfall < 2:
                    score = 15  # 極輕微降雨
                elif total_rainfall < 5:
                    score = 10  # 輕微降雨
                elif total_rainfall < 10:
                    score = 6   # 中度降雨
                elif total_rainfall < 20:
                    score = 3   # 大雨
                else:
                    score = 1   # 暴雨，能見度極差
            
            if score is not None and advance_hours == 0:
                from modules.visibility_observations import reference_visibility, visibility_score_cap
                reading = reference_visibility(weather_data)
                if reading is not None:
                    score = min(score, visibility_score_cap(reading['value']))
            return score
            
        except:
            return None
    
    def _calculate_pressure_factor(self, weather_data):
        """計算氣壓因子 (0-10分)"""
        if not weather_data:
            return None
        
        try:
            # 檢查簡化數據格式
            from modules.hourly_weather import model_reading
            if weather_data.get('hourly_weather_forecast'):
                reading = model_reading(weather_data, 'pressure')
                if reading is None:
                    return None
                pressure_value = reading['value']
            elif weather_data.get('pressure_observation'):
                from modules.environmental_observations import fresh_observation
                from datetime import timezone
                reading = fresh_observation(weather_data['pressure_observation'], datetime.now(timezone.utc), 30)
                if reading is None:
                    return None
                pressure_value = reading['value']
            elif number(weather_data.get('pressure')) is not None and 850 <= weather_data['pressure'] <= 1100:
                pressure_value = float(weather_data['pressure'])
            else:
                # 檢查複雜數據格式
                return None
            
            # 氣壓評分邏輯 (hPa)
            if pressure_value >= 1020:
                score = 10  # 高氣壓，天氣穩定，有利燒天
            elif pressure_value >= 1013:
                score = 8   # 正常氣壓
            elif pressure_value >= 1000:
                score = 6   # 稍低氣壓
            elif pressure_value >= 990:
                score = 4   # 低氣壓，天氣不穩定
            else:
                score = 2   # 極低氣壓，風暴天氣
                
            return score
            
        except:
            return None
    
    def _calculate_cloud_factor(self, forecast_data, weather_data=None):
        """計算雲層因子 (0-35分) - 最重要因子（已修正邏輯）"""
        from modules.cloud_forecast import score_cloud_layers, valid_cloud_forecast
        weather = weather_data or {}
        cloud = weather.get('cloud_forecast')
        layered_score = score_cloud_layers(cloud) if valid_cloud_forecast(cloud, weather.get('forecast_target_at')) else None
        if layered_score is not None:
            from modules.sunward_clouds import sunward_multiplier
            multiplier = sunward_multiplier(weather.get('sunward_cloud_forecast'),
                                            weather.get('forecast_target_at'))
            return round(layered_score * multiplier, 2) if multiplier is not None else layered_score
        if not forecast_data or 'forecastDesc' not in forecast_data:
            return None
        
        try:
            desc = forecast_data['forecastDesc'].lower()
            
            # 雲層評分邏輯（修正：多雲才高分，晴天低分）
            # 燒天需要雲層！無雲=無燒天
            if '部分時間有陽光' in desc:
                return 35  # 理想：有雲有陽光（滿分）
            elif '短暫時間有陽光' in desc:
                return 32  # 優秀：較多雲有陽光
            elif '大致多雲' in desc:
                return 28  # 良好：多雲
            elif '多雲' in desc:
                return 25  # 適合：多雲
            elif '大致天晴' in desc:
                return 18  # 可接受：少量雲
            elif '密雲' in desc or '陰天' in desc:
                return 12  # 太多雲，光線不足
            elif '晴朗' in desc or '天晴' in desc:
                return 3   # 無雲無燒天！
            elif '有雨' in desc:
                return 2   # 下雨影響拍攝
            elif '大雨' in desc or '暴雨' in desc:
                return 1   # 大雨完全無法拍攝
            else:
                return None  # 未識別文字不補分
                
        except:
            return None
    
    def _calculate_uv_factor(self, weather_data):
        """計算UV指數因子 (0-2分) - 降低重要性"""
        if not weather_data or 'uvindex' not in weather_data:
            return None
        
        try:
            uv_data = weather_data['uvindex']['data'][0]
            uv_value = number(uv_data.get('value'))
            if uv_value is None or not 0 <= uv_value <= 30:
                return None
            
            # UV指數評分邏輯（降低分數範圍）
            # UV只是參考指標，不是決定性因素
            if uv_value >= 5:
                return 2   # 有陽光
            elif uv_value >= 3:
                return 1.5
            elif uv_value >= 1:
                return 1
            else:
                return 0.5 # 陰天
                
        except:
            return None
    
    def _calculate_wind_factor(self, weather_data):
        """計算風速因子 (0-15分)"""
        if not weather_data:
            return None
        
        try:
            from modules.prediction_quality import weather_value
            wind_speed = weather_value(weather_data, 'wind_speed')
            # 每日預報風級範圍不是實測風速，不取中點冒充讀數。
            if wind_speed is None or not 0 <= wind_speed <= 300:
                return None
            
            # 風速評分邏輯（收緊標準）
            if 6 <= wind_speed <= 12:
                return 15  # 理想風速（微風擴散雲層）
            elif 4 <= wind_speed <= 16:
                return 12  # 良好風速
            elif 2 <= wind_speed <= 20:
                return 9   # 可接受風速
            elif wind_speed <= 25:
                return 5   # 風速偏大
            elif wind_speed <= 30:
                return 2   # 強風影響拍攝
            else:
                return 1   # 烈風不利拍攝
                
        except:
            return None
    
    def _calculate_air_quality_factor(self, weather_data):
        """計算空氣品質因子 (0-15分)"""
        try:
            # 使用空氣品質獲取器
            air_quality_data = weather_data.get('air_quality', {})
            if not isinstance(air_quality_data, dict):
                return None
            if air_quality_data.get('source_kind') == 'observed':
                from modules.environmental_observations import fresh_observation
                from datetime import timezone
                if fresh_observation(air_quality_data, datetime.now(timezone.utc), 120) is None:
                    return None
            aqhi = number(air_quality_data.get('aqhi'))
            if aqhi is None or not 1 <= aqhi <= 11:
                return None
            
            # AQHI評分邏輯
            if aqhi <= 3:
                return 15  # 優良空氣
            elif aqhi <= 6:
                return 12  # 良好空氣
            elif aqhi <= 7:
                return 8   # 一般空氣
            elif aqhi <= 10:
                return 5   # 不佳空氣
            else:
                return 2   # 極差空氣
                
        except:
            return None
    
    def _get_ml_score(self, weather_data, forecast_data, diagnostics=None):
        """現有模型以模擬資料訓練，且沿用缺失特徵補值；暫停參與正式評分。"""
        if diagnostics is not None:
            diagnostics['ml_score_source'] = 'unavailable'
            diagnostics['ml_unavailable_reason'] = '現有ML模型以模擬資料訓練，尚未驗證缺失輸入及目標時段；暫不參與評分，不補50分。'
        return None
    
    def _determine_weights(self, advance_hours):
        """確定權重配置"""
        if 1 <= advance_hours <= 2:
            return self.SCORING_CONFIG['ml_weights']['golden_hour']
        elif advance_hours > 0:
            return self.SCORING_CONFIG['ml_weights']['advance']
        else:
            return self.SCORING_CONFIG['ml_weights']['immediate']
    
    def _apply_adjustments(self, score, weather_data, forecast_data, use_seasonal, result):
        """應用各種調整係數 - 使用加減分數避免疊加效應"""
        adjusted_score = score
        adjustments = {}
        total_adjustment = 0  # 記錄總調整分數
        
        # 舊雲厚度流程含預設值，暫停額外加減分。
        result['cloud_adjustment_status'] = 'unavailable'

        # 2. 季節調整
        if use_seasonal:
            from zoneinfo import ZoneInfo
            month = datetime.fromisoformat(result['prediction_info']['evaluated_at']).astimezone(
                ZoneInfo('Asia/Hong_Kong')).month
            if month in [6, 7, 8]:  # 夏季
                adjustment = self.SCORING_CONFIG['adjustment_factors']['seasonal_summer']
                total_adjustment += adjustment
                adjustments['seasonal'] = f'夏季加分 {adjustment:+.0f}分'
            elif month in [12, 1, 2]:  # 冬季
                adjustment = self.SCORING_CONFIG['adjustment_factors']['seasonal_winter']
                total_adjustment += adjustment
                adjustments['seasonal'] = f'冬季調整 {adjustment:+.0f}分'
        
        # 應用總調整分數
        adjusted_score = score + total_adjustment
        adjustments['total_adjustment'] = f'總調整: {total_adjustment:+.0f}分'
        adjustments['numeric_total'] = total_adjustment
        
        result['adjustments'] = adjustments
        return adjusted_score
    
    def _generate_analysis(self, result, weather_data, forecast_data, advance_hours=0):
        """生成分析結果"""
        analysis = {
            'score_breakdown': {
                'traditional_raw': result['traditional_score'],
                'traditional_normalized': result['traditional_normalized'],
                'ml_score': result['ml_score'],
                'weighted_score': result['weighted_score'],
                'final_score': result['final_score']
            },
            'top_factors': [],
            'recommendation': '',
            'confidence': 'limited'
        }
        
        # 找出得分最高的因子
        factor_scores = result['factor_scores']
        sorted_factors = sorted(((key, value) for key, value in factor_scores.items() if value is not None), key=lambda x: x[1], reverse=True)
        
        factor_names = {
            'time': '時間因子',
            'temperature': '溫度因子', 
            'humidity': '濕度因子',
            'visibility': '降雨遮擋參考',
            'cloud': '雲層因子',
            'uv': 'UV指數因子',
            'wind': '風速因子',
            'air_quality': '空氣品質因子'
        }
        
        analysis['top_factors'] = [
            {'name': factor_names.get(factor, factor), 'score': score, 'max': self.SCORING_CONFIG['factor_max_scores'].get(factor, 0)}
            for factor, score in sorted_factors[:3]
        ]
        
        # 生成建議；資料覆蓋不足時不能以低分推斷燒天機會。
        final_score = result['final_score']
        if result.get('input_coverage', {}).get('missing_factors'):
            analysis['recommendation'] = '資料有限，缺失因子不補分；先查看天空實況，再更新觀賞時段條件。'
        elif final_score >= 70:
            analysis['recommendation'] = '建議準備相機，前往拍攝地點'
        elif final_score >= 50:
            analysis['recommendation'] = '密切關注天空變化，準備拍攝'
        elif final_score >= 30:
            analysis['recommendation'] = '等待更好的時段或明天'
        else:
            analysis['recommendation'] = '今日燒天機會較低，查看明日預報'
        
        # 生成智能分析摘要
        top_factor = sorted_factors[0] if sorted_factors else ('unknown', 0)
        top_factor_name = factor_names.get(top_factor[0], '未知因子')
        
        ml_score = result['ml_score']
        traditional_score = result['traditional_score']
        
        # 構建摘要文字
        summary_parts = []
        
        # 總體評估
        if result.get('input_coverage', {}).get('missing_factors'):
            summary_parts.append('資料有限；低分亦可能反映資料不足')
        elif final_score >= 70:
            summary_parts.append("🔥 燒天條件極佳")
        elif final_score >= 50:
            summary_parts.append("🌅 燒天條件良好")
        elif final_score >= 30:
            summary_parts.append("⛅ 燒天條件一般")
        else:
            summary_parts.append("☁️ 燒天條件較差")
        
        # AI vs 傳統分析對比
        if ml_score is None:
            summary_parts.append('ML未參與；缺失因子不補分，總分上限維持150')
        elif abs(ml_score - result['traditional_normalized']) > 20:
            if ml_score > traditional_score:
                summary_parts.append("AI模型較樂觀")
            else:
                summary_parts.append("AI模型較保守")
        else:
            summary_parts.append("AI與傳統算法結果一致")
        
        # 關鍵因子分析
        summary_parts.append(f"關鍵因子: {top_factor_name}({top_factor[1]:.0f}分)")
        
        # 時段分析
        if advance_hours > 0:
            summary_parts.append(f"{advance_hours}小時後條件推算（評估時間見上方）")
        else:
            summary_parts.append("當前條件評估（評估時間見上方）")
            
        analysis['summary'] = " | ".join(summary_parts)
        
        return analysis

# 延遲初始化全域實例
_unified_scorer = None

def get_unified_scorer():
    """獲取統一計分器實例（延遲初始化）"""
    global _unified_scorer
    if _unified_scorer is None:
        _unified_scorer = UnifiedBurnskyScorer()
    return _unified_scorer

def calculate_burnsky_score_unified(weather_data, forecast_data, ninday_data, 
                                   prediction_type='sunset', advance_hours=0):
    """
    統一燒天計分介面 - 取代所有舊版本
    
    這是新的標準計分方法，整合了所有現有算法的優點
    """
    scorer = get_unified_scorer()
    return scorer.calculate_unified_score(
        weather_data, forecast_data, ninday_data, 
        prediction_type, advance_hours
    )
