(function (root) {
    'use strict';
            const factors = {
                'time_factor': {
                    name: '評估時間因子',
                    icon: '🌅',
                    maxScore: 18,
                    explanation: '基於真實日出/日落時間評分（12%權重）：黃金30分鐘內（15-18分）、1小時內（12分）、2小時內（8分）、其他時段（4分）'
                },
                'temperature_factor': {
                    name: '溫度因子',
                    icon: '🌡️',
                    maxScore: 15,
                    explanation: '影響燒天顏色飽和度（10%權重）：理想26-31°C（15分）、良好24-33°C（12分）、可接受20-35°C（7分）、邊緣15-38°C（3分）'
                },
                'humidity_factor': {
                    name: '濕度因子',
                    icon: '💧',
                    maxScore: 20,
                    explanation: '影響大氣層顏色（13.3%權重）：理想55-70%（20分）、良好50-75%（16分）、可接受45-80%（12分）、邊緣40-85%（7分）、極端<40%或>85%（3分）'
                },
                'visibility_factor': {
                    name: '降雨／能見度遮擋參考',
                    icon: '👁️',
                    maxScore: 20,
                    explanation: '影響拍攝清晰度（13.3%權重）：無降雨（20分）、極輕微<2mm（15分）、輕微<5mm（10分）、中度<10mm（6分）、大雨<20mm（3分）、暴雨≥20mm（1分）'
                },
                'cloud_analysis_factor': {
                    name: '雲層分析因子',
                    icon: '☁️',
                    maxScore: 35,
                    explanation: '佔總分23.3%。優先使用目標時段分層雲量；中高雲覆蓋適中較有利，低雲遮擋降低分數。晨昏時額外參考太陽方向50及100公里低雲，兩點齊全才套用方向扣分。尚未包含雲厚或地形遮擋；未經實拍校準。'
                },
                'uv_factor': {
                    name: 'UV指數因子',
                    icon: '☀️',
                    maxScore: 2,
                    explanation: '僅供參考（1.3%權重）：UV≥5（2分）、3-4（1.5分）、1-2（1分）、<1（0.5分）。UV不是燒天決定性因素，僅作為陽光強度參考'
                },
                'wind_factor': {
                    name: '風速因子',
                    icon: '💨',
                    maxScore: 15,
                    explanation: '影響雲層擴散（10%權重）：理想6-12km/h（15分）、良好4-16km/h（12分）、可接受2-20km/h（9分）、偏大≤25km/h（5分）、強風≤30km/h（2分）、烈風>30km/h（1分）。適度風速有助雲層形態變化'
                },
                'pressure_factor': {
                    name: '氣壓因子', icon: '📈', maxScore: 10,
                    explanation: '只使用可用氣壓讀數；缺失時不參與計分。'
                },
                'air_quality_factor': {
                    name: '空氣品質因子',
                    icon: '🌫️',
                    maxScore: 15,
                    explanation: '影響色彩清晰度（10%權重）：優良AQHI≤3（15分）、良好≤6（12分）、一般≤7（8分）、不佳≤10（5分）、極差>10（2分）。空氣越清澈，燒天色彩越鮮豔'
                }
            };

    function escape(value) {
        return String(value ?? '').replace(/[&<>"']/g, char => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[char]));
    }

    function model(details) {
        if (!details || Array.isArray(details) || typeof details !== 'object') return null;
        const entries = Object.entries(factors).map(([key, config]) => {
            const value = details[key] || {};
            const max = Number.isFinite(value.max_score) && value.max_score > 0 ? value.max_score : config.maxScore;
            const score = Number.isFinite(value.score) && value.score >= 0 && value.score <= max ? value.score : null;
            return {key, ...config, max, score, description: value.description || '未取得可用計分資料。'};
        });
        const available = entries.filter(entry => entry.score !== null);
        return {
            entries,
            // Order by original points lost/gained, not by incomparable raw scores.
            negative: available.filter(entry => entry.score / entry.max <= .4)
                .sort((a, b) => (b.max - b.score) - (a.max - a.score)).slice(0, 3),
            positive: available.filter(entry => entry.score / entry.max >= .8)
                .sort((a, b) => b.score - a.score).slice(0, 2),
            missing: entries.filter(entry => entry.score === null),
            breakdown: details.score_breakdown || {}
        };
    }

    function present(details) {
        const data = model(details);
        if (!data) return {summary: '<p>暫未取得主要因素，請更新評估。</p>', details: '<p>暫無計分詳情。</p>'};
        const rows = [];
        const negativeNotes = {
            cloud_analysis_factor: '雲層組合按規則取得較少分；出發前需核對天空實況。',
            humidity_factor: '濕度未落於現有規則較有利的範圍。',
            temperature_factor: '溫度未落於現有規則較有利的範圍。',
            wind_factor: '風速偏離現有規則較有利的範圍。',
            time_factor: '評估時間的晨昏條件評分偏低；請核對所選時段。',
            visibility_factor: '降雨／遮擋參考取得較少分；請核對預報雨量及天空實況。'
        };
        for (const entry of data.negative) {
            rows.push(`<li class="factor-impact negative"><strong>⚠️ 較不利 · ${escape(entry.name)}</strong><p>${escape(negativeNotes[entry.key] || '按現有規則，這項因素取得較少分數。')}</p></li>`);
        }
        for (const entry of data.positive) {
            const note = entry.key === 'visibility_factor' ? '降雨遮擋計分較有利；無雨亦不代表能見度良好。' : '按現有規則，這項因素取得較多分數。';
            rows.push(`<li class="factor-impact positive"><strong>✅ 較有利 · ${escape(entry.name)}</strong><p>${note}</p></li>`);
        }
        if (data.missing.length) {
            rows.push(`<li class="factor-impact missing"><strong>ℹ️ 未參與計分</strong><p>${escape(data.missing.map(entry => entry.name.replace('因子', '')).join('、'))}缺少可用計分資料；沒有補預設分。低分亦可能受缺失資料影響。</p></li>`);
        }
        if (!data.positive.length && !data.negative.length && data.missing.length < data.entries.length) {
            rows.unshift('<li class="factor-impact"><p>現有可用因子未有明顯偏高或偏低的規則評分；請查看計分詳情。</p></li>');
        }
        const breakdown = data.breakdown;
        const points = value => Number.isFinite(value) ? `${escape(Math.round(value * 10) / 10)}分` : '未提供';
        let detailHTML = `<div class="factor-breakdown"><h3>條件評分組成</h3><p>傳統算法: ${points(breakdown.traditional_normalized ?? breakdown.traditional_score)}<br>機器學習: ${Number.isFinite(breakdown.ml_score) ? points(breakdown.ml_score) : '未參與'}<br>加權結果: ${points(breakdown.final_weighted_score)}</p><p>因子權重覆蓋：${Number.isFinite(breakdown.input_coverage?.weighted_percent) ? escape(breakdown.input_coverage.weighted_percent) + '%' : '未提供'}。缺失因子不補分。</p><p>各因子原始滿分不同，原始滿分合計150；總分經換算及調整，不能直接將下面分數當成／100的貢獻相加。</p>${breakdown.weight_explanation ? `<p>${escape(breakdown.weight_explanation)}</p>` : ''}${breakdown.ml_unavailable_reason ? `<p>${escape(breakdown.ml_unavailable_reason)}</p>` : ''}</div>`;
        for (const entry of data.entries) {
            detailHTML += `<article class="factor-detail"><div class="factor-detail-heading"><h3>${entry.icon} ${escape(entry.name)}</h3><strong>${entry.score === null ? '未參與' : escape(entry.score) + '/' + escape(entry.max) + '分'}</strong></div><p>${escape(entry.description)}</p><details><summary>查看此因子計分規則</summary><p>${escape(entry.explanation)}。屬現有規則設定，尚未經實拍校準。</p></details></article>`;
        }
        return {summary: `<ul class="factor-impact-list">${rows.join('')}</ul>`, details: detailHTML};
    }

    const api = {model, present};
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.BurnSkyFactors = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
