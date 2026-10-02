---
q: Verificar clock offset; SQX vs MT5 trade times; FTMO Hantec server timezone; EETUS; Asia/Jerusalem the5ers; trades unpaired in March; DST US vs EU; clock_h 1 or 0 changes by strategy; row 1 matched below 95%
tag: 🔬  date: 2026-09-30  see: export/feed-clock-timezones, eng/mt5-history-depth-first-bar
---
# SQX's feed clock and the firms' server clock differ by date, not by a constant — convert zones
- FTMO's and Hantec's MT5 servers run on `EETUS` (New York + 7 h); the5ers' feeds on
  `Asia/Jerusalem`. They agree most of the year and differ by 1 h in the weeks between the US and
  the European/Israeli change (mid-March to late March, late October to early November).
- `mt5.verify.judge` converts every SQX time zone to zone (`mt5.compare.to_zone`, server zone in
  `mt5/verify/config.yaml` `clock.server_zone`) before seeking any whole-hour shift left.
- The residual shift is scored on pairs within half the tolerance first: with a one-bar
  tolerance greedy pairing can find one pair MORE when every pair is an hour off.

## Evidence
- 🔬 2026-09-30, USDJPY H1, 2022-06-01 → 2026-09-24, four strategies × two firms: with a constant
  shift every unpaired SQX entry but a handful fell in 2024-03-12…27, 2025-03-12…25,
  2026-03-09…26, 2022-10-31…11-03. Exact entry matches, constant → by zone: 16.9.76 FTMO
  0.889 → 0.946, Hantec 0.902 → 0.959; 10.9.72 0.887 → 0.955, 0.877 → 0.942.
- 🔬 same day, 10.9.72 Hantec after conversion: shift 0 → 375 pairs, all exact; shift +1 → 376
  pairs, all 1 h off; the old scorer took +1 (`clock_h` 1 for two strategies, 0 for the third).
  After the fix `clock_h` is 0 for all six; Hantec's daily correlation 0.944 → 0.979 (16.9.76),
  0.879 → 0.918 (10.9.72). Hantec still fails row 5 (drawdown) and 10.9.72 rows 1 and 3a.
