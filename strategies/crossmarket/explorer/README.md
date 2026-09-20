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
| `sweep_run.py` | The window sweep's execution: each free-placement model re-drawn inside every block size | imported | fixed + bars → windows, points |
| `jobs.py` | One job at a time, off the request thread, publishing a continuous share | imported | callable → progress |
| `sections.py` | The tab registry and the tabs that are tables | imported | record → HTML |
| `overview_tab.py` | **The tab the panel opens on**: every market's real backtest, at equal risk, its equity curves and what holds the numbers up | imported | record → HTML |
| `portfolio_tab.py` | The Portfolio tab: the combined account, what each market adds to it, and two ways of asking how much is luck | imported | record → HTML |
| `stress_tab.py` | The cost-and-execution tab, with the assumptions it ran under named per market | imported | record → HTML |
| `sweep_tab.py` | The window-sweep tab: the markets × block sizes grid, then one market's three models on one p curve with Calendar Shift flat | imported | record → HTML |
| `sweep_views.py` | That tab's per-market panels: the power table, one histogram per block size, the cone of one size's confined runs, and the blocks | imported | sweep → HTML |
| `simulations.py` | The three tabs that draw simulated distributions and equity cones | imported | record → HTML |
| `page.html` | The panel: dropdown, market list, run buttons, tabs, progress bar, config drawer | served | — |

## It is the one place allowed to cross every layer

`analysis.py` is where the study's layers meet: it slices the window (`mechanics/envelope`), prices
the real run and the nulls (`simulate/backtest`), runs every test (`simulate/`), attaches the
warnings (`verdict/inference`) and hands the record to `views.py` for what needs more than one
market. The tab modules then read `render/` and nothing else that computes. Which layer a thing
belongs to is decided there, not here — see the module `README.md` and the import-direction table in
it.

## Nothing is stored

There is no cache, no staleness flag and no file on disk. `work.RESULTS` holds the session's runs in
memory and dies with the process; start-up deletes anything an earlier build left under
`<data root>/derived/crossmarket/`. A number on the panel always comes from the button that was just
pressed — which is the whole reason the cache was removed on 2026-09-15.

The cost of that is real: a strategy takes 107 s at the default 25,000 draws over two markets
— most of it the window sweep's nine extra nulls per market — and closing the panel throws it away.

## The two run buttons

**Run analysis** does the whole strategy: every market, every null model, every test. **run** beside
a market in the list does that one market only, with whatever the drawer says at that moment, and
**merges into what is already there** — so re-running one market at 50,000 draws does not throw away
the other. The markets are listed per strategy: one this strategy never traded on is shown greyed as
`sin operaciones` with no button, because the export writes a market's file only when the strategy
fired there, and that absence is a result rather than a gap.

## The tabs

`Backtest` · `Entrada aleatoria (1a)` · `Modelos` · `Barrido de ventana` · `Pareado (1b)` ·
`Exposición (1c)` · `Coste y ejecución` · `Huella` · `Portfolio` · `Avisos` · `Glosario`. There is no
verdict tab, because there is no verdict.

**`Backtest` opens first** and is where a reading starts: it absorbed `Resumen`, `Significancia` and
`Correlación`, which answered one question between them. `El mercado` (drivers) and the PCA half of
`Correlación` were removed — see `../render/README.md` for why. `Portfolio` is new: one account for every
market at once, and what each market adds to or takes from it.

Two of them draw simulations: **Entrada aleatoria** and **Coste y ejecución**. Both show, per market,
the equity cone with the real backtest on it and then one histogram per statistic — net, Ret/DD,
drawdown, Sharpe, PF — each with the simulated median, the p5-p95 band and the real value marked,
above the full percentile table. They answer different questions: the first is what random *timing*
could have done with the same rhythm, the second is what a worse *broker* could do to the same
trades.

**Barrido de ventana** opens on a grid rather than on a chart: one row per market, one column per
block size, the p in each cell and the trend beside it, so the question the tab exists to answer is
read without scrolling. Clicking a row opens that market underneath — the three swept models on one
p curve, the selected model's power table, one histogram per block size, the equity cone of the
block size the chips choose, and the blocks collapsed. Two selectors govern the whole tab: the
**model** chips and the **statistic** dropdown, which defaults to Net profit. Every half comes from
`/api/sweep/view`, rendered from results already in memory: changing any selector recomputes
nothing. It used to emit every market × every model at once, which on ten markets was thirty charts
and thirty tables in one page.

That dropdown is why `simulate/backtest.swept()` is gone. It priced only `mean_r` and the trade count, so the
sweep could answer for no other statistic and had no distribution to draw; every sweep point now
goes through the same `simulate/backtest.drawn()` + `summary()` as a null model and keeps the whole
metric table, a histogram per metric and a cone. It costs: the same strategy over two markets at
25,000 draws went from 36-52 s to **107 s**, and the sweep is most of it. 🔬 After the 2026-09-16
rebuild, Strategy 2.29.29 over two markets measures **95 s** — the additions on top of the sweep are
the cost stress at 25,000 runs instead of 5,000, Test 1b under four reference windows, and the
portfolio account.

## The config drawer

Every knob of `config.yaml`, grouped by section, each with the sentence `tooltips.py` gives it on
hover. Editing one changes what the **next** run does and is never written back to disk; the same
overrides can be passed at launch with `--set nulls.draws=20000`.

## Progress

`jobs.py` publishes a continuous share rather than counting steps, because
`simulate/backtest.null()` draws
its runs in batches and calls back after each one. The bar therefore moves several times inside every
model, and the line under it names the market and the model running right now.

## What the panel deliberately cannot do

- **Decide anything.** No verdict, no ranking, and no market is ever hidden.
- **Reuse a result.** See above. A second strategy's numbers never come from a previous session.
- **Write a knob back to disk.** The drawer patches one run; `config.yaml` is edited by hand.
- **Be reached from another machine.** It binds `127.0.0.1` only.
