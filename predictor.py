import math
from datetime import datetime, time
import pytz
from advanced_predictor import AdvancedBurnskyPredictor

# 初始化進階預測器
advanced_predictor = AdvancedBurnskyPredictor()

def calculate_burnsky_score(weather_data, forecast_data, ninday_data):
    """
    計算燒天指數 (0-100分) - 整合進階功能版本
    
    燒天出現的條件：
    1. 實時日落前後 30 分鐘判斷 (時間因子)
    2. 雲層類型分析 (30%-70%)
    3. 高空雲（卷雲、卷層雲）出現
    4. 空氣清晰（能見度高）
    5. 濕度適中（不太高）
    6. 日照時間長（代表天氣好）
    7. 機器學習模型預測
    
    Args:
        weather_data: 即時天氣數據
        forecast_data: 天氣預報數據
        ninday_data: 九天預報數據
    
    Returns:
        tuple: (燒天指數, 分析詳情)
    """
    
    score = 0
    details = {}
    
    # 1. 進階時間因子 (0-25分) - 基於實際日出日落時間
    time_result = advanced_predictor.calculate_time_factor_advanced()
    score += time_result['score']
    details['time_factor'] = time_result
    
    # 2. 溫度因子 (0-15分)
    temp_result = calculate_temperature_factor(weather_data)
    score += temp_result['score']
    details['temperature_factor'] = temp_result
    
    # 3. 濕度因子 (0-20分)
    humidity_result = calculate_humidity_factor(weather_data)
    score += humidity_result['score']
    details['humidity_factor'] = humidity_result
    
    # 4. 能見度/空氣品質因子 (0-15分)
    visibility_result = calculate_visibility_factor(weather_data)
    score += visibility_result['score']
    details['visibility_factor'] = visibility_result
    
    # 5. 進階天氣描述和雲層分析因子 (0-25分)
    if forecast_data and 'forecastDesc' in forecast_data:
        cloud_result = advanced_predictor.analyze_cloud_types(forecast_data['forecastDesc'])
        score += cloud_result['score']
        details['cloud_analysis_factor'] = cloud_result
    else:
        details['cloud_analysis_factor'] = {'score': 0, 'description': '無天氣預報數據'}
    
    # 6. UV指數因子 (0-10分) - 高UV表示日照充足
    uv_result = calculate_uv_factor(weather_data)
    score += uv_result['score']
    details['uv_factor'] = uv_result
    
    # 7. 機器學習預測 (整合所有因子)
    try:
        ml_result = advanced_predictor.predict_ml(weather_data, forecast_data)
        details['ml_prediction'] = ml_result
        
        # 結合傳統算法和機器學習結果
        traditional_score = score
        ml_score = ml_result['ml_burnsky_score']
        
        # 加權平均 (傳統算法 40%, 機器學習 60%)
        final_score = traditional_score * 0.4 + ml_score * 0.6
        
        details['score_breakdown'] = {
            'traditional_score': traditional_score,
            'ml_score': ml_score,
            'final_weighted_score': final_score
        }
        
    except Exception as e:
        final_score = score
        details['ml_prediction'] = {'error': f'機器學習預測失敗: {str(e)}'}
        details['score_breakdown'] = {
            'traditional_score': score,
            'ml_score': 0,
            'final_weighted_score': score
        }
    
    # 確保分數在0-100範圍內
    final_score = max(0, min(100, final_score))
    
    details['total_score'] = final_score
    details['analysis_summary'] = generate_analysis_summary_advanced(details)
    
    return final_score, details

def calculate_time_factor():
    """計算時間因子 - 日落前後30分鐘得分最高"""
    # 使用香港時區
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    now = datetime.now(hk_tz)
    current_hour = now.hour
    current_minute = now.minute
    
    # 香港夏季日落時間大約 19:00-19:30，冬季約 17:30-18:30
    # 這裡使用簡化的計算，實際可以接入日出日落API
    month = now.month
    if 4 <= month <= 9:  # 夏季
        sunset_hour = 19
        sunset_minute = 15
    else:  # 冬季
        sunset_hour = 18
        sunset_minute = 0
    
    # 計算與日落時間的差距（分鐘）
    current_minutes = current_hour * 60 + current_minute
    sunset_minutes = sunset_hour * 60 + sunset_minute
    time_diff = abs(current_minutes - sunset_minutes)
    
    # 日落前後30分鐘內得分最高
    if time_diff <= 30:
        return 20
    elif time_diff <= 60:
        return 15
    elif time_diff <= 120:
        return 10
    else:
        return 5

def calculate_temperature_factor(weather_data):
    """計算溫度因子"""
    if not weather_data or 'temperature' not in weather_data:
        return {'score': 0, 'description': '無溫度數據'}
    
    try:
        # 取香港天文台的溫度
        hko_temp = None
        for temp_record in weather_data['temperature']['data']:
            if temp_record['place'] == '香港天文台':
                hko_temp = temp_record['value']
                break
        
        if hko_temp is None:
            # 如果沒有天文台數據，取平均值
            temps = [record['value'] for record in weather_data['temperature']['data']]
            hko_temp = sum(temps) / len(temps)
        
        # 溫度適中時燒天機率較高
        score = 0
        description = f"目前溫度: {hko_temp}°C"
        
        if 25 <= hko_temp <= 32:
            score = 15
            description += " (理想溫度範圍)"
        elif 20 <= hko_temp <= 35:
            score = 10
            description += " (適合溫度範圍)"
        elif 15 <= hko_temp <= 38:
            score = 5
            description += " (可接受溫度範圍)"
        else:
            score = 2
            description += " (溫度過高或過低)"
        
        return {'score': round(score), 'description': description, 'temperature': hko_temp}
    
    except Exception as e:
        return {'score': 0, 'description': f'溫度數據解析錯誤: {str(e)}'}

def calculate_humidity_factor(weather_data):
    """計算濕度因子 - 濕度適中時得分較高"""
    if not weather_data or 'humidity' not in weather_data:
        return {'score': 0, 'description': '無濕度數據'}
    
    try:
        # 取香港天文台的濕度
        hko_humidity = None
        for humidity_record in weather_data['humidity']['data']:
            if humidity_record['place'] == '香港天文台':
                hko_humidity = humidity_record['value']
                break
        
        if hko_humidity is None:
            return {'score': 0, 'description': '無天文台濕度數據'}
        
        score = 0
        description = f"目前濕度: {hko_humidity}%"
        
        # 濕度50-70%時燒天效果最佳
        if 50 <= hko_humidity <= 70:
            score = 20
            description += " (理想濕度範圍)"
        elif 40 <= hko_humidity <= 80:
            score = 15
            description += " (良好濕度範圍)"
        elif 30 <= hko_humidity <= 90:
            score = 10
            description += " (可接受濕度範圍)"
        else:
            score = 5
            description += " (濕度過高或過低)"
        
        return {'score': round(score), 'description': description, 'humidity': hko_humidity}
    
    except Exception as e:
        return {'score': 0, 'description': f'濕度數據解析錯誤: {str(e)}'}

def calculate_visibility_factor(weather_data):
    """計算能見度因子 - 基於降雨量判斷空氣清晰度"""
    if not weather_data:
        return {'score': 0, 'description': '無天氣數據'}
    
    try:
        score = 10  # 基礎分數
        description = "能見度評估: "
        
        # 檢查降雨量
        if 'rainfall' in weather_data and 'data' in weather_data['rainfall']:
            rainfall_data = weather_data['rainfall']['data']
            total_rainfall = 0
            for r in rainfall_data:
                if isinstance(r, dict) and 'value' in r and r['value'] > 0:
                    total_rainfall += r['value']
            
            if total_rainfall == 0:
                score = 15
                description += "無降雨，空氣清晰"
            elif total_rainfall < 5:
                score = 12
                description += "少量降雨，能見度良好"
            elif total_rainfall < 15:
                score = 8
                description += "中等降雨，能見度一般"
            else:
                score = 3
                description += "大量降雨，能見度較差"
        else:
            description += "無降雨數據，假設能見度良好"
        
        # 檢查天氣警告
        if 'warningMessage' in weather_data and weather_data['warningMessage']:
            score -= 5
            description += "，有天氣警告"
        
        return {'score': round(max(0, score)), 'description': description}
    
    except Exception as e:
        return {'score': 5, 'description': f'能見度評估錯誤: {str(e)}'}

def calculate_weather_description_factor(forecast_data):
    """根據天氣預報描述計算得分"""
    if not forecast_data or 'forecastDesc' not in forecast_data:
        return {'score': 0, 'description': '無天氣預報數據'}
    
    forecast_desc = forecast_data['forecastDesc']
    score = 0
    description = f"預報: {forecast_desc}"
    
    # 正面關鍵字
    positive_keywords = ['多雲', '部分時間有陽光', '短暫時間有陽光', '天晴', '晴朗']
    negative_keywords = ['大雨', '暴雨', '雷暴', '密雲', '陰天']
    
    positive_count = sum(1 for keyword in positive_keywords if keyword in forecast_desc)
    negative_count = sum(1 for keyword in negative_keywords if keyword in forecast_desc)
    
    if positive_count > negative_count:
        score = 20
        description += " (有利燒天條件)"
    elif positive_count == negative_count:
        score = 10
        description += " (中性條件)"
    else:
        score = 5
        description += " (不利燒天條件)"
    
    return {'score': round(score), 'description': description}

def calculate_uv_factor(weather_data):
    """計算UV指數因子 - 高UV表示日照充足"""
    if not weather_data or 'uvindex' not in weather_data:
        return {'score': 0, 'description': '無UV指數數據'}
    
    try:
        uv_data = weather_data['uvindex']
        if 'data' not in uv_data or not uv_data['data']:
            return {'score': 0, 'description': '無UV指數數據'}
        
        uv_value = uv_data['data'][0]['value']
        score = 0
        description = f"UV指數: {uv_value}"
        
        if uv_value >= 8:
            score = 10
            description += " (極高，日照充足)"
        elif uv_value >= 6:
            score = 8
            description += " (高，日照良好)"
        elif uv_value >= 3:
            score = 5
            description += " (中等)"
        else:
            score = 2
            description += " (低，日照不足)"
        
        return {'score': round(score), 'description': description, 'uv_index': uv_value}
    
    except Exception as e:
        return {'score': 0, 'description': f'UV指數解析錯誤: {str(e)}'}

def generate_analysis_summary(details):
    """生成分析摘要"""
    total_score = details['total_score']
    
    summary = []
    
    # 時間因子分析
    if details['time_factor']['score'] >= 15:
        summary.append("✅ 當前時間接近日落黃金時段")
    else:
        summary.append("⏰ 非最佳拍攝時間")
    
    # 濕度因子分析
    if details['humidity_factor']['score'] >= 15:
        summary.append("✅ 濕度條件理想")
    elif details['humidity_factor']['score'] >= 10:
        summary.append("⚠️ 濕度條件尚可")
    else:
        summary.append("❌ 濕度條件不佳")
    
    # 溫度因子分析
    if details['temperature_factor']['score'] >= 10:
        summary.append("✅ 溫度條件良好")
    else:
        summary.append("⚠️ 溫度條件一般")
    
    # 總體建議
    if total_score >= 70:
        summary.append("🔥 強烈建議外出拍攝燒天！")
    elif total_score >= 50:
        summary.append("📸 可以嘗試拍攝，有一定機會")
    else:
        summary.append("📱 建議在室內等待更好的條件")
    
    return summary

def generate_analysis_summary_advanced(details):
    """生成進階分析摘要"""
    total_score = details['total_score']
    
    summary = []
    
    # 時間因子分析 - 基於實際日落時間
    if 'time_factor' in details:
        time_data = details['time_factor']
        if time_data['score'] >= 20:
            summary.append(f"🌅 完美時機！{time_data.get('description', '')}")
        elif time_data['score'] >= 15:
            summary.append(f"⏰ 良好時段，{time_data.get('description', '')}")
        else:
            summary.append(f"⏰ {time_data.get('description', '非最佳拍攝時間')}")
    
    # 濕度因子分析
    if 'humidity_factor' in details and details['humidity_factor']['score'] >= 15:
        summary.append("✅ 濕度條件理想")
    elif 'humidity_factor' in details and details['humidity_factor']['score'] >= 10:
        summary.append("⚠️ 濕度條件尚可")
    else:
        summary.append("❌ 濕度條件不佳")
    
    # 溫度因子分析
    if 'temperature_factor' in details and details['temperature_factor']['score'] >= 10:
        summary.append("✅ 溫度條件良好")
    else:
        summary.append("⚠️ 溫度條件一般")
    
    # 雲層分析
    if 'cloud_analysis_factor' in details:
        cloud_data = details['cloud_analysis_factor']
        if cloud_data['score'] >= 18:
            summary.append("☁️ 雲層條件極佳")
        elif cloud_data['score'] >= 12:
            summary.append("☁️ 雲層條件良好")
        else:
            summary.append("☁️ 雲層條件一般")
        
        # 添加具體的雲層類型信息
        if 'favorable_conditions' in cloud_data and cloud_data['favorable_conditions']:
            summary.append(f"🌤️ 有利條件: {', '.join(cloud_data['favorable_conditions'])}")
    
    # 機器學習預測結果
    if 'ml_prediction' in details and 'ml_burnsky_score' in details['ml_prediction']:
        ml_score = details['ml_prediction']['ml_burnsky_score']
        ml_class = details['ml_prediction'].get('ml_class', 0)
        
        if ml_class == 2:
            summary.append("🤖 AI預測: 高機率燒天")
        elif ml_class == 1:
            summary.append("🤖 AI預測: 中等機率燒天")
        else:
            summary.append("🤖 AI預測: 低機率燒天")
    
    # 綜合評分分析
    if 'score_breakdown' in details:
        breakdown = details['score_breakdown']
        traditional = breakdown['traditional_score']
        ml_score = breakdown['ml_score']
        
        if abs(traditional - ml_score) <= 10:
            summary.append("⚖️ 傳統算法與AI預測一致")
        elif traditional > ml_score:
            summary.append("📊 傳統算法較樂觀")
        else:
            summary.append("🤖 AI模型較樂觀")
    
    # 總體建議
    if total_score >= 80:
        summary.append("🔥 強烈建議立即外出拍攝燒天！")
    elif total_score >= 70:
        summary.append("📸 高度推薦外出拍攝")
    elif total_score >= 50:
        summary.append("📸 可以嘗試拍攝，有一定機會")
    elif total_score >= 30:
        summary.append("🤔 建議等待更好的條件")
    else:
        summary.append("📱 建議在室內等待，條件不佳")
    
    return summary

def calculate_burnsky_score_advanced(weather_data, forecast_data, ninday_data, 
                                   prediction_type='sunset', advance_hours=0):
    """
    進階燒天指數計算 - 支援日出/日落和提前預測
    
    Args:
        weather_data: 即時天氣數據
        forecast_data: 天氣預報數據
        ninday_data: 九天預報數據
        prediction_type: 'sunrise' 或 'sunset'
        advance_hours: 提前預測小時數 (0-24)
    
    Returns:
        tuple: (燒天指數, 詳細分析, 燒天程度, 顏色預測)
    """
    
    score = 0
    details = {}
    
    # 1. 進階時間因子 - 支援日出/日落和提前預測
    time_result = advanced_predictor.calculate_advanced_time_factor(
        prediction_type=prediction_type, 
        advance_hours=advance_hours
    )
    score += time_result['score']
    details['time_factor'] = time_result
    
    # 2. 溫度因子 (0-15分)
    temp_result = calculate_temperature_factor(weather_data)
    score += temp_result['score']
    details['temperature_factor'] = temp_result
    
    # 3. 濕度因子 (0-20分)
    humidity_result = calculate_humidity_factor(weather_data)
    score += humidity_result['score']
    details['humidity_factor'] = humidity_result
    
    # 4. 能見度/空氣品質因子 (0-15分)
    visibility_result = calculate_visibility_factor(weather_data)
    score += visibility_result['score']
    details['visibility_factor'] = visibility_result
    
    # 5. 進階雲層分析因子 (0-25分)
    if forecast_data and 'forecastDesc' in forecast_data:
        cloud_result = advanced_predictor.analyze_cloud_types(forecast_data['forecastDesc'])
        score += cloud_result['score']
        details['cloud_analysis_factor'] = cloud_result
    else:
        details['cloud_analysis_factor'] = {'score': 0, 'description': '無天氣預報數據'}
    
    # 6. UV指數因子 (0-10分)
    uv_result = calculate_uv_factor(weather_data)
    score += uv_result['score']
    details['uv_factor'] = uv_result
    
    # 7. 機器學習預測
    try:
        ml_result = advanced_predictor.predict_ml(weather_data, forecast_data)
        details['ml_prediction'] = ml_result
        
        # 結合傳統算法和機器學習結果
        traditional_score = score
        ml_score = ml_result['ml_burnsky_score']
        
        # 如果是提前預測，調整權重
        if advance_hours > 0:
            # 提前預測時更依賴機器學習
            final_score = traditional_score * 0.4 + ml_score * 0.6
        else:
            # 即時預測時也以機器學習為主
            final_score = traditional_score * 0.4 + ml_score * 0.6
        
        details['score_breakdown'] = {
            'traditional_score': traditional_score,
            'ml_score': ml_score,
            'final_weighted_score': final_score,
            'prediction_type': prediction_type,
            'advance_hours': advance_hours
        }
        
    except Exception as e:
        final_score = score
        details['ml_prediction'] = {'error': f'機器學習預測失敗: {str(e)}'}
        details['score_breakdown'] = {
            'traditional_score': score,
            'ml_score': 0,
            'final_weighted_score': score,
            'prediction_type': prediction_type,
            'advance_hours': advance_hours
        }
    
    # 確保分數在0-100範圍內
    final_score = max(0, min(100, final_score))
    
    # 8. 燒天程度預測
    intensity_prediction = advanced_predictor.predict_burnsky_intensity(final_score)
    details['intensity_prediction'] = intensity_prediction
    
    # 9. 燒天顏色預測
    color_prediction = advanced_predictor.predict_burnsky_colors(
        weather_data, forecast_data, final_score
    )
    details['color_prediction'] = color_prediction
    
    # 10. 生成進階分析摘要
    details['total_score'] = final_score
    details['analysis_summary'] = generate_analysis_summary_enhanced(details)
    
    return final_score, details, intensity_prediction, color_prediction

def generate_analysis_summary_enhanced(details):
    """生成增強版分析摘要"""
    total_score = details['total_score']
    prediction_type = details['score_breakdown'].get('prediction_type', 'sunset')
    advance_hours = details['score_breakdown'].get('advance_hours', 0)
    
    summary = []
    
    # 預測類型和時間說明
    if advance_hours > 0:
        if prediction_type == 'sunrise':
            summary.append(f"🌅 {advance_hours}小時後日出燒天預測")
        else:
            summary.append(f"🌇 {advance_hours}小時後日落燒天預測")
    else:
        if prediction_type == 'sunrise':
            summary.append("🌅 即時日出燒天分析")
        else:
            summary.append("🌇 即時日落燒天分析")
    
    # 時間因子分析
    if 'time_factor' in details:
        time_data = details['time_factor']
        if time_data['score'] >= 20:
            summary.append(f"⏰ {time_data.get('description', '完美時機')}")
        elif time_data['score'] >= 15:
            summary.append(f"⏰ {time_data.get('description', '良好時段')}")
        else:
            summary.append(f"⏰ {time_data.get('description', '非理想時段')}")
    
    # 燒天程度分析
    if 'intensity_prediction' in details:
        intensity = details['intensity_prediction']
        summary.append(f"🔥 預測程度: {intensity['name']} (等級{intensity['level']})")
        summary.append(f"⏱️ 預估持續: {intensity['duration_estimate']}")
    
    # 顏色預測摘要
    if 'color_prediction' in details:
        colors = details['color_prediction']
        if colors['primary_colors']:
            primary_str = '、'.join(colors['primary_colors'][:2])
            summary.append(f"🎨 主要色彩: {primary_str}")
        summary.append(f"💫 色彩強度: {colors['color_intensity']}")
    
    # 天氣條件分析
    if 'humidity_factor' in details and details['humidity_factor']['score'] >= 15:
        summary.append("✅ 濕度條件理想")
    elif 'humidity_factor' in details and details['humidity_factor']['score'] >= 10:
        summary.append("⚠️ 濕度條件尚可")
    
    if 'temperature_factor' in details and details['temperature_factor']['score'] >= 10:
        summary.append("✅ 溫度條件良好")
    
    # 雲層條件
    if 'cloud_analysis_factor' in details:
        cloud_data = details['cloud_analysis_factor']
        if cloud_data['score'] >= 15:
            summary.append("☁️ 雲層條件有利")
        elif cloud_data['score'] >= 10:
            summary.append("☁️ 雲層條件一般")
        
        if 'favorable_conditions' in cloud_data and cloud_data['favorable_conditions']:
            summary.append(f"🌤️ 有利條件: {', '.join(cloud_data['favorable_conditions'][:2])}")
    
    # AI vs 傳統算法對比
    if 'score_breakdown' in details:
        breakdown = details['score_breakdown']
        traditional = breakdown['traditional_score']
        ml_score = breakdown['ml_score']
        
        if abs(traditional - ml_score) <= 10:
            summary.append("⚖️ 傳統與AI預測一致")
        elif traditional > ml_score:
            summary.append("📊 傳統算法較樂觀")
        else:
            summary.append("🤖 AI模型較樂觀")
    
    # 攝影建議
    if 'intensity_prediction' in details:
        advice = details['intensity_prediction']['photography_advice']
        summary.append(f"📸 拍攝建議: {advice}")
    
    # 總體建議
    if total_score >= 80:
        summary.append("🔥 強烈推薦！絕佳燒天機會")
    elif total_score >= 70:
        summary.append("🌟 高度推薦外出觀賞")
    elif total_score >= 50:
        summary.append("📸 值得嘗試，有不錯機會")
    elif total_score >= 30:
        summary.append("🤔 可以觀察，條件一般")
    else:
        summary.append("📱 建議等待更好時機")
    
    return summary

def calculate_time_factor():
    """簡化版時間因子計算 - 保持向後兼容性"""
    return advanced_predictor.calculate_time_factor_advanced()['score']
