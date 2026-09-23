"""What the factory reads: its own settings, the design brief, the known results, where it writes."""

import json
from pathlib import Path

import pandas as pd
import yaml

from core.paths import DATA, variants_dir

HERE = Path(__file__).resolve().parent
ORIGINAL = -1


def load() -> dict:
    """The factory's settings.

    Returns:
        The parsed `config.yaml`, unmodified.
    """
    return yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))


def brief(path: Path) -> dict:
    """One strategy's design brief.

    Args:
        path: A `design_brief_<strategy>.json` written by `strategies/sppUltra`.

    Returns:
        Contract C1 as it stands on disk: the live parameters with their levels, the
        frozen ones with their values, the stratum shares and the target count.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def source(design: dict) -> Path:
    """The parent `.sqx` every variant is written from.

    Args:
        design: A parsed brief. Its `source` field is the export's `spp/` folder.

    Returns:
        Path to the strategy file the same export carries beside that folder. The parent
        is taken from the export and not from the databank so that the tuple in the brief
        and the file being rewritten come from one snapshot.
    """
    return Path(design["source"]).parent / "strategies" / f"{design['strategy']}.sqx"


def known(design: dict) -> pd.DataFrame:
    """Tuples whose result SQX has already computed, for the canaries.

    Args:
        design: A parsed brief.

    Returns:
        One row per SPP permutation: a column per permuted parameter, plus `NetProfit`
        and `NumberOfTrades`. The original sits at permutation -1 in the parameter table
        and has no row in the results table, so it is dropped here and handled as the
        origin instead.

        Only the parameter columns plus two of the 152 statistics are read: the table is
        Parquet, so asking for those columns costs their bytes and nothing else. The full
        grid is `strategies/sppUltra`'s business and is not needed to pick a control.
    """
    folder, strategy = Path(design["source"]), design["strategy"]
    names = (pd.read_parquet(folder / "runs.parquet").set_index("strategy")
             .loc[strategy, "parameters"].split())
    frame = pd.read_parquet(folder / "spp.parquet",
                            columns=["strategy", "permutation", *names, "NetProfit",
                                     "NumberOfTrades"],
                            filters=[("strategy", "==", strategy)])
    return frame.drop(columns="strategy").set_index("permutation")


def out_dir(project: str, strategy: str) -> Path:
    """Where one strategy's variants and their manifest land.

    Args:
        project: Project name on the master.
        strategy: Strategy name as SQX writes it.

    Returns:
        Path under the data root. There is one current design per strategy and rebuilding
        replaces it, so "which of these five thousand files is the real batch" cannot
        arise. Heavy output never goes in the repository.
    """
    return variants_dir(project, strategy)
