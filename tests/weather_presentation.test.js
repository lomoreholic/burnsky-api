const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { formatHongKongDateTime } = require('../static/prediction_presentation.js');
const html = fs.readFileSync(path.join(__dirname, '../templates/index.html'), 'utf8');
const script = html.slice(html.indexOf('        function appendWeatherCard('), html.indexOf('        function updateAnalysisSummary('));

function node() {
    return {children: [], style: {}, _text: '',
        set textContent(value) {this._text = String(value); this.children = [];},
        get textContent() {return this._text + this.children.map(child => child.textContent).join('\n');},
        append(...items) {this.children.push(...items);},
        appendChild(item) {this.children.push(item);},
        replaceChildren() {this.children = []; this._text = '';}
    };
}
function harness() {
    const elements = {weatherData: node(), weatherSourceSummary: node()};
    const context = {document: {getElementById: id => elements[id], createElement: node},
        BurnSkyPresentation: {formatHongKongDateTime}, getWeatherIconDescription: code => '天氣代碼' + code};
    vm.createContext(context);
    vm.runInContext(script, context);
    return {context, elements};
}

test('a factor score without measurements cannot turn into AQHI4 and PM2.5 25', () => {
    const h = harness();
    h.context.updateAirQualityData({score: 5, max_score: 15});
    const text = h.elements.weatherData.textContent;
    assert.match(text, /暫缺資料/);
    assert.match(text, /因子分數並非AQHI/);
    assert.doesNotMatch(text, /AQHI 4|PM2.5|25|空氣品質一般|良好燒天/);
});

test('estimates remain visibly estimated and missing PM2.5 stays missing', () => {
    const h = harness();
    h.context.updateAirQualityData({source_kind: 'estimated', aqhi: 4, pm25: null, source: '天氣估算'});
    const text = h.elements.weatherData.textContent;
    assert.match(text, /模型估算/);
    assert.doesNotMatch(text, /官方觀測|PM2.5/);
});

test('zero readings stay visible with their source and actual observation time', () => {
    const h = harness();
    h.context.updateWeatherData({}, {summary: '觀測資料', cards: [{key: 'uvindex', label: 'UV指數',
        value: 0, source_kind: 'observed', source: '香港天文台', updated_at: '2026-11-14T07:00:00Z'}]});
    const text = h.elements.weatherData.textContent;
    assert.match(text, /UV指數\n0/);
    assert.match(text, /官方觀測/);
    assert.match(text, /15:00/);
    assert.doesNotMatch(text, /夜間/);
});

test('refresh clears old cards and missing provenance never becomes official data', () => {
    const h = harness();
    h.context.updateWeatherData({}, {summary: '推算', cards: [{label: '溫度', value: 27,
        source_kind: 'estimated', valid_at: '2026-11-14T17:00:00+08:00'}]});
    assert.match(h.elements.weatherData.textContent, /模型估算/);
    assert.match(h.elements.weatherData.textContent, /17:00/);
    h.context.updateWeatherData({temperature: 25});
    assert.equal(h.elements.weatherData.children.length, 0);
    assert.match(h.elements.weatherSourceSummary.textContent, /未取得可確認來源/);
});

test('wind forecast date is shown as a day and source text is inserted as plain text', () => {
    const h = harness();
    h.context.appendWeatherCard({key: 'wind', label: '風力預報', value: '東風4級',
        source_kind: 'forecast', valid_at: '20261114', source: '<img src=x onerror=alert(1)>'});
    const text = h.elements.weatherData.textContent;
    assert.match(text, /官方每日預報/);
    assert.match(text, /2026-11-14/);
    assert.equal(h.elements.weatherData.children[0].children[2].children.length, 0);
    assert.match(text, /<img/);
});
