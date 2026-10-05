# construct/contract — the portfolio run as the window's blocks

The result of `../many.py` in the shape of `core/study/CONTRACT.md` (PLAN §5.6): what the «Construir»
tab (M7) will paint and what `../report.py` writes as `cartera.json` / `.html`. It computes nothing
the verdict did not: it only draws.

**Imports from:** `core.study`, `../segment.py`, `../equity/matrix` · **Consumed by:** `../many.py`

| file | what it does | run it | in → out |
|---|---|---|---|
| `tabs.py` | Five tabs — Veredicto (the oos1 null with the chosen one marked, or a callout when the null cannot discriminate; the chosen metrics; the oos2 reading), Universo (members, floor risk, days per segment, exclusions), Parejas (pairs rejected per filter on build; the chosen pairs over a threshold out of sample), Búsqueda (the funnel, every build score), Cartera (cumulative P&L per segment with each member's own share as a reference line, members and weights, P&L per month) — and the envelope with the verdict block on top | imported | inputs, verdict → contract dict |
| `words.py` | The Spanish titles and notes of those blocks | imported | — |

## Traps
- **oos2 is drawn only when the verdict read it**: the Cartera tab plots `build` plus the segments
  in `verdict["cost"]["segments"]`, never the calendar's.
- **The Universo tab counts days per segment, oos2 included** — a count of rows, no P&L.
- Not built (PLAN §5.6, M7's): the per-measure grid of every pair, the universe's reconciliation table.
