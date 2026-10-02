"""The window-sweep tab: the free-placement nulls re-drawn inside ever smaller calendar blocks."""

import pandas as pd

from core.study import blocks, result as envelope
from core.symbols import alias
from studies.transfer.crossmarket.contract import shared, words
from studies.transfer.crossmarket.simulate import metrics, sweep

# No `sharpe`: per-run, unannualised (review pass 2026-09-30) — same reasoning as
# contract/nulls.py DRAWN.
METRICS = ("net", "ret_dd", "dd", "pf")
TRENDS = {"timing": "plano o decreciente: timing", "regime": "creciente: régimen",
          "no_pass": "sin pass a ningún tamaño", "unassessable": "no evaluable"}


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
        rows.append(alias(feed))
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
    """One market's p against block size, one column per swept model, as a table (§4.14, owner
    2026-09-30: a plot here invited reading a trend into three or four points; the table is
    the same numbers with no line to over-read).

    `feed` is already the short display name (`tab()` aliases it once before calling
    `market()`/`curve()`) — never a raw SQX symbol.
    """
    models = cfg["sweep"]["models"]
    body = [[window_name(w["window"]), *[_p(sw["points"][m][i], metric) for m in models]]
            for i, w in enumerate(sw["windows"])]
    columns = ["tamaño de bloque", *[words.NAMES[m] for m in models]]
    if sw["reference"] is not None:
        ref = sw["reference"][metric]
        body = [[*r, ref] for r in body]
        columns = [*columns, f"{words.NAMES[cfg['sweep']['reference']]} (referencia, plana)"]
    return {**blocks.table(f"p de «{metrics.LABELS[metric]}» según el tamaño de bloque — {feed}",
                           pd.DataFrame(body, columns=columns)),
            "select": {"mercado": feed, "estadístico": metrics.LABELS[metric]},
            "note": "Si p se mantiene bajo al encoger el bloque, el acierto sobrevive sin la "
                    "suerte de régimen: es timing. Si sube, el aprobado era herencia de "
                    "régimen. La referencia no converge con los demás: es otro eje, el "
                    "calendario y las rachas, no el tamaño del bloque."}


def market(sw: dict, cfg: dict, feed: str) -> list[dict]:
    """Everything the sweep keeps for one market, tagged by its selectors."""
    out = []
    for metric in METRICS:
        out.append(curve(sw, cfg, feed, metric))
        for model in cfg["sweep"]["models"]:
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


def model_list(models: list[str]) -> dict:
    """What each swept (free-placement) model does, title + short text (§4.14)."""
    return {"kind": "list", "title": "Qué hace cada modelo aquí", "items": [
        {"title": words.NAMES[m], "text": shared.text(words.EXPLAINED[m])} for m in models],
            "note": "Los tres son de colocación libre: destruyen a la vez régimen, calendario "
                    "y rachas al correr sobre la ventana completa. Aquí se confinan a bloques "
                    "cada vez más cortos, lo que devuelve el régimen y nada más."}


def tab(record: dict, cfg: dict) -> dict:
    """The window sweep on every market, behind four selectors."""
    s = cfg["sweep"]
    body = [grid(record, cfg, m, k) for m in s["models"] for k in METRICS]
    body.append(model_list(s["models"]))
    for feed, runs in record["runs"].items():
        body += market(runs["sweep"], cfg, alias(feed))
    feeds = [alias(f) for f in record["runs"]]
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
             "encoger el bloque devuelve el régimen y nada más, así que la tabla separa qué "
             "parte del p es acierto y qué parte herencia de régimen. El estadístico del "
             "veredicto sigue siendo Mean R bajo Calendar Shift; el selector es exploración y "
             "no lo mueve.")
