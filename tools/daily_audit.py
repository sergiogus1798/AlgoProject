#!/usr/bin/env python3
"""The half of the daily audit a machine can do alone. Judgement stays with the /audit agent."""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import manifest
from core.paths import AUDIT, DATA, MASTER, ROOT
from tools import audit_tests


def run(*command: str) -> tuple[int, str]:
    """Run one project command from the repository root.

    Args:
        command: Argument list, e.g. ("python3", "tools/checks.py").

    Returns:
        (exit code, combined output).
    """
    p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


WONT_FIX = {
    "Infinox_SP500ft_H4_HighPrecision"
}  # OPEN.md #3: the owner's decision, not a nightly finding


def corrupt_projects() -> list[str]:
    """Projects whose config.xml references task files their archive lacks.

    Returns:
        Project names that fail to render. This is the failure the GUI hides by
        dropping the project from its list without an error.
    """
    bad = []
    for d in sorted((MASTER / "user/projects").iterdir()):
        if d.name in WONT_FIX or not (d / "project.cfx").exists():
            continue
        code, _ = run(
            "python3", "-m", "sqx.inspect.dump_project", d.name, "-o", "/dev/null"
        )
        if code:
            bad.append(d.name)
    return bad


def exports_without_manifest() -> list[str]:
    """Export directories that cannot be reproduced.

    A partitioned export (`pnl/task=x/strategy=y/`) carries one manifest at its dated root, so a
    leaf is covered by a manifest in any folder above it, and a missing one is reported once per
    export (`raw/<project>/<databank>/<date>`), not once per partition.

    Returns:
        Exports under the data root holding data files but no manifest.json.
    """
    raw = DATA / "raw"
    missing = set()
    for d in raw.rglob("*"):
        if d.is_dir() and any(d.iterdir()) and not any(c.is_dir() for c in d.iterdir()):
            chain = [d, *d.parents[: len(d.relative_to(raw).parts) - 1]]
            if not any((p / "manifest.json").exists() for p in chain):
                missing.add(str(Path("raw", *d.relative_to(raw).parts[:3])))
    return sorted(missing)


def manifests_of_unknown_code() -> list[str]:
    """Exports whose manifest names code that cannot be found again.

    Returns:
        One `<export folder> (<code_version>)` per distinct `code_version` under the data root
        that is neither a commit of this repository ("-dirty" aside) nor `manifest.PRE_GIT`.
    """
    seen = {}
    for m in sorted((DATA / "raw").rglob("manifest.json")):
        seen.setdefault(
            json.loads(m.read_text(encoding="utf-8")).get("code_version", ""), m.parent
        )
    return [
        f"{d.relative_to(DATA)} ({v or 'no code_version'})"
        for v, d in seen.items()
        if v != manifest.PRE_GIT
        and run("git", "cat-file", "-e", v.removesuffix("-dirty") + "^{commit}")[0]
    ]


def undecided_assets() -> list[str]:
    """Assets a live project uses whose real spread or commission is still undecided.

    Returns:
        Asset names still carrying `use: null` in a required field.
    """
    sys.path.insert(0, str(ROOT))
    from core import assets

    out = []
    for symbol in assets.symbols():
        data = assets.load(symbol)
        if assets.pending(data) and data.get("projects_using_it"):
            out.append(symbol)
    return out


def dead_code() -> list[str]:
    """Vulture findings over the repo with `tools/vulture_whitelist.py` (reported, never deleted)."""
    got = subprocess.run(
        [
            sys.executable,
            "-m",
            "vulture",
            ".",
            "--min-confidence",
            "60",
            "--exclude",
            "scratch,tools/sqx-lab",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return [x for x in got.stdout.splitlines() if x]


def main() -> None:
    """Write today's mechanical audit and exit non-zero if anything regressed."""
    checks_code, checks_out = run("python3", "tools/checks.py")
    results, wall = audit_tests.run_all()
    tests_row, tests_failed = audit_tests.report(results, wall)
    # Stale = depmap changed the file just now. Uncommitted is not stale: the owner commits (rule 12),
    # so `git status` called it dirty every night between two of his commits.
    deps = ROOT / "docs/DEPENDENCIES.md"
    before = deps.read_bytes() if deps.exists() else b""
    depmap_code, _ = run("python3", "tools/depmap.py")
    dirty = deps.read_bytes() != before

    bad = corrupt_projects()
    no_manifest = exports_without_manifest()
    unknown_code = manifests_of_unknown_code()
    undecided = undecided_assets()
    dead = dead_code()

    lines = [
        f"# Mechanical audit {date.today().isoformat()}",
        "",
        "Written by `tools/daily_audit.py`. It checks only what a machine can check;",
        "documentation drift and statistical rigour need the `/audit` agent.",
        "",
        "| check | result |",
        "|---|---|",
        f"| `tools/checks.py` | {'ok' if not checks_code else 'FAILED'} |",
        tests_row[0],
        f"| `docs/DEPENDENCIES.md` | {'stale, regenerated' if dirty else 'current'} |",
        f"| projects that fail to render | {', '.join(bad) or 'none'} |",
        f"| exports without a manifest | {', '.join(no_manifest) or 'none'} |",
        f"| manifests naming unknown code | {', '.join(unknown_code) or 'none'} |",
        f"| assets in use, cost still undecided | {', '.join(undecided) or 'none'} |",
        f"| dead code (vulture, with the whitelist) | {len(dead) or 'none'} |",
    ]
    if checks_code:
        lines += ["", "## checks.py output", "", "```", checks_out, "```"]
    if dead:
        lines += ["", "## dead code (vulture)", "", "```", *dead[:50], "```"]
    lines += tests_row[1:]

    AUDIT.mkdir(parents=True, exist_ok=True)
    out = AUDIT / f"{date.today().isoformat()}-mechanical.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    sys.exit(
        1 if (checks_code or tests_failed or depmap_code or bad or no_manifest) else 0
    )


if __name__ == "__main__":
    main()
