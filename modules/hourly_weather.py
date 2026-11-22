"""Target-time regional model weather, with separate instantaneous/period values."""

from datetime import timedelta

from .cloud_forecast import LICENSE_URL, SOURCE_URL, utc_time
from .weather_presentation import number


# Native units are checked before converting speed to the scorer's km/h.
FIELDS = {
    'temperature': ('air_temperature', 'celsius', -50, 60, '°C', 1),
    'humidity': ('relative_humidity', '%', 0, 100, '%', 1),
    'wind_speed': ('wind_speed', 'm/s', 0, 300 / 3.6, 'km/h', 3.6),
}


def model_reading(weather, key):
    """Revalidate selected fields against the snapshot target at consumption."""
    if key not in (*FIELDS, 'rainfall'):
        return None
    model = weather.get('hourly_weather_forecast')
    fields = model.get('fields') if isinstance(model, dict) else None
    reading = fields.get(key) if isinstance(fields, dict) else None
    target = utc_time(weather.get('forecast_target_at'))
    valid_at = utc_time(model.get('valid_at')) if isinstance(model, dict) else None
    if target is None or valid_at != target:
        return None
    unit = 'mm' if key == 'rainfall' else FIELDS[key][4]
    if not isinstance(reading, dict) or reading.get('unit') != unit:
        return None
    value = number(reading.get('value'))
    if value is None:
        return None
    low, high = (0, 1000) if key == 'rainfall' else (FIELDS[key][2] * FIELDS[key][5], FIELDS[key][3] * FIELDS[key][5])
    if not low <= value <= high:
        return None
    raw_samples = reading.get('sample_times')
    if not isinstance(raw_samples, list) or len(raw_samples) not in (1, 2):
        return None
    samples = [utc_time(at) for at in raw_samples]
    if any(at is None for at in samples):
        return None
    method = reading.get('method')
    if key == 'rainfall':
        start, end = (utc_time(reading.get(key)) for key in ('period_start', 'period_end'))
        usable = (method == 'hourly_accumulation' and start is not None and end is not None
                  and end - start == timedelta(hours=1) and start <= target < end
                  and samples == [start])
    elif method == 'hourly_model':
        usable = samples == [target]
    elif method == 'linear_interpolation':
        usable = (len(samples) == 2 and samples[0] < target < samples[1]
                  and samples[1] - samples[0] <= timedelta(hours=1))
    else:
        usable = False
    return reading if usable else None


def select_hourly_weather(payload, target_at, now):
    """No extrapolation, missing-hour bridging or six-hour rain disaggregation."""
    if not isinstance(payload, dict) or target_at.tzinfo is None or now.tzinfo is None:
        return None
    properties = payload.get('properties')
    if not isinstance(properties, dict):
        return None
    meta = properties.get('meta')
    updated = utc_time(meta.get('updated_at')) if isinstance(meta, dict) else None
    if updated is None or not timedelta(minutes=-15) <= now - updated <= timedelta(hours=18):
        return None
    units = meta.get('units')
    series = properties.get('timeseries')
    if not isinstance(units, dict) or not isinstance(series, list):
        return None
    records = {}
    for entry in series:
        if not isinstance(entry, dict):
            continue
        at = utc_time(entry.get('time'))
        if at is not None:
            # Conflicting duplicate timestamps are ambiguous, not last-write-wins.
            records[at] = entry.get('data') if at not in records else None
    before = max((at for at in records if at <= target_at), default=None)
    after = min((at for at in records if at >= target_at), default=None)
    fields = {}

    def details(at, period):
        data = records.get(at)
        block = data.get(period) if isinstance(data, dict) else None
        result = block.get('details') if isinstance(block, dict) else None
        return result if isinstance(result, dict) else {}

    if before is not None and after is not None and after - before <= timedelta(hours=1):
        fraction = (target_at - before) / (after - before) if before != after else 0
        for key, (field, native_unit, low, high, unit, scale) in FIELDS.items():
            first, last = (number(details(at, 'instant').get(field)) for at in (before, after))
            if units.get(field) != native_unit or first is None or last is None or not low <= first <= high or not low <= last <= high:
                continue
            fields[key] = dict(value=round((first + fraction * (last - first)) * scale, 2), unit=unit,
                               native_unit=native_unit, sample_times=[before.isoformat()] if before == after else [before.isoformat(), after.isoformat()],
                               method='hourly_model' if before == after else 'linear_interpolation')
    # next_1_hours is accumulation over [record time, record time + 1h).
    # Keep that complete interval; do not interpolate or pro-rate its amount.
    if before is not None and before <= target_at < before + timedelta(hours=1) and units.get('precipitation_amount') == 'mm':
        amount = number(details(before, 'next_1_hours').get('precipitation_amount'))
        if amount is not None and 0 <= amount <= 1000:
            fields['rainfall'] = dict(value=amount, unit='mm', method='hourly_accumulation',
                                      period_start=before.isoformat(), period_end=(before + timedelta(hours=1)).isoformat(),
                                      sample_times=[before.isoformat()])
    if not fields:
        return None
    return dict(source='MET Norway', source_url=SOURCE_URL, license_url=LICENSE_URL,
                latitude=22.30, longitude=114.17, updated_at=updated.isoformat(),
                retrieved_at=payload.get('_burnsky_retrieved_at'), valid_at=target_at.isoformat(),
                fields=fields, missing_fields=[key for key in (*FIELDS, 'rainfall') if key not in fields])
