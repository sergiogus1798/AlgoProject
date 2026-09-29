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

**No window opens**: `wine.env()` sends every Wine program to an Xvfb on `:77` (in `~/.local/bin`, started on demand); `MT5_VISIBLE=1` shows them on the desktop. `knowhow/eng/mt5-tester-unattended.md`.

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
| `server.py` | The MCP server: status, compile, backtest start/result, runs, compare, and the read-only live tools | `python3 -m mt5.server` (Claude Code starts it) | tool calls → JSON |
| `wine.py` | Where the terminal, MetaEditor and the Windows Python live in the prefix; Linux → Windows paths; the terminal's data folder (via `origin.txt`); running an .exe (`cwd=` for a space-free relative argument) | imported | — |
| `metaeditor.py` | Compile an .mq5 (or a folder) with MetaEditor and read its log; install SQX's `Sq*` indicators and the project's `indicators/` over them — refuses while the terminal is open | imported | .mq5 → .ex5 + errors |
| `tester.py` | Write a tester ini, start the terminal detached, collect the report into `MT5_DATA/tests/<run>/` | imported | EA + window → report.htm, deals/trades.parquet |
| `report.py` | Parse the tester's HTML report: summary cells, the deal rows (found by shape, not by language), trades paired from in/out deals | imported | report.htm → summary, deals, trades |
| `compare.py` | Pair MT5 trades with SQX's (same side, nearest entry within a tolerance) and the figures of the gap | imported | two trade frames → pairs + figures |
| `live.py` | Run a verb of `winside/query.py` under the Windows Python; bars and ticks to Parquet | imported | verb → JSON / parquet |

`winside/` runs under the Windows Python inside the prefix, not under the project's Python.

`newsfilter/` writes a prop firm's news rule into SQX's MQL5 export — two EAs per strategy, with and
without the filter (`/ea-news`, its own README).

`indicators/` is the project's MQL5 indicator set, in MQL5's own `Indicators/` and `Include/` layout: the
add-on `Sq*` indicators SQX does not ship, and the owner's versions of `SqBBWidthRatio`,
`SqSRPercentRank` and `SqSuperTrend` (no rounding to 6 decimals, a range check instead of
`EMPTY_VALUE`). `mt5_install_sqx_indicators` copies it after SQX's, so it wins where both have a file.
