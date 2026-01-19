"""
pytest 配置和共用 fixtures
"""
import os
import sys
import pytest
from pathlib import Path

# 添加項目根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設置測試環境變量
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'
os.environ['RATE_LIMIT_ENABLED'] = 'false'  # 測試時禁用速率限制
os.environ['CACHE_TYPE'] = 'null'  # 測試時禁用Flask-Caching快取

from app import app as flask_app


@pytest.fixture
def app():
    """創建 Flask 應用 fixture"""
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'RATELIMIT_ENABLED': False,
    })
    yield flask_app


@pytest.fixture
def client(app):
    """創建測試客戶端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """創建 CLI runner"""
    return app.test_cli_runner()
