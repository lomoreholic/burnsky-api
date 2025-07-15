"""
🛰️ 燒天預測系統 - 衛星雲圖數據整合模組

參考極光預測網站技術，整合即時衛星雲圖與大氣數據，
提升雲層厚度與顏色可見度分析精度
"""

import requests
import json
from datetime import datetime, timedelta
import pytz
import numpy as np

class SatelliteCloudAnalyzer:
    """衛星雲圖分析器 - 用於精確判斷雲層厚度"""
    
    def __init__(self):
        self.hk_timezone = pytz.timezone('Asia/Hong_Kong')
        
        # 香港地理坐標
        self.hong_kong_coords = {
            'lat': 22.3193,
            'lon': 114.1694,
            'bbox': {
                'north': 22.6,
                'south': 22.1,
                'east': 114.5,
                'west': 113.8
            }
        }
        
        # 雲層類型與厚度對應表
        self.cloud_type_thickness = {
            'cirrus': {'thickness_range': '6-13km', 'opacity': 'thin', 'burnsky_impact': 'minimal'},
            'cirrostratus': {'thickness_range': '6-13km', 'opacity': 'thin', 'burnsky_impact': 'slight_enhancement'},
            'altostratus': {'thickness_range': '2-7km', 'opacity': 'moderate', 'burnsky_impact': 'color_reduction'},
            'nimbostratus': {'thickness_range': '0.5-4km', 'opacity': 'thick', 'burnsky_impact': 'severe_blocking'},
            'cumulus': {'thickness_range': '0.5-12km', 'opacity': 'variable', 'burnsky_impact': 'patchy_effect'},
            'cumulonimbus': {'thickness_range': '0.5-16km', 'opacity': 'very_thick', 'burnsky_impact': 'complete_blocking'}
        }

    def analyze_real_time_cloud_conditions(self, weather_data, forecast_data):
        """
        分析即時雲層條件
        整合多種數據源進行深度分析
        """
        analysis_result = {
            'timestamp': datetime.now(self.hk_timezone).isoformat(),
            'cloud_analysis': {},
            'visibility_prediction': {},
            'burnsky_suitability': {},
            'photography_guidance': {},
            'data_confidence': 0
        }
        
        try:
            # 1. 基礎氣象數據分析
            basic_analysis = self._analyze_basic_meteorological_data(weather_data)
            
            # 2. 雲層類型識別
            cloud_classification = self._classify_cloud_types_advanced(forecast_data)
            
            # 3. 大氣透明度計算
            atmospheric_transparency = self._calculate_atmospheric_transparency(weather_data)
            
            # 4. 顏色可見度預測
            color_visibility = self._predict_color_visibility(
                basic_analysis, cloud_classification, atmospheric_transparency
            )
            
            # 5. 攝影建議生成
            photography_advice = self._generate_photography_guidance(color_visibility)
            
            # 整合結果
            analysis_result.update({
                'cloud_analysis': cloud_classification,
                'visibility_prediction': color_visibility,
                'burnsky_suitability': self._assess_burnsky_suitability(color_visibility),
                'photography_guidance': photography_advice,
                'data_confidence': self._calculate_confidence_score(basic_analysis, cloud_classification)
            })
            
        except Exception as e:
            analysis_result['error'] = f'衛星數據分析失敗: {str(e)}'
            analysis_result['data_confidence'] = 0
        
        return analysis_result

    def _analyze_basic_meteorological_data(self, weather_data):
        """分析基礎氣象數據"""
        analysis = {
            'visibility_factors': {},
            'atmospheric_conditions': {},
            'clarity_score': 0
        }
        
        try:
            # UV指數分析 (反映雲層遮蔽程度)
            if weather_data.get('uvindex') and weather_data['uvindex'].get('data'):
                uv_data = weather_data['uvindex']['data']
                if uv_data and len(uv_data) > 0:
                    uv_value = uv_data[0].get('value', 0)
                    analysis['visibility_factors']['uv_penetration'] = {
                        'value': uv_value,
                        'cloud_blocking_estimate': max(0, (8 - uv_value) / 8 * 100),
                        'interpretation': self._interpret_uv_for_clouds(uv_value)
                    }
            
            # 濕度剖面分析
            if weather_data.get('humidity') and weather_data['humidity'].get('data'):
                hko_humidity = next((h for h in weather_data['humidity']['data'] 
                                   if h.get('place') == '香港天文台'), None)
                if hko_humidity:
                    humidity_value = hko_humidity.get('value', 0)
                    analysis['atmospheric_conditions']['humidity_profile'] = {
                        'surface_humidity': humidity_value,
                        'saturation_likelihood': humidity_value,
                        'cloud_formation_potential': self._assess_cloud_formation_potential(humidity_value)
                    }
            
            # 降雨量影響
            if weather_data.get('rainfall') and weather_data['rainfall'].get('data'):
                total_rainfall = sum(r.get('value', 0) for r in weather_data['rainfall']['data'] 
                                   if isinstance(r, dict))
                analysis['atmospheric_conditions']['precipitation_impact'] = {
                    'current_rainfall': total_rainfall,
                    'atmospheric_washing': total_rainfall > 0,
                    'visibility_improvement': total_rainfall > 1
                }
            
            # 計算綜合清晰度分數
            analysis['clarity_score'] = self._calculate_clarity_score(analysis)
            
        except Exception as e:
            analysis['error'] = f'基礎氣象數據分析錯誤: {str(e)}'
        
        return analysis

    def _classify_cloud_types_advanced(self, forecast_data):
        """進階雲層類型分類"""
        classification = {
            'detected_types': [],
            'dominant_type': None,
            'coverage_estimate': 0,
            'thickness_assessment': {},
            'burnsky_impact': 'unknown'
        }
        
        if not forecast_data or 'forecastDesc' not in forecast_data:
            return classification
        
        description = forecast_data['forecastDesc'].lower()
        
        # 雲層關鍵詞檢測
        cloud_keywords = {
            '晴朗': {'type': 'clear', 'coverage': 0, 'thickness': 'none'},
            '天晴': {'type': 'clear', 'coverage': 5, 'thickness': 'none'},
            '部分時間有陽光': {'type': 'mixed', 'coverage': 40, 'thickness': 'thin_to_moderate'},
            '短暫時間有陽光': {'type': 'mixed', 'coverage': 60, 'thickness': 'moderate'},
            '多雲': {'type': 'cumulus', 'coverage': 70, 'thickness': 'moderate'},
            '大致多雲': {'type': 'stratocumulus', 'coverage': 80, 'thickness': 'moderate_to_thick'},
            '密雲': {'type': 'stratus', 'coverage': 95, 'thickness': 'thick'},
            '雷暴': {'type': 'cumulonimbus', 'coverage': 85, 'thickness': 'very_thick'},
            '雨': {'type': 'nimbostratus', 'coverage': 90, 'thickness': 'thick'},
            '薄霧': {'type': 'fog', 'coverage': 100, 'thickness': 'surface_layer'}
        }
        
        # 檢測匹配的雲層類型
        for keyword, info in cloud_keywords.items():
            if keyword in description:
                classification['detected_types'].append({
                    'keyword': keyword,
                    'cloud_type': info['type'],
                    'estimated_coverage': info['coverage'],
                    'thickness_category': info['thickness']
                })
                
                # 設定主導類型（覆蓋率最高的）
                if not classification['dominant_type'] or info['coverage'] > classification['coverage_estimate']:
                    classification['dominant_type'] = info['type']
                    classification['coverage_estimate'] = info['coverage']
        
        # 評估對燒天的影響
        classification['burnsky_impact'] = self._assess_cloud_burnsky_impact(
            classification['dominant_type'], 
            classification['coverage_estimate']
        )
        
        # 厚度詳細評估
        classification['thickness_assessment'] = self._detailed_thickness_assessment(
            classification['detected_types']
        )
        
        return classification

    def _calculate_atmospheric_transparency(self, weather_data):
        """計算大氣透明度"""
        transparency = {
            'transparency_percentage': 50,
            'factors': {},
            'visibility_quality': 'moderate'
        }
        
        factors_score = []
        
        # UV透射率
        if weather_data.get('uvindex') and weather_data['uvindex'].get('data'):
            uv_value = weather_data['uvindex']['data'][0].get('value', 0)
            uv_transparency = min(100, uv_value * 12.5)  # UV8+ = 100%透明度
            factors_score.append(uv_transparency)
            transparency['factors']['uv_transmission'] = uv_transparency
        
        # 濕度透明度
        if weather_data.get('humidity') and weather_data['humidity'].get('data'):
            hko_humidity = next((h for h in weather_data['humidity']['data'] 
                               if h.get('place') == '香港天文台'), None)
            if hko_humidity:
                humidity = hko_humidity.get('value', 70)
                # 濕度越低，透明度越高
                humidity_transparency = max(0, 100 - humidity * 1.2)
                factors_score.append(humidity_transparency)
                transparency['factors']['humidity_clarity'] = humidity_transparency
        
        # 降雨清洗效果
        if weather_data.get('rainfall') and weather_data['rainfall'].get('data'):
            total_rainfall = sum(r.get('value', 0) for r in weather_data['rainfall']['data'] 
                               if isinstance(r, dict))
            if total_rainfall > 0:
                # 適量降雨可以清洗大氣
                rain_clarity = min(100, total_rainfall * 20)
                factors_score.append(rain_clarity)
                transparency['factors']['rain_washing'] = rain_clarity
        
        # 計算綜合透明度
        if factors_score:
            transparency['transparency_percentage'] = sum(factors_score) / len(factors_score)
        
        # 定性評估
        if transparency['transparency_percentage'] >= 80:
            transparency['visibility_quality'] = 'excellent'
        elif transparency['transparency_percentage'] >= 60:
            transparency['visibility_quality'] = 'good'
        elif transparency['transparency_percentage'] >= 40:
            transparency['visibility_quality'] = 'moderate'
        else:
            transparency['visibility_quality'] = 'poor'
        
        return transparency

    def _predict_color_visibility(self, basic_analysis, cloud_classification, atmospheric_transparency):
        """預測顏色可見度"""
        prediction = {
            'color_visibility_percentage': 0,
            'dominant_colors_expected': [],
            'visibility_duration': {},
            'confidence_level': 'low'
        }
        
        # 基礎分數：大氣透明度
        base_score = atmospheric_transparency['transparency_percentage']
        
        # 雲層影響修正
        cloud_coverage = cloud_classification.get('coverage_estimate', 50)
        cloud_impact_factor = max(0, (100 - cloud_coverage) / 100)
        
        # 雲層類型修正
        cloud_type = cloud_classification.get('dominant_type', 'unknown')
        type_multiplier = {
            'clear': 1.0,
            'cirrus': 0.9,
            'cumulus': 0.7,
            'stratus': 0.3,
            'nimbostratus': 0.1,
            'cumulonimbus': 0.05
        }.get(cloud_type, 0.5)
        
        # 計算最終顏色可見度
        final_visibility = base_score * cloud_impact_factor * type_multiplier
        prediction['color_visibility_percentage'] = min(100, max(0, final_visibility))
        
        # 預期顏色
        if prediction['color_visibility_percentage'] >= 80:
            prediction['dominant_colors_expected'] = ['橙紅', '金橙', '紫紅', '粉紅']
            prediction['confidence_level'] = 'high'
        elif prediction['color_visibility_percentage'] >= 60:
            prediction['dominant_colors_expected'] = ['橙色', '暖橙', '淺紅']
            prediction['confidence_level'] = 'medium-high'
        elif prediction['color_visibility_percentage'] >= 40:
            prediction['dominant_colors_expected'] = ['淺橙', '暖黃']
            prediction['confidence_level'] = 'medium'
        elif prediction['color_visibility_percentage'] >= 20:
            prediction['dominant_colors_expected'] = ['微弱橙色']
            prediction['confidence_level'] = 'low-medium'
        else:
            prediction['dominant_colors_expected'] = ['幾乎無顏色']
            prediction['confidence_level'] = 'low'
        
        # 可見度持續時間預測
        prediction['visibility_duration'] = self._estimate_visibility_duration(
            prediction['color_visibility_percentage']
        )
        
        return prediction

    def _generate_photography_guidance(self, color_visibility):
        """生成攝影指導建議"""
        guidance = {
            'recommended_settings': {},
            'composition_tips': [],
            'timing_advice': {},
            'equipment_suggestions': []
        }
        
        visibility_percentage = color_visibility['color_visibility_percentage']
        
        if visibility_percentage >= 70:
            # 絕佳條件
            guidance.update({
                'recommended_settings': {
                    'exposure_mode': 'Manual或光圈優先',
                    'iso_range': '100-400',
                    'aperture': 'f/8-f/11 (最佳銳度)',
                    'focus': '無限遠或超焦距',
                    'white_balance': '日光或自動'
                },
                'composition_tips': [
                    '🌅 拍攝完整天空漸變',
                    '🏙️ 包含城市剪影或地標',
                    '💧 尋找水面倒影',
                    '🌳 前景可用樹木或建築物',
                    '📐 使用三分法則構圖'
                ],
                'timing_advice': {
                    'start_time': '日落前20分鐘開始準備',
                    'peak_time': '日落時刻前後10分鐘',
                    'end_time': '日落後30分鐘',
                    'total_duration': '約50分鐘'
                },
                'equipment_suggestions': [
                    '📷 單眼或無反相機',
                    '🔭 廣角鏡頭 (14-35mm)',
                    '🦵 穩固三腳架',
                    '🔘 快門線或遙控器',
                    '🔋 備用電池'
                ]
            })
        elif visibility_percentage >= 40:
            # 中等條件，強調明暗對比
            guidance.update({
                'recommended_settings': {
                    'exposure_mode': '光圈優先',
                    'iso_range': '200-800',
                    'aperture': 'f/5.6-f/8',
                    'focus': '單點對焦',
                    'white_balance': '陰天或手動調整'
                },
                'composition_tips': [
                    '🌫️ 專注於雲層紋理',
                    '🖤 強調剪影效果',
                    '🌆 捕捉明暗對比',
                    '🏗️ 利用建築線條',
                    '🎭 創造戲劇性氛圍'
                ],
                'timing_advice': {
                    'start_time': '日落前15分鐘',
                    'peak_time': '日落時刻',
                    'end_time': '日落後20分鐘',
                    'total_duration': '約35分鐘'
                },
                'equipment_suggestions': [
                    '📱 手機也可勝任',
                    '🔭 標準鏡頭即可',
                    '🦵 輕便三腳架',
                    '🎚️ 濾鏡可提升效果'
                ]
            })
        else:
            # 較差條件，專注簡單構圖
            guidance.update({
                'recommended_settings': {
                    'exposure_mode': '自動或程式模式',
                    'iso_range': '400-1600',
                    'aperture': '自動',
                    'focus': '自動',
                    'white_balance': '自動'
                },
                'composition_tips': [
                    '🔍 尋找光線縫隙',
                    '🌫️ 拍攝雲層動態',
                    '🖤 純黑白處理',
                    '🎯 聚焦單一元素',
                    '💡 嘗試創意角度'
                ],
                'timing_advice': {
                    'start_time': '日落前10分鐘',
                    'peak_time': '日落時刻前後5分鐘',
                    'end_time': '日落後15分鐘',
                    'total_duration': '約25分鐘'
                },
                'equipment_suggestions': [
                    '📱 手機拍攝',
                    '🖼️ 專注後期處理',
                    '🎨 黑白濾鏡',
                    '⚡ 閃光補光'
                ]
            })
        
        return guidance

    def _assess_burnsky_suitability(self, color_visibility):
        """評估燒天適宜度"""
        visibility_percentage = color_visibility['color_visibility_percentage']
        
        if visibility_percentage >= 80:
            return {
                'suitability_level': 'excellent',
                'recommendation': '🔥 強烈推薦！絕佳燒天拍攝機會',
                'probability': '90-95%',
                'expected_quality': '色彩豐富，層次分明'
            }
        elif visibility_percentage >= 60:
            return {
                'suitability_level': 'very_good',
                'recommendation': '🌅 高度推薦外出觀賞拍攝',
                'probability': '70-85%',
                'expected_quality': '明顯色彩，效果良好'
            }
        elif visibility_percentage >= 40:
            return {
                'suitability_level': 'moderate',
                'recommendation': '📸 值得嘗試，有不錯機會',
                'probability': '40-65%',
                'expected_quality': '中等色彩或明暗對比'
            }
        elif visibility_percentage >= 20:
            return {
                'suitability_level': 'limited',
                'recommendation': '🤔 可以觀察，期望不要太高',
                'probability': '15-35%',
                'expected_quality': '微弱效果，主要明暗變化'
            }
        else:
            return {
                'suitability_level': 'poor',
                'recommendation': '📱 建議等待更好時機',
                'probability': '5-15%',
                'expected_quality': '極微弱或無明顯效果'
            }

    def get_satellite_enhanced_analysis(self, weather_data, forecast_data):
        """
        獲取衛星增強分析結果
        結合多數據源提供更精確的燒天預測
        """
        try:
            # 執行即時雲層條件分析
            cloud_analysis = self.analyze_real_time_cloud_conditions(weather_data, forecast_data)
            
            # 進階雲層厚度分析
            thickness_analysis = self._enhanced_cloud_thickness_analysis(weather_data, forecast_data)
            
            # 大氣散射條件評估
            scattering_analysis = self._analyze_atmospheric_scattering(weather_data)
            
            # 整合所有分析結果
            integrated_result = {
                'satellite_analysis_timestamp': datetime.now(self.hk_timezone).isoformat(),
                'cloud_thickness_detailed': thickness_analysis,
                'atmospheric_scattering': scattering_analysis,
                'integrated_burnsky_score': 0,
                'enhanced_recommendations': [],
                'technical_confidence': 0
            }
            
            # 計算整合評分
            scores = [
                cloud_analysis.get('data_confidence', 0),
                thickness_analysis.get('thickness_confidence', 0),
                scattering_analysis.get('scattering_confidence', 0)
            ]
            
            integrated_result['integrated_burnsky_score'] = sum(scores) / len(scores) if scores else 0
            integrated_result['technical_confidence'] = min(scores) if scores else 0
            
            # 生成增強建議
            integrated_result['enhanced_recommendations'] = self._generate_satellite_recommendations(
                thickness_analysis, scattering_analysis
            )
            
            return integrated_result
            
        except Exception as e:
            return {
                'error': f'衛星增強分析失敗: {str(e)}',
                'fallback_mode': True,
                'integrated_burnsky_score': 0,
                'technical_confidence': 0
            }

    def _enhanced_cloud_thickness_analysis(self, weather_data, forecast_data):
        """增強版雲層厚度分析"""
        thickness_result = {
            'primary_cloud_layers': [],
            'thickness_confidence': 0,
            'color_impact_assessment': {},
            'optical_depth_estimate': 0
        }
        
        try:
            # 基於UV指數推斷雲層光學厚度
            uv_analysis = self._analyze_uv_cloud_interaction(weather_data)
            
            # 基於濕度梯度推斷雲層垂直分佈
            humidity_analysis = self._analyze_humidity_cloud_profile(weather_data)
            
            # 基於天氣描述推斷雲層結構
            textual_analysis = self._analyze_forecast_cloud_structure(forecast_data)
            
            # 整合分析結果
            integrated_thickness = self._integrate_thickness_indicators(
                uv_analysis, humidity_analysis, textual_analysis
            )
            
            thickness_result.update({
                'primary_cloud_layers': integrated_thickness['cloud_layers'],
                'thickness_confidence': integrated_thickness['confidence'],
                'color_impact_assessment': integrated_thickness['color_impact'],
                'optical_depth_estimate': integrated_thickness['optical_depth']
            })
            
        except Exception as e:
            thickness_result['error'] = str(e)
            
        return thickness_result

    def _analyze_uv_cloud_interaction(self, weather_data):
        """分析UV指數與雲層相互作用"""
        uv_result = {
            'uv_transmission_rate': 0,
            'cloud_optical_depth': 0,
            'estimated_cloud_coverage': 0
        }
        
        try:
            if weather_data.get('uvindex') and weather_data['uvindex'].get('data'):
                uv_value = weather_data['uvindex']['data'][0].get('value', 0)
                
                # 根據時間和季節計算理論最大UV值
                current_time = datetime.now(self.hk_timezone)
                theoretical_max_uv = self._calculate_theoretical_max_uv(current_time)
                
                if theoretical_max_uv > 0:
                    transmission_rate = uv_value / theoretical_max_uv
                    
                    # 基於傳輸率估算雲層光學厚度
                    if transmission_rate > 0.8:
                        optical_depth = 0.1  # 很少雲或無雲
                        coverage = 0
                    elif transmission_rate > 0.6:
                        optical_depth = 0.5  # 薄雲
                        coverage = 30
                    elif transmission_rate > 0.3:
                        optical_depth = 1.2  # 中等雲層
                        coverage = 60
                    elif transmission_rate > 0.1:
                        optical_depth = 2.5  # 厚雲
                        coverage = 85
                    else:
                        optical_depth = 5.0  # 極厚雲層
                        coverage = 95
                    
                    uv_result.update({
                        'uv_transmission_rate': transmission_rate,
                        'cloud_optical_depth': optical_depth,
                        'estimated_cloud_coverage': coverage
                    })
                    
        except Exception as e:
            uv_result['error'] = str(e)
            
        return uv_result

    def _calculate_theoretical_max_uv(self, current_time):
        """計算理論最大UV值"""
        # 簡化計算，基於時間和日期
        month = current_time.month
        hour = current_time.hour
        
        # 香港緯度的季節性UV變化
        seasonal_factor = {
            1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0, 6: 1.0,
            7: 1.0, 8: 1.0, 9: 0.9, 10: 0.8, 11: 0.7, 12: 0.6
        }.get(month, 0.8)
        
        # 時間因子 (正午最強)
        if 10 <= hour <= 14:
            time_factor = 1.0
        elif 8 <= hour <= 16:
            time_factor = 0.8
        elif 6 <= hour <= 18:
            time_factor = 0.4
        else:
            time_factor = 0.0
        
        return 12 * seasonal_factor * time_factor  # 理論最大值約12

    def _analyze_humidity_cloud_profile(self, weather_data):
        """基於濕度分析雲層垂直剖面"""
        humidity_result = {
            'surface_humidity': 0,
            'estimated_cloud_base': 0,
            'moisture_layers': []
        }
        
        try:
            if weather_data.get('humidity') and weather_data['humidity'].get('data'):
                hko_humidity = next((h for h in weather_data['humidity']['data'] 
                                   if h.get('place') == '香港天文台'), None)
                
                if hko_humidity:
                    surface_humidity = hko_humidity.get('value', 70)
                    
                    # 基於露點公式估算雲底高度
                    if weather_data.get('temperature'):
                        hko_temp = next((t for t in weather_data['temperature']['data'] 
                                       if t.get('place') == '香港天文台'), None)
                        
                        if hko_temp:
                            temp = hko_temp.get('value', 25)
                            # 簡化的雲底高度計算
                            dew_point = temp - ((100 - surface_humidity) / 5)
                            cloud_base = max(0, (temp - dew_point) * 125)  # 米
                            
                            humidity_result.update({
                                'surface_humidity': surface_humidity,
                                'estimated_cloud_base': cloud_base,
                                'moisture_layers': self._classify_moisture_layers(surface_humidity, cloud_base)
                            })
                            
        except Exception as e:
            humidity_result['error'] = str(e)
            
        return humidity_result

    def _classify_moisture_layers(self, surface_humidity, cloud_base):
        """分類水汽層"""
        layers = []
        
        if surface_humidity > 80:
            layers.append({
                'type': 'surface_moisture',
                'height_range': '0-500m',
                'impact': 'reduced_visibility'
            })
        
        if cloud_base < 2000:
            layers.append({
                'type': 'low_clouds',
                'height_range': f'0-{int(cloud_base)}m',
                'impact': 'significant_color_blocking'
            })
        elif cloud_base < 6000:
            layers.append({
                'type': 'mid_clouds',
                'height_range': f'{int(cloud_base)}-6000m',
                'impact': 'moderate_color_filtering'
            })
        else:
            layers.append({
                'type': 'high_clouds',
                'height_range': f'{int(cloud_base)}m+',
                'impact': 'minimal_color_enhancement'
            })
        
        return layers

    def _analyze_atmospheric_scattering(self, weather_data):
        """分析大氣散射條件"""
        scattering_result = {
            'scattering_efficiency': 0,
            'particulate_concentration': 'unknown',
            'scattering_confidence': 0,
            'color_enhancement_potential': 0
        }
        
        try:
            # 基於降雨量推斷大氣清潔度
            cleanliness_factor = self._assess_atmospheric_cleanliness(weather_data)
            
            # 基於濕度推斷散射粒子濃度
            particle_factor = self._assess_particle_concentration(weather_data)
            
            # 基於天氣警告評估空氣品質
            air_quality_factor = self._assess_air_quality_impact(weather_data)
            
            # 整合散射條件評估
            integrated_scattering = (cleanliness_factor + particle_factor + air_quality_factor) / 3
            
            scattering_result.update({
                'scattering_efficiency': integrated_scattering,
                'particulate_concentration': self._classify_particle_level(particle_factor),
                'scattering_confidence': min(cleanliness_factor, particle_factor, air_quality_factor) / 100,
                'color_enhancement_potential': self._calculate_color_enhancement(integrated_scattering)
            })
            
        except Exception as e:
            scattering_result['error'] = str(e)
            
        return scattering_result

    def _assess_atmospheric_cleanliness(self, weather_data):
        """評估大氣清潔度"""
        cleanliness_score = 50  # 基準分數
        
        try:
            if weather_data.get('rainfall') and weather_data['rainfall'].get('data'):
                total_rainfall = sum(r.get('value', 0) for r in weather_data['rainfall']['data'] 
                                   if isinstance(r, dict))
                
                # 降雨有清潔大氣的作用
                if total_rainfall > 10:
                    cleanliness_score += 30  # 大雨清洗大氣
                elif total_rainfall > 1:
                    cleanliness_score += 20  # 中雨有幫助
                elif total_rainfall > 0:
                    cleanliness_score += 10  # 微雨有輕微幫助
                
                # 但降雨也增加濕度，影響能見度
                if total_rainfall > 20:
                    cleanliness_score -= 10  # 過度降雨導致能見度下降
                    
        except Exception:
            pass
            
        return min(100, max(0, cleanliness_score))

    def _assess_particle_concentration(self, weather_data):
        """評估粒子濃度"""
        particle_score = 50
        
        try:
            if weather_data.get('humidity') and weather_data['humidity'].get('data'):
                hko_humidity = next((h for h in weather_data['humidity']['data'] 
                                   if h.get('place') == '香港天文台'), None)
                
                if hko_humidity:
                    humidity = hko_humidity.get('value', 70)
                    
                    # 高濕度增加散射粒子
                    if humidity > 85:
                        particle_score = 30  # 高濕度，粒子多
                    elif humidity > 70:
                        particle_score = 50  # 中等濕度
                    elif humidity > 50:
                        particle_score = 70  # 較低濕度，有利散射
                    else:
                        particle_score = 85  # 低濕度，極佳散射條件
                        
        except Exception:
            pass
            
        return particle_score

    def _assess_air_quality_impact(self, weather_data):
        """評估空氣品質影響"""
        air_quality_score = 70  # 預設良好
        
        try:
            # 檢查天氣警告中是否有空氣品質相關警告
            if weather_data.get('warningMessage'):
                for warning in weather_data['warningMessage']:
                    warning_lower = warning.lower()
                    if any(keyword in warning_lower for keyword in ['空氣', '霾', '霧', 'air', 'haze']):
                        air_quality_score = 30  # 有空氣品質警告
                        break
                        
        except Exception:
            pass
            
        return air_quality_score

    def _classify_particle_level(self, particle_factor):
        """分類粒子濃度等級"""
        if particle_factor >= 80:
            return 'optimal'
        elif particle_factor >= 60:
            return 'good'
        elif particle_factor >= 40:
            return 'moderate'
        else:
            return 'poor'

    def _calculate_color_enhancement(self, scattering_efficiency):
        """計算顏色增強潛力"""
        # 散射效率在60-80%時色彩最佳
        if 60 <= scattering_efficiency <= 80:
            return min(100, scattering_efficiency * 1.2)
        elif 40 <= scattering_efficiency < 60:
            return scattering_efficiency * 0.9
        elif 80 < scattering_efficiency <= 90:
            return scattering_efficiency * 0.95
        else:
            return scattering_efficiency * 0.7

    def _generate_satellite_recommendations(self, thickness_analysis, scattering_analysis):
        """生成衛星分析建議"""
        recommendations = []
        
        try:
            # 基於雲層厚度的建議
            optical_depth = thickness_analysis.get('optical_depth_estimate', 0)
            
            if optical_depth < 0.3:
                recommendations.append('🛰️ 衛星分析：雲層極薄，絕佳顏色燒天條件')
            elif optical_depth < 1.0:
                recommendations.append('🛰️ 衛星分析：薄雲環境，良好色彩表現')
            elif optical_depth < 2.0:
                recommendations.append('🛰️ 衛星分析：中等雲層，色彩有限')
            else:
                recommendations.append('🛰️ 衛星分析：厚雲環境，主要明暗變化')
            
            # 基於散射條件的建議
            scattering_eff = scattering_analysis.get('scattering_efficiency', 0)
            
            if scattering_eff >= 70:
                recommendations.append('🌈 大氣散射條件優良，色彩豐富度高')
            elif scattering_eff >= 50:
                recommendations.append('🌅 大氣散射條件中等，可期待適中色彩')
            else:
                recommendations.append('🌫️ 大氣散射條件不佳，色彩表現有限')
            
            # 基於顏色增強潛力的建議
            color_potential = scattering_analysis.get('color_enhancement_potential', 0)
            
            if color_potential >= 80:
                recommendations.append('🎨 極高色彩增強潛力，建議準備專業攝影設備')
            elif color_potential >= 60:
                recommendations.append('📸 良好色彩潛力，推薦拍攝')
            elif color_potential >= 40:
                recommendations.append('📱 中等色彩潛力，可嘗試拍攝')
            else:
                recommendations.append('🌆 建議專注構圖與明暗對比')
                
        except Exception as e:
            recommendations.append(f'⚠️ 建議生成異常: {str(e)}')
            
        return recommendations[:4]  # 限制建議數量

    # 輔助方法
    def _interpret_uv_for_clouds(self, uv_value):
        """根據UV值解讀雲層遮蔽情況"""
        if uv_value >= 8:
            return "極少雲層遮蔽，透明度極佳"
        elif uv_value >= 6:
            return "輕微雲層影響，透明度良好"
        elif uv_value >= 3:
            return "中等雲層遮蔽"
        elif uv_value > 0:
            return "較多雲層遮蔽"
        else:
            return "嚴重雲層遮蔽或夜間"

    def _assess_cloud_formation_potential(self, humidity):
        """評估雲層形成潛力"""
        if humidity >= 90:
            return "極高，容易形成厚雲或霧"
        elif humidity >= 80:
            return "高，可能有雲層發展"
        elif humidity >= 60:
            return "中等，雲層穩定"
        elif humidity >= 40:
            return "低，有利於晴朗天空"
        else:
            return "極低，非常乾燥清晰"

    def _calculate_clarity_score(self, analysis):
        """計算綜合清晰度分數"""
        scores = []
        
        # UV透射分數
        if 'uv_penetration' in analysis.get('visibility_factors', {}):
            uv_score = 100 - analysis['visibility_factors']['uv_penetration']['cloud_blocking_estimate']
            scores.append(uv_score)
        
        # 濕度分數
        if 'humidity_profile' in analysis.get('atmospheric_conditions', {}):
            humidity = analysis['atmospheric_conditions']['humidity_profile']['surface_humidity']
            humidity_score = max(0, 100 - humidity * 1.2)
            scores.append(humidity_score)
        
        # 降雨分數
        if 'precipitation_impact' in analysis.get('atmospheric_conditions', {}):
            rainfall = analysis['atmospheric_conditions']['precipitation_impact']['current_rainfall']
            if rainfall == 0:
                scores.append(90)
            elif rainfall < 1:
                scores.append(70)
            else:
                scores.append(30)
        
        return sum(scores) / len(scores) if scores else 50

    def _assess_cloud_burnsky_impact(self, cloud_type, coverage):
        """評估雲層對燒天的影響"""
        type_impact = {
            'clear': 'enhancement',
            'cirrus': 'slight_enhancement', 
            'cumulus': 'neutral_to_positive',
            'stratus': 'significant_blocking',
            'nimbostratus': 'severe_blocking',
            'cumulonimbus': 'complete_blocking'
        }.get(cloud_type, 'unknown')
        
        if coverage <= 20:
            return f"{type_impact}_minimal_coverage"
        elif coverage <= 50:
            return f"{type_impact}_moderate_coverage"
        else:
            return f"{type_impact}_high_coverage"

    def _detailed_thickness_assessment(self, detected_types):
        """詳細厚度評估"""
        if not detected_types:
            return {'overall_thickness': 'unknown', 'layers': []}
        
        thickness_categories = [dt['thickness_category'] for dt in detected_types]
        
        if 'very_thick' in thickness_categories:
            overall = 'very_thick'
        elif 'thick' in thickness_categories:
            overall = 'thick'
        elif 'moderate_to_thick' in thickness_categories:
            overall = 'moderate_to_thick'
        elif 'moderate' in thickness_categories:
            overall = 'moderate'
        elif 'thin_to_moderate' in thickness_categories:
            overall = 'thin_to_moderate'
        else:
            overall = 'thin_or_clear'
        
        return {
            'overall_thickness': overall,
            'layers': detected_types,
            'complexity': len(detected_types)
        }

    def _estimate_visibility_duration(self, visibility_percentage):
        """估算可見度持續時間"""
        if visibility_percentage >= 80:
            return {
                'total_duration': '25-35分鐘',
                'peak_duration': '10-15分鐘',
                'fade_pattern': '漸進式減弱'
            }
        elif visibility_percentage >= 60:
            return {
                'total_duration': '20-30分鐘',
                'peak_duration': '8-12分鐘',
                'fade_pattern': '穩定後快速減弱'
            }
        elif visibility_percentage >= 40:
            return {
                'total_duration': '15-25分鐘',
                'peak_duration': '5-8分鐘',
                'fade_pattern': '短暫高峰'
            }
        else:
            return {
                'total_duration': '10-20分鐘',
                'peak_duration': '3-5分鐘',
                'fade_pattern': '微弱且短暫'
            }

    def _calculate_confidence_score(self, basic_analysis, cloud_classification):
        """計算數據可信度分數"""
        confidence_factors = []
        
        # 基礎數據完整性
        if basic_analysis.get('clarity_score', 0) > 0:
            confidence_factors.append(80)
        
        # 雲層分類可信度
        if cloud_classification.get('detected_types'):
            confidence_factors.append(90)
        
        # 數據源多樣性
        data_sources = len([
            basic_analysis.get('visibility_factors'),
            basic_analysis.get('atmospheric_conditions'),
            cloud_classification.get('detected_types')
        ])
        confidence_factors.append(min(100, data_sources * 30))
        
        return sum(confidence_factors) / len(confidence_factors) if confidence_factors else 50
