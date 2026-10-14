"""Stop hook: ruff and the touched tests on the .py files THIS session edited; red blocks the stop.

The files come from the session's own transcript (the tree is shared, rule 12), never `git status`.
Any internal error lets the stop through, like guard.py.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def edited_files(transcript: Path) -> list[str]:
    """The existing repo .py files this transcript edited, in order, no repeats."""
    found: dict[str, None] = {}
    for line in transcript.read_text(errors="replace").splitlines():
        try:
            content = json.loads(line).get("message", {}).get("content")
        except (ValueError, AttributeError):
            continue
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict) or block.get("name") not in EDIT_TOOLS:
                continue
            path = Path((block.get("input") or {}).get("file_path", ""))
            if (
                path.suffix == ".py"
                and path.is_file()
                and path.resolve().is_relative_to(ROOT)
            ):
                found[str(path.resolve())] = None
    return list(found)


def run(cmd: list[str]) -> str:
    """'' when the command is green, else the last ~15 lines of its output."""
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=570)
    if out.returncode == 0:
        return ""
    return (
        "\n".join((out.stdout + out.stderr).strip().splitlines()[-15:])
        or f"exit {out.returncode}"
    )


def main() -> int:
    """Exit 0 always; on a red check print the block decision."""
    try:
        data = json.load(sys.stdin)
        if data.get("stop_hook_active"):
            return 0
        files = edited_files(Path(data["transcript_path"]))
        if not files:
            return 0
        failures = []
        for name, cmd in (
            (
                "ruff",
                [
                    "ruff",
                    "check",
                    "--config",
                    str(ROOT / "ruff.toml"),
                    "--no-cache",
                    *files,
                ],
            ),
            ("tests", [sys.executable, "tools/audit_tests.py", "--changed", *files]),
        ):
            if tail := run(cmd):
                failures.append(f"{name} en rojo:\n{tail}")
    except (
        OSError,
        ValueError,
        KeyError,
        subprocess.SubprocessError,
    ) as e:  # a hook bug must never block work
        print(f"stop_checks: skipped ({e!r})", file=sys.stderr)
        return 0
    if failures:
        reason = "\n\n".join(failures) + "\n\nArregla esto antes de terminar."
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


sys.exit(
    main()
)  # a hook, not a command: nothing imports this file, and it has no manual chapter
