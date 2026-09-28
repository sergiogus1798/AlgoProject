---
q: ampersand disappears in button text, "buy & hold" shows "buy _hold", QCheckBox QPushButton mnemonic, & underline shortcut, escape && in Qt text
tag: 🔬  date: 2026-09-27  see: eng/qt-painting-traps
---
# In a QCheckBox or QPushButton text, `&` is a mnemonic: write `&&`
Qt turns `&x` into an underlined shortcut on buttons and check boxes, so «SPA y StepM contra buy & hold»
paints «buy _hold». Escape with `text.replace("&", "&&")` on any button or box whose text comes from
data (catalogue titles, study names). A plain `QLabel` without a buddy shows `&` as written: do not
escape there, or it shows `&&`.

## Evidence
- `ui/desktop/workspace/railconfig.py`, 2026-09-27, offscreen `grab()` of the rail's drawer: the
  snoopingScreen box read «buy _hold»; with `&&` it reads «buy & hold». The step card's `QLabel`
  «Exposición vs buy & hold» was right unescaped.
