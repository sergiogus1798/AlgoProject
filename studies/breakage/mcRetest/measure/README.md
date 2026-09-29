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
| `originals.py` | The unperturbed trade list each strategy actually produced, joined in from its own harvest by identity, with `core.trades.cost()` already added | imported | project + identities + point value → trades |

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
  (`studies.screening.gate.harvest`, joined by identity) priced with `core.trades.cost()`, kept
  only so `verdict/evidence.py` can benchmark `psr()` against a same-footprint random trader
  instead of zero (OPEN.md #71) — never read for anything a simulation could answer instead.
