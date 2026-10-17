#!/usr/bin/env python3
"""Apply the night's commit proposal: per group `git add -- paths` + `git commit -- paths`, then one push. No model.

The proposal (AlgoData/audit/<date>-commit.json) is written by bin/nightly-commit-proposal.sh; the
commit stays the owner's decision (hard rule 12), so this runs only after his «sí». `--facts` prints
the git state with each file's age, which is what the proposing agent reads.
"""

import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import proc
from core.paths import AUDIT

PUSH = ["git", "-c", "credential.helper=!gh auth git-credential", "push", "origin"]
NEVER = ("config/machine.yaml",)
NEVER_SUFFIX = (".csv", ".parquet", ".sqx", ".db")


def git(repo: Path, *args: str) -> str:
    """Run git in `repo` and return stdout; a failure raises with git's own message."""
    got = proc.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if got.returncode:
        raise SystemExit(f"git {' '.join(args[:2])}: {got.stderr.strip()}")
    return got.stdout


def status(repo: Path) -> dict[str, str]:
    """Path -> two-letter porcelain code of everything not committed (untracked files listed one by one)."""
    out = git(repo, "status", "--porcelain", "-uall", "--no-renames", "-z")
    return {e[3:]: e[:2] for e in out.split("\0") if e}


def mtime(repo: Path, path: str) -> float:
    """Modification time of a file, 0 when it was deleted."""
    p = repo / path
    return p.stat().st_mtime if p.exists() else 0.0


def facts(repo: Path) -> str:
    """One line per uncommitted path: code, age in minutes, size in KB, path."""
    now = time.time()
    rows = []
    for path, code in sorted(status(repo).items()):
        p = repo / path
        age = f"{(now - p.stat().st_mtime) / 60:.0f}" if p.exists() else "-"
        kb = f"{p.stat().st_size / 1024:.0f}" if p.exists() else "-"
        rows.append(f"{code}\t{age}\t{kb}\t{path}")
    return "code\tage_min\tsize_kb\tpath\n" + "\n".join(rows)


def load(file: Path) -> dict[str, Any]:
    """The proposal as {"groups": [...], ...}; a bare list of groups is accepted too."""
    data = json.loads(file.read_text(encoding="utf-8"))
    return {"groups": data} if isinstance(data, list) else data


def check(
    group: dict, current: dict[str, str], repo: Path, since: float
) -> tuple[list[str], list[str]]:
    """The group's paths that left `git status` and the ones modified after the proposal."""
    gone = [p for p in group["paths"] if p not in current]
    changed = [p for p in group["paths"] if p in current and mtime(repo, p) > since]
    return gone, changed


def forbidden(group: dict) -> list[str]:
    """Paths a commit must never carry: the machine's config and data files (the /sync skill's stops)."""
    return [
        p
        for p in group["paths"]
        if p in NEVER
        or (p.endswith(NEVER_SUFFIX) and not p.startswith("tests/fixtures/"))
    ]


def commit(repo: Path, group: dict, trailer: str) -> str:
    """Stage exactly the group's paths and commit only them; returns the short hash."""
    paths = group["paths"]
    git(repo, "add", "--", *paths)
    msg = ["-m", group["message"]]
    msg += ["-m", group["body"]] if group.get("body") else []
    msg += ["-m", trailer] if trailer else []
    git(repo, "commit", *msg, "--", *paths)
    return git(repo, "rev-parse", "--short", "HEAD").strip()


def apply(
    file: Path,
    repo: Path,
    *,
    dry: bool = False,
    only: set[int] | None = None,
    push: bool = True,
    force: bool = False,
    max_age_h: float = 12,
    trailer: str = "",
) -> int:
    """Apply a proposal; prints the Spanish summary and returns the exit code (2 = refused)."""
    since = file.stat().st_mtime
    age_h = (time.time() - since) / 3600
    if age_h > max_age_h and not force:
        print(
            f"RECHAZADA: la propuesta tiene {age_h:.1f} h (límite {max_age_h:g} h) y el árbol se mueve. "
            "Pide una nueva, o usa --force si sabes que no ha cambiado nada."
        )
        return 2
    proposal = load(file)
    done, skipped = [], []
    for n, group in enumerate(proposal["groups"], 1):
        if only and n not in only:
            continue
        head = f"[{n}] {group['message']} ({len(group['paths'])} ficheros)"
        current = status(repo)
        gone, changed = check(group, current, repo, since)
        bad = forbidden(group)
        if bad:
            skipped.append(f"{head}: lleva ficheros prohibidos {bad}")
        elif (gone or changed) and not force:
            why = (f"ya no están en git status {gone} " if gone else "") + (
                f"modificados tras la propuesta {changed}" if changed else ""
            )
            skipped.append(f"{head}: {why.strip()}")
        else:
            group = {**group, "paths": [p for p in group["paths"] if p in current]}
            if not group["paths"]:
                skipped.append(f"{head}: ya estaba commiteado")
            elif dry:
                done.append(
                    f"{head}: haría `git add` + `git commit` de {len(group['paths'])} ficheros"
                )
            else:
                done.append(f"{head}: commit {commit(repo, group, trailer)}")
    pushed = ""
    if done and push and not dry:
        branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip()
        env = {
            **os.environ,
            "PATH": f"{Path.home() / '.local/bin'}:{os.environ['PATH']}",
        }
        got = proc.run(
            [*PUSH, branch],
            cwd=repo,
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=300,
        )
        pushed = (
            "push hecho" if got.returncode == 0 else f"PUSH FALLÓ: {got.stderr.strip()}"
        )
    elif done:
        pushed = "sin push (dry-run o --no-push)"
    print(
        f"{'DRY-RUN — ' if dry else ''}Propuesta de {proposal.get('date', file.name)}"
    )
    print("Commits:" if not dry else "Haría:", *(done or ["ninguno"]), sep="\n  ")
    print("Saltados:", *(skipped or ["ninguno"]), sep="\n  ")
    print(f"{pushed}\n" if pushed else "", end="")
    print(
        f"Sigue sin commitear: {len(status(repo))} ficheros "
        f"(en curso según la propuesta: {len(proposal.get('en_curso', []))})."
    )
    return 0


def main() -> None:
    """Parse the flags and apply the proposal of the given day (default today)."""
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument(
        "day", nargs="?", default=str(date.today()), help="YYYY-MM-DD of the proposal"
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print what would be done, change nothing",
    )
    ap.add_argument("--only", help="comma-separated group numbers, e.g. 1,3")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument(
        "--force",
        action="store_true",
        help="apply a stale proposal and groups whose files moved",
    )
    ap.add_argument("--max-age-hours", type=float, default=12)
    ap.add_argument(
        "--trailer",
        default="",
        help="attribution line appended to every commit message",
    )
    ap.add_argument(
        "--facts",
        action="store_true",
        help="print the uncommitted files with their age and exit",
    )
    a = ap.parse_args()
    if a.facts:
        print(facts(ROOT))
        return
    file = AUDIT / f"{a.day}-commit.json"
    if not file.exists():
        sys.exit(f"No hay propuesta: {file}")
    only = {int(x) for x in a.only.split(",")} if a.only else None
    sys.exit(
        apply(
            file,
            ROOT,
            dry=a.dry_run,
            only=only,
            push=not a.no_push,
            force=a.force,
            max_age_h=a.max_age_hours,
            trailer=a.trailer,
        )
    )


if __name__ == "__main__":
    main()
