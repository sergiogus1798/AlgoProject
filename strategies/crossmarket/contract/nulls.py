"""The random-entry tabs: 1a per market, 1a on the base asset's own OOS stretch, and the models."""

import pandas as pd

from core.study import blocks, result as envelope
from strategies.crossmarket.contract import shared, words
from strategies.crossmarket.simulate import metrics
from strategies.crossmarket.verdict import alerts

# The statistics that get a histogram; mean_r leads because the summary's p is its.
DRAWN = ("mean_r", "net", "ret_dd", "dd", "sharpe", "pf")


def view(run: dict, cfg: dict, where: dict, name: str) -> list[dict]:
    """One market under one null model: its cone, a histogram per statistic, its table.

    Args:
        run: backtest.run()'s result for that market and model.
        cfg: What config.load() returned.
        where: The selector values these blocks belong to, e.g. {"mercado", "modelo"}.
        name: The market as shown.

    Returns:
        Blocks tagged with `where`, each histogram also with its statistic.
    """
    draws = cfg["nulls"]["draws"]
    model = words.NAMES[run["model"]]
    out = [{**shared.cone(run["cone"], f"Equity en calendario — {name} · {model}",
                          f"{draws:,} simulaciones"), "select": where}]
    out += [{**shared.distribution(run["shapes"][m], m, f"{metrics.LABELS[m]} — {name} · "
                                   f"{model}", p=run["table"][m]["p_value"]),
             "select": {**where, "estadístico": metrics.LABELS[m]}} for m in DRAWN]
    out.append({**shared.metric_table(run["table"], cfg, f"Todos los estadísticos — {name} · "
                                                        f"{model}"), "select": where})
    return out


def random_tab(record: dict, cfg: dict) -> dict:
    """Test 1a: every market × every null model, behind three selectors."""
    models = cfg["nulls"]["models"]
    body = [b for feed, runs in record["runs"].items() for m in models
            for b in view(runs[m], cfg, {"mercado": feed, "modelo": words.NAMES[m]}, feed)]
    return envelope.tab(
        "random", "Entrada aleatoria (1a)", body,
        selectors=[{"key": "mercado", "label": "Mercado", "options": list(record["runs"]),
                    "default": next(iter(record["runs"]), "")},
                   {"key": "modelo", "label": "Modelo nulo",
                    "options": [words.NAMES[m] for m in models],
                    "default": words.NAMES[cfg["nulls"]["headline"]]},
                   {"key": "estadístico", "label": "Estadístico",
                    "options": [metrics.LABELS[m] for m in DRAWN],
                    "default": metrics.LABELS["mean_r"]}],
        note=f"{cfg['nulls']['draws']:,} backtests aleatorios por cada mercado y cada modelo, "
             f"valorados con las mismas posiciones y los mismos costes que el real. Qué hace "
             f"cada modelo, en la pestaña Modelos.")


def warnings_table(rows: list[dict], title: str) -> dict:
    """Every warning of these rows in its four parts: what, affects, spares, what to do."""
    body = [[r["feed"], shared.text(alerts.TEXTS[k][0]), alerts.TRIGGER[k](r),
             *[shared.text(t) for t in alerts.TEXTS[k][1:]]]
            for r in rows for k in r["warnings"]]
    return blocks.table(title, pd.DataFrame(
        body, columns=["mercado", "aviso", "qué lo disparó", "afecta a", "no afecta a",
                       "qué hacer"]),
        "Ningún mercado se excluye por esto: un aviso es contexto para leer el número."
        if body else "Ninguna comprobación saltó.")


def oos_tab(record: dict, cfg: dict) -> dict:
    """The same 1a on the base asset's declared out-of-sample stretch, alone."""
    oos = record.get("oos")
    if oos is None:
        return envelope.tab("oos", "Entrada aleatoria · OOS principal", [],
                            note="Este activo base no declara ningún tramo fuera de muestra en "
                                 "assets/_markets.yaml (out_of_sample): no hay nada que probar.")
    span, row, shown = oos["span"], oos["row"], oos["row"]["feed"]
    body = [b for m in cfg["nulls"]["models"]
            for b in view(oos["runs"][m], cfg, {"modelo": words.NAMES[m]}, shown)]
    body.append(warnings_table([row], "Qué hay que desconfiar de estos números"))
    return envelope.tab(
        "oos", "Entrada aleatoria · OOS principal", body,
        selectors=[{"key": "modelo", "label": "Modelo nulo",
                    "options": [words.NAMES[m] for m in cfg["nulls"]["models"]],
                    "default": words.NAMES[cfg["nulls"]["headline"]]},
                   {"key": "estadístico", "label": "Estadístico",
                    "options": [metrics.LABELS[m] for m in DRAWN],
                    "default": metrics.LABELS["mean_r"]}],
        note=f"El test 1a sobre {oos['feed']} recortado a {span['from']} – {span['to']}, el "
             f"tramo que la estrategia no optimizó: {row['trades_all']} de sus {oos['of']} "
             f"operaciones viven enteras dentro. No cuenta con los demás mercados — es el "
             f"mismo, sobre fechas que solapan — y no es dato virgen: las condiciones de "
             f"aceptación del proyecto lo leyeron.")


def models_tab(record: dict, cfg: dict) -> dict:
    """Each null model's p per market for a chosen statistic, and what each model randomises."""
    alpha = cfg["diagnostics"]["alpha"]
    body = [{"kind": "bars", "title": f"p por modelo — {feed} · {metrics.LABELS[k]}",
             "unit": "p", "reference": alpha, "select": {"estadístico": metrics.LABELS[k]},
             "items": [{"label": words.NAMES[m], "value": runs[m]["table"][k]["p_value"],
                        "error": None,
                        "state": "pass" if runs[m]["table"][k]["p_value"] <= alpha else "fail"}
                       for m in cfg["nulls"]["models"]]}
            for feed, runs in record["runs"].items() for k in metrics.TABLED]
    body.append(blocks.table("Qué hace cada modelo", pd.DataFrame(
        [[words.NAMES[m], m, words.RANDOMISES[m], shared.text(words.EXPLAINED[m])]
         for m in cfg["nulls"]["models"]],
        columns=["modelo", "clave", "aleatoriza", "qué añade"]), shared.text(words.RETIRED)))
    return envelope.tab(
        "models", "Modelos", body,
        selectors=[{"key": "estadístico", "label": "p de qué estadístico",
                    "options": [metrics.LABELS[k] for k in metrics.TABLED],
                    "default": metrics.LABELS["mean_r"]}],
        note=f"Cada modelo corre sus {cfg['nulls']['draws']:,} simulaciones en cada mercado. "
             f"El p del resumen es el de {words.NAMES[cfg['nulls']['headline']]} sobre "
             f"{metrics.LABELS['mean_r']}, elegido de antemano; el selector es exploración: "
             f"mirar siete estadísticos y quedarse con el mejor p es hacerse trampas.")
