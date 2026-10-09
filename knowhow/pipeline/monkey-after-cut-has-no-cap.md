---
q: Why did a run sit for hours in "paso 8 · python" after the judge?
kw: paso 8 python hours, estado.txt [4/13] paso 8, monkey after cut serial, 1352 survivors limbo, run never finishes step 8, no cap on survivors
tag: 🔬  date: 2026-10-09  see: pipeline/monkeyexcess-after-the-cut, research/step8-gate-measured-on-six-populations
---
# The after-cut `monkey` runs once per survivor, ~12 s each: eight at a time since 2026-10-09, one by one before
One by one, the usual 2-75 survivors took 36-275 s and 1,352 survivors held a run 6 h 30. Now
`ui.daemon.jobs.width` runs `PICKED["monkey"]` = 8 at once (1.9 GB each, inside Python's 20 GB): ~35 min
for 1,352. Nothing caps the survivors: before waiting on a run, read the judge line of `resumen.md`;
`estado.txt` shows only «[4/13] paso 8 · python».

## Evidence
- 🔬 cal6 (NIKKEI225 H1 aroonLong, 2026-10-09): 1,352 survivors in limbo; the monkey ran 6 h 30 min without finishing (1,960 strategy folders written) until cancelled. Folder: `AlgoData/autopilot/Test_<...>_cal6/`.
