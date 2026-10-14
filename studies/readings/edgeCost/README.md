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
| `costs.py` | Price oos1's trades at the common repricer, so the edge is read against the cost PAID. | imported | trades + bars + costs → `identity, open_time, pnl, cost` |
| `inputs.py` | Every knob, and the harvest this study reads: gate's harvest (step 8) or a strategy export. | imported | folder → frames |
| `many.py` | Every strategy of one harvest against its own edge-per-cost bar, as one result and one panel. | imported | priced trades → panel |
| `one.py` | One strategy's oos1 edge against the cost it paid, as the contract's data. | imported — the window calls it | priced trades → result |
| `report.py` | Edge per operation over the cost paid, oos1 only — encargo 11, redefined by encargo 44. Step 8 or step 25. | `python3 -m studies.readings.edgeCost.report --project P --databank D --feed XAUUSD_M1 [--strategy "Strategy 10.9.51"]` | harvest → reports |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |

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
