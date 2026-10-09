---
q: Does an in-sample filter inside the Build (trade floor, PF, Ret/DD, WinningPct) breed better strategies than none?
kw: IS filter in the build, ab1 ab3 ab5 arms, PF 1.3 Ret/DD 3, trades per year floor 35 inside the build, build box minutes, accepted per minute, MaxStrategies cap 20000, robust per 1000, purity, adaptive calibration RECIPE, long builds untested
tag: 🔬  date: 2026-10-04  see: post-selection-bias, conditions/build-rankings-acceptance, sqx-drive/unselected-build-population
---
# No IS filter breeds more robust strategies per build minute than none; the build BOX dominates
Seven arms inside the Build (trades floor, PF/RetDD ladders 1.2/2, 1.3/3, 1.5/5, 1.8/8, WinningPct ≥ 55), one box, same
cell: each yields **70-98 % fewer** oos1-robust per minute; inside = the same cut afterwards. Only PF ≥ 1.3 & Ret/DD ≥ 3
shows purity ×1.54 (CI 0.86-2.43; oos2 ×3.3, 1.6-4.6) — **optional, undecided**. The BUILD BOX dominates: the search
needs ~2 min to start (600-3,800 accepted at 2 min vs 12,000-20,000 at 6). Keep acceptance minimal (`NumberOfTrades ≥ 100`,
`NetProfit > 0`), spend minutes; a filter the owner wants anyway goes inside, an unsure one is cut in Python.
**Not tested:** 180-min builds with a full databank (cap 10,000 replaces by IS Ret/DD) — there purity is what matters.

## Evidence

- 📓 `AlgoData/scratch/calib2/adaptive/RECIPE.md` (tables per arm, hold-out run once, pre-registered) and `redteam/review.md` §C5.
  Robust = bias-corrected drift-excess t ≥ 1.65 & oos1 net > 0. Red team confirms: floor H1 2.1 vs 7.5 per 1,000
  (5.0 vs 28.9 per min); ab5 purity ×1.55 (0.87-2.47) is one cell (DJ30 pullbackL, ×4.7).
- 🔬 Toolkit's «put ab5 inside» compares inside with cut-afterwards (5.8 vs 2.0 per min); the owner's question is inside
  vs NO filter (5.8 vs 24.4, ×0.24). The director's label is right; seven builds stopped at the 20,000 cap, so their per-minute is a floor.
- 🔬 Per-cell ab5 purity 0.25-4.5 with no pattern by class/family/timeframe: no cell-specific rule.
- 🔬 Not worth it: SQN/RExpectancy ≡ ProfitFactor (ρ 0.99-1.00), SharpeRatio ≡ Ret/DD (0.97); thresholds read on 2-min
  populations (PF ≥ 1.2 lift 2.07) fell to ~1.1 on evolved ones. On oos2 the filtered arms look better only through index longs.
- Verified Build conditions: `conditions/build-rankings-acceptance`.
