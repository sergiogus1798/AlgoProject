---
q: export strategy to MQL5 mq5 source code headless without GUI, sqcli code export verb, Save to files task SaveSourceCode generator name, Invalid source code generator, Expert Advisor for MetaTrader5 (*.MQ5), magic numbers MNActive, exported EA money management differs from strategy, customSettings false retest sizing, SQX data to MT5 exportToMT5, SQX MCP tools list
tag: 🔬  date: 2026-09-29  see: eng/mt5-under-wine, eng/mt5-account-switch-unattended
---
# No sqcli verb writes MQL5; a "Save to files" task does — generator «Expert Advisor for MetaTrader5 (*.MQ5)»
- `sqcli -h` (build of 2026-09-29) has no code-export verb. SQX's own MCP (`mcpx`) has 6 tools: list_projects/databanks/strategies, get_strategy_stats, run_project, stop_project — none writes code.
- A custom project's **SaveToFiles** task does: `<SaveSourceCode type="Expert Advisor for MetaTrader5 (*.MQ5)">true</SaveSourceCode>` + `<DestDirectorySC>` (a Linux path works); its input databank is exported, one `.mq5` per strategy, named after it. Seconds, inside the same `action=start` as the project's other tasks (`sqx.projects.mt5verify.save_task`).
- ⚠️ The type is SQX's **internal** name. The GUI's label «MetaTrader 5 (*.mq5)» fails the whole project at start: `Cannot load SaveToFiles settings. Invalid source code generator`. The others: `Expert Advisor for MetaTrader4 (*.MQ4)`, `EasyLanguage for Tradestation / MultiCharts (*.el)`.
- Same task: `<MNActive>true</MNActive><MNValue>N</MNValue>` numbers the EAs' `MagicNumber` input from N — what a live↔backtest reconciliation keys on.
- ⚠️ **Neither the exported EA nor a retest task sizes like the strategy.** The EA came out «Fixed Amount» 100 USD (0.01-0.04 lots) and a retest with `customSettings="false"` applied its own `<MoneyManagement>` flags (the donor's ATR sizing, 0.07-0.47 lots), for a strategy whose `strategy_Portfolio.xml` stores FixedSize 0.1. Per lot the two agreed (1,637 vs 1,642 USD/lot). To compare, set both: the task's method flags (`tasksettings.set_money_management`) and the EA's `UseMoneyManagement = false` + `mmLotsIfNoMM` (`mt5.verify.mt5side.fixed_lots`).
- `sqcli -data action=exportToMT5 symbol=… timeframe=M1|Tick …` writes SQX's bars/ticks for MT5 — a way to backtest in MT5 on SQX's own data.

## Evidence
`curl 'http://localhost:5060/call?cmd=-h'` on the conductor, 2026-09-29: verbs -project -databank -symbol -instrument -data -tools -stockgroup -brokerprofile -run -gui -deletefile -waitfor -execute -license -exit.
`internal/plugins/SettingsSaveToFiles/SettingsSaveToFilesService.js` lines 40-60 (XML it writes), 88-92 (reads); the names from `internal/plugins/ResultsSourceCode/sourceCode.html` lines 45-53 (`config.type=='Expert Advisor for MetaTrader5 (*.MQ5)'`).
2026-09-29 19:42, `Test_MT5Verify_XAUUSD_H1_194218` with type «MetaTrader 5 (*.mq5)»: `action=start` → «it has config errors in task 'MQL5'. Invalid source code generator». 19:44, the same project with the internal name: «MQL5 : Task finished» 0.5 s after the retest, `Strategy 3.48.75.mq5` (8,662 lines, ASCII, `input int MagicNumber = 1;`) in `AlgoData/mt5/verify/20260929-194417_Strategy_3_48_75/mq5/`.
