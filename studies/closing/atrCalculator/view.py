"""The §2 reading drawn as the contract's tabs: X, the point of no return, the transfer."""

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope


GLOSSARY = [
    {"term": "MAE/ATR", "text": "Lo más que una operación llegó a ir en contra (medido por SQX "
     "sobre el camino M1, en dólares, pasado a precio con su tamaño) dividido por el ATR(20) "
     "de la barra cerrada antes de la entrada: la distancia a la que un stop X·ATR la habría "
     "cerrado."},
    {"term": "X", "text": "El percentil elegido del MAE/ATR de las ganadoras del IS. Un stop "
     "a X·ATR(20) deja intactas ese porcentaje de las ganadoras del IS."},
    {"term": "Ganadora", "text": "Una operación con resultado neto de costes mayor que cero."},
    {"term": "Intervalo de X", "text": "El 95 % central de la X al remuestrear las ganadoras "
     "del IS con reemplazo 9.999 veces. Ancho = otra muestra daría otra X."},
    {"term": "Punto sin retorno", "text": "La distancia a partir de la cual casi ninguna "
     "operación que llegó ahí acaba ganando y su resultado final medio es peor que cortar "
     "ahí. Cortar en esa zona ahorra dinero sin quitar ganadoras."},
    {"term": "Percentil efectivo", "text": "Qué percentil de las ganadoras de oos1 u oos2 es "
     "la X del IS. Si la X del p90 es su p75 en oos1, allí cortaría una de cada cuatro "
     "ganadoras en vez de una de cada diez."},
    {"term": "KS D", "text": "La mayor separación vertical entre las dos curvas acumuladas, "
     "de 0 a 1: el tamaño de la diferencia, que la p sola no da."},
    {"term": "Anderson-Darling", "text": "Otro test de dos muestras que pesa más las colas, "
     "que es donde vive la X. scipy recorta su p entre 0,001 y 0,25."},
    {"term": "Cociente de medianas", "text": "Mediana del MAE/ATR de las ganadoras OOS entre "
     "la del IS. Por encima de 1, fuera de muestra las ganadoras necesitaron más aire."}]
WINDOWS = {"build": "IS", "oos1": "oos1", "oos2": "oos2"}


def _yes(value: object) -> str:
    """A tri-state flag as the table says it."""
    return "—" if value is None or value != value else ("sí" if value else "no")


def x_tab(found: dict) -> dict:
    """The winners' MAE/ATR with each percentile's X marked, and the four side by side."""
    xs, won = found["xs"], found["winners"]["build"]
    options = [str(p) for p in xs["percentile"]]
    dists = []
    for r in xs.itertuples():
        d = blocks.distribution(
            f"MAE/ATR de las {len(won)} ganadoras del IS", "ATR", won, r.x,
            f"La línea es X al p{r.percentile}: {r.x:.2f} ATR (intervalo {r.low:.2f}–"
            f"{r.high:.2f}).")
        d["mark"] = f"X del p{r.percentile}"
        d["select"] = {"percentil": str(r.percentile)}
        dists.append(d)
    table = blocks.table("Las cuatro X, lado a lado", pd.DataFrame({
        "percentil": xs["percentile"], "X (ATR)": xs["x"], "desde": xs["low"],
        "hasta": xs["high"], "ancho / X": xs["width"],
        "poco fiable": [_yes(v) for v in xs["unreliable"]], "zona": xs["zone"],
        "p. efectivo oos1": xs["effective_oos1"], "p. efectivo oos2": xs["effective_oos2"]}),
        "Ninguna fila es la buena: el estudio no elige percentil.")
    return envelope.tab("x", "X", dists + [table],
                        [{"key": "percentil", "label": "Percentil", "options": options,
                          "default": options[len(options) // 2]}],
                        "X sale de las ganadoras del IS y de nada más; oos1 y oos2 sólo "
                        "dicen si se transfiere.")


def noreturn_tab(found: dict) -> dict:
    """What became of the IS trades that reached each distance, and where each X falls."""
    c, xs = found["curve"], found["xs"]
    x = [round(v, 4) for v in c["x"]]
    recovered = blocks.plain(100 * c["recovered"].to_numpy())
    return envelope.tab("noreturn", "Punto sin retorno", [
        {"kind": "lines", "title": "De las que llegaron a ir x ATR en contra, cuántas acabaron "
         "ganando", "unit": "%", "x": x,
         "series": [{"label": "se recuperan", "values": recovered, "role": "real"}]},
        {"kind": "lines", "title": "Su resultado final medio frente a cortar en x", "unit": "ATR",
         "x": x, "series": [
             {"label": "resultado final medio", "values": blocks.plain(c["mean_final"].to_numpy()),
              "role": "real"},
             {"label": "−x (lo que costaría cortar ahí)", "values": [-v for v in x],
              "role": "reference"}]},
        blocks.table("En qué zona cae cada X", pd.DataFrame({
            "percentil": xs["percentile"], "X (ATR)": xs["x"], "zona": xs["zone"]}),
            "«ruido»: muchas de las que llegan ahí se recuperan, cortar es cortar ruido. "
            "«sin retorno»: casi ninguna se recupera y acaban peor que −x.")],
        note=f"Todas las operaciones del IS, ganadoras y perdedoras. {int(c['reached'].iloc[0])} "
             f"llegaron a {c['x'].iloc[0]:.2f} ATR en contra.")


def ecdf(values: np.ndarray, x: list[float]) -> list[float | None]:
    """The share of values at or below each x, in percent; None for an empty sample."""
    if not len(values):
        return [None] * len(x)
    v = np.sort(values)
    return list(100 * np.searchsorted(v, x, side="right") / len(v))


def transfer_tab(found: dict) -> dict:
    """The IS winners' distribution against each OOS window's, and each X's effective percentile."""
    won, xs = found["winners"], found["xs"]
    top = float(np.percentile(np.concatenate(list(won.values())), 99))
    x = [round(v, 3) for v in np.linspace(0, top, 80)]
    rows = []
    for s, got in found["shapes"].items():
        if got:
            rows.append({"ventana": s, "ganadoras IS": got["n_is"], "ganadoras": got["n_oos"],
                         "KS D": got["ks_d"], "KS p": got["ks_p"], "AD": got["ad"],
                         "AD p": got["ad_p"], "mediana OOS / IS": got["median_ratio"]})
    effective = pd.DataFrame({
        "percentil": xs["percentile"], "X (ATR)": xs["x"],
        "p. efectivo oos1": xs["effective_oos1"],
        "se transfiere a oos1": [_yes(v) for v in xs["transfers_oos1"]],
        "p. efectivo oos2": xs["effective_oos2"],
        "se transfiere a oos2": [_yes(v) for v in xs["transfers_oos2"]]})
    return envelope.tab("transfer", "Transferencia", [
        {"kind": "lines", "title": "MAE/ATR de las ganadoras, acumulado, por ventana",
         "unit": "%", "x": x,
         "series": [{"label": f"{WINDOWS[s]} ({len(v)})", "values": ecdf(v, x),
                     "role": "real" if s == "build" else "sim"} for s, v in won.items()]},
        blocks.table("El percentil que la X del IS es en cada ventana", effective,
                     "Si no se transfiere, no se recalcula X fuera de muestra: se informa."),
        blocks.table("La forma entera, IS contra cada ventana", pd.DataFrame(rows),
                     "D y el cociente de medianas son el tamaño; la p sola no lo dice.")],
        note="Se mide sin tocar X: sólo se describe.")


def tabs(found: dict, cfg: dict) -> list[dict]:
    """The three §2 tabs, in reading order."""
    return [x_tab(found), noreturn_tab(found), transfer_tab(found)]
