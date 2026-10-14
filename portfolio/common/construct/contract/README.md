# construct/contract — the portfolio run as the window's blocks

The result of `../many.py` in the shape of `core/study/CONTRACT.md` (PLAN §5.6): what the «Construir»
tab (M7) will paint and what `../report.py` writes as `cartera.json` / `.html`. It computes nothing
the verdict did not: it only draws.

**Imports from:** `core.study`, `../segment.py`, `../equity/matrix` · **Consumed by:** `../many.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `tabs.py` | The portfolio run as the contract's blocks (PLAN §5.6): Veredicto, Universo, Parejas, Búsqueda, Cartera. | imported | inputs, verdict → contract dict |
| `words.py` | The Spanish words of the portfolio result: tab titles, the notes each block opens with. | imported | — |

## Traps
- **oos2 is drawn only when the verdict read it**: the Cartera tab plots `build` plus the segments
  in `verdict["cost"]["segments"]`, never the calendar's.
- **The Universo tab counts days per segment, oos2 included** — a count of rows, no P&L.
- Not built (PLAN §5.6, M7's): the per-measure grid of every pair, the universe's reconciliation table.
