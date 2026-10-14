"""Every strategy of one harvest through the deep-trade reading: one panel, one population result."""

import math
import time
from typing import Any, cast

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.screening.maeDepth import measures, one

MODULE = one.MODULE


def panel(measured: pd.DataFrame, names: pd.Series, cfg: dict) -> pd.DataFrame:
    """One row per strategy: every measure of both segments side by side, and the verdict.

    Args:
        measured: `measures.per_trade` rows of the whole harvest with `identity` and `segment`.
        names: Identity -> strategy name.
        cfg: What `inputs.config` returned.

    Returns:
        Indexed by strategy name; columns `<measure>_<segment>`, `marcada`, `verdict` and
        `decil_profundas` (the decile of the build's deep-trade share among the strategies,
        informative only). `marcada` needs `verdict.min_cuota_rec`; unset, nobody is marked.
    """
    rows: dict[Any, dict[str, Any]] = {}
    for key, g in measured.groupby(["identity", "segment"], observed=True):
        identity, segment = cast(tuple, key)
        rows.setdefault(identity, {"identity": identity}).update(
            {f"{k}_{segment}": v for k, v in measures.one_segment(g, cfg).items()})
    out = pd.DataFrame(rows).T
    out["strategy"] = names.reindex(out.index)
    out = out.set_index("strategy")
    bar = cfg["verdict"]["min_cuota_rec"]
    cols = [f"anom{k:g}_cuota_rec_{s}" for k in cfg["depth"]["k"] for s in one.SEGMENTS]
    cols = [c for c in cols if c in out]
    out["marcada"] = (out[cols].astype(float).ge(bar).any(axis=1) if bar is not None
                      else False)
    out["verdict"] = np.where(out["marcada"] & (cfg["verdict"]["action"] == "drop"),
                              "DESCARTAR", "MANTENER")
    first = f"prof{cfg['depth']['k'][0]:g}_frac_build"
    if first in out:
        out["decil_profundas"] = (out[first].astype(float).rank(pct=True) * 10).apply(
            lambda r: math.ceil(r) if np.isfinite(r) else None)
    return out


def run(measured: pd.DataFrame, names: pd.Series, cfg: dict) -> dict[str, Any]:
    """The population's reading.

    Returns:
        {"population": the contract dict, "panel": what `panel` returned}.
    """
    started = time.time()
    p = panel(measured, names, cfg)
    ks = cfg["depth"]["k"]
    show = ["n_build", "n_long_build", "dur_cut_build"] + [
        f"{x}{k:g}_{y}_{s}" for k in ks for s in one.SEGMENTS
        for x, y in (("prof", "n_rec"), ("prof", "cuota_rec"), ("anom", "n"), ("anom", "cuota_rec"))
    ] + ["marcada"]
    shown = p[[c for c in show if c in p]].reset_index()
    dist = []
    for k in ks:
        series = {s: p[f"anom{k:g}_cuota_rec_{s}"].astype(float).dropna().to_numpy()
                  for s in one.SEGMENTS if f"anom{k:g}_cuota_rec_{s}" in p}
        series = {s: v for s, v in series.items() if len(v)}     # the block cannot draw an empty one
        if series:
            dist.append(blocks.distribution(
                f"Cuota del neto que dan las anómalas recuperadas — k = {k:g} ATR", "",
                np.concatenate(list(series.values())), None,
                "Una estrategia sin neto positivo en el tramo no tiene cuota y no aparece.",
                series=series))
    bar = cfg["verdict"]["min_cuota_rec"]
    marked = int(p["marcada"].sum())
    note = (f"{marked} de {len(p)} marcadas con cuota ≥ {bar}." if bar is not None else
            "Sin umbral fijado (decisión del dueño): ninguna marcada, sólo medidas.")
    table = blocks.table("Cada estrategia", shown, note)
    population = envelope.envelope(
        MODULE, None, None, cfg, started,
        [envelope.tab("poblacion", "La población", [table, *dist], note=note)],
        glossary=one.GLOSSARY)
    return {"population": population, "panel": p}
