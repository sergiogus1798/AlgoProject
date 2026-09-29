"""PreToolUse guard: turns the mechanical HARD RULES of CLAUDE.md into blocks.

Reads the hook's JSON on stdin; exit 2 with the reason on stderr blocks the call, exit 0 lets it
through. A bug in here must never block work, so any exception lets the call through.
Facts and tests: knowhow/eng/claude-hooks-guard.md.
"""
import json
import re
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MASTER_PORT = 5050   # the master's GUI API; not in machine.yaml because nothing else dials it


def _master() -> Path:
    """The master install, from core.paths — the only place that knows where it lives."""
    sys.path.insert(0, str(ROOT))
    from core.paths import MASTER
    return MASTER


def _listening(port: int) -> bool:
    """Whether something accepts connections on this loopback port."""
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.3):
            return True
    except OSError:
        return False


def _names_master(cmd: str) -> bool:
    """Whether the command names the master install, absolute or home-relative."""
    master = _master()
    forms = {str(master)}
    try:
        rel = master.relative_to(Path.home())
        forms |= {f"{home}/{rel}" for home in ("~", "$HOME", "${HOME}")}
    except ValueError:
        pass
    # `SQX` but never `SQX_w1`: the path must end at a separator, a quote or the end.
    return any(re.search(re.escape(f) + r"(?=[/\s'\"]|$)", cmd) for f in forms)


GIT = [
    (r"\bgit\s+worktree\b", "rule 12: one folder — never `git worktree`"),
    (r"\bgit\s+switch\b", "rule 12: one branch — never switch branches"),
    (r"\bgit\s+checkout\s+(-[bB]|--orphan)\b", "rule 12: one branch — never create a branch"),
    (r"\bgit\s+add\s+(-A\b|--all\b|\.(\s|$|;|&))",
     "rule 12: stage only this task's files by name — never `git add -A` / `git add .`"),
]


def bash(cmd: str) -> str | None:
    """The rule a shell command breaks, or None."""
    if re.search(r"\b(pkill|killall)\b", cmd) and "StrategyQuant" in cmd:
        return "rule 2: the pattern matches your own shell — kill SQX by PID"
    for pattern, why in GIT:
        if re.search(pattern, cmd):
            return why
    if "sqcli" in cmd and _names_master(cmd) and _listening(MASTER_PORT):
        return ("rule 2: the master's GUI is up (port 5050) — use the conductor, "
                "`bin/sqx-worker.sh --role conductor`")
    return None


def write(tool: str, path: str) -> str | None:
    """The rule an edit or write to this path breaks, or None."""
    p = Path(path)
    if p.name == "project.cfx":
        return ("rule 4: SQX rewrites project.cfx on save and exit — use the `-project` API "
                "on the worker")
    if tool == "Write" and p.suffix in (".csv", ".parquet"):
        try:
            rel = p.resolve().relative_to(ROOT)
        except ValueError:
            return None
        if rel.parts[0] not in ("scratch", "tests"):
            return "rule 7: heavy data goes to the data root (core.paths.DATA), never the repo"
    return None


try:
    event = json.load(sys.stdin)
    tool = event.get("tool_name", "")
    args = event.get("tool_input") or {}
    if tool == "Bash":
        reason = bash(args.get("command", ""))
    elif tool in ("Edit", "Write", "MultiEdit"):
        reason = write(tool, args.get("file_path", ""))
    else:
        reason = None
except Exception:
    reason = None

if reason:
    print(f"BLOCKED by .claude/hooks/guard.py — {reason}", file=sys.stderr)
    sys.exit(2)
