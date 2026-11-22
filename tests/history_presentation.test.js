const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {createController} = require('../static/history_presentation.js');
function node(tag) {
    return {tag, textContent:'', children:[], handlers:{},
        replaceChildren(){this.children=[];}, appendChild(child){this.children.push(child);},
        setAttribute(){}, addEventListener(event, handler){this.handlers[event]=handler;}};
}
function harness(fetch) {
    const nodes = {};
    const document = {getElementById:id => nodes[id] ||= node(id), createElement:node};
    document.getElementById('historyDays').value = '30';
    document.getElementById('historyResult');
    return {nodes, controller:createController(document, fetch)};
}
function text(node) { return node.textContent + ' ' + node.children.map(text).join(' '); }
function report(overrides={}) {
    return {status:'success', data_source:'prediction_history', time_basis:'prediction_generated_at_hong_kong',
        time_range:{days:30, start_date:'2026-10-24', end_date:'2026-11-23'},
        summary:{total_predictions:0, avg_score:0, high_score_count:0, medium_score_count:0, low_score_count:0, high_score_prediction_rate:0},
        verified_accuracy:{has_data:false}, by_type:{}, daily_trends:[], best_hours:[], ...overrides};
}
const response = data => ({ok:true, json:async()=>data});
test('homepage keeps three-hour verification and moves historical statistics to a linked page', () => {
    const html = fs.readFileSync('templates/index.html', 'utf8');
    assert.match(html, /id="verificationSection"/);
    assert.match(html, /href="\/prediction-history"/);
    assert.doesNotMatch(html, /id="burnskyHistorySection"|loadBurnskyOverview|refreshOpenBurnskyHistory|真實準確率/);
});
test('empty history shows a real zero without inventing accuracy or shooting recommendations', async()=>{
    const h = harness(async()=>response(report())); await h.controller.load();
    assert.match(text(h.nodes.historyResult), /0 次預測紀錄/);
    assert.match(text(h.nodes.historyResult), /暫無可用自報評分/);
    assert.doesNotMatch(text(h.nodes.historyResult), /100%|最佳拍攝/);
});
test('first request failure leaves statistics unknown and retry enabled', async()=>{
    const h = harness(async()=>{throw new Error('offline');}); await h.controller.load();
    assert.match(h.nodes.historyStatus.textContent, /數值未知/);
    assert.equal(h.nodes.historyResult.children.length, 0);
    assert.equal(h.nodes.historyRefresh.disabled, false);
});
test('refresh failure retains the original period and successful records', async()=>{
    let fail = false;
    const h = harness(async()=>{if(fail)throw new Error('offline'); return response(report());});
    await h.controller.load(); fail = true; h.nodes.historyDays.value='7'; await h.controller.load();
    assert.match(text(h.nodes.historyResult), /最近 30 天/);
    assert.match(h.nodes.historyStatus.textContent, /保留上次結果/);
});
test('malformed or mismatched refresh does not replace the last successful period', async()=>{
    let data = report();
    const h = harness(async()=>response(data));
    await h.controller.load();
    data = report({daily_trends:[null]}); await h.controller.load();
    assert.match(text(h.nodes.historyResult), /最近 30 天/);
    assert.match(h.nodes.historyStatus.textContent, /保留上次結果/);
    data = report(); h.nodes.historyDays.value='7'; await h.controller.load();
    assert.match(h.nodes.historyStatus.textContent, /保留上次結果/);
});
test('numeric feedback reports absolute error and source counts instead of a manufactured accuracy', async()=>{
    const h = harness(async()=>response(report({verified_accuracy:{has_data:true, feedback_count:2,
        avg_error:12, accuracy:88, manual_verified_count:1, photo_verified_count:1}})));
    await h.controller.load();
    const output=text(h.nodes.historyResult);
    assert.match(output, /平均絕對評分誤差 12 分/);
    assert.match(output, /手動回報 1 筆、相片輔助回報 1 筆/);
    assert.doesNotMatch(output, /88%|準確率.*88/);
});
test('dates remain text and generation-hour groups do not become shooting advice', async()=>{
    const data=report({summary:{total_predictions:1, avg_score:90, high_score_count:1, medium_score_count:0, low_score_count:0, high_score_prediction_rate:100},
        daily_trends:[{date:'<script>alert(1)</script>', avg_score:90, max_score:90, high_score_count:1}],
        best_hours:[{hour:0, count:1, avg_score:90}]});
    const h=harness(async()=>response(data)); await h.controller.load();
    const output=text(h.nodes.historyResult);
    assert.match(output, /<script>alert\(1\)<\/script>/);
    assert.match(output, /不是預測目標時間/);
    assert.match(output, /0:00/);
});
