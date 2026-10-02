"""Call a read-only tool of the running MT5 terminal's own MCP server over HTTP, from Python."""
import json
import os
import urllib.request
from pathlib import Path

from core.paths import ROOT

# Where Claude Code keeps the server's address and token (local scope, written by `claude mcp add`).
CLAUDE_JSON = Path.home() / ".claude.json"
SERVER = "metatrader5"


def endpoint() -> dict:
    """{url, headers} of the terminal's MCP: $MT5_MCP_URL / $MT5_MCP_TOKEN, else Claude Code's entry."""
    if os.environ.get("MT5_MCP_URL"):
        return {"url": os.environ["MT5_MCP_URL"],
                "headers": {"Authorization": f"Bearer {os.environ['MT5_MCP_TOKEN']}"}}
    return json.loads(CLAUDE_JSON.read_text())["projects"][str(ROOT)]["mcpServers"][SERVER]


def _post(cfg: dict, body: dict, session: str | None) -> tuple[str | None, dict | None]:
    """One JSON-RPC message; returns the session id the server names and its decoded answer."""
    headers = {**cfg["headers"], "Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if session:
        headers["Mcp-Session-Id"] = session
    request = urllib.request.Request(cfg["url"], json.dumps(body).encode(), headers)
    with urllib.request.urlopen(request, timeout=600) as r:
        raw = r.read()
        return r.headers.get("Mcp-Session-Id"), json.loads(raw) if raw.strip() else None


def session() -> dict:
    """Open an MCP session with the terminal (it must be running); pass the result to call()."""
    cfg = endpoint()
    sid, _ = _post(cfg, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "algoproject-newsfilter", "version": "1"}}}, None)
    _post(cfg, {"jsonrpc": "2.0", "method": "notifications/initialized"}, sid)
    return {"cfg": cfg, "sid": sid}


def call(s: dict, tool: str, args: dict) -> dict:
    """The JSON a tool answers with.

    Args:
        s: What session() returned.
        tool: One of the terminal's read-only tools, e.g. economic_calendar_list_values.
        args: Its arguments, as the tool's schema names them.
    """
    _, answer = _post(s["cfg"], {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                 "params": {"name": tool, "arguments": args}}, s["sid"])
    return json.loads(answer["result"]["content"][0]["text"])
