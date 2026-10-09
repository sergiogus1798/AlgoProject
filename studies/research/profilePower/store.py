"""Where the power study lives on disk: the replications, and the judged tables."""

from pathlib import Path

import pandas as pd

from core.researchpaths import research_profiles_dir

KEY = ["symbol", "timeframe", "measure", "direction", "effect_planted", "rep", "how"]


def folder() -> Path:
    """`AlgoData/research/power/`, created on first use."""
    path = research_profiles_dir().parent / "power"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runs(cut: float, draws: int) -> pd.DataFrame:
    """The replications stored so far that were stopped against this cut and this count."""
    path = folder() / "runs.parquet"
    if not path.exists():
        return pd.DataFrame(columns=KEY)
    old = pd.read_parquet(path)
    return old[(old["cut"] == cut) & (old["draws"] == draws)]


def save(rows: pd.DataFrame) -> None:
    """Write the replications, replacing the file whole through a temp beside it."""
    tmp = folder() / "runs.parquet.tmp"
    rows.to_parquet(tmp, index=False)
    tmp.replace(folder() / "runs.parquet")


def write(tables: dict[str, pd.DataFrame]) -> Path:
    """Each judged table as `<name>.csv`; returns the folder."""
    for name, table in tables.items():
        table.to_csv(folder() / f"{name}.csv", index=False)
    return folder()
