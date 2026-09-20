"""Prepare immutable-style weather input bundles for prediction services."""

from copy import deepcopy
from dataclasses import dataclass


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

    def __init__(self, get_cached_data, fetch_weather, fetch_forecast, fetch_ninday, fetch_wind, fetch_warnings, forecast_extractor):
        self._get_cached_data = get_cached_data
        self._fetch_weather = fetch_weather
        self._fetch_forecast = fetch_forecast
        self._fetch_ninday = fetch_ninday
        self._fetch_wind = fetch_wind
        self._fetch_warnings = fetch_warnings
        self._forecast_extractor = forecast_extractor

    def prepare(self, advance_hours=0):
        """Return current inputs plus the weather snapshot for the requested horizon."""
        advance_hours = int(advance_hours)
        observed_weather = deepcopy(self._get_cached_data('weather', self._fetch_weather))
        forecast_data = self._get_cached_data('forecast', self._fetch_forecast)
        ninday_data = self._get_cached_data('ninday', self._fetch_ninday)
        wind_data = self._get_cached_data('wind', self._fetch_wind)
        warning_data = self._get_cached_data('warning', self._fetch_warnings)

        observed_weather['wind'] = deepcopy(wind_data)
        observed_weather['warnings'] = deepcopy(warning_data)
        if advance_hours > 0:
            target_weather = self._forecast_extractor.extract_future_weather_data(
                deepcopy(observed_weather), forecast_data, ninday_data, advance_hours
            )
            target_weather['wind'] = deepcopy(wind_data)
            target_weather['warnings'] = deepcopy(warning_data)
        else:
            target_weather = observed_weather

        return PredictionInputs(
            observed_weather=observed_weather,
            target_weather=target_weather,
            forecast_data=forecast_data,
            ninday_data=ninday_data,
            wind_data=wind_data,
            warning_data=warning_data
        )