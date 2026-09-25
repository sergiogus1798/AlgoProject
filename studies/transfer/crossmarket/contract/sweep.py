"""The window-sweep tab: the free-placement nulls re-drawn inside ever smaller calendar blocks."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.transfer.crossmarket.contract import shared, words
from studies.transfer.crossmarket.simulate import metrics, sweep

METRICS = ("net", "mean_r", "ret_dd", "dd", "sharpe", "pf")
TRENDS = {"timing": "plano o decreciente: timing", "regime": "creciente: régimen",
          "no_pass": "sin pass a ningún tamaño", "unassessable": "no evaluable"}
REASONS = {"short_window": "ventana por debajo de sweep.min_months",
           "weak_blocks": "demasiadas operaciones en bloques débiles"}


def window_name(window: str) -> str:
    """"completa" for the whole window, "3 años" for 3y, "6 meses" for 6m."""
    if window == sweep.FULL:
        return "completa"
    count = int(window[:-1])
    return f"{count} " + {"y": ("año", "años"), "m": ("mes", "meses")}[window[-1]][count != 1]


def _p(point: dict, metric: str) -> float | None:
    """One point's p for one statistic, None where the point was withheld."""
    return None if point["table"] is None else point["table"][metric]["p_value"]


def grid(record: dict, cfg: dict, model: str, metric: str) -> dict:
    """Every market's sweep for one model and statistic: p per block size, trend beside it."""
    labels = sweep.ordered(cfg["sweep"]["windows"])
    rows, values, texts = [], [], []
    for feed, runs in record["runs"].items():
        sw = runs["sweep"]
        at = {w["window"]: pt for w, pt in zip(sw["windows"], sw["points"][model])}
        ps = [_p(at[w], metric) if w in at else None for w in labels]
        rows.append(feed)
        values.append(ps + [None])
        texts.append(["✕" if p is None else f"{p:.4f}" for p in ps]
                     + [TRENDS[sw["trend"][model][metric]]])
    alpha = cfg["diagnostics"]["alpha"]
    return {"kind": "grid", "title": "p por mercado y tamaño de bloque", "rows": rows,
            "cols": [window_name(w) for w in labels] + ["tendencia"], "values": values,
            "scale": "sequential", "levels": [alpha, 0.1, 0.25, 0.5], "labels": texts,
            "select": {"modelo": words.NAMES[model], "estadístico": metrics.LABELS[metric]},
            "note": "✕ es un tamaño que no se calculó: demasiadas operaciones en bloques "
                    "débiles o ventana demasiado corta. Nunca un número."}


def curve(sw: dict, cfg: dict, feed: str, metric: str) -> dict:
    """One market's p against block size, one series per swept model, the reference flat."""
    x = [window_name(w["window"]) for w in sw["windows"]]
    series = [{"label": words.NAMES[m], "values": [_p(pt, metric) for pt in sw["points"][m]],
               "role": "real"} for m in cfg["sweep"]["models"]]
    if sw["reference"] is not None:
        series.append({"label": words.NAMES[cfg["sweep"]["reference"]],
                       "values": [sw["reference"][metric]] * len(x), "role": "reference"})
    return {"kind": "lines", "title": f"p de «{metrics.LABELS[metric]}» según el tamaño de "
                                      f"bloque — {feed}", "unit": "p", "x": x, "series": series,
            "select": {"mercado": feed, "estadístico": metrics.LABELS[metric]},
            "note": "Si p se mantiene bajo al encoger, el acierto sobrevive sin la suerte de "
                    "régimen: es timing. Si sube, el aprobado era herencia de régimen. La "
                    "curva nunca converge a la referencia: es otro eje."}


def power(sw: dict, feed: str, model: str, metric: str) -> dict:
    """One model's sweep point by point, beside the counts that say how far to trust each p."""
    body = []
    for window, point in zip(sw["windows"], sw["points"][model]):
        used = [b for b in window["blocks"] if b["trades"]]
        counts = [b["trades"] for b in used]
        withheld = point["table"] is None
        body.append([window_name(window["window"]), len(window["blocks"]),
                     len(window["blocks"]) - len(used), min(counts), float(np.median(counts)),
                     sum(b["free"] for b in window["blocks"]),
                     min(b["free_share"] for b in used), window["weak_share"],
                     point["trades"], None if withheld else point["table"][metric]["std"],
                     REASONS[window["reason"]] if withheld else _p(point, metric)])
    return {**blocks.table(f"Potencia punto a punto — {feed} · {words.NAMES[model]}",
                           pd.DataFrame(body, columns=[
                               "ventana", "bloques", "vacíos", "ops/bloque mín",
                               "ops/bloque mediana", "hueco libre (velas)", "libre mín",
                               "ops en bloques débiles", "ops vivas por tirada",
                               "σ del nulo", "p"])),
            "select": {"mercado": feed, "modelo": words.NAMES[model],
                       "estadístico": metrics.LABELS[metric]}}


def blocks_table(sw: dict, feed: str) -> dict:
    """Every block of every window size on one market; they depend on trades, not the model."""
    body = [[window_name(w["window"]), f'{b["start"]} → {b["end"]}', b["bars"], b["trades"],
             b["occupied"], b["free"], b["free_share"],
             "" if not weak else "vacío" if not b["trades"] else "débil"]
            for w in sw["windows"] for b, weak in zip(w["blocks"], w["weak"])]
    return {**blocks.table(f"Bloques — {feed}", pd.DataFrame(body, columns=[
        "ventana", "bloque", "velas", "operaciones", "ocupadas", "libres", "libre", ""])),
            "select": {"mercado": feed}}


def market(sw: dict, cfg: dict, feed: str) -> list[dict]:
    """Everything the sweep keeps for one market, tagged by its selectors."""
    out = [blocks_table(sw, feed)]
    for metric in METRICS:
        out.append(curve(sw, cfg, feed, metric))
        for model in cfg["sweep"]["models"]:
            out.append(power(sw, feed, model, metric))
            for window, point in zip(sw["windows"], sw["points"][model]):
                if point["shapes"] is not None:
                    out.append({**shared.distribution(
                        point["shapes"][metric], metric,
                        f"Nulo confinado a bloques de {window_name(window['window'])} — "
                        f"{feed} · {words.NAMES[model]}", p=_p(point, metric)),
                        "select": {"mercado": feed, "modelo": words.NAMES[model],
                                   "estadístico": metrics.LABELS[metric],
                                   "ventana": window_name(window["window"])}})
    for model in cfg["sweep"]["models"]:
        for window, point in zip(sw["windows"], sw["points"][model]):
            if point["cone"] is not None:
                out.append({**shared.cone(point["cone"], f"Equity de las tiradas confinadas — "
                                          f"bloque {window_name(window['window'])}"),
                            "select": {"mercado": feed, "modelo": words.NAMES[model],
                                       "ventana": window_name(window["window"])}})
    return out


def tab(record: dict, cfg: dict) -> dict:
    """The window sweep on every market, behind four selectors."""
    s = cfg["sweep"]
    body = [grid(record, cfg, m, k) for m in s["models"] for k in METRICS]
    for feed, runs in record["runs"].items():
        body += market(runs["sweep"], cfg, feed)
    feeds = list(record["runs"])
    return envelope.tab(
        "sweep", "Barrido de ventana", body,
        selectors=[{"key": "modelo", "label": "Modelo",
                    "options": [words.NAMES[m] for m in s["models"]],
                    "default": words.NAMES[s["models"][0]]},
                   {"key": "estadístico", "label": "Estadístico",
                    "options": [metrics.LABELS[k] for k in METRICS],
                    "default": metrics.LABELS["net"]},
                   {"key": "mercado", "label": "Mercado", "options": feeds,
                    "default": feeds[0] if feeds else ""},
                   {"key": "ventana", "label": "Tamaño de bloque",
                    "options": [window_name(w) for w in sweep.ordered(s["windows"])],
                    "default": window_name(sweep.FULL)}],
        note="Los modelos de colocación libre destruyen a la vez régimen, calendario y "
             "rachas. Aquí se vuelven a sortear dentro de bloques cada vez más cortos: "
             "encoger el bloque devuelve el régimen y nada más, así que la curva separa qué "
             "parte del p es acierto y qué parte herencia de régimen. El estadístico del "
             "veredicto sigue siendo mean_r bajo block_shift; el selector es exploración.")
