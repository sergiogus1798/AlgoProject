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
resampling: not yet checked together with the gate's AR(1) effective n.
