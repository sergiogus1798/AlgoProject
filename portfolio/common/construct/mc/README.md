# construct/mc — Monte Carlo paths of a combination's server days, and the rules over them

What stage B and the funded verdict resample (PLAN §14.3b): three ways of drawing a challenge
horizon of server days for one combination, all returning the same five arrays the rule machine
reads, and the machine's own day loop over every path and risk setting with the detail its sweep
does not return. The bank simulation (`portfolio/funded/sim/`, F5) codes against `paths.py`.

**Imports from:** `equity/clock`, `portfolio.funded.rules.machine`, `engines.inference.snooping.superior` · **Consumed by:** `search/stageb*.py`, `../funded_b.py`, `portfolio/funded/sim/`

| file | what it does | run it | in → out |
|---|---|---|---|
| `blocklen.py` | How long the resampled blocks are: measured on the combination's own daily P&L, plus a sweep. | imported | day table → lengths |
| `judge.py` | The rule machine over Monte Carlo paths and risk settings: who passes, when, and which rule fails. | imported | paths, plan, risk [C, phases] → codes, figures |
| `lay.py` | Whole trades laid on a synthetic calendar of server days: the kernels behind T1 and T2. | imported | units → day arrays |
| `paths.py` | Monte Carlo paths of a combination's server days: joint-daily blocks (D), trade bootstrap (T1, T2). | imported | day arrays or member units → `closed`, `float_end`, `low`, `high`, `opened` [n_paths, horizon] |
| `units.py` | A member's trades as whole units: each one's floating path per block since entry, at unit risk. | imported | trades + M1 → unit dict |

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
