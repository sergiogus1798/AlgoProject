"""The SQX retest drawn as the contract's tabs: the two proofs, the cost per X and the shape."""

import pandas as pd

from core.study import blocks, result as envelope

WINDOWS = {"build": "IS", "oos1": "oos1", "oos2": "oos2"}


def proofs_tab(measured: dict) -> dict:
    """The graft and ATR proofs; nothing else in the retest is readable until both pass."""
    g = measured["graft"]
    graft = blocks.table("Prueba del injerto: X = 1000 contra la original", pd.DataFrame({
        "ventana": [WINDOWS[s] for s in g["segment"]], "operaciones original": g["n_reference"],
        "operaciones X = 1000": g["n_probe"], "distintas": g["differ"],
        "mayor diferencia P/L (USD)": g["max_pl_diff"],
        "idénticas": ["sí" if v else "no" for v in g["identical"]]}),
        "Un stop a 1000 ATR no salta nunca: si el injerto no cambia nada más, las operaciones "
        "son las mismas una a una.")
    out = [graft]
    if len(measured["atr"]):
        a = measured["atr"]
        out.append(blocks.table("Prueba del ATR: la distancia de cada stop contra X · ATR(20)",
                                pd.DataFrame({"barra": a["bar"], "stops": a["n"],
                                              "residuo mediano (precio)": a["median_residual"],
                                              "residuo p90 (precio)": a["p90_residual"]}),
                                "El stop se pone desde el precio de entrada y resbala al salir: "
                                "en la barra buena el residuo es sólo spread y slippage."))
    ok = bool(g["identical"].all())
    return envelope.tab("proofs", "Pruebas", out,
                        note="El injerto reproduce la original." if ok else
                        "⚠️ El injerto NO reproduce la original: nada de lo que sigue se lee.")


def cost_tab(measured: dict) -> dict:
    """What the stop does at each percentile's X, window by window, against the original."""
    m = measured["metrics"]
    centre = m[m["step"] == 0]
    options = list(dict.fromkeys(WINDOWS[s] for s in centre["segment"]))
    out = []
    for s in dict.fromkeys(centre["segment"]):
        c = centre[centre["segment"] == s]
        t = blocks.table(f"{WINDOWS[s]}: cada X contra la original sin stop", pd.DataFrame({
            "percentil": c["percentile"], "X (ATR)": c["x"], "operaciones": c["n"],
            "paradas por el stop": c["stopped"], "% paradas": c["stopped_pct"],
            "ganadoras que mata": c["killed"], "pérdida ahorrada (USD)": c["saved"],
            "ganancia perdida (USD)": c["given_up"], "entradas nuevas": c["new"],
            "neto (USD)": c["net"], "neto original": c["net_original"], "PF": c["pf"],
            "PF original": c["pf_original"], "max DD (USD)": c["maxdd"],
            "max DD original": c["maxdd_original"], "peor operación": c["worst"],
            "peor original": c["worst_original"]}),
            "Costes y slippage los de SQX en esa ventana. Si Python y SQX discrepan, manda SQX.")
        t["select"] = {"ventana": WINDOWS[s]}
        out.append(t)
    return envelope.tab("cost", "Lo que cuesta en SQX", out,
                        [{"key": "ventana", "label": "Ventana", "options": options,
                          "default": options[0]}],
                        "Los cuatro percentiles lado a lado; ninguno es el elegido.")


def shape_tab(measured: dict, cfg: dict) -> dict:
    """The net result along the grid around each X, per window, and whether it is flat."""
    m, sh = measured["metrics"], measured["shape"]
    options = list(dict.fromkeys(WINDOWS[s] for s in m["segment"]))
    out = []
    for s in dict.fromkeys(m["segment"]):
        here = m[m["segment"] == s]
        steps = sorted(here["step"].unique())
        band = cfg["grid"]["band"] / cfg["grid"]["steps"]
        x = [f"X·{1 + band * k:.2f}" for k in steps]
        series = [{"label": f"p{p}", "role": "real",
                   "values": [float(g.loc[g["step"] == k, "net"].iloc[0]) for k in steps]}
                  for p, g in here.groupby("percentile")]
        original = float(here["net_original"].iloc[0])
        series.append({"label": "original sin stop", "role": "reference",
                        "values": [original] * len(steps)})
        lines = {"kind": "lines", "title": f"{WINDOWS[s]}: neto a lo largo de la rejilla",
                 "unit": "USD", "x": x, "series": series, "select": {"ventana": WINDOWS[s]}}
        here_shape = sh[sh["segment"] == s]
        t = blocks.table(f"{WINDOWS[s]}: meseta o borde", pd.DataFrame({
            "percentil": here_shape["percentile"], "neto en X": here_shape["centre_net"],
            "mayor cambio al apretar": here_shape["tighter"],
            "mayor cambio al aflojar": here_shape["looser"], "forma": here_shape["shape"]}),
            f"Cambios como parte del neto en X; meseta si ninguno pasa de "
            f"{cfg['shape']['tolerance']:.0%}. Se lee la forma, nunca el máximo.")
        t["select"] = {"ventana": WINDOWS[s]}
        out += [lines, t]
    return envelope.tab("shape", "Estabilidad", out,
                        [{"key": "ventana", "label": "Ventana", "options": options,
                          "default": options[0]}],
                        "Una X en meseta es robusta; una en el borde de un precipicio no, aunque "
                        "gane más.")


def tabs(measured: dict, cfg: dict) -> list[dict]:
    """The three SQX tabs, in reading order."""
    return [proofs_tab(measured), cost_tab(measured), shape_tab(measured, cfg)]
