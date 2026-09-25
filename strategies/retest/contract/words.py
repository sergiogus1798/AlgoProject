"""The Spanish sentence behind every check that can fire, and every task. gates decides, this narrates."""

from strategies.retest.inputs import tasks

# One entry per gates.VETOES. report.py asserts the two sets are equal at start-up, because a
# veto that fires with no words attached is a verdict nobody can argue with.
SENTENCES = {
    "beneficio_no_robusto":
        "Bajo el estrés combinado, el 5% de las peores re-ejecuciones no gana dinero. El "
        "beneficio del backtest no sobrevive a que el mundo sea algo distinto.",
    "drawdown_insostenible":
        "El drawdown medio del 5% de peores re-ejecuciones supera lo que la cuenta aguanta. "
        "No es el percentil, es la media de la cola: lo que pasa cuando pasa lo malo.",
    "colapso_de_regimen":
        "La mediana de re-ejecuciones opera menos de la mitad que el original. Eso no es una "
        "estrategia degradada, es otra estrategia, y su beneficio no significa nada.",
    "edge_indistinguible_de_cero":
        "Ni la distribución empírica de Sharpe ni el PSR del backtest original separan esta "
        "ventaja de cero.",
    "ejecucion_fragil":
        "La peor de las tres pruebas de ejecución —spread, slippage, distancia mínima— se lleva "
        "más beneficio del admisible. Se juzga la peor y no la media: sobrevivir a dos y morir "
        "en la tercera sigue siendo un problema de ejecución.",
    "sobreajuste_de_parametros":
        "Moviendo sus propios parámetros un 15%, el percentil 5 es una pérdida. La ventaja vive "
        "en un pico estrecho de la función de fitness, no en una meseta.",
    "tarea_sin_dispersion":
        "Esta tarea corrió y la estrategia no se enteró: las mil simulaciones dieron el mismo "
        "resultado. No es un aprobado, es que ese eje no se llegó a probar.",
    "tabla_de_niveles_corrupta":
        "Esta corrida se cortó antes de terminar. Las simulaciones guardadas son válidas, pero "
        "SQX escribió su tabla de confianza sobre el total que le pediste, así que esa tabla "
        "tiene todos los rangos desplazados y no se lee.",
    "reconciliacion_fallida":
        "Alguna métrica reconstruida ya no reproduce lo que SQX calculó. Ningún número de este "
        "informe es fiable hasta que eso se resuelva."}

# What each task perturbs, in the report's language. tasks.PERTURBS is the English contract the
# code reasons about; this is the sentence the owner reads. Two tables, one meaning, on purpose.
PERTURBA = {
    "bar": "la barra en la que empieza el backtest",
    "spread": "el spread cobrado en cada operación",
    "slippage": "el slippage de cada relleno",
    "mindist": "lo cerca del precio que puede estar una orden pendiente antes de que el bróker la rechace",
    "params": "todos los parámetros de la estrategia, cada uno con certeza de moverse",
    "exits": "solo los parámetros de salida: stop, target, trailing",
    "ohlc": "el propio histórico de precios, cada vela movida una fracción de su ATR",
    "stress": "las seis cosas a la vez"}

FIJA = {
    "bar": "la estrategia, sus parámetros, los datos y todos los costes",
    "spread": "la estrategia, los datos y todos los costes salvo el spread",
    "slippage": "la estrategia, los datos y todos los costes salvo el slippage",
    "mindist": "la estrategia, los datos y todos los costes por operación",
    "params": "los datos y todos los costes",
    "exits": "los datos, todos los costes y todos los parámetros de entrada",
    "ohlc": "la estrategia, sus parámetros y todos los costes",
    "stress": "nada salvo las propias reglas de la estrategia"}

VERDICTS = {
    "STRONG": "Aguanta las ocho tareas con margen.",
    "ACCEPTABLE": "Aguanta, sin margen de sobra.",
    "MARGINAL": "Se sostiene por poco; cualquier deterioro la tumba.",
    "FAIL": "Algo la descalifica. Mira los vetos.",
    "INCONCLUSIVE": "No falló: no se pudo juzgar. La batería no dio evidencia suficiente."}


STATE = {"STRONG": "pass", "ACCEPTABLE": "pass", "MARGINAL": "watch", "FAIL": "fail",
         "INCONCLUSIVE": "none"}


def shape(entry: dict) -> str:
    """What a task's outcome looks like, in words: nothing moved, a grid, or a real shape."""
    m = entry["modes"]
    if not m["perturbed"]:
        return "no perturbó nada"
    if not m["discriminated"]:
        return f"{m['outcomes']} valores: rejilla, sin forma que medir"
    return "bimodal" if m["bimodality"]["bimodal"] else "unimodal"


def battery(result: dict) -> list[list[str]]:
    """What can only be said across the strategies, one row per fact.

    Args:
        result: What run.battery() returned.

    Returns:
        Rows of (fact, value, what it means).
    """
    enb, mult, ranks = result["effective_bets"], result["multiplicity"], result["rank_stability"]
    order = (f"no evaluable con {ranks['n']} estrategias, hacen falta {ranks['needed']}"
             if not ranks["measurable"] else
             f"tau de Kendall {ranks['tau']:+.2f} (p = {ranks['p']:.3f})")
    return [["Apuestas efectivas", f"{enb['enb']:.2f} de {enb['n']} ({enb['ratio']:.0%})",
             "Comparten plantilla de generación, pero sus retornos diarios apenas se "
             "correlacionan: la plantilla fija la forma de las reglas, no el momento."],
            ["Multiplicidad", f"{mult['pool']} contrastes, {mult['method'].upper()} factor "
                              f"{mult.get('factor', 1):.2f}",
             "Sólo entran los tests del dip: los contrastes entre tareas se llevan a cero "
             "subiendo simulaciones, así que no son evidencia."],
            ["Estabilidad del ranking", order, "Si el orden de las estrategias sobrevive al "
                                               "estrés combinado."]]
