# mt5 — MetaTrader 5 under Wine, and its MCP server

Test an SQX strategy's MQL5 export in MT5's Strategy Tester, pair its trades with SQX's, and read
the terminal read-only. Claude drives it through the `mt5` MCP server (`.mcp.json`, stdio). There
is **no tool that sends, modifies or closes an order** (owner, 2026-09-27).

Install: `bin/mt5-wine-system.sh` (root, once: WineHQ staging as MetaQuotes' `mt5linux.sh` does it)
then `bin/mt5-install.sh` (prefix at `mt5_prefix` in `config/machine.yaml`, the terminal, a Windows
Python with the `MetaTrader5` package). Everything it writes goes to `core.paths.MT5_DATA`.
Manual: chapter `60-mt5`, in `docs/manual/10-cierre.pdf`. State: OPEN.md #78.

| file | what it does | run it | in → out |
|---|---|---|---|
| `server.py` | The MCP server: status, compile, backtest start/result, runs, compare, and the read-only live tools | `python3 -m mt5.server` (Claude Code starts it) | tool calls → JSON |
| `wine.py` | Where the terminal, MetaEditor and the Windows Python live in the prefix; Linux → Windows paths; the terminal's data folder (via `origin.txt`); running an .exe | imported | — |
| `metaeditor.py` | Compile an .mq5 (or a folder) with MetaEditor and read its log; install SQX's `Sq*` indicators | imported | .mq5 → .ex5 + errors |
| `tester.py` | Write a tester ini, start the terminal detached, collect the report into `MT5_DATA/tests/<run>/` | imported | EA + window → report.htm, deals/trades.parquet |
| `report.py` | Parse the tester's HTML report: summary cells, the deal rows (found by shape, not by language), trades paired from in/out deals | imported | report.htm → summary, deals, trades |
| `compare.py` | Pair MT5 trades with SQX's (same side, nearest entry within a tolerance) and the figures of the gap | imported | two trade frames → pairs + figures |
| `live.py` | Run a verb of `winside/query.py` under the Windows Python; bars and ticks to Parquet | imported | verb → JSON / parquet |

`winside/` runs under the Windows Python inside the prefix, not under the project's Python.
