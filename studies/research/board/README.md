# research/board — which cell to investigate next, the proposal that follows, and whether the profile guides

Phases 4 and 6 of the research director (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md`
§5-§7). Pure Python, no SQX, 50 ms: it joins the profile (`marketProfile/`) and the memory
(`memory/`) into ONE page the `researchDirector` agent reads. Its output is Spanish: the owner and
the director read it. Outputs: `AlgoData/research/board/` and `AlgoData/research/proposals/`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__main__.py` | The command: prints the board's one page and writes it as board.json and board.txt. | `python3 -m studies.research.board` | profile + memory → the page |
| `factors.py` | The board's numbers per cell — prior, evidence, signal, coverage gap, past, brake — each 0-1. | imported | numbers → 0-1 |
| `inputs.py` | What the board reads: its config, the profile's scores, the sweep's best variants, the memory. | imported | files → tables |
| `many.py` | The board: the cells the prior or the measurements let in, ordered, each factor beside its rank. | imported | tables → the board dict |
| `page.py` | The board as one page of Spanish text: what the director and the owner read. | imported | board → text |
| `palette.py` | The free hole's block families for an idea of one family, by the two rules of the dossier's §5. | `python3 -m studies.research.board.palette momentum` | idea family → families, blocks |
| `prior.py` | The owner's prior per asset, timeframe, direction and family: Alta, Media or nothing. | imported | cell → level |
| `proposal.py` | A director's proposal: checked, stamped with the board's facts, saved as JSON and Markdown. | `python3 -m studies.research.board.proposal DRAFT.json` · `--step N --note "…"` | the director's draft → `<id>.json`, `<id>.md` |
| `proposalmd.py` | A proposal as the Markdown the owner reads. | imported | proposal → text |
| `selfcheck.py` | The profile examines itself: did high-score cells give more survivors than low-score ones? | `python3 -m studies.research.board.selfcheck` | attempts + scores → decision |
| `store.py` | Where the board and the proposals live under the data root. | imported | — |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | The weights of the three factors, the signal's cap, the prior of the past factor, the brake, the provisional-costs mark, **the one Spanish ↔ taxonomy family mapping**, the hole rules, the self-check's thresholds | edited | — |
| `prior.yaml` | The owner's prior transcribed: matrix asset × family (Alta/Media/Baja), main and secondary family per timeframe, and where it holds for longs only | edited | — |

## The gate and the order (owner, 2026-10-02) — supersedes the dossier's «celdas grises no entran»

«Use both: the document is very good, and statistics on our side all the better.» The statistics
are a bonus on top of the prior, never a requirement. A cell-family **enters** when the prior rates
it Alta (Alta in the matrix, or main/secondary family of that timeframe), OR it passes the profile's
four filters, OR a variant of the exit/parameter sweep passes on a plateau. Clock families never
enter; a prior-Baja or prior-less cell with no measured support stays out. Where the prior says
«(largo)» only the long cell holds it. The prior's `pullback` is not one of the seven keys: it is
filed under `reversion` (a reversion trigger as the fixed condition, the D1 trend as its context)
and the page marks it. A cell admitted by the prior alone prints «sin medir» for effect and trades.
**Order:** points = 100 × brakes × (0.30 prior + 0.30 evidence + 0.10 signal + 0.15 gap + 0.15 past);
evidence is graded naked 1 > plateau 0.8 > significant under 2× 0.5 > none 0.25 > against 0, and
«medido en contra» also halves the points and prints its warning. The page prints the first
`page.rows` cells; all are in `board.json`.

## The decisions the code takes that the design left open

- **Points**: see above. Signal = effect ÷ cost, saturating at 10 costs; gap = 1/(1 + runs of that family in that cell);
  brake = 1/(1 + ideas/6). All in `config.yaml`, all printed in the page's legend.
- **Past** is a Beta posterior: prior of 4 pseudo-attempts at the rate pooled over every family and
  class. Nothing closed anywhere → 0.50 for every cell (today). An untried family sits on the
  pooled rate: unknown, not penalised.
- **An idea with no family yet** (it never became a template) counts against every family of its
  asset × timeframe × direction.
- **`provisional_costs`** (XAGUSD, UKOIL, USOIL) is a mark, never a gate. The trades-a-year minimum
  is the profile's fourth filter (2026-10-02), so a board cell always reaches it.
- **The self-check** splits at the median score of the closed runs, not at `passes`: since only
  passing cells are proposed, future runs are all «high» by the profile's own filter, and the low
  half comes from runs launched by hand. Until both halves exist it cannot conclude.

## The ideas spent reach the deflated Sharpe (wired 2026-10-02)

`ledger.report` adds to a study's N the **hypotheses** the ideaExpert measured (owner: the real
looks, not the ideas), through `studies.research.memory.trials.spent` — each idea file once per
study, only the study's direction, an idea with no family yet in every study of its asset,
timeframe and direction. The board is not in that path: `inputs.ideas_spent(…)` stays what the
proposal prints as «ya van K ideas», a count of ideas, per cell. The profile's own measures stay
out of N. → `ledger/README.md`, `knowhow/research/ideas-are-ledger-trials.md`.

Manual: `AlgoData/manual-fuentes/83-tablero-de-investigacion.md`. Test: `tests/test_research_board.py`.
