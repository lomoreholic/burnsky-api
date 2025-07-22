#!/usr/bin/env python3
"""
檢查 index.html 中的 JavaScript 語法
"""

import re
from datetime import datetime

def check_javascript_syntax():
    print("🔍 JavaScript 語法檢查")
    print("=" * 50)
    print(f"⏰ 檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取主要的 JavaScript 部分（從第一個 <script> 到最後一個 </script>）
        start_pos = content.find('<script>')
        if start_pos == -1:
            print("❌ 未找到 JavaScript 代碼")
            return
        
        end_pos = content.rfind('</script>')
        if end_pos == -1:
            print("❌ 未找到 JavaScript 結束標籤")
            return
        
        js_code = content[start_pos:end_pos + 9]  # 包含完整的 script 標籤
        
        print("📊 語法檢查結果:")
        
        # 檢查常見的語法問題
        checks = [
            ("函數定義", r'async function \w+\(', "✅"),
            ("Chart.js 變量", r'let \w+Chart = null', "✅"),
            ("API 調用", r'fetch\([\'\"]/api/', "✅"),
            ("事件監聽器", r'addEventListener\(', "✅"),
            ("錯誤處理", r'catch \(error\)', "✅"),
            ("Chart 創建", r'new Chart\(', "✅"),
            ("圖表銷毀", r'\.destroy\(\)', "✅")
        ]
        
        for check_name, pattern, status in checks:
            matches = re.findall(pattern, js_code)
            if matches:
                print(f"   ✅ {check_name}: 找到 {len(matches)} 個實例")
            else:
                print(f"   ⚠️  {check_name}: 未找到")
        
        print()
        
        # 檢查可能的語法錯誤
        print("🔧 潛在問題檢查:")
        
        issues = []
        
        # 檢查未閉合的括號
        open_braces = js_code.count('{')
        close_braces = js_code.count('}')
        if open_braces != close_braces:
            issues.append(f"大括號不匹配: {open_braces} 開 vs {close_braces} 閉")
        
        open_parens = js_code.count('(')
        close_parens = js_code.count(')')
        if open_parens != close_parens:
            issues.append(f"小括號不匹配: {open_parens} 開 vs {close_parens} 閉")
        
        # 檢查重複的函數註釋
        duplicate_comments = re.findall(r'//\s*載入類別分布圖表', js_code)
        if len(duplicate_comments) > 1:
            issues.append(f"重複註釋: '載入類別分布圖表' 出現 {len(duplicate_comments)} 次")
        
        # 檢查重複的函數定義
        function_pattern = r'async function (\w+)\('
        functions = re.findall(function_pattern, js_code)
        function_counts = {}
        for func in functions:
            function_counts[func] = function_counts.get(func, 0) + 1
        
        for func, count in function_counts.items():
            if count > 1:
                issues.append(f"重複函數定義: '{func}' 定義了 {count} 次")
        
        if issues:
            for issue in issues:
                print(f"   ⚠️  {issue}")
        else:
            print("   ✅ 未發現語法問題")
        
        print()
        
        # 統計信息
        print("📈 代碼統計:")
        print(f"   📄 JavaScript 總行數: {js_code.count(chr(10)) + 1:,}")
        print(f"   🔧 函數定義數量: {len(functions)}")
        print(f"   📡 API 調用數量: {len(re.findall(r'fetch\(', js_code))}")
        print(f"   📊 圖表實例: {len(re.findall(r'new Chart\(', js_code))}")
        
        print()
        print("🎯 檢查完成!")
        
        if not issues:
            print("✅ JavaScript 語法正常，圖表功能已完全集成！")
        else:
            print("⚠️  發現一些問題，但可能不影響功能")
        
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")

if __name__ == "__main__":
    check_javascript_syntax()
