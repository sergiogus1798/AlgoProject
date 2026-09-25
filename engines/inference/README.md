# engines/inference — correcting for the search

Every study that tests many things at once needs the same arithmetic: how many passed against
how many chance gives, and which of them can be named. It lives here once.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `fdr.py` | Benjamini-Hochberg over a family of tests: which may be named | imported | p-values → names |
| `excess.py` | Observed against chance over a family: the excess, Storey's share of nulls, and whether the p-values are fine-grained enough to name anyone | imported | p-values → excess, resolution |

Three related pieces stay where the ledger and the surfaces already read them: the PSR and the
minimum track record in `core/significance.py`, the number of independent trials in
`core/surface/trials.py`, and the deflated Sharpe in `core/surface/plateau.py`.
