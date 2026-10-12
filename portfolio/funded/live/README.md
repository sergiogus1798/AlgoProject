# portfolio/funded/live — the live protocol (encargo 65, row 10)

Two readings of a strategy once it trades for real, and one decision line. It simulates nothing,
places no order and touches no terminal: the accounts are opened by the owner.

**Imports from:** `mt5.verify.judge` (rows 1, 2, 3a, 5, `clock`), `mt5.compare` (`mean_loss`, the judge's own R), `mt5.compare`, `mt5.reconcile` (register, deals to trades), `mt5.fleet.app.history`, `core.assetwrite`, `ledger.thresholds`
**Numbers:** `ledger/thresholds.yaml`, keys `funded.live.*` (stage A and SPRT) and `mt5verify.*` (the row limits)

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | `ledger:` placeholders for every number | edit the ledger, not this | — |
| `real.py` | the strategy's closed trades from the fleet's history (`<login>.history.json`) split by magic through the reconciler's register; R of each trade | imported | strategy, firm → trades, .sqx, timeframe |
| `stage_a.py` | the first 30 real trades against the SQX backtest: row 1 (matched) only warns, rows 2, 3a, 5 take the strategy out; under 30 trades there is no verdict | imported | two trade frames → rows, `failed`, `warning`, `out` |
| `sprt.py` | Wald's SPRT on R per trade: limits `ln·σ²/(μ1−μ0)` on `S_n − 0.05·n` (14.4 / −11.2), derived, never typed | imported | list of R → `raise` / `retire` / `continue` and the n where it crossed |
| `run.py` | **THE COMMAND**; prints both readings and `DECISIÓN:`; `--anotar` writes each failed row with `core.assetwrite.add_live_failure` into the card's `live_failures` | `python3 -m portfolio.funded.live.run --asset A --strategy S --firm F --sqx a.csv --deposit 10000 [--real b.csv --timeframe H1] [--r r.csv] [--anotar]` | CSV + fleet → stdout |

Behaviour (owner, 2026-10-12):
- **Source.** The fleet history; `--real` (CSV in SQX's export shape) overrides it and is what the tests use.
- **Join.** The deal's magic number, through the reconciler's register (`AlgoData/mt5/reconcile/register.csv`, `mt5/reconcile/register.py`) — no new table.
- **1 R** is the mean losing trade of the SQX backtest, `compare.mean_loss` (the judge's `rows` calls it too), in points (`compare.in_points`), for stage A and for the SPRT's R alike; `--r` overrides the R column.
- **Step 26's preparation is reused:** SQX moved from its feed's zone to the server's (`compare.to_zone`) and then the whole-hour shift `judge.clock` finds; P&L of both sides in points.
- **The SQX side is clipped** to the first real trades' time window.
- The SPRT reads all the strategy's closed trades on that account, oldest first.
