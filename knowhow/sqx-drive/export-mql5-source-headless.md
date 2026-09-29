---
q: export strategy to MQL5 mq5 source code headless without GUI, sqcli code export verb, Save to files task SaveSourceCode generator, magic numbers MNActive, SQX data to MT5 exportToMT5, SQX MCP tools list
tag: 📓  date: 2026-09-29  see: eng/mt5-under-wine
---
# No sqcli verb writes MQL5; the "Save to files" task does (SaveSourceCode), with magic numbers
- `sqcli -h` (build of 2026-09-29) has no code-export verb. SQX's own MCP (`mcpx`) has 6 tools: list_projects/databanks/strategies, get_strategy_stats, run_project, stop_project — none writes code.
- A custom project's **SaveToFiles** task does: `<SaveSourceCode type="<generator>" format="...">true</SaveSourceCode>` + `<DestDirectorySC>`; the generator is looked up by name (`SourceCodeGenerators.getGeneratorFromName`) — the MT5 name is unverified (code folders: `MetaTrader5`, `MetaTrader4`, `EasyLanguage`, `JForex`, `PseudoCode`).
- Same task: `<MNActive>true</MNActive><MNValue>N</MNValue>` numbers the EAs' magic numbers from N — what a live↔backtest reconciliation keys on.
- `sqcli -data action=exportToMT5 symbol=… timeframe=M1|Tick …` writes SQX's bars/ticks for MT5 — a way to backtest in MT5 on SQX's own data.

## Evidence
`curl 'http://localhost:5060/call?cmd=-h'` on the conductor, 2026-09-29: verbs -project -databank -symbol -instrument -data -tools -stockgroup -brokerprofile -run -gui -deletefile -waitfor -execute -license -exit.
`internal/plugins/SettingsSaveToFiles/SettingsSaveToFilesService.js` lines 40-60 (XML it writes), 88-92 (reads); `TaskSaveToFiles.jar` strings: SaveSourceCode, SourceCodeType, SourceCodeFormat, "Invalid source code generator".
`strings mcpx/.../MCPTools.class`. Not yet run headless: OPEN.md #78.
