#!/usr/bin/env python3
"""Fabricate the structural batch of one or more mothers: write the files, read them back, refuse a mismatch."""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from sqx.structural import logic, plan
from sqx.variants import inputs
from sqx.variants.build import rewrite

FILE = "structure.parquet"
NAME = "{strategy} {variant_id}"
COLLISION = re.compile(r"\(\d+\)$")   # SQX renames a second copy `S00O00(1)`


def write(rows: pd.DataFrame, folder: Path, shape: str) -> None:
    """Write every planned file: the rules rewritten, then the variant factory's three stamps.

    Args:
        rows: Output of `plan.build`.
        folder: Where the `.sqx` go; emptied first, because the read-back adopts whatever
            is on disk.
        shape: A key of `rewrite.SHAPES`.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for stale in folder.glob("*.sqx"):
        stale.unlink()
    for row in rows.itertuples():
        parent = rewrite.members(Path(row.mother))
        text = parent[rewrite.PORTFOLIO].decode("utf-8")
        if row.kind == "ablation":
            text = logic.ablate(text, row.signal, row.index)
        elif row.kind == "inversion":
            text = logic.invert(text)
        parent[rewrite.PORTFOLIO] = text.encode("utf-8")
        # The id stamp, both name fields and no inherited fingerprint: the three traps
        # the variant factory already solved (sqx/variants/build/README.md).
        parts = rewrite.variant(parent, row.variant_id,
                                NAME.format(strategy=row.strategy, variant_id=row.variant_id), {})
        rewrite.save(folder / f"{row.variant_id}.sqx", parts, shape)


def read_back(folder: Path) -> pd.DataFrame:
    """What every file in the folder actually holds, read off the disk.

    Args:
        folder: Where the batch was written.

    Returns:
        One row per file: `variant_id` from the file name, the `stamp` the file carries,
        `blocks` (the entry blocks left) and `direction` (the entry orders' sides), spelt as
        `plan.rows` spells what it expects. Nothing here comes from the plan.

        ⚠️ The id is the file name, `(N)` stripped, and not the stamp: a retest drops the
        `<!--variant_id-->` comment (🔬 2026-09-26, knowhow/sqx-format/writing-a-variant.md),
        so a retested file carries no stamp at all.
    """
    out = []
    for path in sorted(folder.glob("*.sqx")):
        text = rewrite.members(path)[rewrite.PORTFOLIO].decode("utf-8")
        out.append({"variant_id": COLLISION.sub("", path.stem), "stamp": rewrite.stamped(text),
                    "file": path.name,
                    "blocks": "+".join(f"{c['signal']}:{c['block']}"
                                       for c in logic.conditions(text)),
                    "direction": "+".join(str(v) for v in logic.direction(text))})
    return pd.DataFrame(out)


def verify(rows: pd.DataFrame, disk: pd.DataFrame) -> pd.DataFrame:
    """The plan joined to the disk, with the rows whose file is not what was meant.

    Args:
        rows: Output of `plan.build`.
        disk: Output of `read_back`.

    Returns:
        The joined frame, `ok` per row. A missing file, an unexpected one, a block that
        survived its ablation or a direction that did not flip is `ok = False`.
    """
    both = rows.merge(disk, on="variant_id", how="outer", indicator=True)
    both["ok"] = ((both["_merge"] == "both") & (both["blocks"] == both["expect_blocks"])
                  & (both["direction"] == both["expect_direction"]))
    return both.drop(columns="_merge")


def main() -> None:
    """Fabricate the batch and its manifest, and refuse one whose files are not the plan."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mothers", required=True, type=Path,
                    help="folder of .sqx copied out of SQX; the stem is the strategy's name")
    ap.add_argument("--out", required=True, type=Path,
                    help="the batch directory under the data root; holds sqx/ afterwards")
    a = ap.parse_args()

    mothers = sorted(a.mothers.glob("*.sqx"))
    rows = plan.build(mothers)
    write(rows, a.out / "sqx", inputs.load()["build"]["shape"])
    checked = verify(rows, read_back(a.out / "sqx"))
    checked["ok"] &= checked["stamp"] == checked["variant_id"]
    checked.to_parquet(a.out / FILE, compression="zstd", index=False)
    print(checked[["variant_id", "strategy", "kind", "block", "direction", "ok"]]
          .to_string(index=False))
    if not checked["ok"].all():
        raise SystemExit(f"el lote no es el plan: {list(checked.loc[~checked['ok'], 'variant_id'])}")
    print(f"{len(mothers)} madre(s) -> {len(rows)} ficheros en {a.out / 'sqx'}")


if __name__ == "__main__":
    main()
