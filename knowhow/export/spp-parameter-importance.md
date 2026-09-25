---
q: which parameters matter SPP eta-squared sensitivity; marginal profile WFC without pairing; freeze parameters shrink grid; unpaired SPP runs
tag: 🔬  date: 2026-09-19  see: export/spp-pairing-for-wfc, research/eta-squared-vs-duplicates
---
# Unpaired SPP runs still give parameter importance (eta²) and a marginal-profile WFC
- eta² = share of Ret/DD variance between groups of one parameter's value (permutations ≥100 trades), per run.
- 2–3 parameters carry most variance; freezing the rest shrinks the grid 7×–51,000× → a saturated paired run becomes routine.
- Marginal profile `E[Ret/DD | parameter = v]` per window; rank correlation IS vs OOS says if the response replicates.
- 🤔 eta² is first-order: a pure-interaction parameter reads 0. For "does nothing", use the exact-duplicate test (`knowhow/sqx-format/`, `research/eta-squared-vs-duplicates`).

## Evidence
11–13k permutations per XAUUSD run:

| strategy | params | eta² ≥ 0.01 either window | grid before | after |
|---|---|---|---|---|
| `17.9.39` | 8 | 3 | 2.3e7 | 7.2e2 |
| `23.16.37` | 11 | 6 | 3.2e11 | 6.3e6 |
| `1.19.29` | 10 | 8 | 6.0e9 | 4.7e7 |
| `41.5.25` | 12 | 9 | 1.4e11 | 4.1e8 |
| `4.33.46` | 9 | 7 | 7.2e8 | 1.0e8 |

- Top: `DICrossPeriod1` 0.28, `DICrossShift1` 0.23 (`17.9.39`); `KCBarCloseserShift1` 0.41 (`41.5.25`); rest < 0.01.
- Profile correlation: `4.33.46` / `ATRPrcRnkCrsDwnATRPrd1` +0.95 (eta² 0.17/0.14) — matters and holds.
  `17.9.39` / `DICrossPeriod1` −0.47 despite eta² 0.28 — best in 2008–2017 among worst in 2018–2022.
