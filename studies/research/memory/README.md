# research/memory — what was tried, where it died, and which ideas were spent

Phase 2 of the research director (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §4, §7).
Pure Python, read-only over its sources; it rebuilds its outputs from scratch each time, so there
is nothing to keep in sync. Outputs: `AlgoData/research/memory/` (`core.researchpaths.research_memory_dir()`).
Config (grid, families, archetype → family, asset → class, stage order): `config.yaml`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `sources.py` | Readers: `projects/registry.csv`, `templates/registry.csv`, `templates/runs.csv`, and every autopilot run's `resumen.md` (+ `fallo.md`) folded per project | imported | files → dicts |
| `attempts.py` | One row per project run (template × asset × timeframe × direction): the funnel per stage, where it died, survivors, outcome, hours | imported | sources → `COLUMNS` rows |
| `ideas.py` | Every `### Idea N` of `AlgoData/ideas/<SYMBOL>/*.md` with the hypotheses its file measured and whether it came from a book | imported | idea files → `COLUMNS` rows |
| `queries.py` | `untouched_cells`, `survivors_by_family`, `ideas_spent`, `grid` | imported | tables → rows |
| `verdict.py` | `close_run(run_dir)`: closes the project's row in `runs.csv` with its funnel and a verdict sentence | `python3 -m studies.research.memory.report --close <run_dir> [--runs-csv X]` | a finished run → runs.csv row |
| `report.py` | The command: rebuilds the five CSVs, prints the summary | `python3 -m studies.research.memory.report [--out DIR]` | sources → `attempts.csv`, `ideas.csv`, `ideas_spent.csv`, `survivors_by_family.csv`, `untouched_cells.csv` |

## Traps

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
  the funnel comes from the autopilot's own summary.

Manual: `AlgoData/manual-fuentes/81-memoria-de-resultados.md`. Test: `tests/test_research_memory.py`.
