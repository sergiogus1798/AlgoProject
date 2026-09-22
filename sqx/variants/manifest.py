"""Contract C2: what was fabricated, read back off the disk. Never what the plan meant to fabricate."""

import zipfile
from pathlib import Path

import pandas as pd

from sqx.variants import tuples
from sqx.variants.build import rewrite

FILE = "manifest.parquet"
NUMERIC = ("int", "double")


def read_back(folder: Path, names: list[str]) -> pd.DataFrame:
    """Every .sqx in a folder, as the file itself describes it.

    Args:
        folder: Where the batch was written.
        names: The design's parameters, the columns to report.

    Returns:
        One row per file: the identifier stamped inside it, the name SQX will show it
        under, its tuple read out of `strategy_Portfolio.xml`, and the hash of that
        tuple. Nothing here comes from the plan, which is the whole point: this is the
        only place the study finds out that file `P01234` holds the combination the plan
        says it holds.
    """
    rows = []
    for path in sorted(folder.glob("*.sqx")):
        with zipfile.ZipFile(path) as archive:
            portfolio = archive.read(rewrite.PORTFOLIO).decode("utf-8")
            settings = archive.read(rewrite.SETTINGS).decode("utf-8")
        declared = rewrite.declared(portfolio)
        stored = rewrite.values(portfolio)
        found = {n: float(stored[n]) for n in names
                 if n in stored and declared[n] in NUMERIC}
        rows.append({"variant_id": rewrite.stamped(portfolio),
                     "sqx_name": rewrite.RESULT_NAME.search(settings).group(0).split('"')[1],
                     "file": path.name, **tuples.columns(found),
                     "tuple_hash": tuples.tuple_hash(found)})
    return pd.DataFrame(rows)


def verify(plan: pd.DataFrame, disk: pd.DataFrame) -> dict:
    """Whether the batch on disk is the batch that was planned.

    Args:
        plan: Output of `design.plan.build`.
        disk: Output of `read_back`.

    Returns:
        Counts for the three silent failures this module exists to catch: an identifier
        that reached no file or a file with none (mode 1, the collision rename), a file
        whose tuple is not the tuple the plan gave that identifier (mode 3), and two
        files holding the same tuple, which SQX may merge into one strategy (mode 2's
        cousin, and the reason a design deduplicates before it fabricates).

        It counts rather than trusts. A batch with a non-zero count here is not a batch
        with a warning, it is a study that cannot be joined.
    """
    paired = plan.merge(disk, on="variant_id", how="outer", suffixes=("_plan", "_disk"),
                        indicator=True)
    both = paired[paired["_merge"] == "both"]
    return {"planned": len(plan), "on_disk": len(disk),
            "missing": sorted(paired.loc[paired["_merge"] == "left_only", "variant_id"]),
            "unexpected": sorted(paired.loc[paired["_merge"] == "right_only", "variant_id"]),
            "tuple_mismatch": sorted(
                both.loc[both["tuple_hash_plan"] != both["tuple_hash_disk"], "variant_id"]),
            "duplicate_tuples": int(disk["tuple_hash"].duplicated().sum())}


def write(plan: pd.DataFrame, folder: Path, names: list[str]) -> tuple[pd.DataFrame, dict]:
    """Build contract C2 from the files on disk and store it beside them.

    Args:
        plan: Output of `design.plan.build`.
        folder: Where the `.sqx` were written; the parquet lands in its parent.
        names: The design's parameters.

    Returns:
        The manifest and the verification report.

        The tuple columns come from the files. The stratum, the origin flag and the canary
        expectations come from the plan, because no file can know them -- so they are
        joined on `variant_id`, and `verify` has already said whether that join is sound.

        `sqx_name` here is the name the file was written under. It is not yet the name SQX
        returns: a collision rename happens when the databank loads the batch, and the
        collection stage overwrites this column with what came back.
    """
    disk = read_back(folder, names)
    report = verify(plan, disk)
    carried = ["variant_id", "stratum", "origin", "canary_expect_netprofit",
               "canary_expect_trades", "canary_expect_same_as"]
    frame = disk.merge(plan[carried], on="variant_id", how="left")
    frame.to_parquet(folder.parent / FILE, compression="zstd", index=False)
    return frame, report


def read(folder: Path) -> pd.DataFrame:
    """Load a batch's manifest.

    Args:
        folder: The strategy's variants directory.

    Returns:
        Contract C2 as it was written.
    """
    return pd.read_parquet(folder / FILE)
