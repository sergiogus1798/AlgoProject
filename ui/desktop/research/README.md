# ui/desktop/research — BIBLIOTECA › Investigar

The research director's panel (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md` §8), in
the terminal look (`QFrame#term`). Draws what `ui/daemon/research/` says; opens no file.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The package's one-line purpose | imported | — |
| `zone.py` | `ResearchZone`: the four tabs; `fetch`/`send` injectable (a fake makes every call synchronous); jumps to the proposal when the director ends | imported by `shell.py` | — |
| `parts.py` | The seven family colours at three discrete intensities, the read-only table with explained headers, `esc` (agent text is escaped: a rule holds `<`), `call` (off the GUI thread) | imported | — |
| `mapview.py` | Mapa: assets × timeframes as buttons — family, ▲/▼ and effect in words as well as colour, grey when nothing passes; a click fills the families and the measures, each with what it measures | imported | `/api/research/map`, `/cell` |
| `memoryview.py` | Memoria: coverage in one sentence, every attempt's funnel, survivors per family and asset class | imported | `/api/research/memory` |
| `directview.py` | Proponer investigación: the board with each factor explained, the button with its cost confirmation, the director's five steps while it runs | imported | `/api/research/board`, `/direct` |
| `proposalview.py` | Propuesta: diagnosis, three ideas side by side with a veto each and their open questions, the fixed `Research_` prefix (no choice), «Crear plantillas y lanzar en SQX» with the preflight's sentence, and the queue | imported | `/api/research/proposal`, `/veto`, `/answer`, `/launch`, `/queue` |

**Imports from:** `ui/desktop` (theme, background, blocks.card, studypage.net) · **Consumed by:** `shell.py`

Manual: `AlgoData/manual-fuentes/84-app-investigar.md`. Test: `tests/test_ui_research.py`.
