---
q: Why is the gate's drift_excess_t biased toward one side (long or short) of an asset, and how much?
kw: drift_excess_t side bias, long vs short false positive rate, size 1/ATR covariance, blind trade of the same hold, mu mean bar change, EURUSD short USDCAD long, pooled t by side, FPR 1.65 5.8 vs 2.6, step 8 step 10 t scale, favoured side
tag: 🔬  date: 2026-10-06  see: gate-t-scales, random-entry-nulls, post-selection-bias, gates-are-owner-decisions
---
# `drift_excess_t`'s drift term favours one side of each asset; the blind trade (variants c, d) removes it, b makes it worse
Trap: a long and a short, or two assets, are NOT on one t scale under the mean-bar term (variants `a` and `b` of
`tradelevel.drift_term`). It subtracts `mu × bars_held × Size × pv`; the doctrine sizes `∝ 1/ATR`, so size covaries
with the move that follows and a break-even long keeps `pv·h·cov(Size, move)` of t (a short's is minus it).
🔬 2026-10-06 (encargo 44 D-m, 240,000 no-edge strategies, 4 assets × 2 sides, oos1, gross): mean |shift| **a 0.09**
(max 0.16) · **b 0.12-0.15** (max 0.33: a move per window with the mean-bar assumption is WORSE than today's) ·
**c 0.016 · d 0.017** (max 0.05-0.06, any window). Null FPR at 1.65 by cell: a 2.6-5.9 %, b 1.6-7.6 %, c/d 3.2-4.7 %.
Use `d` (or `c`); never `b`. A second bias, the CALENDAR footprint, only a per-window term touches, and partly (Evidence).

## Evidence
Calendar footprint (the strategy trades more in some quarters): only a per-window term touches it, and only partly — mean |t| a 0.22, c 0.21, d-year 0.15, d-semester 0.12; USA500 H1 IBS long −0.61 / −0.52 / −0.46 / −0.33. Until `d` is live read lifts WITHIN asset × side × timeframe.

- 🔬 D-m, 2026-10-06 (`scratch/encargo44/dm/`, tables in `AlgoData/scratch/encargo44_dm/`). No-edge strategy = a real
  donor's oos1 trade count and holds, entries uniform without overlap, size `c / ATR(bar before entry)`, 20,000 per cell
  (USDJPY H1 15,000), statistic = skew-kurtosis t at AR(1) n. Mean t, long / short:

  | cell | a | b year | b semester | c | d year | d semester |
  |---|---|---|---|---|---|---|
  | NIKKEI225 M30 | −0.14 / +0.12 | −0.16 / +0.14 | −0.24 / +0.22 | +0.01 / −0.02 | +0.01 / −0.02 | +0.01 / −0.02 |
  | USA500 H1 | −0.05 / +0.04 | −0.29 / +0.28 | −0.33 / +0.32 | +0.04 / −0.05 | +0.04 / −0.05 | +0.04 / −0.05 |
  | USDJPY H1 | −0.07 / +0.07 | +0.06 / −0.06 | −0.01 / +0.02 | +0.01 / −0.01 | +0.01 / −0.01 | +0.01 / −0.01 |
  | USDJPY M30 | −0.06 / +0.08 | +0.03 / −0.01 | −0.03 / +0.04 | +0.01 / +0.01 | +0.01 / +0.01 | +0.01 / +0.01 |
  | XAUUSD H1 | +0.08 / −0.09 | +0.10 / −0.12 | +0.08 / −0.10 | −0.00 / −0.01 | −0.00 / −0.01 | −0.01 / −0.01 |
  | XAUUSD M30 | +0.16 / −0.16 | +0.21 / −0.20 | +0.18 / −0.17 | −0.01 / +0.01 | −0.01 / +0.01 | −0.01 / +0.01 |

  Pooled gross FPR at 1.65: a 4.16 %, c 4.03 %, d 4.05 % (±0.08) — below 5 % because non-overlapping trades cover
  10-20 % of a finite window (sd of t 0.90-0.99) and the AR(1) cap only ever shrinks; net of costs 0.85-0.87 %.
- Real populations (26,159 strategies, 13 populations, all long), pass at 1.65 against variant a's 496: c 638
  (−0/+142) · d year 582 (−33/+119) · d semester 579 (−58/+141) · d quarter 415 (−120/+39) · b year 459 (−46/+9) ·
  b semester 383 (−132/+19). Year and semester share 524 of their passes. The gain is NIKKEI225 and USDJPY longs,
  which `a` penalised; XAUUSD and USA500 had no pass under any variant.
- Calendar footprint: the same monkeys with each trade kept in the donor's own quarter (229,900). d-quarter is
  unbiased there by construction, so this null cannot price the quarter window; it costs 29 % of d-year's passes.
- Mechanism: exact enumeration (17 assets × M30/H1/H4 × build/oos1) predicts null2's 442 cells (r 0.98, slope 0.88); not the weekend gap, not the price level.
- 📓 `AlgoData/scratch/calib_step10/drift_bias.md` (+ `drift_bias.py`, `out/drift_bias_enum.csv`, 17 assets × M30/H1/H4
  × build/oos1): exact enumeration predicts null2's 442 cells (r 0.98, slope 0.88). Not the weekend gap, not the price level.
- 🔬 Red team 2026-10-03 (`AlgoData/scratch/calib2/redteam/review.md` §C6): mean |shift| 0.122 on oos1 over 10 assets,
  0.116 oos2; real populations, corrected − gate's t: longs −0.03…−0.17 / shorts +0.06…+0.14 by class; with the Friday
  cut the toolkit's term leaves 0.08 mean |t| (gate's: 0.19, max 0.94), longs favoured in 83 % of cells.
- 📓 Toolkit count (not recomputed by the red team): of 115 thresholds, 45 looked side-dependent with the gate's term, 8 with the corrected one.
- A bug found on the way: `c[i0−1]` with i0 = 0 on the five index frames read the last close; `null2/run2.py` `prepare`
  still has it, so null2's IS columns of those indices are wrong (its OOS columns are not).
- `studies/transfer/crossmarket/simulate/excess.py` copies the gate's term on purpose: change both together.
