---
q: decay measured after OOS filter, selection bias, strategies improve out of sample?, Sharpe retention 1.00 vs 0.45, gate reads inert on selected population, monkey p-values selected sample, generator decay
tag: 🔬  date: 2026-09-23  see: research/gates-are-owner-decisions, research/random-entry-nulls, research/is-proxies-top-decile
---
# A filter on the OOS spends the OOS
Any statistic measured after selecting on the OOS is biased toward zero decay or beyond (strategies seem to
"improve"). Measure decay on the unselected population as a generator diagnostic; keep selection filters on
IS-side columns only (`improvement.py` enforces it). Before reading gate results, know whether the population
was selected on that window: a selected one passes every screen and every null.

## Evidence
Unselected decay, 5 XAUUSD runs (~10,000 rows each), IS 2008–2017 vs OOS 2018–2022; median PF (IS) 0.98–1.01, 42.0–52.2 % profitable IS:

| | OOS | OOS-Sharpe | OOS-Rexpect | OOS-Rexpect2 | OOS-Rsquared |
|---|---|---|---|---|---|
| median Sharpe IS → OOS | −0.11 → −0.28 | 0.00 → −0.24 | 0.01 → −0.20 | −0.03 → −0.26 | −0.08 → −0.27 |
| median PF IS → OOS | 0.98 → 0.95 | 1.00 → 0.95 | 1.01 → 0.96 | 1.00 → 0.95 | 0.98 → 0.95 |
| profitable OOS | 26.9 % | 30.2 % | 33.5 % | 27.9 % | 25.3 % |

Generator decay: **−0.17 Sharpe, −0.03 PF**. Inside `Net profit (OOS) > 0` survivors (25.3–33.5 %) it flips to +0.10…+0.19 Sharpe, +0.03…+0.06 PF in all 5.

`studies/screening/gate/` on `XAUUSD/OOS` — the 231 `.sqx` on disk (owner-kept survivors, not the 10,000-row export), lax thresholds:
sanidad (≥20 OOS trades, no duplicate trade set) 2 died; estaticas (`Net profit (OOS) > 0`) 0 of 229; degradacion
(retention ≥ 0, t ≥ 0, ≥1 profitable year, concentration ≤ 1.0) 1; forma (max DD OOS/IS ≤ 5) 0; mono (p ≤ 0.50 `sharpe`, rung `timing`, 2,000 draws) 0 of 228.
Reconciliation 0.999999 on all 228 (pricing is not the cause). BH over 228 p-values names 146.

Contrast, `XAU_ISOOS_ejemplo` (build + separate retest task, 120 built, acceptance never read OOS): presencia 120→5 died
(SQX dropped them from the retest databank); sanidad 115→3; estaticas 112→48 (43 % lose OOS); degradacion 64→19; forma, mono 45→0. 45 survive.

| | `XAUUSD/OOS` (selected on OOS) | `XAU_ISOOS_ejemplo` (not selected) |
|---|---|---|
| profitable OOS | 229/231 (99 %) | 64/112 (57 %) |
| median Sharpe retention | **1.00** | **0.45** |
| median p vs monkey | 0.022 (worst 0.23) | **0.100** |
| beat monkey p ≤ 0.05 | 184/228 | **5/45** |

Operational: trade-level dedup found 2 clone pairs in 231 (identical trade sets, different hashes and names; cf. 45-of-231
in `studies/CLAUDE.md`) → dedup before expensive screens. Cost: harvest (staging, metrics + trade export, 231 zip reads) ~5 min of SQX;
whole cascade incl. 2,000 nulls = 0.1 s/strategy (no stops/targets → `barrier.exits()` fast path; changes with barriers).
Redundancy by structure: the 45 survivors are 13 distinct structures, one holds 24.
