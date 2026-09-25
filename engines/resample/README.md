# engines/resample — reorderings and resamplings of a trade sequence

Index generators: given a sequence length and a block, which positions each simulated run takes.
Nothing here prices a trade or reads a statistic.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `draws.py` | i.i.d. and stationary bootstraps, plain and block shuffles, what each preserves and which family it belongs to | imported | n, size, block → index matrix |

Read by the Monte Carlo study and by the cross-market portfolio, which reorders the combined
account with the same generators — until 2026-09-25 one study imported the other to get them.
