# retest/measure — what are the numbers, and do they reconcile?

The execution layer. It reads each `.sqx` once, turns its simulations into the 30 reconstructed
metrics, **proves that reconstruction against SQX's own stored answers**, and writes the result as
a dated, immutable parquet. Everything downstream reads that parquet and nothing downstream ever
reopens an archive.

This is where a sibling study would say `simulate/`. Nothing is simulated here: SQX ran the
thousand backtests before any Python did, and naming the folder for something it does not do is
exactly the trap these READMEs exist to prevent.

**Imports from:** `core/`, `inputs/`, `model/` · **Consumed by:** `verdict/`, `render/`, `explorer/`
**Must not contain:** a threshold, a verdict, or a choice of what a metric means

| file | what it does | run it | in → out |
|---|---|---|---|
| `integrity.py` | Rebuilds the confidence table from the simulations and checks it against the one SQX stored, and proves every metric is accounted for | imported | metrics + stored → agreement |
| `store.py` | Where the parquet lives, how it is partitioned, and the only way anything reads it back | imported | keys → frames |
| `originals.py` | The unperturbed trade list each strategy actually produced, joined in from its own harvest by identity: `sample == "OOS"` for `footprint()` (the default; owner, 2026-09-29) and `sample == "IS"` — the build, the backtest `bar` and `ohlc` perturb — for the dates T2 and T3 need, each its own dataset (`trades`, `build`); `sample == "OOS"` only reaches the benchmark, with `core.trades.cost()` already added | imported | project + identities + point value → trades |
| `excess.py` | **T2 and T3.** The original's per-trade excess — SQX's own P/L (the kind of number a re-run carries; never the repriced one) minus `studies.screening.analysis.tradelevel.drift_term` at step 8's own window and variant — then `t2` (the `ohlc` re-runs' approximate excess) and `t3` (the `bar` re-runs in the common window, by matching tails). Numbers only: the cuts are in `pipeline/autopilot/criteria.yaml` | imported | build trades + original P/L + re-runs → facts |

The command that drives them is `../ingest.py`, in the module root with the other entry points.

## The reconciliation is the point, not a formality

The whole study is a reconstruction: SQX kept eleven quantiles per metric and threw the individual
simulations away, so every number here is recomputed from raw P/L. That is only trustworthy because
it reproduces what SQX itself computed. **`ingest.py` refuses to write when it does not.**

Measured on this battery, 2026-09-18: **12,210 checks — 30 metrics × 11 levels × 5 strategies ×
8 tasks — with zero disagreements**, and the worst metric sitting at 96% of its allowance, so the
tolerance is not slack.

The test is not a fixed tolerance. SQX's answer must be **one of the order statistics one rank
either side of the nominal rank**, and the band between them is the whole admissible answer. That
matters because `NumberOfProfits` is an integer over a thousand simulations: hundreds of them share
a value, so the nominal rank lands anywhere inside that run, and a fixed tolerance would either
reject a correct formula there or accept a wrong one everywhere else. On a continuous metric the
three ranks are a hair apart and it costs nothing.

## Contracts and traps

- **An export is dated and immutable, and the guard is not decorative.** `to_parquet` with
  partition columns **appends**, it does not replace, so ingesting twice into one directory silently
  doubles every row. That happened here on 2026-09-18 and read back as 79,992 simulations from 40
  runs of 1,000 — a number that looks plausible until you multiply. `ingest.py` now asserts the
  directory is empty; a re-ingest is a new `--day`.
- **`levels/` is stored long, and `load_levels()` filters on `usable` by default.** A confidence
  level is a marginal order statistic per metric, so two metrics at one level come from two
  different simulations. Long format makes `df[["NetProfit", "Drawdown"]]` — which looks like a
  scenario and is not one — impossible to write. Asking for the rank-shifted tables of the three
  short runs requires saying `usable=False` out loud.
- **`pnl/` is a separate dataset because only the equity fan and the coherent scenario need it.**
  It holds 73 MB of the export's 73 MB at five strategies, and the test battery never reads it. It
  is stored as the integer cents the `.bin` holds, so the parquet is reproducible from the archive;
  `load_pnl()` does the one documented division into USD.
- **`integrity.stored_only()` is how the other channel stays visible.** 98 metrics move with the
  confidence level: 30 are reconstructed, 5 are daily-equity analogues, 1 is excluded, and **60 to
  62 exist only as those eleven quantiles** — MAE, MFE, exposure, duration, CAGR. Coarse, but it is
  the only way to ask a retest anything about them, and the manifest records the list per run rather
  than the code hard-coding it, because which metrics an install reports is its own fact.
- **`ingest.py` raises rather than flagging when a databank does not hold the task it claims.**
  Numbers written under a false label are worse than no numbers.
- **`trades/` is the one dataset that is not a simulation.** It is this project's own harvest
  (`studies.screening.gate.harvest`, joined by identity), **out-of-sample rows only**, priced with
  `core.trades.cost()`, kept only so `verdict/evidence.py` can benchmark `psr()` against a
  same-footprint random trader instead of zero (OPEN.md #71) — never read for anything a
  simulation could answer instead. It is never the build side: the strategy was selected on that,
  so a footprint priced there would score the search, not the edge (owner, 2026-09-29).

## T2 and T3: what a re-run's P/L can and cannot be dated with

SQX stores, per simulation, the P/L per trade in cents and nothing else
(`knowhow/sqx-format/mc-retest-storage.md`). The excess over the drift needs dates, side and size, so
it is exact only for the original, whose build trades the harvest holds. 🔬 2026-10-07, 26 strategies
of four projects: the harvest's `IS` trades and `core.sqxretest.original()` of the `bar` and `ohlc`
tasks are the same trades one to one — same count, each P/L within one cent (the harvest rounds, the
.bin truncates). `excess.original()` checks exactly that and returns None otherwise.

- **T2 (`ohlc`)** subtracts from every re-run's total the drift the ORIGINAL collected. Its support
  is that a re-run trades almost when the original did: measured, the trade count moves by a median
  0-3 % of the original's, although the share of runs with *exactly* its count is anywhere from 0 to
  1 — read `count_dev_med`, not `same_count_frac` alone. The fact names say `aprox`.
- **T3 (`bar`)** compares only inside the common window: the original's trades opened after
  `RandomizeStartingBar.MaxChange` bars (off the run's own provenance) from the build's first bar. A
  re-run is dated by the tail it shares with the original, at least `fragility.min_tail` trades.
  Covering the whole window, its excess there is the original's, exactly. Parting inside it, the
  unshared head is P/L without dates: head P/L minus the original's drift over the uncovered part of
  the window, pro rata to the head's trade count (a run that only *lost* trades there collected no
  drift) — and the head's trades from before the window cannot be told apart, so they are counted in:
  an error of at most the trades of those bars, 0-4 of 135-736 measured. No tail, no count. Fewer
  than `fragility.min_matched` dated, or one single result in all the runs: no retention, which the
  judge reads as LIMBO. It never fails anything.
- 🔬 same day, same 26: every re-run with the original's trade count shares a tail of `min_tail` or
  more and is identical inside the window (100 %), while only 0-9 % of them are the original trade
  for trade on USA500 and on NIKKEI225's reference project — they differ in the first trades, the ones the window leaves
  out. 67-100 % of all runs are identical in the window, so **`ret_med` was 1.000 on all 24 with a
  positive excess**: the median is a control that says «the path does not matter», and what parts
  shows in `ret_p5` (0.91-1.00) and `identical_frac`.
