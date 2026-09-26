---
q: how SQX computes ATR; Wilder or simple mean; ATR-based stop loss formula; ATRBasedValue getATRValue shift 1 round 6; reproduce the ATR SQX used for a stop; calibrate.atr is a rolling mean
tag: 📓  date: 2026-09-26  see: export/fill-and-pricing
---
# SQX's ATR is Wilder with an averaged start; the stop is X · round(ATR(20), 6) of the last closed bar
- `ATR[i] = ((n-1)·ATR[i-1] + TR[i]) / n`, `n = min(i+1, period)`, `ATR[0] = High-Low`: a running mean for
  the first `period` bars, then Wilder. `engines.market.atr.sqx(frame, 20)` is that, rounded to 6.
- `engines.market.calibrate.atr` is a **rolling mean** and does not reproduce SQX: never use it for a stop.
- An `ATR-based value` stop is `X · SQUtils.round(getATRValue(chart, 20, shift=1), 6)` from the fill price.
  Shift 1 is read as the bar before the entry bar (entries fill at the bar open) — the SQX proof in
  `studies/closing/atrCalculator/` is what confirms it.

## Evidence
- `internal/extend/Snippets/SQ/Blocks/Indicators/ATR/ATR.java` `OnBarUpdate` (the recurrence above).
- `internal/extend/Snippets/SQ/Formulas/SLPT/ATRBasedValue.java`: `atr = strategy.getATRValue(chartData,
  AtrPeriod, 1); valueInRealPrice = Value * SQUtils.round(atr, 6)`. `getATRValue` is compiled code, not the
  block: that it runs the same recurrence is 🤔 until the stop-distance proof reconciles it.
- Hand-computed known answer: `tests/test_atr.py`. 282,850 XAUUSD M30 bars in 0.12 s.
