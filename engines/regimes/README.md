# engines/regimes — the market state a trade was opened into

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `regime.py` | Daily volatility by ATR or GARCH, and each trade tagged with its tercile at entry | imported | daily bars + entries → terciles |

Read by the Monte Carlo study's family D; the conditional map (encargo 14) is the next reader.
