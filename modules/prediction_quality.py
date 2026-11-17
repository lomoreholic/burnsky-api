"""Describe input limitations; never interpret missing readings as favourable weather."""

from .weather_presentation import number


class InsufficientPredictionData(Exception):
    def __init__(self, quality):
        self.quality = quality
        super().__init__(quality['summary'])


def station_value(weather, key):
    block = weather.get(key)
    entries = block.get('data', []) if isinstance(block, dict) else []
    entries = entries if isinstance(entries, list) else []
    return next((number(item.get('value')) for item in entries
                 if isinstance(item, dict) and item.get('place') == '香港天文台'), None)


def highest_rainfall(weather):
    block = weather.get('rainfall')
    entries = block.get('data', []) if isinstance(block, dict) else []
    entries = entries if isinstance(entries, list) else []
    readings = [number(item.get('max', item.get('value'))) for item in entries if isinstance(item, dict)]
    return max((value for value in readings if value is not None and value >= 0), default=None)


def assess_prediction_quality(target, observed, forecast, advance_hours=0):
    missing = []
    for key, label, low, high in [('temperature', '天文台溫度', -50, 60), ('humidity', '天文台濕度', 0, 100)]:
        readings = [station_value(weather, key) for weather in (observed, target)]
        if any(value is None or not low <= value <= high for value in readings):
            missing.append(label)
    description = forecast.get('forecastDesc') if isinstance(forecast, dict) else None
    if not isinstance(description, str) or not description.strip():
        missing.append('天氣預報文字（雲層分析輸入）')
    limitations = ['雲層因子按天氣預報文字推斷，並非雲量或雲高實測。',
                   '空氣品質沒有可用AQHI監測值時不參與計分。']
    if number(target.get('pressure')) is None:
        limitations.append('氣壓讀數缺失，不參與計分。')
    wind = target.get('wind')
    if not isinstance(wind, dict) or number(wind.get('speed')) is None:
        limitations.append('風速因子未取得計分所需的風速讀數，不參與計分；每日預報風級範圍不當作實測風速。')
    if highest_rainfall(target) is None:
        limitations.append('雨量資料缺失；能見度因子不參與計分，沒有視作無雨。')
    else:
        limitations.append('能見度因子以各地區最高雨量作間接參考，並非能見度實測。')
    uv = target.get('uvindex')
    entries = uv.get('data', []) if isinstance(uv, dict) else []
    entries = entries if isinstance(entries, list) else []
    if not entries or not isinstance(entries[0], dict) or number(entries[0].get('value')) is None:
        limitations.append('UV因子缺少可用讀數，不參與計分。')
    if advance_hours > 0:
        limitations.append('未來條件包含模型推算及沿用現有觀測，並非目標時段的完整預報。')
    # Optional sensors and proxy inputs affect confidence, not whether the
    # short-term condition estimate can be shown at all.
    short_term_ready = not missing and 0 <= advance_hours <= 3 and highest_rainfall(target) is not None
    if missing:
        summary = '主要資料不足，暫停評分：' + '、'.join(missing) + '。'
    elif short_term_ready:
        summary = '主要資料齊全，可提供3小時內短期預測；可信度一般。'
    else:
        summary = '可提供初步預測；' + ('超過3小時，可信度較低。' if advance_hours > 3 else '缺少雨量參考，可信度較低。')
    if not missing:
        summary += '缺失因子不補分，低分亦可能受資料覆蓋影響；詳細限制見下方。'
    return {'status': 'insufficient' if missing else 'ready' if short_term_ready else 'limited',
            'confidence': 'unavailable' if missing else 'moderate' if short_term_ready else 'low',
            'score_usable': not missing, 'allow_high_score_notification': False,
            'missing_required': missing, 'limitations': limitations,
            'summary': summary}


def require_prediction_inputs(target, observed, forecast, advance_hours=0):
    quality = assess_prediction_quality(target, observed, forecast, advance_hours)
    if not quality['score_usable']:
        raise InsufficientPredictionData(quality)
    return quality
