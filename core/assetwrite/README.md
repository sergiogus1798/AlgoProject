# core/assetwrite — the only writer of assets/

Split into a folder on 2026-09-29 (`CODESTYLE.md` rule 1, file length cap). Every caller still writes
`from core import assetwrite` or `from core.assetwrite import <name>`: `__init__.py` re-exports
`brokers.py` and `markets.py`'s functions, so this remains one writer surface, not three.

| file | what it does | run it | in → out |
|---|---|---|---|
| `__init__.py` | The only writer of assets/: one value, one cost, or a whole asset in or out of the library. | — | change → file |
| `brokers.py` | Write one asset's `costs.commission.brokers` table — the per-broker figures `use` is picked from. | — | brokers dict → file |
| `failures.py` | Write one entry of an asset's `live_failures` list — why a strategy of it left the live protocol. | — | failure → file |
| `markets.py` | Write one asset's Cross Market check — `_markets.yaml`'s `family`/`structural` feeds. | — | feeds → file |
