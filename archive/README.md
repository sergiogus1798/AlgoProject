# archive — finished work, not maintained

Scripts that answered a question once and were then superseded. They are kept because their results
are cited elsewhere and someone may want to reproduce them. **`CODESTYLE.md` does not apply here and
`tools/checks.py` skips this folder** — rewriting a finished study to satisfy a line limit buys nothing.

Nothing new goes here. If a script here is worth using again, rewrite it under `CODESTYLE.md` in the
phase folder where it belongs, and delete the copy here.

Everything here was written against the **old** data layout (`AlgoProject_Old/src/out`), not against
the data root. Reusing one means rewriting it over `core/` anyway, so it is parked rather than
polished. The findings themselves are already in `knowhow/`, which is what actually had to survive.

| file | what it answered |
|---|---|
| `studies/atr_stop.py` | What multiple of ATR(20) should the stop be? The re-runnable version |
| `studies/atr_stop_study.py` | The same question, first and longer version (770 lines) |
| `studies/is_oos_analysis.py` | Which in-sample metrics actually predict out-of-sample performance? |
| `studies/scan_strategies.py` | What is in the XAUUSD databanks — SL/PT settings, sides, exits? |
| `studies/validate_trades.py` | Do the exported trade CSVs agree with the strategies they came from? |
| `studies/plots.py`, `studies/plots_is_oos.py` | Figures for the two studies above |
| `studies/scatter_page.py` | Self-contained HTML explorer for a metrics export |
