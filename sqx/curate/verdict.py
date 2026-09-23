#!/usr/bin/env python3
"""Write a verdict.csv: keep what passes a filter over the metrics export, or drop the names given."""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from core import sqxfile
from core.paths import WORKERS, databank_dir, metrics_export, report_dir
from sqx.curate.apply_verdict import install_of

DROP = "DESCARTAR"
KEEP = "MANTENER"
NAME = "Strategy Name"


def slug(column: str) -> str:
    """The name a metrics column goes by inside a filter expression.

    Args:
        column: Header as SQX exports it, e.g. "# of trades (IS)".

    Returns:
        Lowercase identifier, e.g. "n_of_trades_is", so a filter can be typed without
        quoting: `net_profit_oos > 0 and n_of_trades_is >= 100`.
    """
    return re.sub(r"[^a-z0-9]+", "_", column.replace("#", "n").lower()).strip("_")


def metrics(project: str, databank: str) -> pd.DataFrame:
    """The databank's current metrics export, one row per strategy, columns slugged.

    Args:
        project: Project name.
        databank: Databank name as SQX shows it.

    Returns:
        The export with every column renamed by `slug`, plus `strategy` holding the name
        as SQX has it. SQX writes a trailing `;`, which pandas reads as an unnamed column.
    """
    csv = metrics_export(project, databank) / "metrics.csv"
    if not csv.exists():
        sys.exit(f"no metrics export at {csv}. Run sqx.export.export_metrics first: the "
                 "filter judges that CSV, nothing else.")
    df = pd.read_csv(csv, sep=";", quotechar='"')
    df = df[[c for c in df.columns if not c.startswith("Unnamed")]]
    df.insert(0, "strategy", df[NAME])
    return df.rename(columns={c: slug(c) for c in df.columns if c != "strategy"})


def identities(names: list[str], source: Path) -> dict[str, str]:
    """SHA-256 of each strategy's definition, read from its file.

    Args:
        names: Strategy names.
        source: Databank directory holding their .sqx files.

    Returns:
        Name to identity; "" for a name with no file on disk, which happens when the
        databank is `Auto-sync never` and has not been written yet.
    """
    return {n: sqxfile.identity(source / f"{n}.sqx") if (source / f"{n}.sqx").exists() else ""
            for n in names}


def main() -> None:
    """Judge a databank and write the verdict the curation step applies."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True)
    ap.add_argument("--role", default="master", choices=["master", *sorted(WORKERS)],
                    help="install holding the databank; its files give the identities")
    how = ap.add_mutually_exclusive_group(required=True)
    how.add_argument("--keep", help="pandas expression over the slugged metrics columns; "
                                    "what does not match is DESCARTAR")
    how.add_argument("--drop", nargs="+", metavar="NAME",
                     help="strategy names to mark DESCARTAR, e.g. 'Strategy 11.4.39'")
    how.add_argument("--columns", action="store_true",
                     help="print the column names a --keep expression can use, and stop")
    a = ap.parse_args()

    df = metrics(a.project, a.databank)
    if a.columns:
        print("\n".join(c for c in df.columns if c != "strategy"))
        return
    if a.keep:
        kept = set(df.query(a.keep)["strategy"])
        reason = f"failed: {a.keep}"
    else:
        missing = [n for n in a.drop if n not in set(df.strategy)]
        if missing:
            sys.exit(f"not in the export: {', '.join(missing)}")
        kept = set(df.strategy) - set(a.drop)
        reason = "dropped by name"
    verdict = pd.DataFrame({"strategy": df.strategy})
    verdict["verdict"] = [KEEP if s in kept else DROP for s in verdict.strategy]
    verdict["reason"] = ["" if s in kept else reason for s in verdict.strategy]
    source = databank_dir(a.project, a.databank, install_of(a.role))
    ids = identities(list(verdict.strategy), source)
    verdict["identity"] = [ids[s] for s in verdict.strategy]

    now = datetime.now()
    out = report_dir(a.project, a.databank, now.date().isoformat()) / "curate"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"verdict-{now:%H%M%S}.csv"
    verdict.to_csv(path, index=False)
    dropped = (verdict.verdict == DROP).sum()
    print(f"{a.project}/{a.databank}: {len(verdict)} judged, {len(kept)} kept, {dropped} DESCARTAR")
    print(f"  identity from file on {sum(1 for i in ids.values() if i)} of {len(ids)} "
          f"({source})")
    print(f"  {path}")
    print(f"apply it: python3 -m sqx.curate.apply_verdict --project {a.project} "
          f"--databank {a.databank} --verdict {path} --role {a.role}   # then --apply, stopped")


if __name__ == "__main__":
    main()
