const test = require('node:test');
const assert = require('node:assert/strict');
const {createController} = require('../static/forecast_verification.js');

function node(tag) {
    return {tag, children:[], textContent:'', style:{}, handlers:{},
        replaceChildren(){this.children=[];}, appendChild(n){this.children.push(n);},
        addEventListener(event, callback){this.handlers[event]=callback;}, setAttribute(){}, reportValidity(){return true;}};
}
function harness(fetch) {
    const nodes = {};
    const document = {getElementById:id=>nodes[id] ||= node(id), createElement:node};
    return {nodes, controller:createController(document, fetch)};
}
function text(n) { return n.textContent + ' ' + n.children.map(text).join(' '); }
function all(n) { return [n, ...n.children.flatMap(all)]; }
function report(records=[]) { return {status:'success', records, by_version:{}, note:'自報，未經核實。'}; }
function response(data) { return {ok:true, json:async()=>data}; }
function record(state='awaiting_report') {
    return {assessment_id:'a'.repeat(64), lead_minutes:179.5, state,
        prediction:{burnsky_score:71, scoring_method:'v1', prediction_timing:{event_type:'sunrise',
            event_at:'2026-11-19T06:40:00+08:00', generated_at:'2026-11-19T03:40:30+08:00',
            window_start:'2026-11-19T06:10:00+08:00', window_end:'2026-11-19T07:10:00+08:00'}}};
}

test('empty ledger never displays invented forecasts or an accuracy claim', async()=>{
    const h=harness(async()=>response(report())); await h.controller.load();
    assert.match(h.nodes.verificationStatus.textContent,/未有提前三小時/);
    assert.equal(h.nodes.verificationRecords.children.length,0);
});

test('pending event shows actual lead time and cannot solicit premature outcome', async()=>{
    const h=harness(async()=>response(report([record('awaiting_event')]))); await h.controller.load();
    assert.match(text(h.nodes.verificationRecords),/179.5 分鐘/);
    assert.match(text(h.nodes.verificationRecords),/等待目標時段結束/);
    assert.equal(all(h.nodes.verificationRecords).some(n=>n.tag==='form'),false);
});

test('manual outcome submits original snapshot and explicit Hong Kong observation time', async()=>{
    const calls=[];
    const h=harness(async(url, options)=>{
        calls.push({url,options});
        return response(options.method==='POST' ? {status:'success'} : report([record()]));
    });
    await h.controller.load();
    const elements=all(h.nodes.verificationRecords), form=elements.find(n=>n.tag==='form');
    elements.find(n=>n.tag==='select').value='strong';
    elements.find(n=>n.type==='datetime-local').value='2026-11-19T06:45';
    elements.find(n=>n.placeholder).value='西環海濱';
    elements.find(n=>n.type==='checkbox').checked=true;
    await form.handlers.submit({preventDefault(){}});
    const post=calls.find(c=>c.options.method==='POST');
    assert.match(post.url,new RegExp('a'.repeat(64)));
    const data=JSON.parse(post.options.body);
    assert.equal(data.observed_at,'2026-11-19T06:45+08:00');
    assert.equal(data.confirmed,true);
    assert.equal('predicted_score' in data,false);
});

test('self-reported location remains text and refresh failure preserves labeled record', async()=>{
    const r=record('reported'); r.outcome={result:'strong', location:'<script>test</script>', observed_at:'2026-11-19T06:45:00+08:00'};
    let fail=false;
    const h=harness(async()=>{if(fail)throw new Error('offline');return response(report([r]));});
    await h.controller.load(); fail=true; await h.controller.load();
    assert.match(text(h.nodes.verificationRecords),/<script>test<\/script>/);
    assert.match(text(h.nodes.verificationRecords),/未獨立核實/);
    assert.match(h.nodes.verificationStatus.textContent,/現有顯示可能過時/);
    assert.equal(h.nodes.verificationRefresh.disabled,false);
});

function stats(overrides={}) {
    return {forecasts:0, labeled:0, unsure:0, awaiting_event:0, awaiting_report:0,
        hits:0, false_alarms:0, misses:0, correct_negatives:0,
        predicted_positive:0, observed_positive:0,
        score_bands:[{label:'0–<45', forecasts:0, labeled:0, strong:0, weak_or_none:0,
            unsure:0, awaiting_event:0, awaiting_report:0}], ...overrides};
}

test('version details show separate event denominators and score-band counts safely', async()=>{
    const data=report([record()]);
    const sunrise=stats({forecasts:4, labeled:2, unsure:1, awaiting_report:1,
        hits:1, false_alarms:1, predicted_positive:2, observed_positive:1,
        score_bands:[{label:'<b>70–<85</b>', forecasts:4, labeled:2, strong:1, weak_or_none:1,
            unsure:1, awaiting_event:0, awaiting_report:1}]});
    data.by_version={'<script>v1</script>':stats({by_event:{sunrise, sunset:stats()}})};
    const h=harness(async()=>response(data)); await h.controller.load();
    const content=text(h.nodes.verificationSummary), elements=all(h.nodes.verificationSummary);
    assert.match(content, /<script>v1<\/script>/);
    assert.match(content, /高分但微弱／沒有：1\/2/);
    assert.match(content, /高分預測中自報明顯燒天：1\/2/);
    assert.match(content, /分類不符：1\/2/);
    assert.match(content, /明顯燒天但預測低分：0\/1/);
    assert.match(content, /時段已完待回報 1 次/);
    assert.match(content, /日出分數區間/);
    assert.match(content, /日落分數區間/);
    assert.match(content, /<b>70–<85<\/b>/);
    assert.match(content, /未有可判斷自報/);
    assert.doesNotMatch(content, /0\/0|NaN|undefined|100%/);
    assert.equal(elements.filter(n=>n.tag==='table').length,2);
    assert.equal(elements.some(n=>n.tag==='script'||n.tag==='b'),false);
    const cells=elements.filter(n=>n.tag==='tbody')[0].children[0].children.map(n=>n.textContent);
    assert.deepEqual(cells,['<b>70–<85</b>','4','2','1','1','1','1']);
});

test('unreported samples remain pending when event statistics refresh', async()=>{
    const data=report([record('awaiting_event')]);
    const pending=stats({forecasts:1, awaiting_event:1});
    data.by_version={v1:stats({...pending, by_event:{sunrise:pending, sunset:stats()}})};
    const h=harness(async()=>response(data)); await h.controller.load();
    const content=text(h.nodes.verificationSummary);
    assert.match(content,/可判斷自報 0 次/);
    assert.match(content,/等待時段結束 1 次/);
    assert.match(content,/未有可判斷自報/);
    assert.doesNotMatch(content,/0\/0|NaN|undefined/);
});
