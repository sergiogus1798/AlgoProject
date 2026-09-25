---
q: sequential optimisation IS vs OOS walk forward correlation; Seq. Opt. chained scan BestValue; Fitness equals Ret/DD; how to get a real WFC paired tuples
tag: 🔬  date: 2026-09-19  see: export/spp-pairing-for-wfc, sqx-format/sequential-optimisation-xml, sqx-drive/variant-route
---
# Sequential optimisation pairs by label but not by strategy — only the chain prefix is a real WFC
- The scan is chained: parameter k is scanned with 1..k-1 at the values THAT run chose; IS and OOS runs choose differently → same label, different tuple.
- Usable: scans up to the first `BestValue` divergence (≈ one clean scan per strategy). Demean ranks within each scan; never pool the cloud (Simpson).
- Stored `Fitness` = databank `Fitness` = Ret/DD ranks above 100 trades. No trade count stored → ≥100-trades filter impossible.
- Real WFC route: draw the tuple list once, write N variant `.sqx`, retest once over 2008–2022 with OOS cut 2018, `.vw` with sampleType 10 and 20 → IS and OOS on one row.

## Evidence
- `XAUUSD/Seq. Opt. IS` (task 15, 2008–2017) vs `Seq. Opt. OOS` (task 16, 2018–2022), 5 strategies, ±30 %, 30 steps, `ApplyToStrategy` false:
  50 parameters, identical `<Values>` grids, 1,507 (IS, OOS) fitness pairs; 1,356 are different strategies. `BestValue` agrees on 1–2 of 8–12 parameters.
- Clean prefix: 7 scans, 211 pairs; 2 inert (`CBlock_SqzMmnInt21`, flat over 31 values) → 5 informative scans, 150 pairs — a sensitivity line, not a surface.
- 1,507 points = 50 axes × 30–31. Pooled Spearman +0.292; per strategy −0.05 to +0.74; within-scan demeaned +0.235 over 1,415. Degenerate (fitness 0): 26 IS, 32 OOS.
- Fitness at first scan's original value = SPP `Fitness` stat to float32 on all 5. `17.9.39`, 10,935 SPP permutations ≥100 trades: Spearman(Fitness, ReturnDDRatio) +0.999
  (+0.978 vs ProfitFactor), +0.999 on OOS 11,262; unrestricted +0.769.

| | scans | pooled rho (Fisher-z) | 95 % CI | positive |
|---|---|---|---|---|
| clean, first link only | 5 | +0.335 | +0.10 to +0.54 | 5/5 |
| all non-inert | 47 | +0.309 | +0.14 to +0.46 | 35/47 |

- 🤔 Star of axes → nothing on joint overfitting; lag-1 autocorrelation up to +0.89, effective n 9–33; part of rho is mechanical (exposure moves IS and OOS together).
  No "high" threshold without a random-entry null.
- 🤔 No SQX cross-check scores the same tuples on two windows at scale: Optimize keeps top `maxOptimizations` (truncates on IS rank); WFM stores picked params per step only.
  Parameters are `<variable><id>NAME</id><value>N</value>` in `strategy_Portfolio.xml`; pair by strategy identity.
