"""The questions the chat asks before a template idea is written down, and which is next."""

from ui.daemon.coverage import ARCHETYPES

# One entry per question, asked in this order. `default` is the owner's documented default
# in sqx/templates/README.md and is applied silently when he skips the question — except
# where it is None, which marks the one question that has no default and is always asked.
QUESTIONS = [
    {"id": "idea", "kind": "text", "default": None,
     "ask": "Cuéntame la entrada en una frase. ¿Qué tiene que pasar en el gráfico para entrar?",
     "why": "Es la idea. Todo lo demás se deduce o lleva default."},
    {"id": "logic", "kind": "choice", "default": None,
     "ask": "¿Es un estado o una transición?",
     "why": "La única pregunta sin default. «El cierre está por encima» dispara en cada barra "
            "del tramo; «el cierre cruza» dispara una sola vez. Son dos estrategias distintas.",
     "options": [{"value": "transition", "label": "Transición — cruza, rompe, pasa a estar"},
                 {"value": "state", "label": "Estado — está por encima, sigue dentro"}]},
    {"id": "direction", "kind": "choice", "default": "long",
     "ask": "¿Dirección?",
     "why": "Default del dueño: long.",
     "options": [{"value": "long", "label": "Long (default)"},
                 {"value": "short", "label": "Short"},
                 {"value": "both", "label": "Las dos"}]},
    {"id": "archetype", "kind": "choice", "default": "breakout",
     "ask": "¿Qué arquetipo es? Es la columna con la que la matriz contesta de qué tienes poco.",
     "why": "No cambia el .sqx: cambia dónde cae en la matriz de cobertura.",
     "options": [{"value": a, "label": a} for a in ARCHETYPES]},
    {"id": "random", "kind": "choice", "default": "one_free",
     "ask": "¿Cuántas condiciones aleatorias acompañan a la fija?",
     "why": "Default del dueño: una libre, con #Group# vacío, muestreando las 500 condiciones "
            "nativas.",
     "options": [{"value": "one_free", "label": "Una libre (default)"},
                 {"value": "one_group", "label": "Una de un grupo concreto"},
                 {"value": "two_free", "label": "Dos libres"},
                 {"value": "none", "label": "Ninguna — solo la condición fija"}]},
    {"id": "group", "kind": "text", "default": "", "only_if": ("random", "one_group"),
     "ask": "¿Qué grupo aleatorio? Nombre tal cual lo tiene la instalación.",
     "why": "Un hueco solo alcanza bloques a través del grupo que lo puebla."},
    {"id": "entry", "kind": "choice", "default": "market",
     "ask": "¿Tipo de orden de entrada?",
     "why": "Decide el esqueleto que emite el generador, y si el MC Retest lleva la tarea "
            "MinDistance.",
     "options": [{"value": "market", "label": "A mercado (default)"},
                 {"value": "stop", "label": "Stop"},
                 {"value": "limit", "label": "Limit"}]},
    {"id": "exit", "kind": "choice", "default": "skeleton",
     "ask": "¿Las salidas las fija la plantilla, o las deja como vienen?",
     "why": "Default del dueño: la pila del esqueleto sin tocar (SL/PT/Trailing/MoveSL2BE/"
            "ExitAfterBars).",
     "options": [{"value": "skeleton", "label": "La pila del esqueleto, sin tocar (default)"},
                 {"value": "fixed", "label": "La fijo yo — te la describo"}]},
    {"id": "exit_rule", "kind": "text", "default": "", "only_if": ("exit", "fixed"),
     "ask": "Describe la salida que quieres fija.",
     "why": "Va al nombre de la plantilla como segundo rol: entrada_salida."},
    {"id": "name", "kind": "text", "default": "",
     "ask": "Nombre de la plantilla, en camelCase. Sin símbolo y sin timeframe.",
     "why": "Una plantilla no pertenece a ningún mercado: eso es una fila de runs.csv."},
]


def applies(question: dict[str, object], answers: dict[str, str]) -> bool:
    """Whether a conditional question is live given what has been answered.

    Args:
        question: An entry of `QUESTIONS`.
        answers: What the reader has answered so far, by question id.

    Returns:
        True unless the question declares an `only_if` the answers do not satisfy.
    """
    gate = question.get("only_if")
    return gate is None or answers.get(gate[0]) == gate[1]


def step(answers: dict[str, str]) -> dict[str, object]:
    """The next question to put to the reader, or the news that there are none left.

    Args:
        answers: What has been answered so far, by question id. A question absent from it
            is unanswered; one present with "" took its default.

    Returns:
        `{"done": False, "question": …, "progress": (n, total)}`, or `{"done": True}` when
        every live question has an answer. Stateless on purpose: the whole conversation is
        the answers dict, so a window that is closed mid-interview loses nothing the client
        did not already hold.
    """
    live = [q for q in QUESTIONS if applies(q, answers)]
    for i, q in enumerate(live):
        if q["id"] not in answers:
            return {"done": False, "question": q, "progress": [i + 1, len(live)]}
    return {"done": True}


def resolved(answers: dict[str, str]) -> dict[str, str]:
    """The answers with every skipped question replaced by its documented default.

    Args:
        answers: What the reader answered; "" means "you choose".

    Returns:
        One value per live question. The two defaults that are None never resolve, so a
        missing idea or a missing state/transition is a crash here and not a silent guess.
    """
    out = {}
    for q in QUESTIONS:
        if not applies(q, answers):
            continue
        given = answers.get(q["id"], "")
        if not given:
            assert q["default"] is not None, f"{q['id']} has no default and was not answered"
            given = q["default"]
        out[q["id"]] = given
    return out
