const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const presentation = require('../static/factor_presentation.js');
const html = fs.readFileSync('templates/index.html', 'utf8');
const source = html.slice(html.indexOf('        function updateAnalysisFactors('), html.indexOf('        // 香港天文台天氣圖標代碼對照表'));

function render(details) {
    const grid = {innerHTML: ''};
    const summary = {innerHTML: ''};
    const scope = {document: {getElementById: id => id === 'analysisGrid' ? grid : summary}, BurnSkyFactors: presentation};
    vm.createContext(scope);
    vm.runInContext(source, scope);
    scope.updateAnalysisFactors(details);
    return grid.innerHTML;
}

test('missing factor and ML scores display unavailable without inventing zero or 50', () => {
    const result = render({score_breakdown: {traditional_normalized: 0, traditional_score: 50,
        final_weighted_score: 0, ml_score: null, input_coverage: {weighted_percent: 72}},
        uv_factor: {score: null, max_score: 2, description: '資料不足'}, cloud_visibility_analysis: {}});
    assert.match(result, /傳統算法: 0分/);
    assert.match(result, /機器學習: 未參與/);
    assert.match(result, /因子權重覆蓋：72%/);
    assert.doesNotMatch(result, /null\/2|0\/2|50\/100|顏色可見度/);
});

test('a real zero factor remains zero and unsupported visibility analysis is omitted', () => {
    const result = render({uv_factor: {score: 0, max_score: 2, description: '實測'},
        cloud_visibility_analysis: {technical_details: {combined_score: 0}, color_visibility_percentage: 0}});
    assert.match(result, /0\/2分/);
    assert.doesNotMatch(result, /顏色可見度|0\/100分|50\/100/);
});

test('missing scores do not become unfavourable weather and all-missing input is explicit', () => {
    const result = presentation.present({humidity_factor: {score: null}, pressure_factor: {score: '0'}});
    assert.match(result.summary, /未參與計分/);
    assert.doesNotMatch(result.summary, /較不利|較有利|未有明顯/);
    assert.doesNotMatch(result.details, /傳統算法: 0分|加權結果: 0分/);
});

test('summary ranks different factor scales by original points lost and keeps rainfall caveat', () => {
    const result = presentation.model({cloud_analysis_factor: {score: 1, max_score: 35},
        humidity_factor: {score: 3, max_score: 20}, wind_factor: {score: 1, max_score: 15},
        uv_factor: {score: 0, max_score: 2}, visibility_factor: {score: 20, max_score: 20}});
    assert.deepEqual(result.negative.map(entry => entry.key), ['cloud_analysis_factor', 'humidity_factor', 'wind_factor']);
    const html = presentation.present({visibility_factor: {score: 20, max_score: 20}}).summary;
    assert.match(html, /無雨亦不代表能見度良好/);
    assert.doesNotMatch(html, /20\/20/);
});

test('backend descriptions are escaped and speculative intensity and ML cards are not displayed', () => {
    const result = render({humidity_factor: {score: 3, description: '<img src=x onerror=alert(1)>'},
        burnsky_intensity: {duration: '0-10分鐘'}, ml_prediction: {ml_burnsky_score: 90}});
    assert.match(result, /&lt;img/);
    assert.doesNotMatch(result, /<img|0-10分鐘|90分|燒天程度預測|不建議專程/);
});

test('invalid input clears old explanations and medium scores do not invent a strong effect', () => {
    assert.match(presentation.present(null).summary, /暫未取得/);
    assert.match(presentation.present({humidity_factor: {score: 12, max_score: 20}}).summary, /未有明顯偏高或偏低/);
    assert.equal(presentation.model({humidity_factor: {score: 21, max_score: 20}}).entries.find(entry => entry.key === 'humidity_factor').score, null);
});

test('latest AQHI observation is distinguished from a missing target forecast', () => {
    const result = presentation.present({air_quality_factor: {score: null,
        source_kind: 'observation_reference', description: 'AQHI 4，最新監測只作參考'}});
    assert.match(result.summary, /空氣品質已取得最新監測/);
    assert.match(result.summary, /缺少目標時段預報/);
    assert.doesNotMatch(result.summary, /空氣品質缺少可用計分資料/);
    assert.match(result.details, /AQHI 4/);
});
