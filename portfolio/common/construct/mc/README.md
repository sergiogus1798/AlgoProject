# construct/mc — Monte Carlo paths of a combination's server days, and the rules over them

What stage B and the funded verdict resample (PLAN §14.3b): three ways of drawing a challenge
horizon of server days for one combination, all returning the same five arrays the rule machine
reads, and the machine's own day loop over every path and risk setting with the detail its sweep
does not return. The bank simulation (`portfolio/funded/sim/`, F5) codes against `paths.py`.

**Imports from:** `equity/clock`, `portfolio.funded.rules.machine`, `engines.inference.snooping.superior` · **Consumed by:** `search/stageb*.py`, `../funded_b.py`, `portfolio/funded/sim/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `paths.py` | The three generators, one contract: `daily_blocks` (D, stationary bootstrap of the joint day table), `trade_bootstrap` (T1, each member's whole trades with replacement, a drawn gap after each, members independent), `trade_blocks` (T2, windows of history with every member's trades that opened in them); `history` replays the units where they really were | imported | day arrays or member units → `closed`, `float_end`, `low`, `high`, `opened` [n_paths, horizon] |
| `units.py` | A member's trades as whole units: per trade its worst, best and last floating per 5-minute block since entry (M1 wicks, the exit block holds the realised P&L), the day and block it opened in, the gaps between trades | imported | trades + M1 → unit dict |
| `lay.py` | The numba kernels that lay whole trades on a synthetic calendar and fold each day's blocks into its joint low and high | imported | units → day arrays |
| `judge.py` | Every path through every risk setting from its day 0: pass, fail or open, stages passed, the day, the rule; and the figures per setting — P(pass), P per phase, time to pass, which rule fails | imported | paths, plan, risk [C, phases] → codes, figures |
| `blocklen.py` | The block lengths a combination is read at: Politis and White's on its own daily P&L, plus the sweep | imported | day table → lengths |

## The registry: what each flavour holds fixed

| flavour | draws | keeps | loses |
|---|---|---|---|
| D | runs of consecutive days (geometric lengths) | co-movement between members; each day's exact intraday low and high | a trade open at a seam is settled there at its mark |
| T1 | per member, trades with replacement and a gap after each | every trade whole, with its floating | co-movement: the portfolio drawdown reads smaller |
| T2 | windows of history (geometric lengths), every member's trades that opened in them | every trade whole **and** which trades opened together | variety: fewer distinct windows than trades |

## Traps
- **`judge._kernel` repeats the rule machine's day loop** (`portfolio/funded/rules/` is frozen and
  its sweep returns only pass/fail/open). `tests/test_portfolio_stageb.py` holds it equal to
  `machine.challenge` — outcome, stages, day, rule — on every catalogue plan; a rule changed in
  the machine must be changed here in the same task.
- **D settles a cut trade at the seam.** Carrying the floating across seams instead reads a
  strategy that holds overnight as riskier for no reason (`knowhow/research/daily-block-seams.md`).
- **A synthetic day is 288 blocks**; a 23- or 25-hour server day (change of time) shifts a
  multi-day trade's later midnights by an hour inside that trade only.
- **A trade straddling the stretch's first or last day is not a unit**: it stays in D's day
  table and is missing from T1 and T2.
- **T1's path starts inside a gap** and a trade lands at whatever hour the drawn gap gives:
  T1 keeps no clock, by design it keeps nothing between members.
