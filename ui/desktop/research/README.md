# ui/desktop/research — BIBLIOTECA › Investigar

The research director's panel (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §8), in
the terminal look (`QFrame#term`). Draws what `ui/daemon/research/` says; opens no file.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | BIBLIOTECA › Investigar: the map, the memory, the director and its proposal. | imported | — |
| `directview.py` | «Tablero»: the board the director reads, one row per cell-family. No launcher: the director has none. | imported | `/api/research/board` |
| `mapview.py` | The map: assets × timeframes, colour = dominant family, intensity = effect; click for the measures. | imported | `/api/research/map`, `/cell` |
| `memoryview.py` | The memory: today's coverage, the funnel of every attempt, and what each family has given. | imported | `/api/research/memory` |
| `parts.py` | What the four views of «Investigar» share: family colours, a filled table, a daemon call. | imported | — |
| `proposalview.py` | The proposal: three ideas side by side, a veto each, their open questions, the launch and the queue. | imported | `/api/research/proposal`, `/veto`, `/answer`, `/launch`, `/queue` |
| `zone.py` | BIBLIOTECA › Investigar: the four views of the research board in one terminal frame. | imported by `shell.py` | — |

**Imports from:** `ui/desktop` (theme, background, blocks.card, studypage.net) · **Consumed by:** `shell.py`

Manual: `AlgoData/manual-fuentes/84-app-investigar.md`. Test: `tests/test_ui_research.py`.
