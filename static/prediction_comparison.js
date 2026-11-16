(function (root) {
    'use strict';
    const storageKey = 'burnsky-comparison-assessment';
    function validId(id) { return typeof id === 'string' && /^[a-f0-9]{64}$/.test(id); }
    function formatTime(value) {
        if (!value || !Number.isFinite(Date.parse(value))) return '未提供';
        return new Intl.DateTimeFormat('zh-HK', {timeZone: 'Asia/Hong_Kong', year:'numeric', month:'2-digit',
            day:'2-digit', hour:'2-digit', minute:'2-digit', hour12:false}).format(new Date(value));
    }
    function describePrediction(data) {
        const timing = data?.prediction_timing || {};
        return [
            `${timing.event_type === 'sunrise' ? '日出' : '日落'}條件指數：${Number.isFinite(data?.burnsky_score) ? Math.round(data.burnsky_score * 10) / 10 + '／100' : '未提供'}`,
            `原評估產生：${formatTime(timing.generated_at)}（香港時間）`,
            `評估目標：${formatTime(timing.evaluated_at)}（香港時間）`,
            `觀賞參考：${formatTime(timing.window_start)} 至 ${formatTime(timing.window_end)}（香港時間）`,
            data?.data_quality?.summary || '未提供原評估資料限制。'
        ];
    }
    function createController({document, fetch, storage, setTimer=setTimeout, clearTimer=clearTimeout}) {
        let latest = null, selectedId = null, pinnedId = null, sequence = 0, lastResult = null;
        try { const value = storage.getItem(storageKey); if (validId(value)) pinnedId = selectedId = value; } catch (_) {}
        const el = id => document.getElementById(id);
        function text(tag, value, parent) {
            const node = document.createElement(tag); node.textContent = value; parent.appendChild(node); return node;
        }
        function clear(id) { const node=el(id); node.replaceChildren(); return node; }
        function status(value) { el('comparisonStatus').textContent = value; }
        function buttons() {
            el('comparisonUnpin').hidden = !pinnedId;
            el('comparisonPin').disabled = !validId(latest?.assessment_id);
            el('comparisonRefresh').disabled = !selectedId;
        }
        function prediction(data) {
            const box = clear('comparisonPrediction');
            text('strong', pinnedId ? '已保留的原評估（不隨新分數更新）' : '目前選擇的原評估', box);
            describePrediction(data).forEach(line => text('p', line, box));
        }
        function render(result) {
            prediction(result.prediction);
            const box = clear('comparisonObservations');
            result.observations.forEach(item => {
                const card = document.createElement('article'); box.appendChild(card);
                text('h3', item.location, card);
                text('p', `方向：${item.direction} · ${item.aligned_reference ? '時間相符的更新參考' : '時間未配對，不能驗證原評估'}`, card);
                if (/^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(item.image_data_url || '')) {
                    const image = document.createElement('img'); image.src=item.image_data_url;
                    image.alt=`${item.location} 實況，來源更新 ${formatTime(item.source_updated_at)}（香港時間）`;
                    image.style.width='100%'; image.style.borderRadius='8px'; card.appendChild(image);
                }
                text('p', `影像來源：${item.source}`, card);
                text('p', `來源更新：${formatTime(item.source_updated_at)}（香港時間）`, card);
                text('p', '拍攝時間：未經核實', card);
                text('p', `取得圖片：${formatTime(item.retrieved_at)}（香港時間）`, card);
                text('p', `分析時間：${formatTime(item.analyzed_at)}（香港時間）`, card);
                text('p', item.description, card);
                text('small', item.note, card);
            });
            status(result.message);
        }
        async function load() {
            if (!validId(selectedId)) { status('未有已保存的評估；請先更新條件評估。'); return; }
            const id = selectedId, request = ++sequence;
            const controller = new AbortController();
            const timer = setTimer(() => controller.abort(), 20000);
            el('comparisonRefresh').disabled = true;
            status('正在載入所選評估的實況對照…');
            try {
                const response = await fetch('/api/prediction/cross-check?assessment_id=' + encodeURIComponent(id), {signal:controller.signal});
                const result = await response.json();
                if (request !== sequence || id !== selectedId) return;
                if (!response.ok || result.status !== 'success' || !result.prediction?.prediction_timing || !Array.isArray(result.observations)) {
                    throw new Error(result.message || '實況對照資料不完整');
                }
                render(result); lastResult = result;
            } catch (error) {
                if (request !== sequence || id !== selectedId) return;
                status((lastResult ? '更新失敗，保留上次實況及其原時間。' : '未能載入實況對照。') + '請按「載入／更新對照」重試。');
            } finally {
                clearTimer(timer); if (request === sequence) buttons();
            }
        }
        function choose(id, data) {
            ++sequence; selectedId = id; lastResult = null;
            clear('comparisonObservations');
            if (data) prediction(data); else clear('comparisonPrediction');
            status(id ? '原評估已選定；按「載入／更新對照」查看實況配對狀態。' : '未能保存原評估，請更新條件評估後重試。');
            buttons();
        }
        function setPrediction(data) {
            latest = data;
            if (!pinnedId && (selectedId !== data.assessment_id || !validId(data.assessment_id))) choose(validId(data.assessment_id) ? data.assessment_id : null, data);
            buttons();
        }
        function pin() {
            if (!validId(latest?.assessment_id)) return;
            pinnedId = latest.assessment_id;
            let persisted = true;
            try { storage.setItem(storageKey, pinnedId); } catch (_) { persisted=false; }
            choose(pinnedId, latest);
            status('已保留這次評估；新評分不會取代它，目標時段內可再更新實況。' +
                   (persisted ? '' : ' 此瀏覽器未能保存選擇，重新開頁後需再選。'));
        }
        function unpin() {
            pinnedId = null; try { storage.removeItem(storageKey); } catch (_) {}
            choose(validId(latest?.assessment_id) ? latest.assessment_id : null, latest);
        }
        el('comparisonRefresh').addEventListener('click', load);
        el('comparisonPin').addEventListener('click', pin);
        el('comparisonUnpin').addEventListener('click', unpin);
        buttons();
        if (pinnedId) load();
        return {setPrediction, load, pin, unpin};
    }
    const api = {validId, describePrediction, createController};
    if (typeof module === 'object' && module.exports) module.exports = api;
    if (root.document?.getElementById('comparisonSection')) {
        let storage;
        try { storage=root.localStorage; } catch (_) { storage={getItem(){},setItem(){},removeItem(){}}; }
        root.BurnSkyComparison = createController({document:root.document, fetch:root.fetch.bind(root), storage});
    }
})(typeof window === 'object' ? window : globalThis);
