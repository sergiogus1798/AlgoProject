# engines/inference — correcting for the search

Every study that tests many things at once needs the same arithmetic: how many passed against
how many chance gives, and which of them can be named. It lives here once.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Correcting for the search. | — | — |
| `excess.py` | Observed against chance: how many of a family of tests passed, and how many should have. | imported | p-values → excess, resolution |
| `fdr.py` | Benjamini-Hochberg over a family of tests: which of them may be named as discoveries. | imported | p-values → names |
| `localfdr.py` | Local false discovery rate of one lot of z, against the lot's own empirical null. | imported | z → p, delta0, sigma0, pi0 |
| `snooping/` | Hansen's SPA and Romano–Wolf's StepM over a panel of daily excess returns: does any beat its benchmark, and which | imported | T×K excess → p-values, names |

Three related pieces stay where the ledger and the surfaces already read them: the PSR and the
minimum track record in `core/significance.py`, the number of independent trials in
`core/surface/trials.py`, and the deflated Sharpe in `core/surface/plateau.py`.
