# scheduler.py - 調度器模塊

import schedule
import threading
import time
from datetime import datetime
from .database import save_prediction_to_history
from .cache import clear_prediction_cache

def auto_save_current_predictions():
    """自動保存當前預測到歷史數據庫"""
    try:
        from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast, get_current_wind_data, fetch_warning_data
        from unified_scorer import calculate_burnsky_score_unified
        from forecast_extractor import forecast_extractor
        from .cache import get_cached_data

        print("🕐 開始自動保存每小時預測...")

        # 獲取天氣數據
        weather_data = get_cached_data('weather', fetch_weather_data)
        forecast_data = get_cached_data('forecast', fetch_forecast_data)
        ninday_data = get_cached_data('ninday', fetch_ninday_forecast)
        wind_data = get_cached_data('wind', get_current_wind_data)
        warning_data = get_cached_data('warning', fetch_warning_data)

        # 將風速數據加入天氣數據中
        weather_data['wind'] = wind_data
        # 將警告數據加入天氣數據
        weather_data['warnings'] = warning_data

        # 保存即時預測
        for prediction_type in ['sunrise', 'sunset']:
            try:
                # 使用統一計分系統
                unified_result = calculate_burnsky_score_unified(
                    weather_data, forecast_data, ninday_data, prediction_type, 0
                )
                score = unified_result['final_score']

                # 保存到歷史數據庫
                save_prediction_to_history(
                    prediction_type=prediction_type,
                    advance_hours=0,
                    score=score,
                    factors=unified_result.get('factor_scores', {}),
                    weather_data=weather_data,
                    warnings=warning_data
                )

            except Exception as e:
                print(f"⚠️ 保存{prediction_type}預測失敗: {e}")

        # 保存提前預測（1, 2, 3, 6, 12小時）
        for advance_hours in [1, 2, 3, 6, 12]:
            for prediction_type in ['sunrise', 'sunset']:
                try:
                    # 使用未來天氣數據
                    future_weather_data = forecast_extractor.extract_future_weather_data(
                        weather_data, forecast_data, ninday_data, advance_hours
                    )
                    # 將風速數據加入未來天氣數據中
                    future_weather_data['wind'] = wind_data
                    # 提前預測時無法預知未來警告，使用當前警告作參考
                    future_weather_data['warnings'] = warning_data

                    # 使用統一計分系統
                    unified_result = calculate_burnsky_score_unified(
                        future_weather_data, forecast_data, ninday_data, prediction_type, advance_hours
                    )
                    score = unified_result['final_score']

                    # 保存到歷史數據庫
                    save_prediction_to_history(
                        prediction_type=prediction_type,
                        advance_hours=advance_hours,
                        score=score,
                        factors=unified_result.get('factor_scores', {}),
                        weather_data=future_weather_data,
                        warnings=warning_data
                    )

                except Exception as e:
                    print(f"⚠️ 保存{prediction_type} {advance_hours}小時預測失敗: {e}")

        print("✅ 每小時預測保存完成")

    except Exception as e:
        print(f"⚠️ 自動保存預測失敗: {e}")

def start_hourly_scheduler():
    """啟動每小時調度器"""
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次

    # 設定每小時執行一次
    schedule.every().hour.at(":00").do(auto_save_current_predictions)

    # 啟動調度器線程
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    print("⏰ 每小時預測保存調度器已啟動")
