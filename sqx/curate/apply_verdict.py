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
    """The install one role names.

    Args:
        role: "master", or a headless role from machine.yaml.

    Returns:
        Its top-level folder.
    """
    return MASTER if role == "master" else WORKERS[role]["path"]


def is_up(role: str) -> bool:
    """Whether anything is holding that install.

    Args:
        role: "master" or a headless role.

    Returns:
        True when it is running. Nothing here may run against a live install: SQX holds a
        databank's records in memory and rewrites the files from them, so a file moved
        underneath it is undone by the next sync.
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
    """Strategies whose file on disk is not the one the verdict judged.

    Args:
        source: Databank directory.
        names: Name to expected identity; "" skips the check for that name.

    Returns:
        Names whose file exists but hashes differently. Safe with the install running: it
        only reads.
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
    databank's metrics export, when there is one, with the reason as its first column. The .sqx themselves are deleted, not
    kept: at ~5 MB each, 8k rejects are 40 GB for a strategy nobody will revisit. Owner's
    decision, 2026-09-23.
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
        How many went, and the names that had no file. A file per strategy is the only
        handle there is: the CLI's own `strategies=` selector cannot be used — over the
        worker's HTTP API the name is cut at its first space, and a one-shot sqcli never
        loads the records, so both report success and change nothing.
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


def main() -> None:
    """Print what would move; move it only with --apply and the install stopped."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--verdict", required=True, type=Path, help="path of a verdict.csv")
    ap.add_argument("--into", help="databank of the same project to move the rejected into "
                                   "instead of deleting them. A databank inside the project is "
                                   "loaded into memory on the next start, so this costs RAM")
    ap.add_argument("--role", default="master", choices=["master", *sorted(WORKERS)])
    ap.add_argument("--apply", action="store_true", help="without it nothing is touched")
    a = ap.parse_args()

    install = install_of(a.role)
    source = databank_dir(a.project, a.databank, install)
    names = rejected(a.verdict)
    on_disk = sorted(f.stem for f in source.glob("*.sqx"))
    print(f"{install.name} · {a.project}/{a.databank}: {len(on_disk)} strategies on disk")
    print(f"  the verdict drops {len(names)}, keeping {len(on_disk) - len(names)}")
    if not on_disk:
        sys.exit(f"{source} holds no .sqx at all. A databank set to `Auto-sync never` keeps its "
                 "records in memory and leaves the directory empty, so there is nothing here to "
                 "curate and nothing for Python to have filtered. Set it to `Auto-sync every 1 "
                 "hour` in project.cfx, or run `-databank action=synctofiles` on the instance "
                 "that holds them, before stopping it.")
    unknown = [n for n in names if n not in set(on_disk)]
    if unknown:
        print(f"  ⚠️ {len(unknown)} named by the verdict are not here: {', '.join(unknown[:5])}")
    wrong = mismatched(source, names)
    if wrong:
        sys.exit(f"  ✗ {len(wrong)} carry a different strategy than the verdict judged: "
                 f"{', '.join(wrong[:5])}. The databank changed under that name since the "
                 f"verdict was written; re-export and judge again. Nothing was moved.")
    print(f"  identity checked on {sum(1 for i in names.values() if i)} of {len(names)}")
    if not a.apply:
        print(f"\ndry run. Re-run with --apply, with the {a.role} stopped.")
        return

    if is_up(a.role):
        sys.exit(f"the {a.role} is running. It holds this databank in memory and rewrites the "
                 f"files from it, so the move would be undone. Stop it first"
                 + ("." if a.role == "master" else f": bin/sqx-worker.sh --role {a.role} stop"))

    now = datetime.now()
    out = report_dir(a.project, a.databank, now.date().isoformat()) / "curate"
    out.mkdir(parents=True, exist_ok=True)
    stamp = f"{now:%H%M%S}"
    record(source, names, reasons(a.verdict), out, stamp, a.project, a.databank)
    before = len(on_disk)
    print(f"  what was here is listed in {out / f'before-{stamp}.csv'}")

    into = databank_dir(a.project, a.into, install) if a.into else None
    gone, absent = remove(source, into, list(names))
    after = len(list(source.glob("*.sqx")))
    print(f"{a.databank}: {before} → {after}   " + (f"{into}: +{gone}" if into else f"deleted {gone}"))
    if before - after != gone or absent:
        sys.exit(f"{len(absent)} had no file and {before - after} left against {gone} gone. "
                 f"Compare the directory with {out / f'before-{stamp}.csv'} before running "
                 "anything else.")
    print(f"start the {a.role} and the sync from files makes memory match: the next task "
          f"reads {after}.")

    manifest.write(out,
                   {"install": install.name, "project": a.project, "databank": a.databank,
                    "into": str(into), "verdict": str(a.verdict), "stamp": stamp},
                   f"apply_verdict.py --project {a.project} --databank {a.databank} "
                   f"--role {a.role} --apply" + (f" --into {a.into}" if a.into else ""),
                   {"judged": before, "kept": after, "removed": gone})


if __name__ == "__main__":
    main()
