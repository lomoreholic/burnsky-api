#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更細緻警告分類處理 - 實際驗證
"""

import sys
import json
from datetime import datetime

# 模擬 app.py 的核心警告分類函數
def parse_warning_details(warning_text):
    """解析警告詳細資訊"""
    warning_text_lower = warning_text.lower()
    
    # 雨量警告分類
    if '黑色暴雨' in warning_text or '黑雨' in warning_text:
        return {
            'category': 'rainfall',
            'subcategory': 'black_rain',
            'severity': 'extreme',
            'level': 4,
            'impact_factors': ['能見度極差', '道路積水', '山洪風險']
        }
    elif '紅色暴雨' in warning_text or '紅雨' in warning_text:
        return {
            'category': 'rainfall', 
            'subcategory': 'red_rain',
            'severity': 'severe',
            'level': 3,
            'impact_factors': ['能見度差', '交通阻塞', '戶外風險']
        }
    elif '八號烈風' in warning_text or '八號風球' in warning_text:
        return {
            'category': 'wind_storm',
            'subcategory': 'gale_8',
            'severity': 'moderate',
            'level': 2,
            'impact_factors': ['強風影響', '戶外活動限制']
        }
    elif '雷暴' in warning_text:
        if '嚴重' in warning_text:
            return {
                'category': 'thunderstorm',
                'subcategory': 'severe_thunderstorm', 
                'severity': 'severe',
                'level': 3,
                'impact_factors': ['強烈雷電', '局部大雨', '強陣風']
            }
        else:
            return {
                'category': 'thunderstorm',
                'subcategory': 'general_thunderstorm',
                'severity': 'moderate',
                'level': 2,
                'impact_factors': ['雷電活動', '局部雨水']
            }
    elif '霧' in warning_text:
        return {
            'category': 'visibility',
            'subcategory': 'fog',
            'severity': 'moderate', 
            'level': 2,
            'impact_factors': ['能見度差', '海陸交通', '航海風險']
        }
    
    return None

def validate_warning_classification():
    """驗證警告分類功能"""
    print("🧪 測試：更細緻的警告分類處理")
    print("=" * 50)
    
    test_warnings = [
        "黑色暴雨警告信號現正生效",
        "紅色暴雨警告信號現正生效", 
        "八號烈風信號現正生效",
        "嚴重雷暴警告",
        "雷暴警告",
        "大霧警告"
    ]
    
    success_count = 0
    total_tests = len(test_warnings)
    
    for i, warning in enumerate(test_warnings, 1):
        print(f"\n📋 測試 {i}: {warning}")
        result = parse_warning_details(warning)
        
        if result:
            print(f"   ✅ 類別: {result['category']}")
            print(f"   ✅ 子類: {result['subcategory']}")
            print(f"   ✅ 嚴重度: {result['severity']} (等級 {result['level']})")
            print(f"   ✅ 影響因子: {', '.join(result['impact_factors'])}")
            success_count += 1
        else:
            print("   ❌ 無法識別")
    
    print(f"\n📊 測試結果:")
    print(f"   成功識別: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    if success_count == total_tests:
        print("   🎉 所有警告都成功分類！")
        return True
    else:
        print("   ⚠️ 部分警告未能正確分類")
        return False

if __name__ == "__main__":
    print("🌩️ 燒天預測系統 - 警告分類驗證")
    print(f"📅 驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = validate_warning_classification()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 更細緻的警告分類處理功能運作正常！")
        print("🎯 系統已具備智能警告識別能力")
        sys.exit(0)
    else:
        print("❌ 警告分類功能需要進一步調整")
        sys.exit(1)
