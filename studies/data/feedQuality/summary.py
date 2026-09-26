"""What one feed's anomalies add up to: counts by year and month, K*, the stable year, episodes."""

import numpy as np
import pandas as pd

from studies.data.feedQuality.calendar import HOLIDAY, OUTAGE, OWN, PARTIAL

# What the attribution marks, and what is only reported: the rollover's frozen runs and gaps
# are counted and can make an episode, but never mark a trade (owner, 2026-09-26).
MARKED = ["cierre y vuelta", "mecha y vuelta", "congelado", "hueco", "caída del proveedor"]


def _columns(ev: pd.DataFrame) -> dict[str, pd.Series]:
    """Each report column as a bool per event row."""
    spike = ev["kind"].isin(["cierre", "mecha"])
    back = ev["cls"] == "vuelta"
    return {
        "cierre": ev["kind"] == "cierre", "mecha": ev["kind"] == "mecha",
        "cierre y mecha": (ev["kind"] == "cierre") & ev["both"].eq(True),
        "cierre y vuelta": (ev["kind"] == "cierre") & back,
        "mecha y vuelta": (ev["kind"] == "mecha") & back,
        "vuelta m=1": (ev["kind"] == "cierre") & ev["rev_m1"].eq(True),
        "vuelta m=5": (ev["kind"] == "cierre") & ev["rev_m5"].eq(True),
        "movimiento extremo": spike & ~back,
        "congelado": (ev["kind"] == "congelado") & (ev["cls"] == "congelado"),
        "hueco": (ev["kind"] == "hueco") & (ev["cls"] == OWN),
        "congelado en rollover": (ev["kind"] == "congelado") & (ev["cls"] == "rollover"),
        "hueco en rollover": (ev["kind"] == "hueco") & (ev["cls"] == "rollover"),
        "caída del proveedor": ev["cls"] == OUTAGE,
        "cierre parcial": ev["cls"] == PARTIAL, "festivo": ev["cls"] == HOLIDAY}


def counts(ev: pd.DataFrame, period: str) -> pd.DataFrame:
    """Events per year ("Y") or per month ("M"), one column per report column.

    Args:
        ev: A feed's events with gaps classified.
        period: "Y" or "M".

    Returns:
        Periods as rows, plus `marcadas`, the sum of what the attribution reads.
    """
    key = ev["t"].dt.year if period == "Y" else ev["t"].dt.to_period("M")
    out = pd.DataFrame({name: flag.groupby(key).sum() for name, flag in _columns(ev).items()})
    out["marcadas"] = out[MARKED].sum(axis=1)
    return out.fillna(0).astype(int)


def k_star(yearly: pd.DataFrame, cfg: dict) -> tuple[int | None, dict]:
    """The smallest candidate K whose quiet-year median stays under the weekly bar.

    Args:
        yearly: detect.yearly_counts()'s table.
        cfg: inputs.config()'s dict.

    Returns:
        (K*, {K: quiet-year median}). None when no candidate passes: that feed is reviewed,
        not given the largest K.
    """
    lo, hi = cfg["k"]["quiet_years"]
    quiet = yearly.loc[(yearly.index >= lo) & (yearly.index <= hi)]
    medians = {int(k): float(quiet[k].median()) for k in yearly.columns}
    passing = [k for k, v in medians.items() if v < cfg["k"]["max_per_year"]]
    return (min(passing) if passing else None), medians


def stability(yearly: pd.DataFrame, cfg: dict) -> tuple[int | None, dict]:
    """The year from which the feed's gaps stay near their modern level, and each year's grade.

    Args:
        yearly: counts(..., "Y").
        cfg: inputs.config()'s dict.

    Returns:
        (Y*, {year: "estable" | "calidad B" | "inestable"}). G(y) is the marked gaps of the
        year — the symbol's own and the provider's outages; Y* is the first year after which
        every year stays under `factor` × the median since `base_year`, never a bar lower
        than `floor` — with a median of two or three, one thin Christmas would triple it.
    """
    st = cfg["stable"]
    g = yearly["hueco"] + yearly["caída del proveedor"]
    base = np.median(g[g.index >= st["base_year"]])
    ok = g <= max(st["factor"] * base, st["floor"])
    after = ok.astype(int)[::-1].cummin()[::-1].astype(bool)
    grade = {int(y): "estable" if after[y] else
             "calidad B" if v <= max(st["b_factor"] * base, st["floor"]) else "inestable"
             for y, v in g.items()}
    return (int(after.idxmax()) if after.any() else None), grade


def episodes(monthly: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Months whose frozen runs or gaps jump well above their own recent past.

    Args:
        monthly: counts(..., "M").
        cfg: inputs.config()'s dict.

    Returns:
        One row per (month, column) that is an episode, with its count and the median it
        was judged against. The first `months` months have no past to judge against.
    """
    ep = cfg["episode"]
    full = monthly.reindex(pd.period_range(monthly.index.min(), monthly.index.max(), freq="M"),
                           fill_value=0)
    rows = []
    for col in ("congelado", "hueco", "congelado en rollover", "hueco en rollover"):
        past = full[col].shift(1).rolling(ep["months"], min_periods=ep["months"]).median()
        hit = (full[col] > ep["factor"] * past) & (full[col] >= ep["min_events"])
        rows += [{"mes": str(m), "columna": col, "sucesos": int(full[col][m]),
                  "mediana previa": float(past[m])} for m in full.index[hit]]
    return pd.DataFrame(rows, columns=["mes", "columna", "sucesos", "mediana previa"])


def residual_gaps(yearly: pd.DataFrame, cfg: dict, last_full_year: int) -> float:
    """Median of the symbol's own gaps per full year since the base year.

    Returns:
        Over `gap.max_residual_per_year`, the session is declared wrong (owner's answer 2.10).
    """
    g = yearly["hueco"]
    return float(np.median(g[(g.index >= cfg["stable"]["base_year"]) & (g.index <= last_full_year)]))
