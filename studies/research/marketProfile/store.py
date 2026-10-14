"""Where the profile lives on disk: one file of measures per asset, and the judged tables."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from core.researchpaths import research_profiles_dir
from studies.research.marketProfile.many import Map


def cells() -> Path:
    """The folder of per-asset results, created on first use."""
    path = research_profiles_dir() / "cells"
    path.mkdir(parents=True, exist_ok=True)
    return path


def done() -> list[str]:
    """The assets whose cells are already measured, sorted."""
    return sorted(p.stem for p in cells().glob("*.parquet"))


def save(symbol: str, got: list[dict], meta: dict) -> None:
    """Write one asset's cells: the measure rows as parquet, the rest as JSON beside them.

    Args:
        symbol: Asset name.
        got: What one.run() returned for each of its timeframes.
        meta: The build window, the seed, the config hash and the timings.
    """
    rows = pd.DataFrame([r for g in got for r in g["rows"]])
    rows.to_parquet(cells() / f"{symbol}.parquet", index=False)
    side = {**meta, "context": [g["context"] for g in got],
            "overlap": [o for g in got for o in g["overlap"]]}
    (cells() / f"{symbol}.json").write_text(json.dumps(side, default=float, indent=1),
                                            encoding="utf-8")


def extend(symbol: str, rows: list[dict], meta: dict) -> None:
    """Add measure rows to an asset's stored cells, and the top-up's record to its side file.

    Args:
        symbol: Asset name, already measured.
        rows: Measure rows of the measures it lacked (one.run's `rows`).
        meta: The measures added, their seed, timings and date.
    """
    path = cells() / f"{symbol}.parquet"
    pd.concat([pd.read_parquet(path), pd.DataFrame(rows)], ignore_index=True).to_parquet(
        path, index=False)
    side = cells() / f"{symbol}.json"
    held = json.loads(side.read_text(encoding="utf-8"))
    held.setdefault("top_ups", []).append(meta)
    side.write_text(json.dumps(held, default=float, indent=1), encoding="utf-8")


def load() -> dict[str, Any]:
    """Everything measured so far.

    Returns:
        {"rows": every asset's measure rows, "context": one row per cell, "overlap": one row
        per cell, direction and pair of families, "meta": {symbol: its side file}}.
    """
    names = done()
    meta = {s: json.loads((cells() / f"{s}.json").read_text(encoding="utf-8")) for s in names}
    return {"rows": pd.concat([pd.read_parquet(cells() / f"{s}.parquet") for s in names],
                              ignore_index=True),
            "context": pd.DataFrame([c for m in meta.values() for c in m["context"]]),
            "overlap": pd.DataFrame([o for m in meta.values() for o in m["overlap"]]),
            "meta": meta}


def write(judged: Map, stored: dict) -> Path:
    """The judged map as CSV tables the board reads.

    Args:
        judged: What many.run() returned.
        stored: What load() returned.

    Returns:
        The folder: measures.csv, scores.csv, correlation.csv, context.csv, overlap.csv.
    """
    out = research_profiles_dir()
    for name in ("measures", "scores", "correlation"):
        judged[name].to_csv(out / f"{name}.csv", index=False)
    stored["context"].to_csv(out / "context.csv", index=False)
    stored["overlap"].to_csv(out / "overlap.csv", index=False)
    return out
