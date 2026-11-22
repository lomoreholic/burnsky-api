const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { formatHongKongDateTime } = require('../static/prediction_presentation.js');
const html = fs.readFileSync(path.join(__dirname, '../templates/index.html'), 'utf8');
const script = html.slice(html.indexOf('        function appendWeatherCard('), html.indexOf('        function updateAnalysisSummary('));

test('hourly cloud forecast is distinct from observations and daily forecasts', () => {
    const h = harness();
    h.context.updateWeatherData({}, {summary: '分層雲量', cloud_attribution: {source: 'MET Norway'},
        cards: [{key: 'cloud_low', label: '低層雲量預報', value: 0, unit: '%',
            source_kind: 'hourly_forecast', source: 'MET Norway', valid_at: '2026-11-18T17:00:00+08:00'}]});
    assert.match(h.elements.weatherData.textContent, /逐小時模式預報/);
    assert.match(h.elements.weatherData.textContent, /0%/);
    assert.doesNotMatch(h.elements.weatherData.textContent, /官方觀測|官方每日預報/);
    assert.match(h.elements.weatherSourceSummary.textContent, /MET Norway/);
    assert.match(h.elements.weatherSourceSummary.textContent, /CC BY 4.0/);
});

test('solar geometry is calculated and a missing sunward sample never renders zero', () => {
    const h = harness();
    h.context.updateWeatherData({}, {summary: '取樣未齊，沒有當作光路暢通', cards: [
        {key: 'solar_azimuth_deg', label: '太陽方位角', value: 250, unit: '°', source_kind: 'calculated',
            source: 'Astral 天文計算', valid_at: '2026-11-18T17:30:00+08:00'},
        {key: 'sunward_low_100', label: '太陽方向約100公里低雲', value: null, unit: '%', source_kind: 'unavailable'}]});
    assert.match(h.elements.weatherData.textContent, /天文計算/);
    assert.match(h.elements.weatherData.textContent, /計算適用：.*17:30/);
    assert.doesNotMatch(h.elements.weatherData.textContent, /官方觀測|官方每日預報/);
    assert.equal(h.elements.weatherData.children[1].children[1].textContent, '--');
});

test('hourly rainfall displays its full accumulation interval without becoming an observation', () => {
    const h = harness();
    h.context.updateWeatherData({}, {summary:'逐小時雨量', cards:[{key:'rainfall', label:'一小時預報雨量', value:0,
        unit:'mm', source_kind:'hourly_forecast', source:'MET Norway', updated_at:'2026-11-18T21:00:00+08:00',
        valid_at:'2026-11-19T06:30:00+08:00', period_start:'2026-11-19T06:00:00+08:00',
        period_end:'2026-11-19T07:00:00+08:00', note:'並非能見度預報。'}]});
    const text=h.elements.weatherData.textContent;
    assert.match(text,/0mm/); assert.match(text,/累積區間：.*06:00.*07:00/);
    assert.match(text,/逐小時模式預報/); assert.doesNotMatch(text,/官方觀測/);
});

test('visibility keeps its station and observed time instead of a future valid time', () => {
    const h = harness();
    h.context.updateWeatherData({}, {cards:[{key:'visibility_Central', label:'十分鐘平均能見度',
        value:0, unit:'km', station:'中環', source:'香港天文台', source_kind:'observed',
        updated_at:'2026-11-19T17:10:00+08:00', valid_at:null,
        note:'現有觀測，並非目標時段能見度預報；未用作未來分數扣分。'}]});
    const text = h.elements.weatherData.textContent;
    assert.match(text, /0km/);
    assert.match(text, /中環/);
    assert.match(text, /17:10/);
    assert.match(text, /未用作未來分數扣分/);
    assert.doesNotMatch(text, /逐小時模式預報|適用：/);
});

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

test('official observation cards are not duplicated by the legacy factor fallback', () => {
    const h = harness();
    const presentation = {cards:[{key:'aqhi', label:'現時AQHI', value:4, source_kind:'observed',
        source:'環境保護署', updated_at:'2026-11-23T00:00:00+08:00'}]};
    h.context.updateWeatherData({}, presentation);
    h.context.updateAirQualityData({score:null, source_kind:'observation_reference', aqhi:4}, presentation);
    assert.equal(h.elements.weatherData.children.length, 1);
    assert.doesNotMatch(h.elements.weatherData.textContent, /暫缺資料/);
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
