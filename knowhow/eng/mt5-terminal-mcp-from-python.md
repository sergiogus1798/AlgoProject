---
q: call the MetaTrader 5 MCP server from Python, metatrader5 MCP HTTP 127.0.0.1, MCP session is not initialized, export economic calendar without an MQL5 script, bulk data from the terminal MCP without spending tokens, Mcp-Session-Id
tag: 🔬  date: 2026-10-02  see: eng/mt5-calendar-history-clock, eng/mt5-tester-unattended
---
# The terminal's own MCP is plain HTTP on localhost — Python can call its read-only tools in bulk, with a session
- The `metatrader5` MCP (MetaQuotes, inside the running terminal) listens on `http://127.0.0.1:<port>/mcp` with a bearer token; Claude Code keeps both in `~/.claude.json` → `projects[<repo>].mcpServers.metatrader5`. `mt5.newsfilter.terminal` reads them from there (or `$MT5_MCP_URL`/`$MT5_MCP_TOKEN`).
- A bare `tools/call` answers `MCP session is not initialized`: POST `initialize`, keep the `Mcp-Session-Id` response header, POST `notifications/initialized`, then send that header on every call.
- This is how 20 years of calendar (216,713 releases) leave the terminal in 20 s without an MQL5 script (script and EA tools are denied here) and without passing through a model's context. `limit` takes 1,000,000; `truncated` says if it cut.
- The server dies with the terminal: every session's `metatrader5` tools go away while a tester run holds it closed, and come back when it is reopened.

## Evidence
2026-10-02, build 6231: `initialize` → header `Mcp-Session-Id`, `protocolVersion 2025-06-18`; `economic_calendar_list_values` for one month 0.12 s, 422 kB. `python3 -m mt5.newsfilter.history` 21 s end to end.
