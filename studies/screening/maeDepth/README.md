# maeDepth — how much of each strategy's net lives on trades that went k ATR against and came back

Step 8, chained after `studies.screening.gate.report` on the same harvest (no import between the
studies). Reads `build` (`sample` IS) and `oos1` (`sample` OOS) side by side; `oos2` is never read.
It picks no stop: it warns, with numbers, of what step 24 will meet. Encargo 27. Manual:
`docs/manual/05-cribado-oos.pdf` (cap. 98-criba-mae-profundo). Test: `tests/test_maedepth.py`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | Every knob; k, slippages, sigma and action are `ledger:maeDepth.*`; `verdict.min_cuota_rec` is `null` until the owner sets it | edited | — |
| `tooltips.py` | One Spanish sentence per knob | imported | — |
| `inputs.py` | Config, newest harvest, bars + SQX ATR(20) + point value of the feed | imported | harvest → inputs |
| `measures.py` | Per trade: MAE in ATR (`engines.market.excursion`, shared with step 24) and duration in bars; per strategy and segment: deep, recovered, anomalous, counterfactual | imported | trades → numbers |
| `one.py` | One strategy, build and oos1 side by side, MAE histogram of winners vs losers, as the contract's dict | imported | measured trades → dict |
| `many.py` | The population: panel, decile, marks, distribution of the recovered's share | imported | measured trades → dict + panel |
| `report.py` | The command: prints the duration cut, writes the report, `panel.parquet`, `verdict.csv`, the ledger row per segment (with `--family`) | `python3 -m studies.screening.maeDepth.report --project P --databank D --feed F` | harvest → `reports/.../maeDepth/` |

## Things this study must get right
- **Anomalous = MAE ≥ k ATR AND duration ≥ mean + sigma·sd of that strategy's durations in that segment**,
  counted in bars. On a population that exits after X bars the cut marks nothing (🔬 USDJPY M30, 21
  strategies: 0 of 34,118 trades); the report shows the cut first and never changes it by itself.
- **The counterfactual is a bound, not a stop's backtest**: closed at −(k + slippage) ATR, three slippages.
- **No mark without the owner's threshold**: `verdict.min_cuota_rec` null means nobody is marked.
- **The cuota can exceed 1** when the net is small: it is the recovered's P&L over the segment net.
