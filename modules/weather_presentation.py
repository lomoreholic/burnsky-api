"""Describe the actual origin of display values without filling missing readings."""

from math import isfinite


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) else None


def build_weather_presentation(target, observed, advance_hours, timing):
    cards = []
    future = advance_hours > 0
    observed_at = observed.get('updateTime')

    def card(key, label, value, unit='', *, kind='observed', source='香港天文台公開資料',
             station=None, note='', updated_at=observed_at, valid_at=None):
        if value is None:
            kind, source, note = 'unavailable', '', '未取得可用數據。'
        cards.append(dict(key=key, label=label, value=value, unit=unit, source_kind=kind,
                          source=source, station=station, note=note,
                          updated_at=updated_at, valid_at=valid_at))

    for key, label, unit in [('temperature', '溫度', '°C'), ('humidity', '相對濕度', '%')]:
        block = target.get(key)
        entries = block.get('data', []) if isinstance(block, dict) else []
        reading = next((item for item in entries if isinstance(item, dict) and item.get('place') == '香港天文台'), {})
        card(key, label, number(reading.get('value')), unit, station=reading.get('place'),
             kind='estimated' if future else 'observed',
             source='BurnSky 條件推算' if future else '香港天文台公開資料',
             valid_at=timing['evaluated_at'] if future else None,
             note='按觀測及可用預報推算，並非天文台逐小時預報。' if future else '')

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
    card('wind', '風力預報', description or None, kind='forecast', source='香港天文台九天天氣預報',
         updated_at=wind.get('source_updated_at') if isinstance(wind, dict) else None,
         valid_at=wind.get('forecast_date') if isinstance(wind, dict) else None,
         note='每日預報文字，並非風站實測；未來模式仍沿用此日的風力資料。' if future else '每日預報文字，並非風站實測。')

    # Each entry describes a different district. Summing them is not local rainfall.
    rainfall = observed.get('rainfall') or {}
    entries = rainfall.get('data', []) if isinstance(rainfall, dict) else []
    readings = [item for item in entries if isinstance(item, dict) and number(item.get('max')) is not None]
    highest = max(readings, key=lambda item: item['max']) if readings else {}
    card('rainfall', '各地區一小時最高雨量', number(highest.get('max')), 'mm', station=highest.get('place'),
         updated_at=rainfall.get('endTime') if isinstance(rainfall, dict) else None,
         note='各地區最高雨量，並非全港累積雨量。' + ('沿用現有觀測，並非目標時段預報。' if future else ''))

    icons = observed.get('icon') or []
    card('weather_icon', '天氣狀況（觀測圖示）', icons[0] if isinstance(icons, list) and icons else None,
         note='沿用現有觀測圖示，並非目標時段預報。' if future else '天文台提供的天氣狀況代碼。')
    return {
        'summary': ('溫度及濕度為BurnSky推算；UV、雨量及圖示沿用現有觀測。風力為每日預報，各項時間請見卡片。'
                    if future else '溫度、濕度、UV及雨量取自天文台公開觀測；風力取自每日預報。缺失資料不會補作實測值。'),
        'cards': cards,
    }
