---
q: Why did a run trimmed with --until mcretest|spp fail at step 13 with "None no esta en project.cfx"?
kw: None no esta en project.cfx, sqx.projects.wfc, no hay lote de variantes, marketSurfaces, --until spp, --until mcretest, workflow.trim, WFC 1 IS, neighbours.py, step 13 neighbours, plan halts at 16.5
tag: 🔬  date: 2026-10-10  see: pipeline/resumable-jobs
---
# `--until mcretest|spp` must keep the WFC legs: step 13's neighbours retest through them
Trap: `sqx.projects.workflow.trim` dropped the WFC legs, but step 13's neighbour batch
(`pipeline/autopilot/neighbours.py`) retests through them: «sqx.projects.wfc: None no esta en
project.cfx». Fix: `trim` keeps the `wfc` tasks whenever `mcretest` is kept. Second trap: with the legs
present the plan no longer stopped at 16 (only SQX-stage steps were checked for `missing`) and ran 16.5,
dying at 18.5 «no hay lote de variantes». Fix: `plan.py` halts at 16.5 when step 19 is `missing`.
🤔 The plan fix is unit-tested, NOT live-tested.

## Evidence
Runs 2026-10-09/10 in `AlgoData/autopilot/<P>/<stamp>/`: `Test_NIKKEI225_H1_aroonL_mc1` (failed at 13),
`..._mc1b` (`--until spp`), `Test_DAX40_M30_momentumL_mc3` (`--smoke --until spp`, failed at 18.5 before the plan fix).

Tests: `test_a_project_trimmed_to_spp_keeps_the_wfc_legs_step_13_runs_through`,
`test_a_project_trimmed_to_spp_ends_at_the_16_judge`. On mc3 the 16.5 ran for 3 mothers; the oos2 leg's
backtests are in `AlgoData/strategyPermutations/Test_DAX40_M30_momentumL_mc3/` and no study read them.
