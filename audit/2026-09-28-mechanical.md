# Mechanical audit 2026-09-28

Written by `tools/daily_audit.py`. It checks only what a machine can check;
documentation drift and statistical rigour need the `/audit` agent.

| check | result |
|---|---|
| `tools/checks.py` | FAILED |
| `tests/test_cfx.py` | ok |
| `tests/test_sqxfile.py` | ok |
| `docs/DEPENDENCIES.md` | stale, regenerated |
| projects that fail to render | Infinox_SP500ft_H4_HighPrecision |
| exports without a manifest | raw/Test_USDJPY_donchianUpperCrossUp_M30/SPP_IS/2026-09-27 |
| assets in use, cost still undecided | none |

## checks.py output

```
## file length: ok

## documentation: ok

## hardcoded paths: ok

## requirements: ok

## folder READMEs: 1
  ui/daemon/sqxconfig/README.md: lists.py not listed

## manual pages: ok

## dependency map: ok

## knowhow cards: ok

## knowhow links: 1
  ui/daemon/sqxconfig/lists.py:28: knowhow/conditions/wfm-acceptance does not exist

## knowhow indexes: ok

## workflow table: ok

766 files checked, 2 problems
```
