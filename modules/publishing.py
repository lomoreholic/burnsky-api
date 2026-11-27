"""Keep advertising separate from operational and development pages."""

import os

from flask import request


AD_CONTENT_PATHS = frozenset({
    '/photography-guide', '/best-locations', '/weather-terms', '/faq',
    '/how-it-works',
})
UTILITY_PATHS = frozenset({
    '/status', '/health', '/api', '/ml-test', '/chart-test',
    '/charts-showcase', '/photo-analysis-test', '/test_api.html',
    '/chart_debug.html',
})


def configure_publishing(app):
    @app.context_processor
    def advertising_context():
        return {
            'ADSENSE_ALLOWED': (
                os.getenv('ADSENSE_ENABLED', 'false').lower() == 'true'
                and request.path in AD_CONTENT_PATHS
                and request.method in {'GET', 'HEAD'}
            ),
        }

    @app.after_request
    def indexing_headers(response):
        if (response.status_code >= 400 or request.path in UTILITY_PATHS
                or request.path.startswith(('/api/', '/predict'))):
            response.headers['X-Robots-Tag'] = 'noindex'
        return response
