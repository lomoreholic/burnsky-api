(function (root) {
    'use strict';
    function time(value) {
        return new Intl.DateTimeFormat('zh-HK', {timeZone:'Asia/Hong_Kong', month:'2-digit', day:'2-digit',
            hour:'2-digit', minute:'2-digit', hour12:false}).format(new Date(value));
    }
    function summary(version, stats) {
        return `${version}：已留底 ${stats.forecasts} 次；可判斷自報 ${stats.labeled} 次，無法判斷 ${stats.unsure} 次。` +
            ` 等待時段結束 ${stats.awaiting_event} 次、時段已完待回報 ${stats.awaiting_report} 次。` +
            ` 命中 ${stats.hits}、錯報 ${stats.false_alarms}、漏報 ${stats.misses}、正確低分 ${stats.correct_negatives}。`;
    }
    function createController(document, fetch) {
        const el = id => document.getElementById(id);
        function add(parent, tag, content) {
            const node = document.createElement(tag); node.textContent = content; parent.appendChild(node); return node;
        }
        function field(form, label, node) {
            const wrapper = add(form, 'label', label + ' ');
            wrapper.style.display = 'block'; wrapper.style.margin = '10px 0'; wrapper.appendChild(node);
            return node;
        }
        function fraction(count, total) {
            return total > 0 ? `${count}/${total}` : '未有可判斷自報';
        }
        function eventSummary(parent, label, stats) {
            add(parent, 'h4', label);
            add(parent, 'p', summary(label, stats));
            add(parent, 'p', `高分預測中自報明顯燒天：${fraction(stats.hits, stats.predicted_positive)}（只計可判斷自報）；` +
                `分類不符：${fraction(stats.false_alarms + stats.misses, stats.labeled)}。`);
            add(parent, 'p', `高分但微弱／沒有：${fraction(stats.false_alarms, stats.predicted_positive)}（已回報高分預測）；` +
                `明顯燒天但預測低分：${fraction(stats.misses, stats.observed_positive)}（自報明顯燒天）。`);
            const scroll = add(parent, 'div', ''); scroll.style.overflowX = 'auto';
            const table = add(scroll, 'table', ''); table.style.width = '100%'; table.style.color = '#333';
            add(table, 'caption', `${label}分數區間實況次數；分組不代表發生機率`);
            const header = add(add(table, 'thead', ''), 'tr', '');
            ['條件指數', '留底', '可判斷自報', '明顯燒天', '微弱／沒有', '無法判斷', '待實況'].forEach(label => {
                const cell = add(header, 'th', label); cell.setAttribute('scope', 'col');
            });
            const body = add(table, 'tbody', '');
            stats.score_bands.forEach(band => {
                const row = add(body, 'tr', '');
                const heading = add(row, 'th', band.label); heading.setAttribute('scope', 'row');
                [band.forecasts, band.labeled, band.strong, band.weak_or_none, band.unsure,
                    band.awaiting_event + band.awaiting_report].forEach(value => add(row, 'td', String(value)));
            });
        }
        let busy = false;
        async function json(url, options) {
            const response = await fetch(url, {...options, signal:AbortSignal.timeout(20000)});
            const data = await response.json();
            if (!response.ok || data.status !== 'success') throw new Error(data.message || '未能讀取紀錄。');
            return data;
        }
        function formFor(card, record) {
            const form = document.createElement('form'); card.appendChild(form);
            const result = field(form, '親身觀察實況', document.createElement('select'));
            [['', '請選擇'], ['strong', '明顯成片燒天'], ['weak_or_none', '微弱／沒有'], ['unsure', '無法判斷／視線受阻']].forEach(([value, label]) => {
                const option = add(result, 'option', label); option.value = value;
            });
            result.required = true;
            const observed = field(form, '實際觀察時間（香港時間）', document.createElement('input'));
            observed.type = 'datetime-local'; observed.required = true;
            // API times carry +08:00; do not convert this input through the browser's local zone.
            observed.min = record.prediction.prediction_timing.window_start.slice(0, 16);
            observed.max = record.prediction.prediction_timing.window_end.slice(0, 16);
            const location = field(form, '香港觀察地點', document.createElement('input'));
            location.required = true; location.maxLength = 120; location.placeholder = '例如：西環海濱';
            const confirmed = field(form, '確認以上為本人在香港親身觀察，並非根據預測分數填寫', document.createElement('input'));
            confirmed.type = 'checkbox'; confirmed.required = true;
            const button = add(form, 'button', '提交實況（每次預測只記錄一次）'); button.type = 'submit'; button.className = 'refresh-btn';
            const status = add(form, 'p', ''); status.setAttribute('role', 'status');
            form.addEventListener('submit', async event => {
                event.preventDefault();
                if (!form.reportValidity() || button.disabled) return;
                button.disabled = true;
                try {
                    await json('/api/verification/three-hour/' + encodeURIComponent(record.assessment_id) + '/outcome', {
                        method:'POST', headers:{'Content-Type':'application/json'},
                        body:JSON.stringify({result:result.value, observed_at:observed.value + '+08:00',
                            location:location.value, confirmed:confirmed.checked})
                    });
                    status.textContent = '實況已保存。'; await load();
                } catch (error) { status.textContent = error.message; button.disabled = false; }
            });
        }
        function render(data) {
            el('verificationSummary').replaceChildren(); el('verificationRecords').replaceChildren();
            Object.entries(data.by_version).forEach(([version, stats]) => {
                const parent = el('verificationSummary');
                add(parent, 'p', summary(version, stats));
                if (stats.by_event) {
                    const details = add(parent, 'details', '');
                    add(details, 'summary', `${version}：查看日出／日落及分數區間`);
                    eventSummary(details, '日出', stats.by_event.sunrise);
                    eventSummary(details, '日落', stats.by_event.sunset);
                }
            });
            data.records.slice(0, 12).forEach(record => {
                const p = record.prediction, timing = p.prediction_timing;
                const card = add(el('verificationRecords'), 'article', '');
                card.style.borderTop = '1px solid #ddd'; card.style.padding = '12px 0';
                add(card, 'h3', `${time(timing.event_at)} ${timing.event_type === 'sunrise' ? '日出' : '日落'} · ${p.burnsky_score}/100`);
                add(card, 'p', `發出：${time(timing.generated_at)}（提前 ${record.lead_minutes} 分鐘）；${p.scoring_method}`);
                if (record.outcome) {
                    const labels = {strong:'明顯成片燒天', weak_or_none:'微弱／沒有', unsure:'無法判斷'};
                    add(card, 'p', `用戶自報：${labels[record.outcome.result]} · ${record.outcome.location} · ${time(record.outcome.observed_at)}（未獨立核實）`);
                } else if (record.state === 'awaiting_event') {
                    add(card, 'p', '等待目標時段結束，之後可填實況。');
                } else formFor(card, record);
            });
            el('verificationStatus').textContent = data.records.length ? data.note : '未有提前三小時留底紀錄。由下一次符合時段的日出／日落開始收集，暫時沒有驗證結果。';
        }
        async function load() {
            if (busy) return;
            busy = true; el('verificationRefresh').disabled = true;
            try { render(await json('/api/verification/three-hour')); }
            catch (error) { el('verificationStatus').textContent = '未能更新，現有顯示可能過時。' + error.message; }
            finally { busy = false; el('verificationRefresh').disabled = false; }
        }
        el('verificationRefresh').addEventListener('click', load);
        return {load};
    }
    const api = {summary, createController};
    if (typeof module === 'object' && module.exports) module.exports = api;
    if (root.document?.getElementById('verificationSection')) createController(root.document, root.fetch.bind(root)).load();
})(typeof window === 'object' ? window : globalThis);
