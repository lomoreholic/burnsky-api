#!/bin/bash

# 要更新的頁面列表
pages=("best_locations.html" "warning_dashboard.html" "faq.html" "weather_terms.html" "terms.html" "ml_test.html")

for page in "${pages[@]}"; do
    echo "更新 $page..."
    
    # 更新 CSS
    sed -i.bak 's/display: grid !important;.*grid-template-columns: repeat(4, 1fr) !important;.*gap: 8px !important;.*grid-auto-rows: auto !important;/display: flex !important; flex-direction: column !important; gap: 8px !important;/g' "templates/$page"
    
    echo "$page CSS 已更新"
done

echo "所有頁面 CSS 更新完成！"
