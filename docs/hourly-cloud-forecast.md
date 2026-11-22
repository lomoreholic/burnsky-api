# Hourly cloud and target-weather inputs

BurnSky now prefers MET Norway Locationforecast **complete** hourly total,
low, medium and high cloud area fractions at the Hong Kong reference point
22.30°N, 114.17°E. These are regional model forecasts, not camera observations
or a forecast for each shooting location. The compact API omits cloud layers.

Data from [MET Norway](https://api.met.no/weatherapi/locationforecast/2.0/documentation),
licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
BurnSky interpolates time samples and derives its own heuristic condition score.
Read the provider's [terms](https://api.met.no/doc/TermsOfService) before deployment.

## Time alignment and outages

- The requested time is preparation time plus the selected advance hours,
  including the three-hour horizon. This does not automatically select sunset.
- Use exact hourly values or linear interpolation between two records at most
  one hour apart. Never extrapolate or bridge missing hours.
- Require all four percentages to be finite numbers in 0–100; missing is not zero.
- Reject model issue times older than 18 hours or more than 15 minutes ahead
  of the server clock. These limits are operational assumptions, not accuracy guarantees.
- Keep issue time, retrieval time, source sample times, evaluated time, coordinates,
  source and license in the response.
- The backend shares an in-memory cache, observes Expires and Retry-After,
  sends If-Modified-Since and backs off at least 15 minutes after failures.
- When the provider is unavailable, validate any cached model before using it.
  Otherwise retain HKO text cloud scoring and show the limitation. This does not
  block otherwise usable HKO inputs or change the notification policy.

## Initial cloud scoring rule

Only the cloud factor (maximum 35 of the existing 150 raw points) changes.
The following constants are uncalibrated assumptions:

1. `canvas = min(total, max(medium, high)) / 100`. Layers overlap, so do not sum them.
2. Canvas suitability increases linearly from 0 to 1 at 60% cover, then decreases
   to 0.4 at 100% cover. Coverage cannot tell us optical depth.
3. Low-cloud transmission proxy: `1 - 0.85 * low / 100`.
4. Cloud points: `35 * suitability * transmission`, bounded to 0–35.

This conservative first rule assigns zero when there is no middle/high cloud
canvas, including low-cloud-only scenes. Low clouds can also produce colourful
sunsets; handling those cases requires geometry and actual outcome validation.
It also cannot distinguish thin cirrus from opaque cloud at identical coverage.
The overall index remains a condition index, not a calibrated occurrence probability.
HKO temperature/humidity estimates and the rainfall visibility proxy are unchanged.

## Sunward sampling — second algorithm improvement

Near sunrise/sunset (geometric solar elevation from −8° to +8°), Astral computes
the solar azimuth **at the evaluated instant** at the same Hong Kong reference
point. It changes with date and time; it is not fixed east/west. It does not
implicitly move a current or three-hour assessment to the next solar event.

The service selects two more hourly forecasts at points 50 and 100 km along
that bearing. Great-circle coordinates are rounded to four decimals. To reuse
the provider's cached forecasts, the sampling bearing is quantised to 5°
(maximum deviation 2.5°); both actual and sampled bearings are retained.
Spatial requests run concurrently with at most two workers, share the provider
cache/expiry/backoff policy, and use 2s connect/3s read timeouts. Each application
process has its own cache; multiple workers do not share it.

Only when **both** points have complete, fresh cloud forecasts for exactly the
same evaluated instant, multiply the base cloud score by
`1 - 0.6 * max(low_cloud_50km, low_cloud_100km) / 100`.
It can only reduce the cloud factor (maximum 60% reduction), never increase it.
The 50/100 km distances, ±8° gate and 0.6 coefficient are initial assumptions,
not fitted physical parameters. Two point coverages are a regional low-cloud
obstruction proxy; they cannot establish an unobstructed optical path or model
cloud illumination, depth, base/top altitude, terrain or cloud movement.

Missing, stale or partial directional inputs retain the base layered-cloud rule
and explicitly show that the direction adjustment is unavailable. This is a
fallback to the previous rule, not evidence that the light path is clear. No
confidence upgrade or occurrence probability is inferred. Outside the elevation
range no spatial requests or directional adjustment are made. API factor details
preserve the base score, applied multiplier, solar position and per-point sources.

## Validation and next steps

Offline tests cover three-hour interpolation, midnight/time zones, exact samples,
missing hours, stale/malformed data, valid zeroes, low-cloud obstruction, layer
overlap, HTTP caching/backoff, outages and UI provenance. Passing them demonstrates
software behaviour, not improved forecast accuracy.

Tests also cover real seasonal solar bearings, timezone equivalence, great-circle
points, per-point provenance, missing/stale samples, timeout fallback, spatial
cache reuse and the actual scorer's downside-only adjustment.

### Prospective three-hour verification

The running scheduler now checks every minute (and at startup) for solar events
three hours ahead, allowing ±5 minutes. It stores the first usable forecast for
each HK reference-region/event, including actual issue/evaluation/event times,
version, input weather and provider provenance, factor details and data quality.
The forecast must genuinely have been issued within the tolerance, with an
evaluated instant within five minutes of the event. Cached forecasts older than
five minutes are rejected. The integer three-hour horizon is retained; the UI
reports the actual lead in minutes, not an exact 180-minute promise. A missed
window is never backfilled. The service must be running with scheduling enabled.

`GET /api/verification/three-hour` lists up to 200 recent snapshots and per-version
counts. The dashboard shows the latest 12. After an event's ±30-minute reference
window ends, users can submit one immutable, explicitly confirmed personal
observation with a Hong Kong location and timezone-aware observation time inside
that window. `POST /api/verification/three-hour/<assessment_id>/outcome` gets the
prediction score from the stored snapshot; client-supplied scores are not used.
These are anonymous self-reports, not independently verified ground truth or
photo verification. A location can differ from the regional reference and
visibility can vary; this is a data-collection pilot, not calibrated validation.

The declared experimental high-score threshold is 70. Reported outcomes are
strong (clear, extensive orange/red/pink clouds toward the solar event), weak or
absent, and unsure/obstructed. Pending and unsure cases never count as negatives.
Hits, false alarms, misses and correct negatives use only labeled cases and are
split by scoring version. Precision/recall include denominators via these counts;
accuracy remains null. Anonymous first reports can be mistaken or malicious;
they must be reviewed before fitting weights. Existing legacy feedback accuracy
reports are separate and do not validate this new three-hour cohort.

Next, review outcomes and compare the old text rule and layered rule on
the same dates, reserve later dates for validation, and report sample count,
missed events and false alarms before tuning constants or claiming improvement.
Viewing-location geometry and cloud optical properties need separate data and validation.

## Target-time weather inputs (v1.6)

The central Locationforecast response is fetched once per preparation through
the existing cached client. For future horizons, its temperature (celsius),
relative humidity (%) and wind speed (m/s) are selected independently of cloud
availability. Native units and finite physical ranges are checked per field.
Instantaneous values use exact samples or linear interpolation between adjacent
records no more than one hour apart, without extrapolating or bridging gaps.
Wind is converted to km/h before applying the existing wind scoring thresholds.
Cloud selection, attribution, caching, 18-hour issue-age bound and 15-minute
future issue tolerance retain their previous policy.

Rain is different: `next_1_hours.details.precipitation_amount` is a complete
one-hour accumulation starting at the record time, as defined by the provider's
[ForecastJSON documentation](https://docs.api.met.no/doc/ForecastJSON.html).
Select the interval containing the target (start inclusive, end exclusive).
Do not interpolate, pro-rate, or divide `next_6_hours` into invented hourly rain.
The UI shows both ends of the accumulation interval as well as the target time.
This interval is not a forecast for the whole ±30-minute viewing window.

`weather_data.hourly_weather_forecast` preserves each selected field's native
and output units, interpolation method or rain period, source sample times,
issue/retrieval times, reference coordinates and missing fields. Future target
temperature/humidity blocks use the MET reference-point label, not a fictional
HKO station observation. The scorer, color heuristic and future wind/humidity
risk assessment consume the selected target values. Original HKO observations
remain separate. No extra HTTP request is made for these fields, and current
mode retains actual observations. Clear-sky UV is not used as all-sky UV.

Partial or stale input falls back separately to existing temperature/humidity
estimates, observed district rainfall or daily wind text. Fallbacks remain
labeled and available for review; missing fields are never filled with zero.
A valid real model temperature/humidity can support the future score even if
the corresponding HKO observation is missing. Without either valid model input
or the required observed basis for a fallback, the core-data gate still applies.
Adding these fields does not upgrade the heuristic to calibrated probability.

The API's legacy `visibility` factor key remains for compatibility; the product
labels it as a **rain-obstruction reference**. A regional forecast accumulation
and an observed maximum across districts are different proxies, so the scoring
version is now `unified_v1.6_hourly_weather`. Neither is visibility in metres;
zero rain cannot exclude haze, fog or other obstruction. Existing temperature,
humidity and wind preferences are still uncalibrated assumptions. Forecasts must
be evaluated against the prospective outcome cohort before claiming improved
accuracy. Existing daily rain-probability and seasonal warning-risk heuristics
also remain separate assumptions.

The response retains the target instant chosen before network work, while its
generation timestamp records completion. Provider latency therefore does not
silently move the displayed target beyond the actual model samples used.

## Removal of unvalidated photo bonuses

`unified_v1.7_no_legacy_photo_bonus` removes the extra photo correction after
warning penalties. The old path used a fixed 18:50 clock time and default
humidity/cloud values, and could award 11 extra points even with an empty
weather object at that time. The separate photo-case similarity correction is
also disabled. Both legacy helper signatures remain available and return zero.
Photo observations can still be collected for prospective validation.

The final score is the unified scorer result minus the combined warning/risk
penalty (capped at 10), with a floor of zero. The same final score feeds the API,
intensity/color descriptions, warning history, immutable snapshot and cache.
The score breakdown explicitly records the disabled photo correction. Missing
factor scenarios no longer absorb an unexplained score adjustment: their range
is unavailable if the final score does not reconcile with that calculation.

This changes scoring behavior, so new verification records use a new version
and existing snapshots are not rewritten. Existing seasonal adjustments and
temperature/humidity/wind thresholds remain uncalibrated. Removing the bonus
can lower sunset scores; improved forecasting accuracy must still be measured
against future observations.

## HKO visibility observations

`unified_v1.8_current_visibility` adds the HKO LTMV CSV feed: ten-minute mean
visibility at Central, Chek Lap Kok, Sai Wan Ho and Waglan Island. CSV timestamps
are interpreted in Hong Kong time. Metres convert to kilometres; an actual zero
remains zero. Invalid units, dates, duplicate station/timestamp rows and missing
values are not filled. Every use filters out observations older than 30 minutes
or more than two minutes in the future. Requests time out after three seconds,
cache for five minutes and back off one minute after failure. Dated cached data
can survive a fetch failure but is still subject to the same freshness filter.

Each available station is shown separately with its own observation time. No
territory-wide average or minimum is invented. Current-mode scoring uses only
Central as the fixed reference station. With rainfall available, the existing
rain-obstruction score is capped at 20/15/8/4/1 for visibility at least
10/5/2/1/0 kilometres respectively (an actual zero caps at zero). This cap can
only reduce points. It does not award points or fill missing rainfall, and
another station never silently replaces Central. These provisional thresholds
are uncalibrated and a station reading is not a measurement of the sunward path.

For all future horizons, including three hours, visibility is displayed as a
current observation only and never modifies the future score. There is no
visibility forecast in this integration. Missing optional visibility cannot
block a forecast; existing dated assessments and outcomes are preserved.

## One target instant across scoring

`unified_v1.9_aligned_target_time` passes the timezone-aware `forecast_target_at`
selected before provider requests to the time factor and uses its Hong Kong
calendar month for seasonal adjustment. Hourly weather, layered clouds and
sunward geometry already use that same instant. Provider latency therefore
cannot move time scoring across a threshold or move seasonal points to a
different month. Existing score thresholds and seasonal point amounts remain
unchanged and uncalibrated.

The scorer records `prediction_info.evaluated_at` and the time factor's actual
`evaluated_at`, `prediction_time`, `event_at` and `time_diff_minutes` for audit.
Response generation time remains separate from the forecast target. A direct
legacy scorer call without target metadata resolves one aware target from its
clock and lead time; explicitly malformed or timezone-naive target metadata
fails scoring instead of silently evaluating another instant. Existing
verification snapshots keep their original scoring version.

## Prospective verification diagnostics

The three-hour verification report preserves totals under `by_version` and now
also returns each version's `by_event.sunrise` and `by_event.sunset` summaries.
It continues to use only the most recent 200 captured forecasts across all
versions; these totals are not lifetime statistics. The page lists 12 recent
records and offers expandable event tables. No score weights or the provisional
high-score threshold of 70 change in this reporting update.

Each summary separates `awaiting_event`, `awaiting_report`, `unsure` and `labeled`.
Only strong and weak/none self-reports enter the confusion counts. Precision's
denominator (`predicted_positive`) is hits plus false alarms, and recall's
denominator (`observed_positive`) is hits plus misses. Both remain null when
their denominator is zero. The page shows false alarms over labeled high-score
forecasts and misses over self-reported strong events as counts with their
explicit denominators; it never displays a zero-over-zero fraction.

Score bins are descriptive intervals `[0,45)`, `[45,70)`, `[70,85)`, `[85,100]`.
Every bin separately counts forecasts, labeled outcomes, strong, weak/none,
unsure and pending records. Its observed counts are not forecast probabilities,
calibration estimates or proof that a weight is useful. Sunrise and sunset can
have different error patterns, and self-reported events have location and
selection bias. A future weight comparison needs independent held-out outcomes.
Reports are derived from immutable snapshots and do not rewrite predictions,
outcomes, score versions or historical inputs.

## Fallback time and missing-value corrections

`unified_v1.10_fallback_provenance` also supplies the initial target instant to
the observation-based fallback extractor. Hong Kong date and hour selection,
including the daily forecast chosen across midnight, therefore do not drift
while data providers are being fetched. Calls outside the main input service
can still omit the optional target and use their existing clock-plus-lead path.

Fallback `updateTime` now preserves the original observation update time rather
than replacing it with a future timestamp. `forecast_target_at` and
`forecast_estimation.valid_at` separately identify the estimate's target;
`forecast_estimation.method` identifies the uncalibrated heuristic. The input
snapshot and displayed fallback factors retain both times. This change does
not establish that an observation is fresh, nor turn fallback values into
official hourly forecasts.

Missing, nonnumeric, out-of-range or inverted daily temperature extrema are
not replaced with 25/30°C defaults. The old 15–40°C clamp is removed: a winter
estimate below 15°C stays below 15°C. Estimates outside the scorer's existing
−50–60°C input bounds become unavailable instead of being clipped to a plausible
boundary. Valid humidity adjustments use the physical 0–100% limits instead of
forcing values into 30–95%. Malformed station rows do not break other valid
readings or contaminate the station-average adjustment. UV and rainfall remain
observations when no corresponding forecast is supplied; nested observation
structures are copied to prevent fallback edits from changing the originals.

MET Norway hourly fields retain priority. The retained clock-based temperature
offsets, daily-range blending and text-based humidity offsets are still
uncalibrated fallback rules; these corrections do not demonstrate improved
forecast accuracy. Existing captured assessments retain their scoring versions.

## Hourly weather consumption checks

`unified_v1.11_hourly_time_validation` rechecks each selected temperature,
humidity, wind and rainfall field when it is consumed. The model's aware
`valid_at` must equal the snapshot's aware `forecast_target_at` as an instant;
equivalent UTC/Hong Kong timestamps are accepted. Missing or malformed target
metadata does not select another time implicitly. An exact instantaneous
sample must match the target; interpolation needs two ordered samples strictly
bracketing it, no more than one hour apart. Rainfall must retain a one-hour
`[start, end)` interval containing the target, with its sample matching start.

Invalid fields are excluded independently. Remaining valid fields and existing
declared non-model fallbacks remain usable; a rejected model copy cannot be
reused as observed rain or wind. Scoring, wind-risk messages and factor details
read the same validated values rather than trusting duplicate raw copies.
Rain cards can still show the separate original observation as a reference.
This validation does not add a new observation freshness policy or validate
cloud-layer time metadata; the provider selector's existing run-age checks
remain in effect. It prevents time-mismatched input use, and does not by itself
demonstrate improved forecast accuracy.

## Cloud input time and unit checks

`unified_v1.12_cloud_time_validation` extends consumption-time checks to the
central cloud layers and both sunward samples. Scoring, input-quality checks,
factor details and cloud cards require aware `valid_at` metadata aligned to the
snapshot's `forecast_target_at`, with either one exact sample or two ordered
samples strictly bracketing the target and at most one hour apart. Sunward
assessment and sample timestamps compare instants, so equivalent UTC and Hong
Kong representations no longer incorrectly disable the directional adjustment.

The provider selector now requires `%` unit metadata for all four cloud layers.
Duplicate timestamps are ambiguous even when their values agree or one record
is malformed; they cannot be resolved by response order. Invalid records keep
their timestamp, preventing interpolation through a known unusable sample.
Unrelated hours and independently valid hourly weather fields remain usable.

Rejected central clouds use the existing HKO forecast-text fallback when it is
available; invalid directional data leave the validated central cloud score
unchanged. The numerical cloud-scoring formula and directional weights remain
uncalibrated and unchanged. The pure `score_cloud_layers` arithmetic helper
still accepts numerical layers; production consumers validate metadata first.
No new freshness policy or forecast-accuracy claim is introduced, and captured
assessments retain their original score versions.
