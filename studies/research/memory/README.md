# research/memory — what was tried, where it died and why, and which ideas were spent

Phase 2 of the research director (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §4, §7).
Pure Python, read-only over its sources; it rebuilds its outputs from scratch each time, so there
is nothing to keep in sync. Outputs: `AlgoData/research/memory/` (`core.researchpaths.research_memory_dir()`).
Config (grid, families, archetype → family, asset → class, stage order, **the vocabulary of causes**,
the hypothesis sheet's tolerance, the reviewer's switch): `config.yaml`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `attempts.py` | The attempts table: one row per project run of a template on an asset, timeframe and direction. | imported | sources → `COLUMNS` rows |
| `causes.py` | Why a run died: one cause of a closed vocabulary, from the reasons the autopilot's judge wrote. | imported | `paso-<n>/verdict.csv` + the outcome → one cause of `config.yaml` › `causes.vocabulary` |
| `ideas.py` | The ideas index: every idea the ideaExpert proposed, chosen or not, and what finding it cost. | imported | idea files → `COLUMNS` rows |
| `queries.py` | The questions the board asks of the memory: untouched cells, what survived, what was spent. | imported | tables → rows |
| `report.py` | The command: rebuilds the attempts table and the ideas index, writes them, prints a summary. | `python3 -m studies.research.memory.report [--out DIR]` · `--cell XAUUSD H1 long ruptura` | sources → `attempts.csv`, `ideas.csv`, `ideas_spent.csv`, `survivors_by_family.csv`, `untouched_cells.csv`, `failures.csv` |
| `sheet.py` | The hypothesis sheet: what an idea predicts before its build, its seal, and what the build did. | imported | proposals + `raw/<P>/Results/<day>/trades.parquet` → ratios and `hypothesis` |
| `sources.py` | Readers of the memory's sources: the two registries, runs.csv and the autopilot's resumen.md. | imported | files → dicts |
| `trials.py` | What the research spent on one ledger study: the hypotheses measured before any search row. | imported by `ledger.report` | ideas index + template registry → K |
| `verdict.py` | The verdict writer: closes a finished autopilot run's row in templates/runs.csv. | `python3 -m studies.research.memory.report --close <run_dir> [--runs-csv X]` | a finished run → runs.csv row |

## Why a run died (encargo 42, front B)

Every attempt carries `cause`, one word of a closed vocabulary that is **data**
(`config.yaml` › `causes`, `status: approved`: the 12 causes were approved by the owner on 2026-10-02), with what
it rules out and what to try next. Pattern: the typed failure record of
`hch-wang/Negative_Knowledge` (MIT) — the schema idea, no code.

- **Where it comes from.** The autopilot's judge writes each strategy's reason as
  `<state>: <fact>=<value>` parts (`pipeline/autopilot/criteria.py`). Only `fail:` parts count;
  the fact names the cause through `causes.facts` (first pattern that matches). A dead run takes
  the cause that failed the most strategies in the `verdict.csv` of the step that emptied it
  (`causes.judged_at`); `cause_share` is «strategies it took / strategies that failed» and
  `causes` lists them all. No reason written (an SQX task left the databank empty by its own
  filters) → the stage's default (`causes.stage`).
- **`failed@<step>` is `infrastructure`**: typed, and never evidence — `queries.failures` leaves
  it out, as it leaves out a development draw (`dev_cut`).
- **The sheet.** An idea of a proposal carries `sheet` (trades a year and holding hours of the
  median built strategy, where it should not work, what kills it), sealed by
  `board.proposal.stamp` (`sheet_seal`). On every rebuild `sheet.reading` compares it with the
  in-sample trades of the build's databank (`sheet.databank`, the newest export under `raw/`):
  `trades_ratio` and `holding_ratio` are built ÷ predicted. `hypothesis` is `match` or
  `mismatch` against `sheet.tolerance` — **owner, 2026-10-02: factor 2 either way**, on trades per
  year and on holding hours (clock hours, weekends included); it stays `pending` only if the
  value is set back to `pending`; `altered` when the sheet no longer matches its seal, `no_data` when
  the build was never exported, '' for an idea without a sheet.
- **A mismatch is one more cause**: `hypothesis_mismatch` is the `cause` of a run that did not
  die, and is appended to `causes` of one that did (its death stays the cause). A mismatch on a
  run with survivors is only annotated: it does not remove or demote them (`review.removes: false`;
  the reviewer annotates only, one pass, Opus).

## Traps

- **A two-sided rule needs `split`**: the judge's reason carries the fact and its value, not which
  of two rules on that fact failed. `is_trades_per_year` has a floor and a ceiling: the mapping
  tells them apart by a value between both. Move a band in `criteria.yaml` → check `split`.
- **A fact no pattern names is `unclassified`**, not an error: add its row to `causes.facts`.
- **The sheet's years are the population's**: first in-sample entry to last exit of the whole
  export, a little under the build window, so trades a year read slightly high.
- **Holding hours are by the clock**: a position held over a weekend counts its 48 hours.
- **The link from a run to its sheet is the name**: template name = idea name, newest proposal
  wins. A template built outside a proposal has no sheet.

- **A row is a project run, not a cell.** Several projects can share a cell (template × asset ×
  timeframe × direction); the board counts them.
- **`outcome` is derived, `verdict` is runs.csv's text.** Outcomes: `survivors` (reached 15 with
  some), `died@<stage>`, `failed@<step>` (inconclusive: a crash is not a verdict, and a zero after
  it is not a death), `incomplete@<stage>`, `unknown` (no autopilot run: only runs.csv/registry).
- **`dev_cut = yes`**: step 8 kept a random draw of 5 (`criteria.yaml` dev mode). Such a run proves
  the chain, says nothing about the family: `survivors_by_family` leaves it out of `closed` unless
  `include_dev=True`.
- **`resumen.md` can lose the failure**: the autopilot rewrites it in `finally` without the error;
  `fallo.md` is the reliable sign and is what `failed_at` reads.
- **Counts are the databank after each task** (`0 → N`): `crosstf_cells` counts siblings
  (mothers × timeframes), not mothers, so it is kept out of the funnel.
- **`custodian_hours` is wall time on the custodian** (sum of the runs' `Total`), not CPU hours:
  no source records CPU time. Empty = never ran under the autopilot.
- **`from_book` is `unknown`** unless the idea's section has an `Origen:` line; unknown is not no.
- The ledger is per study (asset × timeframe × family), not per project, so it is not read here;
  the funnel comes from the autopilot's own summary. The other way round it is: `ledger.report`
  reads `trials.spent` to add the hypotheses to its N.
- **`hypotheses_measured` is the largest «Hipótesis medidas: N» of the file**: an addendum restates
  the running total (24, then «29 (24 de antes + 5 nuevas)»), and the first match undercounted.

Manual: `AlgoData/manual-fuentes/81-memoria-de-resultados.md`. Test: `tests/test_research_memory.py`.
Cards: `knowhow/pipeline/typed-failure-causes.md`, `knowhow/research/hypothesis-sheet-vs-build.md`.
