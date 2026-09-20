# file_handler.py - 文件處理模塊

import os
import time
import io
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from PIL import Image
from .config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_FILE_SIZE, PHOTO_RETENTION_DAYS

def allowed_file(filename):
    """檢查文件類型是否被允許"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_content(image_data):
    """驗證圖片內容是否有效"""
    try:
        # 嘗試打開圖片
        image = Image.open(io.BytesIO(image_data))
        image.verify()  # 驗證圖片完整性
        return True
    except Exception:
        return False

def cleanup_old_photos():
    """清理舊照片文件"""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            return

        cutoff_time = time.time() - (PHOTO_RETENTION_DAYS * 24 * 60 * 60)
        deleted_count = 0

        for filename in os.listdir(UPLOAD_FOLDER):
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except OSError as e:
                    print(f"清理檔案失敗: {filename} - {e}")

        if deleted_count > 0:
            print(f"🧹 已清理 {deleted_count} 個舊照片檔案")

    except Exception as e:
        print(f"⚠️ 清理舊照片失敗: {e}")

def save_uploaded_photo(photo_data, filename):
    """保存上傳的照片"""
    try:
        # 生成安全檔名
        safe_filename = secure_filename(filename)
        if not safe_filename:
            safe_filename = "photo.jpg"

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{safe_filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # 儲存檔案
        with open(file_path, 'wb') as f:
            f.write(photo_data)

        print(f"📁 照片已儲存: {filename}")
        return file_path

    except Exception as e:
        print(f"⚠️ 照片儲存失敗: {e}")
        return None

def get_photo_storage_info():
    """獲取照片儲存資訊"""
    try:
        total_files = 0
        total_size = 0
        files_info = []

        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    file_time = os.path.getmtime(file_path)

                    files_info.append({
                        'filename': filename,
                        'size': file_size,
                        'created': datetime.fromtimestamp(file_time).isoformat(),
                        'age_days': (time.time() - file_time) / (24 * 60 * 60)
                    })

                    total_files += 1
                    total_size += file_size

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024*1024), 2),
            "files": files_info
        }

    except Exception as e:
        print(f"⚠️ 獲取照片儲存資訊失敗: {e}")
        return {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "files": []
        }
