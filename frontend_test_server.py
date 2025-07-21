#!/usr/bin/env python3
"""
燒天預測系統前端測試服務器
集成警告歷史分析功能
"""

from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    """主頁面"""
    return render_template('index.html')

@app.route('/test')
def test():
    """測試頁面"""
    return render_template('test.html')

@app.route('/api/warnings/history')
def warning_history():
    """警告歷史數據 API"""
    return jsonify({
        "total_warnings": 127,
        "average_accuracy": 85.3,
        "best_category": "暴雨警告",
        "status": "success"
    })

@app.route('/api/warnings/timeline')
def warning_timeline():
    """警告時間軸圖表 API"""
    return jsonify({
        "chart_url": None,
        "data": "暫無時間軸數據",
        "status": "success"
    })

@app.route('/api/warnings/category-distribution')
def warning_category_distribution():
    """警告類別分布圖表 API"""
    return jsonify({
        "chart_url": None,
        "data": "暫無類別分布數據", 
        "status": "success"
    })

@app.route('/api/warnings/seasonal')
def warning_seasonal():
    """季節性警告趨勢 API"""
    return jsonify({
        "chart_url": None,
        "data": "暫無季節趨勢數據",
        "status": "success"
    })

@app.route('/api/warnings/accuracy')
def warning_accuracy():
    """警告準確度指標 API"""
    return jsonify({
        "overall_accuracy": 87.5,
        "timely_accuracy": 92.1,
        "improvement_trend": "+3.2%",
        "chart_url": None,
        "status": "success"
    })

@app.route('/api/warnings/insights')
def warning_insights():
    """警告智能分析 API"""
    return jsonify({
        "key_findings": [
            "暴雨警告預測準確度最高，達到92%",
            "下午2-6點是警告發布的高峰時段", 
            "夏季警告頻率比冬季高出60%"
        ],
        "statistical_summary": [
            "總共分析了127次警告事件",
            "平均提前2.3小時發出警告",
            "準確度呈上升趨勢"
        ],
        "recommendations": [
            "建議加強對午後對流天氣的監測",
            "優化夏季警告算法",
            "增加多模式集成預報"
        ],
        "status": "success"
    })

@app.route('/predict')
def predict():
    """簡單的預測 API（用於測試）"""
    return jsonify({
        "score": 85,
        "level": "高機率",
        "probability": "85%",
        "status": "success",
        "data": {
            "temperature": 28,
            "humidity": 75,
            "cloud_cover": 65
        }
    })

@app.route('/predict/sunset')
def predict_sunset():
    """日落燒天預測 API"""
    advance_hours = request.args.get('advance_hours', 2)
    return jsonify({
        "burnsky_score": 78,
        "score": 78,
        "prediction_level": "🌅 高機率",
        "level": "高機率",
        "probability": "78%",
        "prediction_type": "sunset",
        "advance_hours": int(advance_hours),
        "status": "success",
        "weather_data": {
            "temperature": 29,
            "humidity": 72,
            "cloud_cover": 60,
            "wind_speed": 12,
            "pressure": 1013,
            "visibility": 15,
            "uv_index": 2
        },
        "analysis_details": [
            {
                "factor": "雲層厚度",
                "score": 82,
                "description": "中等厚度雲層，透光性良好，有利於夕陽光線穿透",
                "impact": "positive"
            },
            {
                "factor": "大氣穩定度", 
                "score": 75,
                "description": "大氣層結構穩定，有利於雲層形態維持",
                "impact": "positive"
            },
            {
                "factor": "濕度條件",
                "score": 80,
                "description": "濕度適中，有助於雲層折射光線",
                "impact": "positive"
            },
            {
                "factor": "風速條件",
                "score": 73,
                "description": "風速溫和，雲層移動緩慢，有利於拍攝",
                "impact": "positive"
            }
        ],
        "analysis_summary": [
            "🌅 雲層厚度適中，有利於燒天形成",
            "🌡️ 溫度適宜，大氣穩定度良好", 
            "💨 風速溫和，雲層移動緩慢",
            "📊 綜合條件評估為高機率燒天"
        ],
        "viewing_guide": {
            "best_direction": "西南方",
            "best_time": "18:30-19:00",
            "camera_settings": "ISO 100-200, 光圈 f/8-11",
            "recommendation": "建議提前30分鐘到達拍攝地點"
        },
        "last_updated": "2025-07-21 10:30:00"
    })

@app.route('/predict/sunrise')
def predict_sunrise():
    """日出燒天預測 API"""
    advance_hours = request.args.get('advance_hours', 2)
    return jsonify({
        "burnsky_score": 72,
        "score": 72,
        "prediction_level": "🌄 中等機率",
        "level": "中等機率",
        "probability": "72%",
        "prediction_type": "sunrise",
        "advance_hours": int(advance_hours),
        "status": "success",
        "weather_data": {
            "temperature": 26,
            "humidity": 78,
            "cloud_cover": 55,
            "wind_speed": 8,
            "pressure": 1015,
            "visibility": 12,
            "uv_index": 1
        },
        "analysis_details": [
            {
                "factor": "雲層分布",
                "score": 75,
                "description": "雲層分布較為均勻，覆蓋面適中",
                "impact": "positive"
            },
            {
                "factor": "水汽條件",
                "score": 70,
                "description": "水汽充足，有利於雲層形成和光線散射",
                "impact": "positive"
            },
            {
                "factor": "能見度",
                "score": 68,
                "description": "能見度良好，有利於遠景拍攝",
                "impact": "positive"
            },
            {
                "factor": "溫度條件",
                "score": 74,
                "description": "夜間降溫適度，有利於水汽凝結",
                "impact": "positive"
            }
        ],
        "analysis_summary": [
            "🌄 晨間雲層分布較為均勻",
            "🌡️ 夜間降溫適度，有利於水汽凝結",
            "💨 微風輕拂，雲層變化緩慢",
            "📊 綜合條件評估為中等機率燒天"
        ],
        "viewing_guide": {
            "best_direction": "東南方",
            "best_time": "06:00-06:30",
            "camera_settings": "ISO 200-400, 光圈 f/5.6-8",
            "recommendation": "建議關注天氣變化，提前觀察雲層動態"
        },
        "last_updated": "2025-07-21 10:30:00"
    })

if __name__ == '__main__':
    print("🚀 啟動燒天預測系統前端測試服務器...")
    print("📊 警告歷史分析功能已集成")
    print("🌐 訪問: http://localhost:8888")
    
    app.run(
        host='0.0.0.0',
        port=8888,
        debug=True,
        use_reloader=False
    )
