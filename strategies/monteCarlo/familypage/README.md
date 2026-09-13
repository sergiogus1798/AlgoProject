# strategies/monteCarlo/familypage — one strategy's page, one file per family

Split out of a single `familypage.py` once it passed 250 lines. `common.py` holds what every
family shares — the metric labels and `fmt()` — so `a.py`..`e.py` import from it, never from
`__init__.py`, which would be circular. `__init__.py` re-exports `family_a`..`family_e` and
`common`'s names, so `strategies.monteCarlo.familypage.family_a(...)` and `.fmt(...)` still work
exactly as before the split — nothing outside this folder needed to change.

| file | what it does | in → out |
|---|---|---|
| `common.py` | The metric labels and `fmt()`, shared by every family | imported | metric → label, cell |
| `a.py` | Family A — order luck | imported | result → HTML |
| `b.py` | Family B — composition luck, the IS/OOS level comparison | imported | result → HTML |
| `c.py` | Family C — execution luck, the four stress tests | imported | result → HTML |
| `d.py` | Family D — regime luck: calendar windows, volatility terciles, the two time series | imported | result → HTML |
| `e.py` | Family E — significance, the PSR | imported | result → HTML |
