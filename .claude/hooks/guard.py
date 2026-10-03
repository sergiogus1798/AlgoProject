"""PreToolUse guard: turns the mechanical HARD RULES of CLAUDE.md into blocks.

Reads the hook's JSON on stdin; exit 2 with the reason on stderr blocks the call, exit 0 lets it
through. A bug in here must never block work, so any exception lets the call through, and a shell
line the parser cannot read falls back to the raw-text checks of `legacy`.
Facts and tests: knowhow/eng/claude-hooks-guard.md, tests/test_guard.py.
"""
import json
import os
import re
import socket
import sys
from pathlib import Path

from gitrule import git
from shellwords import commands

ROOT = Path(__file__).resolve().parent.parent.parent
# The master's GUI API; not in machine.yaml because nothing else dials it. The variable is for
# tests/test_guard.py, which points it at a listener of its own and never dials the real one.
MASTER_PORT = int(os.environ.get("GUARD_MASTER_PORT", 5050))
DATA = {".csv", ".parquet", ".pkl", ".feather", ".h5", ".npy", ".npz"}
SQX_PROCESS = re.compile(r"StrategyQuant|sqcli|java", re.I)
INPLACE = re.compile(r"--in-place.*|-[a-zA-Z]*i.*")
COPIERS = {"cp", "mv", "install", "rsync", "ln"}
INTERPRETERS = ("python", "perl", "ruby", "node")
WRITES = re.compile(r"open\([^)]*['\"](?:[wax]b?\+?|r\+b?|rb\+)['\"]|write_text|write_bytes"
                    r"|\.write\(|writeFile|shutil\.(?:copy|move)|os\.(?:replace|rename|remove|unlink)"
                    r"|\.(?:rename|unlink)\(")
CFX_PATH = re.compile(r"project\.cfx['\"]")     # a path literal in the code, not a word in a text
KILL = "rule 2: never kill SQX by pattern (it matches your own shell) — kill by numeric PID"
CFX = "rule 4: SQX rewrites project.cfx on save and exit — use the `-project` API on the worker"
MASTER_UP = ("rule 2: the master's GUI is up (port 5050) — use the conductor, "
             "`bin/sqx-worker.sh --role conductor`")
LEGACY_GIT = [
    (r"\bgit\s+worktree\b", "rule 12: one folder — never `git worktree`"),
    (r"\bgit\s+switch\b", "rule 12: one branch — never switch branches"),
    (r"\bgit\s+checkout\s+(-[bB]|--orphan)\b", "rule 12: one branch — never create a branch"),
    (r"\bgit\s+add\s+(-A\b|--all\b|\.(\s|$|;|&))",
     "rule 12: stage only this task's files by name — never `git add -A` / `git add .`"),
]


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


def _names_master(text: str) -> bool:
    """Whether the text names the master install, absolute or home-relative."""
    master = _master()
    forms = {str(master)}
    try:
        rel = master.relative_to(Path.home())
        forms |= {f"{home}/{rel}" for home in ("~", "$HOME", "${HOME}")}
    except ValueError:
        pass
    # `SQX` but never `SQX_w1`: the path must end at a separator, a quote, an operator or the end.
    return any(re.search(re.escape(f) + r"(?=[/\s'\";&|)]|$)", text) for f in forms)


def _at(cwd: str, word: str) -> Path:
    """Where a path word points from a directory, `~` and `$HOME` expanded, no disk access."""
    return Path(os.path.normpath(os.path.join(cwd, os.path.expanduser(os.path.expandvars(word)))))


def _is_cfx(word: str) -> bool:
    """Whether a shell word is a path to a project.cfx."""
    return Path(word).name == "project.cfx"


def _master_cli(cmds: list, cwd: str) -> bool:
    """Whether a command runs `sqcli` from the master, or on it, following each `cd` on the way."""
    if not any(Path(words[0]).name == "sqcli" for words, _ in cmds):
        return False
    master = _master()
    for words, _ in cmds:
        name = Path(words[0]).name
        if name in ("cd", "pushd") and len(words) > 1:
            cwd = str(_at(cwd, words[-1]))
        elif name == "sqcli" and (master in _at(cwd, words[0]).parents
                                  or any(_names_master(a) for a in words[1:])):
            return True
    return False


def _kills_by_pattern(cmds: list) -> bool:
    """pkill/killall on an SQX process name, or a `kill` fed by a search for one."""
    names = [Path(words[0]).name for words, _ in cmds]
    naming = {name for name, (words, _) in zip(names, cmds)
              if any(SQX_PROCESS.search(a) for a in words[1:])}
    hunts = bool({"pgrep", "pidof"} & naming) or (
        "ps" in names and bool({"grep", "egrep", "awk"} & naming))
    for name, (words, _) in zip(names, cmds):
        targets = [a for a in words[1:] if not a.startswith("-") and not a.isupper()]
        if name in ("pkill", "killall") and name in naming:
            return True
        if name == "kill" and hunts and not (targets and all(t.isdigit() for t in targets)):
            return True
    return False


def _writes_cfx(words: list[str], writes: list[str], cwd: str) -> bool:
    """Whether one shell command writes a project.cfx: a redirection, a write verb, inline code."""
    name, args = Path(words[0]).name, words[1:]
    named = [a for a in args if _is_cfx(a)]
    if any(_is_cfx(t) for t in writes):
        return True
    if name in ("tee", "truncate") or (name in ("sed", "perl") and any(map(INPLACE.fullmatch, args))):
        return bool(named)
    if name == "dd":
        return any(a.startswith("of=") and _is_cfx(a[3:]) for a in args)
    if name in COPIERS:
        paths = [a for a in args if not a.startswith("-")]
        # into a folder that already holds one is an overwrite; `mv` of one takes it away
        return bool(paths) and (_is_cfx(paths[-1]) or (bool(named) and (
            name == "mv" or (_at(cwd, paths[-1]) / "project.cfx").exists())))
    if name.startswith(INTERPRETERS):
        return any(CFX_PATH.search(a) and WRITES.search(a) for a in args)
    return False


def legacy(cmd: str) -> str | None:
    """The raw-text checks, for a line the parser cannot read (an unbalanced quote)."""
    if re.search(r"\b(pkill|killall)\b", cmd) and "StrategyQuant" in cmd:
        return KILL
    for pattern, why in LEGACY_GIT:
        if re.search(pattern, cmd):
            return why
    if "sqcli" in cmd and _names_master(cmd) and _listening(MASTER_PORT):
        return MASTER_UP
    return None


def parsed(cmd: str, cwd: str) -> str | None:
    """The rule a shell line breaks, judged on the commands it runs and not on its text."""
    cmds = commands(cmd)
    if _kills_by_pattern(cmds):
        return KILL
    for words, writes in cmds:
        why = git(words, str(ROOT)) if Path(words[0]).name == "git" else None
        if why or _writes_cfx(words, writes, cwd):
            return why or CFX
    if _master_cli(cmds, cwd) and _listening(MASTER_PORT):
        return MASTER_UP
    return None


def bash(cmd: str, cwd: str) -> str | None:
    """The rule a shell command breaks, or None."""
    try:
        return parsed(cmd, cwd)
    except Exception:
        return legacy(cmd)


def write(path: str) -> str | None:
    """The rule an edit or write to this path breaks, or None."""
    p = Path(path)
    if p.name == "project.cfx":
        return CFX
    if p.suffix in DATA:
        try:
            rel = p.resolve().relative_to(ROOT)
        except ValueError:
            return None
        if rel.parts[0] not in ("scratch", "tests"):
            return "rule 7: heavy data goes to the data root (core.paths.DATA), never the repo"
    return None


def decide(event: dict) -> str | None:
    """The rule one tool call breaks, or None."""
    tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
    if tool == "Bash":
        return bash(args.get("command", ""), event.get("cwd") or os.getcwd())
    if tool in ("Edit", "Write", "MultiEdit"):
        return write(args.get("file_path", ""))
    if tool == "EnterWorktree" or args.get("isolation") == "worktree":
        return "rule 12: one folder — never a worktree (`isolation: \"worktree\"`, EnterWorktree)"
    return None


def main() -> None:
    """Read the hook's event, and exit 2 with the reason when a rule blocks it."""
    try:
        reason = decide(json.load(sys.stdin))
    except Exception:
        reason = None
    if reason:
        print(f"BLOCKED by .claude/hooks/guard.py — {reason}", file=sys.stderr)
        sys.exit(2)


main()   # a hook, not a command: nothing imports this file, and it has no manual chapter
