"""
🌅 燒天預測系統增強方案 - 雲層厚度與極光預測技術整合

參考極光預測網站的先進技術，提升燒天預測準確性
"""

import requests
import json
from datetime import datetime, timedelta
import numpy as np

class EnhancedBurnskyPredictor:
    def __init__(self):
        """增強版燒天預測器 - 整合多種數據源"""
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.satellite_api = "https://api.nasa.gov/planetary/earth/imagery"
        
        # 雲層厚度分級 (參考極光預測的雲覆蓋分析)
        self.cloud_thickness_levels = {
            'clear': {'opacity': 0-10, 'color_visibility': 100, 'description': '晴空，完全可見顏色變化'},
            'thin_clouds': {'opacity': 10-30, 'color_visibility': 80, 'description': '薄雲，顏色稍有影響'},
            'moderate_clouds': {'opacity': 30-60, 'color_visibility': 50, 'description': '中雲，主要顏色可見'},
            'thick_clouds': {'opacity': 60-80, 'color_visibility': 20, 'description': '厚雲，僅見明暗變化'},
            'overcast': {'opacity': 80-100, 'color_visibility': 5, 'description': '密雲，極難見顏色'}
        }
        
        # 新增數據源 (模擬極光預測網站的多元數據整合)
        self.additional_data_sources = {
            'satellite_imagery': 'NASA MODIS 衛星雲圖',
            'atmospheric_pressure': '大氣壓力變化趨勢',
            'wind_patterns': '高空風向數據',
            'aerosol_index': '大氣懸浮粒子指數',
            'solar_angle': '太陽角度與散射計算',
            'humidity_profile': '垂直濕度剖面',
            'temperature_inversion': '逆溫層分析'
        }

    def analyze_cloud_thickness_and_visibility(self, weather_data, forecast_data):
        """
        分析雲層厚度和顏色可見度
        參考極光預測網站的雲覆蓋分析技術
        """
        analysis = {
            'cloud_thickness': 'unknown',
            'color_visibility_percentage': 0,
            'visibility_type': 'unknown',
            'recommendations': [],
            'detailed_analysis': {}
        }
        
        try:
            # 1. 基於天氣描述判斷雲層厚度
            cloud_keywords = {
                '晴朗': 'clear',
                '天晴': 'clear', 
                '大致天晴': 'thin_clouds',
                '部分時間有陽光': 'thin_clouds',
                '短暫時間有陽光': 'moderate_clouds',
                '多雲': 'moderate_clouds',
                '大致多雲': 'thick_clouds',
                '密雲': 'overcast',
                '陰天': 'overcast'
            }
            
            # 2. 分析當前天氣描述
            if forecast_data and 'forecastDesc' in forecast_data:
                desc = forecast_data['forecastDesc']
                for keyword, thickness in cloud_keywords.items():
                    if keyword in desc:
                        analysis['cloud_thickness'] = thickness
                        cloud_info = self.cloud_thickness_levels[thickness]
                        analysis['color_visibility_percentage'] = cloud_info['color_visibility']
                        analysis['detailed_analysis']['description'] = cloud_info['description']
                        break
            
            # 3. 基於濕度和能見度推斷雲層厚度
            if weather_data:
                humidity_factor = self._analyze_humidity_for_clouds(weather_data)
                uv_factor = self._analyze_uv_for_cloud_thickness(weather_data)
                rainfall_factor = self._analyze_rainfall_for_clouds(weather_data)
                
                # 綜合評估雲層厚度
                thickness_score = humidity_factor + uv_factor + rainfall_factor
                
                if thickness_score >= 80:
                    analysis['cloud_thickness'] = 'overcast'
                    analysis['visibility_type'] = 'brightness_only'
                    analysis['recommendations'].append('🌫️ 雲層過厚，主要觀察明暗變化')
                elif thickness_score >= 60:
                    analysis['cloud_thickness'] = 'thick_clouds'
                    analysis['visibility_type'] = 'limited_colors'
                    analysis['recommendations'].append('🌥️ 厚雲，顏色變化有限')
                elif thickness_score >= 30:
                    analysis['cloud_thickness'] = 'moderate_clouds'
                    analysis['visibility_type'] = 'good_colors'
                    analysis['recommendations'].append('☁️ 中等雲量，主要顏色可見')
                else:
                    analysis['cloud_thickness'] = 'thin_clouds'
                    analysis['visibility_type'] = 'excellent_colors'
                    analysis['recommendations'].append('🌤️ 薄雲或晴空，絕佳顏色效果')
            
            # 4. 生成觀測建議
            visibility_pct = analysis['color_visibility_percentage']
            if visibility_pct >= 80:
                analysis['recommendations'].extend([
                    '📸 絕佳拍攝條件，可捕捉完整色彩變化',
                    '🎨 預期可見：金色、橙色、紅色、紫色漸變'
                ])
            elif visibility_pct >= 50:
                analysis['recommendations'].extend([
                    '📸 良好拍攝條件，主要顏色清晰可見',
                    '🎨 預期可見：橙色、紅色為主，部分金色'
                ])
            elif visibility_pct >= 20:
                analysis['recommendations'].extend([
                    '📸 有限拍攝條件，以剪影和明暗對比為主',
                    '🌆 預期效果：戲劇性明暗變化，少量顏色'
                ])
            else:
                analysis['recommendations'].extend([
                    '📸 考慮延後拍攝，或專注於雲層形態',
                    '🌫️ 預期效果：主要為明暗變化，幾乎無顏色'
                ])
                
        except Exception as e:
            analysis['error'] = f'雲層分析失敗: {str(e)}'
        
        return analysis

    def _analyze_humidity_for_clouds(self, weather_data):
        """基於濕度分析雲層厚度"""
        try:
            if weather_data.get('humidity') and weather_data['humidity'].get('data'):
                hko_humidity = next((h for h in weather_data['humidity']['data'] 
                                   if h.get('place') == '香港天文台'), None)
                if hko_humidity and hko_humidity.get('value'):
                    humidity = hko_humidity['value']
                    if humidity >= 90: return 30  # 高濕度 = 厚雲可能
                    elif humidity >= 70: return 20  # 中濕度 = 中等雲量
                    elif humidity >= 50: return 10  # 適中濕度 = 薄雲
                    else: return 0  # 低濕度 = 晴空
        except:
            pass
        return 15  # 預設中等

    def _analyze_uv_for_cloud_thickness(self, weather_data):
        """基於UV指數推斷雲層厚度"""
        try:
            if weather_data.get('uvindex') and weather_data['uvindex'].get('data'):
                uv_data = weather_data['uvindex']['data']
                if uv_data and len(uv_data) > 0:
                    uv_value = uv_data[0].get('value', 0)
                    if uv_value <= 2: return 30  # 極低UV = 厚雲遮蔽
                    elif uv_value <= 5: return 20  # 低UV = 中等遮蔽
                    elif uv_value <= 7: return 10  # 中UV = 少量遮蔽
                    else: return 0  # 高UV = 晴空
        except:
            pass
        return 15  # 預設中等

    def _analyze_rainfall_for_clouds(self, weather_data):
        """基於降雨量推斷雲層厚度"""
        try:
            if weather_data.get('rainfall') and weather_data['rainfall'].get('data'):
                total_rainfall = sum(r.get('value', 0) for r in weather_data['rainfall']['data'] 
                                   if isinstance(r, dict))
                if total_rainfall > 5: return 40  # 有雨 = 厚雲
                elif total_rainfall > 0: return 20  # 微雨 = 中等雲量
                else: return 0  # 無雨 = 可能晴朗
        except:
            pass
        return 0

    def get_enhanced_prediction_factors(self, weather_data, forecast_data):
        """
        整合多種數據源的增強預測因子
        參考極光預測網站的多元數據分析
        """
        factors = {
            'aurora_inspired_factors': {},
            'advanced_atmospheric_analysis': {},
            'satellite_data_simulation': {},
            'recommendations': []
        }
        
        # 1. 大氣透明度分析 (模擬極光預測的大氣條件分析)
        factors['aurora_inspired_factors']['atmospheric_transparency'] = self._analyze_atmospheric_transparency(weather_data)
        
        # 2. 太陽角度和散射分析
        factors['aurora_inspired_factors']['solar_scattering'] = self._analyze_solar_scattering()
        
        # 3. 風速對雲層移動的影響
        factors['aurora_inspired_factors']['cloud_movement'] = self._analyze_cloud_movement_potential(weather_data)
        
        # 4. 大氣穩定度分析
        factors['advanced_atmospheric_analysis']['stability'] = self._analyze_atmospheric_stability(weather_data)
        
        # 5. 多層雲結構分析
        factors['advanced_atmospheric_analysis']['cloud_layers'] = self._analyze_cloud_layer_structure(weather_data, forecast_data)
        
        return factors

    def _analyze_atmospheric_transparency(self, weather_data):
        """分析大氣透明度 (參考極光預測技術)"""
        transparency = {
            'score': 50,
            'level': 'moderate',
            'factors': [],
            'description': ''
        }
        
        try:
            # 基於多個因子綜合評估大氣透明度
            factors_score = 0
            
            # 濕度影響 (濕度越高，透明度越低)
            if weather_data.get('humidity'):
                hko_humidity = next((h for h in weather_data['humidity']['data'] 
                                   if h.get('place') == '香港天文台'), None)
                if hko_humidity:
                    humidity = hko_humidity.get('value', 60)
                    if humidity <= 40:
                        factors_score += 30
                        transparency['factors'].append('低濕度有利透明度')
                    elif humidity <= 70:
                        factors_score += 15
                        transparency['factors'].append('適中濕度')
                    else:
                        factors_score += 5
                        transparency['factors'].append('高濕度影響透明度')
            
            # UV指數影響 (高UV表示大氣清晰)
            if weather_data.get('uvindex'):
                uv_data = weather_data['uvindex']['data']
                if uv_data and len(uv_data) > 0:
                    uv_value = uv_data[0].get('value', 0)
                    if uv_value >= 8:
                        factors_score += 25
                        transparency['factors'].append('高UV指數，大氣清晰')
                    elif uv_value >= 5:
                        factors_score += 15
                        transparency['factors'].append('中等UV指數')
                    else:
                        factors_score += 5
                        transparency['factors'].append('低UV指數，可能有遮蔽')
            
            # 降雨影響
            if weather_data.get('rainfall'):
                total_rainfall = sum(r.get('value', 0) for r in weather_data['rainfall']['data'] 
                                   if isinstance(r, dict))
                if total_rainfall == 0:
                    factors_score += 20
                    transparency['factors'].append('無降雨，大氣乾淨')
                else:
                    factors_score -= 10
                    transparency['factors'].append('有降雨，影響透明度')
            
            transparency['score'] = min(100, max(0, factors_score))
            
            if transparency['score'] >= 80:
                transparency['level'] = 'excellent'
                transparency['description'] = '極佳透明度，顏色效果絕佳'
            elif transparency['score'] >= 60:
                transparency['level'] = 'good'
                transparency['description'] = '良好透明度，顏色效果佳'
            elif transparency['score'] >= 40:
                transparency['level'] = 'moderate'
                transparency['description'] = '中等透明度，部分顏色可見'
            else:
                transparency['level'] = 'poor'
                transparency['description'] = '透明度差，主要為明暗變化'
                
        except Exception as e:
            transparency['error'] = f'透明度分析失敗: {str(e)}'
        
        return transparency

    def _analyze_solar_scattering(self):
        """分析太陽角度和光線散射效果"""
        now = datetime.now()
        
        scattering = {
            'solar_elevation': 0,
            'scattering_potential': 'unknown',
            'optimal_time_remaining': 0,
            'color_prediction': []
        }
        
        # 這裡可以整合更精確的太陽位置計算
        # 目前簡化處理
        hour = now.hour
        
        if 17 <= hour <= 19:  # 日落時段
            scattering['scattering_potential'] = 'high'
            scattering['color_prediction'] = ['金色', '橙色', '紅色', '紫色']
        elif 6 <= hour <= 8:  # 日出時段
            scattering['scattering_potential'] = 'high'
            scattering['color_prediction'] = ['淡黃', '橙色', '粉紅']
        else:
            scattering['scattering_potential'] = 'low'
            scattering['color_prediction'] = ['有限顏色變化']
        
        return scattering

    def _analyze_cloud_movement_potential(self, weather_data):
        """分析雲層移動潛力 (風速影響)"""
        movement = {
            'wind_speed': 0,
            'movement_potential': 'unknown',
            'change_probability': 0,
            'recommendation': ''
        }
        
        # 這裡可以加入風速數據分析
        # 高風速 = 雲層快速移動 = 條件可能快速改變
        movement['recommendation'] = '持續監控天氣變化'
        
        return movement

    def _analyze_atmospheric_stability(self, weather_data):
        """分析大氣穩定度"""
        stability = {
            'level': 'moderate',
            'score': 50,
            'description': '大氣條件穩定',
            'prediction_reliability': 'medium'
        }
        
        # 基於溫度、濕度、氣壓變化分析大氣穩定度
        return stability

    def _analyze_cloud_layer_structure(self, weather_data, forecast_data):
        """分析多層雲結構"""
        layers = {
            'high_clouds': False,
            'mid_clouds': False, 
            'low_clouds': False,
            'structure_type': 'unknown',
            'burnsky_potential': 'unknown'
        }
        
        # 可以根據天氣描述和數據推斷雲層結構
        if forecast_data and 'forecastDesc' in forecast_data:
            desc = forecast_data['forecastDesc']
            if '高雲' in desc or '卷雲' in desc:
                layers['high_clouds'] = True
                layers['burnsky_potential'] = 'excellent'
            if '中雲' in desc:
                layers['mid_clouds'] = True
            if '低雲' in desc or '霧' in desc:
                layers['low_clouds'] = True
                layers['burnsky_potential'] = 'poor'
        
        return layers


def suggest_additional_data_sources():
    """
    建議整合的額外數據源
    參考極光預測網站的數據豐富度
    """
    suggestions = {
        'real_time_satellite': {
            'source': 'NASA MODIS 即時衛星雲圖',
            'benefit': '即時雲層厚度和分布',
            'implementation': 'NASA API 整合',
            'cost': '免費 (有限制)'
        },
        'atmospheric_profile': {
            'source': '垂直大氣剖面數據',
            'benefit': '精確雲層高度和密度',
            'implementation': '氣象探空數據',
            'cost': '中等'
        },
        'aerosol_data': {
            'source': '大氣懸浮粒子監測',
            'benefit': '空氣品質對顏色的影響',
            'implementation': 'EPA 空氣品質API',
            'cost': '免費'
        },
        'solar_activity': {
            'source': '太陽活動數據',
            'benefit': '影響大氣散射效果',
            'implementation': 'NOAA 太陽數據',
            'cost': '免費'
        },
        'high_resolution_forecast': {
            'source': '高解析度數值天氣預報',
            'benefit': '更精確的短期預測',
            'implementation': '商業天氣API',
            'cost': '高'
        },
        'crowd_sourced_reports': {
            'source': '用戶即時觀測回報',
            'benefit': '即時驗證預測準確性',
            'implementation': '手機APP用戶回報系統',
            'cost': '低'
        },
        'webcam_analysis': {
            'source': '即時網路攝影機影像分析',
            'benefit': '即時視覺驗證',
            'implementation': 'AI影像識別',
            'cost': '中等'
        }
    }
    
    return suggestions


def generate_enhanced_prediction_strategy():
    """
    生成增強預測策略
    整合雲層厚度分析和多元數據源
    """
    strategy = {
        'phase_1': {
            'name': '雲層厚度與顏色可見度分析',
            'tasks': [
                '整合現有濕度、UV、降雨數據分析雲層厚度',
                '建立顏色可見度評估系統',
                '區分"顏色燒天"和"明暗燒天"',
                '提供針對性拍攝建議'
            ],
            'timeline': '1-2週',
            'impact': '中等'
        },
        'phase_2': {
            'name': '多元數據源整合',
            'tasks': [
                '整合NASA衛星雲圖API',
                '加入空氣品質數據',
                '分析大氣透明度',
                '建立風速對雲層移動的預測'
            ],
            'timeline': '3-4週', 
            'impact': '高'
        },
        'phase_3': {
            'name': '用戶回報系統',
            'tasks': [
                '建立即時觀測回報功能',
                '機器學習用戶回報數據',
                '動態調整預測權重',
                '建立預測準確度追蹤'
            ],
            'timeline': '4-6週',
            'impact': '很高'
        },
        'phase_4': {
            'name': '極光預測級別優化',
            'tasks': [
                '整合高解析度天氣預報',
                '建立3D大氣模型',
                '預測雲層動態變化',
                '提供時間序列預測'
            ],
            'timeline': '2-3月',
            'impact': '極高'
        }
    }
    
    return strategy
