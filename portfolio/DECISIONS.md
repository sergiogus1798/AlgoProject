# Portfolio — open decisions

Questions the owner has not settled yet. Nothing here is implemented; do not guess an answer.

| # | question | why it matters |
|---|---|---|
| 1 | Funded vs real: same strategy pool, or different admission bars? | A daily loss cap punishes variance that own capital tolerates |
| 2 | How many strategies per portfolio, and per symbol? | Decides whether correlation or capacity is the binding constraint |
| 3 | Fixed weights, volatility parity, or optimised? | Optimised weights on backtested curves overfit hard |
| 4 | What counts as too correlated, and measured over what window? | A single threshold on the whole history hides regime clustering |
| 5 | Rebalancing: never, on a schedule, or on degradation? | Changes what the backtest of the portfolio even means |
| 6 | Prop-firm rules to encode: daily loss, total drawdown, minimum days, consistency — and which firm (static or trailing DD, news windows) | These are constraints, not post-hoc filters. Encargo 33 (`docs/encargos/33-economia-del-fondeo.md`) answers it from data; Hantec's catalogue is already extracted |
| 7 | Size with the trade bootstrap, or with a block bootstrap (~20 days) of the joint daily P&L? | Faith and Fitschen: shuffling trades understates portfolio DD — `BUILD_COMPENDIUM.md` §7.1 |
| 8 | Capped fractional Kelly, or pure fixed fractional risk? | Chan against Fitschen and Williams — §6.2-6.3 |
| 9 | Trade the plateau (sibling variants together), or treat siblings as one position? | Clones multiply correlated risk (Turtles S1+S2) — §4.4 |
| 10 | Keep the gate's near-survivors for confluence and portfolio, or keep deleting them? | Pieces that fail alone can pay combined — §3.1 |
| 11 | ~~Which segment may the portfolio selection read~~ — **partly settled (owner, 2026-09-29)**: strategies reach the portfolio only after steps 1-25 and the MT5 validation of step 26, so `oos2` is already spent and every segment may be read. **Still open:** with no unseen segment left, what validates the chosen combination (the firm-feed period, a live incubation, nothing)? | Choosing a combination is a search; it needs unseen data to validate — §2.2 |
| 12 | Allow an "unexplained, on probation" category with small capital? | Renaissance did; the hypothesis-first protocol says no — dossier §1.20 |

Answer one, and it moves from here into `portfolio/CLAUDE.md` as a settled rule.
