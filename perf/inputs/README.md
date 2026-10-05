# perf/inputs — what is measured, and on which data

Configuration only. Nothing here times anything; `perf/measure/` does that.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | reads `perf/config.yaml` and applies `--set` overrides | imported | overrides → the whole config |
| `sample.py` | finds the real files a target runs on: newest export, fixed file order | imported | config → paths and bytes |
| `targets.py` | the registry — one row per comparable number, with its area and its unit | imported | names → target entries |
| `workloads.py` | the analysis work: Monte Carlo, retest read-back, cross-market kernel | imported | config → scale and bytes read |
| `construct.py` | the portfolio engine's work: one archived strategy through the universe, the close-to-close panel of 64 strategies of one harvest (`equity/closecurve`, 🔬 2026-10-04: 0.55 s CPU per strategy, ~2 min for 3,700 on 16 cores), a 500-strategy pairs table on every core, and a GA's 30,000 combinations scored by ranks (🔬 2026-10-04: 24 s on one core, 1,270 combinations/s, 183 MB), and one 5-member combination through stage B at the committed knobs — 11 path sets × 10,000 paths × 100 risk settings (🔬 2026-10-05: 4.0 s wall, 46 s CPU, 670 MB). `verdict_null`: the real verdict's oos1 null at the committed knobs — 10,000 random 5-member combinations of a 50-member pool measured on two years over four shifted starts and ranked (🔬 2026-10-05: 9.9 s, 390 MB, measured with other work on the cores); and the funded bank table (`portfolio.funded_bank`: 10,000 synthetic paths × 504 days, every universe plan × add-on × risk × re-buy policy = 2,610 configurations; 🔬 2026-10-05: 126 s wall, 518 s CPU with the machine at load 90 — 86 s on the real path set of that size; the owner's unset inputs are given test values that only size the workload). `weights_wf` (`portfolio.weights_wf`): the weight walk-forward's maths on a synthetic 5-member portfolio, 8 years to estimate and 4 to test, four methods re-estimated each January, 2,000 resamples (🔬 2026-10-05: 0.26 s, 320 MB with the imports; `wf.confidence` given a test value that only sizes the workload). ⚠ the universe reads each feed's time zone from the master's `data.db` read-only (`sqx.inspect.feeds`) — the one file of an install a target opens | imported | config → scale |
| `parsers.py` | the reading work: trade CSVs, bars, `.sqx` XML and statistics | imported | config → scale and bytes read |

**No target ever touches StrategyQuant X.** Every one of them reads files already exported
under the data root — never the install, never the worker, never a databank in memory. A
catalogue that needed SQX up could not be run while a build is running, which is exactly
when the owner most wants to know what the machine is doing.

**The `.sqx` files come from the export, not from `user/projects/`.** Hard rule 1: what is on
the master's disk is whatever the last sync left there. The export is immutable, so the same
twenty files are parsed every time.
