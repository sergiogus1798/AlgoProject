"""Load a metrics export and work out which of its columns pair in-sample against out-of-sample."""

import csv
from pathlib import Path

import numpy as np

IS, OOS = " (IS)", " (OOS)"


def load(path: Path) -> tuple[dict[str, np.ndarray], list[str]]:
    """Read a metrics export into numeric columns.

    Args:
        path: The ";"-separated CSV written by `python3 -m sqx.export.export_metrics`.

    Returns:
        Every numeric column keyed by its full header, and the strategy names in row
        order. Text columns (Strategy Name, Filters result, TimeFrame) fall away.
    """
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig"), delimiter=";"))
    columns = {}
    for key in rows[0]:
        # A column is numeric or it is not; the conversion is the test.
        try:
            columns[key] = np.array([float(r[key]) for r in rows])
        except ValueError:
            pass
    return columns, [r["Strategy Name"] for r in rows]


def measured(columns: dict[str, np.ndarray], suffix: str) -> list[str]:
    """Every metric the export measures at one sample type.

    Args:
        columns: Numeric columns from load.
        suffix: IS or OOS.

    Returns:
        Full column names, sorted. A column SQX leaves at one value across the whole
        population is excluded: it has no correlation to compute and would read as NaN.
    """
    return sorted(k for k, v in columns.items() if k.endswith(suffix) and v.std() > 0)


def paired(columns: dict[str, np.ndarray]) -> list[str]:
    """Metrics the export carries, and varies, at both sample types.

    Args:
        columns: Numeric columns from load.

    Returns:
        Bare metric names without either suffix, sorted.
    """
    varying = set(measured(columns, IS)) | set(measured(columns, OOS))
    return sorted(k[: -len(IS)] for k in varying
                  if k.endswith(IS) and f"{k[: -len(IS)]}{OOS}" in varying)
