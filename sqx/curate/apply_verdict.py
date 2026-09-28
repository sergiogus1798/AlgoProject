#!/usr/bin/env python3
"""Delete the strategies a verdict rejected from a databank, with the install stopped, keeping a record."""

import argparse
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from core import manifest, sqxfile, worker
from core.paths import MASTER, WORKERS, databank_dir, metrics_export, report_dir

DROP = "DESCARTAR"


def install_of(role: str) -> Path:
    """The top-level folder of the install one role ("master" or a headless role) names."""
    return MASTER if role == "master" else WORKERS[role]["path"]


def is_up(role: str) -> bool:
    """Whether anything holds that install ("master" or a headless role).

    Nothing here may run against a live install: SQX holds a databank's records in memory
    and rewrites the files from them, so a file moved underneath it is undone by the next sync.
    """
    if role == "master":
        worker.require_posix()
        return subprocess.run(["pgrep", "-f", f"{MASTER}/StrategyQuantX"],
                              capture_output=True, text=True).returncode == 0
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", WORKERS[role]["port"])) == 0


def rejected(verdict: Path) -> dict[str, str]:
    """The strategies a verdict drops.

    Args:
        verdict: A CSV with a `strategy` column, a `verdict` column and, when the judging
            module could compute it, an `identity` column (SHA-256 of the strategy's inner
            strategy_Portfolio.xml, `core.sqxfile.identity`).

    Returns:
        Name to identity, "" where none was given, sorted by name. This CSV is the whole
        contract between Python and SQX: any module that judges strategies writes one, and
        this command applies it. The identity exists because the name is not one: SQX
        renames on collision (`Strategy 19.6.36(1)`) and `copy` stacks identical files
        under one name, so a name alone can point at the wrong strategy.
    """
    calls = pd.read_csv(verdict, dtype=str).fillna("")
    drop = calls[calls.verdict == DROP]
    ids = drop["identity"] if "identity" in drop else [""] * len(drop)
    return dict(sorted(zip(drop.strategy, ids)))


def mismatched(source: Path, names: dict[str, str]) -> list[str]:
    """Names whose file exists but hashes differently from the identity the verdict gave.

    Args:
        source: Databank directory.
        names: Name to expected identity; "" skips the check for that name. Only reads.
    """
    return [n for n, i in names.items()
            if i and (source / f"{n}.sqx").exists() and sqxfile.identity(source / f"{n}.sqx") != i]


def reasons(verdict: Path) -> dict[str, str]:
    """Why each dropped strategy was dropped, as the judging module wrote it.

    Args:
        verdict: The verdict CSV.

    Returns:
        Name to its `reason` (the filter it failed, the test, "dropped by name"), or to the
        verdict's file name when the module wrote no `reason` column — then the file itself
        is the record of the test.
    """
    calls = pd.read_csv(verdict, dtype=str).fillna("")
    drop = calls[calls.verdict == DROP]
    why = drop["reason"] if "reason" in drop else [verdict.name] * len(drop)
    return dict(zip(drop.strategy, why))


def record(source: Path, names: dict[str, str], why: dict[str, str], out: Path, stamp: str,
           project: str, databank: str) -> None:
    """Write down what the cut removes, and why, before the files are gone.

    Args:
        source: Databank directory.
        names: Name to identity of the strategies being dropped.
        why: Name to the reason it is dropped.
        out: Directory to write into, the same one the verdicts live in.
        stamp: HHMMSS of this cut, so several cuts a day keep apart.
        project, databank: Whose metrics export to take the dropped rows from.

    Two files: `before-<stamp>.csv`, every strategy on disk with identity, size, whether
    this cut drops it and why; `rejected-<stamp>.csv`, the dropped ones' rows of the
    databank's metrics export, when there is one, with the reason as its first column. Here the
    .sqx are deleted, not kept (~5 MB each; owner, 2026-09-23); the window's «Continuar
    workflow» copies them to `AlgoData/projects/discards/` before calling (owner, Q7, 2026-09-27).
    """
    files = sorted(source.glob("*.sqx"))
    pd.DataFrame({"strategy": [f.stem for f in files],
                  "identity": [sqxfile.identity(f) for f in files],
                  "bytes": [f.stat().st_size for f in files],
                  "verdict": [DROP if f.stem in names else "MANTENER" for f in files],
                  "reason": [why.get(f.stem, "") for f in files]}
                 ).to_csv(out / f"before-{stamp}.csv", index=False)
    csv = metrics_export(project, databank) / "metrics.csv"
    if csv.exists():
        m = pd.read_csv(csv, sep=";", quotechar='"')
        m = m[m["Strategy Name"].isin(names)]
        m.insert(0, "reason", [why[n] for n in m["Strategy Name"]])
        m.to_csv(out / f"rejected-{stamp}.csv", index=False)
        print(f"  metrics of the dropped kept in {out / f'rejected-{stamp}.csv'}")
    else:
        print(f"  no metrics export at {csv}: only names and identities are kept")


def remove(source: Path, into: Path | None, names: list[str]) -> tuple[int, list[str]]:
    """Take the named strategies' files out of a databank directory.

    Args:
        source: Databank directory holding them.
        into: Databank directory to move them to, created when missing; None deletes them.
        names: Strategy names, without the .sqx suffix.

    Returns:
        How many went, and the names with no file. Files are the only handle: over the HTTP
        API a name is cut at its first space and a one-shot sqcli never loads the records.
    """
    if into:
        into.mkdir(parents=True, exist_ok=True)
    gone, absent = 0, []
    for name in names:
        f = source / f"{name}.sqx"
        if not f.exists():
            absent.append(name)
            continue
        shutil.move(str(f), str(into / f.name)) if into else f.unlink()
        gone += 1
    return gone, absent


EMPTY = ("{source} holds no .sqx at all: a databank on `Auto-sync never` keeps its records in "
         "memory only. Set it to `Auto-sync every 1 hour` in project.cfx, or run `-databank "
         "action=synctofiles` on the instance that holds them, before stopping it.")


def refuse_mismatch(source: Path, names: dict[str, str]) -> None:
    """Stop, with nothing moved, when a file is not the strategy the verdict judged."""
    wrong = mismatched(source, names)
    if wrong:
        sys.exit(f"  ✗ {len(wrong)} carry a different strategy than the verdict judged: "
                 f"{', '.join(wrong[:5])}. The databank changed under that name since the "
                 f"verdict was written; re-export and judge again. Nothing was moved.")


def apply(project: str, databank: str, verdict_csv: Path, role: str,
          into: str | None = None) -> dict:
    """Cut a databank by a verdict: check, record, then delete (or move) the rejected files.

    Args:
        project: Project name in that install.
        databank: Databank to cut.
        verdict_csv: The verdict, as `rejected` reads it.
        role: Which install holds the project, "master" or a headless role; never defaulted.
        into: A databank of the same project to move the rejected into; None deletes them.

    Returns:
        `install`, `before`, `after`, `removed` and `out` (the folder of the records).
        SystemExit, nothing touched, on an empty databank, a changed file or a live install.
    """
    install = install_of(role)
    source = databank_dir(project, databank, install)
    names = rejected(verdict_csv)
    on_disk = sorted(f.stem for f in source.glob("*.sqx"))
    if not on_disk:
        sys.exit(EMPTY.format(source=source))
    refuse_mismatch(source, names)
    if is_up(role):
        sys.exit(f"the {role} is running. It holds this databank in memory and rewrites the "
                 f"files from it, so the move would be undone. Stop it first"
                 + ("." if role == "master" else f": bin/sqx-worker.sh --role {role} stop"))
    now = datetime.now()
    out, stamp = report_dir(project, databank, now.date().isoformat()) / "curate", f"{now:%H%M%S}"
    out.mkdir(parents=True, exist_ok=True)
    record(source, names, reasons(verdict_csv), out, stamp, project, databank)
    print(f"  what was here is listed in {out / f'before-{stamp}.csv'}")
    target = databank_dir(project, into, install) if into else None
    gone, absent = remove(source, target, list(names))
    after = len(list(source.glob("*.sqx")))
    print(f"{databank}: {len(on_disk)} → {after}   "
          + (f"{target}: +{gone}" if target else f"deleted {gone}"))
    if len(on_disk) - after != gone or absent:
        sys.exit(f"{len(absent)} had no file and {len(on_disk) - after} left against {gone} "
                 f"gone. Compare the directory with {out / f'before-{stamp}.csv'} before "
                 "running anything else.")
    manifest.write(out,
                   {"install": install.name, "project": project, "databank": databank,
                    "into": str(target), "verdict": str(verdict_csv), "stamp": stamp},
                   f"apply_verdict.py --project {project} --databank {databank} "
                   f"--role {role} --apply" + (f" --into {into}" if into else ""),
                   {"judged": len(on_disk), "kept": after, "removed": gone})
    return {"install": install.name, "before": len(on_disk), "after": after, "removed": gone,
            "out": out}


def main() -> None:
    """Print what would move; move it only with --apply and the install stopped."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--verdict", required=True, type=Path, help="path of a verdict.csv")
    ap.add_argument("--into", help="databank of the same project to move the rejected into "
                                   "instead of deleting them. A databank inside the project is "
                                   "loaded into memory on the next start, so this costs RAM")
    # Required since 2026-09-28 (F7): its old default, the master, made a forgotten flag cut his.
    ap.add_argument("--role", required=True, choices=["master", *sorted(WORKERS)])
    ap.add_argument("--apply", action="store_true", help="without it nothing is touched")
    a = ap.parse_args()

    install = install_of(a.role)
    source = databank_dir(a.project, a.databank, install)
    names = rejected(a.verdict)
    on_disk = sorted(f.stem for f in source.glob("*.sqx"))
    print(f"{install.name} · {a.project}/{a.databank}: {len(on_disk)} strategies on disk")
    print(f"  the verdict drops {len(names)}, keeping {len(on_disk) - len(names)}")
    if not on_disk:
        sys.exit(EMPTY.format(source=source))
    unknown = [n for n in names if n not in set(on_disk)]
    if unknown:
        print(f"  ⚠️ {len(unknown)} named by the verdict are not here: {', '.join(unknown[:5])}")
    print(f"  identity checked on {sum(1 for i in names.values() if i)} of {len(names)}")
    if not a.apply:
        refuse_mismatch(source, names)
        print(f"\ndry run. Re-run with --apply, with the {a.role} stopped.")
        return
    done = apply(a.project, a.databank, a.verdict, a.role, a.into)
    print(f"start the {a.role} and the sync from files makes memory match: the next task "
          f"reads {done['after']}.")


if __name__ == "__main__":
    main()
