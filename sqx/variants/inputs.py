"""What the factory reads: its own settings, the design brief, the known results, where it writes."""

import json
from pathlib import Path

import pandas as pd
import yaml

from core.paths import DATA

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

        Only four columns of a 40 MB file are read. The full grid, all 154 columns of it,
        is `strategies/sppUltra`'s business and is not needed to pick a control.
    """
    folder, strategy = Path(design["source"]), design["strategy"]
    params = pd.read_csv(folder / "permutation_params.csv")
    results = pd.read_csv(folder / "permutations.csv",
                          usecols=["strategy", "permutation", "NetProfit", "NumberOfTrades"])
    wide = params[params["strategy"] == strategy].pivot(
        index="permutation", columns="parameter", values="value")
    measured = results[results["strategy"] == strategy].set_index("permutation")
    return wide.join(measured.drop(columns="strategy"), how="inner")


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
    return DATA / "variants" / project / strategy.replace(" ", "_")
