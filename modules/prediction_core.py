# prediction_core.py - 預測核心邏輯模塊

from datetime import datetime, timedelta
from .cache import get_cached_data, cache
from .database import save_prediction_to_history
from .utils import convert_numpy_types, get_prediction_level
from .photo_analyzer import apply_burnsky_photo_corrections
from .config import warning_analysis_available, warning_analyzer

def predict_burnsky_core(prediction_type, advance_hours):
    """燒天預測核心邏輯"""
    from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast, get_current_wind_data, fetch_warning_data
    from unified_scorer import calculate_burnsky_score_unified
    from forecast_extractor import forecast_extractor

    current_time = datetime.now()

    # 獲取天氣數據
    weather_data = get_cached_data('weather', fetch_weather_data)
    forecast_data = get_cached_data('forecast', fetch_forecast_data)
    ninday_data = get_cached_data('ninday', fetch_ninday_forecast)
    wind_data = get_cached_data('wind', get_current_wind_data)
    warning_data = get_cached_data('warning', fetch_warning_data)

    print(f"🚨 獲取天氣警告數據: {len(warning_data.get('details', [])) if warning_data else 0} 個警告")

    # 將風速數據加入天氣數據中
    weather_data['wind'] = wind_data

    # 🚨 將警告數據加入天氣數據（新增）
    weather_data['warnings'] = warning_data

    # 如果是提前預測，使用未來天氣數據
    if advance_hours > 0:
        future_weather_data = forecast_extractor.extract_future_weather_data(
            weather_data, forecast_data, ninday_data, advance_hours
        )
        # 將風速數據加入未來天氣數據中
        future_weather_data['wind'] = wind_data
        # 🚨 提前預測時無法預知未來警告，使用當前警告作參考
        future_weather_data['warnings'] = warning_data
        print(f"🔮 使用 {advance_hours} 小時後的推算天氣數據進行{prediction_type}預測")
        print(f"⚠️ 提前預測無法預知未來警告狀態，使用當前警告作參考")
    else:
        future_weather_data = weather_data
        print(f"🕐 使用即時天氣數據進行{prediction_type}預測")

    # 使用統一計分系統 (整合所有計分方式)
    unified_result = calculate_burnsky_score_unified(
        future_weather_data, forecast_data, ninday_data, prediction_type, advance_hours
    )

    # 從統一結果中提取分數和詳情
    score = unified_result['final_score']

    # 🚨 計算警告影響並調整最終分數（增強版）
    warning_impact, active_warnings, warning_analysis = get_warning_impact_score(warning_data)

    # 🔮 新增：提前預測警告風險評估
    warning_risk_score = 0
    warning_risk_warnings = []
    if advance_hours > 0:
        warning_risk_score, warning_risk_warnings = assess_future_warning_risk(
            weather_data, forecast_data, ninday_data, advance_hours
        )

    # 最終分數計算：傳統警告影響 + 未來風險評估，但限制在合理範圍內
    total_warning_impact = min(warning_impact + warning_risk_score, 10.0)  # 限制最高 10 分

    if total_warning_impact > 0:
        adjusted_score = max(0, score - total_warning_impact)
        print(f"🚨 警告影響詳情: -{warning_impact:.1f}分即時警告 + {warning_risk_score:.1f}分風險評估 = -{total_warning_impact:.1f}分總影響")
        print(f"🚨 調整後分數: {adjusted_score:.1f} (原分數: {score:.1f})")
        score = adjusted_score

    # 🌅 應用基於實際照片案例的校正
    photo_correction = apply_burnsky_photo_corrections(score, future_weather_data, prediction_type)

    if photo_correction != 0:
        corrected_score = score + photo_correction
        print(f"📸 照片案例學習校正: {score:.1f} → {corrected_score:.1f}")
        score = corrected_score

    # 🆕 記錄預測和警告數據到歷史分析系統
    if warning_analysis_available and warning_analyzer:
        try:
            # 記錄預測數據
            prediction_record = {
                "prediction_type": prediction_type,
                "advance_hours": advance_hours,
                "original_score": unified_result['final_score'],
                "warning_impact": warning_impact,
                "warning_risk_impact": warning_risk_score,
                "final_score": score,
                "warnings_active": active_warnings
            }
            warning_analyzer.record_prediction(prediction_record)

            # 記錄當前警告
            if active_warnings:
                for warning in active_warnings:
                    warning_record = {
                        "warning_text": warning,
                        "source": "HKO_API",
                        "prediction_context": prediction_record
                    }
                    warning_analyzer.record_warning(warning_record)

        except Exception as e:
            print(f"⚠️ 警告數據記錄失敗: {e}")

    # 復用統一計分器中的雲層厚度分析結果，避免重複計算
    cloud_thickness_analysis = unified_result.get('cloud_thickness_analysis', {})

    # 構建前端兼容的分析詳情格式
    factor_scores = unified_result.get('factor_scores', {})

    # 構建詳細的因子信息，包含前端期望的格式
    def build_factor_info(factor_name, score, max_score=None):
        """構建因子詳情"""
        if max_score is None:
            max_score = {'time': 25, 'temperature': 15, 'humidity': 20, 'visibility': 15,
                        'pressure': 10, 'cloud': 25, 'uv': 10, 'wind': 15, 'air_quality': 15}.get(factor_name, 100)

        factor_data = {
            'score': round(score, 1),
            'max_score': max_score,
            'description': f'{factor_name.title()}因子評分: {round(score, 1)}/{max_score}分'
        }

        # 添加特定因子的額外信息
        if factor_name == 'time':
            # 使用香港時間
            from datetime import datetime, timezone, timedelta
            hk_tz = timezone(timedelta(hours=8))
            hk_now = datetime.now(hk_tz)
            factor_data.update({
                'current_time': hk_now.strftime('%H:%M'),
                'target_time': '18:30' if prediction_type == 'sunset' else '06:30',
                'target_type': prediction_type,
                'advance_hours': advance_hours
            })
        elif factor_name == 'temperature' and 'temperature' in future_weather_data:
            factor_data['current_temp'] = future_weather_data['temperature']
        elif factor_name == 'humidity' and 'humidity' in future_weather_data:
            factor_data['current_humidity'] = future_weather_data['humidity']
        elif factor_name == 'wind' and 'wind' in future_weather_data:
            wind_data = future_weather_data['wind']
            if isinstance(wind_data, dict) and 'speed' in wind_data:
                factor_data['wind_speed'] = wind_data['speed']

        return factor_data

    analysis_details = {
        "confidence": unified_result['analysis'].get('confidence', 'medium'),
        "recommendation": unified_result['analysis'].get('recommendation', ''),
        "score_breakdown": {
            "final_score": score,  # 使用警告調整後的分數
            "final_weighted_score": score,
            "ml_score": unified_result['ml_score'],
            "traditional_normalized": unified_result['traditional_normalized'],
            "traditional_raw": unified_result['traditional_score'],
            "traditional_score": unified_result['traditional_score'],
            "weighted_score": unified_result['weighted_score'],
            "warning_impact": warning_impact,  # 🚨 即時警告影響
            "warning_risk_impact": warning_risk_score,  # 🔮 新增：未來警告風險影響
            "total_warning_impact": total_warning_impact,  # 🔮 新增：總警告影響
            "weight_explanation": f"智能權重分配: AI模型 {unified_result['weights_used'].get('ml', 0.5)*100:.0f}%, 傳統算法 {unified_result['weights_used'].get('traditional', 0.5)*100:.0f}%"
        },
        "top_factors": unified_result['analysis'].get('top_factors', []),
        # 添加前端期望的因子數據 - 將字串摘要轉換為陣列格式
        "analysis_summary": [part.strip() for part in unified_result['analysis'].get('summary', '基於統一計分系統的綜合分析').split('|')],
        "intensity_prediction": unified_result['intensity_prediction'],
        "cloud_visibility_analysis": cloud_thickness_analysis,
        # 🚨 增強版警告相關信息
        "weather_warnings": {
            "active_warnings": active_warnings,
            "warning_count": len(active_warnings),
            "warning_impact_score": warning_impact,
            "warning_risk_score": warning_risk_score,  # 🔮 新增：風險評估分數
            "warning_risk_warnings": warning_risk_warnings,  # 🔮 新增：風險警告列表
            "total_warning_impact": total_warning_impact,  # 🔮 新增：總警告影響
            "has_severe_warnings": warning_impact >= 25,
            "has_future_risks": warning_risk_score > 0,  # 🔮 新增：是否有未來風險
            "detailed_analysis": warning_analysis  # 🆕 新增：詳細警告分析
        },
        # 構建各個因子的詳細信息
        "time_factor": build_factor_info('time', factor_scores.get('time', 0), 25),
        "temperature_factor": build_factor_info('temperature', factor_scores.get('temperature', 0), 15),
        "humidity_factor": build_factor_info('humidity', factor_scores.get('humidity', 0), 20),
        "visibility_factor": build_factor_info('visibility', factor_scores.get('visibility', 0), 15),
        "pressure_factor": build_factor_info('pressure', factor_scores.get('pressure', 0), 10),
        "cloud_analysis_factor": build_factor_info('cloud', factor_scores.get('cloud', 0), 25),
        "uv_factor": build_factor_info('uv', factor_scores.get('uv', 0), 10),
        "wind_factor": build_factor_info('wind', factor_scores.get('wind', 0), 15),
        "air_quality_factor": build_factor_info('air_quality', factor_scores.get('air_quality', 0), 15),
        # 添加機器學習特徵分析
        "ml_feature_analysis": unified_result.get('ml_feature_analysis', {}),
    }

    result = {
        "burnsky_score": score,
        "probability": f"{round(min(score, 100))}%",
        "prediction_level": get_prediction_level(score),
        "prediction_type": prediction_type,
        "advance_hours": advance_hours,
        "unified_analysis": unified_result,  # 完整的統一分析結果
        "analysis_details": analysis_details,  # 前端兼容格式
        "intensity_prediction": unified_result['intensity_prediction'],
        "color_prediction": unified_result['color_prediction'],
        "cloud_thickness_analysis": cloud_thickness_analysis,
        "weather_data": future_weather_data,
        "original_weather_data": weather_data if advance_hours > 0 else None,
        "forecast_data": forecast_data,
        # 🚨 新增警告數據到回應中
        "warning_data": warning_data,
        "warning_analysis": {
            "active_warnings": active_warnings,
            "warning_impact": warning_impact,
            "warning_risk_score": warning_risk_score,  # 🔮 新增：風險評估分數
            "warning_risk_warnings": warning_risk_warnings,  # 🔮 新增：風險警告列表
            "total_warning_impact": total_warning_impact,  # 🔮 新增：總警告影響
            "warning_adjusted": total_warning_impact > 0  # 🔮 更新：使用總影響判斷
        },
        "scoring_method": "unified_v1.2_with_advance_warning_risk"  # � 更新版本號標示風險評估功能
    }

    result = convert_numpy_types(result)

    # 🚀 快取完整預測結果
    prediction_cache_key = f"full_prediction_{prediction_type}_{advance_hours}"
    cache[prediction_cache_key] = (current_time, result)
    print(f"✅ 預測結果已快取: {prediction_cache_key}")

    return result  # 返回結果字典而不是 jsonify

def get_warning_impact_score(warning_data):
    """計算警告影響分數"""
    if not warning_data or not warning_data.get('details'):
        return 0, [], {}

    active_warnings = []
    total_impact = 0
    analysis = {
        'warning_types': [],
        'impact_breakdown': {},
        'severity_levels': []
    }

    for warning in warning_data['details']:
        warning_text = warning.get('contents', [''])[0] if warning.get('contents') else ''
        if not warning_text:
            continue

        active_warnings.append(warning_text)

        # 計算警告影響（簡化版）
        impact = 0
        if '紅色' in warning_text or '黑色' in warning_text:
            impact = 25  # 嚴重警告
        elif '黃色' in warning_text:
            impact = 15  # 中等警告
        elif '藍色' in warning_text:
            impact = 5   # 輕微警告
        elif any(keyword in warning_text.lower() for keyword in ['暴雨', '雷暴', '大風', '颱風']):
            impact = 20  # 天氣事件警告

        total_impact += impact
        analysis['impact_breakdown'][warning_text] = impact

    return total_impact, active_warnings, analysis

def assess_future_warning_risk(weather_data, forecast_data, ninday_data, advance_hours):
    """評估未來警告風險"""
    risk_score = 0
    risk_warnings = []

    try:
        # 基於當前天氣條件和預報評估未來風險
        current_temp = weather_data.get('temperature', 25)
        current_humidity = weather_data.get('humidity', 70)

        # 季節性風險評估
        from datetime import datetime
        current_month = datetime.now().month

        # 冬季霧霾風險
        if current_month in [12, 1, 2]:
            if current_humidity > 80:
                risk_score += 3
                risk_warnings.append("冬季高濕度 - 霧霾風險較高")

        # 時間不確定性風險（越遠的預測風險越高）
        time_uncertainty = min(advance_hours * 0.5, 6.0)  # 每小時增加0.5分風險
        risk_score += time_uncertainty

        # 天氣條件風險
        if current_humidity > 85:
            risk_score += 2
            risk_warnings.append("高濕度環境 - 可能出現能見度問題")

        # 風速風險（靜風容易積累污染物）
        wind_data = weather_data.get('wind', {})
        if isinstance(wind_data, dict):
            wind_speed = wind_data.get('speed', 0)
            if wind_speed < 5:
                risk_score += 1
                risk_warnings.append("低風速 - 大氣污染物容易積累")

        # 能見度風險
        visibility = weather_data.get('visibility', 10)
        if visibility < 8:
            risk_score += 2
            risk_warnings.append("能見度不佳 - 可能影響拍攝效果")

    except Exception as e:
        print(f"⚠️ 未來警告風險評估失敗: {e}")

    return risk_score, risk_warnings
