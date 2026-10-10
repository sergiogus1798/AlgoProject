---
q: How long do autopilot steps 13 to 16 take, and what does the spp skill's "half an hour per mother" get wrong?
kw: step 13 neighbours seconds per mother, MCR 1 Bar 7 OHLC, step 15 SPP IS OOS 757 s, spp report 25 s, crossTF 573 s, parada y export final 711 s, falsePositives 3169, whole run to step 12 105 min
tag: 🔬  date: 2026-10-10  see: perf/workflow-step-durations, perf/autopilot-dead-time
---
# Steps 13-16 cost minutes, not hours: ~17-21 s per mother at 13, 757 s for 10 at 15
Step 15 is NOT «half an hour per mother» (`.claude/skills/spp/SKILL.md`, 2026-09-22, 22 parameters).
Whole run to step 12 with 10,000 strategies: 105-107 min on NIKKEI H1, of which falsePositives 3,169-4,065 s.
🤔 mc3 (DAX40 M30, 10 mothers): crossTF 573/582 s vs 63-96 s on H1/9 mothers. `fases.csv` has ONE row for the
study (`test crossTF`), none inside it: the cell nulls (`cells.numbers`, `engines.nulls.simulate`) are priced per
cell on its own bars and an M30 mother adds M15 cells (4x H1's bars); not profiled, so a guess.
🔬 «parada» 513/711 s = `liverun.close`: `live.sync` + `export` + `live.stop`; the export is 14 s/196 s and the stop
~10 s/>300 s («custodian still here after 300 s», salida.txt:502); `live.sync` is not timed in `fases.csv`.

## Evidence
Runs of 2026-10-09/10 (`AlgoData/autopilot/<P>/<stamp>/`; 10,000 drawn, 30 min build):
| step | NIKKEI H1, 9 mothers | NIKKEI H1, 50 | DAX M30, 10 |
|---|---|---|---|
| 13 neighbours | 179 s | 844 s (execute 447, export 290) | 214 s |
| 13 MCR (1 Bar + 7 OHLC) | 58 s | 125 s | 71 s |
Step 14 study 32-38 s. Step 15 SPP IS + OOS: 757 s for 10 strategies (587 s in SQX). Step 16 spp report: 25 s for 10.
