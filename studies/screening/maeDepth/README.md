# maeDepth — how much of each strategy's net lives on trades that went k ATR against and came back

Step 8, chained after `studies.screening.gate.report` on the same harvest (no import between the
studies). Reads `build` (`sample` IS) and `oos1` (`sample` OOS) side by side; `oos2` is never read.
It picks no stop: it warns, with numbers, of what step 24 will meet. Encargo 27. Manual:
`docs/manual/05-cribado-oos.pdf` (cap. 98-criba-mae-profundo). Test: `tests/test_maedepth.py`.

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | Every knob, and what one run reads: the gate's harvest, the bars and the ATR of the feed. | imported | harvest → inputs |
| `many.py` | Every strategy of one harvest through the deep-trade reading: one panel, one population result. | imported | measured trades → dict + panel |
| `measures.py` | The maths: per trade, MAE in ATR and duration in bars; per strategy and segment, how much of the result lives on trades that went k ATR against. | imported | trades → numbers |
| `one.py` | One strategy's dependence on deep trades, build and oos1 side by side, as the contract's data. | imported | measured trades → dict |
| `report.py` | The deep-MAE screen (encargo 27, step 8): how much of each strategy's result lives on trades that went k ATR against and came back, over the gate's harvest. Chained after the gate's report. | `python3 -m studies.screening.maeDepth.report --project P --databank D --feed F` | harvest → `reports/.../maeDepth/` |
| `tooltips.py` | One sentence per config.yaml knob, for the window's configuration drawer. | imported | — |
| `config.yaml` | Every knob; k, slippages, sigma and action are `ledger:maeDepth.*`; `verdict.min_cuota_rec` is `null` until the owner sets it | edited | — |

## Things this study must get right
- **Anomalous = MAE ≥ k ATR AND duration ≥ mean + sigma·sd of that strategy's durations in that segment**,
  counted in bars. On a population that exits after X bars the cut marks nothing (🔬 USDJPY M30, 21
  strategies: 0 of 34,118 trades); the report shows the cut first and never changes it by itself.
- **The counterfactual is a bound, not a stop's backtest**: closed at −(k + slippage) ATR, three slippages.
- **No mark without the owner's threshold**: `verdict.min_cuota_rec` null means nobody is marked.
- **The cuota can exceed 1** when the net is small: it is the recovered's P&L over the segment net.
