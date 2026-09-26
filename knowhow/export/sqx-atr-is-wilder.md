---
q: how SQX computes ATR; Wilder or simple mean; ATR-based stop loss formula; ATRBasedValue getATRValue shift 1 round 6; reproduce the ATR SQX used for a stop; calibrate.atr is a rolling mean; Close type SL
tag: 🔬  date: 2026-09-26  see: export/fill-and-pricing, sqx-format/grafting-a-stop-loss
---
# SQX's ATR is Wilder with an averaged start; the stop is X · round(ATR(20), 6) of the last closed bar
- `ATR[i] = ((n-1)·ATR[i-1] + TR[i]) / n`, `n = min(i+1, period)`, `ATR[0] = High-Low`.
  `engines.market.atr.sqx(frame, 20)` reproduces it; `engines.market.calibrate.atr` is a rolling mean — never for a stop.
- `ATR-based value` stop = `X · ATR` of the **bar closed before the entry bar** (SQX's shift 1), placed
  from the fill price; the exit then slips by the task's slippage. A stopped trade exports `Close type = SL`.

## Evidence
- Source: `Snippets/SQ/Blocks/Indicators/ATR/ATR.java`, `Formulas/SLPT/ATRBasedValue.java` (`getATRValue(chart, AtrPeriod, 1)`).
- Proof 2026-09-26, `Strategy 19.8.78` XAUUSD M30, 20 grafted variants X = 2.15–6.09, `ATRCalc_XAUUSD_M30_dev`:
  `|close − open| / (X·ATR)` of 8,100 stopped trades, p5–p95: bar before entry 1.001–1.006 (IS, 4,425),
  spread ≤ 0.011 in every window; entry bar 0.93–1.03, two bars before 0.98–1.18. Excess `|close−open| − X·ATR`
  median 0.020 IS / 0.050 oos1, oos2 = the slippage of each window. `studies/closing/atrCalculator/proofs.py`.
- Hand-computed known answer: `tests/test_atr.py`. 282,850 XAUUSD M30 bars in 0.12 s.
