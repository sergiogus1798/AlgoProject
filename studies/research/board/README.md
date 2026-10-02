# research/board — which cell to investigate next, the proposal that follows, and whether the profile guides

Phases 4 and 6 of the research director (`docs/AgentPDFs/director-de-investigacion-2026-10-01.md`
§5-§7). Pure Python, no SQX, 50 ms: it joins the profile (`marketProfile/`) and the memory
(`memory/`) into ONE page the `researchDirector` agent reads. Its output is Spanish: the owner and
the director read it. Outputs: `AlgoData/research/board/` and `AlgoData/research/proposals/`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | The weights of the three factors, the signal's cap, the prior of the past factor, the brake, the provisional-costs mark, **the one Spanish ↔ taxonomy family mapping**, the hole rules, the self-check's thresholds | edited | — |
| `tooltips.py` | One Spanish sentence per knob | imported | — |
| `inputs.py` | The config; `scores.csv`; the memory recomputed from its sources; `ideas_spent(…)` and `attempts_in(…)` per cell | imported | files → tables |
| `prior.yaml` | The owner's prior transcribed: matrix asset × family (Alta/Media/Baja), main and secondary family per timeframe, and where it holds for longs only | edited | — |
| `prior.py` | `level(…)` of one of the prior's families in a cell; `of(…)` for a board cell, with the prior's `pullback` filed under `prior.pullback_as` | imported | cell → level |
| `factors.py` | `evidence` (naked, plateau, weak, none, against), `signal`, `gap`, `brake`, `past` (Beta posterior shrunk to the pooled rate, with its interval), `points` | imported | numbers → 0-1 |
| `many.py` | `run(scores, memory, cfg, sweep)`: the gate — the prior rates the cell Alta, OR it passes the four filters naked, OR a sweep variant passes on a plateau; never a family whose lead needs the clock — the factors per cell, the order | imported | tables → the board dict |
| `page.py` | The board as one page of Spanish text, every factor's raw value beside its 0-1, and the legend | imported | board → text |
| `store.py` | `board_dir()`, `proposals_dir()`, JSON read/write | imported | — |
| `__main__.py` | **The command**: prints the page, writes `board.json` and `board.txt` | `python3 -m studies.research.board` | profile + memory → the page |
| `palette.py` | `hole(family)`: the block families the free hole may draw from and their weight, by orthogonality and «trend with counter-trend, never two alike», with `family_blocks` | `python3 -m studies.research.board.palette momentum` | idea family → families, blocks |
| `proposal.py` | `check` (three ideas, one direction, no palette alike, questions with readings), `launchable` (no veto, no open question), `stamp` (id, board row, ideas spent, provisional costs, the two standing costs), `save`/`load`/`listing`, `step` | `python3 -m studies.research.board.proposal DRAFT.json` · `--step N --note "…"` | the director's draft → `<id>.json`, `<id>.md` |
| `proposalmd.py` | A stamped proposal as the Markdown the owner reads | imported | proposal → text |
| `selfcheck.py` | The profile examines itself: closed runs split at their median score, survival rate of each half, Fisher's p, the decision (keep or halve `weights.signal`) and its cost in runs | `python3 -m studies.research.board.selfcheck` | attempts + scores → decision |

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

## The hook for `ledger/trials.py` (not wired: `ledger/` was not to be edited)

`inputs.ideas_spent(inputs.memory()["spent"], symbol, timeframe, direction, family) -> int` is the
number of ideas already proposed for a cell; `memory.queries.ideas_spent` also carries
`hypotheses`, what the ideaExpert measured. A deflated Sharpe that wants «trials of the cell» adds
them to `trials.accumulated(frame)["n"]`: `OPEN.md` (entry in the phase-4 report).

Manual: `AlgoData/manual-fuentes/83-tablero-de-investigacion.md`. Test: `tests/test_research_board.py`.
