---
q: PySide6 paintEvent exception swallowed, grab() raises, deleteLater old widget still paints, QStackedWidget tallest page height, QSizePolicy Ignored, emoji glyph missing font ⛔ 👁 empty box, offscreen widget test, attribute named metric segfault
tag: 🔬  date: 2026-09-26  see: eng/qt-reload-inside-own-signal
---
# Five PySide6 traps met building the study viewer (`ui/desktop/blocks/`)
- A `paintEvent` that raises only prints; **`widget.grab()` re-raises it** — an offscreen test must grab, not just build.
- **`deleteLater` is not immediate**: the old widget keeps painting until the event loop runs. `hide()` (or `setParent(None)`) it first.
- **A `QStackedWidget` is as tall as its tallest page** — set the non-current pages `QSizePolicy.Ignored`.
- **No installed font has ⛔ or 👁** (0 families; ⊘ and ◉ are in 21): paint the mark by hand or use ⊘/◉.
- **Never name an attribute `metric`** on a widget: it hides `QPaintDevice.metric()` and the process segfaults at first paint.

## Evidence
- `tests/test_ui_blocks.py` draws every real study result offscreen and calls `grab()` on each (line 59,
  comment: "PySide re-raises a paintEvent error from here"); without it broken blocks passed.
- `ui/desktop/blocks/tabpage.py` `old.hide(); old.deleteLater()` — before, a replaced body painted over the
  selectors. Same in `ui/desktop/workflow/rail.py` (`setParent(None)` before `deleteLater`).
- `ui/desktop/blocks/result.py` sets `Ignored` on every page but the current one; a short tab sat on
  the blank height of a long one.
- `QFontMetrics(QFont(f)).inFontUcs4(ord(ch))` over `QFontDatabase.families()`, 2026-09-26: ⛔ 0, 👁 0,
  ⊘ 21, ◉ 21; `fc-list | grep -ci emoji` → 0. `ui/desktop/matrix/paint.py` draws the red disc and eye.
- `ui/desktop/batchview/`, 2026-09-27: `self.metric = ...` on the parallel-coordinates widget segfaulted on the first paint / devicePixelRatio query; renamed, fixed (its README).
