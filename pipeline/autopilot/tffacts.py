"""Step 12's redesigned facts (encargo 47): `crossTF.tf.*`, read from the two files the study writes beside the old reading."""

from collections.abc import Iterable
from pathlib import Path
from typing import cast

import pandas as pd

# A state is a number a rule of criteria.yaml can compare: «>= 1» passes, «>= 0» is limbo or better.
STATE = {"pass": 1.0, "limbo": 0.0, "fail": -1.0}
MOTHER_COLUMNS = (
    "state",
    "phase1",
    "t1",
    "t2a",
    "t2b",
    "t3",
)  # tf_mothers.csv, as `tf.<col>`
NAMES = {"mother", "sibling", "timeframe", "role"}  # tf_siblings.parquet's keys


def encode(column: pd.Series) -> pd.Series:
    """A column as numbers: pass/limbo/fail as `STATE`, booleans as 0/1, any other text as NaN."""
    return cast(
        pd.Series,
        pd.to_numeric(
            column.map(lambda v: STATE.get(v, v) if isinstance(v, str) else v),
            errors="coerce",
        ),
    )


def rows(folder: Path) -> list[dict]:
    """The facts of one run's `tf_mothers.csv` and `tf_siblings.parquet`, one set per MOTHER.

    Args:
        folder: The study's result folder. A file that is not there gives no facts — the
            run was made before the redesign — never an exception.

    Returns:
        Fact rows (`study, strategy, identity, key, value`), keys without the `crossTF.`:
        `tf.state`, `tf.phase1`, `tf.t1`, `tf.t2a`, `tf.t2b`, `tf.t3` (states as `STATE`;
        a state the study could not say is no fact) and `tf.<TF>.<column>`, every numeric
        column of the mother's sibling on timeframe <TF> (`z_delta`, `z_build`, `ret`,
        `t2a`…). A mother with no sibling row on <TF> has no `tf.<TF>.*` facts.
    """
    out = []

    def add(key: str, values: pd.Series, names: Iterable[str]) -> None:
        """One key for every mother whose value is a number."""
        out.extend(
            {
                "study": "crossTF",
                "strategy": m,
                "identity": "",
                "key": key,
                "value": float(v),
            }
            for m, v in zip(names, values)
            if v == v
        )

    if (folder / "tf_mothers.csv").exists():
        mothers = pd.read_csv(folder / "tf_mothers.csv", dtype=object)
        for col in MOTHER_COLUMNS:
            add(
                f"tf.{col}",
                encode(cast(pd.Series, mothers[col])),
                cast(pd.Series, mothers["strategy"]),
            )
    if (folder / "tf_siblings.parquet").exists():
        siblings = pd.read_parquet(folder / "tf_siblings.parquet")
        for tf, part in siblings.groupby("timeframe", sort=True):
            for col in part.columns.difference(NAMES, sort=False):
                add(
                    f"tf.{tf}.{col}",
                    encode(cast(pd.Series, part[col])),
                    cast(pd.Series, part["mother"]),
                )
    return out
