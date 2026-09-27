# Mechanical audit 2026-09-27

Written by `tools/daily_audit.py`. It checks only what a machine can check;
documentation drift and statistical rigour need the `/audit` agent.

| check | result |
|---|---|
| `tools/checks.py` | FAILED |
| `tests/test_cfx.py` | ok |
| `tests/test_sqxfile.py` | ok |
| `docs/DEPENDENCIES.md` | stale, regenerated |
| projects that fail to render | Infinox_SP500ft_H4_HighPrecision |
| exports without a manifest | raw/TestUSDJPY_Workflow_v1/SPP_IS/2026-09-24, raw/TestUSDJPY_Workflow_v1/SPP_IS_perf/2026-09-24, raw/Test_USDJPY_donchianUpperCrossUp_M30/SPP_IS/2026-09-26, raw/Test_USDJPY_donchianUpperCrossUp_M30/SPP_OOS/2026-09-26, raw/USDJPY_emaCross_H1/SPP_IS/2026-09-25, raw/USDJPY_emaCross_H1/SPP_OOS/2026-09-25, raw/USDJPY_workflow_profiling_v1/SPP_IS/2026-09-26, raw/USDJPY_workflow_profiling_v1/SPP_OOS/2026-09-26 |
| assets in use, cost still undecided | DAX40, DJ30, NIKKEI225, SP500ft, USA500, USATEC |

## checks.py output

```
## file length: ok

## documentation: ok

## hardcoded paths: ok

## requirements: ok

## folder READMEs: ok

## manual pages: ok

## dependency map: ok

## knowhow cards: ok

## knowhow links: ok

## knowhow indexes: 1
  knowhow/sqx-format/INDEX.md: stale, run tools/knowhowmap.py

658 files checked, 1 problems
```
