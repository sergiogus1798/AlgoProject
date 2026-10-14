# monteCarlo/contract — the result read as the contract's blocks

`run.analyse()` returns numbers; this folder turns them into what `core/study/CONTRACT.md` calls the
result: tabs of blocks, each block one of eight kinds, every sentence in Spanish. It decides
nothing — the gates and the score are `verdict/` — and computes nothing but the reshaping.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The Monte Carlo result read as the contract's blocks. | — | — |
| `explorer.py` | The explorer tab: any sub-test's distribution of any statistic, chosen by two selectors. | imported | result → tab |
| `headline.py` | The verdict tab: the call and why, what failed, the backtest at a glance, and the sub-scores. | imported | result + verdict → tab |
| `order.py` | Families A and B as tabs: order luck (the same trades reordered) and composition luck. | imported | result → tab |
| `regime.py` | Families C, D and E as tabs: execution, regime, and whether the edge could be zero. | imported | result → tab |
| `shapes.py` | This study's histograms and percentile tables turned into contract blocks, in reading units. | imported | result parts → blocks |
| `words.py` | The words the owner reads: every fired check as a sentence, and why the verdict is what it is. | imported | flag → text |

The explorer tab carries every combination; a static page draws only the selectors' defaults
(`core/study/render/page.shown`), which keeps a strategy's page near the old 0.6 MB.
