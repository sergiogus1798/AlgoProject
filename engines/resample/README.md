# engines/resample — reorderings and resamplings of a trade sequence

Index generators: given a sequence length and a block, which positions each simulated run takes.
Nothing here prices a trade or reads a statistic.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Reorderings and resamplings of a trade sequence. | — | — |
| `draws.py` | How a trade stream is reordered or resampled. Every model behind one signature. | imported | n, size, block → index matrix |

Read by the Monte Carlo study and by the cross-market portfolio, which reorders the combined
account with the same generators — until 2026-09-25 one study imported the other to get them.
