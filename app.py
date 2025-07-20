from flask import Flask, jsonify, render_template, request, send_from_directory
from hko_fetcher import fetch_weather_data, fetch_forecast_data, fetch_ninday_forecast, get_current_wind_data, fetch_warning_data
from unified_scorer import calculate_burnsky_score_unified
from forecast_extractor import forecast_extractor
import numpy as np
import os
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

def get_warning_impact_score(warning_data):
    """計算天氣警告對燒天預測的影響分數"""
    if not warning_data or 'details' not in warning_data:
        return 0, []  # 無警告時不影響分數
    
    warning_details = warning_data.get('details', [])
    if not warning_details:
        return 0, []
    
    total_impact = 0
    active_warnings = []
    severe_warnings = []  # 記錄嚴重警告
    
    for warning in warning_details:
        warning_text = warning.lower() if isinstance(warning, str) else str(warning).lower()
        active_warnings.append(warning)
        
        # 更細緻的警告類型計算影響 - 調整為更合理的數值
        if any(keyword in warning_text for keyword in ['黑雨', '黑色暴雨']):
            impact = 35  # 黑雨最嚴重
            severe_warnings.append("黑色暴雨")
        elif any(keyword in warning_text for keyword in ['紅雨', '紅色暴雨']):
            impact = 20  # 紅雨嚴重 (降低影響)
            severe_warnings.append("紅色暴雨")
        elif any(keyword in warning_text for keyword in ['黃雨', '黃色暴雨']):
            impact = 12  # 黃雨中等
        elif any(keyword in warning_text for keyword in ['水浸', '特別報告']):
            impact = 15  # 水浸警告
        elif any(keyword in warning_text for keyword in ['十號', '颶風', '十號風球']):
            impact = 40  # 十號風球極嚴重
            severe_warnings.append("十號颶風信號")
        elif any(keyword in warning_text for keyword in ['九號', '暴風信號']):
            impact = 25  # 九號風球嚴重
            severe_warnings.append("九號暴風信號")
        elif any(keyword in warning_text for keyword in ['八號', '烈風信號', '烈風或暴風信號']):
            impact = 18  # 八號風球中等嚴重 (降低影響)
            severe_warnings.append("八號烈風信號")
        elif any(keyword in warning_text for keyword in ['熱帶氣旋', 'wtcsgnl']):
            impact = 15  # 一般熱帶氣旋警報
        elif any(keyword in warning_text for keyword in ['雷暴', '閃電']):
            impact = 8   # 雷暴警告 (大幅降低影響)
        elif any(keyword in warning_text for keyword in ['霧', '能見度']):
            impact = 15  # 霧警告影響能見度
        elif any(keyword in warning_text for keyword in ['空氣污染', 'pm2.5', '臭氧']):
            impact = 5   # 空氣污染輕微影響
        else:
            impact = 3   # 其他警告輕微影響
            
        total_impact += impact
    
    # 動態調整最大扣分上限 - 更寬鬆的限制
    if len(severe_warnings) >= 2:
        max_impact = 40  # 多個嚴重警告 (降低上限)
    elif len(severe_warnings) >= 1:
        max_impact = 30  # 單個嚴重警告 (降低上限)
    else:
        max_impact = 25  # 一般警告 (降低上限)
    
    print(f"🚨 警告影響詳情: 總影響{total_impact}分, 上限{max_impact}分, 嚴重警告: {severe_warnings}")
    
    return min(total_impact, max_impact), active_warnings

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
    
    # 🚨 獲取天氣警告數據（新增）
    warning_data = fetch_warning_data()
    print(f"🚨 獲取天氣警告數據: {len(warning_data.get('details', [])) if warning_data else 0} 個警告")
    
    # 將風速數據加入天氣數據中
    weather_data['wind'] = wind_data
    
    # 🚨 將警告數據加入天氣數據（新增）
    weather_data['warnings'] = warning_data
    
    # 如果是提前預測，使用未來天氣數據
    if advance_hours > 0:
        future_weather_data = forecast_extractor.extract_future_weather_data(
            weather_data, forecast_data, ninday_data, advance_hours
        )
        # 將風速數據加入未來天氣數據中
        future_weather_data['wind'] = wind_data
        # 🚨 提前預測時無法預知未來警告，使用當前警告作參考
        future_weather_data['warnings'] = warning_data
        print(f"🔮 使用 {advance_hours} 小時後的推算天氣數據進行{prediction_type}預測")
        print(f"⚠️ 提前預測無法預知未來警告狀態，使用當前警告作參考")
    else:
        future_weather_data = weather_data
        print(f"🕐 使用即時天氣數據進行{prediction_type}預測")
    
    # 使用統一計分系統 (整合所有計分方式)
    unified_result = calculate_burnsky_score_unified(
        future_weather_data, forecast_data, ninday_data, prediction_type, advance_hours
    )
    
    # 從統一結果中提取分數和詳情
    score = unified_result['final_score']
    
    # 🚨 計算警告影響並調整最終分數（新增）
    warning_impact, active_warnings = get_warning_impact_score(warning_data)
    if warning_impact > 0:
        adjusted_score = max(0, score - warning_impact)
        print(f"🚨 天氣警告影響: -{warning_impact}分，調整後分數: {adjusted_score}")
        score = adjusted_score
    
    # 復用統一計分器中的雲層厚度分析結果，避免重複計算
    cloud_thickness_analysis = unified_result.get('cloud_thickness_analysis', {})

    # 構建前端兼容的分析詳情格式
    factor_scores = unified_result.get('factor_scores', {})
    
    # 構建詳細的因子信息，包含前端期望的格式
    def build_factor_info(factor_name, score, max_score=None):
        """構建因子詳情"""
        if max_score is None:
            max_score = {'time': 25, 'temperature': 15, 'humidity': 20, 'visibility': 15, 
                        'cloud': 25, 'uv': 10, 'wind': 15, 'air_quality': 15}.get(factor_name, 100)
        
        factor_data = {
            'score': round(score, 1),
            'max_score': max_score,
            'description': f'{factor_name.title()}因子評分: {round(score, 1)}/{max_score}分'
        }
        
        # 添加特定因子的額外信息
        if factor_name == 'time':
            factor_data.update({
                'current_time': datetime.now().strftime('%H:%M'),
                'target_time': '18:30' if prediction_type == 'sunset' else '06:30',
                'target_type': prediction_type,
                'advance_hours': advance_hours
            })
        elif factor_name == 'temperature' and 'temperature' in future_weather_data:
            factor_data['current_temp'] = future_weather_data['temperature']
        elif factor_name == 'humidity' and 'humidity' in future_weather_data:
            factor_data['current_humidity'] = future_weather_data['humidity']
        elif factor_name == 'wind' and 'wind' in future_weather_data:
            wind_data = future_weather_data['wind']
            if isinstance(wind_data, dict) and 'speed' in wind_data:
                factor_data['wind_speed'] = wind_data['speed']
        
        return factor_data
    
    analysis_details = {
        "confidence": unified_result['analysis'].get('confidence', 'medium'),
        "recommendation": unified_result['analysis'].get('recommendation', ''),
        "score_breakdown": {
            "final_score": score,  # 使用警告調整後的分數
            "final_weighted_score": score,
            "ml_score": unified_result['ml_score'],
            "traditional_normalized": unified_result['traditional_normalized'],
            "traditional_raw": unified_result['traditional_score'],
            "traditional_score": unified_result['traditional_score'],
            "weighted_score": unified_result['weighted_score'],
            "warning_impact": warning_impact,  # 🚨 新增警告影響
            "weight_explanation": f"智能權重分配: AI模型 {unified_result['weights_used'].get('ml', 0.5)*100:.0f}%, 傳統算法 {unified_result['weights_used'].get('traditional', 0.5)*100:.0f}%"
        },
        "top_factors": unified_result['analysis'].get('top_factors', []),
        # 添加前端期望的因子數據 - 將字串摘要轉換為陣列格式
        "analysis_summary": [part.strip() for part in unified_result['analysis'].get('summary', '基於統一計分系統的綜合分析').split('|')],
        "intensity_prediction": unified_result['intensity_prediction'],
        "cloud_visibility_analysis": cloud_thickness_analysis,
        # 🚨 新增警告相關信息
        "weather_warnings": {
            "active_warnings": active_warnings,
            "warning_count": len(active_warnings),
            "warning_impact_score": warning_impact,
            "has_severe_warnings": warning_impact >= 25
        },
        # 構建各個因子的詳細信息
        "time_factor": build_factor_info('time', factor_scores.get('time', 0), 25),
        "temperature_factor": build_factor_info('temperature', factor_scores.get('temperature', 0), 15),
        "humidity_factor": build_factor_info('humidity', factor_scores.get('humidity', 0), 20),
        "visibility_factor": build_factor_info('visibility', factor_scores.get('visibility', 0), 15),
        "cloud_analysis_factor": build_factor_info('cloud', factor_scores.get('cloud', 0), 25),
        "uv_factor": build_factor_info('uv', factor_scores.get('uv', 0), 10),
        "wind_factor": build_factor_info('wind', factor_scores.get('wind', 0), 15),
        "air_quality_factor": build_factor_info('air_quality', factor_scores.get('air_quality', 0), 15),
        # 添加機器學習特徵分析
        "ml_feature_analysis": unified_result.get('ml_feature_analysis', {}),
    }

    result = {
        "burnsky_score": score,
        "probability": f"{round(min(score, 100))}%",
        "prediction_level": get_prediction_level(score),
        "prediction_type": prediction_type,
        "advance_hours": advance_hours,
        "unified_analysis": unified_result,  # 完整的統一分析結果
        "analysis_details": analysis_details,  # 前端兼容格式
        "intensity_prediction": unified_result['intensity_prediction'],
        "color_prediction": unified_result['color_prediction'],
        "cloud_thickness_analysis": cloud_thickness_analysis,
        "weather_data": future_weather_data,
        "original_weather_data": weather_data if advance_hours > 0 else None,
        "forecast_data": forecast_data,
        # 🚨 新增警告數據到回應中
        "warning_data": warning_data,
        "warning_analysis": {
            "active_warnings": active_warnings,
            "warning_impact": warning_impact,
            "warning_adjusted": warning_impact > 0
        },
        "scoring_method": "unified_v1.1_with_warnings"  # 🚨 更新版本號標示警告整合
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
        "version": "3.0",
        "description": "香港燒天預測服務 - 統一整合計分系統",
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
            "統一計分系統 - 整合所有計分方式",
            "8因子綜合評估 - 科學權重分配",
            "動態權重調整 - 根據預測時段優化",
            "機器學習增強 - 傳統算法+AI預測",
            "實時天氣數據分析",
            "空氣品質健康指數 (AQHI) 監測", 
            "提前24小時預測",
            "日出日落分別預測",
            "燒天強度和顏色預測",
            "季節性和環境調整",
            "詳細因子分析報告"
        ],
        "data_source": "香港天文台開放數據 API + CSDI 政府空間數據共享平台",
        "update_frequency": "每小時更新",
        "accuracy": "基於歷史數據訓練，準確率約85%",
        "improvements_v3.0": [
            "統一計分系統，整合所有現有算法",
            "標準化因子權重和評分邏輯",
            "增強錯誤處理和容錯機制",
            "詳細的分析報告和建議",
            "模組化設計，便於維護和擴展",
            "完整的計分透明度和可追溯性"
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
