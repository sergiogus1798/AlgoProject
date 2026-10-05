# Steps 5-25 as the autopilot runs them

Sources: `pipeline/autopilot/{plan.py,criteria.yaml,README.md}`, `sqx/projects/{stages.yaml,workflow.py}`,
`ui/daemon/launch/steps.py`, a real `plan.json` (`Test_NIKKEI225_M30_simpleL_fin/20261005-160743`).
`?` = not established by those sources. A judge row after a python step is the same step number.

| step | kind | what runs | reads | fills | cut (criteria.yaml) |
|---|---|---|---|---|---|
| 5 | python (before the run) | `sqx.projects.builder --workflow` (+ `--palette`) | - | the project, every step's task | - |
| 6 | sqx | task `CONSTRUCCION` | - | `Results` | - |
| 7 | sqx | task `OOS` (run chained with 6) | `Results` | `OOS` | - |
| 8 | python | gate, edgeCost, feedQuality, spread, isOos, filters, decay, monkeyExcess, falsePositives, monkey, then profitShape, entryQuality | `OOS` (+ build) | facts | - |
| 8 | judge | rules of step 8 (R1-R9) + dev draw | facts | `paso-8/` | `OOS` |
| 9 | sqx | `Retest Markets - Family` | `OOS` (the cut's databank) | `Retest Markets - Family` | - |
| 10 | python | crossmarket | `Retest Markets - Family` | facts | - |
| 10 | judge | `excess_t_vs_main_half`, `excess_t_pooled` | facts | `paso-10/` | `Retest Markets - Family` |
| 10.5 | python (inside 11) | `sqx.projects.crosstfload`: survivors scaled, loaded with the worker stopped | `Retest Markets - Family` | `CrossTF_Input` | - |
| 11 | sqx | `CrossTF` | `CrossTF_Input` | `CrossTF` | - |
| 12 | python | crossTF | `CrossTF` | facts | - |
| 12 | judge | `crossTF.combined.z_new` | facts | `paso-12/` | `CrossTF` |
| 13 | sqx | `MCR 1 Bar` .. `MCR 8 Stress` (MCR 4 MinDist only for stop/limit orders) | `CrossTF_Mothers` (copied from `CrossTF` before 13) | `MCR 1`..`MCR 8` | - |
| 14 | python | mcRetest | `MCR *` | facts | - |
| 14 | judge | `mcRetest.stress.la_cola.profit_factor_p5` | facts | `paso-14/` | `MCR 8 Stress` |
| 15 | sqx | `SPP IS`, `SPP OOS` | `MCR 8 Stress` | `SPP IS`, `SPP OOS` | - |
| 16 | python | spp | `SPP IS/OOS` | facts | - |
| 16 | judge | no rules (`rules: []`) | facts | `paso-16/` | `SPP OOS` |
| 16.5 | variants | `pipeline.autopilot.variants`: wire WFC legs, per mother make, execute, equity, collect, clear | survivors in `SPP OOS` matched to `SPP IS` | `WFC_Variants` -> `WFC_Build`/`WFC_OOS1`/`WFC_OOS2` | - |
| 17 | blind | wfc | per mother | `paso-17` results | - |
| 18 | blind | cscv | per mother | results | - |
| 18.5 | blind | marketSurfaces | per mother | results | - |
| 19 | sqx | `WFM`, then its reading and the ledger rows 17-19 | `SPP OOS` | `WFM` | - |
| 20 | joint | blindJoint, then judge | 17, 18, 18.5, 19 | `paso-20/` | none named (`steps` has no "20") |
| 21 | reading | exposure | panel `CrossTF_Mothers` (`--panel 21=`) | window results | - |
| 22 | reading | conditionalMap | panel `Results` (`--panel 22=`) | window results | - |
| 23 | structural | structural (ablations, order inversion) | the mothers left | `AlgoData/structural/<P>/<stamp>` | - |
| 24 | stop | atrCalculator, two stopgrid passes | the mothers left | `AlgoData/atrCalculator/<P>/<stamp>` | - |
| 25 | edge | edgeCost per version at stop p90 (`Stop_p90`) | step-24 variants | `finalistas.json` | - |

Notes
- Variant databanks of 16.5: `WFC_Variants` in; `WFC_Build`, `WFC_OOS1`, `WFC_OOS2` out; emptied after each mother.
- Only steps 8, 10, 12, 14, 16 have a `cut` in `criteria.yaml`; a step with rules and no `cut` stops the run. 20-25 do not cut.
- The run stops before step 26 (MT5) unless `--mt5-from`, `--mt5-to`, `--mt5-model`, `--mt5-firms` are all given.
- Outputs: `AlgoData/autopilot/<P>/<stamp>/{estado.txt,resumen.md,tiempos.md,fallo.md,plan.json,paso-<n>/}`.
- `fallo.md` exists only if the run failed; `estado.txt` last line is `FIN · …` or `FALLO en el paso N: …`.
