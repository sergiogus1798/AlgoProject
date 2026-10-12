---
q: Does SQX's built-in MCP server answer on a worker, and is it worth registering in Claude Code?
kw: mcp, mcpx, /mcp endpoint, Unable to resolve the request mcp, Mcp-Session-Id, StrategyQuant X MCP integration, list_projects list_strategies get_strategy_stats run_project stop_project, HTTP transport, Remote Access port, sqcli vs GUI mode
tag: 🔬  date: 2026-10-12  see: live-chain-without-restart
---
# SQX's MCP server exists only in GUI mode, on the worker's own port — and adds nothing the live session lacks
`http://localhost:<port>/mcp` (HTTP transport, the Remote Access port: 5060 on the conductor)
answers only when SQX runs in GUI mode — what `sqx.projects.live.start` opens. Under `sqcli` the
same URL returns «Unable to resolve the request mcp». It is not registered in Claude Code, on
purpose: it is alive only while a live session is, its six tools (`list_projects`,
`list_strategies`, `list_databanks`, `get_strategy_stats`, `run_project`, `stop_project`) are what
`live.call` / `live.run` / `live.records` already do, and a `run_project` from it would start a
task past the owner lock and `.claude/hooks/guard.py` (root rules 3 and 18).

## Evidence
- 🔬 conductor, 2026-10-12, sqcli mode: `POST /mcp` → «Unable to resolve the request mcp».
- 🔬 same day, GUI mode (`live.start("conductor")`): `initialize` → 200, header `Mcp-Session-Id`,
  `serverInfo {"name":"StrategyQuant X","version":"1.0.0"}`, capabilities `tools`, `logging`.
- 🔬 custodian, 2026-10-12, GUI mode: `initialize`, then `notifications/initialized` (202) and
  `tools/list` with the `Mcp-Session-Id` header → exactly `list_projects`, `list_databanks`,
  `list_strategies`, `get_strategy_stats`, `run_project`, `stop_project`. Without the header
  `tools/list` is a 400.
