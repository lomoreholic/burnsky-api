"""Prepare immutable-style weather input bundles for prediction services."""

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .cloud_forecast import select_cloud_forecast
from .hourly_weather import select_hourly_weather


@dataclass
class PredictionInputs:
    observed_weather: dict
    target_weather: dict
    forecast_data: dict
    ninday_data: dict
    wind_data: dict
    warning_data: dict


class WeatherInputService:
    """Fetch cached data sources and prepare a prediction-time weather snapshot."""

    def __init__(self, get_cached_data, fetch_weather, fetch_forecast, fetch_ninday, fetch_wind, fetch_warnings, forecast_extractor,
                 fetch_cloud_forecast=None, now=None, sunward_service=None, fetch_visibility=None):
        self._get_cached_data = get_cached_data
        self._fetch_weather = fetch_weather
        self._fetch_forecast = fetch_forecast
        self._fetch_ninday = fetch_ninday
        self._fetch_wind = fetch_wind
        self._fetch_warnings = fetch_warnings
        self._forecast_extractor = forecast_extractor
        self._fetch_cloud_forecast = fetch_cloud_forecast
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._sunward_service = sunward_service
        self._fetch_visibility = fetch_visibility

    def prepare(self, advance_hours=0):
        """Return current inputs plus the weather snapshot for the requested horizon."""
        advance_hours = int(advance_hours)
        now = self._now()
        target_at = now + timedelta(hours=advance_hours)
        observed_weather = deepcopy(self._get_cached_data('weather', self._fetch_weather))
        if not isinstance(observed_weather, dict):
            observed_weather = {}
        from .visibility_observations import select_visibility
        observed_weather.pop('visibility_observations', None)
        if self._fetch_visibility:
            visibility = select_visibility(self._fetch_visibility(), now)
            if visibility:
                observed_weather['visibility_observations'] = visibility
        forecast_data = self._get_cached_data('forecast', self._fetch_forecast)
        ninday_data = self._get_cached_data('ninday', self._fetch_ninday)
        wind_data = self._get_cached_data('wind', self._fetch_wind)
        warning_data = self._get_cached_data('warning', self._fetch_warnings)

        observed_weather['wind'] = deepcopy(wind_data)
        observed_weather['warnings'] = deepcopy(warning_data)
        if advance_hours > 0:
            target_weather = self._forecast_extractor.extract_future_weather_data(
                deepcopy(observed_weather), forecast_data, ninday_data, advance_hours,
                evaluated_at=target_at
            )
            target_weather['wind'] = deepcopy(wind_data)
            target_weather['warnings'] = deepcopy(warning_data)
        else:
            target_weather = deepcopy(observed_weather)

        target_weather.pop('cloud_forecast', None)
        target_weather.pop('sunward_cloud_forecast', None)
        target_weather.pop('hourly_weather_forecast', None)
        target_weather['forecast_target_at'] = target_at.isoformat()
        target_weather['cloud_forecast_status'] = 'unavailable'
        if self._fetch_cloud_forecast:
            try:
                payload = self._fetch_cloud_forecast()
                cloud = select_cloud_forecast(payload, target_at, now)
                hourly = select_hourly_weather(payload, target_at, now) if advance_hours > 0 else None
            except (ValueError, TypeError, KeyError):
                cloud = None
                hourly = None
            if hourly:
                target_weather['hourly_weather_forecast'] = hourly
                for key in ('temperature', 'humidity'):
                    reading = hourly['fields'].get(key)
                    if reading:
                        target_weather[key] = {'data': [{'place': 'MET Norway香港參考點',
                                                        'value': reading['value'], 'unit': reading['unit']}],
                                               'source_kind': 'hourly_forecast', 'source': 'MET Norway'}
                speed = hourly['fields'].get('wind_speed')
                if speed:
                    target_weather['wind'] = dict(speed=speed['value'], unit='km/h', source_kind='hourly_forecast', source='MET Norway')
                rain = hourly['fields'].get('rainfall')
                if rain:
                    target_weather['rainfall'] = {'data': [{'place': 'MET Norway香港參考點', 'max': rain['value'], 'unit': 'mm'}],
                                                  'startTime': rain['period_start'], 'endTime': rain['period_end'],
                                                  'source_kind': 'hourly_forecast', 'source': 'MET Norway'}
            if cloud:
                target_weather['cloud_forecast'] = cloud
                target_weather['cloud_forecast_status'] = 'available'
                if self._sunward_service:
                    target_weather['sunward_cloud_forecast'] = self._sunward_service.assess(
                        target_at, now)

        return PredictionInputs(
            observed_weather=observed_weather,
            target_weather=target_weather,
            forecast_data=forecast_data,
            ninday_data=ninday_data,
            wind_data=wind_data,
            warning_data=warning_data
        )
