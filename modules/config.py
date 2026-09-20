# config.py - 應用配置和全局變數

import os
from datetime import datetime

# 快取機制
CACHE_DURATION = 300  # 快取5分鐘

# 照片案例學習系統
BURNSKY_PHOTO_CASES = {}
LAST_CASE_UPDATE = None  # 記錄最後一次案例更新時間

# 即時攝影機監控系統
webcam_monitor = None  # 將在 app.py 中初始化

# 上傳配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
AUTO_SAVE_PHOTOS = False  # 預設不自動儲存照片
PHOTO_RETENTION_DAYS = 30  # 照片保留30天

# 預測歷史數據庫配置
PREDICTION_HISTORY_DB = 'prediction_history.db'
HOURLY_SAVE_ENABLED = True  # 啟用每小時自動保存

# 確保上傳目錄存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 警告分析系統
warning_analysis_available = False
warning_analyzer = None
warning_collector = None
