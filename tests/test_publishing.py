"""Exercise real templates without importing app startup or writing live databases."""

import ast
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from flask import Flask, render_template
import pytest

from modules.publishing import AD_CONTENT_PATHS, UTILITY_PATHS, configure_publishing


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = {
    '/': 'index.html', '/photography-guide': 'photography_guide.html',
    '/best-locations': 'best_locations.html', '/weather-terms': 'weather_terms.html',
    '/faq': 'faq.html', '/how-it-works': 'how_it_works.html',
    '/status': 'status.html', '/api-docs': 'api_docs.html',
    '/about': 'about.html', '/contact': 'contact.html',
    '/privacy': 'privacy.html', '/terms': 'terms.html',
    '/photo-analysis': 'photo_analysis.html', '/webcam-analysis': 'webcam_analysis.html',
    '/burnsky-dashboard': 'burnsky_dashboard.html',
    '/ml-test': 'ml_test.html', '/charts-showcase': 'charts_showcase.html',
}


@pytest.fixture
def publishing_app():
    app = Flask(__name__, template_folder=str(ROOT / 'templates'),
                static_folder=str(ROOT / 'static'))
    app.config['TESTING'] = True
    configure_publishing(app)

    @app.context_processor
    def site_meta():
        return dict(SITE_URL='https://burnsky-api.onrender.com', CURRENT_YEAR=2026,
                    GITHUB_REPO_URL='https://github.com/lomoreholic/burnsky-api',
                    CONTACT_EMAIL='')

    for path, template in TEMPLATES.items():
        app.add_url_rule(path, path, lambda name=template: render_template(name))
    for path in UTILITY_PATHS - TEMPLATES.keys():
        app.add_url_rule(path, path, lambda: 'Utility page')
    return app


@pytest.mark.parametrize('path', TEMPLATES)
def test_review_mode_preserves_verification_without_ads(publishing_app, monkeypatch, path):
    monkeypatch.delenv('ADSENSE_ENABLED', raising=False)
    response = publishing_app.test_client().get(path)
    html = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'name="google-adsense-account"' in html
    assert 'pagead2.googlesyndication.com' not in html
    assert '<ins class="adsbygoogle"' not in html


@pytest.mark.parametrize('path', TEMPLATES)
def test_enabled_ads_only_load_on_editorial_pages(publishing_app, monkeypatch, path):
    monkeypatch.setenv('ADSENSE_ENABLED', 'true')
    html = publishing_app.test_client().get(path).get_data(as_text=True)
    assert ('pagead2.googlesyndication.com' in html) == (path in AD_CONTENT_PATHS)


@pytest.mark.parametrize('path', sorted(UTILITY_PATHS | {'/api/data', '/predict', '/missing'}))
def test_utility_and_error_responses_are_noindex(publishing_app, path):
    response = publishing_app.test_client().get(path)
    assert response.headers['X-Robots-Tag'] == 'noindex'


def test_editorial_pages_remain_indexable(publishing_app):
    for path in AD_CONTENT_PATHS:
        assert 'X-Robots-Tag' not in publishing_app.test_client().get(path).headers


def test_sitemap_only_lists_existing_content_routes():
    routes = set()
    for source in (ROOT / 'app.py', ROOT / 'modules/history.py'):
        for node in ast.walk(ast.parse(source.read_text(encoding='utf-8'))):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'route' and node.args
                    and isinstance(node.args[0], ast.Constant)):
                routes.add(node.args[0].value)
    tree = ET.parse(ROOT / 'static/sitemap.xml')
    locations = [node.text for node in tree.findall('.//{*}loc')]
    assert len(locations) == len(set(locations))
    for url in locations:
        path = url.removeprefix('https://burnsky-api.onrender.com')
        assert path in routes
        assert path not in UTILITY_PATHS
        assert path != '/robots.txt'
    assert 'https://burnsky-api.onrender.com/prediction-history' in locations


def test_homepage_structured_data_matches_service(publishing_app):
    html = publishing_app.test_client().get('/').get_data(as_text=True)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    assert blocks
    types = {json.loads(block)['@type'] for block in blocks}
    assert 'WebApplication' in types
    assert types <= {'WebApplication', 'BreadcrumbList'}
