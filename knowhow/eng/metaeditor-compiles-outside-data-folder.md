---
q: compile an mq5 without closing the MT5 terminal, MetaEditor with terminal open compiles nothing, compile EA outside MQL5 folder, /include MetaEditor command line, .ex5 in AlgoData, terminal MCP dies when the terminal closes
tag: 🔬  date: 2026-10-02  see: eng/metaeditor-compile-under-wine, eng/mt5-terminal-mcp-from-python
---
# MetaEditor compiles with the terminal open when the source sits outside the data folder
- The lock that makes MetaEditor write an empty log is on the data folder's `MQL5/` tree. A source elsewhere (`AlgoData/mt5/eas/<Firm>/x.mq5`) compiles while the terminal runs, and the `.ex5` lands next to it.
- Command line: `/compile:Z:\…\x.mq5 /log:Z:\…\x.log /include:.` with `cwd` = the data folder's `MQL5/` (the standard `<Trade/…>` includes resolve through `/include:.`; the `Z:` paths have no space, so Wine's argument splitting does not bite).
- So a recompile no longer needs the terminal closed — closing it kills the terminal's MCP for every session. Only the tester still does, and it needs the `.ex5` under `Experts/`.

## Evidence
2026-10-02, build 6231, terminal up (pid alive before and after): the 28 EAs of `AlgoData/mt5/eas/{FTMO,Hantec}/` compiled one by one, `Result: 0 errors, 0 warnings` each, 28 `.ex5` written there; `Experts/AlgoProject/{FTMO,Hantec}` byte-identical to its backup afterwards (`diff -rq`).
