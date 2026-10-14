"""The cross-TF rows with the T0-T4 reading beside the old one: `tf_*` columns, read from the study's two new files."""

import csv
import math
from pathlib import Path

import pandas as pd

# What the window shows of tf_siblings.parquet (per sibling timeframe) and tf_mothers.csv (per
# mother, on every one of her rows), under a `tf_` prefix; the helpers in ui/text/columnhelp_fields.
SIBLING = (
    "t0",
    "t1",
    "t2a",
    "t2b",
    "z_frec",
    "z_delta",
    "ret",
    "z_build",
    "ret_build",
    "ret_build_pct",
)
MOTHER = ("state", "phase1", "t3")


def text(value: object) -> str:
    """A cell as the verdict.csv would hold it: empty for no value, 4 decimals for a float."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return f"{value:.4g}" if isinstance(value, float) else str(value)


def merge(rows: list[dict], folder: Path) -> list[dict]:
    """The verdict.csv rows with their `tf_*` columns.

    Args:
        rows: The study's verdict.csv rows, one per mother and timeframe.
        folder: The study's result folder.

    Returns:
        `rows` as they are when the run left no `tf_mothers.csv` / `tf_siblings.parquet` (a
        run made before the redesign); else each with `tf_<column>` for `SIBLING` and `MOTHER`
        — empty where the study had no number, never a zero.
    """
    both = [folder / "tf_mothers.csv", folder / "tf_siblings.parquet"]
    if not all(f.is_file() for f in both):
        return rows
    with both[0].open(encoding="utf-8", newline="") as fh:
        mothers = {r["strategy"]: r for r in csv.DictReader(fh)}
    siblings = (
        pd.read_parquet(both[1]).set_index(["mother", "timeframe"]).to_dict("index")
    )
    return [
        row
        | {
            f"tf_{c}": text(siblings.get((row["mother"], row["timeframe"]), {}).get(c))
            for c in SIBLING
        }
        | {f"tf_{c}": mothers.get(row["mother"], {}).get(c, "") for c in MOTHER}
        for row in rows
    ]
