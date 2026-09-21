# perf/inputs — what is measured, and on which data

Configuration only. Nothing here times anything; `perf/measure/` does that.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | reads `perf/config.yaml` and applies `--set` overrides | imported | overrides → the whole config |
| `sample.py` | finds the real files a target runs on: newest export, fixed file order | imported | config → paths and bytes |
| `targets.py` | the registry — one row per comparable number, with its area and its unit | imported | names → target entries |
| `workloads.py` | the analysis work: Monte Carlo, retest read-back, cross-market kernel | imported | config → scale and bytes read |
| `parsers.py` | the reading work: trade CSVs, bars, `.sqx` XML and statistics | imported | config → scale and bytes read |

**No target ever touches StrategyQuant X.** Every one of them reads files already exported
under the data root — never the install, never the worker, never a databank in memory. A
catalogue that needed SQX up could not be run while a build is running, which is exactly
when the owner most wants to know what the machine is doing.

**The `.sqx` files come from the export, not from `user/projects/`.** Hard rule 1: what is on
the master's disk is whatever the last sync left there. The export is immutable, so the same
twenty files are parsed every time.
