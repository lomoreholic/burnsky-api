"""Describe the actual origin of display values without filling missing readings."""

from math import isfinite


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) else None


def build_weather_presentation(target, observed, advance_hours, timing):
    cards = []
    future = advance_hours > 0
    observed_at = observed.get('updateTime')
    from .hourly_weather import model_reading
    model = target.get('hourly_weather_forecast') or {}

    def card(key, label, value, unit='', *, kind='observed', source='香港天文台公開資料',
             station=None, note='', updated_at=observed_at, valid_at=None):
        if value is None:
            kind, source, note = 'unavailable', '', '未取得可用數據。'
        cards.append(dict(key=key, label=label, value=value, unit=unit, source_kind=kind,
                          source=source, station=station, note=note,
                          updated_at=updated_at, valid_at=valid_at))

    def model_card(key, field, label):
        reading = model_reading(target, field) if future else None
        if reading is None:
            return False
        card(key, label, reading['value'], reading['unit'], kind='hourly_forecast',
             source='MET Norway', station='香港參考點 22.30°N, 114.17°E',
             updated_at=model.get('updated_at'), valid_at=model.get('valid_at'),
             note=('涵蓋目標時間的完整一小時預報累積量，沒有按分鐘攤分；並非能見度預報。' if field == 'rainfall'
                   else '區域數值模式預報，並非天文台站實測。' +
                        ('由相鄰整點線性插值。' if reading['method'] == 'linear_interpolation' else '') +
                        ('風速由m/s換算成km/h。' if field == 'wind_speed' else '')))
        if field == 'rainfall':
            cards[-1].update(period_start=reading['period_start'], period_end=reading['period_end'])
        return True

    for key, label, unit in [('temperature', '溫度', '°C'), ('humidity', '相對濕度', '%')]:
        if model_card(key, key, label):
            continue
        block = target.get(key)
        entries = block.get('data', []) if isinstance(block, dict) else []
        reading = next((item for item in entries if isinstance(item, dict) and item.get('place') == '香港天文台'), {})
        card(key, label, number(reading.get('value')), unit, station=reading.get('place'),
             kind='estimated' if future else 'observed',
             source='BurnSky 條件推算' if future else '香港天文台公開資料',
             valid_at=timing['evaluated_at'] if future else None,
             note='逐小時資料未能使用；按觀測及可用預報推算，並非天文台逐小時預報。' if future else '')

    if not model_card('pressure', 'pressure', '海平面氣壓'):
        pressure = observed.get('pressure_observation') or {}
        card('pressure', '現時海平面氣壓', number(pressure.get('value')), 'hPa',
             station=pressure.get('station'), updated_at=pressure.get('observed_at'),
             note='現時觀測作參考，並非目標時段預報，未用作未來計分。' if future else '天文台測站觀測。')
    air = observed.get('air_quality') or {}
    card('aqhi', '現時空氣質素健康指數', air.get('aqhi_display', number(air.get('aqhi'))),
         source='環境保護署', station=air.get('station'), updated_at=air.get('observed_at'),
         note='健康風險指數，並非天空透明度。' + ('現時監測只作參考，不參與未來計分。' if future else ''))
    card('pm25', '現時PM2.5', number(air.get('components', {}).get('pm25')), 'µg/m³',
         source='環境保護署', station=air.get('station'), updated_at=air.get('observed_at'),
         note='一般監測站污染物實測，不額外加減分。' + ('並非目標時段預報。' if future else ''))

    # The forecast extractor leaves nested UV readings unchanged; display the
    # original observation rather than claiming that it is an hourly forecast.
    uv = observed.get('uvindex')
    entries = uv.get('data', []) if isinstance(uv, dict) else []
    reading = next((item for item in entries if isinstance(item, dict) and number(item.get('value')) is not None), {})
    value = number(reading.get('value')) if isinstance(uv, dict) else number(uv)
    card('uvindex', 'UV指數', value, station=reading.get('place'),
         note='沿用現有UV觀測，並非目標時段預報。' if future else '')

    wind = target.get('wind') or {}
    description = wind.get('description') if isinstance(wind, dict) else None
    if not model_card('wind', 'wind_speed', '風速預報'):
        card('wind', '風力預報', description or None, kind='forecast', source='香港天文台九天天氣預報',
             updated_at=wind.get('source_updated_at') if isinstance(wind, dict) else None,
             valid_at=wind.get('forecast_date') if isinstance(wind, dict) else None,
             note='逐小時風速暫缺，沿用此日每日預報文字，並非目標時段風速。' if future else '每日預報文字，並非風站實測。')

    # Each entry describes a different district. Summing them is not local rainfall.
    rainfall = observed.get('rainfall') or {}
    entries = rainfall.get('data', []) if isinstance(rainfall, dict) else []
    readings = [item for item in entries if isinstance(item, dict) and number(item.get('max')) is not None]
    highest = max(readings, key=lambda item: item['max']) if readings else {}
    if not model_card('rainfall', 'rainfall', '目標時段一小時預報雨量'):
        card('rainfall', '各地區一小時最高雨量', number(highest.get('max')), 'mm', station=highest.get('place'),
             updated_at=rainfall.get('endTime') if isinstance(rainfall, dict) else None,
             note='各地區最高雨量，並非全港累積雨量。' + ('逐小時雨量暫缺，沿用現有觀測，並非目標時段預報。' if future else ''))

    icons = observed.get('icon') or []
    from datetime import datetime, timezone
    from .visibility_observations import select_visibility
    visibility = select_visibility(observed.get('visibility_observations'), datetime.now(timezone.utc))
    if visibility:
        for reading in visibility['data']:
            card('visibility_' + reading['station'], '十分鐘平均能見度', reading['value'], 'km',
                 station=reading['station_name'], updated_at=reading['observed_at'],
                 note=('現有觀測，只作參考，並非目標時段能見度預報；未用作未來分數扣分。' if future
                       else '只代表此測站，並非全港或太陽方向光路能見度。中環讀數只限制遮擋因子上限，不額外加分。'))
    else:
        card('visibility', '十分鐘平均能見度', None, 'km', updated_at=None)
    card('weather_icon', '天氣狀況（觀測圖示）', icons[0] if isinstance(icons, list) and icons else None,
         note='沿用現有觀測圖示，並非目標時段預報。' if future else '天文台提供的天氣狀況代碼。')
    from .cloud_forecast import valid_cloud_forecast
    cloud = target.get('cloud_forecast')
    has_cloud = valid_cloud_forecast(cloud, target.get('forecast_target_at'))
    if has_cloud:
        for key, label in [('low', '低層雲量預報'), ('medium', '中層雲量預報'),
                           ('high', '高層雲量預報'), ('total', '總雲量預報')]:
            card('cloud_' + key, label, cloud[key], '%', kind='hourly_forecast',
                 source='MET Norway', station='香港參考點 22.30°N, 114.17°E',
                 updated_at=cloud.get('updated_at'), valid_at=cloud.get('valid_at'),
                 note='區域數值模式預報，並非現場觀測；層間可重疊，不能相加。'
                      + ('目標時間由相鄰兩個整點線性插值。' if cloud.get('method') == 'linear_interpolation' else ''))
    direction = target.get('sunward_cloud_forecast')
    direction_note = ''
    if isinstance(direction, dict):
        from .sunward_clouds import sunward_multiplier
        applied = sunward_multiplier(direction, cloud.get('valid_at') if has_cloud else '')
        direction_note = ('已參考太陽方向50及100公里低雲覆蓋，作遮擋風險估算。' if applied is not None
                          else '評估時間不在晨昏範圍，未套用方向扣分。' if direction.get('status') == 'outside_twilight'
                          else '太陽方向取樣未齊，保留原本雲層評分；沒有當作光路暢通。')
        for key, label in [('azimuth_deg', '太陽方位角'), ('elevation_deg', '太陽高度角')]:
            if number(direction.get(key)) is not None:
                card('solar_' + key, label, direction[key], '°', kind='calculated',
                     source='Astral 天文計算', updated_at=None, valid_at=direction.get('valid_at'),
                     station='香港參考點 22.30°N, 114.17°E',
                     note='方位角由正北起順時針計；高度角採幾何角度，未計地形遮擋。')
        samples = direction.get('samples')
        for sample in samples if isinstance(samples, list) else []:
            if not isinstance(sample, dict):
                continue
            sample_cloud = sample.get('cloud_forecast')
            present = valid_cloud_forecast(sample_cloud, target.get('forecast_target_at'))
            card('sunward_low_' + str(sample.get('distance_km')), f"太陽方向約{sample.get('distance_km')}公里低雲",
                 sample_cloud['low'] if present else None, '%', kind='hourly_forecast', source='MET Norway',
                 station=f"參考點 {sample.get('latitude')}°N, {sample.get('longitude')}°E",
                 updated_at=sample_cloud.get('updated_at') if present else None,
                 valid_at=sample_cloud.get('valid_at') if present else direction.get('valid_at'),
                 note=f"取樣方位{direction.get('sampling_bearing_deg')}°（最多偏離太陽方向2.5°）。低雲覆蓋並非實測透光率。")
    return {
        'cloud_attribution': ({'source': 'MET Norway', 'url': cloud.get('source_url'),
                               'license_url': cloud.get('license_url'),
                               'note': '分層雲量經時段插值及BurnSky規則計分。'} if has_cloud else
                              {'source': 'MET Norway', 'url': model.get('source_url'), 'license_url': model.get('license_url')}
                              if model else None),
        'summary': ('分層雲量採用MET Norway逐小時模式預報。' if has_cloud else '分層雲量暫缺，雲層計分沿用文字預報。')
                   + direction_note + '能見度列出現有測站觀測，並非未來預報；未能取得有效觀測時不補值。'
                   + (('溫濕度、風速及雨量優先採用MET Norway逐小時模式；缺失項目沿用推算、每日預報或現有觀測，逐項來源及時間請見卡片。UV及圖示仍為現有觀測。'
                       if model else '逐小時氣象資料暫缺。溫度及濕度為BurnSky推算；UV、雨量及圖示沿用現有觀測。風力為每日預報，各項時間請見卡片。')
                    if future else '溫度、濕度、UV及雨量取自天文台公開觀測；風力取自每日預報。缺失資料不會補作實測值。'),
        'cards': cards,
    }
