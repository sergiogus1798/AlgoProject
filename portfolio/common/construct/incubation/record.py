"""The incubation record (M9): the frozen portfolio and comparison, and the contract of the fresh rows."""

import hashlib
import json
from datetime import datetime, timezone as tz
from pathlib import Path

import numpy as np
import pandas as pd

from core import paths

from . import band as band_mod

ROOT = paths.portfolio_dir() / "incubation"
COLUMNS = ["day", "identity", "pnl", "segment", "source"]     # the hand-off's daily.parquet (PLAN §2.2)
SEGMENT = "incubation"
SOURCES = ("paper", "live")     # paper: the monthly SQX retest of the bars after oos2; live: a demo or real account
KNOBS = ("figure", "history", "band")
NOT_RUNNING = ("LA INCUBACIÓN NO ESTÁ EN MARCHA: nada produce todavía sus filas — ni el retest mensual en SQX de las "
               "barras posteriores a oos2, ni una cuenta real o demo conectada a este módulo.")


def missing(cfg: dict) -> list[str]:
    """The comparison knobs the owner has not answered (`incubation.*` still null or not valid)."""
    inc = cfg["incubation"]
    bad = [k for k in KNOBS if inc[k] is None]
    if inc["figure"] is not None and inc["figure"] not in band_mod.FIGURES:
        bad.append(f"figure ({'|'.join(band_mod.FIGURES)})")
    if inc["band"] is not None and not (len(inc["band"]) == 2 and 0 <= inc["band"][0] < inc["band"][1] <= 100):
        bad.append("band ([bajo, alto], percentiles 0..100)")
    return bad


def path(record: dict, daily: pd.DataFrame) -> pd.Series:
    """The portfolio's daily P&L per unit of risk from long rows, at the record's frozen weights.

    Args:
        record: `register()`'s record (`portfolio.weights`, `scale`).
        daily: Rows in `COLUMNS`' shape; a member with no row on a day counts 0 that day.

    Returns:
        day -> P&L, sorted, one entry per day any member has a row.
    """
    factor = pd.Series(record["portfolio"]["weights"]) * pd.Series(record["scale"])
    return (daily["pnl"] * daily["identity"].map(factor)).groupby(daily["day"]).sum().sort_index()


def register(run: Path, comparison: dict, scale: dict[str, float]) -> dict:
    """Freeze a judged run's portfolio and the comparison its fresh days will be read with.

    Args:
        run: A run folder holding `handoff/` (`report.py`'s or `funded_b`'s).
        comparison: `figure`, `history` (segments), `band` -- the owner's, none defaulted.
        scale: identity -> fixed-risk factor (`funded.size_members`).

    Returns:
        The record written to `ROOT/<hash12>/record.json`: `portfolio` (the hand-off's
        `portfolio.json`), `portfolio_hash` (of pool hash, members with versions, weights and
        scale), `scale`, `comparison`, `history` (`from`, `to`, `days`), `registered`.

    Raises:
        SystemExit: The portfolio is already registered (a record is written once), or its
            history has no day on the segments named.
    """
    portfolio = json.loads((run / "handoff" / "portfolio.json").read_text(encoding="utf-8"))
    frozen = {"pool_hash": portfolio["pool_hash"], "weights": portfolio["weights"], "scale": scale,
              "members": sorted((m["identity"], m["version"]) for m in portfolio["members"])}
    digest = hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()
    out = ROOT / digest[:12]
    if (out / "record.json").exists():
        raise SystemExit(f"la cartera {digest[:12]} ya está registrada en {out}: un registro se escribe una vez")
    daily = pd.read_parquet(run / "handoff" / "daily.parquet")
    daily = daily[daily["segment"].isin(comparison["history"])]
    if daily.empty:
        raise SystemExit(f"la cartera no tiene días en {comparison['history']}")
    record = {"schema": 1, "portfolio": portfolio, "portfolio_hash": digest, "scale": scale,
              "comparison": comparison, "registered": datetime.now(tz.utc).isoformat(timespec="seconds"),
              "history": {"from": str(daily["day"].min().date()), "to": str(daily["day"].max().date()),
                          "days": int(daily["day"].nunique())}, "running": False}
    out.mkdir(parents=True)
    daily[COLUMNS].to_parquet(out / "history.parquet", index=False)
    (out / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return record


def load(prefix: str) -> tuple[dict, Path]:
    """The one registered record whose hash starts with `prefix`, and its folder."""
    found = sorted(ROOT.glob(f"{prefix}*/record.json"))
    if len(found) != 1:
        raise SystemExit(f"{len(found)} carteras registradas empiezan por «{prefix}» en {ROOT}")
    return json.loads(found[0].read_text(encoding="utf-8")), found[0].parent


def validate(record: dict, rows: pd.DataFrame) -> list[str]:
    """Everything that makes a file of fresh rows unreadable against this record, in Spanish.

    Args:
        record: The registered record.
        rows: The candidate rows, any columns.

    Returns:
        One line per problem, empty when the rows honour the contract: `COLUMNS` exactly;
        `segment` = "incubation"; one `source` of `SOURCES` per file; only the record's
        members; every day after the record's history; no (day, identity) twice; finite `pnl`
        in the unit of the hand-off's `daily.parquet` (the archived version's own sizing).
    """
    if list(rows.columns) != COLUMNS:
        return [f"columnas {list(rows.columns)}: deben ser exactamente {COLUMNS}"]
    if rows.empty:
        return ["el fichero no trae ninguna fila"]
    problems = []
    if set(rows["segment"]) != {SEGMENT}:
        problems.append(f"segment debe ser «{SEGMENT}» en todas las filas: {sorted(set(rows['segment']))}")
    if len(set(rows["source"])) != 1 or rows["source"].iloc[0] not in SOURCES:
        problems.append(f"source debe ser uno solo de {SOURCES} por fichero: {sorted(set(rows['source']))}")
    if strangers := sorted(set(rows["identity"]) - set(record["portfolio"]["weights"])):
        problems.append(f"identidades que no son de la cartera: {[s[:12] for s in strangers]}")
    days = pd.to_datetime(rows["day"], errors="coerce")
    if days.isna().any() or (days <= pd.Timestamp(record["history"]["to"])).any():
        problems.append(f"hay días no posteriores a la historia registrada (acaba el {record['history']['to']})")
    if rows.duplicated(["day", "identity"]).any():
        problems.append("hay (día, identidad) repetidos")
    if not np.isfinite(pd.to_numeric(rows["pnl"], errors="coerce")).all():
        problems.append("hay pnl no numérico o no finito")
    return problems
