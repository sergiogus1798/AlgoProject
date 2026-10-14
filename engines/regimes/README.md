# engines/regimes — the market state a trade was opened into

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The market state a trade was opened into. | — | — |
| `regime.py` | Family D in market state: the daily volatility a trade was opened into, and its tercile. | imported | daily bars + entries → terciles |

Read by the Monte Carlo study's family D; the conditional map (encargo 14) is the next reader.
