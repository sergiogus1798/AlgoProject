# perf/inputs — what is measured, and on which data

Configuration only. Nothing here times anything; `perf/measure/` does that.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.py` | The single source of truth for what the catalogue measures and what it calls a regression. | imported | overrides → the whole config |
| `construct.py` | The portfolio engine's work the catalogue times: one universe member, a close-to-close panel, the pairs table, a rank search, stage B, the verdict's null, the bank table. | imported | config → scale |
| `gate.py` | The gate's levels, the monkey and `kept`, each timed on the same pinned slice of one harvest. | imported | config → scale and bytes read |
| `parsers.py` | The reading work the catalogue times: the formats every study opens before it can start. | imported | config → scale and bytes read |
| `sample.py` | Where the real files a measurement runs on are found, so two dates measure the same thing. | imported | config → paths and bytes |
| `targets.py` | The registry of everything the catalogue measures: one row is one comparable number. | imported | names → target entries |
| `workloads.py` | The real analysis work the catalogue times: one call each, on data already on disk. | imported | config → scale and bytes read |

**No target ever touches StrategyQuant X.** Every one of them reads files already exported
under the data root — never the install, never the worker, never a databank in memory. A
catalogue that needed SQX up could not be run while a build is running, which is exactly
when the owner most wants to know what the machine is doing.

**The `.sqx` files come from the export, not from `user/projects/`.** Hard rule 1: what is on
the master's disk is whatever the last sync left there. The export is immutable, so the same
twenty files are parsed every time.
