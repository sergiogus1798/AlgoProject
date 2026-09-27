---
q: desktop shortcut window does not open after an update; ui daemon outlives the window; stale daemon 404 on new routes; /api/health code fingerprint
tag: 🔬  date: 2026-09-26  see: eng/qt-painting-traps
---
# The ui daemon outlives its window, so after an update the shortcut met yesterday's code
`bin/algoui` reused any daemon answering `/api/health`; one started the day before lacked the new
routes and the window died on its first 404, silently (a shortcut has no terminal). Now `/api/health`
carries `code` (`ui/daemon/version.py`, mtimes of `ui/daemon/**/*.py`), `pid` and `busy`, and
`ui/desktop/launch.py` replaces a stale idle daemon, or explains in a dialog when it is busy.

## Evidence
PID 1050287 started 2026-09-25 21:26, `/api/catalogue` → 404. After the fix: stale daemon pid
1698791 replaced by 1698929 on launch, `/api/catalogue` → 200.
