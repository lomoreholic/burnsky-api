"""Dated official pressure and air observations, with no fabricated fallbacks."""
import csv
from datetime import datetime, timedelta, timezone
import io
import json
import logging
import re
from threading import Lock

import requests

from .cloud_forecast import utc_time
from .prediction_presentation import HK_TIMEZONE
from .weather_presentation import number
from .http_session import weather_session

PRESSURE_URL = 'https://data.weather.gov.hk/weatherAPI/hko_data/regional-weather/latest_1min_pressure.csv'
AIR_URL = 'https://www.aqhi.gov.hk/js/data/past_24_pollutant.js'


def parse_pressure(text, retrieved_at):
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')))
    if reader.fieldnames != ['Date time', 'Automatic Weather Station', 'Mean Sea Level Pressure(hPa)']:
        return None
    rows = []
    for row in reader:
        if row['Automatic Weather Station'] != 'HK Observatory':
            continue
        try:
            stamp = row['Date time']
            if not re.fullmatch(r'\d{12}', stamp):
                continue
            at = datetime.strptime(stamp, '%Y%m%d%H%M').replace(tzinfo=HK_TIMEZONE)
            value = float(row['Mean Sea Level Pressure(hPa)'])
        except (ValueError, TypeError):
            continue
        if number(value) is not None and 850 <= value <= 1100:
            rows.append(dict(value=value, observed_at=at.isoformat(), station='香港天文台'))
    # A duplicated reference station is ambiguous.
    if len(rows) != 1:
        return None
    return dict(rows[0], unit='hPa', source='香港天文台', source_kind='observed',
                source_url=PRESSURE_URL, retrieved_at=retrieved_at.isoformat())


def parse_air(text, retrieved_at):
    # Decode the site's JSON assignment without executing JavaScript.
    text = text.lstrip('\ufeff')
    match = re.match(r'\s*var\s+station_24_data\s*=\s*', text)
    if not match:
        return None
    try:
        groups, _ = json.JSONDecoder().raw_decode(text[match.end():])
    except (ValueError, TypeError):
        return None
    if not isinstance(groups, list):
        return None
    rows = []
    for group in groups:
        if not isinstance(group, list):
            continue
        for row in group:
            if not isinstance(row, dict) or row.get('StationNameEN') != 'Central/Western' or row.get('type') != 'General Stations':
                continue
            if row.get('surrogate') not in ('false', False):
                continue
            try:
                at = datetime.strptime(row['DateTime'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=HK_TIMEZONE)
            except (ValueError, TypeError, KeyError):
                continue
            raw = row.get('aqhi')
            if not isinstance(raw, str) or not re.fullmatch(r'(?:[1-9]|10|10\+)', raw):
                continue
            aqhi = 11 if raw == '10+' else int(raw)
            components = {}
            for field, key in [('PM25', 'pm25'), ('PM10', 'pm10'), ('NO2', 'no2'), ('O3', 'o3')]:
                raw_value = row.get(field)
                if isinstance(raw_value, str) and re.fullmatch(r'\d+(?:\.\d+)?', raw_value):
                    value = float(raw_value)
                    if 0 <= value <= 5000:
                        components[key] = value
            rows.append(dict(aqhi=aqhi, aqhi_display=raw, observed_at=at.isoformat(),
                             station='中西區一般監測站', components=components))
    if not rows:
        return None
    latest = max(row['observed_at'] for row in rows)
    newest = [row for row in rows if row['observed_at'] == latest]
    if len(newest) != 1:
        return None
    return dict(newest[0], source='環境保護署', source_kind='observed', source_url=AIR_URL,
                retrieved_at=retrieved_at.isoformat(), components_unit='µg/m³')


def fresh_observation(payload, now, minutes):
    if not isinstance(payload, dict) or now.tzinfo is None:
        return None
    at, retrieved = utc_time(payload.get('observed_at')), utc_time(payload.get('retrieved_at'))
    if (at is None or retrieved is None or retrieved > now + timedelta(minutes=2)
            or at > retrieved + timedelta(minutes=2)
            or not timedelta(minutes=-2) <= now - at <= timedelta(minutes=minutes)):
        return None
    return dict(payload)


class ObservationClient:
    def __init__(self, url, parser, session=None, now=None):
        self.url, self.parser = url, parser
        self.session = session or weather_session()
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.next_fetch = datetime.min.replace(tzinfo=timezone.utc)
        self.payload = None
        self.lock = Lock()

    def fetch(self):
        with self.lock:
            now = self.now()
            if now < self.next_fetch:
                return self.payload
            self.next_fetch = now + timedelta(minutes=1)
            try:
                response = self.session.get(self.url, timeout=3,
                    headers={'User-Agent': 'BurnSky/1.0 (+https://github.com/lomoreholic/burnsky-api)'})
                response.raise_for_status()
                parsed = self.parser(response.content.decode('utf-8-sig'), self.now())
                if parsed is None:
                    raise ValueError('No valid reference observation')
                self.payload = parsed
                self.next_fetch = now + timedelta(minutes=5)
            except (requests.RequestException, UnicodeError, ValueError, csv.Error):
                logging.getLogger(__name__).warning('Official environmental observation unavailable; retaining dated cache')
            return self.payload
