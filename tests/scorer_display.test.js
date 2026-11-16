const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync('templates/index.html', 'utf8');
const source = html.slice(html.indexOf('        function updateAnalysisFactors('), html.indexOf('        // 香港天文台天氣圖標代碼對照表'));

function render(details) {
    const cards = [];
    const grid = {innerHTML: '', appendChild: card => cards.push(card)};
    const scope = {document: {getElementById: () => grid, createElement: () => ({style: {}, addEventListener() {}})},
        window: {innerWidth: 1200}, console, loadCrossCheckData() {}};
    vm.createContext(scope);
    vm.runInContext(source, scope);
    scope.updateAnalysisFactors(details);
    return cards.map(card => card.innerHTML).join('\n');
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

test('a real zero factor and zero visibility remain zero', () => {
    const result = render({uv_factor: {score: 0, max_score: 2, description: '實測'},
        cloud_visibility_analysis: {technical_details: {combined_score: 0}, color_visibility_percentage: 0}});
    assert.match(result, /0\/2分/);
    assert.match(result, /0\/100分/);
    assert.doesNotMatch(result, /50\/100/);
});
