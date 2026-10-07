---
q: Which coefficients of a cross-timeframe sibling are divided by the ATR ratio c, and what does step 10.5 actually scale?
kw: crossTF scale coefficient, ranges.yaml, bar window other unverified, ATR ratio c, k / c, maxValue PMax M15, AnchoredVWAP StdDevMult ParamTypePeriod, CandleBreakoutLong Double2, no stop at step 10.5, M15 doubles periods, n_coef_scaled
tag: 🔬  date: 2026-10-07  see: sqx-drive/crosstf-period-source, sqx-format/grafting-a-stop-loss
---
# Siblings scale per-bar coefficients by `k / c`; at step 10.5 there is no stop to scale
`sqx/variants/ranges.yaml` rules each non-length parameter by reading the block's formula: `bar` (multiplies
a per-bar measure: ATR, candle range) is written `k / c`; `window` (a measure over N already-scaled bars,
a Bollinger deviation) and `other` (unit-free: percentile, oscillator level, ratio) stay; `unverified`
leaves it and flags the sibling for T0. `c` = median ATR on the sibling's timeframe (period scaled) over
the mother's, build + oos1 of the asset (`sqx.variants.ranges.measured`; `scale.py --symbol`). Measured for
NIKKEI225 from M30 (encargo 47): M15 0.704, H1 1.419, H4 2.833, close to √(bar ratio).
## Evidence
- **At step 10.5 strategies carry no stop or target** (`assets/_build.yaml` `stop_loss`/`profit_target`
  false; the stop is grafted at step 24), so «scale the stop by ATR» acts today only on condition-block
  coefficients. `ranges.stops` is ready for a strategy that has one.
- `AnchoredVWAP` `Fast/SlowStdDevMult` are typed `ParamTypePeriod` by SQX, so the lengths rule divided them
  as lengths; they are ruled `window` and `scale.py` excludes `measures` from the lengths.
- **Unverified**: `k / c` with c < 1 can exceed a block's `maxValue` (PMax 10.99 → 15.6 on M15, per the
  encargo); the code does not clamp it and nothing here shows SQX accepts it — only a real run does.
  `CBlock_CandleBreakoutLong*.Double2` («body > Mult × ATR»: `bar`, or a ratio `other`) is an owner question.
- M30 → M15 doubles the periods (shift 0 on the batteries' mothers); H4 is where clamps appear.
- 🔬 `sqx/variants/scale.py:128-139` (measures excluded from lengths, `coefs = k / c`), `sqx/variants/ranges.yaml:23`
  (AnchoredVWAP `window`), `:54-57` (CandleBreakout `unverified`), `assets/_build.yaml:51-52`.
- 🔬 `ranges.measured('NIKKEI225','M30',t,14,14)` re-run 2026-10-07: M15 0.694, H1 1.442, H4 2.950 (the period
  changes c by ~2 %). The encargo's «120 real mothers, no clamp on M15, 5 % clamped on H4» was not re-checked.
