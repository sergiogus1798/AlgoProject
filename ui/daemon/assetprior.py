"""How each strategy family suits an asset: the owner's prior judged by the market profile."""

from functools import lru_cache

import pandas as pd

from core.researchpaths import research_profiles_dir
from studies.research.marketProfile import priorview

VERDICTS = ["bien", "sin_confirmar", "mal"]   # the order the Características panel lists them in


@lru_cache(maxsize=1)
def measured(stamp: tuple) -> dict[str, dict[str, dict[str, str]]]:
    """What the market profile measured for every asset, family and timeframe.

    Args:
        stamp: The mtimes of the profile's two files: the cache key, so a new profile is read.

    Returns:
        Asset → family → timeframe → `priorview` flag (a favor / sin evidencia / en contra).
        Each asset's rows are cut out once: asking the whole table 384 times cost 4.7 s.
    """
    folder = research_profiles_dir()
    rows = priorview.graded(pd.read_csv(folder / "measures.csv"))
    variants = pd.read_parquet(folder / "sweep" / "variants.parquet")
    out: dict = {}
    for symbol, mine in rows.groupby("symbol"):
        swept = variants[variants["symbol"] == symbol]
        out[symbol] = {f: {t: flag for t in priorview.TIMEFRAMES
                           if (flag := flag_of(mine, swept, symbol, t, f))}
                       for f in priorview.PRIOR["families"]}
    return out


def flag_of(rows: pd.DataFrame, variants: pd.DataFrame, symbol: str, timeframe: str,
            family: str) -> str | None:
    """One cell's `priorview` flag, or None where the profile measured nothing for it."""
    try:
        return priorview.state(rows, variants, symbol, timeframe, family)["flag"]
    except IndexError:      # no naked measure in that cell: `state` reads the first row
        return None


def prior(symbol: str) -> list[dict]:
    """How each family suits this asset: the owner's prior, judged by what was measured.

    Returns:
        [{family, level (Alta/Media/Baja, None when the prior skips the asset), long_only,
        favour, against (timeframes measured for and against), verdict}], best first. The
        verdict is the measurement's, not the prior's (owner, 2026-10-04: the prior alone read
        «va muy bien» for four families of every yen cross): `bien` with a timeframe measured
        for, `mal` with one against and none for or a prior of Baja, `sin_confirmar` otherwise.
        [] for an asset with neither a prior nor a profile.
    """
    folder = research_profiles_dir()
    files = [folder / "measures.csv", folder / "sweep" / "variants.parquet"]
    seen = measured(tuple(f.stat().st_mtime_ns for f in files)) if all(
        f.exists() for f in files) else {}
    known = symbol in priorview.PRIOR["matrix"]
    if not known and symbol not in seen:
        return []
    rows = []
    for f in priorview.PRIOR["families"]:
        flags = seen.get(symbol, {}).get(f, {})
        level = priorview.matrix(symbol, f) if known else None
        favour = [t for t, flag in flags.items() if flag == priorview.FOR]
        against = [t for t, flag in flags.items() if flag == priorview.AGAINST]
        verdict = "bien" if favour else ("mal" if against or level == "Baja" else "sin_confirmar")
        rows.append({"family": f, "level": level, "long_only": priorview.long_only(symbol, f),
                     "favour": favour, "against": against, "verdict": verdict})
    levels = [*priorview.LEVEL.values(), None]
    return sorted(rows, key=lambda r: (VERDICTS.index(r["verdict"]), -len(r["favour"]),
                                       levels.index(r["level"])))
