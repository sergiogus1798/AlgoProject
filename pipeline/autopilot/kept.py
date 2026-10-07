"""What the funding module keeps of each strategy that passed the WFM: its oos1 floating curve and risk numbers."""

import json

import pandas as pd

from core.paths import DATA, KEPT, report_dir
from pipeline.autopilot import survivors
from studies.screening.gate import inputs

FACTS = ("oos_worst_day_r", "dd_esperado_p95_r", "oos_net_per_year_r")


def rows(card: pd.DataFrame, passed: list[str], equity: pd.DataFrame, risk: float
         ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Join each strategy that passed the WFM to its step-8 scorecard row, and cut its oos1 curve.

    Args:
        card: The gate's scorecard, `identity` as index, with a `strategy` column (file name).
        passed: Names of the strategies in the WFM databank.
        equity: The gate harvest's `equity.parquet`: `day`, `identity`, `equity`, `sample`.
        risk: 1R in account currency.

    Returns:
        (`kept`: one row per strategy found — `strategy`, `identity` and `FACTS` —, `curve`:
        `strategy`, `day`, `equity_r`, SQX's daily-low equity of oos1 in R, from 0). A strategy
        absent from the scorecard, or without a curve, gets no row: never a guess.

    Raises:
        ValueError: A name is held twice by the scorecard, so the link is not unique.
    """
    named = card.reset_index()
    named = named[named["strategy"].isin(passed)]
    if named["strategy"].duplicated().any():
        raise ValueError("el scorecard repite un nombre: la fila del paso 8 no es única")
    kept = named.reindex(columns=["strategy", "identity", *FACTS])
    oos = equity[equity["sample"] == "OOS"]
    after = oos[oos["day"] > equity.loc[equity["sample"] == "IS", "day"].max()]
    wide = after.pivot(index="day", columns="identity", values="equity")
    wide = wide.diff().fillna(0.0).cumsum() / risk
    kept = kept[kept["identity"].isin(wide.columns)]
    curve = wide[kept["identity"]].set_axis(kept["strategy"], axis=1)
    curve = curve.rename_axis("strategy", axis=1).stack().rename("equity_r").reset_index()
    return kept.reset_index(drop=True), curve


def save(project: str, databank: str) -> str:
    """Write `<KEPT>/<project>/kept.csv` and `curves.parquet` for the newest WFM reading.

    Args:
        project: Project name.
        databank: The WFM output databank (`blind.bank`).

    Returns:
        One line: how many were kept and how many of the WFM's were left out.
    """
    read = sorted(report_dir(project, databank, "x").parent.glob("*/wfm/verdict.csv"))[-1]
    passed = list(pd.read_csv(read)["strategy"])
    gate = max((DATA / "reports" / project).glob("*/*/gate/scorecard.parquet"),
               key=lambda f: f.parent.parent.name).parent        # the newest day
    card = pd.read_parquet(gate / "scorecard.parquet")
    harvest = json.loads((gate / "manifest.json").read_text())["source"]["harvest"]
    equity = pd.read_parquet(f"{harvest}/equity.parquet")
    risk = inputs.market(survivors.about(project)["feed"])["risk"]
    kept, curve = rows(card, passed, equity, risk)
    out = KEPT / project
    out.mkdir(parents=True, exist_ok=True)
    kept.to_csv(out / "kept.csv", index=False)
    curve.to_parquet(out / "curves.parquet", compression="zstd")
    return f"{len(kept)} guardadas para fondeo en {out}, {len(passed) - len(kept)} sin fila en el paso 8"
