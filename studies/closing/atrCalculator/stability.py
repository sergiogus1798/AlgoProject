"""§3 — what SQX says each X costs against the original, in each window, and the shape around it."""

import numpy as np
import pandas as pd

from studies.closing.atrCalculator import proofs
from studies.closing.atrCalculator.inputs import SEGMENTS


def stats(trades: pd.DataFrame) -> dict:
    """Net, profit factor, closed-trade drawdown and the worst trade of one run in one window."""
    pl = trades.sort_values("Close time")["Profit/Loss"].to_numpy()
    equity = np.cumsum(pl)
    loss = -pl[pl < 0].sum()
    return {"n": len(pl), "net": float(pl.sum()),
            "pf": float(pl[pl > 0].sum() / loss) if loss else np.nan,
            "maxdd": float(np.max(np.maximum.accumulate(np.maximum(equity, 0)) - equity))
            if len(pl) else 0.0,
            "worst": float(pl.min()) if len(pl) else np.nan}


def against(variant: pd.DataFrame, reference: pd.DataFrame) -> dict:
    """What the stop did to the original's trades, matched by entry time.

    Args:
        variant: One window's trades with the stop.
        reference: The same window's trades without it.

    Returns:
        `stopped` (trades the stop closed) and their share, `killed` (of those, trades that
        were winners in the original), `saved` (loss avoided on stopped trades the original
        lost on), `given_up` (profit lost on stopped trades the original won), and `new`
        (entries the original never took — the stop freed the strategy earlier).
    """
    ref = reference.set_index("Open time")["Profit/Loss"]
    hit = variant[variant["Close type"].astype(str) == proofs.STOP]
    before = ref.reindex(hit["Open time"]).to_numpy()
    after = hit["Profit/Loss"].to_numpy()
    won, lost = before > 0, before <= 0
    return {"stopped": len(hit), "stopped_pct": 100 * len(hit) / len(variant) if len(variant)
            else np.nan, "killed": int(won.sum()),
            "saved": float((after - before)[lost].sum()),
            "given_up": float((before - after)[won].sum()),
            "new": int((~variant["Open time"].isin(ref.index)).sum())}


def measure(strategy: str, inputs: dict, cfg: dict) -> dict:
    """Every variant of one mother in every window, the two proofs, and the shape per percentile.

    Args:
        strategy: The mother's name.
        inputs: What load.load() returned, with a batch.
        cfg: The study's config.

    Returns:
        `graft` (proofs.graft), `atr` (proofs.atr over every stopped trade of the grid),
        `metrics` (one row per grid variant and window, with the original's own numbers
        beside) and `shape` (one row per percentile and window).
    """
    batch = inputs["batch"]
    mine = batch[batch["strategy"] == strategy]
    trades = inputs["trades"]
    by_id = {v: trades[trades["strategy"] == v] for v in mine["variant_id"]}
    ref = by_id[mine.loc[mine["stratum"] == "reference", "variant_id"].iloc[0]]
    probe = by_id[mine.loc[mine["stratum"] == "probe", "variant_id"].iloc[0]]
    rows, stopped = [], []
    for v in mine[mine["stratum"] == "grid"].itertuples():
        got = by_id[v.variant_id]
        stopped.append(got[got["Close type"].astype(str) == proofs.STOP].assign(x=v.x))
        for s in SEGMENTS:
            here, base = got[got["segment"] == s], ref[ref["segment"] == s]
            original = stats(base)
            rows.append({"percentile": int(v.percentile), "step": int(v.step), "x": v.x,
                         "segment": s,
                         **stats(here), **against(here, base),
                         **{f"{k}_original": original[k] for k in ("net", "pf", "maxdd",
                                                                   "worst")}})
    metrics = pd.DataFrame(rows)
    stops = pd.concat(stopped, ignore_index=True) if stopped else pd.DataFrame()
    # The first pass carries no grid yet: the reference and the probe, for the graft proof.
    return {"graft": proofs.graft(ref, probe, cfg), "metrics": metrics,
            "atr": proofs.atr(stops, inputs["bars_index"], inputs["atr"], cfg) if len(stops)
            else pd.DataFrame(), "shape": shape(metrics, cfg) if len(metrics) else metrics}


def score(metrics: pd.DataFrame, cfg: dict) -> pd.Series:
    """The owner's weighted fitness of each variant, against the original without a stop.

    Args:
        metrics: What `measure` built.
        cfg: The study's config; `shape.weights` holds the weights.

    Returns:
        weight_pf * PF / PF original + weight_net * net / net original + weight_maxdd *
        max DD original / max DD, so 1.0 is "the same as without a stop" and every term reads
        higher-is-better. Each metric enters as a ratio to the original, so none weighs more
        because of its units. NaN where the original's net or PF is not positive: a ratio
        to a losing original says nothing about the shape.
    """
    w = cfg["shape"]["weights"]
    ok = (metrics["net_original"] > 0) & (metrics["pf_original"] > 0)
    got = (w["pf"] * metrics["pf"] / metrics["pf_original"]
           + w["net"] * metrics["net"] / metrics["net_original"]
           + w["maxdd"] * metrics["maxdd_original"] / metrics["maxdd"].where(metrics["maxdd"] > 0))
    return got.where(ok)


def shape(metrics: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Plateau or edge: how far the weighted score moves along the grid around each X.

    Args:
        metrics: What `measure` built, one row per grid variant and window.
        cfg: The study's config.

    Returns:
        One row per percentile and window: the centre's score, the largest move of the
        score on the tighter side (steps below 0) and on the looser side, each as a share of
        the centre's, and `shape` — "meseta" when both stay within `shape.tolerance`,
        otherwise which side falls away. It reads the form, never the maximum: the score is
        the owner's yardstick for "flat", not a ranking of the X.
    """
    tol, rows = cfg["shape"]["tolerance"], []
    metrics = metrics.assign(score=score(metrics, cfg))
    for (p, s), g in metrics.groupby(["percentile", "segment"]):
        centre = g.loc[g["step"] == 0, "score"].iloc[0]
        rel = (g.set_index("step")["score"] - centre) / abs(centre)
        tight, loose = rel[rel.index < 0].abs().max(), rel[rel.index > 0].abs().max()
        label = ("sin referencia" if not np.isfinite(centre) else
                 "meseta" if tight <= tol and loose <= tol else
                 "borde al apretar" if loose <= tol else
                 "borde al aflojar" if tight <= tol else "borde por los dos lados")
        rows.append({"percentile": p, "segment": s, "centre_score": centre,
                     "tighter": tight, "looser": loose, "shape": label})
    return pd.DataFrame(rows)

def summary(measured: dict) -> dict:
    """The flat numbers verdict.csv carries from the SQX side: the proofs and the shapes."""
    row = {"graft_identical": bool(measured["graft"]["identical"].all())}
    if len(measured["atr"]):
        a = measured["atr"]
        row["atr_matches"] = bool(a.loc[a["bar"].str.contains("shift 1"), "matches"].all())
    for r in measured["shape"].itertuples():
        row[f"shape_{r.segment}_p{r.percentile}"] = r.shape
    return row
