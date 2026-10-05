---
q: What does a walk that drives every widget by introspection (tools/uiinventory.py) get wrong unless told?
kw: uiinventory uiparts uiwalk inventory every button combo tab cell, ItemIsUserCheckable default flag, CheckStateRole, checkbox painted in a plain cell, text indented truncated column, tab key ordinal shifts, pair dialog swept again, token per data root ALGO_DATA_ROOT 401, QMessageBox.exec patched, reload drops marks, selection moves to newest run
tag: 🔬  date: 2026-10-05  see: ui/offscreen-walk-catches-three-ways
---
# A walk that drives every widget by introspection (`tools/uiinventory.py`, `tools/uiparts.py`) invents three artefacts — and a table refilled on reload forgets what the owner did to it
1. **Every `QTableWidgetItem` has `ItemIsUserCheckable` by default.** Ask `index.data(Qt.CheckStateRole) is not
   None`, never the flag: a check state set on a plain cell paints a box and truncates the column.
2. **A control's key must survive a repaint**: tab titles + kind + label; an ordinal among siblings shifts.
3. **A window opened per cell is ONE context, by class** (`ventana PairDialog`), not 56 dialogs swept apart.
The walking process needs the daemon's `ALGO_DATA_ROOT` (the token lives under the data root). In the view: a
table rebuilt in `fill()` on every reload loses check states, the message beside it and a non-run selection —
keep them by identity before refilling (`Databank.fill`, `PortfoliosBoard.filled`).

## Evidence
- 🔬 2026-10-05, first read-only walk of Portfolios: «Resumen» showed `P(año perdedo…` truncated and
  three metric names indented; «Carteras» showed `■ Re…`; the matrix two black squares. All three were
  the walk's own `setData(…, Qt.CheckStateRole)` on rows 0-2; gone with the `data()` test.
- 🔬 same day, through the window on a disposable root: «Pool declarado.» was erased by the reload it
  triggers (`fill` reset the line); the ten ticks were gone after it; with the pool's row chosen, the
  end of «Calcular parejas» moved the selection to the newest run. Tests: `tests/test_ui_portfolios.py`
  («databank: a reload keeps…», two cases).
- What the walk and its scenarios found beside that, all fixed the same day: matrix figures dark on
  dark when no threshold was read; «Juzgar esta cartera» naming a button spelled «Juzgar: veredicto»;
  `10,000` in Spanish sentences; «Percentil 95» explaining a relaxed percentile 50; «VEREDICTO: SIN
  VEREDICTO»; `--set noexiste.clave=1` refused as `'noexiste'`; the verdict's confirmation telling the
  portfolio that read oos2 that it «solo medirá oos1» when it gets its stored reading back.

## Counter-evidence
Offscreen only: hover, drag, the splitter and keyboard focus are not driven. A cell cap (40 rows, 120
cells per view) leaves the rest to «pasan por el mismo código», stated as `no ejercido` in the report.
