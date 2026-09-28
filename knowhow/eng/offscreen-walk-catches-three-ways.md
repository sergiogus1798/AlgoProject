---
q: uiwalk offscreen exceptions PySide slot excepthook QTimer singleShot processEvents raises threading excepthook, catch every window exception, a refusal test started a real study, stub jobs.start
tag: 🔬  date: 2026-09-28  see: eng/qt-painting-traps
---
# A window exception reaches you three ways — and a refusal test on real data must stub `jobs.start`
To collect every exception of an offscreen walk (`tools/uiwalk.py`): a signal's slot goes to
`sys.excepthook`; a worker thread to `threading.excepthook`; a callable queued with
`QTimer.singleShot` is **raised out of `app.processEvents()`** at the call site — wrap the pump
in `try/except`, or a replaced `sys.excepthook` swallows it and the process exits 1 silently.
A test that expects the daemon to refuse must swap `jobs.start` for a recorder: when the data
changes, a refusal becomes an acceptance and a real study starts on a real project.

## Evidence
- 🔬 2026-09-28, PySide6 offscreen: `QPushButton.clicked → 1/0` → `sys.excepthook`; `Thread(target=[][1])`
  → `threading.excepthook`; `QTimer.singleShot(0, lambda: {}['x'])` then `processEvents()` →
  `KeyError` raised there (default hook: traceback + rc 1; replaced hook: rc 1, nothing printed).
- 🔬 2026-09-28, `tests/test_ui_runner.py::test_refusals` moved to `Test_USDJPY_donchianUpperCrossUp_M30`:
  `blindJoint … many` was accepted and `studies.closing.blindJoint.report` started (it died with the
  test; no report, no ledger row). `isOos` with `--set a.b=1` is accepted too now. The test records.
