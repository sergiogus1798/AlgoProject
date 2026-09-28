# ui/daemon/results — the read side of the study results

What every study already said, read off `AlgoData/reports/<P>/<D>/<day>/<study>/` and served as
the contract of `core/study/CONTRACT.md`: the catalogue of studies, one stored result with its
staleness, its history, the configuration drawer, and the population matrix. Read-only: nothing
here writes into the data root or runs a study (that is `ui/daemon/runner/`) — except `rerun.py`,
the command a `↻ solo …` job runs, which writes one partial result beside the stored one.

**Imports from:** `core.paths`, `core.study.config`, `ui.daemon.runner.table`, each study's own config loader and
`tooltips.py`, `ui.daemon.runs.guess_asset` · **Consumed by:** `ui/desktop/` through `/api/*`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names the package; holds no code | — | — |
| `catalogue.py` | Every study: family, Spanish title, WORKFLOW step, **role** (gate vs describe, one justified line each), `one/many/runnable/why_not` from `ui.daemon.runner.table` (one source with the runner), `source` (`reports` or `batch`) | imported | — → rows |
| `knobs.py` | A study's config through **its own loader** (so the hash matches what the study signs), the drawer's knobs with their tooltips, the hash a run would sign | imported | study + overrides → config, hash |
| `store.py` | Which days hold a study, one result read (or the reason it is not a contract result) with its `partials` — the re-runs kept beside it —, slim rows, `verdict.csv` (verdicts and every column) and a result's table blocks cached by file version and reader, verdict words on the five-state scale | imported | disk → dicts |
| `rerun.py` | One sub-test alone (crossmarket: a market; monteCarlo: a test by its title) written to `<study>/parciales/<stamp>_<only>/estrategias/<S>.json` beside the newest full result, never over it (OPEN §54) | `python3 -m ui.daemon.results.rerun --study crossmarket --project P --databank D --asset USDJPY --day YYYY-MM-DD --strategy S --only FEED` | export → partial JSON + HTML |
| `runs.py` | One stored result with `stale`, and every run of a study, for the population or one strategy | imported | query → result + meta |
| `matrix.py` | The population matrix: every strategy of one databank × every study, keyed by identity | imported | databank → cells |
| `api.py` | The seven routes, as `ROUTER` | imported | request → JSON |

## Routes

`GET /api/catalogue` · `GET /api/result?project&databank&study&strategy=&identity=&day=` ·
`GET /api/history?project&databank&study&strategy=&identity=` · `GET /api/config?study` ·
`POST /api/config/hash {study, overrides}` · `GET /api/matrix?project&databank` ·
`GET /api/projects`. Shapes as `scratch/ui-plan/SPEC.md` §2, plus these fields:
`meta.skipped` and `history.skipped` (newer days passed over, each with its reason),
`source=live|archive&version=` on `/api/result`, `/api/history` and `/api/matrix` (archive:
the strategy's archived version answers through `ui.daemon.strategy.archived`, computing nothing;
`/api/matrix` then needs `identity` and serves that one row),
`matrix.present` (the studies with at least one cell) and `matrix.skipped`
(`{path, reason, n}`), and the optional `identity` query parameter.

## Contracts and traps

- **Staleness is the study's own hash.** Several loaders merge `engines/variants/config.yaml` or
  replace `ledger:<key>` from `ledger/thresholds.yaml`; hashing `config.yaml` alone would mark
  every result stale. `knobs.LOADERS` names each study's loader. A new study adds one row there
  and one in `catalogue.STUDIES` and `catalogue.ROLE`.
- **Role = what `/curate` would do with its `verdict.csv`.** `/curate` drops exactly the rows
  that say `DESCARTAR`. `mcRetest` (FAIL…), `crossTF` (five readings), `wfm` (predicts/blind/
  perverse) and `exposure` (worth_it) never write it, so they are `describe` even though they
  judge. `edgeCost` and `feedQuality` become `gate` only when their `action` knob is `drop`, and
  `blindJoint` only when both `joint.pieces` and `joint.population` are set — the role is read
  from the current config, not frozen.
- **Pairing is by identity, and only inside one databank.** Measured 2026-09-26 on
  `USDJPY_workflow_profiling_v1`: the 8 strategies of `Retest_Markets_-_Family`, `MCR_All`,
  `WFM` and `CrossTF` share their names with `Results` but **none** of their identities (and
  `MCR_All` even drops the `Strategy ` prefix). So the matrix reads only `reports/<P>/<D>/`, and a
  cell comes from the newest day that judged that identity. A per-strategy JSON without identity
  (`wfm` signs `None`) takes the one its own run's `verdict.csv` gives the same name.
- **Older reports are data, not errors.** A JSON without `tabs` and `config_hash`, a
  `verdict.csv` without `strategy`/`verdict` (the Monte Carlo's tier tables), a folder that is not
  a catalogue study (`curate`, `monteCarlo_portfolio`) or a row with no identity (`edgeCost` and
  the older `crossmarket` tables carry none) are skipped with a Spanish reason and a count.
- **Studies that read a variant batch are not here.** `cloud`, `wfc` and `cscv` write into the
  batch's `estudios/`, not under `reports/`, so `/api/result` and the matrix do not reach them;
  the databank panel does (`ui/daemon/databank/batches.py`, by the mother's name).
- **Caches are keyed by file version.** A result's JSON is parsed once per (path, mtime);
  a config once per newest mtime of any YAML under `studies/ engines/ ledger/ portfolio/
  assets/`. `feedQuality`'s loader costs ~2 s uncached, which is why.

## Cost

Measured 2026-09-26 over a synthetic databank of 5,000 strategies (gate and snoopingScreen with a
JSON each, crossmarket as `verdict.csv` only — 10,000 JSON files and 15,000 CSV rows):
`matrix.matrix` 0.62 s the first time, 0.14 s cached; the HTTP route 1.0 s then ~0.27 s, 2.1 MB
of JSON. The first request that touches a study also imports its loader (gate ~0.5 s).
