# screening/filters — what a filter on an in-sample metric buys out of sample

| file | what it does | run it | in → out |
|---|---|---|---|
| `report.py` | Every IS metric cut at 5/10/20/30/50 % from both ends, judged only when it leaves 200 strategies, corrected together by Benjamini-Hochberg; per outcome, the best filters as bars of Δ median with their bootstrap interval | `python3 -m studies.screening.filters.report --project XAUUSD --databank OOS` | `metrics.csv` → `reports/<P>/<D>/<date>/filters/` |
| `TODO.md` | What is still open: combinations, and every project's databank at once | — | — |

The maths is `../analysis/improvement.py`; its README carries the three rules decided with the owner.
