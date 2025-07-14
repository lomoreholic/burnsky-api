#!/bin/bash

# BurnSky SEO 自動化部署和監控腳本
# 用途: 部署代碼並檢查 SEO 狀況

set -e

echo "🔥 BurnSky SEO 自動化部署開始"
echo "=================================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數: 彩色輸出
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# 1. 檢查 Git 狀態
echo ""
print_info "檢查 Git 代碼庫狀態..."
git status --porcelain > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_status "Git 代碼庫正常"
else
    print_error "Git 代碼庫有問題"
    exit 1
fi

# 2. 檢查是否有未提交的更改
if [[ -n $(git status --porcelain) ]]; then
    print_warning "發現未提交的更改"
    echo ""
    git status --short
    echo ""
    read -p "是否要提交並推送這些更改？(y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "提交更改到 Git..."
        git add .
        git commit -m "SEO 優化: 自動提交 - $(date '+%Y-%m-%d %H:%M:%S')"
        
        print_info "推送到遠程代碼庫..."
        git push origin main
        print_status "代碼已推送到 GitHub"
    else
        print_warning "跳過提交，使用現有代碼進行檢查"
    fi
else
    print_status "沒有待提交的更改"
fi

# 3. 等待 Render 部署
print_info "等待 Render 自動部署完成..."
print_warning "通常需要 2-3 分鐘，請耐心等待..."

for i in {1..10}; do
    echo -n "."
    sleep 10
done
echo ""

# 4. 檢查網站可用性
print_info "檢查網站可用性..."
WEBSITE_URL="https://burnsky-api.onrender.com"

response=$(curl -s -o /dev/null -w "%{http_code}" "$WEBSITE_URL" || echo "000")

if [ "$response" = "200" ]; then
    print_status "網站正常運行 (HTTP $response)"
else
    print_error "網站無法訪問 (HTTP $response)"
    print_warning "可能需要更長時間部署，請稍後手動檢查"
fi

# 5. 運行 SEO 檢查
if [ "$response" = "200" ]; then
    print_info "運行線上 SEO 檢查..."
    echo ""
    
    if [ -f "seo_check_online.py" ]; then
        python seo_check_online.py
    else
        print_warning "SEO 檢查腳本不存在，跳過自動檢查"
    fi
fi

# 6. 檢查關鍵文件
print_info "檢查關鍵 SEO 文件..."

key_files=(
    "/robots.txt"
    "/sitemap.xml"
    "/ads.txt"
    "/privacy"
    "/terms"
)

for file in "${key_files[@]}"; do
    url="$WEBSITE_URL$file"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" = "200" ]; then
        print_status "$file (HTTP $response)"
    else
        print_error "$file (HTTP $response)"
    fi
done

# 7. API 端點檢查
print_info "檢查 API 端點..."

api_endpoints=(
    "/api"
    "/predict"
    "/predict/sunset"
    "/predict/sunrise"
)

for endpoint in "${api_endpoints[@]}"; do
    url="$WEBSITE_URL$endpoint"
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$response" = "200" ]; then
        print_status "$endpoint (HTTP $response)"
    else
        print_error "$endpoint (HTTP $response)"
    fi
done

# 8. 性能檢查
print_info "檢查網站性能..."
if command -v curl &> /dev/null; then
    load_time=$(curl -s -o /dev/null -w "%{time_total}" "$WEBSITE_URL")
    if (( $(echo "$load_time < 3.0" | bc -l) )); then
        print_status "載入時間: ${load_time}s (良好)"
    elif (( $(echo "$load_time < 5.0" | bc -l) )); then
        print_warning "載入時間: ${load_time}s (可接受)"
    else
        print_error "載入時間: ${load_time}s (需要優化)"
    fi
fi

# 9. 總結報告
echo ""
echo "🎯 部署和 SEO 檢查完成"
echo "======================="
print_status "網站 URL: $WEBSITE_URL"
print_status "部署時間: $(date '+%Y-%m-%d %H:%M:%S')"

echo ""
echo "📋 下一步建議:"
echo "1. 檢查 Google Search Console"
echo "2. 提交 sitemap.xml 到搜尋引擎"
echo "3. 監控網站性能和SEO表現"
echo "4. 定期更新內容和優化"

# 10. 保存檢查日誌
log_file="seo_deployment_$(date '+%Y%m%d_%H%M%S').log"
echo "SEO 部署檢查 - $(date)" > "$log_file"
echo "網站狀態: HTTP $response" >> "$log_file"
echo "檢查時間: $(date '+%Y-%m-%d %H:%M:%S')" >> "$log_file"

print_info "檢查日誌已保存: $log_file"

echo ""
print_status "🎉 BurnSky SEO 自動化部署完成！"
