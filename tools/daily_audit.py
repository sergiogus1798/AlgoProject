#!/usr/bin/env python3
"""The half of the daily audit a machine can do alone. Judgement stays with the /audit agent."""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import ASSETS, DATA, MASTER, ROOT


def run(*command: str) -> tuple[int, str]:
    """Run one project command from the repository root.

    Args:
        command: Argument list, e.g. ("python3", "tools/checks.py").

    Returns:
        (exit code, combined output).
    """
    p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def corrupt_projects() -> list[str]:
    """Projects whose config.xml references task files their archive lacks.

    Returns:
        Project names that fail to render. This is the failure the GUI hides by
        dropping the project from its list without an error.
    """
    bad = []
    for d in sorted((MASTER / "user/projects").iterdir()):
        if not (d / "project.cfx").exists():
            continue
        code, _ = run("python3", "1_sqx/inspect/dump_project.py", d.name, "-o", "/dev/null")
        if code:
            bad.append(d.name)
    return bad


def exports_without_manifest() -> list[str]:
    """Export directories that cannot be reproduced.

    Returns:
        Paths under the data root holding data files but no manifest.json.
    """
    missing = []
    for d in (DATA / "raw").rglob("*"):
        if d.is_dir() and any(d.iterdir()) and not any(c.is_dir() for c in d.iterdir()):
            if not (d.parent / "manifest.json").exists() and not (d / "manifest.json").exists():
                missing.append(str(d.relative_to(DATA)))
    return missing


def undecided_assets() -> list[str]:
    """Assets a live project uses whose real spread or commission is still undecided.

    Returns:
        Asset names still carrying `use: null` in a required field.
    """
    sys.path.insert(0, str(ROOT))
    from core import assets
    out = []
    for f in sorted(ASSETS.glob("*.yaml")):
        data = assets.load(f.stem)
        if assets.pending(data) and data.get("projects_using_it"):
            out.append(f.stem)
    return out


def main() -> None:
    """Write today's mechanical audit and exit non-zero if anything regressed."""
    checks_code, checks_out = run("python3", "tools/checks.py")
    tests_code, tests_out = run("python3", "tests/test_cfx.py")
    depmap_code, _ = run("python3", "tools/depmap.py")
    dirty = run("git", "status", "--porcelain", "docs/DEPENDENCIES.md")[1]

    bad = corrupt_projects()
    no_manifest = exports_without_manifest()
    undecided = undecided_assets()

    lines = [f"# Mechanical audit {date.today().isoformat()}", "",
             "Written by `tools/daily_audit.py`. It checks only what a machine can check;",
             "documentation drift and statistical rigour need the `/audit` agent.", "",
             "| check | result |", "|---|---|",
             f"| `tools/checks.py` | {'ok' if not checks_code else 'FAILED'} |",
             f"| `tests/test_cfx.py` | {'ok' if not tests_code else 'FAILED'} |",
             f"| `docs/DEPENDENCIES.md` | {'stale, regenerated' if dirty else 'current'} |",
             f"| projects that fail to render | {', '.join(bad) or 'none'} |",
             f"| exports without a manifest | {', '.join(no_manifest) or 'none'} |",
             f"| assets in use, cost still undecided | {', '.join(undecided) or 'none'} |"]
    if checks_code:
        lines += ["", "## checks.py output", "", "```", checks_out, "```"]
    if tests_code:
        lines += ["", "## test output", "", "```", tests_out, "```"]

    out = ROOT / "audit" / f"{date.today().isoformat()}-mechanical.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    sys.exit(1 if (checks_code or tests_code or depmap_code or bad or no_manifest) else 0)


if __name__ == "__main__":
    main()
