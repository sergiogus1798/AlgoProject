# Portfolio — open decisions

Questions the owner has not settled yet. Nothing here is implemented; do not guess an answer.
Settled on 2026-09-29 and moved to `portfolio/CLAUDE.md`: #1 (same pool), #3 (equal weight as the
baseline, pluggable weights), #7 (Monte Carlo of every kind), #8 (fixed fractional), #4 (every
correlation threshold 0.30 by default), #9 (siblings face the same filter, no special rule) and #11 (search `build`, test `oos1`+`oos2`).

| # | question | why it matters |
|---|---|---|
| 2 | How many strategies per portfolio, and per symbol? **Owner, 2026-09-29: undecided — maybe the funding economics or the portfolio's own risk should say.** | Decides whether correlation or capacity is the binding constraint |
| 5 | Rebalancing: never, on a schedule, or on degradation? | Changes what the backtest of the portfolio even means |
| 6 | Prop-firm rules to encode: daily loss, total drawdown, minimum days, consistency — and which firm (static or trailing DD, news windows). **Belongs to encargo 33 now** (owner, 2026-09-29): outright prohibitions filter the pool before the search, the rest is sizing after it | Encargo 33 (`docs/encargos/33-economia-del-fondeo.md`) answers it from data |
| 10 | Keep the gate's near-survivors for confluence and portfolio, or keep deleting them? | Pieces that fail alone can pay combined — §3.1 |
| 12 | Allow an "unexplained, on probation" category with small capital? | Renaissance did; the hypothesis-first protocol says no — dossier §1.20 |

Answer one, and it moves from here into `portfolio/CLAUDE.md` as a settled rule.
