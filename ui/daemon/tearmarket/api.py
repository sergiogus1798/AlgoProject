"""The tear sheet's market routes: month signs against the underlying, and the trade gallery."""

import time

from fastapi import APIRouter

from core import barstore
from core.study.blocks import validate
from ui.daemon.tearmarket import months, source, trades

ROUTER = APIRouter()


def _strategy(project: str, databank: str, identity: str) -> dict | str:
    """The newest harvest and the strategy's name and timeframe, or the refusal sentence.

    Args:
        project, databank, identity: As the window sent them.

    Returns:
        `{harvest, name, tf}` or the sentence.
    """
    wrong = source.bad_name(project, databank, identity)
    if wrong:
        return wrong
    harvest = source.newest(project, databank)
    if harvest is None:
        return source.NO_HARVEST
    got = source.described(harvest, identity)
    if got is None:
        return (f"La identidad {identity[:12]}… no está en la cosecha {harvest.name} de "
                f"{databank}: las identidades solo casan dentro de un databank.")
    return {"harvest": harvest, **got}


def _bars(project: str, databank: str, asset: str, tf: str) -> tuple[dict | str, object]:
    """The asset's bars at the strategy's timeframe, or why there are none.

    Args:
        project, databank: As the window sent them.
        asset: The owner's override, empty to read it off the project's name.
        tf: The strategy's timeframe.

    Returns:
        (`market()` dict or refusal sentence, the bars frame or None).
    """
    m = source.market(project, databank, asset)
    if isinstance(m, str):
        return m, None
    if tf not in barstore.RULE:
        return f"No sé remuestrear el timeframe «{tf}» desde M1.", None
    return m, source.bars(m["feed"], tf, m["end"])


@ROUTER.get("/api/tearsheet/market")
def market(project: str = "", databank: str = "", identity: str = "", asset: str = "") -> dict:
    """Item 5: how many months the strategy and its market moved each way, IS and OOS apart.

    Args:
        project, databank, identity: One strategy inside one databank.
        asset: The owner's override of the asset, empty to read it off the project's name.

    Returns:
        A contract dict (tabs «IS», «OOS»: a 2×2 table and the same counts as bars with the
        both-down cell in `watch`), or `{"error": sentence}`.
    """
    t0 = time.perf_counter()
    try:
        s = _strategy(project, databank, identity)
        if isinstance(s, str):
            return {"error": s}
        m, bars = _bars(project, databank, asset, s["tf"])
        if isinstance(m, str):
            return {"error": m}
        equity = source.rows(s["harvest"], "equity", identity)
        foreign = source.foreign_samples(equity)
        if foreign:
            return {"error": foreign}
        meta = {"project": project, "databank": databank, "identity": identity,
                "name": s["name"], "tf": s["tf"], "day": s["harvest"].name, **m,
                "wall_s": round(time.perf_counter() - t0, 3)}
        return validate(months.result(meta, equity, bars))
    except Exception as e:  # noqa: BLE001 — the boundary with a person: a sentence, never a 500
        return {"error": f"No pude contar los meses: {type(e).__name__}: {e}"}


@ROUTER.get("/api/tearsheet/trades")
def trade_gallery(project: str = "", databank: str = "", identity: str = "", sample: str = "IS",
                  pick: str = "quantile", seed: str = "", asset: str = "") -> dict:
    """Item 6: five trades of one sample with the bars around each.

    Args:
        project, databank, identity: One strategy inside one databank.
        sample: "IS" or "OOS"; nothing else is read.
        pick: "quantile" (P&L quantiles 0/25/50/75/100 %) or "random".
        seed: For "random", a seed to redraw the same five; empty draws a new one.
        asset: The owner's override of the asset, empty to read it off the project's name.

    Returns:
        `{project, databank, identity, name, sample, tf, harvest_day, asset, feed,
        bars_note, pick, seed, n, tiles}`, or `{"error": sentence}`. Unknown bars do not
        refuse: each tile then says its bars are missing.
    """
    if sample not in source.SAMPLES:
        return {"error": f"Muestra «{sample}» no válida: solo IS u OOS."}
    if pick not in ("quantile", "random"):
        return {"error": f"Selección «{pick}» no válida: cuantil o al azar."}
    if seed and not seed.isdigit():
        return {"error": f"La semilla «{seed}» no es un entero."}
    try:
        s = _strategy(project, databank, identity)
        if isinstance(s, str):
            return {"error": s}
        rows = source.rows(s["harvest"], "trades", identity)
        foreign = source.foreign_samples(rows)
        if foreign:
            return {"error": foreign}
        rows = rows[rows["sample"] == sample]
        if rows.empty:
            return {"error": f"La estrategia no tiene operaciones {sample} en la cosecha."}
        m, bars = _bars(project, databank, asset, s["tf"])
        got = trades.gallery(rows, bars, pick, int(seed) if seed else None)
        return {"project": project, "databank": databank, "identity": identity,
                "name": s["name"], "sample": sample, "tf": s["tf"],
                "harvest_day": s["harvest"].name,
                "asset": m.get("asset") if isinstance(m, dict) else None,
                "feed": m.get("feed") if isinstance(m, dict) else None,
                "bars_note": m if isinstance(m, str) else "", **got}
    except Exception as e:  # noqa: BLE001 — the boundary with a person: a sentence, never a 500
        return {"error": f"No pude leer las operaciones: {type(e).__name__}: {e}"}
