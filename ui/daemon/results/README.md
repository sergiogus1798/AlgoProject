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
| `__init__.py` | The read side of the study results: catalogue, stored results, history, config, matrix. | — | — |
| `api.py` | The results routes: catalogue, one stored result, its history, the config drawer, the matrix. | imported | request → JSON |
| `catalogue.py` | Every study the window can show: family, title, step, whether it eliminates, and how it is run. | imported | — → rows |
| `forproject.py` | A study's knobs as the window will run them for one project: the runner's substitutions, and the ones it does not make. | imported | study, sections, project → sections |
| `hits.py` | Every stored result that could answer for one strategy across the whole project, found cheaply: file stats and cached slim reads, never a full parse per question. | imported | project, study, strategy → hits |
| `knobs.py` | A study's knobs as its own loader reads them, their tooltips, and the hash a run would sign. | imported | study + overrides → config, hash |
| `matrix.py` | The population matrix: every strategy of one databank against every study, one state per cell. | imported | databank → cells |
| `presence.py` | Which studies have a result for one strategy anywhere in the project, and what each says — the strategy page's tabs and dots in one cheap answer. | imported | place → {study: cell} |
| `rerun.py` | One sub-test of a study run again alone, written beside the stored result and never over it (OPEN §54). | `python3 -m ui.daemon.results.rerun --study crossmarket --project P --databank D --asset USDJPY --day YYYY-MM-DD --strategy S --only FEED` | export → partial JSON + HTML |
| `runs.py` | A strategy's result as one entity across the whole project (owner, 2026-09-30): the one stored result its page shows, chosen among `hits.sources` — its identity first, else its name. | imported | query → result + meta |
| `slice.py` | A population result read for one strategy: only its rows, bars and grid line, said to be a view. | imported by `runs.result` | population result → the strategy's view |
| `stale.py` | Whether a stored result is «caducado»: no configuration the window could launch today for this project, the same way, would sign its hash. | imported | hash, project, manifest → stale |
| `store.py` | The stored reports of one databank: which days hold a study, one result read with its partial re-runs, and slim cached rows. | imported | disk → dicts |
| `tfrows.py` | The cross-TF rows with the T0-T4 reading beside the old one: `tf_*` columns, read from the study's two new files. | imported | verdict rows, folder → rows |

## Routes

`GET /api/catalogue` · `GET /api/result?project&databank&study&strategy=&identity=&day=` ·
`GET /api/history?project&databank&study&strategy=&identity=` · `GET /api/config?study&project=` (with a project, `forproject.apply`) ·
`POST /api/config/hash {study, overrides}` · `GET /api/matrix?project&databank` ·
`GET /api/projects` · `GET /api/presence?project&databank&strategy&identity=`. Shapes as `scratch/ui-plan/SPEC.md` §2, plus these fields:
`meta.skipped` and `history.skipped` (newer days passed over, each with its reason),
`meta.elsewhere` (the databank a result actually came from, None for this one),
`meta.other_identity` (the match found has a different identity) and `meta.note`,
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
  **And the run's own overrides** (2026-10-01): comparing with the bare config marked 14 of 15
  H1 cloud results «Caducado» right after running (the runner adds `run.symbol`). `stale.fresh`
  signs the project's `forproject.SET` and the run's recorded `manifest.json` overrides, each
  under every `knobs.CHOICES` value; a batch's `estudios/manifest.json` is shared by its
  studies, so only the SET counts there. A config that really changed (a knob removed, a feed
  renamed) still reads stale.
- **Role = what `/curate` would do with its `verdict.csv`.** `/curate` drops exactly the rows
  that say `DESCARTAR`. `mcRetest` (FAIL…), `crossTF` (five readings), `wfm` (predicts/blind/
  perverse) and `exposure` (worth_it) never write it, so they are `describe` even though they
  judge. `edgeCost` and `feedQuality` become `gate` only when their `action` knob is `drop`, and
  `blindJoint` only when both `joint.pieces` and `joint.population` are set — the role is read
  from the current config, not frozen.
- **The matrix pairs by identity, and only inside one databank** — Measured 2026-09-26 on
  `USDJPY_workflow_profiling_v1`: the 8 strategies of `Retest_Markets_-_Family`, `MCR_All`,
  `WFM` and `CrossTF` share their names with `Results` but **none** of their identities (and
  `MCR_All` even drops the `Strategy ` prefix). So `matrix.matrix` reads only `reports/<P>/<D>/`.
  **`runs`/`presence` pair across the whole project instead** (owner, 2026-09-30: the strategy is
  one entity): the identity wins wherever it is, else the name in any spelling, shown with
  `meta.other_identity` when the XML differs — never refused. A row with no identity (a
  population slice without verdict.csv, the monkey on OOS) is accepted by name, unmarked.
- **Older reports are data, not errors.** A JSON without `tabs` and `config_hash`, a
  `verdict.csv` without `strategy`/`verdict` (the Monte Carlo's tier tables), a folder that is not
  a catalogue study (`curate`, `monteCarlo_portfolio`) or a row with no identity (`edgeCost` and
  the older `crossmarket` tables carry none) are skipped with a Spanish reason and a count.
- **Studies that read a variant batch write into the batch's `estudios/`, not `reports/`.**
  `cloud`, `wfc`, `cscv` and `marketSurfaces` are keyed by the mother's name, not by day. The
  databank panel reads them across every mother (`ui/daemon/databank/batches.py`); `/api/result`
  and `/api/history` reach the same folder for one mother (`hits._batch`, OPEN #51 — before
  2026-09-29 they always answered `None` for these; `marketSurfaces` was still missing from both
  `batches.STUDIES` and `catalogue.BATCH` until 2026-09-30, FEEDBACK §8.5 — its run finished but
  the tab never found it). The population matrix still does not: a databank's population is not
  the set of its mothers.
- **Caches are keyed by file version.** A result's JSON is parsed once per (path, mtime);
  a config once per newest mtime of any YAML under `studies/ engines/ ledger/ portfolio/
  assets/`. `feedQuality`'s loader costs ~2 s uncached, which is why.

## Cost

Measured 2026-09-26 over a synthetic databank of 5,000 strategies (gate and crossmarket with a
JSON each, crossmarket as `verdict.csv` only — 10,000 JSON files and 15,000 CSV rows):
`matrix.matrix` 0.62 s the first time, 0.14 s cached; the HTTP route 1.0 s then ~0.27 s, 2.1 MB
of JSON. The first request that touches a study also imports its loader (gate ~0.5 s).
