"""Dated HKO visibility observations; never a future visibility forecast."""
import csv
from datetime import datetime, timedelta, timezone
import io
import logging
import re
from threading import Lock

import requests

from .cloud_forecast import utc_time
from .prediction_presentation import HK_TIMEZONE
from .weather_presentation import number
from .http_session import weather_session


SOURCE_URL = 'https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=LTMV&lang=en&rformat=csv'
STATIONS = {'Central': '中環', 'Chek Lap Kok': '赤鱲角', 'Sai Wan Ho': '西灣河', 'Waglan Island': '橫瀾島'}
HEADERS = ['Date time', 'Automatic Weather Station', '10 minute mean visibility']


def parse_visibility_csv(text, retrieved_at):
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    if reader.fieldnames != HEADERS:
        return None
    records, duplicates = {}, set()
    for row in reader:
        station = row.get(HEADERS[1])
        stamp = row.get(HEADERS[0], '')
        match = re.fullmatch(r'([0-9]+(?:\.[0-9]+)?)\s*(km|m)', (row.get(HEADERS[2]) or '').strip())
        if station not in STATIONS or not re.fullmatch(r'\d{12}', stamp) or match is None:
            continue
        try:
            observed = datetime.strptime(stamp, '%Y%m%d%H%M').replace(tzinfo=HK_TIMEZONE)
            km = float(match[1]) / (1000 if match[2] == 'm' else 1)
        except ValueError:
            continue
        if not 0 <= km <= 100:
            continue
        key = (station, observed)
        if key in records:
            duplicates.add(key)
        records[key] = dict(station=station, station_name=STATIONS[station], value=km, unit='km',
                            native_value=row[HEADERS[2]], observed_at=observed.isoformat())
    data = [record for key, record in records.items() if key not in duplicates]
    return dict(source='香港天文台', source_url=SOURCE_URL, retrieved_at=retrieved_at.isoformat(), data=data) if data else None


def select_visibility(payload, now):
    """Filter every row on use, including cached responses after an outage."""
    if not isinstance(payload, dict) or now.tzinfo is None:
        return None
    retrieved = utc_time(payload.get('retrieved_at'))
    if retrieved is None or retrieved > now + timedelta(minutes=2):
        return None
    latest = {}
    rows = payload.get('data')
    if not isinstance(rows, list):
        return None
    for row in rows:
        if not isinstance(row, dict) or row.get('station') not in STATIONS or row.get('unit') != 'km':
            continue
        observed, km = utc_time(row.get('observed_at')), number(row.get('value'))
        if (observed is None or km is None or not 0 <= km <= 100
                or observed > retrieved + timedelta(minutes=2)
                or not timedelta(minutes=-2) <= now - observed <= timedelta(minutes=30)):
            continue
        previous = latest.get(row['station'])
        if previous is None or observed > utc_time(previous['observed_at']):
            latest[row['station']] = dict(row)
    if not latest:
        return None
    return dict(source='香港天文台', source_url=SOURCE_URL, retrieved_at=payload['retrieved_at'],
                data=list(latest.values()), reference_station='Central')


def reference_visibility(weather):
    selected = select_visibility(weather.get('visibility_observations'), datetime.now(timezone.utc))
    return next((row for row in selected['data'] if row['station'] == 'Central'), None) if selected else None


def visibility_score_cap(km):
    """Uncalibrated downward-only cap on the existing rain-obstruction factor."""
    if number(km) is None or not 0 <= km <= 100:
        return None
    if km == 0:
        return 0
    for minimum, cap in ((10, 20), (5, 15), (2, 8), (1, 4), (0, 1)):
        if km >= minimum:
            return cap


class VisibilityClient:
    def __init__(self, session=None, now=None):
        self._session = session or weather_session()
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._next_fetch = datetime.min.replace(tzinfo=timezone.utc)
        self._payload = None
        self._lock = Lock()

    def fetch(self):
        with self._lock:
            now = self._now()
            if now < self._next_fetch:
                return self._payload
            self._next_fetch = now + timedelta(minutes=1)
            try:
                response = self._session.get(SOURCE_URL, timeout=3,
                    headers={'User-Agent': 'BurnSky/1.0 (+https://github.com/lomoreholic/burnsky-api)'})
                response.raise_for_status()
                parsed = parse_visibility_csv(response.content.decode('utf-8-sig'), self._now())
                if parsed is None:
                    raise ValueError('No valid visibility rows')
                self._payload = parsed
                self._next_fetch = now + timedelta(minutes=5)
            except (requests.RequestException, UnicodeError, ValueError, csv.Error):
                logging.getLogger(__name__).warning('HKO visibility unavailable; retaining dated cache')
            return self._payload
