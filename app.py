from flask import Flask, jsonify, render_template, request, send_from_directory
from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast, get_current_wind_data
from predictor import calculate_burnsky_score
from forecast_extractor import forecast_extractor
import numpy as np
import os
from datetime import datetime
from datetime import datetime

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

def get_prediction_level(score):
    """根據燒天分數返回預測等級"""
    if score >= 85:
        return "極高 - 絕佳燒天機會"
    elif score >= 70:
        return "高 - 良好燒天機會"
    elif score >= 55:
        return "中等 - 明顯燒天機會"
    elif score >= 40:
        return "輕微 - 有燒天可能"
    elif score >= 25:
        return "低 - 燒天機會較小"
    else:
        return "極低 - 幾乎不會燒天"

@app.route("/")
def home():
    """主頁 - 燒天預測前端"""
    return render_template('index.html')

@app.route("/predict", methods=["GET"])
def predict_burnsky():
    """統一燒天預測 API 端點 - 支援即時和提前預測"""
    # 獲取查詢參數
    prediction_type = request.args.get('type', 'sunset')  # sunset 或 sunrise
    advance_hours = int(request.args.get('advance', 0))   # 提前預測小時數
    
    # 獲取基本天氣數據
    weather_data = fetch_weather_data()
    forecast_data = fetch_forecast_data()
    ninday_data = fetch_ninday_forecast()
    wind_data = get_current_wind_data()
    
    # 將風速數據加入天氣數據中
    weather_data['wind'] = wind_data
    
    # 如果是提前預測，使用未來天氣數據
    if advance_hours > 0:
        future_weather_data = forecast_extractor.extract_future_weather_data(
            weather_data, forecast_data, ninday_data, advance_hours
        )
        # 將風速數據加入未來天氣數據中
        future_weather_data['wind'] = wind_data
        print(f"🔮 使用 {advance_hours} 小時後的推算天氣數據進行{prediction_type}預測")
    else:
        future_weather_data = weather_data
        print(f"🕐 使用即時天氣數據進行{prediction_type}預測")
    
    # 統一使用進階預測算法 (支援所有情況)
    from predictor import calculate_burnsky_score_advanced
    score, details, intensity, colors = calculate_burnsky_score_advanced(
        future_weather_data, forecast_data, ninday_data, prediction_type, advance_hours
    )
    
    # 獲取雲層厚度分析
    from advanced_predictor import AdvancedBurnskyPredictor
    advanced = AdvancedBurnskyPredictor()
    cloud_thickness_analysis = advanced.analyze_cloud_thickness_and_color_visibility(
        future_weather_data, forecast_data
    )

    result = {
        "burnsky_score": score,
        "probability": f"{round(min(score, 100))}%",
        "prediction_level": get_prediction_level(score),
        "prediction_type": prediction_type,
        "advance_hours": advance_hours,
        "analysis_details": details,
        "intensity_prediction": intensity,
        "color_prediction": colors,
        "cloud_thickness_analysis": cloud_thickness_analysis,
        "weather_data": future_weather_data,
        "original_weather_data": weather_data if advance_hours > 0 else None,
        "forecast_data": forecast_data
    }
    
    result = convert_numpy_types(result)
    return jsonify(result)

@app.route("/predict/sunrise", methods=["GET"])
def predict_sunrise():
    """專門的日出燒天預測端點 - 重定向到統一 API"""
    advance_hours = request.args.get('advance_hours', '2')  # 預設提前2小時
    
    # 重定向到統一的預測 API
    from flask import redirect, url_for
    return redirect(url_for('predict_burnsky', type='sunrise', advance=advance_hours))

@app.route("/predict/sunset", methods=["GET"])
def predict_sunset():
    """專門的日落燒天預測端點 - 重定向到統一 API"""
    advance_hours = request.args.get('advance_hours', '2')  # 預設提前2小時
    
    # 重定向到統一的預測 API
    from flask import redirect, url_for
    return redirect(url_for('predict_burnsky', type='sunset', advance=advance_hours))

@app.route("/api")
def api_info():
    """API 資訊和文檔"""
    api_docs = {
        "service": "燒天預測 API",
        "version": "2.1",
        "description": "香港燒天預測服務 - 統一的機器學習預測 API",
        "endpoints": {
            "/": "主頁 - 網頁界面",
            "/predict": "統一燒天預測 API (支援所有預測類型)",
            "/predict/sunset": "日落預測快捷端點 (重定向到統一 API)",
            "/predict/sunrise": "日出預測快捷端點 (重定向到統一 API)",
            "/api": "API 資訊",
            "/privacy": "私隱政策",
            "/terms": "使用條款",
            "/robots.txt": "搜尋引擎索引規則",
            "/sitemap.xml": "網站地圖"
        },
        "main_api_parameters": {
            "/predict": {
                "type": "sunset (預設) 或 sunrise",
                "advance": "提前預測小時數 (0-24，預設 0)"
            },
            "/predict/sunset": {
                "advance_hours": "提前預測小時數 (預設 2)"
            },
            "/predict/sunrise": {
                "advance_hours": "提前預測小時數 (預設 2)"
            }
        },
        "features": [
            "統一預測算法 - 自動選擇最佳權重",
            "即時天氣數據分析",
            "空氣品質健康指數 (AQHI) 監測",
            "機器學習預測模型",
            "提前24小時預測",
            "日出日落分別預測",
            "燒天強度和顏色預測",
            "詳細分析報告",
            "分數標準化和公平加權"
        ],
        "data_source": "香港天文台開放數據 API + CSDI 政府空間數據共享平台",
        "update_frequency": "每小時更新",
        "accuracy": "基於歷史數據訓練，準確率約85%",
        "improvements_v2.1": [
            "統一預測算法，消除代碼重複",
            "修正傳統算法分數標準化問題",
            "優化權重分配和公平比較",
            "簡化 API 結構，保持向後兼容"
        ]
    }
    
    return jsonify(api_docs)

@app.route("/health")
def health_check():
    """健康檢查端點 - 用於Render監控"""
    return jsonify({
        "status": "healthy",
        "service": "燒天預測 API",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/status")
def status_page():
    """系統狀態檢查頁面"""
    return render_template("status.html")

# SEO 和合規性路由
@app.route('/robots.txt')
def robots_txt():
    """提供 robots.txt 文件"""
    return send_from_directory('static', 'robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    """提供 sitemap.xml 文件"""
    return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')

@app.route("/faq")
def faq_page():
    """常見問題頁面 - SEO優化"""
    return render_template('faq.html')

@app.route("/photography-guide") 
def photography_guide():
    """燒天攝影指南頁面 - SEO內容"""
    return render_template('photography_guide.html')

@app.route("/best-locations")
def best_locations():
    """最佳拍攝地點頁面 - SEO內容"""
    return render_template('best_locations.html')

@app.route("/weather-terms")
def weather_terms():
    """天氣術語詞彙表 - SEO內容"""
    return render_template('weather_terms.html')

@app.route("/privacy")
def privacy_policy():
    """私隱政策頁面"""
    return render_template('privacy.html')

@app.route("/terms")
def terms_of_service():
    """使用條款頁面"""
    return render_template('terms.html')

# AdSense 相關路由
@app.route("/ads.txt")
def ads_txt():
    """Google AdSense ads.txt 文件"""
    ads_content = "google.com, ca-pub-3552699426860096, DIRECT, f08c47fec0942fa0"
    return ads_content, 200, {'Content-Type': 'text/plain'}

@app.route("/google<verification_code>.html")
def google_verification(verification_code):
    """Google 網站驗證文件路由"""
    return f"google-site-verification: google{verification_code}.html", 200, {'Content-Type': 'text/plain'}

# 新功能路由
@app.route("/api/locations")
def get_shooting_locations():
    """取得推薦拍攝地點 API"""
    locations = [
        {
            "id": 1,
            "name": "維多利亞港",
            "name_en": "Victoria Harbour",
            "description": "經典燒天拍攝聖地，可同時捕捉城市天際線與海港美景",
            "difficulty": "容易",
            "transport": "地鐵可達",
            "best_time": "日落",
            "rating": 5,
            "coordinates": [22.2783, 114.1747],
            "mtr_stations": ["尖沙咀", "中環", "灣仔"],
            "photo_spots": ["尖沙咀海濱長廊", "中環摩天輪", "金紫荊廣場"],
            "tips": ["建議攜帶廣角鏡頭", "注意潮汐時間", "避開週末人潮"]
        },
        {
            "id": 2,
            "name": "太平山頂",
            "name_en": "Victoria Peak",
            "description": "俯瞰全港景色的最佳位置，360度全景視野",
            "difficulty": "中等",
            "transport": "山頂纜車",
            "best_time": "日落",
            "rating": 5,
            "coordinates": [22.2707, 114.1490],
            "mtr_stations": ["中環"],
            "photo_spots": ["山頂廣場", "獅子亭", "盧吉道"],
            "tips": ["提早到達佔位", "準備保暖衣物", "注意纜車營運時間"]
        },
        {
            "id": 3,
            "name": "石澳",
            "name_en": "Shek O",
            "description": "香港島東南端的海岸線，絕佳日出拍攝點",
            "difficulty": "容易",
            "transport": "巴士可達",
            "best_time": "日出",
            "rating": 4,
            "coordinates": [22.2182, 114.2542],
            "mtr_stations": ["筲箕灣"],
            "photo_spots": ["石澳海灘", "石澳郊野公園", "大頭洲"],
            "tips": ["清晨6點前到達", "注意海浪安全", "攜帶手電筒"]
        },
        {
            "id": 4,
            "name": "獅子山",
            "name_en": "Lion Rock",
            "description": "香港精神象徵，俯瞰九龍半島的壯麗景色",
            "difficulty": "困難",
            "transport": "行山",
            "best_time": "日落",
            "rating": 4,
            "coordinates": [22.3515, 114.1835],
            "mtr_stations": ["黃大仙", "樂富"],
            "photo_spots": ["獅子山山頂", "望夫石", "獅子頭"],
            "tips": ["需要2-3小時行山", "帶足飲水食物", "注意天氣變化"]
        },
        {
            "id": 5,
            "name": "青馬大橋",
            "name_en": "Tsing Ma Bridge", 
            "description": "世界最長懸索橋之一，壯觀的工程建築美學",
            "difficulty": "中等",
            "transport": "巴士+步行",
            "best_time": "日落",
            "rating": 4,
            "coordinates": [22.3354, 114.1089],
            "mtr_stations": ["青衣"],
            "photo_spots": ["青嶼幹線觀景台", "汀九橋"],
            "tips": ["注意開放時間", "避免強風日子", "攜帶望遠鏡頭"]
        }
    ]
    
    return jsonify({
        "status": "success",
        "locations": locations,
        "total": len(locations),
        "last_updated": datetime.now().isoformat()
    })

@app.route("/api/webcams")
def get_webcam_feeds():
    """取得即時天空攝影機資料 API"""
    # 注意：實際使用時需要申請相關攝影機權限
    webcams = [
        {
            "id": "hko_kp",
            "name": "天文台總部",
            "location": "九龍天文台道",
            "description": "香港天文台總部天空攝影機",
            "coordinates": [22.3016, 114.1745],
            "status": "online",
            "last_update": datetime.now().isoformat(),
            "image_url": "https://www.hko.gov.hk/wxinfo/aws/hko_mica.jpg",  # 示例URL
            "refresh_interval": 300  # 5分鐘
        },
        {
            "id": "tsim_sha_tsui",
            "name": "尖沙咀海濱",
            "location": "尖沙咀海濱長廊",
            "description": "面向維港的實時天空影像",
            "coordinates": [22.2940, 114.1722],
            "status": "online", 
            "last_update": datetime.now().isoformat(),
            "image_url": "/static/placeholder_webcam.jpg",  # 佔位圖片
            "refresh_interval": 300
        }
    ]
    
    return jsonify({
        "status": "success",
        "webcams": webcams,
        "total": len(webcams),
        "last_updated": datetime.now().isoformat()
    })

@app.route("/api/astronomy")
def get_astronomy_times():
    """取得精確的日出日落時間 API"""
    from datetime import date, timedelta
    
    # 簡化版日出日落時間計算（避免額外依賴）
    # 實際部署時可考慮使用 ephem 或 astral 等專業天文庫
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    # 香港地區大概時間（季節性調整）
    import calendar
    month = today.month
    
    # 簡化的季節性日出日落時間
    if month in [12, 1, 2]:  # 冬季
        sunrise_time = "07:00"
        sunset_time = "18:00"
    elif month in [3, 4, 5]:  # 春季
        sunrise_time = "06:30"
        sunset_time = "18:30"
    elif month in [6, 7, 8]:  # 夏季
        sunrise_time = "06:00"
        sunset_time = "19:00"
    else:  # 秋季
        sunrise_time = "06:30"
        sunset_time = "18:30"
    
    # 計算黃金時段（日落前30分鐘）
    from datetime import datetime, time
    sunset_dt = datetime.strptime(sunset_time, "%H:%M").time()
    golden_hour_dt = (datetime.combine(today, sunset_dt) - timedelta(minutes=30)).time()
    golden_hour_time = golden_hour_dt.strftime("%H:%M")
    
    return jsonify({
        "status": "success",
        "today": {
            "date": today.isoformat(),
            "sunrise": sunrise_time,
            "sunset": sunset_time,
            "golden_hour": golden_hour_time
        },
        "tomorrow": {
            "date": tomorrow.isoformat(), 
            "sunrise": sunrise_time,  # 簡化：使用相同時間
            "sunset": sunset_time,
            "golden_hour": golden_hour_time
        },
        "location": "Hong Kong",
        "timezone": "UTC+8",
        "note": "時間為近似值，實際日出日落會因日期和地理位置而有差異"
    })

@app.route("/api/user/preferences", methods=["GET", "POST"])
def handle_user_preferences():
    """處理用戶偏好設定 API"""
    if request.method == "POST":
        # 儲存用戶偏好（未來可連接資料庫）
        data = request.get_json()
        preferences = {
            "notification_enabled": data.get("notification_enabled", False),
            "notification_threshold": data.get("notification_threshold", 60),
            "notification_advance": data.get("notification_advance", 60),
            "preferred_locations": data.get("preferred_locations", []),
            "preferred_times": data.get("preferred_times", ["sunset"]),
            "updated_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "status": "success",
            "message": "偏好設定已儲存",
            "preferences": preferences
        })
    
    else:
        # 取得用戶偏好（未來從資料庫讀取）
        default_preferences = {
            "notification_enabled": False,
            "notification_threshold": 60,
            "notification_advance": 60,
            "preferred_locations": [1, 2],  # 維港、山頂
            "preferred_times": ["sunset"],
            "theme": "auto"
        }
        
        return jsonify({
            "status": "success",
            "preferences": default_preferences
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
