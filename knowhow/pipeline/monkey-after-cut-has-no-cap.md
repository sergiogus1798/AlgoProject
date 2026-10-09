---
q: Why did a run sit for hours in "paso 8 · python" after the judge?
kw: paso 8 python hours, estado.txt [4/13] paso 8, monkey after cut serial, 1352 survivors limbo, run never finishes step 8, no cap on survivors
tag: 🔬  date: 2026-10-09  see: pipeline/monkeyexcess-after-the-cut, research/step8-gate-measured-on-six-populations
---
# The after-cut `monkey` runs once per survivor, serially, ~12 s each, and nothing caps the survivors
With the usual 2-75 survivors it is 36-275 s. Before waiting on a run, read the judge line of `resumen.md`:
if step 8 left hundreds, the after-cut monkey takes hours. `estado.txt` shows only «[4/13] paso 8 · python».
A cap or a fan-out is the owner's decision (not done).

## Evidence
- 🔬 cal6 (NIKKEI225 H1 aroonLong, 2026-10-09): 1,352 survivors in limbo; the monkey ran 6 h 30 min without finishing (1,960 strategy folders written) until cancelled. Folder: `AlgoData/autopilot/Test_<...>_cal6/`.
