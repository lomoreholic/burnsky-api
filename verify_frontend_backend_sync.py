#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""驗證前後端因子配置一致性"""

import re
import sys

print('🔍 前後端因子配置一致性檢查')
print('='*70)

# 1. 讀取後端配置 (unified_scorer.py)
print('\n📋 步驟1: 讀取後端配置...')
backend_config = {}
try:
    with open('unified_scorer.py', 'r', encoding='utf-8') as f:
        content = f.read()
        # 找到 factor_max_scores 配置
        match = re.search(r"'factor_max_scores':\s*\{([^}]+)\}", content)
        if match:
            config_text = match.group(1)
            # 解析每個因子
            for line in config_text.split('\n'):
                if ':' in line:
                    parts = line.split(':')
                    key = parts[0].strip().strip("'")
                    value = parts[1].strip().rstrip(',')
                    if value.isdigit():
                        backend_config[key] = int(value)
    
    print('✅ 後端配置讀取成功')
    print('   後端因子權重 (unified_scorer.py):')
    for key, val in backend_config.items():
        pct = (val / 150) * 100
        print(f'   • {key}: {val}分 ({pct:.1f}%)')
except Exception as e:
    print(f'❌ 讀取後端配置失敗: {e}')
    sys.exit(1)

# 2. 讀取前端配置 (templates/index.html)
print('\n📋 步驟2: 讀取前端配置...')
frontend_config = {}
try:
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
        # 找到 factorNames 配置
        match = re.search(r'const factorNames = \{(.+?)\};', content, re.DOTALL)
        if match:
            config_text = match.group(1)
            # 解析每個因子的 maxScore
            factor_matches = re.finditer(r"'(\w+)':\s*\{[^}]*maxScore:\s*(\d+)", config_text)
            for m in factor_matches:
                factor_name = m.group(1)
                max_score = int(m.group(2))
                frontend_config[factor_name] = max_score
    
    print('✅ 前端配置讀取成功')
    print('   前端顯示分數 (templates/index.html):')
    for key, val in frontend_config.items():
        pct = (val / 150) * 100
        print(f'   • {key}: {val}分 ({pct:.1f}%)')
except Exception as e:
    print(f'❌ 讀取前端配置失敗: {e}')
    sys.exit(1)

# 3. 對比前後端配置
print('\n📊 步驟3: 對比前後端配置...')
print('='*70)

# 因子名稱映射
factor_mapping = {
    'time': 'time_factor',
    'temperature': 'temperature_factor',
    'humidity': 'humidity_factor',
    'visibility': 'visibility_factor',
    'cloud': 'cloud_analysis_factor',
    'uv': 'uv_factor',
    'wind': 'wind_factor',
    'air_quality': 'air_quality_factor',
    'pressure': 'pressure_factor'  # 前端可能不顯示
}

all_consistent = True
comparison_table = []

print(f'\n{"因子":15s} {"後端":8s} {"前端":8s} {"差異":8s} {"狀態":6s}')
print('-'*70)

for backend_key, frontend_key in factor_mapping.items():
    backend_score = backend_config.get(backend_key, 0)
    frontend_score = frontend_config.get(frontend_key, -1)
    
    if frontend_score == -1:
        status = '⚠️ 未顯示'
        diff = '-'
        if backend_key != 'pressure':  # 氣壓不顯示是正常的
            all_consistent = False
    elif backend_score == frontend_score:
        status = '✅ 一致'
        diff = '0'
    else:
        status = '❌ 不一致'
        diff = f'{frontend_score - backend_score:+d}'
        all_consistent = False
    
    comparison_table.append({
        'factor': backend_key,
        'backend': backend_score,
        'frontend': frontend_score if frontend_score != -1 else '-',
        'diff': diff,
        'status': status
    })
    
    print(f'{backend_key:15s} {backend_score:3d}分    {str(frontend_score if frontend_score != -1 else "-"):>4s}分    {diff:>4s}     {status}')

# 4. 總結
print('\n' + '='*70)
print('📋 驗證結果總結:')
print('='*70)

if all_consistent:
    print('✅ 前後端配置完全一致！')
    print('   所有因子的最大分數在前後端完全匹配。')
else:
    print('⚠️ 發現不一致的地方：')
    inconsistent = [item for item in comparison_table if '❌' in item['status']]
    for item in inconsistent:
        print(f'   • {item["factor"]}: 後端{item["backend"]}分 vs 前端{item["frontend"]}分 (差異{item["diff"]})')
    print('\n💡 建議：檢查並修正不一致的配置')

# 5. 顯示當前總分配置
print(f'\n📊 總分配置:')
backend_total = sum(backend_config.values())
frontend_total = sum([v for v in frontend_config.values() if v > 0])
print(f'   後端總分: {backend_total}分')
print(f'   前端總分: {frontend_total}分 (不含氣壓)')

print('\n' + '='*70)
print('🔍 如何查看實際效果:')
print('='*70)
print('1. 啟動開發伺服器: python run_dev.py')
print('2. 打開瀏覽器: http://localhost:5001')
print('3. 查看「📊 詳細分析因子」區塊')
print('4. 對比每個因子卡片顯示的「X/Y分」')
print('5. 檢查是否與後端配置一致')
print()
print('💡 提示：')
print('   • 時間因子: 應顯示「X/18分」')
print('   • 溫度因子: 應顯示「X/15分」')
print('   • 濕度因子: 應顯示「X/20分」')
print('   • 能見度因子: 應顯示「X/20分」')
print('   • 雲層因子: 應顯示「X/35分」⭐ 最重要')
print('   • UV因子: 應顯示「X/2分」⭐ 已大幅降低')
print('   • 風速因子: 應顯示「X/15分」')
print('   • 空氣因子: 應顯示「X/15分」')
print('='*70)

# 返回狀態碼
sys.exit(0 if all_consistent else 1)
