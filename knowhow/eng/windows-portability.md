---
q: does the project run on Windows? portable, Linux-only, encoding utf-8 cp1252 UnicodeDecodeError, PyYAML wheel, python version 3.14, require_posix
tag: 🔬  date: 2026-09-11  see: eng/checker-blind-spots
---
# SQX driving is Linux-only; the analysis is portable
Export on Linux, analyse anywhere. Every file read passes `encoding="utf-8"` (Windows default is cp1252).
Supported Python 3.10–3.13 (numpy, scipy, arch have no 3.14 wheels at pinned versions).

## Evidence
- Linux-only: `core/worker.py`, `core/exportdrv.py`, `sqx/export/`, `sqx/curate/apply_verdict.py` — they
  shell out to `bin/sqx-worker.sh` (needs `rsync`, `ss`, `md5sum`, `curl`, `setsid`, `stat -c`);
  `apply_verdict.py` also uses `pgrep` and bare `sqcli` (Windows ships `sqcli.bat`).
  `core.worker.require_posix()` raises on `win32` at each entry point → one clear sentence, not a `FileNotFoundError` on a `.sh`.
- Portable: `tasks/`, `strategies/`, `portfolio/`, panels — pure Python over exported CSVs.
- Fixed silent breakers: `PyYAML==5.4.1` has no wheel above cp39 (pip would try to compile and fail);
  ten `read_text()`/`open()` calls lacked `encoding=` → `UnicodeDecodeError` on the first accented word of the Spanish manual.
