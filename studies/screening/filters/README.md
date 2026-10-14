# screening/filters — what a filter on an in-sample metric buys out of sample

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | Sweep in-sample filters against out-of-sample outcomes, as one result and its page. | `python3 -m studies.screening.filters.report --project XAUUSD --databank OOS` | `metrics.csv` → `reports/<P>/<D>/<date>/filters/` |
| `TODO.md` | What is still open: combinations, and every project's databank at once | — | — |

The maths is `../analysis/improvement.py`; its README carries the three rules decided with the owner.
