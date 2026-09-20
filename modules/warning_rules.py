"""Pure scoring rules for parsed weather warnings."""


def calculate_warning_impact_advanced(warning_info, time_of_day='day', season='summer'):
    """Calculate a capped impact score and its explanatory multipliers."""
    severity_base = {'extreme': 35, 'severe': 25, 'moderate': 15, 'low': 8}
    category_adjustments = {
        'rainfall': {'black_rain': 0, 'red_rain': -3, 'amber_rain': -2, 'flood_warning': 2},
        'wind_storm': {'hurricane_10': 5, 'gale_9': 2, 'strong_wind_8': -2, 'strong_wind_3': -3, 'standby_1': -5},
        'thunderstorm': {'severe_thunderstorm': 2, 'general_thunderstorm': -8},
        'visibility': {'dense_fog': 1, 'general_fog': -4},
        'air_quality': {'severe_pollution': -10, 'moderate_pollution': -12},
        'temperature': {'extreme_heat': -8, 'extreme_cold': 2},
        'marine': {'marine_warning': -5}
    }
    base_impact = severity_base.get(warning_info['severity'], 5)
    base_impact += category_adjustments.get(warning_info['category'], {}).get(warning_info['subcategory'], 0)
    multipliers = []

    if time_of_day in ('sunset', 'sunrise'):
        if warning_info['category'] == 'visibility':
            multipliers.append(('能見度在燒天時段更重要', 1.3))
        elif warning_info['category'] == 'air_quality':
            multipliers.append(('空氣品質影響燒天效果', 0.7))

    if season == 'summer':
        if warning_info['category'] == 'thunderstorm':
            multipliers.append(('夏季雷暴頻繁', 0.8))
        elif warning_info['category'] == 'temperature' and warning_info['subcategory'] == 'extreme_heat':
            multipliers.append(('夏季高溫常見', 0.6))
    elif season == 'winter':
        if warning_info['category'] == 'visibility':
            multipliers.append(('冬季霧霾常見', 1.2))
        elif warning_info['category'] == 'air_quality':
            multipliers.append(('冬季空氣品質較差', 1.1))

    if warning_info['area_specific']:
        multipliers.append(('地區性警告影響較小', 0.9))
    if warning_info['duration_hint'] == '間歇性警告':
        multipliers.append(('間歇性警告影響較小', 0.8))
    elif warning_info['duration_hint'] == '持續性警告':
        multipliers.append(('持續性警告影響較大', 1.1))

    final_impact = base_impact
    for _, multiplier in multipliers:
        final_impact *= multiplier
    return round(max(0, min(final_impact, 10)), 1), multipliers