---
q: does the project run on Windows? portable, Linux-only, desktop app ui on Windows, algoui.cmd, PYTHONUTF8, encoding utf-8 cp1252 UnicodeDecodeError, PyYAML wheel, python version 3.14, require_posix, read-only mode, modo lectura, no SQX install, /api/health sqx installs
tag: 🔬  date: 2026-09-27  see: eng/checker-blind-spots, eng/qt-reload-inside-own-signal
---
# SQX driving is Linux-only; the analysis and the window are portable
Export on Linux, analyse and open `ui/` anywhere. On Windows launch with `bin\algoui.cmd` (sets
`PYTHONUTF8=1`; the daemon's jobs get it too). Every file read passes `encoding="utf-8"`.
A UI path that touches an install must degrade when the install is absent, never raise.
No install folder at all → `/api/health` `sqx.installs` all false → banner «modo lectura», ↻ off.
The owner uses the window on Linux only (2026-09-27): nothing more is adapted for Windows.
Supported Python 3.10–3.13 (numpy, scipy, arch have no 3.14 wheels at pinned versions).

## Evidence
- Linux-only: `core/worker.py`, `core/exportdrv.py`, `sqx/export/`, `sqx/curate/apply_verdict.py` — they
  shell out to `bin/sqx-worker.sh` (needs `rsync`, `ss`, `md5sum`, `curl`, `setsid`, `stat -c`).
  `core.worker.require_posix()` raises on `win32` at each entry point.
- UI, 2026-09-26: clean copy of `git ls-files -co --exclude-standard` (1149 files, no symlinks, no
  Windows-illegal names), `machine.yaml` with `sqx_master: /nonexistent`, no `sqx_workers`, no
  `strategy_pools`. Every GET route of the daemon, then every zone walked offscreen with lists,
  tables and combos driven: 0 exceptions after three fixes — `sqx/templates/holes.py` raised on the
  missing `blockGroups.xml` (500 on a template's page); `webbrowser.open(f"file://{p}")` is not a
  URI for `C:\…` (now `Path.as_uri()`); job children printed in cp1252.
- Read-only, 2026-09-27: a scratch `machine.yaml` (installs → missing folders, `ui_port: 8799`),
  a daemon started on 8799 BEFORE the window, then the real file put back after 3 s. A separate
  port is required: `launch` reuses any daemon whose code fingerprint matches, and every process
  reads `machine.yaml` once at import. `--shot` showed the banner; health said all three false.
- Not yet run on a real Windows box: the offscreen walk is Linux Qt.
- Fixed earlier: `PyYAML==5.4.1` had no wheel above cp39; ten `read_text()`/`open()` lacked `encoding=`.
