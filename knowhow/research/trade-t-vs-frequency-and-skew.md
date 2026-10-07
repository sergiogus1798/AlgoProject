---
q: Does a higher trade frequency buy the trade-level t more power, and does skew distort its false-positive rate?
kw: trades per year floor R4a; power vs frequency; Sharpe per trade vs annual Sharpe; negative skew inflates t; mean reversion without stop false positives; PSR skew kurtosis standard error; drift_excess_t share above 1.65
tag: 🔬  date: 2026-10-06  see: research/gate-t-scales, research/drift-term-biased-by-side, research/mintrl-explosion-is-correct
---
# More trades a year does not buy t; strong negative skew inflates its false positives
In the populations measured, the share of strategies with `drift_excess_t >= 1.65` FALLS as trades
per year rise (each extra trade pays the spread), so a frequency floor cannot be justified by power;
and a t-test on per-trade P&L with skew around −1.5 (mean reversion, no stop) rejects a no-edge
strategy 6.9 % of the time at the 5 % line and 2.1 % at the 1 % line.

- No population showed dispersion of real edge (var of t below 1 in every band): `Φ(s·√n − z)` at
  a fixed `s` overstates what frequency buys. Skew within ±0.8 moves the rate only 5.8 → 4.7 %.

## Evidence
⚠️ 2026-10-07: the REAL-population pass counts below were priced with every exit at a bar open; stop-loss exits (30-37 % of trades in IBS, doubleROC, volatilidadL, simpleL) were inflated by ~+300 USD each (`knowhow/export/off-grid-stamps-and-stop-exits.md`). The stored full populations lack `Close type`, so they could not be re-priced; only the monkey (no-edge) numbers stand as measured.

OOS (oos1) trades of four populations at the 2026-10-04 costs; scratch script, 2026-10-06.

Share with `drift_excess_t >= 1.65` by oos trades/year (N strategies):

| trades/yr | NIKKEI225 M30 simple (9,959) | USDJPY M30 doubleROCLong (2,999) |
|---|---|---|
| < 20 | 3.5 % (1,090) | 7.0 % (676) |
| 20–35 | 6.2 % (3,250) | 0.7 % (143) |
| 35–50 | 2.7 % (2,302) | 8.2 % (171) |
| 50–75 | 1.1 % (2,151) | 0.0 % (1,486) |
| > 75 | 0.6 % (1,166) | 0.0 % (523) |

Mean excess `s` per trade, same bands, NIKKEI225: +0.003, +0.011, −0.003, −0.019, −0.020. Spearman
(frequency, excess t): NIKKEI225 −0.18, USDJPY −0.55. USA500 H1 indicesIBS and XAUUSD H1
squeezeBBLong (3,000 each) sit almost wholly in 20–35 and have no strategy at 1.65.

Null bootstrap (400 strategies per population, each strategy's trades centred on zero and resampled
2,000 times, plain t): false-positive rate at 1.645 / 2.326 — NIKKEI225 5.2 % / 1.09 % (median skew
−0.08), USDJPY 5.1 % / 1.02 % (−0.06), XAUUSD 4.8 % / 0.91 % (+0.31), USA500 IBS 6.9 % / 2.11 %
(−1.57, kurtosis 7.4). By skew tercile inside NIKKEI225: −0.68 → 5.8 %, −0.09 → 5.1 %, +0.64 → 4.7 %.
The PSR standard error (`1 − γ3·s + (γ4−1)/4·s²`) lowers the t of USA500's strategies with t > 1 by
7 % (median) and restores the nominal rate: same bootstrap with the PSR t, USA500 5.1 % / 1.08 %,
NIKKEI225 5.2 / 1.15, USDJPY 5.3 / 1.17, XAUUSD 5.1 / 1.11 (Johnson's t: 5.6 / 1.36 on USA500). IID
resampling.

**With the AR(1) effective n (🔬 2026-10-06, encargo 44 D-m).** FPR at 1.65, plain iid / plain AR(1) / skew-kurt iid /
skew-kurt AR(1):

| no-edge world | plain iid | plain AR(1) | s-k iid | s-k AR(1) |
|---|---|---|---|---|
| 240,000 random-entry strategies, gross, term d-year | 4.02 | 3.68 | 4.42 | 4.05 |
| same, today's term a | 4.10 | 3.72 | 4.54 | 4.16 |
| USA500 H1 IBS, centred trades, iid bootstrap | 6.84 | 6.29 | 5.09 | 4.58 |
| same, blocks of 5 (keeps serial dependence) | 4.88 | 4.54 | 3.35 | 3.03 |
| USDJPY H1 donchian, blocks of 5 | 5.58 | 5.21 | 5.44 | 5.08 |
| NIKKEI225 M30 volatilidadL, blocks of 5 | 4.69 | 4.24 | 4.85 | 4.39 |

The AR(1) n is a multiplier outside the formula, capped at n: it only ever lowers t. It takes 0.3-0.5 points of FPR
everywhere, is needed only where trades are positively dependent (USDJPY donchian: 5.4 → 5.1), and cannot correct
negative dependence (USA500 IBS, XAUUSD breakouts: already under 5 %). On 26,159 real strategies with term d-year it
costs 43 of 625 passes (6.9 %); the skew-kurt error ADDS 39 to plain's 586 (most populations here have a positive or
near-zero skew at the pass line). Scripts `scratch/encargo44/dm/`, tables `AlgoData/scratch/encargo44_dm/`.
