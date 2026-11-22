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

test('a usable three-hour forecast gives planning advice and labels its confidence', () => {
    const now = at('14:40');
    const selected = presentation.getNextViewingWindow(schedule(), now);
    const plan = presentation.describeViewingPlan(schedule(), predictionFor(selected, now), 'success', now);
    assert.equal(plan.advanceHours, 3);
    assert.match(plan.status, /95.*可信度較低/);
    assert.match(plan.action, /安排|準備/);
    assert.doesNotMatch(plan.action, /未能判斷是否值得出發|立即出發/);
});

test('outside the short-term horizon the plan says when the three-hour forecast starts', () => {
    const plan = presentation.describeViewingPlan(schedule(), null, 'idle', at('12:00'));
    assert.match(plan.action, /14:40.*3小時/);
});

test('missing factors crossing an advice threshold do not become a bad-weather verdict', () => {
    const now = at('14:40');
    const selected = presentation.getNextViewingWindow(schedule(), now);
    const data = predictionFor(selected, now);
    data.burnsky_score = 36;
    data.score_sensitivity = {kind:'missing_factor_scenarios', lower:36, upper:54,
        weighted_coverage_percent:82, missing_factors:['pressure', 'uv', 'air_quality']};
    const plan = presentation.describeViewingPlan(schedule(), data, 'success', now);
    assert.match(plan.action, /未足以單憑低分/);
    assert.doesNotMatch(plan.action, /不建議專程/);
    assert.match(presentation.describeScoreCoverage(data), /36.0–54.0/);
    assert.match(presentation.describeScoreCoverage(data), /不是機率、可信區間/);
    data.score_sensitivity.upper = 40;
    assert.match(presentation.describeViewingPlan(schedule(), data, 'success', now).action, /目前條件偏低/);
    delete data.score_sensitivity;
    data.data_quality.input_coverage = {missing_factors:['pressure']};
    assert.match(presentation.describeViewingPlan(schedule(), data, 'success', now).action, /未足以單憑低分/);
    assert.match(presentation.describeScoreCoverage(data), /未提供/);
});

test('invalid sensitivity is never displayed as a numeric range', () => {
    for (const range of [{}, {kind:'missing_factor_scenarios', lower:20, upper:110,
        weighted_coverage_percent:80, missing_factors:[]}]) {
        assert.match(presentation.describeScoreCoverage({burnsky_score:20, score_sensitivity:range}), /未提供/);
    }
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
            if (!elements.has(id)) elements.set(id, {textContent:'', value: '', disabled:false, style: {},
                attributes: {}, setAttribute(key, value) {this.attributes[key] = value;},
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

test('matching plan folds duplicate advice but restores it for other times, stale data and failures', async () => {
    const now = at('14:40');
    const h = controllerHarness(now);
    await h.context.initAutoPredictionType();
    const selected = presentation.getNextViewingWindow(schedule(), now);
    const data = predictionFor(selected, now);
    data.advance_hours = 3;
    data.sun_times = {};
    Object.assign(data.prediction_timing, {window_start: selected.window_start,
        window_end: selected.window_end, mode: 'forecast'});
    h.context.assessmentData = data;
    vm.runInContext("lastSuccessfulPrediction = {data: assessmentData}; viewingAssessmentState = 'success'; updateViewingPlan();", h.context);
    assert.equal(h.elements.get('assessmentNextStep').hidden, true);
    assert.equal(h.elements.get('eventReference').hidden, true);
    assert.equal(h.elements.get('conditionScoreDetails').open, false);
    assert.equal(h.elements.get('conditionScoreToggle').hidden, false);
    assert.equal(h.elements.get('sunCountdownContainer').style.display, 'none');
    assert.match(h.elements.get('assessmentHeadline').textContent, /計分依據/);
    assert.equal(h.elements.get('viewingPlanScore').hidden, false);
    assert.equal(h.elements.get('viewingPlanScoreValue').textContent, '95');
    assert.equal(h.elements.get('viewingPlanScore').attributes['aria-valuenow'], '95');
    data.burnsky_score = 0;
    h.context.updateViewingPlan();
    assert.equal(h.elements.get('viewingPlanScore').hidden, false);
    assert.equal(h.elements.get('viewingPlanScoreValue').textContent, '0');
    assert.equal(h.elements.get('viewingPlanScoreArc').attributes['stroke-dasharray'], '0 100');

    data.prediction_timing.evaluated_at = now.toISOString();
    h.context.updateViewingPlan();
    assert.equal(h.elements.get('assessmentNextStep').hidden, false);
    assert.match(h.elements.get('assessmentNextStep').textContent, /調整/);
    assert.equal(h.elements.get('viewingPlanScore').hidden, true);
    assert.equal(h.elements.get('sunCountdownContainer').style.display, 'block');

    data.prediction_timing.evaluated_at = selected.event_at;
    data.prediction_timing.generated_at = at('14:00').toISOString();
    h.context.updateViewingPlan();
    assert.equal(h.elements.get('assessmentNextStep').hidden, false);
    assert.match(h.elements.get('assessmentHeadline').textContent, /過時/);
    assert.equal(h.elements.get('viewingPlanScore').hidden, true);

    data.prediction_timing.generated_at = now.toISOString();
    vm.runInContext("viewingAssessmentState = 'error'; updateViewingPlan();", h.context);
    assert.equal(h.elements.get('assessmentNextStep').hidden, false);
    assert.match(h.elements.get('viewingPlanStatus').textContent, /未能取得/);
    assert.equal(h.elements.get('viewingPlanScore').hidden, true);
    vm.runInContext("viewingAssessmentState = 'success'; updateViewingPlan();", h.context);
    assert.equal(h.elements.get('assessmentNextStep').hidden, true);
});

test('the action card precedes score details and the detailed assessment is initially collapsed', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    assert.ok(html.indexOf('id="viewingPlan"') < html.indexOf('id="conditionScoreDetails"'));
    assert.match(html, /<details id="assessmentDetails"(?![^>]*\bopen\b)/);
    assert.match(html, /href="\/webcam-analysis"/);
    assert.match(html, /href="\/best-locations"/);
});
