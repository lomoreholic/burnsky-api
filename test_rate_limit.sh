#!/bin/bash
# 測試速率限制 - 快速發送多個請求

echo "🧪 測試速率限制功能"
echo "=============================="
echo ""

echo "📊 測試 1: 正常請求（查看限制標頭）"
curl -s -I http://127.0.0.1:5001/predict 2>&1 | grep -E "HTTP|X-RateLimit"
echo ""

echo "📊 測試 2: 發送5個連續請求"
for i in {1..5}; do
    echo -n "請求 $i: "
    response=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/predict)
    echo "HTTP $response"
    sleep 0.2
done
echo ""

echo "📊 測試 3: 檢查速率限制標頭變化"
curl -s -I http://127.0.0.1:5001/predict 2>&1 | grep "X-RateLimit"
echo ""

echo "✅ 測試完成"
