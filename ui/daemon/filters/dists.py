"""The stored `distribution` blocks of a project's strategies, by identity, for the median mode."""

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

from core.paths import DATA
from ui.daemon.results import catalogue

# Central intervals the stored percentiles can give (blocks.PERCENTILES: 1 5 10 25 50 75 90 95 99).
PAIRS = {50: (25, 75), 80: (10, 90), 90: (5, 95), 98: (1, 99)}


@lru_cache(maxsize=4096)
def blocks_of(path: str, _mtime: float) -> tuple[str | None, tuple[dict, ...]]:
    """One per-strategy result's identity and its distribution blocks, slimmed.

    Returns:
        (identity, blocks): each {title, unit, real, percentiles, series} — `series` the
        first and last sample's label, median, bins and density when the block has two.
    """
    got = json.loads(Path(path).read_text(encoding="utf-8"))
    out = []
    for tab in got.get("tabs", []):
        for b in tab.get("blocks", []):
            if b.get("kind") != "distribution":
                continue
            series = b.get("series") or []
            out.append({"title": b["title"], "unit": b.get("unit", ""), "real": b.get("real"),
                        "percentiles": b.get("percentiles", {}), "bins": b.get("bins", []),
                        "series": [{k: s[k] for k in ("label", "median", "counts")}
                                   for s in (series[0], series[-1])] if len(series) > 1
                        else None})
    return got.get("identity"), tuple(out)


def key(study: str, block: dict) -> str:
    """The metric key a distribution is offered under: `dist:<study>/<title> [<unit>]`."""
    return f"dist:{study}/{block['title']}" + (f" [{block['unit']}]" if block["unit"] else "")


def project(project_name: str, refused: set[str]) -> dict[str, dict[str, dict]]:
    """Every distribution block of a project's per-strategy results, the newest day winning.

    Args:
        project_name: Project name.
        refused: Study keys whose figures read OOS2; their blocks are never offered.

    Returns:
        identity → {metric key: block}. Across databanks, since a retest that keeps the
        build's identity (mcRetest) is the same strategy.
    """
    out: dict[str, dict[str, dict]] = {}
    days: dict[tuple[str, str], str] = {}
    root = DATA / "reports" / project_name
    for folder in sorted(root.glob("*/*/*")):
        study = folder.name
        if study not in catalogue.STUDIES or study in refused or not folder.is_dir():
            continue
        for path in folder.glob("estrategias/*.json"):
            identity, blocks = blocks_of(str(path), path.stat().st_mtime)
            if not identity or days.get((identity, study), "") > folder.parent.name:
                continue
            days[(identity, study)] = folder.parent.name
            mine = out.setdefault(identity, {})
            for b in blocks:
                mine.setdefault(key(study, b), {**b, "study": study})
    return out


def quantile(bins: list[float], density: list[float], q: float) -> float:
    """A quantile read off a density histogram, linear inside its bin."""
    edges = np.asarray(bins, dtype=float)
    mass = np.asarray(density, dtype=float) * np.diff(edges)
    cdf = np.concatenate([[0.0], np.cumsum(mass) / mass.sum()])
    return float(np.interp(q, cdf, edges))


def inside(block: dict, width: int) -> bool | None:
    """Whether the median falls inside the block's central `width` % interval.

    Args:
        block: What `project` returned for one strategy and metric.
        width: 50, 80, 90 or 98.

    Returns:
        With two samples (IS against OOS): the last sample's median against the first
        sample's interval. With one: the real value (the backtest that happened) against
        the draws' interval. None when the block has neither a second sample nor a real value.
    """
    lo_q, hi_q = PAIRS[width]
    if block["series"]:
        first, last = block["series"]
        lo, hi = (quantile(block["bins"], first["counts"], q / 100) for q in (lo_q, hi_q))
        point = last["median"]
    else:
        lo, hi, point = block["percentiles"][str(lo_q)], block["percentiles"][str(hi_q)], block["real"]
    return None if point is None else lo <= point <= hi


def reading(block: dict | None) -> str:
    """What the median mode compares for this metric, in words, for the dropdown and the ledger."""
    if block is not None and block["series"]:
        a, b = block["series"]
        return f"mediana de {b['label']} en el intervalo de {a['label']}"
    return "valor real en el intervalo de las re-ejecuciones"
