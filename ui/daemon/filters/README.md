# ui/daemon/filters — the databank filters of Proyecto, and their ledger rows

Encargo 22 §7.1 and §7.2 points 1-2 (plan 24, front F6). A filter is a **view in Python**: it
hides strategies in the window and never touches SQX — the databank there keeps every `.sqx`
until «Continuar workflow» (F7) applies the discards through `/curate`. What it does keep is a
record: the discards on disk, and one ledger row per filter or manual deletion, because a filter
is a search and the ledger exists to count them.

**Imports from:** `core.paths`, `ledger.{record, study}`, `sqx.projects.stage`,
`ui.daemon.{databank, runner.where, workflow.steps, results.catalogue}` · **Consumed by:**
`ui/daemon/routers.py` → `ui/desktop/workspace/filters.py`, `workspace/funnel.py` (`/state`'s
`rows`), F7's `ui/daemon/advance/` (the discards it curates)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | — | — |
| `discards.py` | The append-only `AlgoData/filters/<P>/<D>/discards.jsonl`: an `applied` line per filter or deletion (origin, expression, ts, n_in, n_out), one line per identity set aside, a `clear` line for «quitar filtros»; replayed after the last clear | imported | log ↔ hidden identities, funnel steps |
| `saved.py` | Filters saved by name in `AlgoData/filters/saved.yaml` | imported | name, rows ↔ yaml |
| `dists.py` | Every per-strategy `distribution` block of a project's reports by identity, and the median mode: with two samples, the last one's median inside the first one's central X % (read off its density histogram); with one, the real value inside the draws' X % (the stored percentiles) | imported | `reports/<P>/*/<day>/<study>/estrategias/*.json` → blocks |
| `evaluate.py` | The metrics a filter may read (the table's real columns and the distributions, OOS2 left out), each with its words (`named`: «Cross-timeframe · H1 · p», as the table heads it), the checks, the expression text in those words (the ledger's `criterion`; the machine form stays in `thresholds`) and the AND over the visible rows | imported | table, rows → dropped identities |
| `ledgerrow.py` | The row's study (Q9: `<symbol>_<timeframe>_<template folder>` from `registry.csv`; none → the filter is refused), its step (the Python step that reads the stage whose task writes the databank: `Results` → 8) and segment, written through `record.log` | imported | filter → one ledger row |
| `api.py` | The seven routes as `ROUTER`, every failure an `error` field; the funnel's why in the glossary's words (`ui.text.glossary.label`, a pure function without Qt) | imported | request → JSON |

## Contracts and traps

- **Logged first, then hidden.** `apply` and `discard` write the ledger row before the
  discards; a row the door refuses (`gate.allow`) leaves nothing hidden. A project without a
  template in `registry.csv` has no study to sign, and its filter is **refused**, not applied
  unlogged (plan 24 Q9, applied reading).
- **One row per filter**, whatever it reads: segment `build` when it read only IS columns,
  `oos1` otherwise (an OOS column, a study column, a distribution); the note lists what it read.
  `thresholds` holds the rows. A manual deletion reads everything the table shows: `oos1`.
- **AND only** (Q15). Rows combine with AND; only a strategy whose value fails a row is hidden.
  One with no value for a row's metric **stays visible**, counted as `blank` («sin valor») in
  the answer, the `applied` line, `/state`'s steps and the funnel's why (orchestrator, 2026-09-28).
- **OOS2 never.** Metric columns whose sample is OOS2, any column named `oos2`, and the studies
  that may read it are not offered: `wfm`, `blindJoint`, `cscv`, `marketSurfaces`,
  `atrCalculator`, `exposure`, plus the studies of every step `_policy.yaml` reserves the asset's
  oos2 for (`evaluate.refused`, through `ledger.gate.reserved`). The databanks of the `wfc` and
  `wfm` stages are refused whole.
- **Values are numbers.** The window sends text; `evaluate.normal` turns every numeric value into
  a float before the ledger's `thresholds` and `saved.yaml` see it.
- **Rows without identity** cannot be hidden: counted as `anonymous` in the `applied` line,
  `/state`, `/metrics` and the funnel («N sin identidad, no filtrables»).
- **One root.** `discards.root()` is `AlgoData/filters/`; `saved.yaml` sits in it. It is not in
  `core/paths.py`, which is at its 250-line limit. The table itself already drops
  wfc/cscv/wfm/blindJoint while the blind door is shut.
- **Filters stack.** Each one runs on what the earlier ones left visible: its `n_in` is the
  visible count, not the databank's. «Quitar filtros» brings everything back; the ledger keeps
  every row — what was looked at stays looked at.
- **The databank on disk is untouched.** No route here writes under an install.

## Cost

Measured 2026-09-28 on `Test_USDJPY_donchianUpperCrossUp_M30` / `Results` (200 strategies, 408
per-strategy results): `metrics` 2.4 s cold (the distribution blocks parsed once, cached by
mtime), `apply` 0.5 s warm.
