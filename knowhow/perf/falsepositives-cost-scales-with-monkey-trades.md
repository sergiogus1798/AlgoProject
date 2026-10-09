---
q: Why does step 8's falsePositives take 25-120 min, and does population size matter?
kw: falsePositives slow, step 8 wall time, level3c redraw 5000 draws, monkeys 5000 x 4 levels, USATEC M15 7312 s, cache 3c draws, planted per-identity constant
tag: 🔬  date: 2026-10-09  see: perf/autopilot-dead-time, research/step8-gate-measured-on-six-populations
---
# Step 8 `falsePositives` costs by monkey trades (5,000 monkeys x 4 levels), not by population size
It was 70-84 % of a whole run. 🤔 Inferred from reading, not profiled: `studies/screening/gate/level3c.py` redraws the same 5,000-draw distribution for the null and each planted level, although `planted` only adds a per-identity constant to pnl (`studies/screening/falsePositives/model.py:123-126`); levels 2 and 3ab run in one process (`falsePositives/chain.py:278-286`). Proposed, NOT done: cache 3c's draws from the null pass (~30 lines, ~1 GB per rung, identical numbers with a fixed seed). Confirm by profiling one run.

## Evidence
- 🔬 Wall time, 2026-10-08/09: six H1/M30 runs with the old 75/year ceiling 1,569-2,520 s; EURUSD H1, 10,000 strategies, no ceiling 3,932 s; USATEC M15, 10,000 strategies 7,312 s; USATEC M15 with only 500 (median 122 IS trades/year) 5,159 s. Population size changes little; trades per monkey do.
