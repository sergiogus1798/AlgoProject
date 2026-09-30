# core/assetwrite — the only writer of assets/

Split into a folder on 2026-09-29 (`CODESTYLE.md` rule 1, 250 lines). Every caller still writes
`from core import assetwrite` or `from core.assetwrite import <name>`: `__init__.py` re-exports
`brokers.py` and `markets.py`'s functions, so this remains one writer surface, not three.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | One value, one cost with its `why`, one segment's end (`set_segment_end`, the monthly oos2 roll), or a whole asset into the library or onto the retired shelf | — | change → file |
| `brokers.py` | Replace one asset's `costs.commission.brokers` table — the per-broker figures `commission.use` is picked from | — | brokers dict → file |
| `markets.py` | `declare_main` gives an asset its own empty Cross Market block; `set_market` fills one category of it (`_markets.yaml`'s `family`/`structural` feeds) | — | feeds → file |
