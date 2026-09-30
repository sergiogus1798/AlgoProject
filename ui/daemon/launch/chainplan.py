"""What «Correr workflow» runs, in WORKFLOW.md's order, and the step it stops before — from the rail."""

from ui.daemon.launch.steps import ELSEWHERE
from ui.daemon.workflow.steps import STEPS


HOW = {s["n"]: s["how"] for s in STEPS}
# Python steps that judge strategies: each emits a `strategy, verdict` CSV that /curate or the
# window's filters apply before the next SQX task (WORKFLOW.md, «El contrato que une los pasos
# pares»). A task after one of them must not read a population nobody has looked at.
JUDGES = {"8", "10", "12", "14", "16"}
# SQX steps that read oos2 (WORKFLOW.md, «Qué segmento toca cada paso»): never in the chain,
# like the studies `workflow.tests.SPENDS` names.
OOS2 = {"19": "la Walk Forward Matrix lee el oos2: se lanza con su ▶ SQX, a mano"}
# Preparations the next SQX step's run does itself, worker stopped, just before its start:
# 10.5 fills CrossTF_Input for the 11 (`sqx.projects.crosstfload`, `launch.run.execute`).
FILLED_BY_NEXT = {"10.5"}
# The steps no machine does: the chain only walks past them when they are done.
BEFORE = {"template": "lo haces tú, en el chat (idea, bloques, plantilla)",
          "preflight": "el preflight del activo no pasa: arréglalo en Activos",
          "project": ELSEWHERE["5"]}
RULE = ("La cadena corre, en el orden de WORKFLOW.md, cada paso pendiente: los de SQX (todas "
        "sus tareas en un solo arranque del worker, que se para al acabar) y las pruebas de "
        "Python que corre «todas las pruebas Python pendientes» (nunca las que leen el oos2 o "
        "escriben en el ledger, ni 21-25). Tras un paso de SQX corrido en esta pulsación, lo "
        "que le sigue se vuelve a correr entero: su entrada cambió. Se para SIEMPRE antes de la "
        "siguiente tarea de SQX cuando entre medias hay un paso de Python que juzga (8, 10, 12, "
        "14, 16) y que no estaba hecho o se ha corrido en esta pulsación: ahí decides tú el "
        "corte (filtros y «Continuar workflow», o nada) y vuelves a pulsar; sólo una pulsación "
        "que empieza en esa tarea de SQX, con su análisis ya hecho, la cruza. También se para "
        "en lo que la ventana no lanza (5, 16.5), en el 19 (lee el oos2), en cualquier "
        "paso en marcha y en el primer fallo. El 10.5 no para: lo prepara el propio arranque "
        "del 11 (las supervivientes de Cross Market escaladas, a CrossTF_Input).")


def tests(step: dict, stale: bool) -> list[str]:
    """The tests the chain runs in one Python step: those the rail's «todas las pruebas Python
    pendientes» (once «correr todo») runs.

    Args:
        step: One step of GET /api/workflow.
        stale: An SQX step ran earlier in this press: every free test runs again, done or not.

    Returns:
        Study keys. `auto` already leaves out what reads oos2 or writes the ledger
        (`workflow.tests.SPENDS`), what the window refuses, and 21-25, whose databank only
        the panel knows.
    """
    return [t["key"] for t in step["tests"]
            if t["runnable"] and t["auto"] and t["state"] != "running"
            and (stale or t["state"] == "pending")]


def plan(data: dict) -> dict:
    """Walk the rail and say what one press runs.

    Args:
        data: GET /api/workflow's answer.

    Returns:
        `do` — [{n, title, kind: sqx|python, tests, state}] in order, `state` as confirmed —
        and `stop` — {n, title, why}, `n`
        None when the chain simply runs out. It assumes every SQX step it plans ends well;
        the runner re-checks each one before starting it.
    """
    do, judged, stale = [], False, False

    def halt(step: dict | None, why: str) -> dict:
        """The plan, ending before `step`."""
        return {"do": do, "stop": {"n": step["n"] if step else None,
                                   "title": step["title"] if step else "", "why": why}}

    for step in data["steps"]:
        n, state = step["n"], step["state"]
        if HOW[n] in BEFORE:
            if state != "done":
                return halt(step, BEFORE[HOW[n]])
            continue
        if state == "running":
            return halt(step, "está en marcha" + (" en SQX" if step["kind"] == "sqx" else ""))
        if step["kind"] == "python":
            if state == "done" and not stale:
                continue        # its verdict exists; a leftover test runs with its own ▶ PY
            keys = tests(step, stale)
            if keys:
                do.append({"n": n, "title": step["title"], "kind": "python", "tests": keys,
                           "state": state})
            if n in JUDGES:
                if not keys:
                    return halt(step, "este análisis da el veredicto antes de la siguiente "
                                      "tarea de SQX y la cadena no tiene pruebas suyas que "
                                      "correr: córrelo con su ▶ PY y decide el corte")
                judged = True
            continue
        if judged:
            return halt(step, "antes de esta tarea de SQX hay un corte que decides tú: mira el "
                              "análisis, filtra y «Continuar workflow» (o nada) y vuelve a pulsar")
        if state == "done" and not stale:
            continue
        if n in FILLED_BY_NEXT:
            continue            # the next SQX step's own run prepares it (`crosstfload`)
        if n in OOS2 or n in ELSEWHERE:
            return halt(step, OOS2.get(n) or ELSEWHERE[n])
        do.append({"n": n, "title": step["title"], "kind": "sqx", "tests": [], "state": state})
        judged, stale = False, True
    return halt(None, "no queda ningún paso que la cadena corra sola (17, 18, 18.5, 20 y "
                      "21-25 se corren con su ▶)")
