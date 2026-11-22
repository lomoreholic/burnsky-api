"""Use Windows' trusted certificate store while retaining HTTPS verification."""
import ssl
import sys

import requests
from requests.adapters import HTTPAdapter


class SystemTrustAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = ssl.create_default_context()
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **kwargs):
        kwargs['ssl_context'] = ssl.create_default_context()
        return super().proxy_manager_for(proxy, **kwargs)


def weather_session():
    session = requests.Session()
    if sys.platform == 'win32':
        session.mount('https://', SystemTrustAdapter())
    return session
