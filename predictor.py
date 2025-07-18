import math
from datetime import datetime, time
import pytz
from advanced_predictor import AdvancedBurnskyPredictor
from air_quality_fetcher import AirQualityFetcher

# 初始化進階預測器
advanced_predictor = AdvancedBurnskyPredictor()

# 初始化空氣品質獲取器
air_quality_fetcher = AirQualityFetcher()

def calculate_burnsky_score(weather_data, forecast_data, ninday_data):
    """
    計算燒天指數 (0-100分) - 整合進階功能版本
    
    燒天出現的條件：
    1. 實時日落前後 30 分鐘判斷 (時間因子)
    2. 雲層類型分析 (30%-70%)
    3. 高空雲（卷雲、卷層雲）出現
    4. 空氣清晰（能見度高）
     # 只顯示最多 3 個關鍵因子
    if key_factors:
        summary.append(" | ".join(key_factors[:3]))
    
    # 燒天程度和拍攝建議
    if 'intensity_prediction' in details:
        intensity = details['intensity_prediction']
        summary.append(f"🔥 燒天程度: {intensity['name']} | 📸 拍攝建議: {intensity['photography_advice']}")
    
    # 主要色彩和色彩強度
    if 'color_prediction' in details:
        colors = details['color_prediction']
        color_info = []
        
        if colors.get('primary_colors') and len(colors['primary_colors']) > 0:
            primary_colors = colors['primary_colors'][:2]  # 只顯示前兩個主要色彩
            color_info.append(f"🎨 主要色彩: {' · '.join(primary_colors)}")
        
        if colors.get('color_intensity'):
            color_info.append(f"💫 色彩強度: {colors['color_intensity']}")
        
        if color_info:
            summary.append(" | ".join(color_info))
    
    # 簡潔的操作建議
    if total_score >= 70:
        summary.append("💡 建議：準備相機，前往拍攝地點")
    elif total_score >= 50:
        summary.append("💡 建議：密切關注天空變化")
    elif total_score >= 30:
        summary.append("💡 建議：等待下個時段或明天")
    else:
        summary.append("💡 建議：查看明日天氣預報")
    
    return summary
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
    
    # 1. 實時時間因子 (0-18分) - 降低比重，基於實際日出日落時間
    time_result = advanced_predictor.calculate_time_factor_advanced()
    # 調整時間因子分數 - 將25分調整為18分
    adjusted_time_score = (time_result['score'] / 25) * 18
    score += adjusted_time_score
    time_result['score'] = round(adjusted_time_score)
    details['time_factor'] = time_result
    
    # 2. 溫度因子 (0-18分) - 稍微提高重要性
    temp_result = calculate_temperature_factor(weather_data)
    adjusted_temp_score = (temp_result['score'] / 15) * 18
    score += adjusted_temp_score
    temp_result['score'] = round(adjusted_temp_score)
    details['temperature_factor'] = temp_result
    
    # 3. 濕度因子 (0-22分) - 稍微提高重要性
    humidity_result = calculate_humidity_factor(weather_data)
    adjusted_humidity_score = (humidity_result['score'] / 20) * 22
    score += adjusted_humidity_score
    humidity_result['score'] = round(adjusted_humidity_score)
    details['humidity_factor'] = humidity_result
    
    # 4. 能見度/空氣品質因子 (0-18分) - 稍微提高重要性
    visibility_result = calculate_visibility_factor(weather_data)
    adjusted_visibility_score = (visibility_result['score'] / 15) * 18
    score += adjusted_visibility_score
    visibility_result['score'] = round(adjusted_visibility_score)
    details['visibility_factor'] = visibility_result
    
    # 5. 進階天氣描述和雲層分析因子 (0-30分) - 提高重要性，最關鍵因子
    if forecast_data and 'forecastDesc' in forecast_data:
        cloud_result = advanced_predictor.analyze_cloud_types(forecast_data['forecastDesc'])
        adjusted_cloud_score = (cloud_result['score'] / 25) * 30
        score += adjusted_cloud_score
        cloud_result['score'] = round(adjusted_cloud_score)
        details['cloud_analysis_factor'] = cloud_result
    else:
        details['cloud_analysis_factor'] = {'score': 0, 'description': '無天氣預報數據'}
    
    # 6. UV指數因子 (0-12分) - 稍微提高重要性
    uv_result = calculate_uv_factor(weather_data)
    adjusted_uv_score = (uv_result['score'] / 10) * 12
    score += adjusted_uv_score
    uv_result['score'] = round(adjusted_uv_score)
    details['uv_factor'] = uv_result
    
    # 7. 風速因子 (0-10分) - 新增
    wind_result = calculate_wind_factor(weather_data)
    adjusted_wind_score = (wind_result['score'] / 15) * 10
    score += adjusted_wind_score
    wind_result['score'] = round(adjusted_wind_score)
    details['wind_factor'] = wind_result
    
    # 8. 空氣品質因子 (0-12分) - 新增
    air_quality_result = calculate_air_quality_factor(weather_data)
    adjusted_air_quality_score = (air_quality_result['score'] / 15) * 12
    score += adjusted_air_quality_score
    air_quality_result['score'] = round(adjusted_air_quality_score)
    details['air_quality_factor'] = air_quality_result
    
    # 9. 機器學習預測 (整合所有因子)
    try:
        ml_result = advanced_predictor.predict_ml(weather_data, forecast_data)
        details['ml_prediction'] = ml_result
        
        # 結合傳統算法和機器學習結果
        traditional_score = score
        ml_score = ml_result['ml_burnsky_score']
        
        # 標準化傳統算法分數到100分制 (總分上限140分)
        TRADITIONAL_MAX_SCORE = 140  # 18+18+22+18+30+12+10+12
        traditional_score_normalized = (traditional_score / TRADITIONAL_MAX_SCORE) * 100
        
        # 加權平均 - 使用標準化後的分數確保公平比較 (傳統算法 35%, 機器學習 65%)
        final_score = traditional_score_normalized * 0.35 + ml_score * 0.65
        
        details['score_breakdown'] = {
            'traditional_score': traditional_score,
            'traditional_score_normalized': traditional_score_normalized,
            'ml_score': ml_score,
            'final_weighted_score': final_score,
            'normalization_note': f'傳統算法從{traditional_score:.1f}/140標準化為{traditional_score_normalized:.1f}/100'
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
    """生成簡潔的智能分析摘要"""
    total_score = details['total_score']
    summary = []
    
    # 主要結論 - 根據總分給出核心建議
    if total_score >= 80:
        summary.append("🔥 絕佳燒天機會！強烈建議立即拍攝")
    elif total_score >= 70:
        summary.append("🌅 良好燒天條件，高度推薦外出")
    elif total_score >= 50:
        summary.append("📸 中等機會，可嘗試拍攝")
    elif total_score >= 30:
        summary.append("🤔 條件一般，建議等待更佳時機")
    else:
        summary.append("📱 條件不佳，建議室內等待")
    
    # 關鍵影響因子 - 只突出最重要的 2-3 個
    key_factors = []
    
    # 時間因子 (最重要)
    if 'time_factor' in details:
        time_score = details['time_factor']['score']
        if time_score >= 20:
            key_factors.append("⏰ 黃金時段")
        elif time_score >= 15:
            key_factors.append("⏰ 合適時間")
        elif time_score < 10:
            key_factors.append("⏰ 非最佳時間")
    
    # 雲層條件 (次重要)
    if 'cloud_analysis_factor' in details:
        cloud_score = details['cloud_analysis_factor']['score']
        if cloud_score >= 18:
            key_factors.append("☁️ 理想雲層")
        elif cloud_score >= 12:
            key_factors.append("☁️ 適合雲層")
        elif cloud_score < 8:
            key_factors.append("☁️ 雲層不利")
    
    # AI 預測 (第三重要)
    if 'ml_prediction' in details and 'ml_class' in details['ml_prediction']:
        ml_class = details['ml_prediction']['ml_class']
        if ml_class == 2:
            key_factors.append("🤖 AI高度看好")
        elif ml_class == 0:
            key_factors.append("🤖 AI不看好")
    
    # 只顯示最多 3 個關鍵因子
    if key_factors:
        summary.append(" | ".join(key_factors[:3]))
    
    # 簡潔的操作建議
    if total_score >= 70:
        summary.append("� 建議：準備相機，前往拍攝地點")
    elif total_score >= 50:
        summary.append("� 建議：密切關注天空變化")
    elif total_score >= 30:
        summary.append("💡 建議：等待下個時段或明天")
    else:
        summary.append("� 建議：查看明日天氣預報")
    
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
    
    # 7. 風速因子 (0-15分) - 新增
    wind_result = calculate_wind_factor(weather_data)
    score += wind_result['score']
    details['wind_factor'] = wind_result
    
    # 8. 空氣品質因子 (0-15分) - 新增
    air_quality_result = calculate_air_quality_factor(weather_data)
    score += air_quality_result['score']
    details['air_quality_factor'] = air_quality_result
    
    # 9. 機器學習預測
    try:
        ml_result = advanced_predictor.predict_ml(weather_data, forecast_data)
        details['ml_prediction'] = ml_result
        
        # 結合傳統算法和機器學習結果
        traditional_score = score
        ml_score = ml_result['ml_burnsky_score']
        
        # 標準化傳統算法分數到100分制 (總分上限140分)
        # 分數構成：時間(25) + 溫度(15) + 濕度(20) + 能見度(15) + 雲層(25) + UV(10) + 風速(15) + 空氣品質(15) = 140分
        TRADITIONAL_MAX_SCORE = 140  # 25+15+20+15+25+10+15+15
        traditional_score_normalized = (traditional_score / TRADITIONAL_MAX_SCORE) * 100
        
        # 動態權重調整 - 基於預測時間優化準確率，使用標準化後的分數
        if advance_hours >= 1 and advance_hours <= 2:
            # 提前1-2小時預測時更依賴機器學習 (黃金預測時段)
            final_score = traditional_score_normalized * 0.35 + ml_score * 0.65
            weight_note = "黃金預測時段，AI權重65%"
        elif advance_hours > 0:
            # 其他提前預測時段，機器學習權重60%
            final_score = traditional_score_normalized * 0.4 + ml_score * 0.6
            weight_note = "提前預測時段，AI權重60%"
        else:
            # 即時預測，減少AI權重讓傳統算法有更大發言權
            final_score = traditional_score_normalized * 0.45 + ml_score * 0.55
            weight_note = "即時預測時段，AI權重55%"
        
        details['score_breakdown'] = {
            'traditional_score': traditional_score,
            'traditional_score_normalized': traditional_score_normalized,
            'ml_score': ml_score,
            'final_weighted_score': final_score,
            'prediction_type': prediction_type,
            'advance_hours': advance_hours,
            'weight_explanation': weight_note,
            'normalization_note': f'傳統算法從{traditional_score:.1f}/140標準化為{traditional_score_normalized:.1f}/100'
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
    
    # 8. 新增：雲層厚度與顏色可見度分析
    cloud_visibility_result = advanced_predictor.analyze_cloud_thickness_and_color_visibility(weather_data, forecast_data)
    details['cloud_visibility_analysis'] = cloud_visibility_result
    
    # 根據雲層厚度調整分數
    if cloud_visibility_result['color_visibility_percentage'] < 30:
        # 厚雲天氣，降低整體分數但提供替代價值
        final_score = final_score * 0.8  # 輕微降分
        details['cloud_visibility_analysis']['score_adjustment'] = '厚雲天氣調整：專注明暗變化'
    elif cloud_visibility_result['color_visibility_percentage'] > 80:
        # 極佳顏色條件，輕微加分
        final_score = final_score * 1.1
        details['cloud_visibility_analysis']['score_adjustment'] = '極佳顏色條件加分'
    
    # 確保調整後分數仍在0-100範圍內
    final_score = max(0, min(100, final_score))
    
    # 9. 燒天程度預測
    intensity_prediction = advanced_predictor.predict_burnsky_intensity(final_score)
    details['intensity_prediction'] = intensity_prediction
    
    # 10. 燒天顏色預測
    color_prediction = advanced_predictor.predict_burnsky_colors(
        weather_data, forecast_data, final_score
    )
    details['color_prediction'] = color_prediction
    
    # 生成進階分析摘要
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
    
    # 風速條件評估
    if 'wind_factor' in details:
        wind_data = details['wind_factor']
        if wind_data['score'] >= 10:
            wind_impact = wind_data.get('wind_impact', '未知')
            wind_level = wind_data.get('wind_level', '未知')
            summary.append(f"💨 風速條件{wind_impact}（{wind_level}）")
        elif wind_data['score'] >= 5:
            summary.append("⚠️ 風速條件一般")
        else:
            summary.append("❌ 風速不利燒天")
    
    # 空氣品質條件評估
    if 'air_quality_factor' in details:
        air_data = details['air_quality_factor']
        if air_data['score'] >= 12:
            summary.append(f"✨ 空氣品質{air_data.get('impact', '極佳')}（AQHI {air_data.get('aqhi', 'N/A')}）")
        elif air_data['score'] >= 8:
            summary.append(f"🌫️ 空氣品質{air_data.get('impact', '良好')}（AQHI {air_data.get('aqhi', 'N/A')}）")
        elif air_data['score'] >= 5:
            summary.append(f"⚠️ 空氣污染影響燒天品質（AQHI {air_data.get('aqhi', 'N/A')}）")
        else:
            summary.append(f"❌ 嚴重空氣污染不利燒天（AQHI {air_data.get('aqhi', 'N/A')}）")
    
    return summary

def calculate_wind_factor(weather_data):
    """
    計算風速因子對燒天的影響 (最高15分)
    
    風速影響：
    - 輕微風速 (0-2級): 有利於燒天現象持續，評分較高
    - 適中風速 (3-4級): 適度的風有助於雲層形態變化，評分中等偏高
    - 強風 (5級以上): 會快速吹散雲層，不利於燒天，評分較低
    - 風向也會影響雲層移動和形態
    
    Args:
        weather_data: 包含風速資訊的天氣數據
        
    Returns:
        dict: 包含分數和描述的字典
    """
    if not weather_data or 'wind' not in weather_data:
        return {'score': 0, 'description': '無風速數據'}
    
    wind_info = weather_data['wind']
    
    if not wind_info or not wind_info.get('description'):
        return {'score': 0, 'description': '無風速數據'}
    
    # 獲取風級範圍
    min_beaufort = wind_info.get('speed_beaufort_min', 0)
    max_beaufort = wind_info.get('speed_beaufort_max', 0)
    avg_beaufort = (min_beaufort + max_beaufort) / 2
    
    # 風向資訊
    wind_direction = wind_info.get('direction', '')
    wind_description = wind_info.get('description', '')
    
    score = 0
    description_parts = [f"風速: {wind_description}"]
    
    # 基於平均風級評分
    if avg_beaufort <= 1:  # 0-1級 (無風至軟風)
        score = 15  # 最佳，燒天現象能持續較久
        description_parts.append("(無風/軟風，極佳燒天條件)")
    elif avg_beaufort <= 2:  # 2級 (輕風)
        score = 13  # 優秀，輕微風有助於雲層微調
        description_parts.append("(輕風，優秀燒天條件)")
    elif avg_beaufort <= 3:  # 3級 (微風)
        score = 11  # 良好，適度風速有助於雲層動態
        description_parts.append("(微風，良好燒天條件)")
    elif avg_beaufort <= 4:  # 4級 (和風)
        score = 8   # 中等，適中風速可能加速雲層變化
        description_parts.append("(和風，中等燒天條件)")
    elif avg_beaufort <= 5:  # 5級 (清勁風)
        score = 5   # 較差，風速開始影響雲層穩定性
        description_parts.append("(清勁風，雲層較不穩定)")
    elif avg_beaufort <= 6:  # 6級 (強風)
        score = 3   # 差，強風會快速吹散雲層
        description_parts.append("(強風，雲層易被吹散)")
    else:  # 7級以上 (疾風以上)
        score = 1   # 極差，烈風會完全破壞燒天條件
        description_parts.append("(烈風，燒天條件極差)")
    
    # 風向加成/減分
    if wind_direction:
        description_parts.append(f"風向: {wind_direction}")
        
        # 西南風和西北風在日落時較有利（從陸地吹向海洋）
        # 東南風和東北風在日出時較有利（從海洋吹向陸地）
        if wind_direction in ['SW', 'W', 'NW']:
            # 日落時的有利風向，輕微加分
            if avg_beaufort <= 3:
                score = min(15, score + 1)
                description_parts.append("(有利日落風向)")
        elif wind_direction in ['SE', 'E', 'NE']:
            # 日出時的有利風向，輕微加分  
            if avg_beaufort <= 3:
                score = min(15, score + 1)
                description_parts.append("(有利日出風向)")
    
    # 風速穩定性評估
    wind_range = max_beaufort - min_beaufort
    if wind_range <= 1:
        description_parts.append("風速穩定")
    elif wind_range <= 2:
        description_parts.append("風速較穩定")
        score = max(0, score - 1)  # 輕微減分
    else:
        description_parts.append("風速變化較大")
        score = max(0, score - 2)  # 減分較多
    
    description = " | ".join(description_parts)
    
    return {
        'score': score,
        'description': description,
        'wind_direction': wind_direction,
        'wind_level': f"{min_beaufort}-{max_beaufort}級",
        'wind_impact': '有利' if score >= 10 else '中等' if score >= 6 else '不利'
    }

def calculate_air_quality_factor(weather_data=None):
    """
    計算空氣品質因子對燒天的影響 (最高15分)
    
    空氣品質影響：
    - AQHI 1-3 (低): 空氣清澈透明，極佳燒天條件 (13-15分)
    - AQHI 4-6 (中): 空氣品質一般，良好燒天條件 (10-12分)  
    - AQHI 7-9 (高): 空氣污染影響透明度和色彩 (6-9分)
    - AQHI 10+ (嚴重): 嚴重污染大幅影響燒天品質 (2-5分)
    
    Args:
        weather_data: 天氣數據 (可選，用於估算)
        
    Returns:
        dict: 包含分數和描述的字典
    """
    try:
        # 使用全局的空氣品質獲取器
        air_quality_data = air_quality_fetcher.get_current_air_quality()
        
        if not air_quality_data:
            raise Exception("無法獲取空氣品質數據")
        
        # 提取 AQHI 和 PM2.5 數據
        aqhi = air_quality_data.get('aqhi', 4)
        pm25 = air_quality_data.get('components', {}).get('pm2_5', 25)
        level = air_quality_data.get('level', '中')
        source = air_quality_data.get('source', '未知')
        station_name = air_quality_data.get('station_name', '未知監測站')
        
        # 計算燒天影響分數 (滿分15分)
        if aqhi <= 3:
            score = 15  # 極佳條件
            impact = "極佳"
            description = f"空氣品質極佳 (AQHI: {aqhi})，透明度高，燒天效果極佳"
        elif aqhi <= 6:
            score = 12  # 良好條件
            impact = "良好"
            description = f"空氣品質良好 (AQHI: {aqhi})，對燒天影響輕微"
        elif aqhi <= 9:
            score = 7   # 一般條件
            impact = "一般"
            description = f"空氣品質一般 (AQHI: {aqhi})，可能輕微影響燒天色彩"
        else:
            score = 3   # 不佳條件
            impact = "不佳"
            description = f"空氣品質較差 (AQHI: {aqhi})，會影響燒天透明度和色彩"
        
        # PM2.5 額外調整
        if pm25 <= 15:
            pm25_bonus = 1
        elif pm25 <= 35:
            pm25_bonus = 0
        else:
            pm25_bonus = -2
        
        final_score = max(2, min(15, score + pm25_bonus))
        
        return {
            'score': final_score,
            'description': description,
            'aqhi': aqhi,
            'level': level,
            'pm25': pm25,
            'impact': impact,
            'source': source,
            'station': station_name,
            'details': f"監測站: {station_name} | AQHI: {aqhi} ({level}) | PM2.5: {pm25} μg/m³"
        }
        
    except Exception as e:
        # 如果無法獲取空氣品質數據，返回中性分數
        return {
            'score': 10,
            'description': f'無法獲取空氣品質數據，使用預設值: {str(e)}',
            'aqhi': 4,
            'level': '中',
            'pm25': 25,
            'impact': '未知',
            'source': '預設值',
            'station': '無',
            'details': '使用預設空氣品質數值'
        }
