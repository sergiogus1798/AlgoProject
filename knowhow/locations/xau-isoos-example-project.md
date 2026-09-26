---
q: example project XAU_ISOOS_ejemplo; reference fixture IS OOS two databanks; Results 120 OOS 115; test bench for gate snooping edgeCost perf harvest; acceptance disabled by hand; janitor retires it
tag: 📓  date: 2026-09-26  see: export/databank-metrics-is-oos, sqx-format/strategy-identity, research/post-selection-bias
---
# `XAU_ISOOS_ejemplo` on the custodian is the project's reference fixture: IS and OOS in two databanks
`~/Desktop/SQX_w2/user/projects/XAU_ISOOS_ejemplo/databanks/` — `Results` 120 `.sqx` (IS 2008–2017,
`Build strategies 2`) and `OOS` 115 (2018–2022, `Retest strategies` reading `Results`). Two tasks only.
The gate, snoopingScreen, edgeCost, `perf/config.yaml` and several cards run on it. **It proves the
chain, not the idea**: random Keltner builds, zero evidence. ⚠️ It predates the `Test_`/`Trade_` rule
and has 2 tasks, so `sqx/projects/sweep.py` retires it on the next Monday sweep unless renamed or excluded.

## Evidence
- Same file name in both databanks for 115 of 120 (`Strategy 1.10.59.sqx`); the 5 missing failed
  the retest. The filename pairing equals the normalised identity pairing (`strategy-identity`).
- The IS `.sqx` also carries `Results/CrossCheck_HigherPrecision/` (the cross-check runs only in the
  build); both carry `Results/Main: XAUUSD_DukasM1_Infinox_LOM_M30/`.
- Costs differ by window on purpose: build spread/slippage 5.0/2.5, retest 10.0/5.
- The retest's acceptance conditions were **disabled by hand**: with the donor's
  `AnnualPctReturn > 0` alive, 0 of 120 passed. So `OOS` is NOT selected on OOS — the contrast case
  in `research/post-selection-bias`.
- Built 2026-09-23 with `sqx.projects.builder` from `templates/library/keltnerUpperCrossUp`, `--role
  custodian --tasks Build,Retest --only Build-Task3.xml,Retest-Task1.xml --max-strategies 120 --minutes 12`.
  Harvested reports in `AlgoData/reports/XAU_ISOOS_ejemplo/`.
