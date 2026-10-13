---
q: Which barrier does SQX take when one bar holds both the stop-loss and the profit target, at each precision?
kw: barrier.intrabar; intrabar convention; SL and TP in the same candle; double touch; pessimistic stop first; OHLC tick order; O-L-H-C; O-H-L-C; bar up bar down; doji; testPrecision 1 2; selected timeframe; 1 minute data tick simulation; M1 precision retest; close time minute stamp; tight SL PT build accepts nothing; AutomaticDismissal; GC overhead limit exceeded ProbSharpeRatio; ATRBasedValue level from fill
tag: 🔬  date: 2026-10-13  see: export/off-grid-stamps-and-stop-exits, export/fill-and-pricing, export/sqx-atr-is-wilder
---
# SQX walks each bar of its precision Open→Low→High→Close when it closes up, Open→High→Low→Close when down — H1 bars at `testPrecision=1`, M1 bars at `2`
- `testPrecision=1` (selected timeframe), longs: H1 bar Close > Open → the **stop**; Close < Open → the **target**. 67,652 double-touch trades, 0 exceptions. «Pessimistic» is wrong for 38 %; the M1 path explains only 78 %. Levels: SL = fill − coef × ATR[entry bar − 1], PT = fill + coef × ATR[entry bar − 1]; SL exits at level − slippage, PT at the level.
- `testPrecision=2` (1 minute): the barrier the **M1 path** reaches first, 99.45 % of 69,933 (99.78 % when the touch is > 0.02); the H1 bar's direction drops to 78.8 %. Inside one M1 bar holding both, the same walk at M1 scale: 268 of 268. Close time is then the minute's stamp.
- **To be the reference for intrabar behaviour an SQX corpus must be retested at `testPrecision=2`**: at 1 it carries the bar-direction rule, which flips the barrier in 20.9 % of the double-touch trades.
- Cost of precision 1 here (SL+PT 0.2-0.6 ATR, 20 % of trades double-touch): 5.4 % of trades change exit; net profit per strategy moves by a median −890 $ on −17,857 $. Retest of 300: 3.5 s → 20.6 s (5 y), 36.9 s (10 y).
- A Build with required SL+PT of 0.2-0.6 ATR accepts **nothing** with the donor's `<AutomaticDismissal>` on; all ten `dismiss="false"` → 300 in 3 min, population 50 × 2 (250 × 20 ran the 16g conductor out, `GC overhead limit exceeded`).
- Not decided by the rule: H1 doji bars at precision 1 (97 PT / 41 SL). Not measured: shorts (🤔 an up bar gives a short its target first), tick precision, 145 clear misses at precision 2 (0.2 %).

## Evidence
300 Simple Strategy long XAUUSD H1 (palette `tendencia_base_v3`), build 2008-2017 + oos1 2018-2022. Precision 1:
`Test_E53_5c_XAUUSD_H1`, 358,864 trades. Precision 2: `Test_E53_5c_M1_XAUUSD_H1` (both conductor, retired) — the same 300
`.sqx` loaded into `Results` and retested by the OOS task, byte-identical to the first run's but `testPrecision`, then
again on the build window at the Build task's spread and slippage: 359,150 trades, entry price equal in 100 % of the
357,537 paired entries. Scripts and tables: `/dev/shm/tmp66/E53c/` and `/dev/shm/tmp66/E53c-M1/` (`measure.py`,
`measure.out`; volatile — the precision-1 trades are in `AlgoData/raw/Test_E53_5c_XAUUSD_H1/`; of precision 2 only the
build window's, under `AlgoData/raw/Test_E53_5c_M1_XAUUSD_H1/OOS/`).

| double-touch exit bar (H1) | precision 1: n | SL | PT | precision 2: n | SL | PT |
|---|---|---|---|---|---|---|
| all | 70,066 | 43,285 | 26,781 | 70,201 | 44,699 | 25,502 |
| H1 bar up | 43,240 | 43,137 | 103 | 43,321 | 36,555 | 6,766 |
| H1 bar down | 26,675 | 102 | 26,573 | 26,729 | 8,078 | 18,651 |
| H1 doji | 151 | 46 | 105 | 151 | 66 | 85 |

| rule against SQX | precision 1 (70,134) | precision 2 (70,201) |
|---|---|---|
| H1 bar direction | 99.55 % (205 misses, margin ≤ 0.005) | 78.76 % (CI95 78.46-79.06) |
| M1 path order | 78.46 % | 99.45 % (CI95 99.39-99.50) of the 69,933 it decides |
| M1 path, then M1 bar direction | — | 99.45 %; the 268 same-minute cases 268/268 (194 up → SL, 74 down → PT) |

Precision 1 → 2, 357,537 paired trades: exit type differs in 15,660 (4.38 %; PT→SL 8,314, SL→PT 7,144), exit H1 bar
in 4,607 (1.29 %), exit price in 17,357 (4.85 %), any in 19,296 (5.40 %); 1,327 entries only at 1, 1,613 only at 2.
Net profit p2 − p1 per strategy: median −890 $, worst −11,025 $, lower in 73.7 % (0 of 300 profitable at either).
Of the 388 misses at precision 2, 243 touch by ≤ 0.02 at the minute; the other 145 close at another minute (−15…+6).
SQX's close minute is the first-touch minute in 98.1 %. SQX's exit bar is the first H1 bar touching a barrier in
98.6-99.0 % (precision 1) and 99.1-99.5 % (precision 2).
