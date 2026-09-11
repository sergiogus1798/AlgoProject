# strategies/monteCarlo/explorer — the interactive panel

A local web panel over the study in the folder above. It is **a way of looking, never a second set
of numbers**: every figure it draws comes from `charts.py`, every section from `familypage.py` and
`strategypage.py`, and its report button writes byte-for-byte the same page the batch command
writes. If the panel and the report ever disagreed, one of them would be lying, so neither is
allowed to own a calculation.

```
serve ─▶ jobs ─▶ work ─▶ run / stability ─▶ cache ─▶ sections ─▶ page.html
 routes   one     what     the study         disk    the HTML    the browser
         job at   a button
         a time   does
```

| file | what it does | run it | in → out |
|---|---|---|---|
| `serve.py` | The routes and the launch: which databank, which strategies, which port | `python3 -m strategies.monteCarlo.explorer.serve --project XAUUSD --databank Results --asset XAUUSD --export 2026-09-03` | export → `http://127.0.0.1:8765` |
| `work.py` | What a button actually runs: analyse a strategy, re-run one test, write a report | imported | strategy → cache, file |
| `jobs.py` | One job at a time, off the request thread, publishing the progress the terminal would print | imported | callable → progress |
| `cache.py` | Results on disk under the data root, stamped with a hash of the config | imported | result → JSON |
| `sections.py` | The panel's content, rendered by the report's own functions | imported | result → HTML |
| `page.html` | The panel: dropdown, buttons, tabs, progress bar and the test explorer | served | — |

## Why the cache is the point

Analysing one strategy at 100,000 simulations takes about half a minute of 96 cores. Without a
cache, every click on the dropdown pays it again and the panel becomes unusable in ten minutes.
Results live in `<data root>/derived/montecarlo/<project>/<databank>/<strategy>.json`, and each one
carries a **fingerprint of the whole config**. Change a threshold, the simulation count or the
volatility model and every stored result declares itself out of date, in red, at the top of the
section — it is never silently reused to answer a question it was not computed for.

What is stored is the summary and the histograms (a few hundred kilobytes), never the raw draws.
That is why a distribution can be redrawn instantly and why the file does not grow to gigabytes.

## One job at a time

Two analyses at once would fight over every core and neither progress bar would mean anything, so
`jobs.py` refuses the second. The button that starts a job disables itself until it ends, and a
failure is shown on the page — a traceback in a server log nobody has open is not an error message.

## What the panel deliberately cannot do

- **Decide anything from a single re-run.** «Re-ejecutar esta prueba» runs one sub-test and shows it
  beside the stored one, marked as a re-run. It never overwrites the cached analysis and it cannot
  move a verdict: a verdict comes from one whole analysis or from none.
- **Run a whole databank.** That is the batch command, which is what you leave running while you do
  something else. The panel is for one strategy at a time, in depth.
- **Be reached from another machine.** It binds `127.0.0.1` only. If you clone this repo elsewhere,
  it works there the same way: nothing about it is specific to this machine.
