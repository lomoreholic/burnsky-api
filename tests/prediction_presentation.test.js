const test = require('node:test');
const assert = require('node:assert/strict');
const { describePrediction, getCountdown, formatHongKongDateTime } = require('../static/prediction_presentation.js');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

function prediction(overrides = {}) {
    return {
        burnsky_score: 80, advance_hours: 0,
        data_quality: {status: 'ready', score_usable: true},
        prediction_timing: {
            generated_at: '2026-11-13T23:00:00+08:00',
            evaluated_at: '2026-11-13T23:00:00+08:00', mode: 'current', event_type: 'sunrise',
            event_at: '2026-11-13T06:34:00+08:00',
            window_start: '2026-11-13T06:04:00+08:00', window_end: '2026-11-13T07:04:00+08:00',
            within_reference_window: false, ...overrides
        }
    };
}

test('nighttime high score does not become a tomorrow forecast', () => {
    const data = prediction();
    const text = describePrediction(data);
    assert.match(text.evaluation, /當前條件評估/);
    assert.match(text.evaluation, /23:00/);
    assert.match(text.scope, /不能當作下一次日出的預測/);
    const countdown = getCountdown(data.prediction_timing, new Date('2026-11-13T23:00:00+08:00'));
    assert.equal(countdown.timer, '已結束');
    assert.match(countdown.status, /沒有套用至明日/);
    assert.doesNotMatch(countdown.advice, /高機率|依然高|絕佳燒天/);
});

test('cross-midnight forecast shows its actual date and horizon', () => {
    const data = prediction({ evaluated_at: '2026-11-14T05:00:00+08:00', mode: 'forecast',
        event_at: '2026-11-14T06:35:00+08:00', window_start: '2026-11-14T06:05:00+08:00',
        window_end: '2026-11-14T07:05:00+08:00' });
    data.advance_hours = 6;
    const text = describePrediction(data);
    assert.match(text.evaluation, /2026/);
    assert.match(text.evaluation, /05:00/);
    assert.match(text.evaluation, /6小時後條件推算/);
    assert.match(text.event, /06:35/);
    const countdown = getCountdown(data.prediction_timing, new Date('2026-11-13T23:00:00+08:00'));
    assert.equal(countdown.timer, '07:05:00');
});

test('solar countdown is a reference even during the shooting window', () => {
    const data = prediction({ within_reference_window: true });
    const countdown = getCountdown(data.prediction_timing, new Date('2026-11-13T06:34:00+08:00'));
    assert.equal(countdown.timer, '00:30:00');
    assert.equal(countdown.inWindow, true);
    assert.match(countdown.status, /倒數不代表燒天預測/);
});

test('cached calculation time stays fixed rather than using the receipt time', () => {
    const data = prediction();
    const first = describePrediction(data);
    getCountdown(data.prediction_timing, new Date('2026-11-14T23:00:00+08:00'));
    assert.equal(describePrediction(data).generated, first.generated);
    assert.match(first.generated, /23:00/);
});

test('missing metadata is explicit and never fabricated from the browser clock', () => {
    assert.match(describePrediction({}).evaluation, /未提供/);
    assert.equal(getCountdown(null), null);
    assert.equal(formatHongKongDateTime(null), '未提供');
    assert.equal(formatHongKongDateTime('invalid'), '未提供');
});

test('formatting uses Hong Kong time regardless of the machine time zone', () => {
    assert.match(formatHongKongDateTime('2026-11-13T15:00:00Z'), /23:00/);
});

function alignedPrediction(overrides = {}) {
    return prediction({ generated_at: '2026-11-14T06:20:00+08:00',
        evaluated_at: '2026-11-14T06:20:00+08:00', event_at: '2026-11-14T06:35:00+08:00',
        window_start: '2026-11-14T06:05:00+08:00', window_end: '2026-11-14T07:05:00+08:00',
        within_reference_window: true, ...overrides });
}

test('only a fresh evaluation aligned with an unexpired solar window gets a primary score', () => {
    const text = describePrediction(alignedPrediction(), new Date('2026-11-14T06:25:00+08:00'));
    assert.equal(text.scorePrimary, true);
    assert.match(text.headline, /已對準日出/);
    const forecast = alignedPrediction({ mode: 'forecast', generated_at: '2026-11-14T00:20:00+08:00' });
    forecast.advance_hours = 6;
    assert.equal(describePrediction(forecast, new Date('2026-11-14T00:25:00+08:00')).scorePrimary, true);
});

test('unknown or insufficient quality does not promote a score', async () => {
    for (const quality of [undefined, {status: 'insufficient', score_usable: false}]) {
        const data = {...alignedPrediction(), data_quality: quality, prediction_level: '條件極佳',
            analysis_summary: ['立即出發拍攝']};
        const h = homepageHarness(new Date('2026-11-14T06:25:00+08:00'));
        const request = h.context.loadPrediction();
        h.requests[0].resolve(data);
        assert.equal(await request, true);
        assert.equal(h.elements.get('conditionScoreDetails').open, false);
        assert.match(h.elements.get('assessmentHeadline').textContent, /資料不足|未確認/);
        assert.doesNotMatch(h.summaries[0].join(''), /立即出發/);
        assert.deepEqual(h.notifications, []);
    }
});

test('three-hour forecast shows a usable score and planning advice despite optional gaps', async () => {
    const now = new Date('2026-11-14T03:35:00+08:00');
    const data = {...alignedPrediction({generated_at: now.toISOString(),
        evaluated_at: '2026-11-14T06:35:00+08:00', mode: 'forecast'}),
        advance_hours: 3, prediction_level: '條件良好', burnsky_score: 68,
        data_quality: {status: 'limited', score_usable: true, allow_high_score_notification: false}};
    const h = homepageHarness(now);
    const pending = h.context.loadPrediction();
    h.requests[0].resolve(data);
    assert.equal(await pending, true);
    assert.equal(h.elements.get('conditionScoreDetails').open, true);
    assert.match(h.elements.get('assessmentHeadline').textContent, /提前3小時/);
    assert.match(h.elements.get('assessmentNextStep').textContent, /安排|準備/);
    assert.match(h.summaries[0].join(''), /安排|準備/);
    assert.deepEqual(h.notifications, []);
});

test('missing-data failure explains the reason while preserving the previous result', async () => {
    const h = homepageHarness();
    const initial = h.context.loadPrediction();
    h.requests[0].resolve({...prediction(), prediction_level: '條件良好'});
    await initial;
    const refresh = h.context.loadPrediction();
    const error = new Error('主要資料不足');
    error.predictionReason = '主要資料不足，暫停評分：天文台溫度。';
    h.requests[1].reject(error);
    assert.equal(await refresh, false);
    assert.match(h.elements.get('predictionStatusText').textContent, /原因：主要資料不足/);
    assert.deepEqual(h.scores, [80]);
});

test('a daytime high score outside the window offers time selection instead of a shooting recommendation', () => {
    const data = alignedPrediction({ generated_at: '2026-11-14T03:20:00+08:00',
        evaluated_at: '2026-11-14T03:20:00+08:00', within_reference_window: true });
    const text = describePrediction(data, new Date('2026-11-14T03:25:00+08:00'));
    assert.equal(text.scorePrimary, false);
    assert.match(text.headline, /未對準/);
    assert.match(text.nextStep, /調整下方評估時間/);
});

test('an expired or stale aligned result is kept for reference without a primary score', () => {
    const data = alignedPrediction();
    const expired = describePrediction(data, new Date('2026-11-14T08:00:00+08:00'));
    assert.equal(expired.scorePrimary, false);
    assert.match(expired.headline, /已結束/);
    assert.match(expired.nextStep, /未提供下一次日出/);
    const stale = describePrediction(data, new Date('2026-11-14T06:40:00+08:00'));
    assert.equal(stale.scorePrimary, false);
    assert.match(stale.headline, /已過時/);
});

test('missing or invalid timing never promotes a high score', () => {
    for (const data of [{burnsky_score: 99}, alignedPrediction({window_end: 'invalid'}),
        alignedPrediction({generated_at: null}), alignedPrediction({event_type: 'other'})]) {
        const text = describePrediction(data, new Date('2026-11-14T06:25:00+08:00'));
        assert.equal(text.scorePrimary, false);
        assert.match(text.headline, /未能確認/);
    }
});

function homepageHarness(now) {
    const html = fs.readFileSync(path.join(__dirname, '../templates/index.html'), 'utf8');
    const start = html.indexOf('        function setPredictionStatus(');
    const end = html.indexOf('        function updateAnalysisFactors(', start);
    const elements = new Map();
    const requests = [];
    const scores = [];
    const errors = [];
    const notifications = [];
    const summaries = [];
    const context = {
        document: { getElementById(id) {
            if (!elements.has(id)) elements.set(id, { value: id === 'predictionType' ? 'sunrise' : '0',
                style: { display: 'none' }, classList: { add() {} }, textContent: '', setAttribute() {} });
            return elements.get(id);
        } },
        APIUtils: { fetchAPI: () => new Promise((resolve, reject) => requests.push({ resolve, reject })),
            showToast: (...args) => errors.push(args) },
        BurnSkyPresentation: { describePrediction: data => describePrediction(data, now), formatHongKongDateTime },
        updateBurnskyProgress: score => scores.push(score),
        updateAnalysisFactors() {}, updateCurrentWarnings() {}, updateWeatherData() {},
        updateViewingPlan() {},
        updateAirQualityData() {}, updateAnalysisSummary: summary => summaries.push(summary), loadLocationRecommendations() {},
        notifyHighPotentialPrediction: data => notifications.push(data), scheduleWebcamPreview() {},
        setTimeout() {}, console: { log() {}, error() {} }
    };
    vm.createContext(context);
    vm.runInContext(`let latestPredictionRequest = 0; let lastSuccessfulPrediction = null; ${html.slice(start, end)}`, context);
    return { context, elements, requests, scores, errors, notifications, summaries };
}

test('homepage collapses an out-of-window high score and suppresses its shooting summary and notification', async () => {
    const h = homepageHarness();
    const pending = h.context.loadPrediction();
    h.requests[0].resolve({ ...prediction(), prediction_level: '條件極佳', analysis_summary: ['立即出發拍攝'] });
    assert.equal(await pending, true);
    assert.equal(h.elements.get('conditionScoreDetails').open, false);
    assert.equal(h.elements.get('conditionScoreToggle').hidden, false);
    assert.match(h.elements.get('assessmentHeadline').textContent, /已結束|未對準/);
    assert.doesNotMatch(h.summaries[0].join(''), /立即出發/);
    assert.deepEqual(h.notifications, []);
    assert.deepEqual(h.scores, [80]);
});

test('switching to an aligned fresh evaluation restores the primary score and its analysis', async () => {
    const h = homepageHarness(new Date('2026-11-14T06:25:00+08:00'));
    const initial = h.context.loadPrediction();
    h.requests[0].resolve({ ...prediction(), prediction_level: '條件極佳' });
    await initial;
    assert.equal(h.elements.get('conditionScoreDetails').open, false);
    const refresh = h.context.loadPrediction();
    h.requests[1].resolve({ ...alignedPrediction(), prediction_level: '條件極佳', analysis_summary: ['已對準時段的條件摘要'] });
    await refresh;
    assert.equal(h.elements.get('conditionScoreDetails').open, true);
    assert.equal(h.elements.get('conditionScoreToggle').hidden, true);
    assert.match(h.elements.get('assessmentHeadline').textContent, /已對準日出/);
    assert.deepEqual(h.summaries[1], ['已對準時段的條件摘要']);
    assert.equal(h.notifications.length, 1);
});

test('a late response cannot overwrite the latest selected evaluation', async () => {
    const h = homepageHarness();
    const oldRequest = h.context.loadPrediction();
    const newRequest = h.context.loadPrediction();
    h.requests[1].resolve({ ...prediction(), burnsky_score: 65, prediction_level: '條件良好' });
    await newRequest;
    h.requests[0].resolve({ ...prediction(), burnsky_score: 31, prediction_level: '條件偏低' });
    await oldRequest;
    assert.deepEqual(h.scores, [65]);
    assert.equal(h.context.currentPredictedScore, 65);
    assert.equal(h.elements.get('content').style.display, 'block');
    assert.equal(h.errors.length, 0);
});

test('a late failure cannot hide a newer successful evaluation', async () => {
    const h = homepageHarness();
    const oldRequest = h.context.loadPrediction();
    const newRequest = h.context.loadPrediction();
    h.requests[1].resolve({ ...prediction(), prediction_level: '條件極佳' });
    await newRequest;
    h.requests[0].reject(new Error('stale request failed'));
    await oldRequest;
    assert.equal(h.elements.get('content').style.display, 'block');
    assert.equal(h.errors.length, 0);
});

test('first load remains readable and failure offers a retry without inventing a score', async () => {
    const h = homepageHarness();
    const request = h.context.loadPrediction();
    assert.equal(h.elements.get('content').style.display, 'block');
    assert.match(h.elements.get('predictionStatusText').textContent, /20秒/);
    h.requests[0].reject(new Error('offline'));
    assert.equal(await request, false);
    assert.equal(h.elements.get('predictionRetry').hidden, false);
    assert.match(h.elements.get('predictionStatusText').textContent, /沒有可用評估/);
    assert.deepEqual(h.scores, []);
    const retry = h.context.loadPrediction();
    assert.equal(h.elements.get('predictionRetry').hidden, true);
    h.requests[1].resolve({ ...prediction(), prediction_level: '條件極佳' });
    assert.equal(await retry, true);
    assert.deepEqual(h.scores, [80]);
});

test('failed mode change preserves the previous result and identifies its original selection', async () => {
    const h = homepageHarness();
    const first = h.context.loadPrediction();
    h.requests[0].resolve({ ...prediction(), prediction_level: '條件極佳' });
    await first;
    const generated = h.elements.get('lastUpdated').textContent;
    h.elements.get('predictionType').value = 'sunset';
    h.elements.get('advanceHours').value = '6';
    const refresh = h.context.loadPrediction();
    assert.equal(h.elements.get('content').style.display, 'block');
    assert.match(h.elements.get('predictionStatusText').textContent, /保留上次日出模式/);
    h.requests[1].reject(new Error('timeout'));
    await refresh;
    assert.equal(h.elements.get('lastUpdated').textContent, generated);
    assert.deepEqual(h.scores, [80]);
    assert.match(h.elements.get('predictionStatusText').textContent, /日落模式・6小時後/);
    assert.match(h.elements.get('predictionStatusText').textContent, /保留上次日出模式・當前條件/);
});

test('malformed responses cannot replace the last successful score', async () => {
    const h = homepageHarness();
    const first = h.context.loadPrediction();
    h.requests[0].resolve({ ...prediction(), prediction_level: '條件極佳' });
    await first;
    const refresh = h.context.loadPrediction();
    h.requests[1].resolve({ burnsky_score: 'not a score' });
    assert.equal(await refresh, false);
    assert.deepEqual(h.scores, [80]);
});

test('API timeout aborts a pending request and releases its timer', async () => {
    const html = fs.readFileSync(path.join(__dirname, '../templates/index.html'), 'utf8');
    const start = html.indexOf('            async fetchAPI(');
    const end = html.indexOf('            // 並行載入多個API', start);
    let timeout;
    let cleared = false;
    const context = { AbortController, console: { error() {} },
        setTimeout(fn, ms) { timeout = fn; assert.equal(ms, 20000); return 1; },
        clearTimeout() { cleared = true; },
        fetch(url, options) { return new Promise((resolve, reject) => {
            options.signal.addEventListener('abort', () => reject(new Error('aborted')));
        }); }
    };
    vm.createContext(context);
    vm.runInContext(`const api = { ${html.slice(start, end)} }; this.fetchAPI = api.fetchAPI;`, context);
    const request = context.fetchAPI('/predict');
    timeout();
    await assert.rejects(request, /aborted/);
    assert.equal(cleared, true);
});

test('homepage inline JavaScript parses after the presentation changes', () => {
    const html = fs.readFileSync(path.join(__dirname, '../templates/index.html'), 'utf8');
    for (const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) {
        if (!match[0].includes('application/ld+json')) new vm.Script(match[1]);
    }
});
