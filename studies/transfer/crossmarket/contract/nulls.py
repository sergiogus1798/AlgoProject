"""The random-entry tabs: Entrada aleatoria per market, on the OOS stretch, and the models."""

import pandas as pd

from core.study import blocks, result as envelope
from core.symbols import alias
from studies.transfer.crossmarket.contract import shared, words
from studies.transfer.crossmarket.simulate import metrics
from studies.transfer.crossmarket.verdict import alerts

# §4.13 (owner, 2026-09-30): the histograms and the "with P" table show only these — never
# Mean R (removed from every selector, §1), Return on account or Min return per trade. The
# table keeps Longest losing run "aquí sí" (the one place the global exception applies).
# `sharpe` here is per-trade over one simulated run — the same scale market.py rejected for
# "Sharpe total" (2026-09-30, review pass): labelling it "Sharpe global" without annualising
# would repeat that exact mistake across ~2,900 histograms. Dropped rather than relabelled:
# annualising a per-run Sharpe over one simulated path needs its own daily equity per draw,
# which none of the three simulation families compute (`simulate/metrics.py::paths` only ever
# reduces to one scalar per run). "Sharpe total" stays only in the evidence table, computed
# once on the real backtest's daily equity.
DRAWN = ("net", "ret_dd", "dd", "pf")
TABLE_KEYS = ("net", "dd", "ret_dd", "pf", "losing_run")
# Warnings that are real findings, worth a reader's attention, are rendered; a few keys are
# either not a problem at all (no_drift: A is unaffected, and it is reported beside E anyway)
# or already explained in the tab's own note (selected_window, in oos_tab below) — §4.12,
# owner 2026-09-30. Hidden here still means computed: inference.warnings() is unchanged, and
# both keys still count in "avisos en total" (contract/backtest.py::breadth).
HIDDEN = {"no_drift", "selected_window"}
# The one warning the owner wants impossible to miss (§4.12): a KS test on the fitted holds
# rejecting means the null model built from them does not reproduce the real durations, and
# every p Fitted Distributions Sequence prints is then in doubt.
HIGHLIGHT = {"bad_hold_fit"}


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
                                                        f"{model}", keys=TABLE_KEYS),
               "select": where})
    return out


def headline_callout(record: dict, cfg: dict, metric: str = "pf") -> list[dict]:
    """One highlighted sentence per market (§4.13, owner 2026-09-30: "destacar con color" the
    beats-the-real-backtest sentence), from the headline model's shape for `metric`. Only one
    per market — not one per histogram, which would be a callout for every one of the ~180
    combinations this tab draws."""
    headline = cfg["nulls"]["headline"]
    out = []
    for feed, runs in record["runs"].items():
        shape = runs[headline]["shapes"][metric]
        worse = "sufrieron más" if not shape["higher_is_better"] else "rindieron peor"
        out.append({"kind": "callout", "state": "info", "select": {"mercado": alias(feed)},
                    "text": f"{alias(feed)}: el {shape['beats']:.1%} de las simulaciones "
                            f"{worse} que el backtest real en {metrics.LABELS[metric]}."})
    return out


def model_list(models: list[str]) -> dict:
    """One line per null model under the tab's tables, so a reader knows what each «modelo»
    of the selector re-laid without leaving for the Modelos tab."""
    return {"kind": "list", "title": "Los modelos, en una línea",
            "items": [{"title": words.NAMES[m], "text": words.SHORT[m]} for m in models],
            "note": "La explicación larga de cada uno, en la pestaña Modelos."}


def random_tab(record: dict, cfg: dict) -> dict:
    """Entrada aleatoria: every market × every null model, behind three selectors."""
    models = cfg["nulls"]["models"]
    body = headline_callout(record, cfg) + [
        b for feed, runs in record["runs"].items() for m in models
        for b in view(runs[m], cfg, {"mercado": alias(feed), "modelo": words.NAMES[m]},
                      alias(feed))] + [model_list(models)]
    markets = [alias(f) for f in record["runs"]]
    return envelope.tab(
        "random", words.TEST_1A, body,
        selectors=[{"key": "mercado", "label": "Mercado", "options": markets,
                    "default": markets[0] if markets else ""},
                   {"key": "modelo", "label": "Modelo nulo",
                    "options": [words.NAMES[m] for m in models],
                    "default": words.NAMES[cfg["nulls"]["headline"]]},
                   {"key": "estadístico", "label": "Estadístico",
                    "options": [metrics.LABELS[m] for m in DRAWN],
                    "default": metrics.LABELS["pf"]}],
        note=f"{cfg['nulls']['draws']:,} backtests aleatorios por cada mercado y cada modelo, "
             f"valorados con las mismas posiciones y los mismos costes que el real. Qué hace "
             f"cada modelo, en la pestaña Modelos.")


def warnings_table(rows: list[dict], title: str) -> dict:
    """Every real warning of these rows in its four parts: what, affects, spares, what to do."""
    body = [[alias(r["feed"]), shared.text(alerts.TEXTS[k][0]), alerts.TRIGGER[k](r),
             *[shared.text(t) for t in alerts.TEXTS[k][1:]]]
            for r in rows for k in r["warnings"] if k not in HIDDEN]
    return blocks.table(title, pd.DataFrame(
        body, columns=["mercado", "aviso", "qué lo disparó", "afecta a", "no afecta a",
                       "qué hacer"]),
        "Un aviso es contexto para leer el número, no un motivo para excluir el mercado."
        if body else "Ninguna comprobación saltó.")


def oos_tab(record: dict, cfg: dict) -> dict:
    """The same test on the base asset's declared out-of-sample stretch, alone."""
    oos = record.get("oos")
    if oos is None:
        return envelope.tab("oos", f"{words.TEST_1A} · OOS principal", [],
                            note="Este activo base no declara ningún tramo fuera de muestra en "
                                 "assets/_markets.yaml (out_of_sample): no hay nada que probar.")
    span, row, shown = oos["span"], oos["row"], alias(oos["row"]["feed"])
    headline_shape = oos["runs"][cfg["nulls"]["headline"]]["shapes"]["pf"]
    worse = "sufrieron más" if not headline_shape["higher_is_better"] else "rindieron peor"
    body = [{"kind": "callout", "state": "info",
             "text": f"El {headline_shape['beats']:.1%} de las simulaciones {worse} que el "
                     f"backtest real en {metrics.LABELS['pf']}."}]
    body += [b for m in cfg["nulls"]["models"]
            for b in view(oos["runs"][m], cfg, {"modelo": words.NAMES[m]}, shown)]
    body.append(warnings_table([row], "Qué hay que desconfiar de estos números"))
    return envelope.tab(
        "oos", f"{words.TEST_1A} · OOS principal", body,
        selectors=[{"key": "modelo", "label": "Modelo nulo",
                    "options": [words.NAMES[m] for m in cfg["nulls"]["models"]],
                    "default": words.NAMES[cfg["nulls"]["headline"]]},
                   {"key": "estadístico", "label": "Estadístico",
                    "options": [metrics.LABELS[m] for m in DRAWN],
                    "default": metrics.LABELS["pf"]}],
        note=f"{words.TEST_1A} sobre {alias(oos['feed'])} recortado a {span['from']} – "
             f"{span['to']}, el tramo que la estrategia no optimizó: {row['trades_all']} de "
             f"sus {oos['of']} operaciones viven enteras dentro. No cuenta con los demás "
             f"mercados — es el mismo, sobre fechas que solapan — y las condiciones de "
             f"aceptación del proyecto lo leyeron ya, así que un p bajo aquí no es una "
             f"afirmación sobre datos que nadie hubiera mirado.")


def p_by_model(record: dict, cfg: dict, k: str) -> dict:
    """Market × model, p of one statistic (§4.14, owner 2026-09-30: was a bars chart per
    market; a table reads all markets at once). Coloured pass/fail at diagnostics.alpha, and
    `threshold` (2026-09-30, one editable cut for every model column at once, next to the
    «P de qué estadístico» selector) recolours all of them the instant the reader tries another."""
    models = cfg["nulls"]["models"]
    alpha = cfg["diagnostics"]["alpha"]
    rows = [[alias(feed), *[runs[m]["table"][k]["p_value"] for m in models]]
            for feed, runs in record["runs"].items()]
    states = [[None] + ["pass" if p <= alpha else "fail" for p in row[1:]] for row in rows]
    return {**blocks.table(f"p por modelo — {metrics.LABELS[k]}", pd.DataFrame(
        rows, columns=["mercado", *[words.NAMES[m] for m in models]])),
        "states": states, "select": {"estadístico": metrics.LABELS[k]},
        "threshold": {"column": [words.NAMES[m] for m in models], "default": alpha}}


def models_tab(record: dict, cfg: dict) -> dict:
    """Each null model's p per market for a chosen statistic, and what each model randomises."""
    # §4.14: no Mean R (the verdict's own, fixed in advance), no Longest losing run here, and
    # no Sharpe (per-run, unannualised — see DRAWN above; a mislabelled "Sharpe global" here
    # would be the exact bug this review pass removed).
    keys = ("net", "dd", "ret_dd", "pf")
    body = [p_by_model(record, cfg, k) for k in keys]
    body.append({"kind": "list", "title": "Qué hace cada modelo", "items": [
        {"title": words.NAMES[m], "text": shared.text(words.EXPLAINED[m])}
        for m in cfg["nulls"]["models"]]})
    return envelope.tab(
        "models", "Modelos", body,
        selectors=[{"key": "estadístico", "label": "p de qué estadístico",
                    "options": [metrics.LABELS[k] for k in keys],
                    "default": metrics.LABELS["net"]}],
        note=f"Cada modelo corre sus {cfg['nulls']['draws']:,} simulaciones en cada mercado. "
             f"El p del resumen — el que decide el veredicto — es el de "
             f"{words.NAMES[cfg['nulls']['headline']]} sobre Mean R, elegido de antemano; **no** "
             f"es ninguno de los que este selector muestra. El selector es exploración: mirar "
             f"cinco estadísticos y quedarse con el mejor p es hacerse trampas, y el veredicto "
             f"no cambia sea lo que sea lo que aquí se elija.")
