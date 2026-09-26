# studies/closing/atrCalculator — the stop loss read from the MAE, not optimised

Step 22 of the workflow. The chain builds **without a stop** on purpose — one parameter fewer to
overfit — but a strategy that is going to trade needs one. Owner, 2026-09-26:

> *«No quiero que sea una optimización ni nada.»*

So `SL = X · ATR(20)`, fixed at entry, and **X is read from the trades with a rule fixed before
looking**: a percentile of the in-sample winners' MAE in ATR units. SQX then measures, with its own
spread and slippage, what that stop costs and whether the result is flat around it. The report puts
the four percentiles (80, 85, 90, 95) side by side and **never picks one**. Brief:
`docs/encargos/20-atr-calculator.md`; manual: `docs/manual/49-atr-calculator.md`.

```
config.yaml ─▶ inputs/load ─▶ mae ─▶ threshold ─▶ noreturn ─▶ transfer ─▶ grid ──▶ stopgrid.csv
 every knob    trades, bars,   MAE/   X per       where each   does the IS  X·(1±band)   │
               ATR, windows    ATR    percentile  X falls      X hold OOS                 ▼
                                      + interval                              sqx.variants.stopgrid
                                                                              → SQX retest (3 legs)
                                                   proofs ◀── stability ◀──── export_retest ×3
                                                   graft,     cost per X,
                                                   ATR        plateau/edge
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `config.yaml` | The percentiles, the bootstrap, the no-return and transfer labels, the grid, the shape tolerance, the proof tolerance | edited | — |
| `inputs.py` | The knobs, the trades of one or more exports cut into build/oos1/oos2 by `Open time`, the bars, the point value, the batch's manifest | imported | exports + asset → trades, windows |
| `load.py` | Everything one run reads, once: trades, SQX's ATR on the strategy's timeframe, and which export name holds each mother's trades without a stop | imported | exports (+ batch) → inputs |
| `mae.py` | Per trade: the ATR of the bar closed before the entry, MAE and net result in that ATR, winner = net P/L > 0 | imported | trades + ATR → per-trade table |
| `threshold.py` | §2.1: X per percentile of the IS winners' MAE/ATR, its bootstrap interval (the four percentiles on the same resamples, vectorised in chunks: 36 strategies 182 s → 5.6 s), and the `poco fiable` mark | imported | winners → four X |
| `noreturn.py` | §2.2: for each distance, how many IS trades that got there still won and their mean final result; the zone each X falls in | imported | IS trades → curve, zones |
| `transfer.py` | §2.3: each IS X's effective percentile among the oos1/oos2 winners; KS and Anderson-Darling with D and the median ratio | imported | winners per window → table |
| `grid.py` | The stability grid `X·(1 ± band·k/steps)` written as `stopgrid.csv` | imported | four X → grid rows |
| `proofs.py` | The graft proof (X = 1000 ≡ original, trade for trade) and the ATR proof (each stop's distance against X·ATR at the entry bar, the bar before, and two before) | imported | retested trades → two tables |
| `stability.py` | §3: every grid variant against the original, per window — PF, net, DD, stops, winners killed, loss saved, new entries, worst trade — and the shape (plateau or edge) | imported | retested batch → metrics, shape |
| `view.py` | The §2 tabs: X, punto sin retorno, transferencia | imported | reading → tabs |
| `sqxview.py` | The SQX tabs: pruebas, lo que cuesta, estabilidad | imported | stability → tabs |
| `one.py` | One strategy, as the contract's dict; verdict `info`, never a choice | imported — the window calls it | inputs → result |
| `report.py` | **The command**. Without `--work` it reads the exports, writes one page per strategy and `stopgrid.csv`; with `--work` it adds the proofs and SQX's cost and stability | `python3 -m studies.closing.atrCalculator.report --project P --databank D [D …] --feed F --symbol S --timeframe TF [--strategy N] [--work DIR]` | exports → reports + `stopgrid.csv` |
| `tooltips.py` | One Spanish sentence per knob, for the window's drawer | imported | — |

## The three things this module exists to get right

**The ATR is SQX's, not a rolling mean.** `engines.market.atr.sqx` reproduces `ATR.java` — Wilder with
an averaged start — and the stop formula's rounding. `engines.market.calibrate.atr` is a simple mean
and would put every X off by the gap between the two. The ATR proof checks it against the stops SQX
actually placed (`knowhow/export/sqx-atr-is-wilder.md`).

**Nothing is chosen.** No knob picks the best X or the best percentile; the tables put the four side
by side, the stability grid is read for its *shape*, and the verdict block is `info`. The labels
(`ruido`/`sin retorno`, `se transfiere`, `meseta`/`borde`) describe; the curves under them are drawn
whole so a label can be checked by eye.

**The graft is proven before the retest is read.** The factory can only move parameters a strategy
already declares, and these strategies carry `SLPT.None`. `sqx/variants/build/stoploss.py` adds the
stop; the `X = 1000` probe must reproduce the original trade for trade in all three windows, or the
Pruebas tab says so and nothing after it means anything.

## What it deliberately does not do

- **No MT5, no `StopsLevel`, no broker minimum** (owner, 2026-09-26).
- **No recomputing X out of sample.** If the IS X does not transfer, the report says so and stops.
- **No ledger row for oos2.** `assets/_policy.yaml` reserves oos2 for the WFC and the WFM and the
  ledger's door refuses step 22 on it; whether step 22 may read oos2 on the record is the owner's
  line in the policy, not a wider check here.
