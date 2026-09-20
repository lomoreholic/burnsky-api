"""Background scheduling for persisted burnsky predictions."""

import os
import threading
import time

import schedule


class HourlyPredictionScheduler:
    """Run persisted predictions without coupling scheduler code to Flask globals."""

    def __init__(self, predict, save_prediction, clear_cache, enabled=True, sleep=time.sleep):
        self._predict = predict
        self._save_prediction = save_prediction
        self._clear_cache = clear_cache
        self._enabled = enabled
        self._sleep = sleep
        self._started = False
        self._lock = threading.Lock()

    def save_current_predictions(self):
        """Refresh cached inputs and persist the supported prediction horizons."""
        try:
            print('🕐 開始自動保存每小時預測...')
            self._clear_cache()
            for prediction_type in ('sunset', 'sunrise'):
                for advance_hours in (0, 1, 2, 3, 6, 12):
                    try:
                        result = self._predict(prediction_type, advance_hours)
                        if result and result.get('burnsky_score') is not None:
                            self._save_prediction(
                                prediction_type,
                                advance_hours,
                                result['burnsky_score'],
                                result.get('analysis_details', {}),
                                result.get('weather_data', {}),
                                result.get('warning_data', {})
                            )
                        self._sleep(0.5)
                    except Exception as error:
                        print(f'❌ 保存 {prediction_type} (提前{advance_hours}小時) 失敗: {error}')
            print('✅ 每小時預測保存完成')
        except Exception as error:
            print(f'❌ 自動保存預測失敗: {error}')

    def start(self):
        """Start one daemon scheduler outside the Flask debug reloader parent."""
        if not self._enabled:
            return False
        if (
            os.getenv('FLASK_DEBUG', os.getenv('FLASK_ENV', 'development')) == 'development'
            and os.getenv('WERKZEUG_RUN_MAIN') != 'true'
        ):
            print('⏭️ Debug reloader 父程序不啟動排程')
            return False

        with self._lock:
            if self._started:
                print('⏭️ 每小時預測保存排程已啟動，略過重複初始化')
                return False
            self._started = True

        schedule.every().hour.at(':05').do(self.save_current_predictions)
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        print('⏰ 每小時預測保存排程已啟動')
        return True

    @staticmethod
    def _run():
        while True:
            schedule.run_pending()
            time.sleep(60)