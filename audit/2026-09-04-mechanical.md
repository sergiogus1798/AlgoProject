# Mechanical audit 2026-09-04

Written by `tools/daily_audit.py`. It checks only what a machine can check;
documentation drift and statistical rigour need the `/audit` agent.

| check | result |
|---|---|
| `tools/checks.py` | ok |
| `tests/test_cfx.py` | ok |
| `tests/test_sqxfile.py` | ok |
| `docs/DEPENDENCIES.md` | stale, regenerated |
| projects that fail to render | Infinox_SP500ft_H4_HighPrecision |
| exports without a manifest | none |
| assets in use, cost still undecided | AUDJPY, AUDUSD, CADJPY, DAX40, DJ30, EURJPY, EURUSD, GBPJPY, GBPUSD, NIKKEI225, SP500ft, USA500, USATEC, USDCAD, USDCHF, USDJPY, XAUUSD |
