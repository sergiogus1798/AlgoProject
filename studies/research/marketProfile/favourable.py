"""Which families favour each asset, graded A/B/C from the judged map — the tables of `assets/FAMILIAS.md`."""

from pathlib import Path

import pandas as pd
import yaml

# The two rules of the free hole are the board's data; read as a file, a study imports no other.
BOARD = yaml.safe_load((Path(__file__).parents[1] / "board" / "config.yaml")
                       .read_text(encoding="utf-8"))
CELL = ["symbol", "timeframe", "direction", "family"]
PAYS, HALF_PAYS = 2.0, 1.0     # effect in round-trip costs: the profile's filter, and grade C's floor
RAW_ALPHA = 0.05               # grade C without significance: nominal p before the correction
NO_PAY = 0.5                   # a significant effect below this many costs is structure that loses
REVERSED = (0.95, -1.0)        # raw p at or above, effect at or below: the sign is the opposite one
ORDER = {"A": 0, "B": 1, "C": 2}
# The palette of the fixed condition, per family: `sqx/blocks/palettes/<name>.yaml`.
PALETTE = {"ruptura": "ruptura_base_v2", "reversion": "reversion_base_v2",
           "tendencia": "tendencia_base_v2", "momentum": "momentum_base",
           "volatilidad": "volatilidad_base", "patron": "patron_base", "sesion": "sesion_base"}
WEAK = {"frequent": "pocas operaciones", "stable": "frágil", "pays": "paga 1-2×",
        "significant": "no significativa tras corregir"}
AVOID = {"no_paga": "estructura real que no paga el coste", "signo_contrario": "signo contrario",
         "plana": "ninguna celda llega a medio coste"}


def graded(scores: pd.DataFrame, by_family: bool = False) -> pd.DataFrame:
    """Every cell-family of the map with its grade.

    Args:
        scores: The profile's `scores.csv` (the lead measure's numbers and its four filters).
        by_family: Read the ALTERNATIVE correction (Benjamini-Hochberg inside each family,
            `significant_family` and `p_family`) instead of the headline one over every test.

    Returns:
        scores plus `grade` — **A** the four filters; **B** significant and pays `PAYS` costs but
        not frequent or not stable; **C** stable and frequent with one weakness: significant and
        pays `HALF_PAYS` to `PAYS` costs, or pays `PAYS` with a raw p within `RAW_ALPHA` that the
        correction did not keep; "" below that — `weak` (the filters it fails, in Spanish) and
        `avoid` ("no_paga", "signo_contrario" or ""). A cell-family whose lead needs the clock
        (`needs_clock`: hour, session band, weekday) gets no grade and no avoid: the owner
        builds with no clock block, so it is neither proposed nor warned against.
    """
    out = scores.copy()
    if by_family:
        out["significant"], out["p"] = out["significant_family"], out["p_family"]
    multiple = out["multiple"].fillna(float("-inf"))
    sig, pays, stable, frequent = (out[c].astype(bool) for c in
                                   ("significant", "pays", "stable", "frequent"))
    a = sig & pays & stable & frequent
    b = sig & pays & ~a
    c = stable & frequent & ((sig & ~pays & (multiple >= HALF_PAYS))
                             | (~sig & pays & (out["p_raw"] <= RAW_ALPHA)))
    free = ~out["needs_clock"].astype(bool)
    out["grade"] = pd.Series("", index=out.index).mask(c & free, "C").mask(b & free, "B").mask(
        a & free, "A")
    failed = {"frequent": ~frequent, "stable": ~stable, "pays": ~pays, "significant": ~sig}
    out["weak"] = ["; ".join(WEAK[k] for k, miss in failed.items() if miss[i])
                   for i in out.index]
    out["avoid"] = pd.Series("", index=out.index).mask(
        (out["p_raw"] >= REVERSED[0]) & (multiple <= REVERSED[1]), "signo_contrario").mask(
        sig & (multiple < NO_PAY), "no_paga").where(free, "")
    return out


def hole(family: str) -> str:
    """The palettes the free hole draws from for a fixed condition of `family`, heaviest first.

    The board's two rules (`studies/research/board/config.yaml`, `palette`): another kind of
    data than the fixed condition weighs most, the counter-trend next, the same data least;
    the family itself and a family that follows the move like it are left out.
    """
    rules, key = BOARD["palette"], BOARD["taxonomy_family"]
    fixed, weight = key[family], {}
    for name in PALETTE:
        other, pair = key[name], {key[family], key[name]}
        if rules["data"][other] != rules["data"][fixed]:
            weight[name] = rules["weights"]["orthogonal"]
        elif other == fixed or pair <= set(rules["alike"]):
            weight[name] = 0
        elif rules["counter"] in pair and pair & set(rules["alike"]):
            weight[name] = rules["weights"]["counter"]
        else:
            weight[name] = rules["weights"]["same_data"]
    kept = sorted((f for f in weight if weight[f]), key=lambda f: (-weight[f], f))
    return ", ".join(f"{PALETTE[f]} ({weight[f]})" for f in kept)


def ranked(scores: pd.DataFrame, by_family: bool = False) -> pd.DataFrame:
    """One row per asset and listed family, most favourable first.

    Args:
        scores: The profile's `scores.csv`.
        by_family: The alternative correction, as in graded().

    Returns:
        `symbol`, `rank` (1 = most favourable in the asset), `family`, `grade`, `weak`, the
        best cell's `timeframe`, `direction`, `lead`, `multiple`, `p`, `p_raw`, `stability`,
        `trades_per_year`, `also` (the other graded cells of the family in the asset),
        `palette` and `hole`. Order: grade, then significant before not, then the multiple.
        A family with no graded cell in an asset has no row.
    """
    cells = graded(scores, by_family)
    cells = cells[cells["grade"] != ""].assign(
        _g=lambda d: d["grade"].map(ORDER), _s=lambda d: ~d["significant"].astype(bool))
    cells = cells.sort_values(["symbol", "_g", "_s", "multiple"],
                              ascending=[True, True, True, False])
    rows = []
    for (symbol, family), group in cells.groupby(["symbol", "family"], sort=False):
        best = group.iloc[0]
        also = "; ".join(f"{r.timeframe} {r.direction} {r.grade} {r.multiple:.1f}×"
                         for r in group.iloc[1:].itertuples())
        rows.append({"symbol": symbol, "family": family, "grade": best["grade"],
                     "weak": best["weak"], **{k: best[k] for k in (
                         "timeframe", "direction", "lead", "multiple", "p", "p_raw",
                         "stability", "trades_per_year")},
                     "also": also, "palette": PALETTE[family], "hole": hole(family)})
    out = pd.DataFrame(rows, columns=["symbol", "family", "grade", "weak", "timeframe",
                                      "direction", "lead", "multiple", "p", "p_raw", "stability",
                                      "trades_per_year", "also", "palette", "hole"])
    out.insert(1, "rank", out.groupby("symbol").cumcount() + 1)
    return out


def avoided(scores: pd.DataFrame) -> pd.DataFrame:
    """The families measurably bad in an asset, among those with no graded cell there.

    Returns:
        One row per asset and family: `symbol`, `family`, `reason` (a key of AVOID), `scope`
        — "familia" when at least half of the asset's cells are structure that does not pay
        or none reaches `NO_PAY` costs, "celda" when only the cells in `where` are bad —
        `cells`, `of` (cells measured), `where` and `best_multiple` (the most any cell pays).
    """
    rows, cells = [], graded(scores)
    for (symbol, family), group in cells[~cells["needs_clock"].astype(bool)].groupby(
            ["symbol", "family"]):
        bad, best = group[group["avoid"] != ""], group["multiple"].max()
        if (group["grade"] != "").any() or (bad.empty and best >= NO_PAY):
            continue
        losing = int((group["avoid"] == "no_paga").sum())
        if 2 * losing >= len(group):
            reason, scope, n = "no_paga", "familia", losing
        elif best < NO_PAY:
            reason, scope, n = "plana", "familia", len(group)
        else:
            reason, scope, n = bad["avoid"].iloc[0], "celda", len(bad)
        where = "" if scope == "familia" else "; ".join(
            f"{r.timeframe} {r.direction}" for r in bad.itertuples())
        rows.append({"symbol": symbol, "family": family, "reason": reason, "scope": scope,
                     "cells": n, "of": len(group), "where": where, "best_multiple": best})
    return pd.DataFrame(rows, columns=["symbol", "family", "reason", "scope", "cells", "of",
                                       "where", "best_multiple"])


def summary(table: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    """Asset → its ranked families in one line, «nada favorable medido» where there is none."""
    line = {s: ", ".join(f"{r.family} ({r.grade}, {r.timeframe} {r.direction})"
                         for r in g.itertuples()) for s, g in table.groupby("symbol")}
    return pd.DataFrame({"symbol": symbols,
                         "families": [line.get(s, "nada favorable medido") for s in symbols]})


def reverse(table: pd.DataFrame) -> pd.DataFrame:
    """Family → the assets where it is listed, best grade and largest multiple first."""
    by = table.assign(_g=table["grade"].map(ORDER)).sort_values(["_g", "multiple"],
                                                               ascending=[True, False])
    return pd.DataFrame([{"family": f, "assets": ", ".join(
        f"{r.symbol} ({r.grade}, {r.timeframe} {r.direction}, {r.multiple:.1f}×)"
        for r in g.itertuples())} for f, g in by.groupby("family", sort=False)],
        columns=["family", "assets"])


def by_timeframe(scores: pd.DataFrame) -> pd.DataFrame:
    """Every asset × family on each timeframe: the view that does not hide M30 and H1.

    Returns:
        One row per symbol, family and timeframe: the better of its two directions (grade
        first, then the multiple) with `direction`, `grade` ("" when below the bar), `lead`,
        `multiple`, `p`, `p_raw`, `trades_per_year` and `weak`. Clock families are left out.
    """
    cells = graded(scores)
    cells = cells[~cells["needs_clock"].astype(bool)].assign(
        _g=lambda d: d["grade"].map(ORDER).fillna(len(ORDER)))
    cells = cells.sort_values(["_g", "multiple"], ascending=[True, False])
    best = cells.groupby(["symbol", "family", "timeframe"], sort=False).head(1)
    return best.sort_values(["symbol", "family", "timeframe"])[[
        "symbol", "family", "timeframe", "direction", "grade", "lead", "multiple", "p", "p_raw",
        "trades_per_year", "weak"]].reset_index(drop=True)


def clocked(measures: pd.DataFrame) -> pd.DataFrame:
    """What was measured and is left out for needing the clock, so the knowledge is not lost.

    Args:
        measures: The profile's `measures.csv`.

    Returns:
        The clock measures that would have earned a grade, one row each: `symbol`,
        `timeframe`, `direction`, `measure`, `detail` (the hour, band or weekday chosen),
        `grade`, `multiple`, `p`, `p_raw`, `stability`, `trades_per_year`.
    """
    rows = measures[measures["needs_clock"].astype(bool)].rename(columns={"p": "p_raw"}).rename(
        columns={"q": "p"}).assign(needs_clock=False)
    rows = graded(rows)
    rows = rows[rows["grade"] != ""].assign(_g=lambda d: d["grade"].map(ORDER))
    return rows.sort_values(["symbol", "_g", "multiple"], ascending=[True, True, False])[[
        "symbol", "timeframe", "direction", "measure", "detail", "grade", "multiple", "p",
        "p_raw", "stability", "trades_per_year"]].reset_index(drop=True)


def regraded(scores: pd.DataFrame) -> pd.DataFrame:
    """The cell-families whose grade changes under the alternative correction.

    Returns:
        `symbol`, `timeframe`, `direction`, `family`, `lead`, `multiple`, `p_raw`, `grade`
        (headline: one correction over every test) and `grade_family` (inside each family).
    """
    head, alone = graded(scores), graded(scores, by_family=True)
    out = head.assign(grade_family=alone["grade"], p_family=alone["p"])
    return out[out["grade"] != out["grade_family"]][[
        *CELL, "lead", "multiple", "p_raw", "p", "p_family", "grade", "grade_family"]]
