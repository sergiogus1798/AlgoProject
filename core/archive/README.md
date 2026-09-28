# core/archive — the strategy archive (encargo 23)

A strategy that survived the sequence cost a lot of CPU. The archive freezes it — its `.sqx`, its
cosecha rows and **every study result** that names its identity, across every databank of its
project — and reads it back in the very shapes the daemon serves for a live strategy, so the window
can show it again **without running anything** (`read` imports no `studies.*` and no `ui.*`, and
spawns nothing). The key is the identity (SHA-256 of the normalised XML); a name never pairs.

**Imports from:** `core.paths`, `core.sqxfile`, `core.assetdata`, `core.datapaths`, `core.manifest`,
`ledger`, and on the write side only `ui.daemon.loader.find`, `ui.daemon.results`,
`ui.daemon.gateview`, `ui.daemon.tearsheet.harvest` (the shapes it captures) and
`sqx.inspect.strategymeta` when it exists · **Consumed by:** the Ficha's «Archivar» and
PORTFOLIOS' «Importar» (encargo 22, fronts F4 and F12)

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names the package; holds no code | — | — |
| `__main__.py` | Makes `python3 -m core.archive` run `cli.main` | `python3 -m core.archive …` | — |
| `cli.py` | The command: `list`, `archive`, `show` | `python3 -m core.archive archive --project P --databank Results --identity <sha> --step 16 --family <template>` | args → printed |
| `write.py` | `archive(project, databank, identity, step, note, *, family, sqx=None) -> Path`: locates the `.sqx` on the install by file read (refusing while SQX runs the project), freezes everything, seals it | imported | a live strategy → `archive/<identity>/<stamp>/` |
| `collect.py` | Finds every folder under `reports/<P>/` that names the identity (through any CSV with `strategy`+`identity`, or a JSON's own identity) and copies its JSONs, manifest and the strategy's rows of every table; the loose CSVs outside a study folder cut to the identity; and `skipped`, what could not be paired and why; the cosecha rows | imported | reports, harvest → frozen files |
| `view.py` | Captures what the daemon serves today: `runs.result` per study and its population, the matrix row, `harvest.read`, the gate report and sheet | imported | live daemon reads → `view.json` + parquet |
| `manifest.py` | The provenance: the project's registry row, the asset YAML with its sha256 and the resolved card, the ledger study's `trials.accumulated` and `spend.virgin` | imported | project, symbol → dicts |
| `read.py` | `load(identity, version=None) -> dict`, `versions(identity)`, `listing()` — files only | imported | archive → the live shapes |

## One version on disk

`AlgoData/archive/<identity>/<YYYY-MM-DDTHHMM>/`, built as `.<stamp>.partial` and renamed when
complete, then sealed (files 0444, folders 0555). A second archive of the same identity is a new
folder; the same minute twice is refused, never overwritten.

| path | what |
|---|---|
| `manifest.json` | identity, project, databank, step, note, `archived_at`, `code_version` (git), registry row, `.sqx` origin + sha256, harvest rows, `studies` (databank, day, study, names, `config_hash`, files), `loose`, `skipped` (`{path, reason}`), `asset`, `ledger`, `meta` |
| `strategy.sqx` | the strategy file, byte for byte |
| `view.json` | `results`, `populations`, `cells`, `tearsheet` (without its frames), `gate` — what `load` returns |
| `tearsheet/{equity,trades}.parquet` | the two frames `harvest.read` returns |
| `harvest/{metrics,equity,trades}.parquet` | the cosecha's rows of this identity, every column |
| `reports/<D>/<day>/<study>/` | the contract JSONs, the manifest and the strategy's rows of each CSV/parquet — no figures |
| `asset/<S>.yaml`, `asset/card.json` | the cost card as it was on the day of archiving |
| `meta.json` | front E2's metadata (`sqx.inspect.strategymeta.read`), when that reader exists |

## Traps

- **Nothing is left out silently.** `manifest.json` → `skipped` lists every folder or file that
  could not be paired, with its reason, and `show` prints it. On the USDJPY acceptance
  (2026-09-27): archived — every study folder that names the identity, `curate/` (its
  `before-*.csv` carry identity) and the loose CSVs that name it (`pre_mcr_identity.csv`,
  `capacity8_verdict.csv`, `capacity3_pre_mcr_identity_verdict.csv`, rows cut to the identity);
  skipped — `crossmarket` (identity empty in every row, and `X` beside `X(1)`:
  `knowhow/locations/crossmarket-report-signs-no-identity.md`), `spp` after its 20:33 rerun
  (JSON signed `identity: null`, no verdict.csv), `OOS/isOos` (population result only),
  `workflow-steps.csv` (no identity column). A folder that names strategies by name only — the
  monkey's `nulls.csv` without verdict.csv — is skipped with the same «sin identidad» reason.
- **A folder that is not a catalogue study** (`curate`) is frozen but has no `results` entry:
  no daemon route serves it.
- **`meta.stale` is as of the archive day.** Judging it today means loading the study's config.
- **The ledger count is that day's.** A study whose ledger file was moved away counts 0
  searches; the manifest keeps the file's sha256 (None when absent) so that is visible.
- **`family` is asked for**, not derived: which template family names the ledger study is the
  owner's open question Q9 (plan 24 §10).
- **Versions archived before `skipped` existed** (`2026-09-27T2024`, `T2025`) have no `loose`
  nor `skipped` key; `show` prints nothing for them.
