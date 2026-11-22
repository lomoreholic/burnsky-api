"""Sunward cloud cover is a regional obstruction proxy, not ray tracing."""

from concurrent.futures import ThreadPoolExecutor
from math import asin, atan2, cos, degrees, radians, sin
from threading import Lock

import requests

from .cloud_forecast import CloudForecastClient, select_cloud_forecast, utc_time, valid_cloud_forecast
from .weather_presentation import number


LATITUDE, LONGITUDE = 22.30, 114.17
DISTANCES_KM = (50, 100)
METHOD = 'sunward_low_cloud_proxy_v1'


def solar_position(target_at):
    """Use the actual evaluated instant, not a hardcoded east/west direction."""
    from astral import Observer
    from astral.sun import azimuth, elevation
    observer = Observer(LATITUDE, LONGITUDE)
    return {'azimuth_deg': azimuth(observer, target_at),
            'elevation_deg': elevation(observer, target_at, with_refraction=False)}


def destination(latitude, longitude, bearing_deg, distance_km):
    """Great-circle destination on a spherical earth; retain four decimal places."""
    lat, lon, bearing = map(radians, (latitude, longitude, bearing_deg))
    angle = distance_km / 6371.0088
    dest_lat = asin(sin(lat) * cos(angle) + cos(lat) * sin(angle) * cos(bearing))
    dest_lon = lon + atan2(sin(bearing) * sin(angle) * cos(lat), cos(angle) - sin(lat) * sin(dest_lat))
    return round(degrees(dest_lat), 4), round((degrees(dest_lon) + 540) % 360 - 180, 4)


def sunward_multiplier(assessment, target_at=None):
    """Return a downside-only multiplier only for two complete, aligned samples.

    Maximum 60% reduction at fully covered low-cloud samples is an initial
    heuristic, not a measured transmission or a probability of obstruction.
    """
    if not isinstance(assessment, dict) or assessment.get('status') != 'available':
        return None
    valid_at = utc_time(assessment.get('valid_at'))
    if valid_at is None:
        return None
    if target_at is not None and valid_at != utc_time(target_at):
        return None
    samples = assessment.get('samples')
    if not isinstance(samples, list) or len(samples) != len(DISTANCES_KM):
        return None
    if (number(assessment.get('azimuth_deg')) is None or not 0 <= assessment['azimuth_deg'] < 360
            or number(assessment.get('elevation_deg')) is None
            or not -8 <= assessment['elevation_deg'] <= 8):
        return None
    distances = []
    for sample in samples:
        if not isinstance(sample, dict):
            return None
        cloud = sample.get('cloud_forecast')
        if not valid_cloud_forecast(cloud, assessment.get('valid_at')):
            return None
        distances.append(sample.get('distance_km'))
    if tuple(distances) != DISTANCES_KM:
        return None
    return round(1 - .6 * max(sample['cloud_forecast']['low'] for sample in samples) / 100, 4)


class SunwardCloudService:
    def __init__(self, client_factory=None, position=solar_position):
        self._factory = client_factory or (lambda lat, lon: CloudForecastClient(
            latitude=lat, longitude=lon, timeout=(2, 3)))
        self._position = position
        self._clients = {}
        self._lock = Lock()

    def _sample(self, distance_km, bearing, target_at, now):
        lat, lon = destination(LATITUDE, LONGITUDE, bearing, distance_km)
        # 72 bearing sectors × 2 distances bounds the per-process client cache.
        with self._lock:
            key = (lat, lon)
            if key not in self._clients:
                self._clients[key] = self._factory(lat, lon)
            client = self._clients[key]
        try:
            cloud = select_cloud_forecast(client.fetch(), target_at, now, latitude=lat, longitude=lon)
        except (requests.RequestException, ValueError, TypeError, KeyError):
            cloud = None
        return dict(distance_km=distance_km, latitude=lat, longitude=lon, cloud_forecast=cloud)

    def assess(self, target_at, now):
        result = dict(status='unavailable', method=METHOD, valid_at=target_at.isoformat(),
                      observer={'latitude': LATITUDE, 'longitude': LONGITUDE}, samples=[],
                      limitation='只沿太陽方向取兩點低雲覆蓋；未計雲厚、雲底高度、山勢或真正光線穿透。')
        try:
            position = self._position(target_at)
            azimuth, elevation = position['azimuth_deg'], position['elevation_deg']
            if (number(azimuth) is None or not 0 <= azimuth < 360
                    or number(elevation) is None or not -90 <= elevation <= 90):
                return result
        except (ImportError, ValueError, TypeError, KeyError):
            return result
        result.update(azimuth_deg=round(azimuth, 3), elevation_deg=round(elevation, 3))
        if not -8 <= elevation <= 8:
            result['status'] = 'outside_twilight'
            return result
        # Quantise within 2.5° to reuse spatial forecasts rather than querying
        # slightly different coordinates every refresh. Keep actual bearing too.
        bearing = (int((azimuth + 2.5) // 5) * 5) % 360
        result['sampling_bearing_deg'] = bearing
        with ThreadPoolExecutor(max_workers=2) as pool:
            result['samples'] = list(pool.map(
                lambda distance: self._sample(distance, bearing, target_at, now), DISTANCES_KM))
        available = sum(sample['cloud_forecast'] is not None for sample in result['samples'])
        result['status'] = 'available' if available == 2 else 'partial' if available else 'unavailable'
        result['score_multiplier'] = sunward_multiplier(result)
        return result
