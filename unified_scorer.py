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
import warnings
warnings.filterwarnings('ignore')

class UnifiedBurnskyScorer:
    """統一燒天預測計分器"""
    
    def __init__(self):
        """初始化統一計分器"""
        self.advanced_predictor = AdvancedBurnskyPredictor()
        self.air_quality_fetcher = AirQualityFetcher()
        
        # 計分配置
        self.SCORING_CONFIG = {
            # 各因子最大分數
            'factor_max_scores': {
                'time': 25,          # 時間因子
                'temperature': 15,    # 溫度因子
                'humidity': 20,       # 濕度因子
                'visibility': 15,     # 能見度因子
                'cloud': 25,          # 雲層因子 (最重要)
                'pressure': 10,       # 氣壓因子
                'uv': 10,             # UV指數因子
                'wind': 15,           # 風速因子
                'air_quality': 15     # 空氣品質因子
            },
            
            # 權重配置
            'ml_weights': {
                'immediate': {'traditional': 0.45, 'ml': 0.55},      # 即時預測
                'golden_hour': {'traditional': 0.35, 'ml': 0.65},    # 黃金時段(1-2小時)
                'advance': {'traditional': 0.40, 'ml': 0.60}         # 其他提前預測
            },
            
            # 調整係數 - 改為加減分數而非乘數
            'adjustment_factors': {
                'cloud_visibility_low': -10,    # 厚雲扣10分
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
        
        result = {
            'prediction_info': {
                'type': prediction_type,
                'advance_hours': advance_hours,
                'timestamp': datetime.now().isoformat()
            },
            'factor_scores': {},
            'traditional_score': 0,
            'ml_score': 0,
            'final_score': 0,
            'adjustments': {},
            'analysis': {}
        }
        
        try:
            # 1. 計算各個因子分數
            factor_scores = self._calculate_all_factors(
                weather_data, forecast_data, ninday_data, prediction_type, advance_hours
            )
            result['factor_scores'] = factor_scores
            
            # 2. 計算傳統算法總分
            traditional_total = sum(factor_scores.values())
            result['traditional_score'] = traditional_total
            
            # 3. 標準化傳統算法分數 (150分 → 100分)
            traditional_normalized = (traditional_total / self.MAX_TRADITIONAL_SCORE) * 100
            result['traditional_normalized'] = traditional_normalized
            
            # 4. 獲取機器學習分數
            ml_score = self._get_ml_score(weather_data, forecast_data)
            result['ml_score'] = ml_score
            
            # 5. 確定權重並計算加權分數
            weights = self._determine_weights(advance_hours)
            weighted_score = traditional_normalized * weights['traditional'] + ml_score * weights['ml']
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
            result['final_score'] = 0
            return result
    
    def _calculate_all_factors(self, weather_data, forecast_data, ninday_data, prediction_type, advance_hours):
        """計算所有因子分數"""
        
        factors = {}
        
        # 1. 時間因子
        time_result = self.advanced_predictor.calculate_advanced_time_factor(
            prediction_type=prediction_type, advance_hours=advance_hours
        )
        factors['time'] = time_result['score']
        
        # 2. 溫度因子
        factors['temperature'] = self._calculate_temperature_factor(weather_data)
        
        # 3. 濕度因子
        factors['humidity'] = self._calculate_humidity_factor(weather_data)
        
        # 4. 能見度因子
        factors['visibility'] = self._calculate_visibility_factor(weather_data)
        
        # 5. 氣壓因子
        factors['pressure'] = self._calculate_pressure_factor(weather_data)
        
        # 6. 雲層因子
        factors['cloud'] = self._calculate_cloud_factor(forecast_data)
        
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
            return 0
        
        try:
            # 獲取香港天文台溫度
            hko_temp = None
            for temp_record in weather_data['temperature']['data']:
                if temp_record['place'] == '香港天文台':
                    hko_temp = temp_record['value']
                    break
            
            if hko_temp is None:
                # 使用平均溫度
                temps = [record['value'] for record in weather_data['temperature']['data']]
                hko_temp = sum(temps) / len(temps) if temps else 25
            
            # 溫度評分邏輯
            if 25 <= hko_temp <= 32:
                return 15  # 理想溫度
            elif 20 <= hko_temp <= 35:
                return 10  # 適合溫度
            elif 15 <= hko_temp <= 38:
                return 5   # 可接受溫度
            else:
                return 2   # 過高或過低
                
        except:
            return 0
    
    def _calculate_humidity_factor(self, weather_data):
        """計算濕度因子 (0-20分)"""
        if not weather_data or 'humidity' not in weather_data:
            return 0
        
        try:
            # 獲取香港天文台濕度
            hko_humidity = None
            for humidity_record in weather_data['humidity']['data']:
                if humidity_record['place'] == '香港天文台':
                    hko_humidity = humidity_record['value']
                    break
            
            if hko_humidity is None:
                return 0
            
            # 濕度評分邏輯
            if 50 <= hko_humidity <= 70:
                return 20  # 理想濕度
            elif 40 <= hko_humidity <= 80:
                return 15  # 良好濕度
            elif 30 <= hko_humidity <= 90:
                return 10  # 可接受濕度
            else:
                return 5   # 過高或過低
                
        except:
            return 0
    
    def _calculate_visibility_factor(self, weather_data):
        """計算能見度因子 (0-15分)"""
        try:
            score = 10  # 基礎分數
            
            # 檢查降雨量
            if 'rainfall' in weather_data and 'data' in weather_data['rainfall']:
                total_rainfall = 0
                for r in weather_data['rainfall']['data']:
                    if isinstance(r, dict) and 'value' in r and r['value'] > 0:
                        total_rainfall += r['value']
                
                if total_rainfall == 0:
                    score = 15  # 無降雨，能見度佳
                elif total_rainfall < 5:
                    score = 12  # 輕微降雨
                elif total_rainfall < 20:
                    score = 8   # 中度降雨
                else:
                    score = 3   # 大雨，能見度差
            
            return score
            
        except:
            return 5
    
    def _calculate_pressure_factor(self, weather_data):
        """計算氣壓因子 (0-10分)"""
        if not weather_data:
            return 5  # 預設值
        
        try:
            # 檢查簡化數據格式
            if 'pressure' in weather_data and isinstance(weather_data['pressure'], (int, float)):
                pressure_value = float(weather_data['pressure'])
            else:
                # 檢查複雜數據格式
                return 5  # 暫時返回預設值，因為HKO API沒有提供氣壓數據
            
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
            return 5  # 錯誤時返回預設值
    
    def _calculate_cloud_factor(self, forecast_data):
        """計算雲層因子 (0-25分) - 最重要因子"""
        if not forecast_data or 'forecastDesc' not in forecast_data:
            return 0
        
        try:
            desc = forecast_data['forecastDesc'].lower()
            
            # 雲層評分邏輯
            if '晴朗' in desc or '天晴' in desc:
                return 25
            elif '大致天晴' in desc:
                return 22
            elif '部分時間有陽光' in desc:
                return 20
            elif '短暫時間有陽光' in desc:
                return 18
            elif '多雲' in desc:
                return 15
            elif '大致多雲' in desc:
                return 12
            elif '密雲' in desc or '陰天' in desc:
                return 8
            elif '有雨' in desc:
                return 5
            elif '大雨' in desc or '暴雨' in desc:
                return 2
            else:
                return 10  # 預設值
                
        except:
            return 0
    
    def _calculate_uv_factor(self, weather_data):
        """計算UV指數因子 (0-10分)"""
        if not weather_data or 'uvindex' not in weather_data:
            return 5  # 預設值
        
        try:
            uv_data = weather_data['uvindex']['data'][0]
            uv_value = uv_data['value']
            
            # UV指數評分邏輯
            if uv_value >= 8:
                return 10  # 高UV，天氣晴朗
            elif uv_value >= 6:
                return 8
            elif uv_value >= 3:
                return 6
            elif uv_value >= 1:
                return 4
            else:
                return 2   # 極低UV，可能陰天
                
        except:
            return 5
    
    def _calculate_wind_factor(self, weather_data):
        """計算風速因子 (0-15分)"""
        if not weather_data or 'wind' not in weather_data:
            return 8  # 預設值
        
        try:
            wind_data = weather_data['wind']
            wind_speed = wind_data.get('speed', 0)
            
            # 風速評分邏輯 (適中風速最佳)
            if 5 <= wind_speed <= 15:
                return 15  # 理想風速
            elif 2 <= wind_speed <= 20:
                return 12  # 良好風速
            elif wind_speed <= 25:
                return 8   # 可接受風速
            else:
                return 3   # 強風不利拍攝
                
        except:
            return 8
    
    def _calculate_air_quality_factor(self, weather_data):
        """計算空氣品質因子 (0-15分)"""
        try:
            # 使用空氣品質獲取器
            air_quality_data = self.air_quality_fetcher.get_air_quality_score()
            aqhi = air_quality_data.get('aqhi', 5)
            
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
            return 10  # 預設值
    
    def _get_ml_score(self, weather_data, forecast_data):
        """獲取機器學習分數"""
        try:
            ml_result = self.advanced_predictor.predict_ml(weather_data, forecast_data)
            return ml_result.get('ml_burnsky_score', 50)
        except:
            return 50  # 預設值
    
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
        
        # 1. 雲層厚度調整
        cloud_analysis = None
        try:
            cloud_analysis = self.advanced_predictor.analyze_cloud_thickness_and_color_visibility(
                weather_data, forecast_data
            )
            color_visibility = cloud_analysis.get('color_visibility_percentage', 50)
            
            if color_visibility < 30:
                adjustment = self.SCORING_CONFIG['adjustment_factors']['cloud_visibility_low']
                total_adjustment += adjustment
                adjustments['cloud_thickness'] = f'厚雲調整 {adjustment:+.0f}分'
            elif color_visibility > 80:
                adjustment = self.SCORING_CONFIG['adjustment_factors']['cloud_visibility_high']
                total_adjustment += adjustment
                adjustments['cloud_thickness'] = f'極佳條件加分 {adjustment:+.0f}分'
                
        except:
            pass
        
        # 保存雲層分析結果到 result 中
        if cloud_analysis:
            result['cloud_thickness_analysis'] = cloud_analysis
        
        # 2. 季節調整
        if use_seasonal:
            month = datetime.now().month
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
            'confidence': 'high'
        }
        
        # 找出得分最高的因子
        factor_scores = result['factor_scores']
        sorted_factors = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
        
        factor_names = {
            'time': '時間因子',
            'temperature': '溫度因子', 
            'humidity': '濕度因子',
            'visibility': '能見度因子',
            'cloud': '雲層因子',
            'uv': 'UV指數因子',
            'wind': '風速因子',
            'air_quality': '空氣品質因子'
        }
        
        analysis['top_factors'] = [
            {'name': factor_names.get(factor, factor), 'score': score, 'max': self.SCORING_CONFIG['factor_max_scores'].get(factor, 0)}
            for factor, score in sorted_factors[:3]
        ]
        
        # 生成建議
        final_score = result['final_score']
        if final_score >= 70:
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
        if final_score >= 70:
            summary_parts.append("🔥 燒天條件極佳")
        elif final_score >= 50:
            summary_parts.append("🌅 燒天條件良好")
        elif final_score >= 30:
            summary_parts.append("⛅ 燒天條件一般")
        else:
            summary_parts.append("☁️ 燒天條件較差")
        
        # AI vs 傳統分析對比
        if abs(ml_score - traditional_score) > 20:
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
            summary_parts.append(f"提前{advance_hours}小時預測")
        else:
            summary_parts.append("即時分析")
            
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
