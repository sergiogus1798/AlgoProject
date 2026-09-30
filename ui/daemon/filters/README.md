# ui/daemon/filters — the databank filters of Proyecto, and their ledger rows

Encargo 22 §7.1 and §7.2 points 1-2 (plan 24, front F6). A filter is a **view in Python**: it
hides strategies in the window and never touches SQX — the databank there keeps every `.sqx`
until «Continuar workflow» (F7) applies the discards through `/curate`. What it does keep is a
record: the discards on disk, and one ledger row per filter or manual deletion, because a filter
is a search and the ledger exists to count them.

**Imports from:** `core.paths`, `ledger.{record, study}`, `sqx.projects.stage`,
`ui.daemon.{databank, runner.where, workflow.steps, results.catalogue}` · **Consumed by:**
`ui/daemon/routers.py` → `ui/desktop/workspace/filters.py` (+ `filterrow.py`), `workspace/funnel.py` (`/state`'s
`rows`), F7's `ui/daemon/advance/` (the discards it curates)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | — | — |
| `discards.py` | The append-only `AlgoData/filters/<P>/<D>/discards.jsonl`: an `applied` line per filter or deletion (origin, expression, ts, n_in, n_out, and a filter's `rows`), one line per identity set aside, a `clear` line for «quitar filtros» (and the `cut` of «Continuar»); replayed after the last clear as **the latest filter + every manual deletion** (`current`, `live`, `hidden`, `steps`) | imported | log ↔ hidden identities, funnel steps |
| `saved.py` | Filters saved by name in `AlgoData/filters/saved.yaml` | imported | name, rows ↔ yaml |
| `dists.py` | Every per-strategy `distribution` block of a project's reports by identity, and the median mode: with two samples, the last one's median inside the first one's central X % (read off its density histogram); with one, the real value inside the draws' X % (the stored percentiles) | imported | `reports/<P>/*/<day>/<study>/estrategias/*.json` → blocks |
| `evaluate.py` | The metrics a filter may read (the table's real columns and the distributions, OOS2 left out), each with its words (`named`: «Cross-timeframe · H1 · p», as the table heads it), the checks, the expression text in those words (the ledger's `criterion`; the machine form stays in `thresholds`) and the AND over the visible rows | imported | table, rows → dropped identities |
| `ledgerrow.py` | The row's study (Q9: `<symbol>_<timeframe>_<template folder>` from `registry.csv`; none → the filter is refused), its step (the Python step that reads the stage whose task writes the databank: `Results` → 8) and segment, written through `record.log` | imported | filter → one ledger row |
| `api.py` | The eight routes as `ROUTER`, every failure an `error` field: metrics, `preview` (counts only), apply, discard, clear, state, saved ×2 | imported | request → JSON |
| `view.py` | What the strip and the funnel read: `state_of` (hidden ids, steps, manual count, the `conditions` in force, a `stale` old filter read back into rows by `recovered`), the funnel's rows and their why in the glossary's words | imported | log → state |

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
  `core/paths.py`, which is at its 250-line limit. The table itself drops
  wfc/cscv/wfm/blindJoint while the blind door is shut, and `evaluate.refused` keeps OOS2 columns
  out of the dropdown — both only under `ALGO_AUTONOMOUS=1` (`core.assetdata.enforced`); for a human it is always open (owner, 2026-09-28).
- **The latest filter decides** (owner, 2026-09-28: «si aflojo, que vuelvan a aparecer»).
  «Aplicar» judges the rows on **the whole databank** (since the last clear or cut) and
  replaces the filter in force: loosening brings strategies back, tightening hides more. Its
  `n_in` is the databank's identified rows. `/preview` answers the same counts while the owner
  types, and writes nothing — no discard, no ledger row; only «Aplicar» is a search. A re-apply
  is `same` (nothing logged) only when the conditions **and** the judgement over the table now
  (its `n_in`, the identities it drops) equal the filter in force (`discards.unchanged`): after
  SQX adds or deletes strategies, «Aplicar» re-judges, hides the newcomers and forgets the
  identities the table no longer holds. «Aplicar» with no condition lifts the
  filter (an `applied` line with `rows: []`, no ledger row) and keeps the manual deletions.
- **One `context` per request.** `/state` with a databank answers the strip's whole refresh —
  funnel rows, state and the metric dropdown — off one table read (~0.13 s warm); `/metrics`
  stays for other callers. The strip calls `/state` on every table refresh and `/preview` on
  edits, both off the GUI thread.
- **Truncated logs.** Discard lines with no `applied` header before them since the last clear
  are skipped and counted (`state.orphans`), never hidden.
- **Manual deletions stack** and survive every re-filter; «Quitar filtros» lifts both. What
  «Continuar workflow» cuts (`discards.live`) is exactly what the table hides: the filter in
  force plus the manual deletions. A deletion counted with no filter in force enters from the
  table's identified rows now (`steps(total=…)`); the funnel, which reads no table, uses the
  `total` its header recorded.
- **Old logs.** A header without a `rows` key was written by the stacking version (before
  2026-09-28) and judged on what earlier filters left: it cannot be replayed alone. If the latest
  filter is one, no filter is in force (only manual deletions hide), `state.stale` names it, and
  `view.recovered` reads its expression back into the strip's rows so one «Aplicar» restores it.
- **The databank on disk is untouched.** No route here writes under an install.

## Cost

Measured 2026-09-28 on `Test_USDJPY_donchianUpperCrossUp_M30` / `Results` (200 strategies, 408
per-strategy results): `metrics` 2.4 s cold (the distribution blocks parsed once, cached by
mtime), `apply` 0.5 s warm; the table and distributions warm, 0.14 s — what makes `preview` on
every edit (the strip waits 350 ms after the last keystroke) cheap enough.
