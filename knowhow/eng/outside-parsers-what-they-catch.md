---
q: What do settings.xml, SQX's StrategyProblems and the tester's history quality catch that our parsers do not?
kw: sqx-mcp mt5-quant mcp-mt5 comparison of parsers, cases our readers miss, core.sqxfile.symbol empty, symbol with dot or lowercase UKOIL.cash SP500ft @ES, StrategyProblems bitmask BadStrategyException, History Quality not read, start time changed to provide data, tester report covers another period, .set last used inputs, OptMode terminal.ini, report htm.xml, UTF-16 without BOM
tag: 🔬  date: 2026-10-02  see: mt5/mt5-history-depth-first-bar, mt5/mt5-tester-unattended, databanks/databank-verbs
---
# Three things outside parsers read that ours do not: the symbol from settings.xml, SQX's `StrategyProblems`, and the tester's history quality
Read-only comparison with DAVIDAROCA27/sqx-mcp, masdevid/mt5-quant and PHUICMT/mcp-mt5 (all MIT), each candidate checked on our own files. Confirmed:
1. **`core.sqxfile.symbol()` / `describe()` return `("", "")` when the symbol is not `[A-Z0-9]+`** — a dot, a lowercase letter, an `@`. sqx-mcp reads `<Result>/<ValuesMap>/<Symbol>` in `settings.xml`, which carries any name (`UKOIL.cash_M1`, `SP500ft_Plus02_Infinox`).
2. **`StrategyProblems`** (`settings.xml`, `SpecialValuesMap/SettingsMap`) is SQX's own bitmask of `BadStrategyException` reasons (no trades, too few, zero-P/L, too short, zero duration, too many open, too long, none filled) — the red «Strategy Problems» box of its overview. Nothing here reads it.
3. **The tester's history quality and its `start time changed to …` journal line.** The report's `Period` row repeats the window that was ASKED; `mt5.tester.collect()` reads neither the `History Quality` cell nor the journal, so a run on thin history is collected as a normal one. The a-priori depth guard (`mt5/mt5-history-depth-first-bar`) covers only «Desde = MT5».
Not applicable here (checked): UTF-16 without BOM, `.htm.xml` reports, `ShutdownTerminal` unreliable, stale `.set` inputs, `OptMode=-1`, the first-start history-sync failure, reversal deals, the default magic 11111, databank sync races, XXE — details below.

## Evidence
1. 10,123 `.sqx` under the three installs' `user/projects/*/databanks`: 147 read `("", "")` — mains
   `SP500ft_…` (145) and `@ES`, `@EW`, all on the master. `RESULTS_RE` on the real entry
   `AdditionalMarket: UKOIL.cash_M1_LOM_H1:  UKOIL.cash_M1_LOM_H1` → no match; no file has UKOIL as
   Main yet. 0 files answered from a non-Main entry.
2. 3,375 sampled: `StrategyProblems` 0 in 3,342; 2 in 14, 8 in 13, 1 in 6 (e.g. custodian
   `Test_Calib_GBPUSD_H1_rupturaL/databanks/OOS/Strategy 15.2.366.sqx` = 2). Meaning from
   `internal/extend/Snippets/SQ/Stats/Overview/DefaultOpenDD.java`; the bit of each reason is in
   the jar, not read.
3. 29 reports under `AlgoData/mt5/tests`: ours = the report on every one (trades = «Total Trades»,
   ΣP/L = «Total Net Profit»). `V100545…hantec_USDJPY.h…2008-07-01…`: «History Quality 22%»,
   `Period H1 (2008.07.01 - 2026.09.24)`, first trade 2022-06-08, 457 trades — the same 457 as the
   2022-06-01 run (76 %); FTMO 95–99 %. `Tester/logs/20260930.log`: `USDJPY.h: start time changed
   to 2008.12.03 00:00 to provide data at beginning`.
Not applicable: 29/29 reports carry the BOM and end in `.htm`; every run closed its terminal; 19/19
`MQL5/Profiles/Tester/*.set` equal their `.mq5` defaults (enums aside); `OptMode=-1` sits in
`Config/terminal.ini` with 29 single-pass reports; 0 journal hits for `cannot synchronize` /
`tested with error`; Direction is only in/out; magics are numbered by `MNValue` and
`mt5.reconcile.register` refuses a repeat; sync is covered by `databanks/databank-verbs`;
`ElementTree` resolves no external entity. A task whose XML is missing from the `.cfx`
(`cfx.task_xml` → KeyError) exists only in the master's `Infinox_SP500ft_H4_HighPrecision`, OPEN #3.
