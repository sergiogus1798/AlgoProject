# studies/research — where to look next: the research director's pieces (step 1)

The family that decides **what to investigate**, before any idea exists: which asset, timeframe,
direction and behaviour family has measurable structure, and what has already been tried there.
Design: `docs/AgentPDFs/director-de-investigacion-2026-10-01.md`. Nothing here touches SQX, and
nothing here costs tokens: Python computes, the director (an agent, phase 4) only reads a page.

| study | the question | reads | writes |
|---|---|---|---|
| `marketProfile/` | what behaviour family each asset × timeframe × direction shows, against chance, and whether it pays its costs (piece 1) | the `build` segment of the M1 bars, never `oos1`/`oos2` | `AlgoData/research/profiles/` |
| `profilePower/` | how small an edge the profile can see: an edge of known size planted in the bars and put through the profile's own test; the power curve and the minimum detectable effect, and what the whole map could have seen | the `build` segment; the profile's `measures.csv` and `context.csv` | `AlgoData/research/power/` |
| `pooledProfile/` | the profile's measures judged per group (asset class × timeframe × direction × measure) against a null that resamples the group's assets jointly, each asset's effect shrunk to its group, and the board cells a passing group would bring (counted, the gate untouched) | the `build` segment; `board.json` to count what is new | `AlgoData/research/pooled/` |
| `memory/` | what was tried in each cell, where it died and why (a typed cause), what survived, and each idea's sheet against its build (piece 2) | registries, autopilot runs, ideas | `AlgoData/research/memory/` |
| `literature/` | what published research says, as entries anchored to verbatim quotes: the search, the validator, the dedupe, the store and the queue behind the `literatureScout` agent (the front of the chain) | arXiv, OpenAlex; the profile's `measures.csv` for the queue | `AlgoData/research/literature/` |
| `board/` | which passing cell to investigate next, the director's proposal checked and stamped, and whether the profile guides (pieces 4 and 5) | the profile's scores, the memory | `AlgoData/research/board/`, `AlgoData/research/proposals/` |

Each study carries its own `README.md`. The agent that reads the board is
`.claude/agents/researchDirector.md`, launched by `/research-direct` or by the window's
«Investigar» zone (`ui/daemon/research/`, `ui/desktop/research/`). The agent that feeds the
literature is `.claude/agents/literatureScout.md`, run by `/literature-scout` or daily by
`bin/daily-literature-scout.sh`; it is the one piece of this family that costs tokens.
