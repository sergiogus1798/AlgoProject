---
q: does the project run on Windows? portable, Linux-only, desktop app ui on Windows, algoui.cmd, PYTHONUTF8, encoding utf-8 cp1252 UnicodeDecodeError, PyYAML wheel, python version 3.14, require_posix
tag: 🔬  date: 2026-09-26  see: eng/checker-blind-spots, eng/qt-reload-inside-own-signal
---
# SQX driving is Linux-only; the analysis and the window are portable
Export on Linux, analyse and open `ui/` anywhere. On Windows launch with `bin\algoui.cmd` (sets
`PYTHONUTF8=1`; the daemon's jobs get it too). Every file read passes `encoding="utf-8"`.
A UI path that touches an install must degrade when the install is absent, never raise.
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
- Not yet run on a real Windows box: the offscreen walk is Linux Qt.
- Fixed earlier: `PyYAML==5.4.1` had no wheel above cp39; ten `read_text()`/`open()` lacked `encoding=`.
