"""Step 18 as the contract's blocks: the outputs against their null, the cloud, the curves, who is chosen."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.optimisation.cscv import words
from studies.optimisation.cscv.measure import outputs

YEAR = np.sqrt(52.0)        # a weekly Sharpe shown per year; a constant moves no rank
SHOWN, TOP, DASH = 400, 15, "—"


def pct(x: float | None) -> str:
    """A fraction as «29,2 %»."""
    return DASH if x is None or x != x else f"{x:.1%}".replace(".", ",").replace("%", " %")


def dec(x: float | None) -> str:
    """A number with two decimals and a comma, signed: «−0,57»."""
    return DASH if x is None or x != x else f"{x:+.2f}".replace(".", ",").replace("-", "−")


def verdict(facts: dict, cfg: dict) -> dict:
    """The state with its sentence; the numbers that decided go as parts."""
    said, cuts = facts["estado"], cfg["state"]
    if "p_perdida" not in facts:
        return blocks.verdict(words.LABEL[said], words.STATE[said], words.MEANING["sin_dato"].format(
            n=facts["n"], need=cfg["panel"]["min_variants"]))
    lost, over = facts["p_perdida"], bool(facts["pbo_sobre_p95"])
    meaning = {"pasa": words.MEANING["pasa"] + words.MEANING["estable"] * facts["orden_estable"],
               "limbo": words.MEANING["limbo"].format(
                   got=lost, pct=cuts["p_perdida_null_pct"], top=facts["nulo"]["p_perdida_p95"],
                   fail=cuts["p_perdida_fail"]),
               "no_pasa": " ".join(
                   [words.MEANING["perdida"].format(got=lost, fail=cuts["p_perdida_fail"])]
                   * (lost >= cuts["p_perdida_fail"])
                   + [words.MEANING["p95"].format(got=facts["pbo"], p95=facts["nulo"]["pbo_p95"])]
                   * over)}[said]
    parts = [{"label": "P de pérdida", "value": lost,
              "note": f"p95 del nulo {pct(facts['nulo']['p_perdida_p95'])}. " + words.WHAT["p_perdida"],
              "state": "fail" if lost >= cuts["p_perdida_fail"] else
              "watch" if facts["p_perdida_sobre_p95"] else "pass"},
             {"label": "PBO contra el p95 de su nulo", "value": facts["pbo"],
              "note": f"p95 del nulo {pct(facts['nulo']['pbo_p95'])}. " + words.WHAT["pbo"],
              "state": "fail" if over else "pass"}]
    return blocks.verdict(words.LABEL[said] + words.STABLE * (said == "pasa" and facts["orden_estable"]),
                          words.STATE[said], meaning, f"P pérdida {pct(lost)}", parts)


def filters(counts: dict) -> dict:
    """What each filter of the panel removed."""
    rows = [("Variantes del lote", counts["lote"]), ("Controles (canarios, pares inertes)", counts["controles"]),
            ("Sin operaciones", counts["sin_operaciones"]),
            (f"Duplicados exactos ({pct(counts['duplicados_pct'])})", counts["duplicados"]),
            (f"Bajo el suelo por parámetro vivo ({counts['vivos']} vivos)", counts["suelo_parametros"]),
            ("Bajo el suelo por año", counts["suelo_anual"]), ("Entran en el panel", counts["quedan"])]
    return blocks.table("El panel: qué variantes entran", pd.DataFrame(rows, columns=["Filtro", "Variantes"]),
                        words.WHAT["duplicados"])


def reading(facts: dict) -> dict:
    """The outputs of the method, each beside its null and with what it is."""
    null, gross = facts["nulo"], facts["bruto"]
    rows = [("PBO (neto)", pct(facts["pbo"]), pct(null["pbo_p5"]), pct(null["pbo_mediana"]),
             pct(null["pbo_p95"]), dec(facts["pbo_p"]), words.WHAT["pbo"]),
            ("PBO (bruto)", pct(gross["pbo"]), pct(gross["nulo_p5"]), DASH, pct(gross["nulo_p95"]),
             dec(gross["pbo_p"]), words.WHAT["pbo_bruto"]),
            ("β de la degradación", dec(facts["beta"]), dec(null["beta_p5"]), dec(null["beta_mediana"]),
             dec(null["beta_p95"]), dec(facts["beta_p"]), words.WHAT["beta"]),
            ("R² de la degradación", dec(facts["r2"]), DASH, dec(null["r2_mediana"]), DASH, DASH,
             words.WHAT["r2"]),
            ("P de pérdida", pct(facts["p_perdida"]), DASH, pct(null["p_perdida"]),
             pct(null["p_perdida_p95"]), DASH,
             words.WHAT["p_perdida"]),
            ("Recorte del Sharpe (HC)", pct(facts["hc"]), DASH, pct(null["hc_mediana"]), DASH, DASH,
             words.WHAT["hc"])]
    table = blocks.table("Las salidas del método, contra su nulo", pd.DataFrame(rows, columns=[
        "Salida", "Real", "Nulo p5", "Nulo mediana", "Nulo p95", "p", "Qué es"]),
        f"{null['sorteos']} sorteos del nulo. " + words.WHAT["p"])
    return table | {"align": ["left"] + ["right"] * 5 + ["left"]}


def curves(got: dict) -> dict:
    """The three distribution functions of the out-of-sample Sharpe, on the histogram's bins."""
    found = got["found"]
    edge = np.linspace(found["lo"], found["hi"], len(found["hist"]) + 1)[1:] * YEAR
    lines = {"elegir (la mejor de dentro)": outputs.cdf(found["sr_out"], found),
             "elegir al azar (todas las variantes)": found["hist"].cumsum() / found["hist"].sum()}
    if "track_out" in found:
        lines["la madre"] = outputs.cdf(found["track_out"], found)
    keep = blocks.thin(len(edge), 128)
    return {"kind": "lines", "title": "Dominancia: ¿elegir supera al azar en toda la distribución?",
            "unit": "", "x": [float(edge[i]) for i in keep], "note": words.NOTE["curvas"],
            "series": [{"label": name, "values": [float(v[i]) for i in keep],
                        "role": "reference" if "azar" in name else "real"} for name, v in lines.items()]}


def dominance(facts: dict) -> dict:
    """First and second order, the gap, and how often the null shows each."""
    dom, mother = facts["dominancia"], facts.get("madre")
    word = {1: "sí", 0: "no"}
    rows = [("Elegir, contra el azar", word[dom["primer_orden"]], word[dom["segundo_orden"]], dec(dom["brecha"])),
            ("Nulo: sorteos en que se da", pct(dom["nulo_primer_orden"]), pct(dom["nulo_segundo_orden"]), DASH)]
    if mother:
        rows.insert(1, ("La madre, contra el azar", word[mother["primer_orden"]],
                        word[mother["segundo_orden"]], dec(mother["brecha"])))
    return blocks.table("Dominancia estocástica", pd.DataFrame(rows, columns=[
        "Lista", "Primer orden", "Segundo orden", "Brecha máxima"]), "") | {
        "help": [None, words.WHAT["primer_orden"], words.WHAT["segundo_orden"], words.WHAT["brecha"]]}


def cloud(got: dict) -> dict:
    """The paper's degradation cloud, thinned for the page; the line is fitted on every partition."""
    found, real = got["found"], got["read"]["real"]
    keep = blocks.thin(len(found["sr_in"]), SHOWN)
    r = float(np.corrcoef(found["sr_in"], found["sr_out"])[0, 1])
    return {"kind": "scatter", "title": "Degradación: Sharpe fuera de la elegida contra su Sharpe dentro",
            "x_label": "Sharpe anual dentro", "y_label": "Sharpe anual fuera", "quadrants": False,
            "note": words.NOTE["nube"].format(shown=len(keep), total=len(found["sr_in"])),
            "points": [{"x": float(found["sr_in"][i] * YEAR), "y": float(found["sr_out"][i] * YEAR),
                        "label": str(got["names"][found["pick"][i]]), "group": "partición"} for i in keep],
            "fit": {"slope": real["beta"], "intercept": real["alfa"] * YEAR, "r": r}}


def tabs(got: dict, perf: dict, cfg: dict) -> list[dict]:
    """The study's page for one mother.

    Args:
        got: One mother of `many.run`.
        perf: The queue's own numbers, `many.run`'s second value.
        cfg: The study's config.

    Returns:
        «Lectura» (the outputs against their null, the null's PBO, the logits, the panel),
        «Degradación y dominancia», «Selección y madre», «Potencia y coste»; only the panel's
        table when there was too little to measure.
    """
    facts = got["facts"]
    if "found" not in got:
        return [envelope.tab("lectura", "Lectura", [filters(got["counts"])])]
    found, null, chosen = got["found"], got["draws"]["nulo"], got["read"]["seleccion"]
    lam = np.log(found["omega"] / (1 - found["omega"]))
    weeks = cfg["null"]["block_weeks"]
    first = [reading(facts),
             blocks.distribution("El PBO sin nada que elegir (nulo)", "%", null["pbo"].to_numpy() * 100,
                                 facts["pbo"] * 100, words.NOTE["nulo"].format(weeks=weeks),
                                 p=facts["pbo_p"], sign_shade=False),
             blocks.distribution("Logit del puesto fuera de la elegida (λ)", "", lam, None,
                                 words.NOTE["logit"]),
             filters(got["counts"])]
    second = [cloud(got),
              blocks.distribution("La β de la degradación sin nada que elegir (nulo)", "",
                                  null["beta"].to_numpy(), facts["beta"], words.WHAT["beta"],
                                  p=facts["beta_p"], sign_shade=False),
              curves(got), dominance(facts)]
    third = [{"kind": "bars", "title": "Frecuencia de selección", "unit": "%", "reference": None,
              "note": f"{chosen['distintas']} variantes distintas salen elegidas; la más elegida, "
                      f"{chosen['mas_elegida']}, en el {pct(chosen['peso'])}. " + words.WHAT["seleccion"],
              "items": [{"label": name, "value": share * 100, "error": None, "state": "info"}
                        for name, share in chosen["tabla"][:TOP]]}]
    if "madre" in facts:
        m = facts["madre"]
        third.append(blocks.table("La madre, como una lista más", pd.DataFrame([
            ("Puesto mediano fuera", dec(m["puesto_mediano"]), words.WHAT["puesto_mediano"]),
            ("Por encima de la mitad", pct(m["sobre_mediana"]), words.WHAT["sobre_mediana"]),
            ("P de pérdida", pct(m["p_perdida"]), words.WHAT["madre_perdida"])],
            columns=["Lectura", "Valor", "Qué es"]), words.NOTE["madre"]))
    cpu = got["cpu_s"]
    cost = [("Reloj de la cola", f"{perf['wall_s']:.1f} s"), ("Procesos", str(perf["procesos"])),
            ("Sorteos por tipo", str(perf["sorteos"])), ("Tareas en la cola", str(perf["tareas"])),
            *[(f"CPU · {kind}", f"{seconds:.1f} s") for kind, seconds in cpu.items()],
            ("Memoria máxima de un proceso", f"{perf['mem_proceso_max_mb']:.0f} MB"),
            ("Memoria máxima del proceso padre", f"{perf['mem_padre_mb']:.0f} MB")]
    fourth = [{"kind": "bars", "title": "Curva de potencia: Sharpe anual plantado", "unit": "%",
               "reference": 5.0, "note": words.WHAT["potencia"].format(share=cfg["power"]["share"]),
               "items": [{"label": f"δ = {d}".replace(".", ","), "value": facts["potencia"][key] * 100,
                          "error": None, "state": "info"}
                         for d, key in zip(cfg["power"]["deltas"], facts["potencia"])]},
              blocks.table("Coste de la corrida", pd.DataFrame(cost, columns=["Qué", "Cuánto"]),
                           words.NOTE["coste"])]
    return [envelope.tab("lectura", "Lectura", first),
            envelope.tab("degradacion", "Degradación y dominancia", second),
            envelope.tab("seleccion", "Selección y madre", third),
            envelope.tab("potencia", "Potencia y coste", fourth)]
