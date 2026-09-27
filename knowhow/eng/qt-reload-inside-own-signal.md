---
q: PySide6 segfault when a combo or button reloads the page, QScrollArea setWidget destroys old widget, reload inside signal, QTimer.singleShot
tag: 🔬  date: 2026-09-26  see: eng/windows-portability
---
# A view must not rebuild itself inside the signal of a widget it is about to destroy
`QScrollArea.setWidget` deletes the previous widget at once, not later. A combo whose
`currentIndexChanged` reloads the page is freed while its own signal still runs → segfault.
Defer the rebuild: `QTimer.singleShot(0, reload)` (`ui/desktop/detail.py` `redraw`).

## Evidence
- Template page, verdict combo: `setCurrentIndex` → `save_verdict` → `load` → `page()` →
  `scroll.setWidget(body)` → `Fatal Python error: Segmentation fault`, reproducible offscreen.
  Same path behind «Guardar». After deferring, the full zone walk runs with 0 crashes.
