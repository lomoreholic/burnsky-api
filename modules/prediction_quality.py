"""Describe input limitations; never interpret missing readings as favourable weather."""

from .weather_presentation import number
from .cloud_forecast import valid_cloud_forecast
from .hourly_weather import model_reading


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
    reading = model_reading(weather, 'rainfall')
    if reading is not None:
        return reading['value']
    block = weather.get('rainfall')
    # A rejected forecast copy must not re-enter as an observation.
    if isinstance(block, dict) and block.get('source_kind') == 'hourly_forecast':
        return None
    entries = block.get('data', []) if isinstance(block, dict) else []
    entries = entries if isinstance(entries, list) else []
    readings = [number(item.get('max', item.get('value'))) for item in entries if isinstance(item, dict)]
    return max((value for value in readings if value is not None and value >= 0), default=None)


def weather_value(weather, key):
    reading = model_reading(weather, key)
    if reading is not None:
        return reading['value']
    if key == 'wind_speed':
        wind = weather.get('wind')
        if not isinstance(wind, dict) or wind.get('source_kind') == 'hourly_forecast':
            return None
        speed = number(wind.get('speed'))
        return speed if speed is not None and 0 <= speed <= 300 else None
    return station_value(weather, key)


def assess_prediction_quality(target, observed, forecast, advance_hours=0):
    missing = []
    for key, label, low, high in [('temperature', '天文台溫度', -50, 60), ('humidity', '天文台濕度', 0, 100)]:
        if advance_hours > 0 and model_reading(target, key) is not None:
            continue
        readings = [station_value(weather, key) for weather in (observed, target)]
        if any(value is None or not low <= value <= high for value in readings):
            missing.append(label)
    cloud_available = valid_cloud_forecast(target.get('cloud_forecast'), target.get('forecast_target_at'))
    description = forecast.get('forecastDesc') if isinstance(forecast, dict) else None
    if not cloud_available and (not isinstance(description, str) or not description.strip()):
        missing.append('天氣預報文字（雲層分析輸入）')
    limitations = [('雲量使用MET Norway香港參考點逐小時分層預報；未量度雲厚或真正光線穿透，規則尚待實拍驗證。'
                    if cloud_available else '雲層因子按天氣預報文字推斷，並非雲量或雲高實測。'),
                   '空氣品質沒有可用AQHI監測值時不參與計分。']
    if not cloud_available:
        limitations.append('逐小時分層雲量暫缺、過期或未覆蓋目標時間，已改用天文台文字預報。')
    direction = target.get('sunward_cloud_forecast')
    if cloud_available:
        from .sunward_clouds import sunward_multiplier
        if sunward_multiplier(direction, target['cloud_forecast'].get('valid_at')) is not None:
            limitations.append('方向扣分只參考太陽方向50及100公里低雲覆蓋；未計山勢、雲底高度或完整光路。')
        elif isinstance(direction, dict) and direction.get('status') == 'outside_twilight':
            limitations.append('此評估不在太陽高度±8°晨昏範圍，未套用方向扣分。')
        else:
            limitations.append('太陽方向取樣未齊，保留原本雲層評分；缺失不代表光路暢通。')
    if number(target.get('pressure')) is None:
        limitations.append('氣壓讀數缺失，不參與計分。')
    if weather_value(target, 'wind_speed') is None:
        limitations.append('風速因子未取得計分所需的風速讀數，不參與計分；每日預報風級範圍不當作實測風速。')
    if model_reading(target, 'rainfall') is not None:
        limitations.append('降雨遮擋因子使用涵蓋目標時間的一小時預報累積雨量；並非能見度預報，無雨亦可能有霧或霾。')
    elif highest_rainfall(target) is None:
        limitations.append('雨量資料缺失；能見度因子不參與計分，沒有視作無雨。')
    else:
        limitations.append('降雨遮擋部分以各地區最高雨量作間接參考，雨量本身並非能見度實測。')
    from .visibility_observations import reference_visibility
    visibility = reference_visibility(observed)
    if advance_hours > 0:
        limitations.append('天文台能見度為現有測站觀測，並非目標時段預報；不套用於未來遮擋因子扣分。')
    elif visibility is not None:
        limitations.append('即時遮擋因子另受中環實測能見度上限限制，只減不加；不代表全港能見度，門檻尚待驗證。')
    else:
        limitations.append('中環能見度觀測暫缺或超過30分鐘，未套用實測限制；缺失不代表視野清晰。')
    uv = target.get('uvindex')
    entries = uv.get('data', []) if isinstance(uv, dict) else []
    entries = entries if isinstance(entries, list) else []
    if not entries or not isinstance(entries[0], dict) or number(entries[0].get('value')) is None:
        limitations.append('UV因子缺少可用讀數，不參與計分。')
    if advance_hours > 0:
        if target.get('forecast_estimation') and any(model_reading(target, key) is None for key in ('temperature', 'humidity')):
            limitations.append('後備溫濕度為按觀測、鐘點及可用九天預報作規則推算，尚未校準；缺少每日高低溫不補預設數值，觀測更新時間與推算有效時間分開。')
        used = [label for key, label in [('temperature', '溫度'), ('humidity', '濕度'), ('wind_speed', '風速'), ('rainfall', '雨量')]
                if model_reading(target, key) is not None]
        if used:
            limitations.append('、'.join(used) + '使用MET Norway目標時段模式預報，並非現場觀測；其餘項目仍可能沿用推算或現有觀測。')
        else:
            limitations.append('逐小時氣象預報暫缺或未覆蓋目標時間，仍沿用模型推算及現有觀測；並非目標時段完整預報。')
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
