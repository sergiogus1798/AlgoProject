---
name: analysis-montecarlo
description: Run the trade-level Monte Carlo robustness study on the strategies of one databank — reorder them, resample them, execute them worse, and split them by period and volatility regime — then read which of them survive with their vetoes named, or run the same tests over a portfolio of them. Use when the owner asks how robust a strategy is, how much of a result is luck, what its real drawdown could be, whether it survives worse costs or fills, whether it works in every regime, or asks for a Monte Carlo of a databank or a portfolio.
---

# /analysis-montecarlo

```
raw/<P>/<D>/<date>/trades/  →  report  →  montecarlo.html  →  verdict.csv
      (ya exportado)          el estudio   una página por      la llamada
                                            estrategia
```

It **reads exported trades and writes reports**. It touches no project, task or build — hard rule 3
stands. It never moves a strategy between databanks either; that is `/analysis-crossmarket`'s last
step and the owner's call.

## Step 1 — establish what you are looking at

- **Which databank**, and whether its trades are already exported to
  `~/Desktop/AlgoData/raw/<project>/<databank>/<date>/trades/`. If they are not, export them first
  with `python3 -m sqx.export.export_trades --project P --databank D --symbol SYM` (see `/export`
  for the traps). Re-exporting the same rows costs minutes of SQX time for nothing.
- **Which asset**, so `assets/<SYMBOL>.yaml` supplies the point value and the spread.
- **Whether the bars exist**: `~/Desktop/AlgoData/bars/<feed>/M30.csv`. The daily volatility regime
  is resampled from them. Export them with `python3 -m sqx.export.export_bars --asset XAUUSD`.
- **Whether this is the right stage.** The module assumes the edge is already believed: it runs
  after the OOS decay test and the cross-market retest. Say so if it is being run before them —
  running it earlier is not wrong, but a PASS then means much less than it looks.

## Step 2 — run it

```bash
python3 -m core.assets XAUUSD                            # preflight, read it out
python3 -m strategies.monteCarlo.report --project XAUUSD --databank Results \
    --asset XAUUSD --export 2026-09-03
```

`use: null` in the asset file does **not** block here, as in `/analysis-crossmarket` and for the
same reason: this study stresses a backtest SQX already ran, and the cost of every trade is
**recovered** from the export (`gross − net`) rather than chosen. Say that out loud instead of
silently skipping the preflight.

| flag | what it does |
|---|---|
| `--export` | the export date under `raw/`, not today's date |
| `--portfolio` | analyse every strategy as one combined trade stream; writes to `montecarlo_portfolio/`, beside the per-strategy report and never over it |
| `--bars-timeframe` | which exported bars the daily volatility comes from; `M30` by default |
| `--set KEY=VALUE` | override any value of `config.yaml`, e.g. `--set global.n_sims=20000` |

Everything tunable is in `strategies/monteCarlo/config.yaml`, grouped by family. **The three knobs
that matter**: `global.n_sims` (cost), `scoring.survival_dd_pct` (the account-survival ceiling, a
placeholder) and `stability.n_stability_runs` (the second biggest cost).

Runtime on 96 cores: about 6 s per strategy at 20,000 simulations, plus about a minute of stability
for the whole run. At the specified 100,000 it is roughly five times that.

## The panel, when the question is about one strategy

```bash
python3 -m strategies.monteCarlo.explorer.serve --project XAUUSD --databank Results \
    --asset XAUUSD --export 2026-09-03
```

Opens a local panel on `http://127.0.0.1:8765`: a dropdown of strategies, a button per family and
per sub-test, every distribution and statistic behind two dropdowns, and a button that writes that
strategy's report. Results are cached under `<data root>/derived/montecarlo/` with a fingerprint of
the whole config, so switching strategy is instant and a changed threshold marks every stored result
out of date in red. Use it when the owner asks about **one** strategy in depth, or wants to poke at
a test; use the batch command for a whole databank. Both draw from the same engine — the panel never
computes anything of its own.

## Step 3 — read it, in this order

0. **Open `montecarlo.html`.** Everything below is on it.
1. **The cost cross-check and the join coverage, in *Datos y método*.** If the modelled cost is far
   from the recovered one, Family C is describing another instrument. Nothing else is affected.
2. **The stability figure.** If it says the numbers are unstable, raise `n_sims` and re-run before
   reading a single verdict. There is no seed, on purpose.
3. **«Lo que falló».** Which checks tumbled how many strategies. Read this before any score: a
   veto that fires on five of every six strategies is telling you about the threshold, not about
   the fleet.
4. **The per-strategy table**, then the page of the ones that survived.

## Rules that keep the answer honest

- **This does not measure overfitting.** No DSR, no CSCV, and do not add them: they need the
  population of strategies tried during generation. Presenting a Monte Carlo as evidence against
  overfitting is the single easiest way to mislead with it.
- **The drawdown ceiling is a sizing statement.** `survival_dd_pct` at 10% with 1,000 $ of risk on a
  100,000 $ account vetoed 22 of 36 XAUUSD strategies. Halving the risk clears most of them. Never
  report that veto as a property of the strategies without saying what risk it assumed.
- **A failed gate vetoes; the composite is a reference.** Quote the binding constraint and its
  number, never the composite alone.
- **Runs are not reproducible.** Two runs give slightly different tails by design. The spread between
  them is reported; if it matters for a decision, the answer is more simulations.
- **Portfolio mode changes what order-dependent statistics mean.** When trades overlap in time, the
  longest losing run is not what it is for one strategy. The page says so when it detects it.
