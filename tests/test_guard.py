"""`.claude/hooks/guard.py` blocks what breaks rules 2, 4, 7 and 12 and nothing else.

Every command here is a STRING handed to the guard on stdin; none is ever run. The master's GUI
is a listener of this test's own (`GUARD_MASTER_PORT`), so port 5050 is never dialled.
"""

import json
import os
import socket
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.paths import MASTER  # noqa: E402

GUARD = ROOT / ".claude" / "hooks" / "guard.py"
M = str(MASTER)
HOME_M = str(Path("~") / MASTER.relative_to(Path.home()))
CFX = "/nowhere/SQX_w1/user/projects/Test_X/project.cfx"

BLOCKED = [
    # rule 12 — the forms the raw-text guard let through
    "git add -Av",
    "git add -u",
    "git add *",
    "git add :/",
    "git add -- .",
    "git add ./",
    "git -C . add -A",
    "git commit -am 'msg'",
    "git checkout some-branch",
    "git checkout -t origin/x",
    "git branch x",
    "git clone . ../x",
    "git -C . worktree add ../w",
    "git -c k=v switch main",
    # rule 12 — what it already blocked, and the shapes a command can hide in
    "git add -A",
    "git add --all",
    "git add .",
    "git status && git add .",
    "git worktree add x",
    "git switch -c x",
    "git checkout -b x",
    "git checkout --orphan x",
    "git branch -D x",
    "git branch -m old new",
    "git commit -a -m x",
    "git commit --all -m x",
    "git checkout file.py",
    "git status\ngit add -A",
    "echo $(git add -A)",
    "echo `git add -A`",
    'bash -c "git add -A"',
    "env X=1 git add -A",
    "/usr/bin/git add -A",
    "git status; git add -A; git status",
    "git status | cat; (git add .)",
    "if true; then git add -A; fi",
    'git add "$PWD"',
    "git add file.py && git commit -qam 'x'",
    "git add -A 'unbalanced",
    # rule 4 — a shell write to a project.cfx
    f"sed -i 's/a/b/' {CFX}",
    f"sed -i.bak -e 's/a/b/' {CFX}",
    f"perl -pi -e 's/a/b/' {CFX}",
    f"""python3 -c "open('{CFX}','w').write('x')" """,
    f"> {CFX}",
    f"echo x > {CFX}",
    f"echo x >> {CFX}",
    f"cp /tmp/a.cfx {CFX}",
    f"mv /tmp/a.cfx {CFX}",
    f"mv {CFX} /tmp/a.cfx",
    f"echo x | tee {CFX}",
    f"cat a | tee -a {CFX} >/dev/null",
    f"dd if=/tmp/a of={CFX}",
    f"python3 - <<'EOF'\nfrom pathlib import Path\nPath('{CFX}').write_text('x')\nEOF",
    f"cd /nowhere && cat > {CFX} <<EOF\n<Project/>\nEOF",
    # rule 2 — killing SQX by pattern
    "pkill -f StrategyQuantX",
    "pkill -f sqcli",
    "pkill -f java",
    "killall java",
    "killall -9 sqcli",
    "pgrep -f StrategyQuantX | xargs kill",
    "pgrep -f sqcli | xargs -r kill -9",
    "kill $(pgrep -f StrategyQuantX)",
    "kill -9 `pidof java`",
    'kill -TERM "$(pgrep -x sqcli)"',
    "PID=$(pgrep -f sqcli); kill $PID",
    "ps aux | grep sqcli | awk '{print $2}' | xargs kill",
    "for p in $(pgrep -f java); do kill $p; done",
]

PASS = [
    # the false positives of the raw-text guard: a quoted string is data, not a command
    'grep -rn "git worktree" .',
    'git log --grep="git add -A"',
    "git worktree list",
    'git commit -m "docs: never git switch, never git add -A, never git checkout -b"',
    "git commit -m 'guard: block git add . and pkill -f StrategyQuantX'",
    "grep -rn 'pkill -f StrategyQuantX' knowhow/",
    'echo "do not run git add -A"',
    f"grep -n sqcli {M}/user/log/today.log",
    f"tail -n 20 {M}/user/log/sqcli.log",
    f"cat {HOME_M}/sqcli.config",
    f'echo "the master is {M}, its cli is sqcli"',
    f"ls -lt {M}/user/projects | head",
    "grep -rn '`git add -A`' CLAUDE.md",
    # the master's neighbours are not the master
    f"{M}_w1/sqcli -project action=status",
    f"cd {M}_w2 && ./sqcli -project action=status",
    f"cd {HOME_M}_w1; ./sqcli -run",
    f"cd {M} && {M}_w1/sqcli -project action=status",
    # everyday commands
    "python3 -m core.assets XAUUSD",
    "python3 tools/checks.py",
    "python3 tools/depmap.py && python3 tools/checks.py",
    "python3 -m pytest tests/test_guard.py -q",
    "bin/sqx-worker.sh --role conductor start",
    "bin/sqx-worker.sh --role custodian stop",
    ".claude/skills/sqx-wait/wait.sh SQX_w2",
    ".claude/skills/sqx-wait/preflight.sh",
    "git status",
    "git status --short",
    "git diff --stat",
    "git diff HEAD -- core/paths.py",
    "git log --oneline -5",
    "git show HEAD:CLAUDE.md | head -20",
    "git add path/to/file.py",
    "git add core/paths.py tests/test_guard.py",
    "git add -- docs/manual/01-empezar.pdf",
    "git add docs/",
    "git checkout -- file.py",
    "git checkout HEAD~1 -- core/paths.py",
    "git branch",
    "git branch -a",
    "git branch -r",
    "git branch -vv",
    "git branch --show-current",
    "git branch --list 'ma*'",
    "git commit -m 'checks: fix'",
    "git commit --amend --no-edit",
    "git commit -m 'x' -- core/paths.py",
    "git push",
    "git push origin master",
    "git stash list",
    "git -C . status",
    "git --no-pager log -3",
    "git rev-parse --abbrev-ref HEAD",
    "git ls-files | wc -l",
    "ls",
    "ls -la ~/Desktop/AlgoData | head",
    "grep -rh '^q:' knowhow/eng/",
    "find . -name '*.py' | wc -l",
    "curl -s 'http://127.0.0.1:5060/api?cmd=-project action=status'",
    "kill 12345",
    "kill -9 12345 2>/dev/null",
    "kill -TERM 123 456",
    "pgrep -f sqcli",
    "pgrep -x 'sqcli|StrategyQuantX'",
    "ps aux | grep sqcli | grep -v grep",
    "pgrep -f wait.sh | xargs kill",
    "kill $WAITER",
    "cat OPEN.md | head -40",
    "wc -l core/*.py",
    "mkdir -p scratch/x && cd scratch/x && ls",
    "ruff check . 2>&1 | tail -5",
    "graphify explain 'core/paths.py::MASTER'",
    "python3 - <<'EOF'\nprint('git add -A is forbidden; so is it's cousin')\nEOF",
    "git commit -m \"$(cat <<'EOF'\nguard: 1) never git add -A (it's rule 12)\n\ngit switch x\nEOF\n)\"",
    "find . \\( -name '*.csv' -o -name '*.pkl' \\) -print | head",
    "awk '/^---/{n++} n>=1' f | cut -c1-220",
    "for f in a b; do echo $f; done",
    "echo 'a;b' | tr ';' '\\n' # git add -A",
    'true && echo "it\'s fine"',
    # project.cfx read, named or archived — never written
    "python3 - <<'EOF'\ns = open('R.md').read()\nopen('R.md', 'w').write(s + 'see `project.cfx`, never edited')\nEOF",
    f"cat {CFX}",
    f"grep -c Task {CFX}",
    f"sed -n 1,5p {CFX}",
    f"cp {CFX} /nowhere/archive/Test_X.cfx",
    f"python3 -m sqx.projects.spp XAUUSD --cfx {CFX} --input Results",
    f"""python3 -c "print(open('{CFX}').read()[:200])" """,
    f"python3 sqx/inspect/dump_project.py {CFX} > /tmp/d.txt",
]

MASTER_CLI = [  # blocked while the master's GUI listens, let through when it does not
    f"{M}/sqcli -project action=status",
    f"{HOME_M}/sqcli -run",
    f"cd {HOME_M}; ./sqcli -run",
    f"cd {M} && ./sqcli -project action=status",
    f'bash -c "cd {M} && ./sqcli -run"',
    f"cd {HOME_M}/user && ../sqcli -run",
    f'nohup "{M}/sqcli" -run &',
    f"{M}_w1/sqcli -import {M}/user/x.sqx",
]

TOOLS = [  # (tool, tool_input, blocked)
    ("Agent", {"prompt": "x", "isolation": "worktree"}, True),
    ("Task", {"isolation": "worktree"}, True),
    ("EnterWorktree", {}, True),
    ("EnterWorktree", {"name": "x"}, True),
    ("Agent", {"prompt": "x"}, False),
    ("Agent", {"prompt": "x", "isolation": "remote"}, False),
    ("Edit", {"file_path": CFX}, True),
    ("Write", {"file_path": "/anywhere/project.cfx"}, True),
    ("MultiEdit", {"file_path": CFX}, True),
    ("Write", {"file_path": str(ROOT / "core" / "x.csv")}, True),
    ("Write", {"file_path": str(ROOT / "studies" / "x.parquet")}, True),
    ("Edit", {"file_path": str(ROOT / "core" / "x.csv")}, True),
    ("Write", {"file_path": str(ROOT / "core" / "x.npy")}, True),
    ("Write", {"file_path": str(ROOT / "core" / "x.pkl")}, True),
    ("Write", {"file_path": str(ROOT / "scratch" / "x.csv")}, False),
    ("Write", {"file_path": str(ROOT / "tests" / "fixtures" / "x.csv")}, False),
    ("Write", {"file_path": "/nowhere/AlgoData/x.parquet"}, False),
    ("Write", {"file_path": str(ROOT / "core" / "x.py")}, False),
    ("Edit", {"file_path": str(ROOT / "CLAUDE.md")}, False),
    ("Read", {"file_path": CFX}, False),
    ("ExitWorktree", {}, False),
    ("Bash", {}, False),
    ("Bash", None, False),
]


def guard(stdin: str, port: int) -> int:
    """The guard's exit code for one hook event, the master's port pointed at `port`."""
    done = subprocess.run(
        [sys.executable, str(GUARD)],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=ROOT,
        env={**os.environ, "GUARD_MASTER_PORT": str(port)},
    )
    if done.returncode == 2 and not done.stderr.startswith(
        "BLOCKED by .claude/hooks/guard.py — rule "
    ):
        return -1
    return done.returncode


def event(tool: str, tool_input: dict | None) -> str:
    """The JSON Claude Code hands a PreToolUse hook."""
    return json.dumps({"tool_name": tool, "tool_input": tool_input, "cwd": str(ROOT)})


def failures() -> tuple[list[str], int]:
    """Every case whose exit code is not the expected one, and how many cases there are."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(64)
    up = listener.getsockname()[1]
    spare = socket.socket()
    spare.bind(("127.0.0.1", 0))
    down = spare.getsockname()[1]  # bound and never listening: connections are refused
    bash = [(c, down, 2) for c in BLOCKED] + [(c, up, 0) for c in PASS]
    bash += [(c, up, 2) for c in MASTER_CLI] + [(c, down, 0) for c in MASTER_CLI]
    cases = [
        (
            f"Bash: {c!r} (master {'up' if p == up else 'down'})",
            event("Bash", {"command": c}),
            p,
            want,
        )
        for c, p, want in bash
    ]
    cases += [
        (f"{t}: {i}", event(t, i), down, 2 if blocked else 0) for t, i, blocked in TOOLS
    ]
    cases += [
        ("malformed JSON", "not json {", up, 0),
        ("empty stdin", "", up, 0),
        ("a JSON list", "[1]", up, 0),
    ]
    with ThreadPoolExecutor(8) as pool:
        got = list(pool.map(lambda case: guard(case[1], case[2]), cases))
    listener.close()
    spare.close()
    return [
        f"{label}: exit {code}, expected {want}"
        for (label, _, _, want), code in zip(cases, got)
        if code != want
    ], len(cases)


def test_guard() -> None:
    """Every bypass is blocked, every false positive and everyday command passes."""
    wrong, _ = failures()
    assert not wrong, "\n".join(wrong)


def main() -> None:
    """Print what failed, or the count that passed."""
    wrong, n = failures()
    print("\n".join(wrong) or f"ok: {n} hook events judged as expected, none executed")
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
