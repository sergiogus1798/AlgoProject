"""One strategy's dependence on deep trades, build and oos1 side by side, as the contract's data."""

import time
from typing import Any

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.screening.maeDepth import measures

MODULE = "maeDepth"
GLOSSARY = [
    {
        "term": "Operación profunda",
        "text": "Una operación que en algún momento estuvo a k ATR "
        "o más en contra (MAE en ATR del ATR(20) de SQX de la barra cerrada antes de la entrada).",
    },
    {
        "term": "Recuperada",
        "text": "Una operación profunda que cerró en ganancia neta: en el "
        "backtest cuenta como una ganadora más, y con un stop habría sido una perdedora.",
    },
    {
        "term": "Anómala",
        "text": "Profunda Y de duración anómala: media + 2,5 desviaciones de las "
        "duraciones de esa estrategia en ese tramo, contadas en barras. Es el retrato de aguantar "
        "una perdedora hasta que vuelve.",
    },
    {
        "term": "Neto cortado",
        "text": "El neto que quedaría si cada operación profunda se hubiera "
        "cerrado en -(k + deslizamiento) ATR. Es una cota, no un backtest de stop: un stop real se "
        "llena con hueco y deslizamiento, y por eso se enseñan tres deslizamientos.",
    },
]
SEGMENTS = ("build", "oos1")


def table_rows(got: dict, cfg: dict) -> pd.DataFrame:
    """The measures of `measures.one_segment` laid out one per row, a column per segment."""
    rows = [
        ("operaciones", "n"),
        ("neto", "net"),
        ("duración media (barras)", "dur_mean"),
        ("corte de duración (barras)", "dur_cut"),
        ("operaciones por encima del corte", "n_long"),
        ("peor MAE (ATR)", "peor_mae"),
        ("fecha del peor MAE", "peor_fecha"),
        ("MAE p95 de ganadoras (ATR)", "mae_p95_ganadoras"),
    ]
    for k in cfg["depth"]["k"]:
        for scope, name in (("prof", "profundas"), ("anom", "anómalas")):
            for key, label in (
                ("n", "n"),
                ("frac", "fracción"),
                ("n_rec", "n recuperadas"),
                ("cuota_rec", "cuota del neto de las recuperadas"),
            ):
                rows.append((f"{name} ≥{k:g} ATR · {label}", f"{scope}{k:g}_{key}"))
            for s in cfg["depth"]["slippage"]:
                rows.append(
                    (
                        f"{name} ≥{k:g} ATR · neto cortado (desl. {s:g})",
                        f"{scope}{k:g}_cortado_{s:g}",
                    )
                )
    return pd.DataFrame(
        {
            "medida": [r[0] for r in rows],
            **{s: [got[s].get(r[1]) for r in rows] for s in SEGMENTS if s in got},
        }
    ).astype(object)


def run(
    strategy: str, identity: str, measured: pd.DataFrame, cfg: dict
) -> dict[str, Any]:
    """The strategy's deep-trade reading.

    Args:
        strategy: Its name.
        identity: Its identity.
        measured: `measures.per_trade` rows of this strategy with `segment` ("build"/"oos1").
        cfg: What `inputs.config` returned.

    Returns:
        The contract dict: a table with build and oos1 side by side, and the MAE in ATR of
        winners against losers, one histogram per segment.
    """
    started = time.time()
    got = {s: measures.one_segment(g, cfg) for s, g in measured.groupby("segment")}
    hist = []
    for s, g in measured.groupby("segment"):
        win = g["winner"].to_numpy()
        hist.append(
            blocks.distribution(
                f"MAE en ATR — {s}",
                "ATR",
                g["mae_atr"].to_numpy(),
                None,
                "Ganadoras contra perdedoras. Una ganadora con MAE muy a la derecha es una "
                "recuperada.",
                series={
                    label: v
                    for label, v in (
                        ("ganadoras", g["mae_atr"].to_numpy()[win]),
                        ("perdedoras", g["mae_atr"].to_numpy()[~win]),
                    )
                    if len(v)
                },
            )
        )
    side = blocks.table(
        "Build y oos1 lado a lado",
        table_rows(got, cfg),
        "El contrafactual es una cota, no un backtest de stop (§2.1).",
    )
    return envelope.envelope(
        MODULE,
        strategy,
        identity,
        cfg,
        started,
        [envelope.tab("estrategia", "La estrategia", [side, *hist])],
        glossary=GLOSSARY,
        summary={
            s: {k: v for k, v in d.items() if isinstance(v, float) and np.isfinite(v)}
            for s, d in got.items()
        },
    )
