# retest/explorer — the same study, one strategy at a time, on demand

The panel. It is **a way of looking, never a second set of numbers**: every section it draws comes
from `render/panel.py`, the same functions the batch report calls, and its report button writes
byte for byte the same page `../report.py` writes. Verified rather than asserted — the verdict tab
and the report's section for the same strategy both came back at 22,156 bytes and compared equal
on 2026-09-19. If the two ever disagreed one of them would be lying, so neither is allowed to own
a calculation.

```
serve ─▶ scope ─▶ jobs ─▶ work ─▶ run.one ─▶ sections ─▶ render/panel ─▶ page.html
 routes  drawer's  one job  the       the four   which tab   the same HTML   the browser
         overrides at a time session  questions              the report uses
```

**Imports from:** everything · **Consumed by:** nobody
**Must not contain:** a statistic, a threshold, or a figure of its own

| file | what it does | run it | in → out |
|---|---|---|---|
| `serve.py` | The Flask routes and the one-process entry point | `python3 -m strategies.retest.explorer.serve --project XAUUSD` | request → HTML |
| `scope.py` | The config drawer's overrides into the cfg one request runs with | imported | payload → cfg |
| `jobs.py` | One job at a time, off the request thread | imported | callable → state |
| `work.py` | What each button runs, and the session's result store | imported | setup → result |
| `sections.py` | The tab registry, rendered by the report's own functions | imported | result → HTML |
| `tooltips.py` | One sentence per config knob, for the drawer | imported | — |
| `page.html` | The panel itself: controls, tabs, drawer | served | — |

## Contracts and traps

- **There is no cache, and that is the opposite of what `monteCarlo/explorer/` does.** That study
  caches because analysing one strategy costs half a minute of 96 cores. Here the expensive half
  already happened at ingest: reading one strategy out of the parquet and running the four
  questions takes about a second. A cache would buy nothing and would add a way to read a stored
  number as the answer to a question it was not computed for. `work.RESULTS` lives in memory and
  dies with the process.
- **`scope.scoped()` copies, never mutates.** A run made with the drawer open must not change what
  any other strategy sees. Measured: relaxing `gates.exec_keep_frac` to 0.30 moved one strategy's
  composite from 32.7 to 38.2 and left every other result untouched.
- **A GET carries the drawer state too.** Every tab fetch attaches `?cfg=`, because a section
  rendered under an override has to be rendered with that override and not with `config.yaml` on
  disk — otherwise a number on screen answers a question nobody asked.
- **One job at a time, on purpose.** Two analyses writing into one session store is a race that
  would never fail cleanly.
- **The drawer's thresholds are unvalidated defaults**, and `tooltips.py` says so on the two that
  matter. Relaxing a gate until a strategy passes is not calibration, it is choosing the answer.
