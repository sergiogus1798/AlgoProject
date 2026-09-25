# monteCarlo/contract — the result read as the contract's blocks

`run.analyse()` returns numbers; this folder turns them into what `docs/encargos/19-…` calls the
result: tabs of blocks, each block one of eight kinds, every sentence in Spanish. It decides
nothing — the gates and the score are `verdict/` — and computes nothing but the reshaping.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `words.py` | Every fired check as a sentence with its number, the metric labels and units, and why the verdict is what it is | imported | flag → text |
| `shapes.py` | A stored histogram and its percentile table as a `distribution`, a model table, an IS/OOS pair, a cone; shares read in percent | imported | result parts → blocks |
| `headline.py` | The verdict block, the verdict tab (what failed, at a glance, sub-scores) and the summary row verdict.csv carries | imported | result + verdict → tab |
| `order.py` | Families A and B: order and composition luck | imported | result → tab |
| `regime.py` | Families C, D and E: execution, regime, significance | imported | result → tab |
| `explorer.py` | The explorer tab — every sub-test × statistic behind two selectors, each sub-test's cone — the method tab and the glossary | imported | result → tab |

The explorer tab carries every combination; a static page draws only the selectors' defaults
(`core/study/render/page.shown`), which keeps a strategy's page near the old 0.6 MB.
