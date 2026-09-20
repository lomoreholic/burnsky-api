"""Build the stable prediction response consumed by API clients and the frontend."""

from datetime import datetime, timedelta, timezone


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
        cloud_analysis = unified_result.get('cloud_thickness_analysis', {})
        total_warning_impact = min(warning_impact + warning_risk_score, 10.0)
        details = self._analysis_details(
            score, prediction_type, advance_hours, unified_result, intensity_prediction,
            target_weather, cloud_analysis, warning_impact, warning_risk_score,
            warning_risk_warnings, active_warnings, warning_analysis, total_warning_impact
        )
        sun_times = self._get_sun_times()
        result = {
            'burnsky_score': score,
            'probability': f'{round(min(score, 100))}%',
            'prediction_level': self._get_prediction_level(score),
            'prediction_type': prediction_type,
            'advance_hours': advance_hours,
            'unified_analysis': unified_result,
            'analysis_details': details,
            'intensity_prediction': intensity_prediction,
            'color_prediction': color_prediction,
            'cloud_thickness_analysis': cloud_analysis,
            'weather_data': target_weather,
            'original_weather_data': observed_weather if advance_hours > 0 else None,
            'forecast_data': forecast_data,
            'sun_times': {
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
            'scoring_method': 'unified_v1.2_with_advance_warning_risk'
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
                'weight_explanation': f"智能權重分配: AI模型 {unified_result['weights_used'].get('ml', 0.5) * 100:.0f}%, 傳統算法 {unified_result['weights_used'].get('traditional', 0.5) * 100:.0f}%"
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
            'time_factor': self._factor('time', factor_scores.get('time', 0), 18, prediction_type, advance_hours, target_weather),
            'temperature_factor': self._factor('temperature', factor_scores.get('temperature', 0), 15, prediction_type, advance_hours, target_weather),
            'humidity_factor': self._factor('humidity', factor_scores.get('humidity', 0), 20, prediction_type, advance_hours, target_weather),
            'visibility_factor': self._factor('visibility', factor_scores.get('visibility', 0), 20, prediction_type, advance_hours, target_weather),
            'pressure_factor': self._factor('pressure', factor_scores.get('pressure', 0), 10, prediction_type, advance_hours, target_weather),
            'cloud_analysis_factor': self._factor('cloud', factor_scores.get('cloud', 0), 35, prediction_type, advance_hours, target_weather),
            'uv_factor': self._factor('uv', factor_scores.get('uv', 0), 2, prediction_type, advance_hours, target_weather),
            'wind_factor': self._factor('wind', factor_scores.get('wind', 0), 15, prediction_type, advance_hours, target_weather),
            'air_quality_factor': self._factor('air_quality', factor_scores.get('air_quality', 0), 15, prediction_type, advance_hours, target_weather),
            'ml_feature_analysis': unified_result.get('ml_feature_analysis', {})
        }

    def _factor(self, name, score, max_score, prediction_type, advance_hours, weather):
        factor = {'score': round(score, 1), 'max_score': max_score, 'description': f'{name.title()}因子評分: {round(score, 1)}/{max_score}分'}
        if name == 'time':
            hk_now = self._now(timezone(timedelta(hours=8)))
            factor.update({'current_time': hk_now.strftime('%H:%M'), 'target_time': '18:30' if prediction_type == 'sunset' else '06:30',
                           'target_type': prediction_type, 'advance_hours': advance_hours})
        elif name == 'temperature' and 'temperature' in weather:
            factor['current_temp'] = weather['temperature']
        elif name == 'humidity' and 'humidity' in weather:
            factor['current_humidity'] = weather['humidity']
        elif name == 'wind' and isinstance(weather.get('wind'), dict) and 'speed' in weather['wind']:
            factor['wind_speed'] = weather['wind']['speed']
        return factor