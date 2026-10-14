# mt5 — MetaTrader 5 under Wine, and its MCP server

**Since 2026-09-29 the terminal's own MCP (`metatrader5`, MetaQuotes, local scope) is the main
surface** — tester, charts, data, journals; its trading and EA/script tools are denied in
`.claude/settings.json`. This folder keeps what it lacks: compiling (`metaeditor.py`), the comparison
with SQX (`compare.py`), Parquet exports (`live.py`). `tester.py`/`report.py` go once its JSON report
proves to carry every deal (OPEN.md #78).

Test an SQX strategy's MQL5 export in MT5's Strategy Tester, pair its trades with SQX's, and read
the terminal read-only. Claude drives it through the `mt5` MCP server (`.mcp.json`, stdio). There
is **no tool that sends, modifies or closes an order** (owner, 2026-09-27).

Install: `bin/mt5-wine-system.sh` (root, once: WineHQ staging as MetaQuotes' `mt5linux.sh` does it)
then `bin/mt5-install.sh` (prefix at `mt5_prefix` in `config/machine.yaml`, the terminal, a Windows
Python with the `MetaTrader5` package). Everything it writes goes to `core.paths.MT5_DATA`.
Manual: chapter `60-mt5`, in `docs/manual/10-cierre.pdf`. State: OPEN.md #78.

**No window opens**: `wine.env()` sends every Wine program to an Xvfb on `:77` (in `~/.local/bin`, started on demand); `MT5_VISIBLE=1` shows them on the desktop. `knowhow/mt5/mt5-tester-unattended.md`.

**Compiling needs the terminal closed**, exactly like the tester does: `MetaEditor64.exe` shares
`terminal64.exe`'s data-folder lock and, while the terminal is up, still exits 0 but writes only
the log's BOM and compiles nothing — `metaeditor.compile_path()` checks `wine.terminal_running()`
first and raises instead of returning that silently-empty result.
Every argument `wine.run()` hands a Windows program is joined into one command line **without
requoting one that contains a space** — and every path under the prefix has one (`Program Files`,
`MetaTrader 5`). Quoting the argument does not fix it; `wine.run(..., cwd=...)` plus a path
relative to `cwd` does, and is how `metaeditor.py` calls MetaEditor now.

| file | what it does | run it | in → out |
|---|---|---|---|
| `compare.py` | Pair the trades of an MT5 backtest with SQX's for the same strategy and window, and measure the gap. | imported | two trade frames → pairs + figures |
| `live.py` | Ask the running MT5 terminal read-only questions through the Windows Python in its Wine prefix. | imported | verb → JSON / parquet |
| `metaeditor.py` | Compile MQL5 sources with MetaEditor under Wine, and install the Sq* indicators SQX's EAs call. | imported | .mq5 → .ex5 + errors |
| `report.py` | Read a Strategy Tester HTML report: its summary figures, its deals, and the trades they make. | imported | report.htm → summary, deals, trades |
| `server.py` | MCP server over MetaTrader 5 under Wine: compile, backtest, compare with SQX, and read-only data. | `python3 -m mt5.server` (Claude Code starts it) | tool calls → JSON |
| `tester.py` | Run one Strategy Tester pass: write its ini, start the terminal detached, and collect the report. | imported | EA + window → report.htm, deals/trades.parquet |
| `wine.py` | Where MetaTrader 5 lives inside its Wine prefix, and how to run a Windows program there. | imported | — |

`winside/` runs under the Windows Python inside the prefix, not under the project's Python.

`verify/` is step 26, MT5 Bridge › Verificar in the window: one strategy retested in SQX at each
prop firm's conditions against its EA's backtest on that firm's MT5 account (its own README).
The accounts are `mt5_accounts` in `config/machine.yaml` (`core.paths.MT5_ACCOUNTS`).

`newsfilter/` writes a prop firm's news rule into SQX's MQL5 export — two EAs per strategy, with and
without the filter — keeps the calendar history (MT5's and Forex Factory's, from 2007) in
`MT5_DATA/calendar/`, and measures what the rule costs a strategy in the Strategy Tester, where the
patched EA reads that history from `Common\Files` (`/ea-news`, its own README).

`fleet/` is the live MT5 fleet on the VPS: the FleetBeacon service, the collector and MetaTracker (its own README, `CONTRACT.md`). `reconcile/` is the weeklyReconciler: the live accounts against the SQX backtest of the same week, descriptive, no pass bar (its own README, OPEN.md #78). Each SQX symbol's FTMO and Hantec names live in `mt5:` of `assets/symbols/<SYMBOL>.yaml`, not in a file here.

`indicators/` is the project's MQL5 indicator set, in MQL5's own `Indicators/` and `Include/` layout: the
add-on `Sq*` indicators SQX does not ship, and the owner's versions of `SqBBWidthRatio`,
`SqSRPercentRank` and `SqSuperTrend` (no rounding to 6 decimals, a range check instead of
`EMPTY_VALUE`). `mt5_install_sqx_indicators` copies it after SQX's, so it wins where both have a file.
