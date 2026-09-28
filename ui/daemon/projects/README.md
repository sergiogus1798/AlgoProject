# ui/daemon/projects — the gallery's projects, merged

Encargo 22 §3: the old `/api/projects` (`results/api.py`) lists only projects with a folder under
`AlgoData/reports/`, so a project just built never appeared. `/api/projects/all` merges the four
places that each know part of a project:

| source | gives |
|---|---|
| each install's `user/projects/*/project.cfx` (`progress.projects`) | that it exists, where (workers first, as `loader.find.install_of`), and the symbol and timeframe of its first task's main chart |
| `AlgoData/projects/registry.csv` (`sqx.projects.registry`) | symbol, timeframe, template, purpose — they win over the `.cfx` when present |
| the roster of each databank (`loader.find.roster`) | the total of distinct strategies (identity), 0 for an empty folder without hashing |
| today's SQX log of the install (`progress.run_state`) and, for a worker running it, `-project action=status` (`progress.state` → `tasklog.status`) | the state: corriendo / parado / terminado / construido, and `ausente` for a project that left only reports |

**Imports from:** `core`, `sqx.projects.registry`, `sqx.projects.retire` (`STOCK`), `ui.daemon.progress`,
`ui.daemon.runs`, `ui.daemon.loader.find` · **Consumed by:** `ui/desktop/workspace/gallery.py`,
`ui/desktop/cmdpalette.py`, `ui/desktop/projectflow.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `sources.py` | The merge: one card per project on an install or with reports (SQX's five stock projects left out), running first; and `locate`, the databank and name of one identity | imported | disk → cards |
| `api.py` | `GET /api/projects/all` and `GET /api/projects/find?project&identity[&databank]` | imported | request → JSON |

## Traps

- **Never the `count` verb of `-databank` for a total** (CLAUDE.md rule 3): it syncs from the files and
  wipes what the worker holds only in memory. The totals are the rosters on disk; the one command
  sent is `-project action=status`, and only to a worker whose process is up and whose log has
  this project running. The master is never asked anything (`tasklog.status` refuses it).
- **A project SQX is writing is counted by its files**, not its roster: `find.roster` returns
  nothing while the log has the project running, so a half-written `.sqx` is never hashed.
- **The first answer of a daemon costs ~12 s** (2026-09-27, 7 181 strategies on three installs):
  every roster is hashed once. The counts are then cached per folder mtime in `sources.distinct`,
  unbounded, because `find.roster`'s own cache holds 64 folders and the gallery walks ~400 —
  with only that cache every call cost the full 12 s. Warm: ~0.03 s.
- **«terminado» without today's log is an inference**: no task log survives per project, so a
  project not in today's log with strategies on disk reads «terminado» and its `why` says so.
- **Symbol and timeframe are searched, not parsed**, in the task XML: parsing a task file (MB)
  per project cost the gallery a second.
