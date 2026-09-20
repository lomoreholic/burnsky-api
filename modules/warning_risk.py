"""Future weather warning-risk assessment for advance predictions."""

from datetime import datetime


class FutureWarningRiskService:
    """Estimate warning risk from forecast conditions and prediction horizon."""

    def __init__(self, forecast_extractor, now=datetime.now):
        self._forecast_extractor = forecast_extractor
        self._now = now

    def assess(self, weather_data, forecast_data, ninday_data, advance_hours):
        advance_hours = int(advance_hours)
        if advance_hours <= 0:
            return 0, []

        warnings = []
        try:
            future_weather = self._forecast_extractor.extract_future_weather_data(
                weather_data, forecast_data, ninday_data, advance_hours
            )
        except Exception as error:
            print(f'🔮 警告: 無法提取未來天氣數據: {error}')
            future_weather = {}

        rainfall_risk = self._rainfall_risk(ninday_data, advance_hours, warnings)
        wind_risk = self._wind_risk(future_weather, warnings)
        visibility_risk = self._visibility_risk(future_weather, warnings)
        seasonal_risk = self._seasonal_risk(advance_hours, warnings)
        time_uncertainty = min(advance_hours * 0.5, 8)
        total_risk = rainfall_risk + wind_risk + visibility_risk + seasonal_risk + time_uncertainty
        return min(total_risk, min(20, advance_hours * 2)), warnings

    @staticmethod
    def _rainfall_risk(ninday_data, advance_hours, warnings):
        if not ninday_data or advance_hours > 48:
            return 0
        forecast = ninday_data.get('weatherForecast', [])
        if not forecast:
            return 0
        psr = forecast[0].get('PSR', 'Low')
        if psr in ('High', '高'):
            warnings.append('高降雨概率 - 可能發出雨量警告')
            return 15
        if psr in ('Medium High', '中高'):
            warnings.append('中高降雨概率 - 有雨量警告風險')
            return 10
        if psr in ('Medium', '中等'):
            warnings.append('中等降雨概率 - 輕微雨量警告風險')
            return 5
        return 0

    @staticmethod
    def _wind_risk(future_weather, warnings):
        try:
            speed = float(future_weather.get('wind', {}).get('speed', 0))
        except (AttributeError, TypeError, ValueError):
            return 0
        if speed >= 88:
            warnings.append('預測強風 - 可能發出烈風警告')
            return 12
        if speed >= 62:
            warnings.append('預測中等風力 - 有強風警告風險')
            return 8
        return 0

    @staticmethod
    def _visibility_risk(future_weather, warnings):
        try:
            humidity = float(future_weather.get('humidity', {}).get('value', 50))
        except (AttributeError, TypeError, ValueError):
            return 0
        if humidity >= 95:
            warnings.append('極高濕度 - 可能出現霧患')
            return 8
        if humidity >= 85:
            warnings.append('高濕度 - 有能見度下降風險')
            return 4
        return 0

    def _seasonal_risk(self, advance_hours, warnings):
        month = self._now().month
        if month in (6, 7, 8, 9) and advance_hours >= 2:
            warnings.append('雷暴季節 - 雷暴發展風險')
            return 6
        if month in (12, 1, 2):
            warnings.append('冬季 - 霧霾風險較高')
            return 3
        if month in (3, 4, 5):
            warnings.append('春季 - 天氣變化較大')
            return 4
        return 2