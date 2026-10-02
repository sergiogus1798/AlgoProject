"""Load a metrics export and work out which of its columns pair in-sample against out-of-sample."""

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from core.paths import DATA, metrics_export
from core.surface import dedupe

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


def source(project: str, databank: str) -> tuple[dict[str, np.ndarray], list[str], Path]:
    """The population's IS and OOS metrics, from wherever they live together.

    Args:
        project: Project name.
        databank: The databank studied, either spelling.

    Returns:
        (columns, names, file read). A workflow retest (`OOS`) carries its IS columns empty —
        the IS is its build's (`Results`) — so the newest harvest whose `oos_databank` is this
        one, the two joined by identity, is read instead of the metrics export (📓 2026-09-30:
        «Panel IS/OOS» found one IS metric, «Param Count», and Filtros candidatos none).
    """
    same = databank.replace(" ", "_")
    joined = sorted((m.parent for m in (DATA / "harvest" / project).glob("*/*/manifest.json")
                     if json.loads(m.read_text(encoding="utf-8"))["source"].get(
                         "oos_databank", "").replace(" ", "_") == same),
                    key=lambda f: f.name)
    if not joined:
        path = metrics_export(project, databank) / "metrics.csv"
        return (*load(path), path)
    frame = pd.read_parquet(joined[-1] / "metrics.parquet")
    columns = {c.replace(" [IS]", IS).replace(" [OOS]", OOS): frame[c].to_numpy(float)
               for c in frame.columns if c.endswith(("[IS]", "[OOS]"))
               and pd.api.types.is_numeric_dtype(frame[c])}
    return columns, list(frame["strategy"].astype(str)), joined[-1] / "metrics.parquet"


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


def deduplicated(columns: dict[str, np.ndarray],
                 names: list[str]) -> tuple[dict[str, np.ndarray], list[str], int]:
    """Drop rows that are another strategy's trade list under a different name.

    `metrics.csv` carries no trade list to hash (`studies/CLAUDE.md`'s first trap: 45 of 231
    strategies once shared trades under different `.sqx` hashes), so identity here is
    approximated by agreement on every OOS metric at once -- the same test
    `core.surface.dedupe` uses for an SPP grid's inert parameters, at full column width so an
    unrelated pair matching by chance is not a real risk.

    Args:
        columns: Numeric columns from load.
        names: Strategy names in row order, from load.

    Returns:
        (columns, names, dropped): the same shapes with duplicate rows removed (first of each
        group kept) and how many rows that was. 0 when the export carries no varying OOS
        metric to check against.
    """
    oos = measured(columns, OOS)
    frame = pd.DataFrame({k: columns[k] for k in oos}, index=range(len(names)))
    kept = dedupe.distinct(frame, keys=tuple(oos)).index if oos else frame.index
    dropped = len(names) - len(kept)
    rows = kept.to_numpy()
    return ({k: v[rows] for k, v in columns.items()}, [names[i] for i in kept], dropped)


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
