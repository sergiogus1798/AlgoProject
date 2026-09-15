# strategies/crossmarket/explorer — the panel

The only way to run this study, **one strategy at a time**. Pick a strategy, see the markets SQX
retested it on, set every knob, press **Run analysis**.

```
serve ─▶ scope ─▶ jobs ─▶ work ─▶ analysis ─▶ sections ─▶ page.html
 routes  the      one     the      the study   the HTML    the browser
         drawer's job at  session
         overrides a time record
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `serve.py` | The routes and the launch: which databank, which strategies, which port | `python3 -m strategies.crossmarket.explorer.serve --project XAUUSD --databank "Retest Markets - Family" --asset XAUUSD --export 2026-09-14` | export → `http://127.0.0.1:8766` |
| `scope.py` | Turns the config drawer's overrides into the config one request runs with | imported | payload → cfg |
| `tooltips.py` | One sentence per `config.yaml` knob, for the drawer's hover text | imported | — |
| `work.py` | What a button runs, and the session's results | imported | strategy → RESULTS |
| `analysis.py` | The heavy half: every null model and every test, market by market | imported | strategy → rows, runs |
| `jobs.py` | One job at a time, off the request thread, publishing a continuous share | imported | callable → progress |
| `sections.py` | The tab registry and the tabs that are tables | imported | record → HTML |
| `sweep_tab.py` | The window-sweep tab: one p curve per free-placement model with Calendar Shift flat, its power table, and the blocks | imported | record → HTML |
| `simulations.py` | The three tabs that draw simulated distributions and equity cones | imported | record → HTML |
| `page.html` | The panel: dropdown, market list, run buttons, tabs, progress bar, config drawer | served | — |

## Nothing is stored

There is no cache, no staleness flag and no file on disk. `work.RESULTS` holds the session's runs in
memory and dies with the process; start-up deletes anything an earlier build left under
`<data root>/derived/crossmarket/`. A number on the panel always comes from the button that was just
pressed — which is the whole reason the cache was removed on 2026-09-15.

The cost of that is real: a strategy takes 36-52 s at the default 25,000 draws over two markets
— half of it the window sweep's nine extra nulls per market — and closing the panel throws it away.

## The two run buttons

**Run analysis** does the whole strategy: every market, every null model, every test. **run** beside
a market in the list does that one market only, with whatever the drawer says at that moment, and
**merges into what is already there** — so re-running one market at 50,000 draws does not throw away
the other. The markets are listed per strategy: one this strategy never traded on is shown greyed as
`sin operaciones` with no button, because the export writes a market's file only when the strategy
fired there, and that absence is a result rather than a gap.

## The tabs

`Resumen` · `Entrada aleatoria (1a)` · `Modelos` · `Barrido de ventana` · `Pareado (1b)` · `Exposición (1c)` ·
`Coste y ejecución` · `Significancia` · `Huella` · `El mercado` · `Correlación` · `Avisos` ·
`Glosario`. There is no verdict tab, because there is no verdict.

Two of them draw simulations: **Entrada aleatoria** and **Coste y ejecución**. Both show, per market,
the equity cone with the real backtest on it and then one histogram per statistic — net, Ret/DD,
drawdown, Sharpe, PF — each with the simulated median, the p5-p95 band and the real value marked,
above the full percentile table. They answer different questions: the first is what random *timing*
could have done with the same rhythm, the second is what a worse *broker* could do to the same
trades.

## The config drawer

Every knob of `config.yaml`, grouped by section, each with the sentence `tooltips.py` gives it on
hover. Editing one changes what the **next** run does and is never written back to disk; the same
overrides can be passed at launch with `--set nulls.draws=20000`.

## Progress

`jobs.py` publishes a continuous share rather than counting steps, because `backtest.null()` draws
its runs in batches and calls back after each one. The bar therefore moves several times inside every
model, and the line under it names the market and the model running right now.

## What the panel deliberately cannot do

- **Decide anything.** No verdict, no ranking, and no market is ever hidden.
- **Reuse a result.** See above. A second strategy's numbers never come from a previous session.
- **Write a knob back to disk.** The drawer patches one run; `config.yaml` is edited by hand.
- **Be reached from another machine.** It binds `127.0.0.1` only.
