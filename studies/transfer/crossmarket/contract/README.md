# crossmarket/contract — the study read as the contract's blocks

What the panel's tabs show, as data (`core/study/CONTRACT.md`): the window paints it with
native widgets and `core/study/render` draws the batch page from the same dict. Nothing here
computes a number or decides anything; every block is built from what `orchestrate/` returned.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `words.py` | The two renamed tests' names (`TEST_1A`, `TEST_1B`; no "1A"/"1B" anywhere a reader sees), each null model's name and its argument, the retired one, the mechanical checks, the glossary | imported | — |
| `shared.py` | A stored histogram, a cone, a metric table and per-market bars as blocks; dated curves on one axis; old HTML sentences as plain text | imported | parts → blocks |
| `backtest.py` | The opening tab: breadth, equity (USD, dashed/shaded), every market's backtest at face value and at equal risk, correlation of weekly returns, joint null, tests, evidence (Sharpe total / Sharpe de referencia / MinTRL) | imported | record → tab |
| `nulls.py` | Entrada aleatoria per market × model × statistic, the same on the base asset's OOS stretch, the model comparison (p por modelo as a market × model table), and the warnings table — `HIDDEN`/`HIGHLIGHT` decide what a reader sees | imported | record → tabs |
| `sweep.py` | The window sweep behind four selectors: the grid (kept), the p-by-block-size table (was a plot), confined distributions and cones, a short description per swept model | imported | record → tab |
| `tests.py` | Timing Alpha and Exposure (1c) | imported | record → tabs |

**Removed 2026-09-30 (owner's feedback §4.16, code+UI+tests):** `portfolio.py` (the combined-account
and its warnings tab) and the "Coste y ejecución" / "Huella" tabs that used to live in `tests.py`.
Nothing recomputes them; `simulate/{portfolio,stress,fingerprint}.py` and `inputs/execution.py` are
gone too. `backtest.py`'s "Por dónde salieron las operaciones" table is also removed (§4.11): the
underlying `row["exits"]`/`reproducible_pnl` fields are still written by `orchestrate/market.py`
(nothing else reads them today) but no block shows them any more.

A market run alone (`one.run(only=…)`) returns only the per-market tabs: correlation, the
joint null and the OOS stretch need every market, and a partial result never carries a stale one.
