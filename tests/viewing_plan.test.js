const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const presentation = require('../static/prediction_presentation.js');

function window(day, type, time) {
    const event = new Date(`${day}T${time}:00+08:00`);
    return {event_type: type, event_at: event.toISOString(), method: 'astral',
        window_start: new Date(+event - 1800000).toISOString(), window_end: new Date(+event + 1800000).toISOString()};
}
function schedule() {
    return {today: {date: '2026-11-16'}, viewing_windows: [
        window('2026-11-16', 'sunrise', '06:35'), window('2026-11-16', 'sunset', '17:40'),
        window('2026-11-17', 'sunrise', '06:36'), window('2026-11-17', 'sunset', '17:39')]};
}
function at(time) {return new Date(`2026-11-16T${time}:00+08:00`);}
function predictionFor(selected, now, evaluated = selected.event_at) {
    return {burnsky_score: 95, data_quality: {status: 'limited', score_usable: true},
        prediction_timing: {event_type: selected.event_type, event_at: selected.event_at,
            evaluated_at: evaluated, generated_at: now.toISOString()}};
}

test('a night visit shows tomorrow sunrise and never promotes a nighttime score', () => {
    const now = at('23:00');
    const selected = presentation.getNextViewingWindow(schedule(), now);
    assert.equal(selected.event_type, 'sunrise');
    assert.match(selected.event_at, /2026-11-16T22:36/); // UTC, next Hong Kong morning
    const old = predictionFor(schedule().viewing_windows[1], now, now.toISOString());
    const plan = presentation.describeViewingPlan(schedule(), old, 'success', now);
    assert.match(plan.title, /下一次日出/);
    assert.match(plan.timeLabel, /17\/11\/2026/);
    assert.match(plan.status, /暫未有/);
    assert.match(plan.action, /東面/);
    assert.doesNotMatch(plan.status, /95|極佳|高機率/);
});

test('ongoing sunrise remains selected until its window ends, then switches to sunset', () => {
    assert.match(presentation.describeViewingPlan(schedule(), null, 'idle', at('06:50')).title, /進行中的日出/);
    assert.equal(presentation.getNextViewingWindow(schedule(), at('07:05')).event_type, 'sunrise');
    assert.equal(presentation.getNextViewingWindow(schedule(), at('07:06')).event_type, 'sunset');
    assert.match(presentation.describeViewingPlan(schedule(), null, 'idle', at('12:00')).action, /西面/);
});

test('nearest hourly selection stays within the actual solar window and includes longer horizons', () => {
    for (const now of [at('00:00'), at('12:00'), at('18:11'), at('23:00')]) {
        const plan = presentation.describeViewingPlan(schedule(), null, 'idle', now);
        assert.notEqual(plan.advanceHours, null);
        const evaluated = +now + plan.advanceHours * 3600000;
        assert.ok(evaluated >= Date.parse(plan.window.window_start) && evaluated <= Date.parse(plan.window.window_end));
    }
    assert.equal(presentation.describeViewingPlan(schedule(), null, 'idle', at('06:50')).advanceHours, 0);
});

test('timely but limited data stays limited even at a high score', () => {
    const now = at('16:40');
    const selected = presentation.getNextViewingWindow(schedule(), now);
    const plan = presentation.describeViewingPlan(schedule(), predictionFor(selected, now), 'success', now);
    assert.match(plan.status, /時段內條件參考，資料有限/);
    assert.match(plan.action, /未能判斷是否值得出發/);
    assert.doesNotMatch(plan.status + plan.action, /95|條件極佳|立即出發/);
});

test('wrong event, wrong evaluation time, expired data and unknown quality are not usable assessments', () => {
    const now = at('16:40');
    const selected = presentation.getNextViewingWindow(schedule(), now);
    const wrongEvent = predictionFor(schedule().viewing_windows[2], now);
    const wrongTime = predictionFor(selected, now, now.toISOString());
    const unknown = predictionFor(selected, now); delete unknown.data_quality;
    for (const data of [wrongEvent, wrongTime, unknown]) {
        assert.match(presentation.describeViewingPlan(schedule(), data, 'success', now).status, /暫未有/);
    }
    const stale = predictionFor(selected, at('16:00'));
    assert.match(presentation.describeViewingPlan(schedule(), stale, 'success', now).status, /已過時/);
});

test('failed weather assessment retains independently calculated viewing times', () => {
    const plan = presentation.describeViewingPlan(schedule(), null, 'error', at('12:00'), '缺少濕度資料');
    assert.match(plan.title, /下一次日落/);
    assert.match(plan.timeLabel, /17:10/);
    assert.match(plan.status, /未能取得：缺少濕度資料/);
    assert.match(plan.referenceNote, /不代表會出現燒天/);
});

test('missing, malformed and expired solar data never use invented seasonal times', () => {
    for (const data of [null, {}, {viewing_windows: [{event_type:'sunset', event_at:'invalid'}]}, schedule()]) {
        const now = data?.today ? new Date('2026-11-18T12:00:00+08:00') : at('12:00');
        const plan = presentation.describeViewingPlan(data, null, 'idle', now);
        assert.equal(plan.window, null);
        assert.match(plan.title, /未能確認/);
        assert.equal(plan.advanceHours, null);
    }
});

function controllerHarness(now = at('18:11')) {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    const start = html.indexOf('        let cachedSunTimes = null;');
    const end = html.indexOf('        function setPredictionStatus(', start);
    const elements = new Map();
    const calls = [];
    class Clock extends Date {constructor(value) {super(value === undefined ? +now : value);}}
    const context = {Date: Clock, BurnSkyPresentation: presentation, AbortController,
        console: {warn() {}}, setTimeout() {}, clearTimeout() {},
        document: {getElementById(id) {
            if (!elements.has(id)) elements.set(id, {textContent:'', value: '', disabled:false,
                options: ['0','1','2','3','6','12'].map(value => ({value})), appendChild(option) {this.options.push(option);}});
            return elements.get(id);
        }, createElement() {return {}; }},
        fetch: async () => ({ok: true, json: async () => schedule()}),
        loadPrediction: async () => {calls.push({type:elements.get('predictionType').value, hours:elements.get('advanceHours').value}); return true;}};
    vm.createContext(context);
    vm.runInContext(`let lastSuccessfulPrediction = null; let predictionSelectionChanged = false; ${html.slice(start,end)}`, context);
    return {context, elements, calls};
}

test('initial homepage selection targets tomorrow sunrise and creates a supported hourly option', async () => {
    const h = controllerHarness();
    await h.context.initAutoPredictionType();
    assert.equal(h.elements.get('predictionType').value, 'sunrise');
    assert.equal(h.elements.get('advanceHours').value, '12');
    assert.equal(await h.context.assessViewingWindow(), true);
    assert.equal(h.calls[0].type, 'sunrise');
    assert.match(h.elements.get('viewingPlanTitle').textContent, /下一次日出/);
});

test('one-click assessment adds a missing hour option and preserves manual selection during auto refresh', async () => {
    const h = controllerHarness(at('23:00'));
    await h.context.initAutoPredictionType();
    assert.equal(h.elements.get('advanceHours').value, '8');
    assert.ok(h.elements.get('advanceHours').options.some(option => option.value === '8'));
    await h.context.assessViewingWindow();
    h.elements.get('predictionType').value = 'sunset';
    await h.context.initAutoPredictionType();
    assert.equal(h.elements.get('predictionType').value, 'sunset');
});

test('solar failure exposes retry and does not issue a guessed viewing forecast', async () => {
    const h = controllerHarness();
    h.context.fetch = async () => {throw new Error('offline');};
    assert.equal(await h.context.assessViewingWindow(), false);
    assert.match(h.elements.get('viewingPlanTitle').textContent, /未能確認/);
    assert.equal(h.elements.get('viewingPlanButton').disabled, false);
    assert.deepEqual(h.calls, []);
});

test('the action card precedes score details and the detailed assessment is initially collapsed', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    assert.ok(html.indexOf('id="viewingPlan"') < html.indexOf('id="conditionScoreDetails"'));
    assert.match(html, /<details id="assessmentDetails"(?![^>]*\bopen\b)/);
    assert.match(html, /href="\/webcam-analysis"/);
    assert.match(html, /href="\/best-locations"/);
});
