# crossmarket/orchestrate — one strategy through every market

The modules allowed to cross every layer, because that is what an orchestrator does. Until
2026-09-25 they lived inside the browser panel (`explorer/`), and the batch report imported them
from there; the panel is gone and they are here.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | Names what the package is; holds no code | — | — |
| `strategy.py` | One strategy's whole analysis: every market, the base asset's OOS stretch, the strategy-level views | imported | inputs → record |
| `market.py` | Everything one market's analysis runs — the null models, the window sweep, the tests without a null, the stress, the fingerprint — and the slimmer row the batch verdict needs | imported | trades + bars → row, runs |
| `stretch.py` | The same random-entry test on the base asset's declared out-of-sample stretch alone | imported | inputs → row, runs |
| `sweep.py` | The window sweep's execution: each free-placement model re-drawn inside every block size | imported | fixed + bars → windows, points |
| `views.py` | The two views that need more than one market at once — correlation and the combined account — and the joint null | imported | markets → views |
