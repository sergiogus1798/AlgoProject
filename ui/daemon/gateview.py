"""What the gate zone draws: every cosecha, one gate's funnel and scorecard, one strategy's curve."""

import json
from pathlib import Path

import pandas as pd

from core import assetdata
from core.paths import DATA
from studies.screening.gate.inputs import config
from ui.daemon.runs import guess_asset

META = ("name", "kind", "why")

# The IS/OOS pairs the strategy sheet shows, in reading order. The rest of the 38 columns
# stay in the parquet for whoever wants them.
PAIRS = ("Net profit", "# of trades", "Profit factor", "Sharpe Ratio", "Ret/DD Ratio",
         "Max DD %", "Winning Percent", "R Expectancy", "Stability", "PSR")


def manifest(folder: Path) -> dict:
    """A folder's manifest, or `{}` when nobody signed it.

    Args:
        folder: Any dated export folder.

    Returns:
        The decoded JSON.
    """
    f = folder / "manifest.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def screens() -> list[dict]:
    """The gate's screens as `studies/screening/gate/config.yaml` states them today.

    Returns:
        One dict per screen: name, kind, why and `thresholds`, the rest of its row.
    """
    return [{**{k: s[k] for k in META},
             "thresholds": {k: v for k, v in s.items() if k not in META}}
            for s in config([])["screens"]]


def judged(harvest: Path) -> tuple[str, dict]:
    """The newest gate report over one harvest.

    Args:
        harvest: The harvest folder.

    Returns:
        The report's day and its manifest, or `("", {})`. A report is dated the day it ran,
        not the day of the harvest it judged, so the manifest's `source.harvest` is what
        ties the two — and a harvest judged twice shows its latest judgement.
    """
    project, databank = harvest.parts[-3:-1]
    for folder in sorted((DATA / "reports" / project / databank).glob("*/gate"), reverse=True):
        m = manifest(folder)
        if m.get("source", {}).get("harvest") == str(harvest):
            return folder.parts[-2], m
    return "", {}


def harvests() -> list[dict]:
    """Every cosecha in the data root, and whether the gate has judged it.

    Returns:
        One dict per harvest day: project, databank, day, the harvest's counts, `gate` —
        the newest report's counts over it, or None — `report_day`, when that report ran,
        and `asset`: the one whose feed the report was priced with, else the one the
        project's name says, else None. Newest first.
    """
    out = []
    for f in sorted((DATA / "harvest").glob("*/*/*/metrics.parquet"), reverse=True):
        project, databank, day = f.parts[-4:-1]
        m = manifest(f.parent)
        report_day, g = judged(f.parent)
        feed = g.get("source", {}).get("feed")
        out.append({"project": project, "databank": databank, "day": day,
                    "counts": m.get("counts", {}), "oos_databank": m.get("source", {})
                    .get("oos_databank", "?"), "gate": g.get("counts") if g else None,
                    "report_day": report_day,
                    "asset": (assetdata.symbol_for(feed) if feed else None)
                    or guess_asset(project)})
    return out


def gate(project: str, databank: str, day: str) -> dict:
    """One gate report: its funnel, its source and its scorecard.

    Args:
        project: Project name.
        databank: The build databank.
        day: The report's day, as `harvests()` gives it in `report_day`.

    Returns:
        `source` from the report's manifest, `funnel` rows, `screens` with the thresholds
        printed, and `rows` — one per strategy with identity, both names, where it died,
        whether it survives and every screen's value, pass and note.
    """
    folder = DATA / "reports" / project / databank / day / "gate"
    m = manifest(folder)
    funnel = pd.read_csv(folder / "funnel.csv").to_dict("records")
    scores = pd.read_parquet(folder / "scorecard.parquet").reset_index()
    rows = scores.astype(object).where(scores.notna(), None).to_dict("records")
    return {"source": m["source"], "date": m["date"], "command": m["command"],
            "funnel": funnel, "screens": screens(), "rows": rows}


def strategy(project: str, databank: str, day: str, identity: str) -> dict:
    """One strategy of a harvest: its paired metrics and its daily curve, both sides.

    Args:
        project: Project name.
        databank: The build databank.
        day: The harvest day.
        identity: SHA-256 of the strategy's normalised XML, the harvest's index.

    Returns:
        `metrics` — `[label, IS, OOS]` for every pair of `PAIRS` — and `curve`, the daily
        P&L of each sample as `{sample: {days: [...], equity: [...]}}`; each side starts
        at zero because each was its own backtest.
    """
    folder = DATA / "harvest" / project / databank / day
    # to_dict boxes numpy scalars into Python ones, which is what the JSON layer accepts.
    m = pd.read_parquet(folder / "metrics.parquet").loc[identity].to_dict()
    metrics = [[p, m.get(f"{p} [IS]"), m.get(f"{p} [OOS]")] for p in PAIRS]
    e = pd.read_parquet(folder / "equity.parquet")
    e = e[e["identity"] == identity]
    curve = {s: {"days": b["day"].dt.strftime("%Y-%m-%d").tolist(),
                 "equity": b["equity"].round(2).tolist()} for s, b in e.groupby("sample")}
    return {"metrics": [[p, None if pd.isna(a) else a, None if pd.isna(b) else b]
                        for p, a, b in metrics], "curve": curve}
