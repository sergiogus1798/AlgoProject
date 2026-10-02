"""The owner's prior beside what was measured: each prior family of an asset and timeframe, with its state."""

from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from studies.research.marketProfile import favourable

# The prior is the board's data; read as a file, a study imports no other.
PRIOR = yaml.safe_load((Path(__file__).parents[1] / "board" / "prior.yaml")
                       .read_text(encoding="utf-8"))
LEVEL = {"A": "Alta", "M": "Media", "B": "Baja"}
TIMEFRAMES = ["M15", "M30", "H1", "H4"]
INDICES = ["USA500", "USATEC", "DJ30", "DAX40", "NIKKEI225"]
# What feeds the prior's `pullback`, which is not one of the profile's seven families.
PULL = ["pullback_mom60_trail", "pullback_up200_trail", "rsi2_up200_sma5", "down3_up200_sma5",
        "extreme2_up200", "extreme2_up200_mean", "connors_d1", "williams_pullback_1d"]
PULL_SWEEP = ["pullback", "rsi_up100", "rsi_up200"]
FOR, NONE, AGAINST = "medido a favor", "sin evidencia medida", "medido en contra"
RANK = {FOR: 0, NONE: 1, AGAINST: 2}
EXPECT = {"reversion": "below", "tendencia": "above", "ruptura": "above", "momentum": "above"}


def matrix(symbol: str, family: str) -> str:
    """The matrix level of a prior family for an asset: Alta, Media or Baja."""
    return LEVEL[PRIOR["matrix"][symbol][PRIOR["families"].index(family)]]


def long_only(symbol: str, family: str) -> bool:
    """The prior holds that family for the long side only."""
    return family in PRIOR["long_only"].get(symbol, [])


def graded(measures: pd.DataFrame) -> pd.DataFrame:
    """Every clock-free trade measure with a grade, and its effect net of the drift.

    `net` is the multiple scaled by (statistic − null mean) / statistic: what is left after
    the same rule on the shuffled series, which keeps the drift and the exposure.
    """
    rows = measures[measures["n_trades"].notna() & ~measures["needs_clock"].astype(bool)]
    with np.errstate(divide="ignore", invalid="ignore"):
        net = np.where(rows["stat"] != 0, rows["multiple"] * (rows["stat"] - rows["null_mean"])
                       / rows["stat"], np.nan)
    rows = rows.assign(net=net).rename(columns={"p": "p_raw"}).rename(columns={"q": "p"})
    return favourable.graded(rows)


def naked(rows: pd.DataFrame, symbol: str, timeframe: str, family: str) -> pd.DataFrame:
    """The graded measures that speak for a prior family in one cell, best first."""
    own = rows["measure"].isin(PULL) if family == "pullback" else (
        (rows["family"] == family) & ~rows["measure"].isin(PULL))
    got = rows[(rows["symbol"] == symbol) & (rows["timeframe"] == timeframe) & own]
    if long_only(symbol, family):
        got = got[got["direction"] == "long"]
    return got.assign(_g=got["grade"].map(favourable.ORDER).fillna(9)).sort_values(
        ["_g", "p", "multiple"], ascending=[True, True, False])


def swept(variants: pd.DataFrame, symbol: str, timeframe: str, family: str) -> pd.DataFrame:
    """The sweep's variants that speak for a prior family in one cell, best first."""
    own = variants["entry"].isin(PULL_SWEEP) if family == "pullback" else (
        (variants["family"] == family) & ~variants["entry"].isin(PULL_SWEEP))
    got = variants[(variants["symbol"] == symbol) & (variants["timeframe"] == timeframe) & own]
    if long_only(symbol, family):
        got = got[got["direction"] == "long"]
    return got.sort_values(["on_plateau", "passes", "plateau", "q", "multiple"],
                           ascending=[False, False, False, True, False])


def state(rows: pd.DataFrame, variants: pd.DataFrame, symbol: str, timeframe: str,
          family: str) -> dict:
    """What was measured for one prior family in one cell.

    Returns:
        `flag` (FOR, NONE or AGAINST), `how` (why it is for), `naked` and `swept` (the two
        readings as text; the naked one carries the effect net of drift for index longs).
    """
    n, w = naked(rows, symbol, timeframe, family), swept(variants, symbol, timeframe, family)
    top, how = n.iloc[0], []
    if top["grade"]:
        how.append(f"desnudo nota {top['grade']}")
    if not w.empty and w.iloc[0]["on_plateau"]:
        how.append("barrido en meseta")
    bad = (n["avoid"] != "").any() and not (n["grade"] != "").any() and (
        w.empty or w["multiple"].max() < 2)
    flat = not w.empty and w["multiple"].max() < 0.5 and n["multiple"].max() < 0.5
    flag = FOR if how else (AGAINST if bad or flat else NONE)
    net = (f" · neto de deriva {top['net']:.1f}×"
           if symbol in INDICES and top["direction"] == "long" and pd.notna(top["net"]) else "")
    text = (f"{top['direction']} · `{top['measure']}` · {top['multiple']:.1f}×{net} · p corr. "
            f"{top['p']:.2f} (cruda {top['p_raw']:.3f}) · {top['trades_per_year']:.0f}/año"
            + (f" · nota {top['grade']}" if top["grade"] else ""))
    if w.empty:
        return {"flag": flag, "how": how, "naked": text, "swept": "—"}
    v = w.iloc[0]
    kind = "**meseta**" if v["on_plateau"] else ("pico" if v["passes"] else "no pasa")
    return {"flag": flag, "how": how, "naked": text,
            "swept": f"{kind}: {v['direction']} · `{v['entry']}` {v['param']:g} · {v['exit']} · "
                     f"{v['multiple']:.1f}× · meseta {int(v['plateau'])}/{int(v['neighbours'])} · "
                     f"p {v['q']:.2f} · {v['trades_per_year']:.0f}/año"}


def variance_cell(ratios: pd.DataFrame, symbol: str, timeframe: str, main: str) -> str:
    """The variance ratio of a cell against the sign its prior's main family bets on."""
    here = ratios[(ratios["symbol"] == symbol) & (ratios["timeframe"] == timeframe)]
    short, far = here[here["q"] == 8].iloc[0], here[here["q"] == 32].iloc[0]
    share = short["years_below_1"] / short["years"]
    sign = "below" if short["vr"] < 1 and share >= 0.6 else (
        "above" if short["vr"] > 1 and share <= 0.4 else "none")
    want = EXPECT.get(main)
    verdict = "la prior no afirma signo" if want is None else (
        "**coincide**" if sign == want else ("sin signo estable" if sign == "none"
                                             else "**discrepa**"))
    return (f"VR(8) {short['vr']:.3f}, <1 en {int(short['years_below_1'])} de "
            f"{int(short['years'])} años; VR(32) {far['vr']:.3f} — {verdict}")


def ranking(rows: pd.DataFrame, variants: pd.DataFrame, symbol: str, timeframe: str) -> list[dict]:
    """The prior's families of one asset and timeframe, ordered, each with what was measured.

    Order: Alta before Media; then measured-for before no evidence before against; then main
    before secondary. A family outside the timeframe's cell is added only when it is measured
    clearly for (a naked A or B, or a sweep plateau) — flagged when the prior rates it Baja.
    """
    cell, out = PRIOR["by_timeframe"][symbol][timeframe], []
    for family in PRIOR["families"]:
        got = state(rows, variants, symbol, timeframe, family)
        listed = family in cell
        strong = got["flag"] == FOR and any(k in " ".join(got["how"])
                                            for k in ("nota A", "nota B", "meseta"))
        if not listed and not strong:
            continue
        level = matrix(symbol, family)
        role = ("principal" if cell[0] == family else "secundaria") if listed else (
            f"no está en la celda de {timeframe}")
        out.append({**got, "family": family, "level": level, "role": role,
                    "long_only": long_only(symbol, family),
                    "contradicts": not listed and level == "Baja",
                    "_k": (0 if level == "Alta" and listed else (1 if listed else 3),
                           RANK[got["flag"]], cell.index(family) if listed else 9)})
    return sorted(out, key=lambda r: r["_k"])
