/* Pure presentation helpers shared by the homepage and its regression checks. */
(function (root) {
    'use strict';

    function formatHongKongDateTime(value) {
        if (!value) return '未提供';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return '未提供';
        return new Intl.DateTimeFormat('zh-HK', {
            timeZone: 'Asia/Hong_Kong', year: 'numeric', month: '2-digit', day: '2-digit',
            hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
        }).format(date);
    }

    function describePrediction(data, now = new Date()) {
        const timing = data.prediction_timing;
        const start = Date.parse(timing?.window_start);
        const end = Date.parse(timing?.window_end);
        const evaluated = Date.parse(timing?.evaluated_at);
        const generated = Date.parse(timing?.generated_at);
        const event = Date.parse(timing?.event_at);
        if (!timing || ![start, end, evaluated, generated, event].every(Number.isFinite)
            || start > event || event > end || !['sunrise', 'sunset'].includes(timing.event_type)) {
            return { evaluation: '評估時間未提供，請重新載入', event: '日出／日落參考時間未提供',
                scope: '暫不能確認此指數的適用時段。', generated: '計算時間未提供',
                headline: '未能確認日出／日落評估時段', scorePrimary: false,
                nextStep: '請重新載入評估；暫時可先查看天空實況及官方天氣預報。' };
        }
        const eventName = timing.event_type === 'sunrise' ? '日出' : '日落';
        const aligned = evaluated >= start && evaluated <= end;
        const ended = now.getTime() > end;
        const fresh = now.getTime() - generated <= 15 * 60 * 1000 && generated <= now.getTime() + 60 * 1000;
        const quality = data.data_quality;
        const qualityReady = quality?.status === 'ready' && quality.score_usable === true
            && quality.allow_high_score_notification !== false;
        const scorePrimary = aligned && !ended && fresh && qualityReady;
        const headline = ended ? `所列${eventName}參考時段已結束`
            : !aligned ? `所選評估未對準${eventName}參考時段`
            : !fresh ? '評估資料已過時，請重新載入'
            : `評估已對準${eventName}前後30分鐘`;
        const nextStep = ended ? `請在下一次${eventName}前重新取得評估，並核對新結果的日期與時段。系統未提供下一次${eventName}的有效評估。`
            : !aligned ? `可調整下方評估時間，再核對是否落在所列${eventName}前後30分鐘；亦可接近該時段時重新載入。`
            : !fresh ? '重新載入後再核對計算時間；目前保留的分數只供查閱。'
            : '可配合天空實況及官方天氣警告，判斷是否準備拍攝；分數不保證出現燒天。';
        return {
            headline: aligned && !ended && fresh && !qualityReady ? '資料有限，暫不提供拍攝建議' : headline,
            nextStep: !qualityReady ? `${aligned && !ended && fresh ? '請先查看天空實況及官方天氣預報；此指數未能作為出發拍攝依據。' : nextStep} ${quality?.summary || '未取得評分資料完整性說明，請審慎參考。'}` : nextStep,
            scorePrimary,
            evaluation: `評估時間：${formatHongKongDateTime(timing.evaluated_at)}（香港時間） · ${timing.mode === 'forecast' ? `${data.advance_hours}小時後條件推算` : '當前條件評估'}`,
            event: `評估當日${eventName}參考：${formatHongKongDateTime(timing.event_at)}（香港時間）`,
            scope: aligned
                ? `評估時間在${eventName}前後30分鐘參考時段內；請配合實況判斷。`
                : `評估時間在${eventName}前後30分鐘參考時段以外；此分數只反映所列時間的條件，不能當作下一次${eventName}的預測。`,
            generated: `指數計算時間：${formatHongKongDateTime(timing.generated_at)}（香港時間）`
        };
    }

    function getCountdown(timing, now = new Date()) {
        if (!timing) return null;
        const start = new Date(timing.window_start).getTime();
        const end = new Date(timing.window_end).getTime();
        if (!Number.isFinite(start) || !Number.isFinite(end)) return null;
        const eventName = timing.event_type === 'sunrise' ? '日出' : '日落';
        const current = now.getTime();
        const inWindow = current >= start && current <= end;
        const ended = current > end;
        const difference = Math.max(0, (current < start ? start : end) - current);
        const seconds = Math.floor(difference / 1000);
        const timer = ended ? '已結束' : [Math.floor(seconds / 3600), Math.floor(seconds / 60) % 60, seconds % 60]
            .map(value => String(value).padStart(2, '0')).join(':');
        return {
            label: `評估當日${eventName}前後30分鐘 · ${ended ? '參考時段已過' : inWindow ? '參考時段剩餘' : '距離參考時段'}`,
            timer,
            status: ended ? '此參考時段已結束，沒有套用至明日。' : '日出／日落時間參考；倒數不代表燒天預測。',
            advice: timing.within_reference_window && inWindow
                ? '請查看天空實況及官方天氣警告，再決定是否拍攝。'
                : '分數適用於上方所列評估時間；如需其他時間的條件，請調整評估時間。',
            inWindow
        };
    }

    function getNextViewingWindow(schedule, now = new Date()) {
        if (!Array.isArray(schedule?.viewing_windows)) return null;
        return schedule.viewing_windows.filter(window => {
            const event = Date.parse(window?.event_at);
            const start = Date.parse(window?.window_start);
            const end = Date.parse(window?.window_end);
            return ['sunrise', 'sunset'].includes(window?.event_type)
                && [event, start, end].every(Number.isFinite)
                && start === event - 30 * 60 * 1000 && end === event + 30 * 60 * 1000
                && now.getTime() <= end;
        }).sort((a, b) => Date.parse(a.event_at) - Date.parse(b.event_at))[0] || null;
    }

    function describeViewingPlan(schedule, data, state = 'idle', now = new Date(), reason = '') {
        const window = getNextViewingWindow(schedule, now);
        if (!window) return {window: null, title: '下一次觀賞時段未能確認',
            timeLabel: '暫未取得可用的日出／日落時間', referenceNote: '取得時間資料後才會顯示觀賞參考時段。',
            status: '暫未能評估下一次觀賞條件', action: '可重試時間資料，或先查看天空實況及官方天氣預報。',
            buttonLabel: '重試觀賞時間', advanceHours: null};
        const event = Date.parse(window.event_at);
        const start = Date.parse(window.window_start);
        const end = Date.parse(window.window_end);
        const inWindow = now.getTime() >= start;
        const name = window.event_type === 'sunrise' ? '日出' : '日落';
        const direction = window.event_type === 'sunrise' ? '東面' : '西面';
        const hours = Math.max(0, Math.round((event - now.getTime()) / 3600000));
        const target = now.getTime() + hours * 3600000;
        const advanceHours = hours <= 24 && target >= start && target <= end ? hours : null;
        const timing = data?.prediction_timing;
        const evaluated = Date.parse(timing?.evaluated_at);
        const generated = Date.parse(timing?.generated_at);
        const matched = timing?.event_type === window.event_type && Date.parse(timing?.event_at) === event
            && Number.isFinite(evaluated) && evaluated >= start && evaluated <= end;
        const fresh = Number.isFinite(generated) && now.getTime() - generated <= 15 * 60000
            && generated <= now.getTime() + 60000;
        const usable = Number.isFinite(data?.burnsky_score) && data.burnsky_score >= 0 && data.burnsky_score <= 100
            && data?.data_quality?.score_usable === true;
        let status = '暫未有這個時段的適用評估';
        if (matched && fresh && usable) status = data.data_quality.status === 'ready'
            ? '已取得這個時段的條件參考' : '已取得時段內條件參考，資料有限';
        else if (matched && !fresh) status = '這個時段的評估已過時，請重新取得';
        if (state === 'loading') status = '正在取得條件參考，尚未確認最新結果';
        if (state === 'error') status = `最新條件參考未能取得${reason ? `：${reason}` : '，請重試'}`;
        const checkAt = event - 60 * 60000;
        const recheck = now.getTime() < checkAt ? `建議在${formatHongKongDateTime(checkAt)}（香港時間）再更新。`
            : '現在可再更新條件參考。';
        return {window, advanceHours,
            title: `${inWindow ? '進行中的' : '下一次'}${name}觀賞參考`,
            timeLabel: `${formatHongKongDateTime(window.window_start)} 至 ${formatHongKongDateTime(window.window_end)}（香港時間）`,
            referenceNote: `${name}：${formatHongKongDateTime(window.event_at)}（香港時間） · ${window.method === 'monthly_table' ? '月度時間表近似值' : '天文時間計算'}。前後30分鐘只作觀賞時間參考，不代表會出現燒天。`,
            status, action: `先選好望向${direction}的位置，並查看天空實況及官方天氣警告。${recheck}${matched && fresh && usable && data.data_quality.status === 'ready' ? '條件指數仍不保證出現燒天。' : '目前未能判斷是否值得出發拍攝。'}`,
            buttonLabel: matched ? '更新此時段條件參考' : '取得此時段條件參考'};
    }

    const api = { formatHongKongDateTime, describePrediction, getCountdown, getNextViewingWindow, describeViewingPlan };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.BurnSkyPresentation = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
