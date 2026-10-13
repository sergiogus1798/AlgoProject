---
q: Why does step 8's falsePositives take 25-120 min, and does population size matter?
kw: falsePositives slow, step 8 wall time, level3c redraw 5000 draws, monkeys 5000 x 4 levels, USATEC M15 7312 s, cache 3c draws, planted per-identity constant
tag: 🔬  date: 2026-10-12  see: perf/autopilot-dead-time, research/step8-gate-measured-on-six-populations
---
# Step 8 `falsePositives` costs by monkey trades (5,000 monkeys x 4 levels), not by population size
It was 70-84 % of a whole run. Not: "the cost is level 3c per read". 🔬 Measured 2026-10-12 on the control run of 2026-10-11 (3,330 s at **5,000** draws; `gate/config.yaml` went to 100,000 on 2026-10-12): level 3ab in series (46-51 ms/strategy, ~44 %) plus `draws.save` (zstd 19, ~30 ms/strategy, ~27 %); level 3c only ~9 % (73 ns per valuation, fanout 48). Fixed 2026-10-13 (encargo 66 §2, bit for bit but the three unjudged rung columns): `keep_draws=False` in the control, 3ab per identity through `fanout.run` (root drawn once in the parent), 3c once for the four passes, `q_p`, level 2's moved excess and levels 0/1a shared. 🔬 NIKKEI M30, 200 monkeys, 2,000 draws: 79.5 s -> 11.6 s for the four monkey passes (`tests/test_perf66_fp.py`). At 100,000 draws the control is untested and cannot finish: ~8 GB of draws per pass in /tmp.

## Evidence
- 🔬 Budget table (`findings-FP.md`, 400-monkey NIKKEI harvest scaled to 5,000): 3ab compute ~1,475 s, draws.save ~900 s, 3c ~290 s, levels 0-2 ~286 s, load/walk ~40 s; sum ~3,000 of 3,330.
- 🤔 The old claim (3c redraws the null per planted level) is still true in code but is not the main cost; profile to confirm after fixes.
- 🔬 Wall time, 2026-10-08/09: six H1/M30 runs with the old 75/year ceiling 1,569-2,520 s; EURUSD H1, 10,000 strategies, no ceiling 3,932 s; USATEC M15, 10,000 strategies 7,312 s; USATEC M15 with only 500 (median 122 IS trades/year) 5,159 s. Population size changes little; trades per monkey do.
