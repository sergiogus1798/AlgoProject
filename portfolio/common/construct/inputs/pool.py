"""A declared pool of archived strategies: write it once (frozen), read it, drop prohibitions, hash it."""

import argparse
import hashlib
from datetime import date
from pathlib import Path
from typing import Any, TypedDict, cast

import pandas as pd

from core.archive import read as archive_read
from core.paths import portfolio_dir

ROOT = portfolio_dir()
COLUMNS = ("identity", "version", "development", "near", "added_on", "added_by", "note")
PROHIBITION_COLUMNS = ("identity", "version", "firm", "plan", "rule", "reason", "decided_on")   # PLAN §2.1


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
    } for row in rows], columns=pd.Index(COLUMNS))
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)
    return out


class PoolId(TypedDict):
    """What the ledger needs of a pool: its hash."""

    hash: str


class Pool(PoolId):
    """A declared pool as read: its kept members, the prohibited ones, their counts and the hash."""

    members: list[dict]
    prohibited: list[dict]
    n_pool: int
    n_prohibited: int


def read(name: str, firm: str | None, plan: str | None = None) -> Pool:
    """A declared pool, with one firm's prohibitions removed and hashed.

    Args:
        name: Pool name.
        firm: A `prohibitions/<firm>.csv` to drop before hashing (`PROHIBITION_COLUMNS`); None
            reads the whole pool. A firm with no file prohibits nothing.
        plan: A catalogue plan key. With it a row counts when its `plan` cell is empty (every
            plan of the firm) or a prefix of the key (`hantec:express` covers every size);
            without it every row of the firm counts.

    Returns:
        `members` (rows kept, dicts), `prohibited` (the prohibition rows that dropped a
        member, dicts), `n_pool`, `n_prohibited` (members dropped), `hash` (sha256 of the
        sorted `identity@version` left — stable under row order, so two declarations of the
        same members agree).
    """
    pool = pd.read_csv(ROOT / "pools" / f"{name}.csv", dtype=str)
    prohibited: pd.DataFrame = pd.DataFrame(columns=pd.Index(PROHIBITION_COLUMNS))
    firm_file = ROOT / "prohibitions" / f"{firm}.csv"
    if firm and firm_file.is_file():
        banned = pd.read_csv(firm_file, dtype=str, keep_default_na=False)
        in_pool = set(zip(pool["identity"], pool["version"]))
        prohibited = cast(pd.DataFrame, banned[[(r.identity, r.version) in in_pool
                             and (plan is None or plan.startswith(r.plan))
                             for r in cast(Any, banned).itertuples()]])
    dropped = set(zip(prohibited["identity"], prohibited["version"]))
    kept = cast(pd.DataFrame, pool[~pool.apply(lambda r: (r["identity"], r["version"]) in dropped, axis=1)])
    keys = sorted(f"{i}@{v}" for i, v in zip(kept["identity"], kept["version"]))
    digest = hashlib.sha256("\n".join(keys).encode("utf-8")).hexdigest()
    return {"members": kept.to_dict("records"), "prohibited": prohibited.to_dict("records"),
            "n_pool": len(pool), "n_prohibited": len(pool) - len(kept), "hash": digest}


def scoped(cfg: dict, firm: str | None, plan: str | None = None) -> dict[str, Any]:
    """The run's config naming the firm (and plan) whose prohibitions it applies (`--firm`)."""
    return {**cfg, "pool": {"firm": firm, "plan": plan}} if firm else cfg


def declared(name: str, cfg: dict) -> Pool:
    """`read()` of the pool as the run's config scopes it: whole, or less a firm's prohibitions."""
    scope = cfg.get("pool", {})
    return read(name, scope.get("firm"), scope.get("plan"))


def prohibited_lines(name: str, cfg: dict) -> list[str]:
    """The Spanish lines a report opens with: which firm's prohibitions applied, who they drop."""
    firm = cfg.get("pool", {}).get("firm")
    if not firm:
        return []
    got = declared(name, cfg)
    return [f"Prohibiciones de {firm}: {got['n_prohibited']} de {got['n_pool']} miembros fuera "
            "del pool antes de buscar"] + [
        f"  prohibida {r['identity'][:12]}…: {r['rule']} ({r['plan'] or 'todos los planes'}) — "
        f"{r['reason']}" for r in got["prohibited"]]


def _development(identity: str, version: str) -> bool:
    """Whether an archived strategy has not yet reached the validated pool (step 26, Q13)."""
    step = archive_read.load(identity, version)["manifest"]["step"]
    return float(step) < 26


def main() -> None:
    """`declare <name> --added-by <who>` with the members as `--identity` or one per line of `--file`."""
    parser = argparse.ArgumentParser(prog="python3 -m portfolio.common.construct.inputs.pool")
    declare_ = parser.add_subparsers(dest="verb", required=True).add_parser("declare")
    declare_.add_argument("name")
    declare_.add_argument("--added-by", required=True)
    declare_.add_argument("--identity", action="append", default=[],
                          help="identidad[@versión]; sin versión, la última archivada")
    declare_.add_argument("--file", type=Path, help="una identidad[@versión] por línea")
    declare_.add_argument("--note", default="")
    args = parser.parse_args()
    listed = args.identity + (args.file.read_text(encoding="utf-8").split() if args.file else [])
    rows = [{"identity": identity, "version": version or archive_read.versions(identity)[-1],
             "note": args.note}
            for identity, _, version in (item.partition("@") for item in listed)]
    try:
        out = declare(args.name, rows, args.added_by)
    except FileExistsError as refused:
        raise SystemExit(str(refused)) from refused
    print(f"Pool '{args.name}' declarado: {len(rows)} miembros, hash {read(args.name, None)['hash'][:12]}… → {out}")


if __name__ == "__main__":
    main()
