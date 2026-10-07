# edgeCost — how much edge each trade carries over the cost it paid

Encargo 11, redefined by encargo 44 (P.2-3). One question, in two places of the workflow: step 8
(a reading over the population the gate leaves) and step 25 (the version that will be traded).
The definition is the gate's: **oos1 only**, every trade repriced from raw bar opens by the
common repricer (`engines/market/reprice.py`) at the task's declared costs, and

`edge_mean = mean(pnl + cost) / mean(cost)`, per strategy

— the same number as the gate's `edge_mean_oos` (`studies/screening/analysis/onepass.py`) on the
same trades; `tests/test_edgecost.py` ties them. 1 is break-even and also the multiple of the
cost at which the net edge reaches zero. No gross is rebuilt from SQX's fill prices, no spread
is measured off the bars, and there is no median, no trade count and no per-cost breakdown.

```
inputs ─▶ costs ─▶ one / many ─▶ report
 the      oos1 trades  the edge     the
 harvest  repriced     per strategy command
                       or the panel
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, and the harvest this study reads (trades, the timeframe, identity → name) | imported | folder → frames |
| `costs.py` | Prices the OOS rows with `reprice.real` (`price`, `per_trade`) — the gate's rule: a stop-loss exit at SQX's price, a late stamp at its bar's open — and carries the provisional-cost warning | imported | trades + bars + costs → `identity, open_time, pnl, cost` |
| `one.py` | One strategy against the bar, as the contract's data: the headline and the gross by entry hour and weekday | imported — the window calls it | priced trades → result |
| `many.py` | Every strategy of one harvest against the same bar, as one panel | imported | priced trades → panel |
| `report.py` | **The command**: `verdict.csv` (`identity, edge_mean, verdict`) and the page, or `--strategy` for one read in full | `python3 -m studies.readings.edgeCost.report --project P --databank D --feed XAUUSD_M1 [--strategy "Strategy 10.9.51"]` | harvest → reports |
| `tooltips.py` | One sentence per `config.yaml` knob | imported | — |

## What is the owner's

`min_edge_spreads` and `action` (`mark`/`drop`) in `config.yaml` — the owner's bar, fixed before
looking at results (owner, 2026-09-26), registered in `ledger/thresholds.yaml`.

## Limits, said plainly

- The repricer fills at bar opens, so a step-25 version whose stop closes a trade inside a bar
  is refused (`costs.price`), not approximated. UNVERIFIED against SQX in the repricer itself:
  shorts, a non-zero commission and a swap in points (its docstring). It rejects forex cards.
- The old per-cost sensitivity (×0..×3, breakeven by commission, swap, spread, slippage) is gone:
  `reprice.pnl` returns one cost, not its parts. The breakeven of all costs is `edge_mean`.
- Never touches SQX; step 8 and step 25 read a harvest's `trades.parquet`.
