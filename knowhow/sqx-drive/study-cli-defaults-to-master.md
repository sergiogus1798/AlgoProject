---
q: decay study reads master databank empty; Decaimiento IS/OOS databank tiene ninguno; databank_dir install=MASTER default silently empty; a study CLI script reads the wrong install; runner must resolve project install before building argv
tag: 🔬  date: 2026-09-29  see: sqx-drive/driving-a-role, sqx-drive/three-install-topology
---
# A study's CLI defaults to the master; the runner, not the script, must resolve the real install
`core.paths.databank_dir`/`project_dir` take `install: Path = MASTER`. A study script that calls
them with no `install` (`studies/screening/decay/report.py` before this fix) silently reads the
master's `user/projects/<P>/databanks/<D>/` — empty, no error — for any project a worker actually
holds (every `Test_`/`Trade_` project built on the conductor or custodian, i.e. almost all of
them, CLAUDE.md rule 3). The window showed «Decaimiento IS/OOS» reading a databank with nothing
in it, feedback 2026-09-29 §1.4.

## Evidence
`ui.daemon.workflow.sources.install(project)` already resolves this for the databank panel
(`ui/daemon/databank/layout.py`) and for `sqx/export/export_spp.py`'s `--role` CLI flag
(`driving-a-role`). `decay`'s runner command (`ui/daemon/runner/screening.py`) built its argv with
no such lookup, so it always read the master regardless of where the project's Cross Market H1
rebuild or any other worker-built project actually lived.
Fix: the runner calls `sources.install(project)` before building the argv, appends `--role
<role>` when it is not `"master"`, and `report.py` gained the same `--role` argument
`export_spp.py` already had (`worker_dir(a.role) if a.role else MASTER`). Any other study
script that reads `.sqx` straight off an install (not through `metrics/` or `harvest/`, which
are already install-independent exports) carries the same risk and needs the same check.
