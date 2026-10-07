"""The version of each mother that will be traded: her step-24 variant at the owner's stop percentile, read by step 25."""

from datetime import date
from pathlib import Path

import pandas as pd

from core.manifest import write as write_manifest
from core.paths import DATA, harvest_dir
from ledger import thresholds
from pipeline.autopilot import call, survivors
from sqx.variants import legs as legmod

KEY = "portfolio.funded.stop_percentile"     # owner, 2026-09-30: one rule for every strategy
TAG = "stopgrid"                             # the export tag of step 24's batches
# The export labels build as IS and oos1 as OOS; `edgeCost` reads only the oos1 rows
# (encargo 44). oos2 is not its to read (`assets/_policy.yaml`).
SAMPLE = {"build": "IS", "oos1": "OOS"}
COLUMNS = ["Type", "Open time", "Open price", "Size", "Close time", "Close price",
           "Profit/Loss", "Balance", "Sample type", "Close type", "MAE ($)", "MFE ($)"]


def batch(project: str) -> Path | None:
    """The newest step-24 batch that reached its second pass: the folder holding its manifest."""
    root = DATA / "atrCalculator" / project
    found = [*root.glob("*/pass2/manifest.parquet"), *root.glob("pass2/manifest.parquet")]
    return max(found, key=lambda f: f.stat().st_mtime).parent if found else None


def stops(project: str, mothers: pd.DataFrame) -> tuple[list[dict], list[str]]:
    """Each mother's variant at X = the ledger's percentile of her IS winners' MAE/ATR.

    Args:
        project: Project name.
        mothers: `survivors.mothers`.

    Returns:
        The mothers that have one — `strategy`, `identity` (the mother's), `variant`, `x`,
        `percentile` and `sqx`, the grafted file step 24 fabricated — and the names of
        those that do not: no batch, a mother absent from it, or a study run without that
        percentile. Nothing is chosen here: the percentile is the owner's, the X step 24's.
    """
    wanted, folder = thresholds.value(KEY), batch(project)
    if folder is None:
        return [], list(mothers["strategy"])
    grid = pd.read_parquet(folder / "manifest.parquet")
    grid = grid[(grid["percentile"] == wanted) & (grid["step"] == 0)].set_index("strategy")
    found = [{"strategy": m.strategy, "identity": m.identity, "percentile": int(wanted),
              "variant": grid.at[m.strategy, "variant_id"], "x": float(grid.at[m.strategy, "x"]),
              "sqx": str(folder / "sqx" / f"{grid.at[m.strategy, 'variant_id']}.sqx")}
             for m in mothers.itertuples() if m.strategy in grid.index]
    return found, [m for m in mothers["strategy"] if m not in grid.index]


def export(project: str, databank: str, folder: Path) -> pd.DataFrame:
    """One leg's newest step-24 export, refused unless it is this batch's second pass.

    A variant's name (`S00V014`) is only its place in its own batch, and a retested copy
    does not keep the fabricated file's identity, so the export is tied to the batch by
    what is left: it was written after the batch ran, and holds as many strategies.
    """
    found = sorted((DATA / "raw" / project / databank).glob(f"*/{TAG}/trades.parquet"))
    if not found:
        raise SystemExit(f"{databank}: ningún export «{TAG}» del paso 24")
    names = pd.read_csv(found[-1].with_name("identity.csv"))
    if (found[-1].stat().st_mtime < (folder / "ran.json").stat().st_mtime
            or len(names) != len(pd.read_parquet(folder / "manifest.parquet", columns=["x"]))):
        raise SystemExit(f"{found[-1]} no es el export de la pasada 2 de {folder}: no se lee")
    return pd.read_parquet(found[-1])


def harvest(project: str, picked: list[dict], who: dict) -> str:
    """The traded versions' trades in the shape step 25 reads: a cosecha of its own.

    Args:
        project: Project name.
        picked: `stops`' first list.
        who: `survivors.about`.

    Returns:
        The name it is filed under, `Stop_p<percentile>`: `harvest/<project>/<name>/<day>/`
        with `trades.parquet` (the main market only, `sample` IS for build and OOS for
        oos1), `metrics.parquet` and a manifest naming each variant. Each row is keyed by the
        MOTHER's identity and name, so step 25's facts join her file in the databank; the
        grafted file's own identity is in `finalistas.json`.
    """
    folder, by = batch(project), {p["variant"]: p for p in picked}
    parts = []
    for leg in legmod.legs():
        if leg["segment"] in SAMPLE:
            got = export(project, leg["databank"], folder)
            got = got[got["strategy"].isin(by) & (got["Symbol"] == who["feed"])]
            parts.append(got[COLUMNS].assign(
                identity=got["strategy"].astype(str).map(lambda v: by[v]["identity"]),
                sample=SAMPLE[leg["segment"]]))
    name = f"Stop_p{picked[0]['percentile']}"
    out = harvest_dir(project, name, date.today().isoformat())
    out.mkdir(parents=True, exist_ok=True)
    pd.concat(parts, ignore_index=True).to_parquet(out / "trades.parquet", index=False)
    names = [p["strategy"] for p in picked]
    pd.DataFrame({"strategy_build": names, "strategy": names, "TimeFrame [IS]": who["timeframe"]},
                 index=pd.Index([p["identity"] for p in picked], name="identity")
                 ).to_parquet(out / "metrics.parquet")
    write_manifest(out, {"project": project, "batch": str(folder), "feed": who["feed"],
                         "variants": {p["strategy"]: p["variant"] for p in picked}},
                   "pipeline.autopilot.traded.harvest", {"trades.parquet": sum(map(len, parts))})
    return name


def edge(project: str, mothers: pd.DataFrame) -> str:
    """Step 25: edge per cost of each mother's traded version, with the stop on.

    Returns:
        How many were read, and the mothers left out for lack of a step-24 stop, by name.

    Raises:
        survivors.Done: No mother has one.
    """
    picked, out = stops(project, mothers)
    if not picked:
        raise survivors.Done("ninguna madre tiene stop del paso 24 al percentil "
                             f"{thresholds.value(KEY)}: no hay versión que operar")
    who = survivors.about(project)
    name = harvest(project, picked, who)
    for p in picked:
        call.run(["-m", "studies.readings.edgeCost.report", "--project", project, "--databank",
                  name, "--feed", who["feed"], "--strategy", p["strategy"]])
    return (f"edgeCost de {len(picked)} versión(es) con stop p{picked[0]['percentile']} "
            f"({name})" + (f"; SIN stop, fuera: {', '.join(out)}" if out else ""))
