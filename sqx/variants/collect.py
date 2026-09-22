#!/usr/bin/env python3
"""Join the retested panel back onto the manifest and write contract C3, metrics.parquet."""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

NAME = "Strategy Name"
SENTINEL = 100.0        # |RExpectancy| above this is SQX's own placeholder, not a result
# SQX renames a colliding strategy by appending "(1)", "(2)" ... Stripping it is what lets
# a batch loaded twice still be read; the duplicate rows are then caught as duplicates
# rather than silently joining onto the wrong tuple.
COLLISION = r"\(\d+\)$"


def panel(csv: Path) -> pd.DataFrame:
    """The databank export, as SQX writes it.

    Args:
        csv: The file `sqx.variants.execute` exported.

    Returns:
        One row per retested strategy. Semicolon-separated, and two columns carry a literal
        `?` in their name (`CalmarRatio?`, `AnnualPctReturnDDRatio?`) -- asking for them
        without it returns a column of NaN and no error, so the names are left untouched.
    """
    return pd.read_csv(csv, sep=";")


def join(table: pd.DataFrame, rows: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Attach every variant's design tuple to its measured result.

    Args:
        table: The exported panel.
        rows: The manifest, contract C2.

    Returns:
        The joined frame and what did not line up.

        The key is `variant_id`, because SQX names a databank entry after the **file** --
        `P00000.sqx` comes back as `P00000` -- and not after `<StrategyName>` or
        `ResultsGroup/@ResultName`, both of which say `Strategy 17.9.39 P00000` here. The
        collision suffix SQX appends to a duplicate (`P00000(1)`) is stripped first, so a
        batch loaded twice still joins and its duplicates show up as duplicates.
    """
    back = table[NAME].str.replace(COLLISION, "", regex=True)
    table = table.assign(sqx_returned=table[NAME], **{NAME: back})
    merged = rows.drop(columns="sqx_name").merge(
        table, left_on="variant_id", right_on=NAME, how="left")
    missing = merged.loc[merged[NAME].isna(), "variant_id"].tolist()
    extra = sorted(set(back) - set(rows["variant_id"]))
    return merged, {"missing": missing, "unexpected": extra}


def canaries(merged: pd.DataFrame) -> dict:
    """Whether the controls came back distinguishable from one another.

    Args:
        merged: What `join` returned.

    Returns:
        The count of controls and how many distinct in-sample results they produced.

        **This is the detector for the failure this module exists to prevent.** A variant
        that was never actually run keeps the parent's `SQStats`, so it exports the
        parent's metrics rather than looking empty. If every control returns one identical
        number, nothing ran, and no amount of downstream analysis will say so.
    """
    controls = merged[merged["stratum"].isin(["canary", "origin"])]
    profits = controls["Net profit (IS)"].dropna()
    return {"n": len(controls), "distinct_netprofit": int(profits.nunique()),
            "all_identical": bool(len(profits) > 1 and profits.nunique() == 1)}


def main() -> None:
    """Write C3 beside the batch, and refuse the batch if the controls did not move."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", required=True, type=Path)
    a = ap.parse_args()

    print("PROGRESS 20 leyendo el panel exportado", flush=True)
    rows = pd.read_parquet(a.work / "manifest.parquet")
    merged, gaps = join(panel(a.work / "retest.csv"), rows)

    print(f"PROGRESS 60 {len(merged)} filas unidas", flush=True)
    merged.to_parquet(a.work / "metrics.parquet", index=False)
    found = canaries(merged)
    # Lifted to the top level as well as nested: the pipeline's `must` gate reads one
    # number out of this file by name, and a gate that has to walk into a sub-object is a
    # gate nobody will add the next one to.
    checks = gaps | {"canaries": found, "n": len(merged),
                     "canaries_distinct": found["distinct_netprofit"]}
    (a.work / "collected.json").write_text(
        json.dumps(checks | {"files": [{"path": "metrics.parquet"}],
                             "removable": [str((a.work / "sqx").name)]}, indent=2),
        encoding="utf-8")
    print(f"PROGRESS 100 {checks['canaries']['distinct_netprofit']} resultados distintos "
          f"entre {checks['canaries']['n']} controles", flush=True)
    print(json.dumps(checks, indent=2))

    if checks["canaries"]["all_identical"]:
        sys.exit("los controles devuelven el MISMO resultado: nada se reteseo de verdad, "
                 "las variantes traen las metricas del padre. No uses este lote.")
    if gaps["missing"]:
        sys.exit(f"{len(gaps['missing'])} variantes no volvieron del retest")


if __name__ == "__main__":
    main()
