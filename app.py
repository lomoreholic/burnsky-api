from flask import Flask, jsonify, render_template, request
from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast
from predictor import calculate_burnsky_score
import numpy as np

app = Flask(__name__)

def convert_numpy_types(obj):
    """遞歸轉換 numpy 類型為 Python 原生類型以支援 JSON 序列化"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

@app.route("/")
def home():
    """主頁 - 燒天預測前端"""
    return render_template('index.html')
@app.route("/predict", methods=["GET"])
def predict_burnsky():
    # 獲取查詢參數
    prediction_type = request.args.get('type', 'sunset')  # sunset 或 sunrise
    advance_hours = int(request.args.get('advance', 0))   # 提前預測小時數
    
    weather_data = fetch_weather_data()
    forecast_data = fetch_forecast_data()
    ninday_data = fetch_ninday_forecast()
    
    # 使用新的進階預測功能
    if prediction_type in ['sunrise', 'sunset'] and 0 <= advance_hours <= 24:
        from predictor import calculate_burnsky_score_advanced
        score, details, intensity, colors = calculate_burnsky_score_advanced(
            weather_data, forecast_data, ninday_data, prediction_type, advance_hours
        )
    else:
        # 回退到原始預測
        score, details = calculate_burnsky_score(weather_data, forecast_data, ninday_data)
        intensity = None
        colors = None

    result = {
        "burnsky_score": score,
        "probability": f"{round(min(score, 100))}%",
        "prediction_level": get_prediction_level(score),
        "prediction_type": prediction_type,
        "advance_hours": advance_hours,
        "analysis_details": details,
        "weather_data": weather_data,
        "forecast_data": forecast_data
    }
    
    # 添加燒天程度和顏色預測
    if intensity:
        result["intensity_prediction"] = intensity
    if colors:
        result["color_prediction"] = colors
    
    # 轉換 numpy 類型避免 JSON 序列化錯誤
    result = convert_numpy_types(result)
    
    return jsonify(result)

@app.route("/predict/sunrise", methods=["GET"])
def predict_sunrise():
    """專門的日出燒天預測端點"""
    advance_hours = int(request.args.get('advance_hours', 2))  # 預設提前2小時
    
    weather_data = fetch_weather_data()
    forecast_data = fetch_forecast_data()
    ninday_data = fetch_ninday_forecast()
    
    from predictor import calculate_burnsky_score_advanced
    score, details, intensity, colors = calculate_burnsky_score_advanced(
        weather_data, forecast_data, ninday_data, 'sunrise', advance_hours
    )

    result = {
        "burnsky_score": score,
        "probability": f"{round(min(score, 100))}%",
        "prediction_level": get_prediction_level(score),
        "prediction_type": "sunrise",
        "advance_hours": advance_hours,
        "analysis_details": details,
        "intensity_prediction": intensity,
        "color_prediction": colors,
        "weather_data": weather_data,
        "forecast_data": forecast_data
    }
    
    result = convert_numpy_types(result)
    return jsonify(result)

@app.route("/predict/sunset", methods=["GET"])
def predict_sunset():
    """專門的日落燒天預測端點"""
    advance_hours = int(request.args.get('advance_hours', 2))  # 預設提前2小時
    
    weather_data = fetch_weather_data()
    forecast_data = fetch_forecast_data()
    ninday_data = fetch_ninday_forecast()
    
    from predictor import calculate_burnsky_score_advanced
    score, details, intensity, colors = calculate_burnsky_score_advanced(
        weather_data, forecast_data, ninday_data, 'sunset', advance_hours
    )

    result = {
        "burnsky_score": score,
        "probability": f"{round(min(score, 100))}%",
        "prediction_level": get_prediction_level(score),
        "prediction_type": "sunset",
        "advance_hours": advance_hours,
        "analysis_details": details,
        "intensity_prediction": intensity,
        "color_prediction": colors,
        "weather_data": weather_data,
        "forecast_data": forecast_data
    }
    
    result = convert_numpy_types(result)
    return jsonify(result)

def get_prediction_level(score):
    """根據分數返回預測等級"""
    if score >= 80:
        return "極高機率燒天 🔥"
    elif score >= 70:
        return "高機率燒天 🌅"
    elif score >= 50:
        return "中等機率燒天 ⛅"
    elif score >= 30:
        return "低機率燒天 🌤️"
    else:
        return "不適宜燒天 ☁️"

@app.route("/api")
def api_docs():
    """API 說明頁面"""
    return """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>燒天預測 API 文檔</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px; }
            .method { background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 0.9em; }
            code { background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🔥 燒天預測 API</h1>
        <p>基於香港天文台即時數據的燒天機率預測服務</p>
        
        <div class="endpoint">
            <h3><span class="method">GET</span> /predict</h3>
            <p><strong>功能:</strong> 獲取當前燒天預測結果</p>
            <p><strong>回應格式:</strong></p>
            <pre><code>{
  "burnsky_score": 75.5,
  "probability": "75.5%", 
  "prediction_level": "高機率燒天 🌅",
  "analysis_details": {
    "total_score": 75.5,
    "temperature_factor": {...},
    "humidity_factor": {...},
    "time_factor": {...},
    "cloud_analysis_factor": {...},
    "uv_factor": {...},
    "visibility_factor": {...},
    "ml_prediction": {...},
    "score_breakdown": {...},
    "analysis_summary": [...]
  },
  "weather_data": {...},
  "forecast_data": {...}
}</code></pre>
        </div>
        
        <h3>🎯 預測等級說明</h3>
        <ul>
            <li><strong>80+ 分:</strong> 極高機率燒天 🔥</li>
            <li><strong>70-79 分:</strong> 高機率燒天 🌅</li>
            <li><strong>50-69 分:</strong> 中等機率燒天 ⛅</li>
            <li><strong>30-49 分:</strong> 低機率燒天 🌤️</li>
            <li><strong>30 分以下:</strong> 不適宜燒天 ☁️</li>
        </ul>
        
        <h3>📊 分析因子</h3>
        <ul>
            <li><strong>溫度因子:</strong> 基於當前溫度 (最佳範圍 25-35°C)</li>
            <li><strong>濕度因子:</strong> 基於相對濕度 (最佳範圍 50-80%)</li>
            <li><strong>時間因子:</strong> 基於與日落時間的關係</li>
            <li><strong>雲層因子:</strong> 基於天氣預報描述的雲層分析</li>
            <li><strong>UV 指數:</strong> 紫外線強度指標</li>
            <li><strong>能見度:</strong> 基於降雨和天氣警告</li>
            <li><strong>AI 預測:</strong> 機器學習模型綜合分析</li>
        </ul>
        
        <p><a href="/">← 返回主頁</a></p>
    </body>
    </html>
    """

@app.route("/test")
def test():
    """測試路由"""
    return "Flask 正常運作！免責聲明測試"

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
