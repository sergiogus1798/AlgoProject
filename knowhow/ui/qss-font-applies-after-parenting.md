---
q: Why is a table cell cut with room to spare, or a column measured too narrow, in the terminal style?
kw: resizeColumnsToContents, sizeHintForColumn, QSS descendant selector, QFrame#term QTableWidget, font, JetBrains Mono, Inter, elided cell, truncated, showEvent, compact table, scrollbar, minimum window width, strip
tag: 🔬  date: 2026-10-05  see: ui/inventory-walk-artifacts
---
# A stylesheet's descendant selector gives a widget its font only once it is parented — measure columns on first show, not when the table is built
`ui/desktop/blocks/table.py` built the table unparented and called `resizeColumnsToContents()`: the font was
the application's (Inter 14). Inside its frame, `QFrame#term QTableWidget` makes it JetBrains Mono 13, wider:
a column measured 184 px needed 199, and «paridad de riesgo (1/σ)» was cut. `Fitted.showEvent` now fits once
more, in the real font. A compact table's maximum width must also include the vertical scrollbar when it has
more rows than it shows, or the bar covers the last column.
Same family: a row of fixed-width inputs sets the window's MINIMUM width — the bank's five selectors in one
row forced 1818 px, squeezed its combos to 150 px and cut the launcher; typed inputs on a second row give 1440.

## Evidence
- Unparented: font Inter 14, widths `[184, 282, 115]`; shown under `QFrame(objectName="term")`: JetBrains
  Mono 13, `sizeHintForColumn` = `[199, 285, 27]`.
- `tests/test_ui_portfolios.py`: «tables: columns are measured in the frame's own font», «a compact table
  that scrolls keeps its last column clear of the scrollbar», «strip: with five selectors…».
