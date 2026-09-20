# cache.py - 快取管理模塊

from datetime import datetime, timedelta
from .config import CACHE_DURATION

# 簡單的快取機制
cache = {}

def get_cached_data(key, fetch_function, *args):
    """獲取快取數據，如果過期則重新獲取"""
    current_time = datetime.now()

    # 檢查快取是否存在且未過期
    if key in cache:
        cached_time, cached_data = cache[key]
        if current_time - cached_time < timedelta(seconds=CACHE_DURATION):
            print(f"✅ 使用快取: {key}")
            return cached_data
        else:
            print(f"🔄 快取過期: {key}")

    # 重新獲取數據
    print(f"🔄 重新獲取: {key}")
    try:
        data = fetch_function(*args)
        cache[key] = (current_time, data)
        return data
    except Exception as e:
        print(f"⚠️ 獲取數據失敗: {key} - {e}")
        # 如果獲取失敗，返回舊的快取數據（如果存在）
        if key in cache:
            print(f"⚠️ 返回過期快取數據: {key}")
            return cache[key][1]
        raise e

def clear_prediction_cache():
    """清除預測相關的快取"""
    keys_to_remove = []
    for key in cache.keys():
        if any(keyword in key.lower() for keyword in ['prediction', 'burnsky', 'sunrise', 'sunset']):
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del cache[key]

    print(f"🧹 已清除 {len(keys_to_remove)} 個預測快取項目")
    return len(keys_to_remove)

def trigger_prediction_update():
    """觸發預測更新，清除所有預測快取"""
    cleared_count = clear_prediction_cache()
    print(f"🔄 預測更新已觸發，清除了 {cleared_count} 個快取項目")
    return cleared_count
