---
q: PySide6 paintEvent exception swallowed, grab() raises, deleteLater old widget still paints, QStackedWidget tallest page height, QSizePolicy Ignored, emoji glyph missing font ⛔ 👁 empty box, offscreen widget test, attribute named metric segfault, QTabBar white line under tabs, drawBase, tab stylesheet underline, QScrollArea viewport width stale in resizeEvent, columns relayout
tag: 🔬  date: 2026-09-27  see: eng/qt-reload-inside-own-signal
---
# Seven PySide6 traps met building the window (`ui/desktop/`)
- A `paintEvent` that raises only prints; **`widget.grab()` re-raises it** — an offscreen test must grab, not just build.
- **`deleteLater` is not immediate**: the old widget keeps painting until the event loop runs. `hide()` (or `setParent(None)`) it first.
- **A `QStackedWidget` is as tall as its tallest page** — set the non-current pages `QSizePolicy.Ignored`.
- **No installed font has ⛔ or 👁** (0 families; ⊘ and ◉ are in 21): paint the mark by hand or use ⊘/◉.
- **Never name an attribute `metric`** on a widget: it hides `QPaintDevice.metric()` and the process segfaults at first paint.
- **A styled `QTabBar::tab` still gets Qt's base line** (bright, under the whole bar): `QTabBar { qproperty-drawBase: 0; }`.
- **A scroll area's viewport width is stale in the parent's `resizeEvent`**: watch `area.viewport()` with an event filter (`ui/desktop/assets.py`).

## Evidence
- 🔬 2026-09-27, the asset zone: `place()` in `Assets.resizeEvent` read the old viewport width and the zone opened in
  one column on a 1553 px window; the same call from a viewport `QEvent.Resize` filter laid out two.
- `tests/test_ui_blocks.py` draws every real study result offscreen and calls `grab()` on each (line 59,
  comment: "PySide re-raises a paintEvent error from here"); without it broken blocks passed.
- `ui/desktop/blocks/tabpage.py` `old.hide(); old.deleteLater()` — before, a replaced body painted over the
  selectors. Same in the retired `ui/desktop/workflow/rail.py` (`setParent(None)` before `deleteLater`;
  the zone went with F13 of plan 24, 2026-09-28).
- `ui/desktop/blocks/result.py` sets `Ignored` on every page but the current one; a short tab sat on
  the blank height of a long one.
- `QFontMetrics(QFont(f)).inFontUcs4(ord(ch))` over `QFontDatabase.families()`, 2026-09-26: ⛔ 0, 👁 0,
  ⊘ 21, ◉ 21; `fc-list | grep -ci emoji` → 0. `ui/desktop/matrix/paint.py` drew the red disc and eye
  (retired with Población by F13, 2026-09-28; `studypage/notes.py` keeps ⊘/◉).
- `ui/desktop/batchview/`, 2026-09-27: `self.metric = ...` on the parallel-coordinates widget segfaulted on the first paint / devicePixelRatio query; renamed, fixed (its README).
- `ui/desktop/workspace/filters.py`, 2026-09-28: the filter row's `self.metric` QComboBox segfaulted on the
  first `grab()` offscreen (F15 shots); renamed `self.column`.
- `ui/desktop/theme.py`, 2026-09-27: with only `QTabBar::tab` rules the Estrategia page's family bar kept a
  near-white rule under it (`--shot` capture); `qproperty-drawBase: 0` removed it.
