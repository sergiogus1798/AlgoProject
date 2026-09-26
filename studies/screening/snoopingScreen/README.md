# snoopingScreen — does anything beat buy and hold once the whole search is paid for?

Step 8, right behind the OOS gate, over the same harvest. The gate asks whether each strategy
clears a set of screens; this asks the question those screens cannot: of the K strategies the
harvest paired, **which beat simply holding the asset, with the search over all K discounted**.
Hansen's SPA answers "any?", Romano and Wolf's StepM answers "which?". Encargo 10, part A.

**It annotates and removes nobody** (owner, 2026-09-25): every row of its `verdict.csv` is
MANTENER, so `/curate` applied to it is a no-op, and what the StepM said travels in the `superior`
column, the scorecard of the pages and the ledger's note.

```
config.yaml ─▶ inputs ─▶ benchmark ─▶ measure ─▶ many / one ─▶ report
 every knob    harvest,   buy & hold   SPA, StepM  the contract  pages, verdict.csv,
               scorecard, at equal     (engines/   dicts         table, ledger row
               bars       risk         inference)
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `inputs.py` | The knobs, the newest harvest and the gate scorecard written over it, the policy window, the daily panel cut to it, and the asset's price change on the panel's own days | imported | harvest + feed → panel, moves |
| `benchmark.py` | Buy and hold sized to each strategy's own daily volatility, and the excess over it | imported | panel + moves → excess, lots |
| `measure.py` | The excess panel through the SPA and the StepM, and one row per strategy | imported | excess → p-values, named, table |
| `one.py` | One strategy as the contract's data: SUPERIOR only when the StepM names it | imported — the window calls it | table row → result |
| `many.py` | The population as one result: the three SPA p-values, the Sharpe histogram against buy and hold, the gate's survivors, the StepM set | imported | inputs → results |
| `report.py` | **The command**: runs it, writes `reports/<P>/<D>/<day>/snoopingScreen/`, records a step-8 row in the ledger | `python3 -m studies.screening.snoopingScreen.report --project XAU_ISOOS_ejemplo --databank Results --feed XAUUSD_DukasM1_Infinox --symbol XAUUSD --timeframe M30 --family DirectionalMomentum` | harvest → reports + ledger row |
| `tooltips.py` | One Spanish sentence per `config.yaml` knob | imported | — |
| `config.yaml` | The segment, the benchmark's sizing, the FWER — a `ledger:` placeholder, the number is in `ledger/thresholds.yaml` — and the bootstrap | edited | — |

Manual page, in Spanish: `docs/manual/05-cribado-oos.pdf` (cap. 49-snooping). The engine: `engines/inference/snooping/`.

## The four things this module exists to get right

**K is the harvest, not the gate's survivors.** The gate's screens read this same `oos1`
stretch, and a test run on what a choice kept cannot pay for the choice. So the panel holds every
strategy the harvest paired (115 on `XAU_ISOOS_ejemplo`), and the gate's survivors (45) are a
column. What SQX tried and never wrote to a databank is still invisible — that count is the
ledger's, and a retest databank carrying acceptance conditions on the OOS (the `MC Trades`
trap, `docs/encargos/5-nulos.md` §6bis) is already a selection on this window.

**Buy and hold at equal risk.** Owner, 2026-09-25. Holding the asset with the strategy's own lots,
or with all the capital, compares a position held every day against one held a few percent of the
time, and tests gold's drift. Sized so its daily P&L is as volatile as the strategy's, a positive
mean excess is *exactly* a Sharpe ratio above buy and hold's — `tests/test_snooping.py` checks the
identity. It is the `equal_risk` convention of `studies/closing/exposure`, copied, not imported.

**Marked-to-market days, cut where SQX cuts them.** The panel is `dailyEquity.bin`, which moves on
days nothing closed (🔬 390 such days on one XAU strategy), so the stationary bootstrap sees the
serial dependence of positions held for weeks. The last day is dropped (SQX marks an open position
there and its net profit does not). And 🔬 SQX stamps day D with the equity it *carried into* D:
the gold price is sampled at each label's own instant; a plain daily resample lags buy and hold
one day and halves its correlation with the strategies.

**Three p-values, not one.** `lower` and `upper` bracket `consistent`; a wide gap means many
candidates are clearly worse than buy and hold and are dragging the test.

## What it found the first time

🔬 `XAU_ISOOS_ejemplo`, `oos1` 2018–2022, 1,287 days: buy and hold gold's Sharpe is **0.405**. Of
115 paired strategies, **4** have a higher Sharpe — all four among the gate's 45 survivors — and the
StepM names **none** at FWER 0.05. SPA p: lower 0.753, consistent 0.892, upper 0.901. On synthetic
noise with the same shape, a naive one-sided t-test per column finds "something" in 15 of 20
seeds; the StepM in 0 of 20.

## Not built here

**Part B of the encargo**, the same test on step 20's survivors over data nobody looked at, is
`studies/closing/blindJoint/` and waits until a population reaches step 20.
