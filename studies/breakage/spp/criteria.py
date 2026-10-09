"""The SPP's criteria metrics as the window's tab and as the columns of verdict.csv."""

import pandas as pd

from core.study import blocks, draws, result as envelope
from studies.breakage.spp.model import combine

TITLE = "Métricas para criterios — sin umbral todavía"
# How each metric is spelled in a verdict.csv column, which the databank table shows as words.
TOKEN = {"NetProfit": "Net_Profit", "ProfitFactor": "Profit_Factor", "ReturnDDRatio": "Ret_DD",
         "Drawdown": "Max_Drawdown", "SharpeRatio": "Sharpe", "SortinoRatio": "Sortino",
         "EdgeRatioInPips": "R_Edge"}
NAME = {c: n for c, n, _ in combine.METRICS + combine.TIME_FREE}
NULL = ("Lo que daría esta misma rejilla OOS1 si la familia no tuviera ventaja: conserva su "
        "forma y su centro se sortea con el ruido de un solo camino de precios (Sharpe 0 ± "
        "1/√años). Percentiles 5 a 95. Si el valor real cae dentro, la métrica no distingue "
        "esta estrategia de una sin ventaja.")
HELP_DECAY = [
    None,
    "Mediana(OOS1) / mediana(IS): un cociente de medianas, porque IS y OOS1 no comparten "
    "permutaciones y no hay ratio por variante. 1 = no decae; por debajo de 1, decae. Sharpe y "
    "Sortino son anualizados (√252), comparables entre ventanas de distinta duración. Solo se "
    "publica si la mediana IS supera su suelo: con una mediana IS cerca de cero el cociente "
    "cambia de signo o explota.", NULL,
    "A de Vargha–Delaney: probabilidad de que una permutación OOS1 al azar supere a una IS al "
    "azar (más la mitad de los empates). 0,5 = distribuciones iguales; por debajo, decae. Es un "
    "tamaño de efecto: no depende del número de permutaciones y no es un p-valor.", NULL,
    "Distancia de Wasserstein entre IS y OOS1 dividida por el rango intercuartílico de IS: "
    "cuántos IQR hay que mover una distribución para convertirla en la otra. 0 = iguales. Es "
    "bilateral: también crece si OOS1 es mejor.", NULL]
HELP_ORIGINAL = [
    None,
    "(Original − mediana) / |mediana| de sus permutaciones, con signo. El criterio heredado de "
    "SQX es que quede dentro de ± X %. Premia la poca dispersión: una rejilla estrecha pasa "
    "aunque el original sea su extremo. No se publica si la mediana está a menos de 0,25 IQR "
    "de cero.",
    "La misma distancia en rangos intercuartílicos (IQR) de la rejilla: no depende de lo "
    "grande que sea la mediana.",
    "Entre qué valores cae, en IQR, el 90 % central de las propias permutaciones: lo que "
    "leería un backtest sacado al azar de la rejilla. Un original fuera de este rango es un "
    "extremo de su vecindad."]


def es(value: float | None, pattern: str = "{:.2f}") -> str:
    """A number as the panel prints it, decimal comma; «—» for a missing one."""
    return "—" if value is None else pattern.format(value).replace(".", ",")


def span(pair: list | None, pattern: str = "{:.2f}") -> str:
    """A null's 5th to 95th percentile as «lo a hi»."""
    return "—" if pair is None else f"{es(pair[0], pattern)} a {es(pair[-1], pattern)}"


def table(title: str, columns: list[str], rows: list[list], note: str, tips: list) -> dict:
    """A compact table block with one «?» per column."""
    return blocks.table(title, pd.DataFrame(rows, columns=columns), note) | {
        "help": tips, "compact": True}


def flat(measured: dict) -> dict:
    """The metrics as one flat row: the columns of verdict.csv, hence of the databank table."""
    out = {}
    for col, sides in measured["original"].items():
        for side, d in sides.items():
            out[f"distancia_pct_{side}_{TOKEN[col]}"] = d["rel"]
            out[f"distancia_IQR_{side}_{TOKEN[col]}"] = d["iqr"]
    for col, d in measured["decay"].items():
        out |= {f"decaimiento_{TOKEN[col]}": d["ratio"], f"A_{TOKEN[col]}": d["a"],
                f"Wasserstein_{TOKEN[col]}": d["w"]}
    return out


def recorded(strategy: str, identity: str | None, sides: dict[str, tuple]) -> list[dict]:
    """Each window's permutation grid behind its `distancia_IQR_*` columns, as `draws` rows.

    Args:
        strategy: Its name.
        identity: Its identity, when known.
        sides: Side (`IS`, `OOS1`) -> (the `without_original` grid, the real row).
    """
    return [draws.record("spp", f"distancia_IQR_{side}_{TOKEN[col]}", float(real[col]),
                         pop[col].to_numpy(float), identity or "", strategy=strategy, seed=None,
                         side=side, unit="permutaciones de SQX")
            for side, (pop, real) in sides.items() for col, _, _ in combine.METRICS]


def tab(measured: dict) -> dict:
    """The tab «Métricas para criterios»: computed and shown, judged by nothing.

    Cells are text on purpose: the autopilot reads these numbers from verdict.csv, and a
    numeric cell here would offer each of them a second time under the table's name.
    """
    made = []
    if measured["decay"]:
        rows = []
        for col, d in measured["decay"].items():
            null = d["null"] or {}
            rows.append([NAME[col], es(d["ratio"]), span(null.get("ratio")), es(d["a"]),
                         span(null.get("a")), es(d["w"]), span(null.get("w"))])
        made.append(table(
            f"{TITLE}: IS contra OOS1",
            ["Métrica", "Decaimiento de la mediana", "Decaimiento sin ventaja",
             "A de Vargha–Delaney", "A sin ventaja", "Wasserstein / IQR",
             "Wasserstein sin ventaja"], rows,
            "«—» en el decaimiento: la mediana IS no supera su suelo (Sharpe y Sortino 0,1; "
            "Profit Factor y R/Edge ratio 1), no hay de dónde decaer. «—» en «sin ventaja»: "
            "R/Edge ratio no tiene modelo de ruido, así que no tiene nulo.", HELP_DECAY))
    sides = list(next(iter(measured["original"].values())))
    rows = [[NAME[col]] + [cell for side in sides for cell in (
        es(d[side]["rel"], "{:+.1f} %"), es(d[side]["iqr"], "{:+.2f}"),
        span(d[side]["null"], "{:+.2f}"))] for col, d in measured["original"].items()]
    made.append(table(
        f"{TITLE}: el original frente a sus permutaciones",
        ["Métrica"] + [f"{side}: {what}" for side in sides
                       for what in ("distancia a la mediana", "en IQR", "al azar, en IQR")], rows,
        "«—» en la distancia en %: la mediana está demasiado cerca de cero para dividir por "
        "ella; la distancia en IQR sigue valiendo.",
        HELP_ORIGINAL[:1] + HELP_ORIGINAL[1:] * len(sides)))
    return envelope.tab(
        "criterios", "Métricas para criterios", made,
        note="Calculadas y visibles, sin juzgar: ninguna tiene umbral y ninguna cambia el "
             "veredicto. Son las columnas del SPP en la tabla de Databanks. Comparan "
             "distribuciones, no variantes una a una, y nunca con el p-valor del KS. Las "
             "permutaciones comparten un solo camino de precios: su número no es un tamaño "
             "de muestra, así que aquí no hay p-valores, solo tamaños de efecto y lo que "
             "leería una familia sin ventaja.")
