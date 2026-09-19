"""The Spanish sentence behind every check that can fire. gates decides, this narrates."""

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

VERDICTS = {
    "STRONG": "Aguanta las ocho tareas con margen.",
    "ACCEPTABLE": "Aguanta, sin margen de sobra.",
    "MARGINAL": "Se sostiene por poco; cualquier deterioro la tumba.",
    "FAIL": "Algo la descalifica. Mira los vetos.",
    "INCONCLUSIVE": "No falló: no se pudo juzgar. La batería no dio evidencia suficiente."}


def flag(entry: dict) -> str:
    """One line describing a check that fired.

    Args:
        entry: One of gates.check()'s records.

    Returns:
        What fired, what it measured against what, and the sentence that explains it.
    """
    mark = "VETO" if entry["gate"] else "aviso"
    return (f"**{mark} · {entry['test']}** — midió {entry['value']:,.2f} contra "
            f"{entry['limit']:,.2f}. {SENTENCES[entry['veto']]}")


def task_line(task: str, got: dict) -> str:
    """One line describing what a task did to a strategy.

    Args:
        task: One of tasks.TASKS.
        got: That task's entry in a run.one() result.

    Returns:
        The perturbation, the tail, and whether the task produced a distribution at all.
    """
    tail = got["fragility"]["net_p5"]["point"]
    if not got["modes"]["perturbed"]:
        shape = "no perturbó nada"
    elif not got["modes"]["discriminated"]:
        shape = f"{got['modes']['outcomes']} valores: rejilla, sin forma que medir"
    else:
        shape = "bimodal" if got["modes"]["bimodality"]["bimodal"] else "unimodal"
    return (f"| {tasks.TITLES[task]} | {PERTURBA[task]} | {tail:,.0f} | "
            f"{got['fragility']['drawdown']['cvar']:.1f}% | "
            f"{got['modes']['trades']['median_share']:.0%} | {shape} |")


def battery_note(result: dict) -> str:
    """What can only be said across the strategies, in words.

    Args:
        result: What run.battery() returned.

    Returns:
        The effective number of independent bets, the multiplicity pool, and whether the
        ranking could be measured at all.
    """
    enb, mult, ranks = result["effective_bets"], result["multiplicity"], result["rank_stability"]
    order = (f"no evaluable con {ranks['n']} estrategias, hacen falta {ranks['needed']}"
             if not ranks["measurable"] else
             f"tau de Kendall {ranks['tau']:+.2f} (p = {ranks['p']:.3f})")
    return (f"**Apuestas efectivas:** {enb['enb']:.2f} de {enb['n']} estrategias "
            f"({enb['ratio']:.0%}). Comparten plantilla de generación, pero sus retornos diarios "
            f"apenas se correlacionan: la plantilla fija la forma de las reglas, no el momento "
            f"de las operaciones.\n\n"
            f"**Multiplicidad:** {mult['pool']} contrastes en el pool, corregidos por "
            f"{mult['method'].upper()} con factor {mult.get('factor', 1):.2f}. Solo entran los "
            f"tests del dip: los contrastes entre tareas se llevan a cero subiendo el número de "
            f"simulaciones, así que no son evidencia de nada.\n\n"
            f"**Estabilidad del ranking:** {order}.")
