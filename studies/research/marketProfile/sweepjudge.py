"""The sweep judged: its own correction, each variant's plateau, the best variant per cell-family."""

import numpy as np
import pandas as pd
from scipy.stats import norm

from studies.research.marketProfile import many

CELL = ["symbol", "timeframe", "direction", "family"]


def judged(rows: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Every variant with the four filters, corrected inside the sweep, and its plateau.

    Args:
        rows: Every cell's variant rows (sweep.run), all assets together.
        cfg: The parsed config.

    Returns:
        rows plus what many.judged() adds (Benjamini-Hochberg over every variant of the sweep
        and nothing else). With ~50,000 variants the smallest p of 1,000 draws (0.001) can no
        longer be significant, so a statistic that beat EVERY draw takes the normal tail of
        its z instead (`p`; `p_empirical` keeps the counted one) — measured 2026-10-02: between
        p 0.004 and 0.2 the normal tail is 0.88-1.12 of the counted p. Then `neighbours` (the variants one step away: the same entry and exit
        at an adjacent parameter, the same entry and parameter at the adjacent hold or the
        other trailing width), `plateau` (how many of them also pay `cost_multiple` costs with
        a stable sign) and `on_plateau` (the variant passes the four filters and at least
        `sweep.plateau` neighbours pay).
    """
    floor = 1 / (cfg["sweep"]["draws"] + 1)
    tail = np.where(rows["p"] <= floor * (1 + 1e-9), np.minimum(floor, norm.sf(rows["z"])), rows["p"])
    out = many.judged(rows.assign(p_empirical=rows["p"], p=tail), cfg["filters"]).drop(
        columns=["q_family", "significant_family", "passes_family"])
    out["good"] = out["pays"] & out["stable"]
    knobs = cfg["sweep"]
    rank = {(name, p): i for name, spec in knobs["entries"].items()
            for i, p in enumerate(spec["params"])}
    out["_p"] = [rank[(e, p)] for e, p in zip(out["entry"], out["param"])]
    ladder = {f"hold{m:g}x": i for i, m in enumerate(knobs["holds"])}
    ladder |= {f"trail{w:g}": 100 + i for i, w in enumerate(knobs["trails"])}
    out["_e"] = out["exit"].map(ladder).fillna(-10)
    key = ["symbol", "timeframe", "direction", "entry"]
    good = out.set_index([*key, "_p", "exit"])["good"].to_dict()
    step = out.set_index([*key, "_p", "_e"])["good"].to_dict()
    near, paid = [], []
    for r in out[[*key, "_p", "exit", "_e"]].itertuples(index=False):
        base = tuple(r[:4])
        found = [good.get((*base, r[4] + d, r[5])) for d in (-1, 1)]
        if r[6] >= 0:
            found += [step.get((*base, r[4], r[6] + d)) for d in (-1, 1)]
        found = [f for f in found if f is not None]
        near.append(len(found))
        paid.append(int(sum(found)))
    out["neighbours"], out["plateau"] = near, paid
    out["on_plateau"] = out["passes"] & (out["plateau"] >= knobs["plateau"])
    return out.drop(columns=["_p", "_e", "good"])


def best(variants: pd.DataFrame) -> pd.DataFrame:
    """One row per cell-family: its best variant.

    Returns:
        The variant on a plateau with the widest plateau, then the one that passes, then the
        smallest corrected p — with `variants`, `pass_any`, `plateau_any`, `pays_any` (some
        variant pays twice the cost at all) and `max_multiple` of the cell-family.
    """
    ordered = variants.sort_values(["on_plateau", "passes", "plateau", "q", "multiple"],
                                   ascending=[False, False, False, True, False])
    top = ordered.groupby(CELL, sort=False).head(1).set_index(CELL)
    group = variants.groupby(CELL)
    top["variants"] = group.size()
    top["pass_any"] = group["passes"].any()
    top["plateau_any"] = group["on_plateau"].any()
    top["pays_any"] = group["pays"].any()
    top["max_multiple"] = group["multiple"].max()
    keep = ["entry", "param", "exit", "multiple", "p", "q", "stability", "trades_per_year",
            "plateau", "neighbours", "significant", "pays", "stable", "frequent", "passes",
            "on_plateau", "variants", "pass_any", "plateau_any", "pays_any", "max_multiple"]
    return top[keep].reset_index().sort_values(CELL)


def counts(top: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    """Per timeframe: cell-families that pass naked, with a variant on a plateau, or never pay.

    Args:
        top: What best() returned.
        scores: The main map's `scores.csv`, for the naked verdict of the same cell-families.
    """
    naked = scores[~scores["needs_clock"]].set_index(CELL)["passes"]
    joined = top.join(naked.rename("naked"), on=CELL)
    return joined.groupby("timeframe").agg(
        cell_families=("naked", "size"), naked=("naked", "sum"), any_variant=("pass_any", "sum"),
        on_plateau=("plateau_any", "sum"),
        never_pays=("pays_any", lambda s: int((~s).sum()))).reindex(["M15", "M30", "H1", "H4"])


def summary(variants: pd.DataFrame) -> str:
    """One Spanish paragraph: how many variants, how many survive, and what they are."""
    return (f"{len(variants)} variantes contrastadas y corregidas juntas dentro del barrido; "
            f"{int(variants['significant'].sum())} significativas, "
            f"{int(variants['passes'].sum())} pasan los cuatro filtros, "
            f"{int(variants['on_plateau'].sum())} de ellas en meseta. Una variante elegida aquí "
            "es una HIPÓTESIS seleccionada dentro de muestra, no un hallazgo: dice qué celdas "
            "merecen un build en SQX, que es donde está la prueba fuera de muestra.")
