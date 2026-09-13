# strategies/crossmarket/explorer — the interactive panel

The only way to run this study. There is no batch command: every test in the folder above —
Test 1a, exposure, significance, fingerprint, cost and correlation — runs from here, on one
strategy or on the whole database, and the panel's own "Generar informe" button writes the same
files a batch command used to. It is **a way of looking, never a second set of numbers**: every
figure comes from `charts.py`/`tables.py`, every table from `panel.py`, and the static report is
built by the same functions that render the live tabs.

```
serve ─▶ jobs ─▶ work ─▶ analysis ─▶ cache ─▶ sections ─▶ page.html
 routes   one     what     the study    disk    the HTML    the browser
         job at   a button
         a time   does
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `serve.py` | The routes and the launch: which databank, which strategies, which port | `python3 -m strategies.crossmarket.explorer.serve --project XAUUSD --databank RetestMarkets --asset XAUUSD --export 2026-09-08` | export → `http://127.0.0.1:8766` |
| `work.py` | What a button actually runs: analyse a strategy, analyse the database, write the report | imported | strategy(ies) → cache, file |
| `analysis.py` | The heavy half of `work.py`: every test in the folder above, on one strategy over its additional markets | imported | strategy → rows, shapes, verdict, breadth, correlation |
| `jobs.py` | One job at a time, off the request thread, publishing step-by-step progress | imported | callable → progress |
| `cache.py` | Results on disk under the data root, stamped with a hash of the run configuration | imported | result → JSON |
| `sections.py` | The panel's per-strategy tabs, rendered by `panel.py`/`tables.py`'s own functions | imported | record → HTML |
| `page.html` | The panel: dropdown, buttons, tabs, progress bar, config drawer and the test explorer | served | — |

## Why the cache is the point

Analysing one strategy runs Test 1a under four models plus Fases 1-4 on every additional market —
seconds, not minutes, but multiplied by a whole database it adds up, and every click on the
dropdown would pay it again inside the same session without a cache. Results live in
`<data root>/derived/crossmarket/<project>/<databank>/<strategy>.json`, each stamped with a
**fingerprint of the whole run configuration** — draws, models, alpha, the trade-count floors, the
bootstrap block, the cost multiples, the slippage fractions. Change any of them and every stored
result declares itself out of date, in red, rather than being silently reused to answer a question
it was not computed for.

The cache does not survive across launches: `serve.py` wipes the whole databank's stored results at
start-up, so the panel always opens with nothing analysed rather than showing a previous session's
strategies as if they were the current run's.

## One job at a time

`jobs.py` refuses a second job while one runs, off the request thread so the progress bar can be
polled. Unlike `monteCarlo/explorer`, there is no per-simulation callback to hook: a cross-market
run is a handful of numpy calls, so progress advances once per market (analysing one strategy) or
once per strategy (analysing the whole database).

## What the panel deliberately cannot do

- **Decide anything from a single re-run.** "Re-ejecutar esta prueba" runs one (market, model) pair
  on its own and shows it beside the stored one, marked as a re-run. It never overwrites the cached
  analysis.
- **Change the verdict rule's own file.** The config drawer's ALPHA / MIN_TRADES / MIN_ON_OPEN /
  MIN_MARKETS / CORRELATED fields patch `inference.py`'s module constants for the duration of one
  run (`analysis.overridden()`) and restore them after — `inference.py` itself is never edited, per
  the project's rule that the verdict model is validated and closed.
- **Be reached from another machine.** It binds `127.0.0.1` only.

## What "Analizar toda la base de datos" adds over the old batch command

The old `report.py` was the only way to run every strategy in one pass; now the panel has to do
that too, since it is the only entry point left. The button repeats "Analizar esta estrategia" for
every strategy in the export, filling the headline strip with the database-wide MANTENER count and
the luck figure once it finishes. "Generar informe" then reads what it cached — never recomputes —
to write `by_market.csv`, `verdict.csv`, `crossmarket.md` and `crossmarket.html`, and asks for that
button first if any strategy is missing or stale under the current configuration.
