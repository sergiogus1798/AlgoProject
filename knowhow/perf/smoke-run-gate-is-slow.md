---
q: Why does the gate take 386-447 s in a --smoke run instead of 47-88 s?
kw: smoke gate slow, judge.settings level 0 only, level 3ab serial 52 ms, gate 386 s, funnel.csv
tag: 🔬  date: 2026-10-12  see: perf/falsepositives-cost-scales-with-monkey-trades
---
# A `--smoke` run's gate is slow because only level-0 rules judge, so 3,400-4,100 strategies reach the serial level 3ab
Not a regression. In smoke `judge.settings()` keeps only level-0 rules, nobody falls after it, and 3,422-4,147 of the 10,000 strategies go through every level; level 3ab runs in series at ~52 ms each (~178 s of the 386 s). A full run leaves 299 after 1a and 258 at 3c (wf3; 29 in wf2). Population is always 10,000, so size does not explain it.

## Evidence
- 🔬 `findings-COSTES.md` §1: `smoke` mark exists in runs wf4s, mc5, mc2, chk9, not in wf3. Smoke harvests are gone (wf4s has 3 rows); the extrapolation uses wf3's first 100/1,000 strategies.
