const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '../templates/burnsky_dashboard.html'), 'utf8');
const script = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
    .map(match => match[1]).find(code => code.includes('async function loadDashboardData'));

function element() {
    return {
        children: [], style: {}, hidden: false, _text: '--',
        get textContent() { return this._text + this.children.map(child => child.textContent).join(''); },
        set textContent(value) { this._text = String(value); this.children = []; },
        get childElementCount() { return this.children.length; },
        replaceChildren() { this.children = []; this._text = ''; },
        append(...children) { this.children.push(...children); },
        appendChild(child) { this.children.push(child); },
        addEventListener() {}, querySelectorAll() { return []; }
    };
}

function harness() {
    const elements = new Map();
    const requests = [];
    const getElement = id => {
        if (!elements.has(id)) elements.set(id, element());
        return elements.get(id);
    };
    const context = {
        AbortController, console: { error() {}, warn() {} },
        document: { getElementById: getElement, createElement: element, addEventListener() {},
            querySelectorAll() { return [getElement('totalWarnings'), getElement('high'), getElement('medium')]; } },
        setTimeout() { return 1; }, clearTimeout() {},
        fetch: () => new Promise((resolve, reject) => requests.push({resolve, reject}))
    };
    context.window = context;
    vm.createContext(context);
    vm.runInContext(script, context);
    return {context, requests, getElement};
}

function data(overrides = {}) {
    return {status: 'success', data_source: 'prediction_history', has_data: true,
        generated_at: '2026-11-14T07:00:00Z', statistics: {total_warnings: 2, high_severity: 1, medium_severity: 0},
        accuracy: {verified: false}, monthly_data: [],
        high_impact_warnings: [{score: 90, timestamp: '2026-11-14T07:00:00Z'}],
        insights: {seasonal: '已記錄的季節未足以比較。'}, ...overrides};
}

function respond(h, index, body) {
    h.requests[index].resolve({ok: true, json: async () => body});
}

test('the initial page contains no sample records or fixed statistical claims', () => {
    assert.doesNotMatch(html, /聖誕節燒天|2024-12-28|下午 6:30|冬季月份.*最高/);
    new vm.Script(script);
});

test('an empty successful response clears old records and displays zero separately from failure', async () => {
    const h = harness();
    const first = h.context.loadDashboardData();
    respond(h, 0, data());
    await first;
    assert.equal(h.getElement('highScoreRecords').childElementCount, 1);
    const empty = h.context.loadDashboardData();
    respond(h, 1, data({has_data: false, statistics: {total_warnings: 0}, high_impact_warnings: [], insights: {}}));
    await empty;
    assert.equal(h.getElement('totalWarnings').textContent, '0');
    assert.equal(h.getElement('highScoreRecords').childElementCount, 0);
    assert.match(h.getElement('dashboardStatus').textContent, /未有已保存/);
    assert.match(h.getElement('dashboardInsights').textContent, /未有足夠/);
    assert.equal(h.getElement('warningTimelineChart').hidden, true);
});

test('a first-load failure leaves unknown statistics and offers a retry', async () => {
    const h = harness();
    const first = h.context.loadDashboardData();
    h.requests[0].resolve({ok: false, status: 503});
    await first;
    assert.equal(h.getElement('totalWarnings').textContent, '--');
    assert.equal(h.getElement('dashboardRetry').hidden, false);
    assert.match(h.getElement('dashboardStatus').textContent, /未能確認紀錄數量/);
    const retry = h.context.loadDashboardData();
    respond(h, 1, data());
    await retry;
    assert.equal(h.getElement('totalWarnings').textContent, '2');
    assert.equal(h.getElement('dashboardRetry').hidden, true);
});

test('refresh failure preserves real results and their original timestamp', async () => {
    const h = harness();
    const first = h.context.loadDashboardData();
    respond(h, 0, data());
    await first;
    const records = h.getElement('highScoreRecords').textContent;
    const refresh = h.context.loadDashboardData();
    h.requests[1].reject(new Error('offline'));
    await refresh;
    assert.equal(h.getElement('totalWarnings').textContent, '2');
    assert.equal(h.getElement('highScoreRecords').textContent, records);
    assert.match(h.getElement('dashboardStatus').textContent, /上次整理時間/);
    assert.match(h.getElement('dashboardStatus').textContent, /15:00/);
});

test('a late failure cannot replace a newer successful dashboard response', async () => {
    const h = harness();
    const older = h.context.loadDashboardData();
    const newer = h.context.loadDashboardData();
    respond(h, 1, data());
    await newer;
    h.requests[0].reject(new Error('old request'));
    await older;
    assert.match(h.getElement('dashboardStatus').textContent, /已載入/);
    assert.equal(h.getElement('dashboardRetry').hidden, true);
});

test('successful demo payloads are rejected instead of being displayed', async () => {
    const h = harness();
    const request = h.context.loadDashboardData();
    respond(h, 0, data({data_source: 'demo_data'}));
    await request;
    assert.equal(h.getElement('totalWarnings').textContent, '--');
    assert.equal(h.getElement('dashboardRetry').hidden, false);
});
