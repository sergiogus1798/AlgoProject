"""Write the plan to disk as one .sqx per row. Mechanical; decides nothing and reads nothing back."""

from pathlib import Path

import pandas as pd

from sqx.variants import tuples
from sqx.variants.build import rewrite

NAME = "{strategy} {variant_id}"


def name_of(strategy: str, variant_id: str) -> str:
    """The name a variant is written under.

    Args:
        strategy: The parent's name, as SQX writes it.
        variant_id: `P00000` and up.

    Returns:
        Parent and identifier together, so a databank holding several families stays
        readable and the identifier is still visible without opening the file. SQX may
        rename on collision anyway, which is why the identifier is also stamped inside.
    """
    return NAME.format(strategy=strategy, variant_id=variant_id)


def batch(plan: pd.DataFrame, parent: Path, strategy: str, out: Path, shape: str) -> dict:
    """Fabricate every row of a plan.

    Args:
        plan: Output of `design.plan.build`.
        parent: The `.sqx` every variant is written from.
        strategy: The parent's name.
        out: Directory the files go in; created here.
        shape: A key of `rewrite.SHAPES`.

    Returns:
        How many files and how many bytes. The parent is read once and kept in memory --
        it is at most a few megabytes and five thousand rewrites of it are otherwise five
        thousand reads of the same archive.

        Nothing is verified here on purpose. What was actually written is the manifest's
        question, and it answers it by reading the files back rather than by trusting
        this loop.

        ⚠️ The directory is emptied first, and it has to be. The manifest describes what
        is **on disk**, so a previous, larger batch left in place is silently adopted into
        this one: its files carry no stratum, they join onto nothing, and the count comes
        out wrong in a way that looks like a fabrication fault rather than a stale folder.
    """
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("*.sqx"):
        stale.unlink()
    source = rewrite.members(parent)
    written = 0
    for row in plan.to_dict("records"):
        parts = rewrite.variant(source, row["variant_id"],
                                name_of(strategy, row["variant_id"]),
                                tuples.from_columns(row))
        written += rewrite.save(out / f"{row['variant_id']}.sqx", parts, shape)
    return {"files": len(plan), "bytes": written, "shape": shape}
