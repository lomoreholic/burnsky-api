"""Build the stable prediction response consumed by API clients and the frontend."""

from datetime import datetime

from .prediction_presentation import HK_TIMEZONE, SCORE_DEFINITION, build_prediction_timing
from .weather_presentation import build_weather_presentation


def missing_factor_sensitivity(unified_result, score, warning_penalty):
    """Arithmetic scenarios only; hold known factors and other adjustments fixed."""
    from .weather_presentation import number
    coverage = unified_result.get('input_coverage', {})
    missing_max = number(coverage.get('missing_max_score'))
    total_max = number(coverage.get('total_max_score'))
    base = number(unified_result.get('final_score'))
    normalized = number(unified_result.get('traditional_normalized'))
    adjustment = number(unified_result.get('adjustments', {}).get('numeric_total'))
    weights = unified_result.get('weights_used', {})
    # Defined only for the current unblended fixed-denominator scorer.
    if (None in (missing_max, total_max, base, normalized, adjustment) or total_max <= 0
            or not 0 <= missing_max <= total_max
            or weights.get('traditional') != 1 or weights.get('ml') != 0):
        return None
    # Apply seasonal clipping before warning clipping, as in the actual scoring path.
    upper = min(100, max(0, normalized + missing_max / total_max * 100 + adjustment))
    # A range cannot explain an unexpected adjustment in a future scoring path.
    from math import isclose
    if not isclose(score, max(0, base - warning_penalty), abs_tol=1e-9):
        return None
    return {
        'kind': 'missing_factor_scenarios',
        'lower': score,
        'upper': max(score, max(0, upper - warning_penalty)),
        'weighted_coverage_percent': coverage.get('weighted_percent'),
        'missing_factors': coverage.get('missing_factors', []),
        'definition': '缺失因子由零至滿分的算術情境；其餘輸入、季節調整及警告扣分保持不變。不是機率、可信區間或預測誤差範圍，亦不代表預期會升至上限。',
    }


class PredictionResponseBuilder:
    """Assemble presentation fields separately from prediction calculation."""

    def __init__(self, get_prediction_level, get_sun_times, convert_types, now=datetime.now):
        self._get_prediction_level = get_prediction_level
        self._get_sun_times = get_sun_times
        self._convert_types = convert_types
        self._now = now

    def build(self, *, score, prediction_type, advance_hours, unified_result, intensity_prediction,
              color_prediction, target_weather, observed_weather, forecast_data, warning_data,
              warning_impact, warning_risk_score, warning_risk_warnings, active_warnings,
              warning_analysis):
        from .cloud_forecast import utc_time
        timing, sun_times = build_prediction_timing(
            self._now(HK_TIMEZONE), prediction_type, advance_hours, self._get_sun_times,
            evaluated_at=utc_time(target_weather.get('forecast_target_at'))
        )
        cloud_analysis = unified_result.get('cloud_thickness_analysis', {})
        total_warning_impact = min(warning_impact + warning_risk_score, 10.0)
        sensitivity = missing_factor_sensitivity(unified_result, score, total_warning_impact)
        details = self._analysis_details(
            score, prediction_type, advance_hours, unified_result, intensity_prediction,
            target_weather, cloud_analysis, warning_impact, warning_risk_score,
            warning_risk_warnings, active_warnings, warning_analysis, total_warning_impact
        )
        details['time_factor'].update(unified_result.get('time_factor', {}))
        details['time_factor'].update({
            'current_time': timing['generated_at'][11:16],
            'evaluated_at': timing['evaluated_at'],
            'target_time': sun_times[timing['event_type']],
            'target_date': timing['evaluated_at'][:10],
        })
        details['score_breakdown']['score_sensitivity'] = sensitivity
        result = {
            'burnsky_score': score,
            'score_sensitivity': sensitivity,
            'data_quality': unified_result.get('data_quality'),
            'score_type': 'condition_index',
            'score_definition': SCORE_DEFINITION,
            # Retained as null for existing API clients; this is not calibrated probability.
            'probability': None,
            'prediction_level': self._get_prediction_level(score),
            'prediction_type': prediction_type,
            'advance_hours': advance_hours,
            'prediction_timing': timing,
            'weather_updated_at': observed_weather.get('updateTime'),
            'unified_analysis': unified_result,
            'analysis_details': details,
            'intensity_prediction': intensity_prediction,
            'color_prediction': color_prediction,
            'cloud_thickness_analysis': cloud_analysis,
            'weather_data': target_weather,
            'weather_presentation': build_weather_presentation(target_weather, observed_weather, advance_hours, timing),
            'original_weather_data': observed_weather if advance_hours > 0 else None,
            'forecast_data': forecast_data,
            'sun_times': {
                'date': timing['evaluated_at'][:10],
                'sunrise': sun_times['sunrise'],
                'sunset': sun_times['sunset'],
                'method': sun_times.get('method', 'calculated')
            },
            'warning_data': warning_data,
            'warning_analysis': {
                'active_warnings': active_warnings,
                'warning_impact': warning_impact,
                'warning_risk_score': warning_risk_score,
                'warning_risk_warnings': warning_risk_warnings,
                'total_warning_impact': total_warning_impact,
                'warning_adjusted': total_warning_impact > 0
            },
            'scoring_method': 'unified_v1.12_cloud_time_validation'
        }
        return self._convert_types(result)

    def _analysis_details(self, score, prediction_type, advance_hours, unified_result, intensity_prediction,
                          target_weather, cloud_analysis, warning_impact, warning_risk_score,
                          warning_risk_warnings, active_warnings, warning_analysis, total_warning_impact):
        factor_scores = unified_result.get('factor_scores', {})
        analysis = unified_result['analysis']
        return {
            'confidence': analysis.get('confidence', 'medium'),
            'recommendation': analysis.get('recommendation', ''),
            'score_breakdown': {
                'final_score': score,
                'final_weighted_score': score,
                'ml_score': unified_result['ml_score'],
                'traditional_normalized': unified_result['traditional_normalized'],
                'traditional_raw': unified_result['traditional_score'],
                'traditional_score': unified_result['traditional_score'],
                'weighted_score': unified_result['weighted_score'],
                'warning_impact': warning_impact,
                'warning_risk_impact': warning_risk_score,
                'total_warning_impact': total_warning_impact,
                'photo_correction': 0,
                'photo_correction_status': 'disabled_unvalidated',
                'input_coverage': unified_result.get('input_coverage', {}),
                'ml_unavailable_reason': unified_result.get('ml_unavailable_reason'),
                'weight_explanation': f"實際權重: AI模型 {unified_result['weights_used'].get('ml', 0.5) * 100:.0f}%, 傳統算法 {unified_result['weights_used'].get('traditional', 0.5) * 100:.0f}%"
            },
            'top_factors': analysis.get('top_factors', []),
            'analysis_summary': [part.strip() for part in analysis.get('summary', '基於統一計分系統的綜合分析').split('|')],
            'intensity_prediction': intensity_prediction,
            'cloud_visibility_analysis': cloud_analysis,
            'weather_warnings': {
                'active_warnings': active_warnings,
                'warning_count': len(active_warnings),
                'warning_impact_score': warning_impact,
                'warning_risk_score': warning_risk_score,
                'warning_risk_warnings': warning_risk_warnings,
                'total_warning_impact': total_warning_impact,
                'has_severe_warnings': warning_impact >= 25,
                'has_future_risks': warning_risk_score > 0,
                'detailed_analysis': warning_analysis
            },
            'time_factor': self._factor('time', factor_scores.get('time'), 18, prediction_type, advance_hours, target_weather),
            'temperature_factor': self._factor('temperature', factor_scores.get('temperature'), 15, prediction_type, advance_hours, target_weather),
            'humidity_factor': self._factor('humidity', factor_scores.get('humidity'), 20, prediction_type, advance_hours, target_weather),
            'visibility_factor': self._factor('visibility', factor_scores.get('visibility'), 20, prediction_type, advance_hours, target_weather),
            'pressure_factor': self._factor('pressure', factor_scores.get('pressure'), 10, prediction_type, advance_hours, target_weather),
            'cloud_analysis_factor': self._factor('cloud', factor_scores.get('cloud'), 35, prediction_type, advance_hours, target_weather),
            'uv_factor': self._factor('uv', factor_scores.get('uv'), 2, prediction_type, advance_hours, target_weather),
            'wind_factor': self._factor('wind', factor_scores.get('wind'), 15, prediction_type, advance_hours, target_weather),
            'air_quality_factor': self._factor('air_quality', factor_scores.get('air_quality'), 15, prediction_type, advance_hours, target_weather),
            'ml_feature_analysis': unified_result.get('ml_feature_analysis', {})
        }

    def _factor(self, name, score, max_score, prediction_type, advance_hours, weather):
        factor = {'score': round(score, 1) if score is not None else None, 'max_score': max_score,
                  'available': score is not None,
                  'description': (f'{name.title()}因子評分: {round(score, 1)}/{max_score}分'
                                  if score is not None else '資料不足或未能識別，不參與計分；沒有補預設分。')}
        if name == 'time':
            factor.update({'target_type': prediction_type, 'advance_hours': advance_hours})
        elif name == 'cloud':
            from .cloud_forecast import valid_cloud_forecast
            cloud = weather.get('cloud_forecast')
            if valid_cloud_forecast(cloud, weather.get('forecast_target_at')):
                factor.update({'source_kind': 'hourly_forecast', 'cloud_forecast': cloud,
                               'description': '使用目標時段低、中、高層雲量預報；中高雲提供染色條件，低雲遮擋會扣分。此規則未經實拍校準。'})
                from .cloud_forecast import score_cloud_layers
                from .sunward_clouds import sunward_multiplier
                direction = weather.get('sunward_cloud_forecast')
                multiplier = sunward_multiplier(direction, cloud.get('valid_at'))
                factor.update({'sunward_cloud_forecast': direction,
                               'base_cloud_score': score_cloud_layers(cloud),
                               'sunward_multiplier': multiplier, 'sunward_adjustment_applied': multiplier is not None})
                factor['description'] += ('已參考太陽方向50及100公里低雲覆蓋作風險扣分，並非透光率實測。' if multiplier is not None
                                          else '此評估未套用方向扣分，沒有將缺失取樣當作晴空。')
            else:
                factor.update({'source_kind': 'text_forecast',
                               'description': '逐小時分層雲量未能使用，改以天文台文字預報評分。' if score is not None
                                              else '缺少可識別雲量資料，不補預設分。'})
        elif name == 'temperature' and 'temperature' in weather:
            factor['current_temp'] = weather['temperature']
        elif name == 'humidity' and 'humidity' in weather:
            factor['current_humidity'] = weather['humidity']
        elif name == 'wind':
            from .prediction_quality import weather_value
            factor['wind_speed'] = weather_value(weather, 'wind_speed')
        elif name == 'air_quality':
            air = weather.get('air_quality_reference' if advance_hours > 0 else 'air_quality') or {}
            factor.update(source_kind='observation_reference' if advance_hours > 0 and air else ('observed' if air else 'unavailable'),
                          source=air.get('source'), source_url=air.get('source_url'), station=air.get('station'),
                          observed_at=air.get('observed_at'), aqhi=air.get('aqhi'),
                          pm25=air.get('components', {}).get('pm25'))
            if air:
                factor['description'] = (f"環保署{air.get('station', '')} AQHI {air.get('aqhi_display', air.get('aqhi'))}；"
                                         f"監測時間 {air.get('observed_at')}。健康風險指數不等於天空透明度。"
                                         + ('只作最新實況參考，並非目標時段預報，不參與此時段計分。' if advance_hours > 0
                                            else '按現有AQHI規則評分，尚未經實拍校準。'))
        elif name == 'pressure' and advance_hours == 0:
            reading = weather.get('pressure_observation') or {}
            if reading and score is not None:
                factor.update(source_kind='observed', source=reading.get('source'), source_url=reading.get('source_url'),
                              station=reading.get('station'), observed_at=reading.get('observed_at'), pressure=reading.get('value'))
                factor['description'] = f"天文台測站海平面氣壓 {reading['value']} hPa；監測時間 {reading['observed_at']}。規則尚未經實拍校準。"
        if name in ('temperature', 'humidity', 'wind', 'visibility', 'pressure'):
            from .hourly_weather import model_reading
            key = {'wind': 'wind_speed', 'visibility': 'rainfall'}.get(name, name)
            reading = model_reading(weather, key)
            if reading is not None:
                model = weather['hourly_weather_forecast']
                factor.update(source_kind='hourly_forecast', source='MET Norway',
                              updated_at=model.get('updated_at'), valid_at=model.get('valid_at'), forecast_reading=reading)
                factor['description'] = ('使用涵蓋目標時間的一小時預報雨量作降雨遮擋參考；無雨不代表能見度良好。' if name == 'visibility'
                                         else '使用目標時段區域模式預報計分，並非天文台站實測；計分規則尚未校準。')
                if name == 'pressure':
                    factor['description'] = f"MET Norway目標時段海平面氣壓預報 {reading['value']} hPa；並非現場觀測，評分門檻尚未經實拍校準。"
            elif name in ('temperature', 'humidity') and score is not None and advance_hours > 0 and weather.get('forecast_estimation'):
                factor.update(source_kind='estimated', source='BurnSky 條件推算',
                              valid_at=weather.get('forecast_target_at'),
                              updated_at=weather['forecast_estimation'].get('observation_updated_at'),
                              description='逐小時資料未能使用，按觀測、鐘點及可用九天預報作後備推算；規則尚未校準，並非目標時段實測。')
            elif name == 'visibility':
                factor.update(source_kind='observed_proxy' if score is not None else 'unavailable',
                              description='按各地區最高觀測雨量作降雨遮擋參考，並非能見度實測或目標時段預報。' if score is not None else '雨量資料缺失，不參與計分。')
            if name == 'visibility':
                from .visibility_observations import reference_visibility, visibility_score_cap
                visibility = reference_visibility(weather) if advance_hours == 0 else None
                applied = visibility is not None and score is not None
                factor.update(visibility_observation=visibility,
                              visibility_cap=visibility_score_cap(visibility['value']) if applied else None,
                              visibility_cap_considered=applied)
                if applied:
                    factor['description'] = '各地區最高雨量作遮擋參考，並以中環十分鐘平均能見度限制因子上限，只減不加。只代表此測站，門檻未經校準。'
                elif advance_hours > 0:
                    factor['description'] += '現有能見度觀測不當作未來預報，未用作此因子扣分。'
        return factor
