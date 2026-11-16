"""Describe condition scores and their actual evaluation time without probabilities."""

from datetime import datetime, timedelta, timezone


HK_TIMEZONE = timezone(timedelta(hours=8))
SCORE_DEFINITION = '燒天條件指數（0–100）反映氣象條件的有利程度，並非燒天發生機率，亦不保證出現。'


def get_condition_level(score):
    for minimum, label in (
        (80, '條件極佳'), (65, '條件良好'), (45, '條件一般'),
        (30, '條件偏低'), (0, '條件很低'),
    ):
        if score >= minimum:
            return label
    return '條件很低'


def build_viewing_windows(now, get_sun_times):
    """Solar viewing references remain available independently of weather scores."""
    now = now.astimezone(HK_TIMEZONE)
    windows = []
    for offset in (0, 1):
        day = now.date() + timedelta(days=offset)
        sun = get_sun_times(day)
        for event_type in ('sunrise', 'sunset'):
            event = datetime.combine(day, datetime.strptime(sun[event_type], '%H:%M').time(), tzinfo=HK_TIMEZONE)
            windows.append({'event_type': event_type, 'event_at': event.isoformat(),
                            'window_start': (event - timedelta(minutes=30)).isoformat(),
                            'window_end': (event + timedelta(minutes=30)).isoformat(),
                            'method': sun.get('method', 'calculated')})
    return windows


def build_prediction_timing(generated_at, prediction_type, advance_hours, get_sun_times):
    """Keep the evaluated instant separate from the solar event on that date.

    Solar events are references only: selecting sunrise at night does not turn a
    current-conditions score into a forecast for the following morning.
    """
    generated_at = generated_at.astimezone(HK_TIMEZONE)
    evaluated_at = generated_at + timedelta(hours=advance_hours)
    sun_times = get_sun_times(evaluated_at.date())
    # The existing scorer also treats modes other than sunrise as sunset.
    event_type = 'sunrise' if prediction_type == 'sunrise' else 'sunset'
    event_time = datetime.strptime(sun_times[event_type], '%H:%M').time()
    event_at = datetime.combine(evaluated_at.date(), event_time, tzinfo=HK_TIMEZONE)
    window_start = event_at - timedelta(minutes=30)
    window_end = event_at + timedelta(minutes=30)
    timing = {
        'timezone': 'Asia/Hong_Kong',
        'generated_at': generated_at.isoformat(),
        'evaluated_at': evaluated_at.isoformat(),
        'mode': 'forecast' if advance_hours > 0 else 'current',
        'event_type': event_type,
        'event_at': event_at.isoformat(),
        'window_start': window_start.isoformat(),
        'window_end': window_end.isoformat(),
        'within_reference_window': window_start <= evaluated_at <= window_end,
    }
    return timing, sun_times
