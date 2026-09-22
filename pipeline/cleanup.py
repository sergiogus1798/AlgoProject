#!/usr/bin/env python3
"""Delete a finished mother's variant data, but only what the ledger proves is recoverable."""

import argparse
import hashlib
import shutil
from pathlib import Path

from core.paths import DATA
from perf.disk import retention
from pipeline.ledger import state

COLLECTED = "collected"


def unchanged(entry: dict) -> bool:
    """Whether one exported file is still exactly what collect recorded.

    Args:
        entry: A row of `stages.collected.files`: path, bytes and sha256.

    Returns:
        True when the file is there and hashes to the digest in the ledger. The hash is
        the whole point: it turns "the export probably worked" into evidence that survives
        the data it describes.
    """
    path = DATA / entry["path"]
    return path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]


def inside(path: Path, work: Path) -> bool:
    """Whether a path the ledger proposes deleting lies inside this mother's own folder.

    Args:
        path: Absolute path proposed for deletion.
        work: The strategy's work directory.

    Returns:
        True when it does. **The mother strategy is never deletable**: it lives in the SQX
        databank and in `raw/`, and nothing the pipeline writes puts it inside
        `pipeline/<project>/<strategy>/`. Confining the sweep to that folder therefore
        makes reaching the mother impossible rather than merely forbidden, which is a
        guarantee that does not depend on the manifest's `origin` flag being right.
    """
    return work in path.parents


def candidates(work: Path) -> list[dict]:
    """What the ledger says this mother no longer needs on disk, with what it weighs.

    Args:
        work: The strategy's work directory.

    Returns:
        The rows `perf/disk/retention.py` already derives from this ledger, narrowed to
        this strategy. The list is not re-derived here on purpose: retention owns the
        rule "the ledger recorded it as exported and hashed", this module owns "and it is
        therefore safe to delete", and two definitions of the first would drift apart.

    Raises:
        SystemExit: The collect stage never finished, an exported file no longer matches
            its recorded hash, or a proposed path escapes the mother's own folder.
    """
    ledger = state.read(work)
    stage = ledger["stages"].get(COLLECTED, {})
    if not stage.get("done_at"):
        raise SystemExit(f"{ledger['strategy']}: la recogida no ha terminado, no se borra nada")
    broken = [f["path"] for f in stage["files"] if not unchanged(f)]
    if broken:
        raise SystemExit(f"{ledger['strategy']}: el export ya no coincide con su hash: " +
                         ", ".join(broken))
    here = str(work.relative_to(DATA))
    rows = [r for r in retention.collected() if r["path"].startswith(here)]
    outside = [r["path"] for r in rows if not inside(DATA / r["path"], work)]
    if outside:
        raise SystemExit(f"{ledger['strategy']}: el registro propone borrar fuera de su "
                         f"carpeta: {', '.join(outside)}")
    return rows


def sweep(work: Path, apply: bool) -> list[dict]:
    """Remove the variant data and write what was removed into the ledger.

    Args:
        work: The strategy's work directory.
        apply: False reports and deletes nothing.

    Returns:
        One row per path, with its bytes. The ledger keeps the row after the data is gone,
        which is what makes the deletion auditable instead of a hole in the record.
    """
    found = candidates(work)
    rows = [{"path": r["path"], "bytes": r["bytes"], "at": state.now()} for r in found]
    if not apply:
        return rows
    for row in rows:
        path = DATA / row["path"]
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    ledger = state.read(work)
    ledger["stages"][COLLECTED]["deleted"] = (
        ledger["stages"][COLLECTED].get("deleted", []) + rows)
    state.write(work, ledger)
    return rows


def main() -> None:
    """Report, or with --apply carry out, the sweep of one mother strategy."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--strategy", required=True)
    ap.add_argument("--apply", action="store_true", help="borra de verdad; sin él solo informa")
    args = ap.parse_args()

    rows = sweep(state.work_dir(args.project, args.strategy), args.apply)
    for row in rows:
        print(f"{'borrado ' if args.apply else 'liberaría'} {row['bytes']:>12,d} B  {row['path']}")
    print(f"{sum(r['bytes'] for r in rows):,d} B en {len(rows)} rutas"
          + ("" if args.apply else "  (nada borrado: falta --apply)"))


if __name__ == "__main__":
    main()
