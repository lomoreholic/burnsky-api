"""Hourly model cloud inputs; the cloud score remains an uncalibrated heuristic."""

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import logging
from threading import Lock

import requests

from .weather_presentation import number
from .http_session import weather_session


SOURCE_URL = 'https://api.met.no/weatherapi/locationforecast/2.0/complete?lat=22.30&lon=114.17'
LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/'
FIELDS = {'total': 'cloud_area_fraction', 'low': 'cloud_area_fraction_low',
          'medium': 'cloud_area_fraction_medium', 'high': 'cloud_area_fraction_high'}


def forecast_url(latitude, longitude):
    return ('https://api.met.no/weatherapi/locationforecast/2.0/complete'
            f'?lat={latitude:.4f}&lon={longitude:.4f}')


def utc_time(value):
    try:
        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value.astimezone(timezone.utc) if value.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None


def valid_cloud_layers(cloud):
    return isinstance(cloud, dict) and all(
        number(cloud.get(key)) is not None and 0 <= cloud[key] <= 100 for key in FIELDS)


def valid_cloud_forecast(cloud, target_at):
    """Require usable layer values and samples covering the snapshot target."""
    target = utc_time(target_at)
    if not valid_cloud_layers(cloud) or target is None or utc_time(cloud.get('valid_at')) != target:
        return False
    raw_samples = cloud.get('sample_times')
    if not isinstance(raw_samples, list) or len(raw_samples) not in (1, 2):
        return False
    samples = [utc_time(at) for at in raw_samples]
    if any(at is None for at in samples):
        return False
    if cloud.get('method') == 'hourly_model':
        return samples == [target]
    if cloud.get('method') == 'linear_interpolation':
        return (len(samples) == 2 and samples[0] < target < samples[1]
                and samples[1] - samples[0] <= timedelta(hours=1))
    return False


def select_cloud_forecast(payload, target_at, now, *, latitude=22.30, longitude=114.17):
    """Interpolate only between adjacent hourly records; never extrapolate.

    Reject model runs older than 18h, allowing normal global model publication
    latency without using yesterday's forecast indefinitely during an outage.
    """
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
    if not isinstance(units, dict) or any(units.get(field) != '%' for field in FIELDS.values()):
        return None
    series = properties.get('timeseries')
    if not isinstance(series, list):
        return None
    records = {}
    for entry in series:
        if not isinstance(entry, dict):
            continue
        instant = utc_time(entry.get('time'))
        if instant is None:
            continue
        if instant in records:
            # Duplicates remain ambiguous regardless of order or layer validity.
            records[instant] = None
            continue
        try:
            details = entry['data']['instant']['details']
            layers = {key: details.get(field) for key, field in FIELDS.items()}
        except (KeyError, TypeError, AttributeError):
            layers = None
        records[instant] = layers if valid_cloud_layers(layers) else None
    times = sorted(records)
    before = max((time for time in times if time <= target_at), default=None)
    after = min((time for time in times if time >= target_at), default=None)
    if before is None or after is None or after - before > timedelta(hours=1):
        return None
    if records[before] is None or records[after] is None:
        return None
    fraction = (target_at - before) / (after - before) if after != before else 0
    layers = {key: round(records[before][key] + fraction * (records[after][key] - records[before][key]), 2)
              for key in FIELDS}
    return dict(layers, source='MET Norway', source_url=forecast_url(latitude, longitude), license_url=LICENSE_URL,
                updated_at=updated.isoformat(), valid_at=target_at.isoformat(),
                sample_times=[before.isoformat(), after.isoformat()] if before != after else [before.isoformat()],
                method='linear_interpolation' if before != after else 'hourly_model',
                retrieved_at=payload.get('_burnsky_retrieved_at'),
                latitude=latitude, longitude=longitude, score_method='layered_cloud_heuristic_v1')


def score_cloud_layers(cloud):
    """0–35 points: middle/high cloud canvas reduced by low cloud obstruction.

    Layer overlap is unknown, so use the larger middle/high coverage, not their
    sum. Constants are explicit initial assumptions, not fitted probabilities.
    No cloud optical depth or sunward horizon information is available here.
    """
    if not valid_cloud_layers(cloud):
        return None
    canvas = min(cloud['total'], max(cloud['medium'], cloud['high'])) / 100
    suitability = canvas / .6 if canvas <= .6 else 1 - .6 * (canvas - .6) / .4
    transmission = 1 - .85 * cloud['low'] / 100
    return round(max(0, min(35, 35 * suitability * transmission)), 2)


class CloudForecastClient:
    """Shared backend cache honours Expires and conditional GET, with failsoft retries."""

    def __init__(self, session=None, now=None, *, latitude=22.30, longitude=114.17, timeout=(3, 5)):
        if (number(latitude) is None or not -90 <= latitude <= 90
                or number(longitude) is None or not -180 <= longitude <= 180):
            raise ValueError('Invalid forecast coordinates')
        self.source_url = forecast_url(latitude, longitude)
        self._timeout = timeout
        self._session = session or weather_session()
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._payload = None
        self._next_fetch = datetime.min.replace(tzinfo=timezone.utc)
        self._last_modified = None
        self._lock = Lock()

    def fetch(self):
        with self._lock:
            now = self._now()
            if now < self._next_fetch:
                return self._payload
            headers = {'User-Agent': 'BurnSky/1.0 (+https://github.com/lomoreholic/burnsky-api)'}
            if self._last_modified:
                headers['If-Modified-Since'] = self._last_modified
            self._next_fetch = now + timedelta(minutes=15)
            try:
                response = self._session.get(self.source_url, headers=headers, timeout=self._timeout)
                # Respect server retry/backoff headers even on failures.
                for header in ('Expires', 'Retry-After'):
                    value = response.headers.get(header)
                    if value:
                        try:
                            deadline = (now + timedelta(seconds=int(value)) if value.isdigit()
                                        else parsedate_to_datetime(value))
                            if deadline.tzinfo:
                                self._next_fetch = max(self._next_fetch, deadline)
                        except (ValueError, TypeError, OverflowError):
                            pass
                if response.status_code == 304:
                    return self._payload
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError('Cloud forecast response is not an object')
                payload['_burnsky_retrieved_at'] = now.isoformat()
                self._payload = payload
                self._last_modified = response.headers.get('Last-Modified')
            except (requests.RequestException, ValueError):
                logging.getLogger(__name__).warning('Hourly cloud provider unavailable; using validated cache or HKO text')
            return self._payload
