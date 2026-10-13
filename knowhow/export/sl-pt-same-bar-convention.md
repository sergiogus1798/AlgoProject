---
q: Which barrier does SQX take when one bar's range holds both the stop-loss and the profit target?
kw: barrier.intrabar; intrabar convention; SL and TP in the same candle; double touch; pessimistic stop first; OHLC tick order; O-L-H-C; O-H-L-C; bar up bar down; doji; tight SL PT build accepts nothing; AutomaticDismissal; GC overhead limit exceeded ProbSharpeRatio; ATRBasedValue level from fill; PT exit price
tag: 🔬  date: 2026-10-13  see: export/off-grid-stamps-and-stop-exits, export/fill-and-pricing, export/sqx-atr-is-wilder
---
# SQX walks each bar Open→Low→High→Close when it closes up and Open→High→Low→Close when it closes down — not «stop first»
- `testPrecision=1` (selected timeframe), longs: bar with Close > Open → the **stop**; Close < Open → the **target**. 67,652 double-touch trades, 0 exceptions. So «pessimistic» is wrong for 38 % of them, and the M1 path order explains only 78 %.
- Doji bars (Close == Open, 0.2 %) are not decided by this rule (97 PT / 41 SL); a touch by ≤ 0.01 is rounding noise, not a double touch.
- Levels: SL = fill − coef × ATR(period)[entry bar − 1], PT = fill + coef × ATR[entry bar − 1], fill = bar open + spread + slippage. SL exits at level − slippage, PT at the level exactly. 86 % of these exits are on the entry bar itself.
- A Build with required SL+PT of 0.2-0.6 ATR accepts **nothing** while the donor's `<AutomaticDismissal>` is on (0 in 11 min); all ten `dismiss="false"` → 300 in 3 min. 🤔 which code dismisses was not isolated. With them off, population 250 × 20 islands ran the 16g conductor out (`GC overhead limit exceeded` in `ProbSharpeRatio`); 50 × 2 fits.
- Not measured: shorts (🤔 by the same walk an up bar gives a short its target first), `testPrecision=2`, and what breaks a doji's tie.

## Evidence
`Test_E53_5c_XAUUSD_H1` (conductor, retired), Simple Strategy long, palette `tendencia_base_v3`, 300 strategies,
build 2008-2017 + oos1 2018-2022: 358,864 trades, 355,546 by SL/PT. Scripts and tables: `/dev/shm/tmp66/E53c/`
(`measure.py`, `measure.out`; volatile — the trades are in `AlgoData/raw/Test_E53_5c_XAUUSD_H1/`).

| double-touch exit bar (H1) | n | SL | PT |
|---|---|---|---|
| all | 70,066 | 43,285 (61.8 %, CI95 61.4-62.1) | 26,781 |
| bar up, touch margin > 0.02 | 41,894 | 41,894 | 0 |
| bar down, margin > 0.02 | 25,758 | 0 | 25,758 |
| doji, margin > 0.02 | 138 | 41 | 97 |

Rules against SQX on all 70,134: bar direction 99.55 % (all 205 misses have a margin ≤ 0.005), M1 order 78.5 %,
nearer-to-open first 63.2 %, always SL 61.7 %. Level check: SL exit − level = −0.05 ± 0.005, PT exit − level = 0 ± 0.005.
SQX's exit bar is the first bar touching a barrier in 98.6-99.0 % (the rest not investigated).
`barrier.intrabar: pessimistic` (`engines/nulls/config.yaml`) is read by no code and `kernel.touched` has no production caller.
