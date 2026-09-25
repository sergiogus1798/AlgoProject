---
q: where are SQX logs; log retention 14 days; log size GB; archive_logs AlgoData/logs; XAUUSD data coverage dates; build window unused gold data
tag: 🔬  date: 2026-09-04  see: eng/log-retention, sqx-drive/gui-web-surface
---
# SQX keeps 14 days of logs and prunes on start — `archive_logs.py` must run more often than that
`<install>/user/log/StrategyQuant/log_YYYY_MM_DD.log`; one day can be multi-GB. Archive to
`AlgoData/logs/<install>/` with `sqx/export/archive_logs.py` (per-project condensed logs under
`SQX/projects/<P>/`; retention policy: `eng/log-retention`).
`XAUUSD_DukasM1_Infinox` covers 2003.05.05 → 2026.01.16; the XAUUSD build window ends 2017.12.31.

## Evidence
`log_2026_08_18.log` = 4.66 GB; master's whole log tree 4.4 GB; gzips to 102 MB.
First full archive 2026-09-04, back to 2026-06-13. Coverage from `-symbol action=list` on the worker;
8 years of gold data unused by the build.
