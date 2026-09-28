"""One strategy's SPP reconnaissance as the contract's tabs: the call, influence, plateaus, surfaces, design."""

import pandas as pd

from core.study import blocks, result as envelope
from studies.breakage.spp.surface import label, origin_table

VERDICT = {"proceed": ("SEGUIR", "pass", "el máximo supera lo que daría una rejilla de ruido"),
           "noise": ("RUIDO", "fail", "el máximo no supera lo que daría una rejilla de ruido")}


def verdict(result: dict) -> dict:
    """Whether the family is anything but noise, with the numbers behind the call."""
    n, s = result["noise"], result["shape"]
    label, state, meaning = VERDICT[n["verdict"]]
    return blocks.verdict(label, state, f"{meaning.capitalize()}: máximo {n['observed_max']:.3f} "
                          f"contra {n['noise_max']:.3f} bajo el nulo σ·√(2·ln n_eff).",
                          n["ratio"],
                          [{"label": "tuplas distintas (n_eff)", "state": "info",
                            "value": n["n_eff"], "note": f"de {n['n_rows']:,} filas"},
                           {"label": "área de meseta", "state": "info",
                            "value": n["plateau_area"], "note": ""},
                           {"label": "(máx − mediana)/IQR", "state": "info",
                            "value": s["spike_ratio"], "note": f"curtosis {s['kurtosis']:.2f}"}])


def influence(result: dict) -> dict:
    """Variance explained by each parameter on every metric, beside the duplicate test."""
    eta2, dup = result["eta2"], result["duplicates"]
    shown = eta2.copy()
    shown["grupos"], shown["idénticos"] = dup["groups"], dup["identical"]
    shown["inerte"] = dup["inert"].astype(bool)
    shown = shown.sort_values(result["metric"], ascending=False).reset_index()
    return envelope.tab("influence", "Influencia por parámetro", [
        {"kind": "bars", "title": f"η² sobre {result['metric']}", "unit": "η²",
         "reference": None,
         "items": [{"label": r.iloc[0], "value": float(r[result["metric"]]), "error": None,
                    "state": "none" if r["inerte"] else "info"} for _, r in shown.iterrows()],
         "note": "En gris, los parámetros que el test de duplicados declara inertes."},
        blocks.table("η² por métrica y test de duplicados", shown)],
        note="η² es por métrica: el mismo parámetro puede explicar el 8 % de una y el 78 % de "
             "otra. Congelar se decide por el test de duplicados, nunca por η²: una SPP "
             "muestrea desequilibrado y un parámetro inerte saca η² por encima de cero.")


def plateaus(result: dict) -> dict:
    """One plateau per parameter, and its marginal profile drawn."""
    rows = [{"parámetro": n, **p["plateau"], "original": result["original"][n]}
            for n, p in result["profiles"].items()]
    curves = [{"kind": "lines", "title": f"{n} — mediana de {result['metric']} por nivel",
               "unit": "", "x": [float(v) for v in p["curve"]["level"]],
               "series": [{"label": "mediana", "values": list(p["curve"]["median"]),
                           "role": "real"}],
               "note": f"Meseta de {p['plateau']['from']:g} a {p['plateau']['to']:g}, centro "
                       f"{p['plateau']['center']:g}, argmax {p['plateau']['argmax']:g}, "
                       f"original {result['original'][n]:g}.",
               "select": {"parámetro": n}} for n, p in result["profiles"].items()]
    names = list(result["profiles"])
    return envelope.tab(
        "plateaus", "Meseta y centro por parámetro",
        [blocks.table("Mesetas", pd.DataFrame(rows))] + curves,
        selectors=[{"key": "parámetro", "label": "Parámetro", "options": names,
                    "default": names[0]}],
        note="El centro es el punto medio de la meseta contigua, no el argmax — lo que hace "
             "el BestValue de SQX. Donde centro y argmax se separan, el pico está en el "
             "borde de lo estable.")


def _origin(cell: dict) -> str:
    """What θ₀'s cell says, θ₀ itself left out of it."""
    if not cell["n"]:
        return ("θ₀ está solo en su celda: ninguna otra tupla probó esa pareja de niveles, así "
                "que la rejilla no dice nada de su vecindad.")
    return (f"Sin contar a θ₀, su celda ({cell['n']} tuplas) vale {cell['value']:.3g}, por "
            f"encima del {cell['rank']:.0f} % de las celdas, "
            + ("dentro" if cell["plateau"] else "fuera") + " de la meseta.")


def surfaces(found: list[dict], metric: str, top_share: float) -> dict:
    """Two parameters at a time, picked on two drop-downs, with θ₀ marked on every grid.

    Args:
        found: What `surface.pairs` returned.
        metric: The verdict metric the cells are the median of.
        top_share: The plateau's share of the cells, for the notes.

    Returns:
        One tab: a `grid` per ordered pair tagged {"x", "y"}, then θ₀'s table.
    """
    grids = [{"kind": "grid", "title": f"{p['y']} contra {p['x']} — mediana de {metric}",
              "rows": [label(v) for v in p["surface"].index],
              "cols": [label(v) for v in p["surface"].columns],
              "values": p["surface"].to_numpy(dtype=float).tolist(),
              "scale": "discrete", "levels": p["levels"], "labels": None,
              "mark": {"row": label(p["origin"]["y"]), "col": label(p["origin"]["x"]),
                       "label": "θ₀"},
              "scale_range": None,
              "note": f"Cada celda es la mediana de {metric} de todas las tuplas que usaron esa "
                      f"pareja de niveles, sean cuales sean los demás parámetros, θ₀ fuera. Cortes en los "
                      f"cuartiles y en el percentil {100 * (1 - top_share):g}: la banda de "
                      f"arriba es la meseta (≥ {p['cut']:.3g}). {_origin(p['origin'])}",
              "select": {"x": p["x"], "y": p["y"]}} for p in found]
    names = list(dict.fromkeys(p["x"] for p in found))
    return envelope.tab(
        "surfaces", "Superficies por pareja",
        grids + [blocks.table("θ₀ en cada pareja", origin_table(found),
                              "Una fila por pareja sin orden: (Y, X) es la misma rejilla "
                              "traspuesta.")],
        selectors=[{"key": "x", "label": "Eje X", "options": names, "default": names[0]},
                   {"key": "y", "label": "Eje Y", "options": names, "default": names[1]}],
        note=f"Elige un parámetro para cada eje. Meseta = el decil superior de las celdas de "
             f"esa rejilla ({100 * top_share:g} %), la misma definición que la nube de "
             f"parámetros. Una celda con pocas tuplas pesa lo mismo que una llena: una SPP "
             f"muestrea desequilibrado. Si eliges el mismo parámetro en los dos ejes no hay "
             f"rejilla.")


def design(brief: dict) -> dict:
    """The design the fabrication stage will build, as it was derived here."""
    live = pd.DataFrame([{"parámetro": p["name"], "η²": p["eta2"], "centro": p["center"],
                          "niveles": ", ".join(f"{v:g}" for v in p["levels"]),
                          "original": p["original"], "argmax IS": p["argmax_is"],
                          "ancho de meseta": p["plateau_width"], "pico": p["spike"]}
                         for p in brief["parameters"]])
    frozen = pd.DataFrame([{"parámetro": f["name"], "valor": f["value"],
                            "grupos": f["groups"], "por qué": f["reason"]}
                           for f in brief["frozen"]])
    return envelope.tab("design", "El diseño para la fábrica", [
        blocks.table("Parámetros vivos", live, "Un pico (meseta de ancho 1) no tiene "
                     "margen a ningún lado: su centro es el argmax con otro nombre."),
        blocks.table("Congelados", frozen, "Congelados por el test de duplicados: cambiarlos "
                     "no movió ni un backtest.")],
        note=f"{brief['n_target']:,} variantes en tres estratos: "
             + ", ".join(f"{k} {v:.0%}" for k, v in brief["strata"].items()) + ".")
