(function (root) {
    'use strict';
    function createController(document, fetch) {
        const el = id => document.getElementById(id);
        function add(parent, tag, text, className) {
            const node = document.createElement(tag);
            node.textContent = String(text ?? '');
            if (className) node.className = className;
            parent.appendChild(node);
            return node;
        }
        function number(value, suffix = '') {
            return Number.isFinite(value) ? `${value}${suffix}` : '未提供';
        }
        function table(parent, caption, headers, rows) {
            const wrap = add(parent, 'div', '', 'history-table-wrap');
            const grid = add(wrap, 'table', '', 'history-table');
            add(grid, 'caption', caption);
            const head = add(add(grid, 'thead', ''), 'tr', '');
            headers.forEach(label => add(head, 'th', label).setAttribute('scope', 'col'));
            const body = add(grid, 'tbody', '');
            rows.forEach(values => {
                const row = add(body, 'tr', '');
                values.forEach((value, index) => {
                    const cell = add(row, index ? 'td' : 'th', value);
                    if (!index) cell.setAttribute('scope', 'row');
                });
            });
        }
        function render(data) {
            const target = el('historyResult');
            target.replaceChildren();
            const stats = data.summary;
            add(target, 'h2', `最近 ${data.time_range.days} 天 · 預測分數分布`);
            add(target, 'p', `${data.time_range.start_date} 至 ${data.time_range.end_date}（香港時間）；按預測產生時間統計次數，並非獨立燒天日數。`);
            if (stats.total_predictions === 0) {
                add(target, 'p', '這個期間有 0 次預測紀錄，暫無分布或時段比較。', 'history-empty');
            } else {
                const metrics = add(target, 'div', '', 'history-metrics');
                [['預測次數', stats.total_predictions, ''], ['平均預測分數', stats.avg_score, '/100'],
                    ['高分預測次數（≥70）', stats.high_score_count, ''], ['高分預測比例', stats.high_score_prediction_rate, '%']].forEach(([label, value, suffix]) => {
                    const card = add(metrics, 'div', '', 'history-metric');
                    add(card, 'strong', number(value, suffix)); add(card, 'span', label);
                });
                [['較低分（<50）', stats.low_score_count], ['中分（50–<70）', stats.medium_score_count],
                    ['高分（≥70）', stats.high_score_count]].forEach(([label, count]) => {
                    const row = add(target, 'div', '', 'history-distribution');
                    add(row, 'span', label);
                    const bar = add(row, 'progress', ''); bar.max = stats.total_predictions; bar.value = count;
                    bar.setAttribute('aria-label', label + '預測次數');
                    add(row, 'span', number(count, ' 次'));
                });
                table(target, '日出／日落預測分數；不代表實際拍攝效果', ['預測模式', '次數', '平均分', '高分比例'],
                    Object.entries(data.by_type || {}).map(([type, info]) => [type === 'sunrise' ? '日出' : type === 'sunset' ? '日落' : type,
                        number(info.count), number(info.avg_score), number(info.high_score_prediction_rate, '%')]));
                const daily = add(target, 'details', ''); add(daily, 'summary', '查看每日預測分數');
                table(daily, '按預測產生日期分組（香港時間；最多最近30個有紀錄日期）', ['日期', '平均分', '最高分', '高分次數'],
                    (data.daily_trends || []).map(day => [day.date, number(day.avg_score), number(day.max_score), number(day.high_score_count)]));
                const hours = add(target, 'details', ''); add(hours, 'summary', '開發分析：預測產生鐘點');
                add(hours, 'p', '下面是平均預測分數較高的五個產生鐘點組（香港時間）。不是預測目標時間，也不是拍攝時段推薦。');
                table(hours, '按產生鐘點分組', ['產生鐘點', '次數', '平均預測分'],
                    (data.best_hours || []).map(hour => [number(hour.hour, ':00'), number(hour.count), number(hour.avg_score)]));
            }
            add(target, 'h2', '用戶自報評分誤差');
            add(target, 'p', '來自同期提交的用戶評分，包含不同提前時間的預測；不等同提前 3 小時驗證。相片輔助回報亦未經獨立核實。');
            const feedback = data.verified_accuracy;
            if (!feedback?.has_data) {
                add(target, 'p', feedback?.message?.startsWith('計算錯誤') ? '自報評分統計暫時未能取得，請重試。' : '這個期間暫無可用自報評分；不顯示評分誤差或命中率。');
            } else {
                add(target, 'p', `自報樣本 ${number(feedback.feedback_count)} 筆；平均絕對評分誤差 ${number(feedback.avg_error)} 分（0–100分制，越低表示越接近自報評分）。`);
                add(target, 'p', `其中手動回報 ${number(feedback.manual_verified_count)} 筆、相片輔助回報 ${number(feedback.photo_verified_count)} 筆。`);
                add(target, 'p', '回報地點、主觀評分及回報意願會影響結果；目前不據此宣稱全港預測準確率。');
            }
        }
        let busy = false;
        let loaded = false;
        async function load() {
            if (busy) return;
            busy = true;
            el('historyRefresh').disabled = true; el('historyDays').disabled = true;
            const days = el('historyDays').value;
            el('historyStatus').textContent = '正在更新紀錄。';
            try {
                const response = await fetch(`/api/burnsky/history?days=${encodeURIComponent(days)}`, {signal: AbortSignal.timeout(20000)});
                const data = await response.json();
                if (!response.ok || data.status !== 'success' || data.data_source !== 'prediction_history' ||
                    !['total_predictions', 'avg_score', 'high_score_count', 'medium_score_count', 'low_score_count', 'high_score_prediction_rate']
                        .every(key => Number.isFinite(data.summary?.[key]) && data.summary[key] >= 0) ||
                    !data.time_range || data.time_range.days !== Number(days) ||
                    !data.by_type || Object.values(data.by_type).some(info => !info || !Number.isFinite(info.count)) ||
                    !Array.isArray(data.daily_trends) || data.daily_trends.some(day => !day || typeof day.date !== 'string') ||
                    !Array.isArray(data.best_hours) || data.best_hours.some(hour => !hour || !Number.isFinite(hour.hour)) ||
                    data.time_basis !== 'prediction_generated_at_hong_kong') throw new Error('無效資料');
                render(data); loaded = true;
                el('historyStatus').textContent = `已更新最近 ${data.time_range.days} 天的紀錄。`;
            } catch (error) {
                el('historyStatus').textContent = loaded ? '未能更新；保留上次結果及原有統計期間，請重試。' : '未能讀取紀錄，統計數值未知；請重試。';
            } finally {
                busy = false; el('historyRefresh').disabled = false; el('historyDays').disabled = false;
            }
        }
        el('historyRefresh').addEventListener('click', load);
        el('historyDays').addEventListener('change', load);
        return {load};
    }
    const api = {createController};
    if (typeof module === 'object' && module.exports) module.exports = api;
    if (root.document?.getElementById('historyResult')) createController(root.document, root.fetch.bind(root)).load();
})(typeof window === 'object' ? window : globalThis);
