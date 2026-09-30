"""A declared pool of archived strategies: write it once (frozen), read it, drop prohibitions, hash it."""

import hashlib
from datetime import date
from pathlib import Path

import pandas as pd

from core.archive import read as archive_read
from core.datapaths import portfolio_dir

ROOT = portfolio_dir()
COLUMNS = ("identity", "version", "development", "near", "added_on", "added_by", "note")


def declare(name: str, rows: list[dict], added_by: str) -> Path:
    """Freeze a named pool of archived strategies.

    Args:
        name: Pool name. A pool of this name already on disk refuses — a declared pool is
            never re-pointed at a universe chosen after looking.
        rows: One dict per member: `identity`, `version`, and optionally `near` (bool,
            default False) and `note`.
        added_by: Who declared it, for the CSV.

    Returns:
        The written `pools/<name>.csv` path.
    """
    out = ROOT / "pools" / f"{name}.csv"
    if out.exists():
        raise FileExistsError(f"el pool '{name}' ya está declarado: {out}")
    today = date.today().isoformat()
    frame = pd.DataFrame([{
        "identity": row["identity"],
        "version": row["version"],
        "development": _development(row["identity"], row["version"]),
        "near": bool(row.get("near", False)),
        "added_on": today,
        "added_by": added_by,
        "note": row.get("note", ""),
    } for row in rows], columns=COLUMNS)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    return out


def read(name: str, firm: str | None) -> dict:
    """A declared pool, with one firm's prohibitions removed and hashed.

    Args:
        name: Pool name.
        firm: A `prohibitions/<firm>.csv` to drop before hashing; None reads the whole pool.

    Returns:
        `members` (rows kept, dicts), `prohibited` (the dropped prohibition rows, dicts),
        `n_pool`, `n_prohibited`, `hash` (sha256 of the sorted `identity@version` left —
        stable under row order, so two declarations of the same members agree).
    """
    pool = pd.read_csv(ROOT / "pools" / f"{name}.csv", dtype=str)
    prohibited = pd.DataFrame(columns=["identity", "version"])
    if firm:
        firm_file = ROOT / "prohibitions" / f"{firm}.csv"
        if firm_file.is_file():
            banned = pd.read_csv(firm_file, dtype=str)
            in_pool = set(zip(pool["identity"], pool["version"]))
            prohibited = banned[banned.apply(
                lambda r: (r["identity"], r["version"]) in in_pool, axis=1)]
    dropped = set(zip(prohibited["identity"], prohibited["version"]))
    kept = pool[~pool.apply(lambda r: (r["identity"], r["version"]) in dropped, axis=1)]
    keys = sorted(f"{i}@{v}" for i, v in zip(kept["identity"], kept["version"]))
    digest = hashlib.sha256("\n".join(keys).encode("utf-8")).hexdigest()
    return {"members": kept.to_dict("records"), "prohibited": prohibited.to_dict("records"),
            "n_pool": len(pool), "n_prohibited": len(prohibited), "hash": digest}


def _development(identity: str, version: str) -> bool:
    """Whether an archived strategy has not yet reached the validated pool (step 26, Q13)."""
    step = archive_read.load(identity, version)["manifest"]["step"]
    return float(step) < 26
