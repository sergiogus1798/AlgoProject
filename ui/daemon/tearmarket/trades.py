"""Item 6: five trades of one sample, at P&L quantiles or drawn with a seed, each with its bar window."""

import secrets

import numpy as np
import pandas as pd

QUANTILES = (0, 25, 50, 75, 100)
AROUND = 20          # bars shown before the entry and after the exit


def quantile_picks(pnl: np.ndarray) -> list[tuple[int, str]]:
    """The trades at P&L quantiles 0/25/50/75/100 %, all of them when there are fewer than five.

    Args:
        pnl: P&L per trade, in the order the export lists them.

    Returns:
        (row, label) per pick, lowest P&L first. Ties are ordered by row, so the pick is
        deterministic: rank = round(q × (n − 1)) on a stable sort.
    """
    order = np.argsort(pnl, kind="stable")
    if len(order) <= len(QUANTILES):
        return [(int(r), f"{k + 1}.º de {len(order)}") for k, r in enumerate(order)]
    return [(int(order[round(q / 100 * (len(order) - 1))]), f"cuantil {q} %") for q in QUANTILES]


def random_picks(pnl: np.ndarray, seed: int) -> list[tuple[int, str]]:
    """Five trades drawn without replacement with a seeded generator, shown lowest P&L first.

    Args:
        pnl: P&L per trade.
        seed: The generator's seed; the same seed draws the same five.

    Returns:
        (row, label) per pick.
    """
    rows = np.random.default_rng(seed).choice(len(pnl), min(5, len(pnl)), replace=False)
    rows = sorted(rows, key=lambda r: (pnl[r], r))
    return [(int(r), f"al azar {k + 1}/{len(rows)}") for k, r in enumerate(rows)]


def window(bars: pd.DataFrame | None, opened: pd.Timestamp, closed: pd.Timestamp) -> dict:
    """The bars from AROUND before the entry bar to AROUND after the exit bar.

    Args:
        bars: The feed's bars at the strategy's timeframe, cut at the end of oos1; None when
            the asset or its feed is unknown.
        opened, closed: The trade's open and close times (bar opens, in the feed's clock).

    Returns:
        `{t, o, h, l, c, entry, exit, held}` (entry/exit are indices into t; held = bars from
        the entry bar to the exit bar), or `{missing: sentence}`.
    """
    if bars is None:
        return {"missing": "Sin barras: el activo o su feed no se conocen."}
    idx = bars.index
    if opened < idx[0] or closed > idx[-1]:
        return {"missing": (f"Sin barras para esta operación: el feed cubre {idx[0]:%Y-%m-%d} … "
                            f"{idx[-1]:%Y-%m-%d} en lo que la ventana puede mostrar.")}
    i0, i1 = idx.searchsorted(opened, "right") - 1, idx.searchsorted(closed, "right") - 1
    a, z = max(0, i0 - AROUND), min(len(idx), i1 + AROUND + 1)
    w = bars.iloc[a:z]
    return {"t": [f"{t:%Y-%m-%d %H:%M}" for t in w.index],
            **{k: w[col].round(6).tolist() for k, col in
               (("o", "Open"), ("h", "High"), ("l", "Low"), ("c", "Close"))},
            "entry": int(i0 - a), "exit": int(i1 - a), "held": int(i1 - i0)}


def gallery(trades: pd.DataFrame, bars: pd.DataFrame | None, pick: str,
            seed: int | None) -> dict:
    """The five tiles of one sample.

    Args:
        trades: One sample's trades of one strategy, in export order.
        bars: As in `window`.
        pick: "quantile" or "random".
        seed: For "random", the seed to reuse; None draws a fresh one and returns it.

    Returns:
        `{pick, seed, n, tiles}`; each tile has the trade's figures and its `bars`.
    """
    trades = trades.reset_index(drop=True)
    pnl = trades["Profit/Loss"].to_numpy()
    if pick == "random":
        seed = secrets.randbelow(10**6) if seed is None else seed
        picks = random_picks(pnl, seed)
    else:
        seed, picks = None, quantile_picks(pnl)
    tiles = []
    for row, label in picks:
        t = trades.loc[row]
        tiles.append({"label": label, "row": row, "type": str(t["Type"]),
                      "open_time": f"{t['Open time']:%Y-%m-%d %H:%M}",
                      "close_time": f"{t['Close time']:%Y-%m-%d %H:%M}",
                      "open_price": float(t["Open price"]), "close_price": float(t["Close price"]),
                      "pnl": float(t["Profit/Loss"]), "mae": float(t["MAE ($)"]),
                      "mfe": float(t["MFE ($)"]), "close_type": str(t["Close type"]),
                      "size": float(t["Size"]),
                      "bars": window(bars, t["Open time"], t["Close time"])})
    return {"pick": pick, "seed": seed, "n": len(trades), "tiles": tiles}
