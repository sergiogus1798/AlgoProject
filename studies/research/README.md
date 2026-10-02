# studies/research — where to look next: the research director's pieces (step 1)

The family that decides **what to investigate**, before any idea exists: which asset, timeframe,
direction and behaviour family has measurable structure, and what has already been tried there.
Design: `docs/AgentPDFs/director-de-investigacion-2026-10-01.md`. Nothing here touches SQX, and
nothing here costs tokens: Python computes, the director (an agent, phase 4) only reads a page.

| study | the question | reads | writes |
|---|---|---|---|
| `marketProfile/` | what behaviour family each asset × timeframe × direction shows, against chance, and whether it pays its costs (piece 1) | the `build` segment of the M1 bars, never `oos1`/`oos2` | `AlgoData/research/profiles/` |
| `memory/` | what was tried in each cell, where it died, what survived (piece 2) | registries, autopilot runs, ideas | `AlgoData/research/memory/` |
| `board/` | which passing cell to investigate next, the director's proposal checked and stamped, and whether the profile guides (pieces 4 and 5) | the profile's scores, the memory | `AlgoData/research/board/`, `AlgoData/research/proposals/` |

Each study carries its own `README.md`. The agent that reads the board is
`.claude/agents/researchDirector.md`, launched by `/research-direct` or by the window's
«Investigar» zone (`ui/daemon/research/`, `ui/desktop/research/`).
