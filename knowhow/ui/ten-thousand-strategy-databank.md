---
q: Why did a 10,000-strategy databank time out or freeze the window, and what keeps it fast?
kw: Timed out, el demonio no respondió, Recargar databank, Cierre colgado, freeze, QTableWidget, QTableWidgetItem, identity hash, roster, wait=120, resizeColumnsToContents, diskmemo, single-flight, 10000 strategies
tag: 🔬  date: 2026-10-04  see: zones-load-on-first-open
---
# A big databank costs in four places: identity hashing, repeated work per request, table items, column measuring
Never build one Qt item per cell, never let Qt measure every row, never recompute per request what
depends only on files. Measured on `Trade_NIKKEI225_M30_volatilidadL` (10,000 `.sqx`):
- `core.sqxfile.identity` is memoised by (path, size, mtime_ns); `core/diskmemo.py` keeps it on disk.
- One computation per key, the others wait: `sqx/databank/find.LISTING`, `results/store._READING`, the
  single-flight `databank/table.table`. The window's three whole-databank calls pass `wait=120`.
- The table is a `QAbstractTableModel` (`workspace/tablemodel.py`), `setResizeContentsPrecision(100)`.

## Evidence
- Before: every whole-databank read hashed 10,000 strategies again (~16 s); four at once under one
  GIL took 47–80 s against the 20-s timeout — «Timed out», empty Databanks, «Recargar» failing too
  (it dropped the cache and paid again). Per-strategy locate re-hashed without the cache: 14 s.
- After the daemon fixes: roster cold 6.4 s, after a reload 0.12 s; locate 0.13 s; concurrent cold
  open 28–42 s, warm 5–10 s; `databank/table` Results 4.6 s for 24 MB (10,000 × 314).
- The window froze apart from the daemon: 280,000 `QTableWidgetItem` took 6.5–13 s on the GUI thread
  («Puerta IS/OOS › Resumen» 10000×28, «Cierre › Stop ATR» 10000×13 — the «Cierre colgado»). With
  the model alone it was still 6.9 s: `resizeColumnsToContents` read 1,000 rows × 28 columns × 8
  roles = 224,000 `data()` calls, 4.9 s of it comparing `role == Qt.DisplayRole` (a PySide6 enum
  attribute lookup per call). Precision 100 and module constants: 0.28 s. Worst freeze of any
  sub-panel after: 0.5 s (`scratchpad freeze.py`, offscreen).
- Trap: a table's `set_hidden` and a header sort must be layout changes, never `modelReset` — the
  filters strip and «Continuar» read `modelReset` as «another table painted» and call the daemon.
- Trap: `DataFrame.loc[row]` takes the common dtype of ALL columns; replacing it per row changed
  ints to floats in the payload. `frame.T.to_dict()` gives the same values as before.
