# sqx/inspect/strategymeta — one strategy's metadata as fields

Read-only, off the files: the `.sqx` (and, when given, its `project.cfx`). Never a call to SQX.
The keys `read()` returns are listed in `__init__.py`'s docstring; the window's strategy panel and
the strategy archive consume them.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | `read(sqx_path, project_cfx=None) -> dict`: composes the two modules below | imported | `.sqx` [+ `.cfx`] → dict |
| `__main__.py` | The CLI: prints `read()` as JSON | `python3 -m sqx.inspect.strategymeta <file.sqx> [--cfx <project.cfx>]` | → stdout |
| `rules.py` | `strategy_Portfolio.xml`: direction, entry and exit conditions with their values, entry orders and their exit methods | imported | parsed XML → rows |
| `settings.py` | `settings.xml` and `lastSettings.xml`: trading options, the last test's window, costs and sizing; the `.cfx` tasks writing a databank; today's asset card hash | imported | `.sqx`/`.cfx` → dicts |

Three sources, three meanings. `last_test` is what the stored results were computed with
(`lastSettings.xml`, inside the `.sqx`). `backtest` is what the project's task says **today** —
it can differ if someone edited the task after the run, and then a note says so. The asset card
hash is today's file: `assets/` keeps no history.

A task's costs live in `Data/Setups/Setup`, or in `CustomData/Setups/Setup` for an
AutomaticRetest (MC, SPP, WFM, retest on markets); a CustomAnalysis has none (`costs` None), and a
task whose member the `.cfx` lacks comes back with an `error`. `read()` never raises on a real
project: 57 databanks of the three installs, each with its `.cfx`, 0 failures (2026-09-27).
