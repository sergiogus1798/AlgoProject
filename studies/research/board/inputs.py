"""What the board reads: its config, the profile's scores, the sweep's best variants, the memory."""

from pathlib import Path

import pandas as pd
import yaml

from core.researchpaths import research_profiles_dir
from studies.research.memory import attempts, ideas, queries
from studies.research.memory.sources import CONFIG as MEMORY

CONFIG = yaml.safe_load((Path(__file__).parent / "config.yaml").read_text(encoding="utf-8"))
CELL = ["symbol", "timeframe", "direction", "family"]


def scores() -> pd.DataFrame:
    """The profile's `scores.csv`: one row per symbol × timeframe × direction × family."""
    return pd.read_csv(research_profiles_dir() / "scores.csv")


def sweep() -> pd.DataFrame:
    """The sweep's `best.csv`: the best exit/parameter variant per cell-family; empty if not run."""
    path = research_profiles_dir() / "sweep" / "best.csv"
    return pd.read_csv(path) if path.exists() else pd.DataFrame(columns=CELL)


def memory() -> dict:
    """The memory, recomputed from its sources (50 ms): nothing stale is ever read.

    Returns:
        `attempts` (one row per project run), `ideas` (the index), `by_family`
        (`queries.survivors_by_family`) and `spent` (`queries.ideas_spent`).
    """
    index = ideas.index()
    rows = attempts.table({i["idea"] for i in index})
    index = ideas.index(rows)
    return {"attempts": rows, "ideas": index, "by_family": queries.survivors_by_family(rows),
            "spent": queries.ideas_spent(index)}


def asset_class(symbol: str) -> str:
    """The asset's class in the memory's table (metal, energy, index, forex)."""
    return MEMORY["asset_class"][symbol]


def ideas_spent(spent: list[dict], symbol: str, timeframe: str, direction: str,
                family: str) -> int:
    """Ideas already proposed for one cell — the «ya van K ideas» of the proposal.

    An idea that never became a template has no family yet (family ''): it was a look at that
    asset, timeframe and direction, so it counts against every family there.
    """
    return sum(r["ideas"] for r in spent
               if (r["symbol"], r["timeframe"], r["direction"]) == (symbol, timeframe, direction)
               and r["family"] in ("", family))


def attempts_in(rows: list[dict], symbol: str, timeframe: str, direction: str,
                family: str) -> int:
    """Project runs of that family's templates on that asset, timeframe and direction."""
    return sum(queries.cell(r) == (symbol, timeframe, direction, family) for r in rows)
