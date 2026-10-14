"""One reading across markets: each market's rho and premium, the joint ones, their null and the power."""

from typing import Any
import numpy as np
import pandas as pd

from engines.weekly import flip
from studies.optimisation.marketSurfaces.measure import order, power, premium

NAN = float("nan")
BLANK = {
    "rho": NAN,
    "p_mas": NAN,
    "p_menos": NAN,
    "ties": NAN,
    "prima": NAN,
    "madre": NAN,
    "included": False,
}


def tails(observed: float, null: np.ndarray) -> flip.Tails:
    """`flip.tails`, or four NaN when there is no statistic to place."""
    if not np.isfinite(observed) or not len(null):
        return {"p_mas": NAN, "p_menos": NAN, "nulo_p5": NAN, "nulo_p95": NAN}
    return flip.tails(observed, null[np.isfinite(null)])


def key(rho: float) -> str:
    """The fact name of one planted rho: 0.1 -> `r01`."""
    return f"r{round(rho * 10):02d}"


def measure(
    main: np.ndarray,
    best: np.ndarray,
    markets: dict[str, dict],
    table: pd.DataFrame,
    mother: int | None,
    cfg: dict,
    seed: np.random.SeedSequence,
    block_weeks: int | None = None,
    planted: bool = True,
) -> dict[str, Any]:
    """Every number of one reading: the main market's window against one window of the others.

    The null draws one sign per week (or per block of weeks) and applies it to every variant
    of every market in `markets`; `main` is never flipped. The premium's null uses the same
    signs on the net panels.

    Args:
        main: The main market's gross excess, one per variant (any constant scale).
        best: The main market's top by net excess, a mask over the variants.
        markets: Feed -> `gross` and `net` (weeks x variants, the same weeks for every feed)
            and `ok` (the common set: variants usable on the main market and on this one).
        table: `inputs.markets.declared` rows of those feeds, in the same order.
        mother: The mother's position among the variants, None when she is not one.
        cfg: The study's config: `null`, `markets`, `premium`, `power`.
        seed: This reading's seed; its two children draw the null and the planted families.
        block_weeks: Weeks per sign; `null.block_weeks` when None.
        planted: False skips the power curve.

    Returns:
        `mercados` (one row per feed: `n` common variants, `rho`, `p_mas`, `p_menos`, `ties`,
        `prima`, `madre` (% of the common variants with a lower net excess than the mother),
        `included`, `weight`, with `table`'s columns); `orden` and `categorias` (category ->)
        with `rho`, the four tails, `peso` (sum of weights) and `mercados` (count); `nulo`
        (the joint rho of every draw); `prima` (`valor`, `nulo_p`, `bajo`) and `prima_nulo`;
        `potencia` (`r01`... -> share of planted families read positive).
    """
    knobs, rule = cfg["null"], cfg["markets"]
    weeks = len(next(iter(markets.values()))["gross"])
    seeds = seed.spawn(2)
    block = block_weeks or knobs["block_weeks"]
    signs = flip.signs(seeds[0], knobs["draws"], weeks, block)
    plant = flip.signs(seeds[1], cfg["power"]["draws"], weeks, block)
    rows, rho_null, pi_null, grown = [], {}, {}, {}
    for feed, got in markets.items():
        keep = got["ok"]
        row = {"feed": feed, "n": int(keep.sum())}
        if row["n"] < 3:
            rows.append(row | BLANK)
            continue
        x, gross, net, top = (
            main[keep],
            got["gross"][:, keep],
            got["net"][:, keep],
            best[keep],
        )
        y, e = gross.sum(axis=0), net.sum(axis=0)
        draws = [
            (flip.spearman(x, c @ gross), premium.premium(c @ net, top))
            for c in flip.chunks(signs, knobs["chunk"])
        ]
        rho_null[feed], pi_null[feed] = (np.concatenate(k) for k in zip(*draws))
        rho, ties = float(flip.spearman(x, y)), order.tie_share(y)
        found = tails(rho, rho_null[feed])
        row |= {
            "rho": rho,
            "p_mas": found["p_mas"],
            "p_menos": found["p_menos"],
            "ties": ties,
            "prima": float(premium.premium(e, top)),
            "madre": 100 * float((e < e[keep[:mother].sum()]).mean())
            if mother is not None and keep[mother]
            else NAN,
            "included": bool(
                np.isfinite(rho)
                and row["n"] >= rule["min_common"]
                and ties <= rule["max_ties"]
            ),
        }
        if planted and row["included"]:
            flipped = plant @ gross
            grown[feed] = {
                r: power.planted(x, flipped, r) for r in cfg["power"]["rhos"]
            }
        rows.append(row)
    frame = table.reset_index(drop=True).join(pd.DataFrame(rows).drop(columns="feed"))
    inside = frame["included"].to_numpy(bool)

    def together(
        mask: np.ndarray, values: str, null: dict
    ) -> tuple[float, np.ndarray, np.ndarray]:
        """The weighted mean over the masked markets of one column, observed and per draw."""
        if not mask.any():
            return NAN, np.empty(0), np.empty(0)
        weight = order.weights(frame.loc[mask, "group"])
        draws = np.column_stack([null[f] for f in frame.loc[mask, "feed"]])
        return (
            float(order.joint(frame.loc[mask, values].to_numpy(float), weight)),
            order.joint(draws, weight),
            weight,
        )

    def said(mask: np.ndarray) -> dict[str, Any]:
        """The joint rho of the masked markets with its tails, its weight and its count."""
        rho, null, weight = together(mask, "rho", rho_null)
        return {
            "rho": rho,
            **tails(rho, null),
            "peso": float(weight.sum()),
            "mercados": int(mask.sum()),
        }

    rho, null, weight = together(inside, "rho", rho_null)
    pi, pi_draws, _ = together(inside, "prima", pi_null)
    cut = (
        float(np.nanpercentile(pi_draws, cfg["premium"]["percentile"]))
        if np.isfinite(pi_draws).any()
        else NAN
    )
    frame["weight"] = 0.0
    frame.loc[inside, "weight"] = weight
    feeds = list(frame.loc[inside, "feed"])
    return {
        "mercados": frame,
        "orden": said(inside),
        "nulo": null,
        "categorias": {
            c: said(inside & (frame["category"] == c).to_numpy())
            for c in frame["category"].unique()
        },
        "prima": {
            "valor": pi,
            "nulo_p": cut,
            "bajo": bool(pi <= cut) if np.isfinite(pi) and np.isfinite(cut) else None,
        },
        "prima_nulo": pi_draws,
        "potencia": {
            key(r): power.detected(
                order.joint(np.column_stack([grown[f][r] for f in feeds]), weight),
                null,
                knobs["alpha"],
            )
            for r in cfg["power"]["rhos"]
        }
        if planted and feeds
        else {},
    }
