"""What could be deleted and how much it would free. Proposes; never deletes, never moves."""

import json
import time
from pathlib import Path

from core.paths import DATA

DAY = 86400
INTERMEDIATES = "intermediates"
SUPERSEDED, STRATEGY_COPIES, COLLECTED, STALE = (
    "superseded_export", "strategy_copies", "collected_variants", "stale_branch")


def _bytes(where: Path) -> tuple[int, int]:
    """Size and file count under one directory.

    Args:
        where: Directory to descend.

    Returns:
        (bytes, files).
    """
    total = files = 0
    for path in where.rglob("*"):
        if path.is_file():
            total += path.stat().st_size
            files += 1
    return total, files


def superseded(root: Path = DATA) -> list[dict]:
    """Dated exports of the same databank that a newer export replaced.

    Args:
        root: The data root.

    Returns:
        One row per superseded date folder under `raw/<project>/<databank>/<date>/`.

        **A newer date is not automatically a replacement**, and assuming so was the
        rule's first version. Measured 2026-09-21: `raw/XAUUSD/SPP_IS/2026-09-19` holds
        only `wfc_pairs/`, while `2026-09-10` holds the full permutation tables the whole
        SPP study reads. Calling the older one superseded would have proposed deleting the
        only copy of the study's input. So an older export counts as superseded only when
        the newer one contains **every top-level entry the older has** -- a superset, not
        merely a later date.

        ⚠️ Still candidates, not verdicts. `tasks/CLAUDE.md` makes `raw/` immutable on
        purpose: these exports are slow to produce and are cited by strategy-level
        reports, which is why several dates coexist. An older export is only actually free
        once nothing published still refers to it, and that is a judgement this module
        cannot make.
    """
    rows = []
    for databank in sorted((root / "raw").glob("*/*")):
        dates = sorted(d for d in databank.iterdir() if d.is_dir())
        if not dates:
            continue
        newest = {p.name for p in dates[-1].iterdir()}
        for old in dates[:-1]:
            missing = {p.name for p in old.iterdir()} - newest
            if missing:
                continue
            size, files = _bytes(old)
            rows.append({"rule": SUPERSEDED, "path": str(old.relative_to(root)),
                         "bytes": size, "files": files,
                         "why": f"{dates[-1].name} contains everything it has"})
    return rows


def strategy_copies(root: Path = DATA) -> list[dict]:
    """`.sqx` files sitting inside exports, which are copies of strategies SQX still holds.

    Args:
        root: The data root.

    Returns:
        One row per export folder holding `.sqx` files, with what they weigh.

        These are the cheapest real win: the analysis reads the CSVs beside them, and the
        strategies themselves live in the databank. They are only unrecoverable if the
        databank that held them has since been cleared -- which, given that every sync
        deletes on-disk `.sqx` not held in memory, is not hypothetical. Check before
        proposing, which is why this reports and stops.
    """
    rows = []
    for folder in sorted({p.parent for p in (root / "raw").rglob("*.sqx")}):
        files = list(folder.glob("*.sqx"))
        rows.append({"rule": STRATEGY_COPIES, "path": str(folder.relative_to(root)),
                     "bytes": sum(f.stat().st_size for f in files), "files": len(files),
                     "why": "copies of strategies the databank holds"})
    return rows


def intermediates(root: Path = DATA) -> list[dict]:
    """`raw/` and `trades/` CSV folders left beside a `trades.parquet` that already holds them.

    Args:
        root: The data root.

    Returns:
        One row per such folder. What orderstocsv wrote before it was packed, and the
        per-file splits the first exporters left: exports made after 2026-09-23 delete
        them on the way out, so anything here predates that and is reproducible from the
        Parquet beside it.
    """
    rows = []
    for packed in sorted((root / "raw").rglob("trades.parquet")):
        for name in ("raw", "trades"):
            folder = packed.parent / name
            if folder.is_dir():
                size, files = _bytes(folder)
                rows.append({"rule": INTERMEDIATES, "path": str(folder.relative_to(root)),
                             "bytes": size, "files": files,
                             "why": "CSV intermediates of the trades.parquet beside them"})
    return rows


def collected(root: Path = DATA) -> list[dict]:
    """Variant databanks whose pipeline ledger says their data was exported and verified.

    Args:
        root: The data root.

    Returns:
        One row per strategy whose `state.json` reached the `collected` stage, naming what
        the ledger recorded as safe to remove.

        This is the only rule here that is a verdict rather than a candidate, because the
        ledger records the export's file hashes: the data provably survived the deletion.
        Returns nothing until `pipeline/` exists and has run, which is correct -- an empty
        list means "no evidence", not "nothing to clean".
    """
    rows = []
    for state in sorted((root / "pipeline").rglob("state.json")):
        got = json.loads(state.read_text(encoding="utf-8"))
        stage = got.get("stages", {}).get("collected")
        if not stage or not stage.get("done_at"):
            continue
        for item in stage.get("removable", []):
            path = root / item
            if path.exists():
                size, files = _bytes(path) if path.is_dir() else (path.stat().st_size, 1)
                rows.append({"rule": COLLECTED, "path": item, "bytes": size,
                             "files": files, "why": f"ledger {got['strategy']}: exported "
                                                    f"and hashed at {stage['done_at']}"})
    return rows


def stale(rows: list[dict], cfg: dict, root: Path = DATA) -> list[dict]:
    """Branches nothing has written to in a long time.

    Args:
        rows: Output of `inventory.tree`.
        cfg: What config.load() returned; reads `disk.stale_days`.
        root: The data root.

    Returns:
        One row per stale top-level branch. The weakest rule of the four -- old is not the
        same as unwanted, and `reports/` is meant to accumulate forever -- so it is
        reported last and separately.
    """
    days = cfg["disk"]["stale_days"]
    return [{"rule": STALE, "path": r["branch"], "bytes": r["bytes"], "files": r["files"],
             "why": f"nothing written for {r['age_days']:.0f} days (limit {days})"}
            for r in rows if "/" not in r["branch"] and r["stale"]]


def proposals(rows: list[dict], cfg: dict, root: Path = DATA) -> list[dict]:
    """Everything the five rules found, biggest first.

    Args:
        rows: Output of `inventory.tree`.
        cfg: What config.load() returned.
        root: The data root.

    Returns:
        One row per candidate with its rule, its bytes and why. **Nothing here is deleted
        by anything in this repository.** The owner decides; this only makes the decision
        possible by attaching a number to it.
    """
    found = (collected(root) + superseded(root) + strategy_copies(root)
             + intermediates(root) + stale(rows, cfg, root))
    return sorted(found, key=lambda r: r["bytes"], reverse=True)
