const test = require('node:test');
const assert = require('node:assert/strict');
const {createController, describePrediction, validId} = require('../static/prediction_comparison.js');
const id1='a'.repeat(64), id2='b'.repeat(64);
function prediction(id=id1) {
    return {assessment_id:id, burnsky_score:60, prediction_timing:{event_type:'sunrise',
        generated_at:'2026-11-16T01:36:00+08:00', evaluated_at:'2026-11-16T06:36:00+08:00',
        window_start:'2026-11-16T06:06:00+08:00', window_end:'2026-11-16T07:06:00+08:00'}};
}
function node() { return {children:[], textContent:'', style:{}, replaceChildren(){this.children=[];},
    appendChild(n){this.children.push(n);}, addEventListener(){}}; }
function harness(fetch) {
    const nodes={};
    const values={};
    const storage={getItem:key=>values[key],setItem:(key,value)=>values[key]=value,removeItem:key=>delete values[key]};
    const document={getElementById:id=>nodes[id] ||= node(),createElement:node};
    return {nodes, values, controller:createController({document,storage,fetch,setTimer:()=>1,clearTimer(){}})};
}
function result(p=prediction(), observations=[]) {
    return {ok:true,json:async()=>({status:'success',prediction:p,observations,message:'尚未到目標時段'})};
}
function allText(n) { return n.textContent+' '+n.children.map(allText).join(' '); }

test('original evaluation has Hong Kong dates and stays separate from viewing time',()=>{
    const text=describePrediction(prediction()).join(' ');
    assert.match(text,/01:36/); assert.match(text,/06:36/); assert.match(text,/原評估產生/);
    assert.equal(validId(id1),true); assert.equal(validId('../path'),false);
});
test('pin keeps the original assessment when a newer score arrives and unpin follows latest',async()=>{
    const urls=[];
    const h=harness(async url=>{urls.push(url);return result();});
    h.controller.setPrediction(prediction()); h.controller.pin(); h.controller.setPrediction(prediction(id2));
    await h.controller.load(); assert.match(urls[0],new RegExp(id1));
    assert.ok(Object.values(h.values).includes(id1));
    h.controller.unpin(); await h.controller.load(); assert.match(urls[1],new RegExp(id2));
    assert.equal(Object.keys(h.values).length,0);
});
test('a late response cannot overwrite a newly selected assessment',async()=>{
    let resolve;
    const h=harness(()=>new Promise(done=>resolve=done));
    h.controller.setPrediction(prediction()); const loading=h.controller.load();
    h.controller.setPrediction(prediction(id2)); resolve(result()); await loading;
    assert.match(h.nodes.comparisonStatus.textContent,/已選定/);
    assert.equal(h.nodes.comparisonObservations.children.length,0);
});
test('refresh failure retains original observation and time, first failure is explicit',async()=>{
    let fail=false;
    const observation={location:'測試',direction:'East',source:'天文台',aligned_reference:true,
        source_updated_at:'2026-11-16T06:30:00+08:00',analyzed_at:'2026-11-16T06:36:00+08:00',description:'影像參考',note:'非準確率'};
    const h=harness(async()=>{if(fail)throw new Error('offline');return result(prediction(),[observation]);});
    h.controller.setPrediction(prediction()); await h.controller.load(); fail=true; await h.controller.load();
    assert.match(h.nodes.comparisonStatus.textContent,/保留上次實況/);
    assert.match(allText(h.nodes.comparisonObservations),/06:30/);
    h.controller.setPrediction(prediction(id2));await h.controller.load();
    assert.match(h.nodes.comparisonStatus.textContent,/未能載入/);
    assert.equal(h.nodes.comparisonObservations.children.length,0);
});
test('render inserts camera text safely and rejects external image URLs',async()=>{
    const h=harness(async()=>result(prediction(),[{location:'<script>bad</script>',direction:'East',source:'HKO',
        image_data_url:'https://example.com/tracker.jpg',description:'test',note:'test'}]));
    h.controller.setPrediction(prediction());await h.controller.load();
    assert.match(allText(h.nodes.comparisonObservations),/<script>bad<\/script>/);
    assert.equal(h.nodes.comparisonObservations.children[0].children.some(n=>n.src),false);
});
test('missing snapshot does not issue a guessed comparison request',async()=>{
    let calls=0;const h=harness(async()=>{calls++;return result();});
    h.controller.setPrediction({...prediction(),assessment_id:null});await h.controller.load();
    assert.equal(calls,0);assert.match(h.nodes.comparisonStatus.textContent,/未有已保存/);
});
