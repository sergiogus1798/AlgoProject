# Steps 5-25 as the autopilot runs them

Sources: `pipeline/autopilot/{plan.py,criteria.yaml,README.md}`, `sqx/projects/{stages.yaml,workflow.py}`,
`ui/daemon/launch/steps.py`, a real `plan.json` (`Test_NIKKEI225_M30_simpleL_fin/20261005-160743`).
`?` = not established by those sources. A judge row after a python step is the same step number.

| step | kind | what runs | reads | fills | cut (criteria.yaml) |
|---|---|---|---|---|---|
| 5 | python (before the run) | `sqx.projects.builder --workflow --family <FAMILY>` (+ `--palette`) | - | the project, every step's task | - |
| 6 | sqx | task `CONSTRUCCION` | - | `Results` | - |
| 7 | sqx | task `OOS` (run chained with 6) | `Results` | `OOS` | - |
| 8 | python | gate, edgeCost, feedQuality, spread, isOos, filters, decay, monkeyExcess, falsePositives, monkey, then profitShape, entryQuality | `OOS` (+ build) | facts | - |
| 8 | judge | rules of step 8 (R1-R9) + dev draw | facts | `paso-8/` | `OOS` |
| 9 | sqx | `Retest Markets - Family` | `OOS` (the cut's databank) | `Retest Markets - Family` | - |
| 10 | python | crossmarket | `Retest Markets - Family` | facts | - |
| 10 | judge | P1-P9 of encargo 46 (`criteria.yaml` step 10, provisional): `invalid_fraction`, `fixed_distance`, `freq_off`/`freq_off_fraction`, `z_conj`, `z_conj_v2`, `z_minus_market`, `p_breadth`, `tau_half` (over `e_principal`, the main's own e on oos1, computed by crossmarket), `worse`/`worse_fraction`, `z_beta`+`e_end`; the study writes no verdict of its own | facts | `paso-10/` | `Retest Markets - Family` |
| 10.5 | python (inside 11) | `sqx.projects.crosstfload`: survivors scaled (M30 mothers: M15, H1, H4; per-bar coefficients ÷ the measured ATR ratio), loaded with the worker stopped | `Retest Markets - Family` | `CrossTF_Input` | - |
| 11 | sqx | `CrossTF`, `CrossTF <TF>` (oos1) | `CrossTF_Input` | `CrossTF`, `CrossTF_<TF>` | - |
| 11.5 | python | crossTF, new study phase 1 (T0, T2a, T3) | `CrossTF*` | facts `crossTF.tf.*` | none yet (`rules: []`, `cut: CrossTF_Input`, `siblings: follow`) |
| 11.7 | sqx | phase-2 tasks `CrossTF <TF> build`; skipped with a line if the project has none; does not refill `CrossTF_Input` | `CrossTF_Input` (as 11.5 left it) | `CrossTF_<TF>_build` | - |
| 12 | python | crossTF (adds the build: T1, T2b) | `CrossTF*`, `CrossTF_<TF>_build` | facts | - |
| 12 | judge | `crossTF.combined.z_new` | facts | `paso-12/` | `CrossTF` |
| 13 | neighbours | T1 (`pipeline.autopilot.neighbours`): each mother and her parameter neighbours through `WFC 1 IS` and `WFC 2 OOS1`, trades exported and priced; runs first, right after step 12's judge | the mothers in `CrossTF` (no scaled sibling) | `AlgoData/neighbours/<P>/<stamp>/`, `raw/<P>/T1_Neighbours/<day>/neighbours.parquet`; the WFC databanks emptied again | - |
| 13 | sqx | `MCR 1 Bar`, `MCR 7 OHLC` (+ `MCR 4 MinDist` only for stop/limit orders); MCR 2, 3, 5, 6, 8 are not run since 2026-10-07 | `CrossTF_Mothers` (copied from `CrossTF` before the start) | `MCR 1 Bar`, `MCR 7 OHLC`; at the stop, the `MCR_All` ingest (after the harvests) | - |
| 14 | python | mcRetest (T2 on `MCR 7`, T3 on `MCR 1`, T1 read from the neighbours' table) | the `MCR_All` ingest, `T1_Neighbours` | facts `mcRetest.fragilidad.t{1,2,3}.*` | - |
| 14 | judge | T1 build (`t1.build.ret_med`, `t1.build.f_pos`), T1 oos1 (`t1.oos1.ret_med`), T2 (`t2.build.ret_med_aprox`), T3 (`t3.build.ret_med`, never fails); provisional thresholds, a missing fact is limbo | facts | `paso-14/` | `MCR 7 OHLC` |
| 15 | sqx | `SPP IS`, `SPP OOS` | `MCR 7 OHLC` (a project built before 2026-10-07 still reads `MCR 8 Stress`: re-point it with `sqx.projects.spp --input "MCR 7 OHLC"`) | `SPP IS`, `SPP OOS` | - |
| 16 | python | spp | `SPP IS/OOS` | facts | - |
| 16 | judge | no rules (`rules: []`) | facts | `paso-16/` | `SPP OOS` |
| 16.5 | variants | `pipeline.autopilot.variants`: wire WFC legs; per mother make (Latin hypercube, 1,000-5,000 variants), execute, equity, collect, export every variant's trades, `variant_trades.parquet`, clear; then the mothers' trades and, with SQX idle, the parameter cloud (`studies.optimisation.cloud.report`) per batch. No rule, cuts nothing (`"16.5"`: `cut: null`) | survivors in `SPP OOS` matched to `SPP IS` | `WFC_Variants` -> `WFC_Build`/`WFC_OOS1`/`WFC_OOS2`; `estudios/cloud.json` (facts `vivos`, `r2_ajustado`, `legible`, `sobol_*`) | - |
| 17 | blind | wfc: three compositions (`c1` build+oos1 → oos2 decides, `c2`, `c3` annotated); `facts.c1.estado` `pasa` / `limbo` / `no_pasa` (1 / 0 / -1): PASA = order not perverse, top median > 0 AND `p_nivel` ≤ `wfc.level_alpha` (0.05, the level's own sign-flip null); top > 0 without beating the null (or a perverse order) = LIMBO; top ≤ 0 = NO PASA. **oos2 is sealed** by `ledger.gate.seal` unless `python3 -m studies.optimisation.wfc.calibrate` wrote a record with `abre: true` for the current `"17"` entry (2026-10-07: `abre: true`; if the entry changes the seal closes again — report it, never edit the record or the criteria). Judged **without cutting** (`cut: null`): a verdict and a ledger row, nothing deleted; step 20 reads NO PASA as a failure | per mother | `estudios/wfc.json`, `paso-17` results | - |
| 18 | blind | cscv | per mother | results | - |
| 18.5 | blind | marketSurfaces | per mother | results | - |
| 19 | sqx | `WFM`, then its reading and the ledger rows 17-19 | `SPP OOS` | `WFM` | - |
| 20 | joint | blindJoint, then judge | 17, 18, 18.5, 19 | `paso-20/` | `SPP OOS` |
| 21 | reading | exposure (describes only: no verdict, no efficiency threshold) | panel `CrossTF_Mothers` (`--panel 21=`) | window results | - |
| 22 | - | conditionalMap: DELETED 2026-10-11 | - | - | - |
| 23 | - | structural study: DELETED 2026-10-11 | - | - | - |
| 24 | - | ATR stop (atrCalculator): DELETED 2026-10-11 (pre-registered measurement read NO PASA, `portfolio/DECISIONS.md`); strategies trade with no per-trade stop and step 26 receives the mother's own .sqx | - | - | - |
| 25 | - | edgeCost per version: OUT of the chain (no step runs; `--strategy` mode stays standalone); the `finalists` action hangs from step 26 | - | `finalistas.json` | - |

Notes
- Variant databanks of 16.5: `WFC_Variants` in; `WFC_Build`, `WFC_OOS1`, `WFC_OOS2` out; emptied after each mother, once its trades are in `variant_trades.parquet`.
- Only steps 8, 10, 11.5, 12, 14, 16, 20 have a `cut` in `criteria.yaml`; steps 17, 18, 18.5, 19 have `cut: null` (judges and records without deleting); a step with rules and no `cut` stops the run. 16.5 and 21 do not cut.
- The run stops before step 26 (MT5) unless `--mt5-from`, `--mt5-to`, `--mt5-model`, `--mt5-firms` are all given.
- Outputs: `AlgoData/autopilot/<P>/<stamp>/{estado.txt,resumen.md,tiempos.md,fallo.md,plan.json,paso-<n>/}`.
- `fallo.md` exists only if the run failed; `estado.txt` last line is `FIN · …` or `FALLO en el paso N: …`.
