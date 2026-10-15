# portfolio/funded/live — the live protocol (encargo 65, row 10)

Two readings of a strategy once it trades for real, and one decision line. It simulates nothing,
places no order and touches no terminal: the accounts are opened by the owner.

**Imports from:** `mt5.verify.judge` (rows 1, 2, 3a, 5, `clock`), `mt5.compare` (`mean_loss`, the judge's own R), `mt5.compare`, `mt5.reconcile` (register, deals to trades), `mt5.fleet.app.history`, `core.assetwrite`, `ledger.thresholds`
**Numbers:** `ledger/thresholds.yaml`, keys `funded.live.*` (stage A and SPRT) and `mt5verify.*` (the row limits)

| file | what it does | run it | in → out |
|---|---|---|---|
| `real.py` | The real trades of one strategy, from the fleet's history, a CSV override, and their R. | imported | strategy, firm → trades, .sqx, timeframe |
| `run.py` | THE COMMAND: stage A and the funded account's SPRT for one strategy, ending in a decision line. | `python3 -m portfolio.funded.live.run --asset A --strategy S --firm F --sqx a.csv --deposit 10000 [--real b.csv --timeframe H1] [--r r.csv] [--anotar]` | CSV + fleet → stdout |
| `sprt.py` | Wald's sequential test on a funded account's per-trade results in R. | imported | list of R → `raise` / `retire` / `continue` and the n where it crossed |
| `stage_a.py` | Stage A: the first real trades of a strategy against its SQX backtest, on rows 1, 2, 3a and 5 of step 26. | imported | two trade frames → rows, `failed`, `warning`, `out` |
| `config.yaml` | `ledger:` placeholders for every number | edit the ledger, not this | — |

Behaviour (owner, 2026-10-12):
- **Source.** The fleet history; `--real` (CSV in SQX's export shape) overrides it and is what the tests use.
- **Join.** The deal's magic number, through the reconciler's register (`mt5/reconcile/register.py`, derived from the fleet's `magics.csv`) — no new table.
- **1 R** is the mean losing trade of the SQX backtest, `compare.mean_loss` (the judge's `rows` calls it too), in points (`compare.in_points`), for stage A and for the SPRT's R alike; `--r` overrides the R column.
- **Step 26's preparation is reused:** SQX moved from its feed's zone to the server's (`compare.to_zone`) and then the whole-hour shift `judge.clock` finds; P&L of both sides in points.
- **The SQX side is clipped** to the first real trades' time window.
- The SPRT reads all the strategy's closed trades on that account, oldest first.
