# construct/incubation — the chosen portfolio after oos2 (M9)

PLAN §14.5, Council 2026-10-04: once `oos2` is spent, what validates the chosen combination is the
days that did not exist when it was chosen — each month, the fresh stretch read **against the band
of equal-length windows of the portfolio's own history**, one ledger row per reading.

**INCUBATION IS NOT RUNNING.** Nothing produces the fresh rows today: the monthly SQX retest of the
bars after `oos2` is a worker job nobody has built or launched (the owner's go-ahead each time), no
live or demo account is connected to this module, and no portfolio has been chosen for real. What is
built and tested is the record, the row contract, its validator and the reading — on synthetic
«fresh» series and, in the test root, on a forced portfolio of `Test_nikkei_ref`.

**Imports from:** `../funded.py` (sizing, member meta), `../inputs/config`, `../search/trials` (gate, ledger rows) · **Consumed by:** nothing yet

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Package marker | — | — |
| `record.py` | `register`: freeze a judged run's hand-off portfolio, its fixed-risk scale and the comparison (`figure`, `history`, `band`) under `portfolio/incubation/<hash12>/`, once; `missing`: the unanswered knobs; `validate`: every way a file of fresh rows breaks the contract, in Spanish; `path`: the portfolio's daily P&L per unit of risk from long rows at the frozen weights; `load` | imported | run folder → record.json, history.parquet |
| `band.py` | `read`: the fresh stretch's figure (`pnl` sum or daily `sharpe`) among every window of its length in the history — inside, below or above the band's two percentiles, its percentile, and how many windows share no day | imported | history path, fresh path → reading |
| `run.py` | THE COMMAND: `register` (refuses while any `incubation.*` knob is null) and `read` (validates the rows, asks the gate, reads, appends `readings.jsonl` and one step-27 ledger row on segment `incubation`; without `--rows`, the state). Prints «LA INCUBACIÓN NO ESTÁ EN MARCHA» first, every time | `python3 -m portfolio.common.construct.incubation.run register --run <run> --set incubation.figure=… --set "incubation.history=[…]" --set "incubation.band=[lo, hi]"` · `… run read --portfolio <hash prefix> [--rows <file>]` | a judged run; a rows file → record, reading, ledger row |

## The row contract — the hand-off's `daily.parquet`, nothing new

A file of fresh days has exactly the columns of `<run>/handoff/daily.parquet` (PLAN §2.2):

| column | value |
|---|---|
| `day` | after the last day of the registered history |
| `identity` | a member of the registered portfolio |
| `pnl` | that member's mark-to-market P&L of the day **in the unit of its archived backtest** (what `handoff/daily.parquet` holds); one row per member per trading day, zero days included |
| `segment` | `incubation` |
| `source` | `paper` (SQX retest of the fresh bars, through the universe's rebuild) or `live` (an account); one per file |

A file is **the whole stretch since the history's end**, not the last month: the reading is
cumulative (the plan's «the bars after oos2»). Where each source would come from: `paper` — the same
`equity/` rebuild the universe runs, on the retest's trades; `live` — `mt5/reconcile/live.py` already
turns an account's deals into orderstocsv-shaped trades per strategy (register `magic → identity`),
which would still need re-daying and rescaling from the live lot to the backtest's. Neither producer exists.

## What the plan fixes, and what is the owner's (each a `null` knob or not built)

| | |
|---|---|
| fixed by PLAN §14.5 | monthly; the fresh stretch after `oos2`; read against the band of equal-length windows of the portfolio's own history; one ledger row per reading |
| `incubation.figure` — **null** | what is read: `pnl` or `sharpe` (the two built) |
| `incubation.history` — **null** | which segments make «its own history»: all of it, or the out-of-sample ones only (compendium §11.4: «against the OOS band») |
| `incubation.band` — **null** | the percentiles, and whether above the band is an alarm too (compendium §11.5) |
| not built, nobody's decision yet | the stopping rule (how many flagged readings retire the portfolio or a member), the length of incubation (compendium §11.2 suggests MinTRL), any correction for the monthly repeated looks, the size ramp |

## Traps
- **The band's nominal level is not its real one.** 🔬 `tests/test_portfolio_incubation.py`: ten years of
  history and a 12-month stretch are ten independent windows; over 300 synthetic histories a healthy
  stretch fell under the «5th percentile» 9.7 % of the time, and one history alone ranged 2-12 %.
  The reading prints `independent` next to the overlapping count for that reason.
- **Monthly looks add up**: the same healthy portfolio was flagged at least once in 12 monthly
  readings in 24 % of the draws. → `knowhow/research/incubation-band-is-not-its-nominal-level.md`
- **A record is frozen**: a second `register` of the same portfolio (pool hash, members with
  versions, weights, scale) is refused; the comparison in the record is the one a reading uses,
  whatever `config.yaml` says later.
- **Segments of the history are concatenated**: `[build, oos2]` makes windows that straddle the gap.
- **Every reading is a ledger row** (`portfolio/incubation/<figure>`, `n_out` 0 when flagged), the
  same file read twice included.
