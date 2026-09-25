# crossmarket/contract — the study read as the contract's blocks

What the old panel's twelve tabs showed, as data (`core/study/CONTRACT.md`): the window paints it with
native widgets and `core/study/render` draws the batch page from the same dict. Nothing here
computes a number or decides anything; every block is built from what `orchestrate/` returned.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `words.py` | Each null model's name, what it randomises and the argument for it, the retired one, the mechanical checks, the glossary | imported | — |
| `shared.py` | A stored histogram, a cone, a metric table and per-market bars as blocks; dated curves on one axis; old HTML sentences as plain text | imported | parts → blocks |
| `backtest.py` | The opening tab: breadth, every market's backtest at face value and at equal risk, equity, correlation, joint null, tests, evidence, exits, checks | imported | record → tab |
| `nulls.py` | 1a per market × model × statistic, the same on the base asset's OOS stretch, the model comparison, and the warnings table | imported | record → tabs |
| `sweep.py` | The window sweep behind four selectors: the grid, the p curve, the power table, confined distributions and cones, the blocks | imported | record → tab |
| `tests.py` | The paired test (1b), exposure (1c), cost and execution, and the fingerprint | imported | record → tabs |
| `portfolio.py` | The combined account and the warnings tab | imported | record → tabs |

A market run alone (`one.run(only=…)`) returns only the per-market tabs: correlation, portfolio,
joint null and the OOS stretch need every market, and a partial result never carries a stale one.
