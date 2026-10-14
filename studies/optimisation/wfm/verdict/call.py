"""Step 19's state from its facts: L1 always, the centre cell and L2 only when re-optimising live."""

from typing import TypedDict

PASA, LIMBO, NO_PASA = "pasa", "limbo", "no_pasa"
STATE = {PASA: "pass", LIMBO: "watch", NO_PASA: "fail"}
FIJO, REOPT = "fijo", "reoptimizado"
WINS, HOLDS = "reoptimizar gana", "no descarta"


class Call(TypedDict):
    """The step's call: pasa | limbo | no_pasa, its label and the rules that fired."""

    verdict: str
    label: str
    why: list[str]


def call(facts: dict, mode: str, alpha: float) -> Call:
    """The owner's table (proposal of step 19, section 5), the worst active rule winning.

    Args:
        facts: `l1` {`p_menos`, `p_mas`, `mediana_exceso`} and, when the mother's trades
            exist, `l2` {`p_menos`}; `centro` {`exceso_oos2`}.
        mode: `fijo` or `reoptimizado`.
        alpha: The cut on each tail.

    Returns:
        `verdict` (pasa | limbo | no_pasa), `label` and `why`, the rules that fired.
        NO PASA only when L1 loses beyond noise (p- <= alpha): a loss without significance
        is LIMBO, because the WFC already kills on the same 2.75 years. The two rules of
        `reoptimizado` can only add LIMBO, and a fact that does not exist fires nothing.
    """
    one = facts["l1"]
    why: list[str] = []
    if one["p_menos"] <= alpha:
        return {"verdict": NO_PASA, "label": "NO PASA", "why": ["l1_pierde"]}
    if one["mediana_exceso"] <= 0:
        why.append("l1_no_gana")
    if mode == REOPT:
        if facts["centro"]["exceso_oos2"] <= 0:
            why.append("centro_no_gana")
        if "l2" in facts and facts["l2"]["p_menos"] <= alpha:
            why.append("reoptimizar_empeora")
    if why:
        return {"verdict": LIMBO, "label": "LIMBO", "why": why}
    return {
        "verdict": PASA,
        "why": [],
        "label": f"PASA · {WINS if one['p_mas'] <= alpha else HOLDS}",
    }


MEANING = {
    "l1_pierde": "la estrategia reoptimizada pierde en oos2 más de lo que explica el ruido",
    "l1_no_gana": "reoptimizar no gana en oos2, pero con este tramo no se puede afirmar que pierda",
    "centro_no_gana": "la celda que se va a operar no gana en oos2",
    "reoptimizar_empeora": "reoptimizar empeora a congelar más de lo que explica el ruido: "
    "mejor operar la madre fija",
}


def sentence(got: dict, facts: dict, mode: str) -> str:
    """The call as the paragraph the owner reads first.

    Args:
        got: call()'s return.
        facts: The facts it was made from.
        mode: `fijo` or `reoptimizado`.

    Returns:
        Spanish: the median excess, its two tails, what fired, and the mode it was judged in.
    """

    def n(x: float, f: str = ",.2f") -> str:
        """A figure with the decimal comma."""
        return format(x, f).replace(",", " ").replace(".", ",")

    one = facts["l1"]
    said = (
        "; ".join(MEANING[w] for w in got["why"])
        if got["why"]
        else "gana en dato limpio más allá del ruido: cuenta como evidencia"
        if got["label"].endswith(WINS)
        else "gana en oos2 sin superar al ruido: no descarta, y no cuenta como evidencia"
    )
    return (
        f"Mediana de las celdas en oos2: {n(one['mediana_exceso'])} de exceso neto por año "
        f"(p+ {n(one['p_mas'], '.3f')}, p− {n(one['p_menos'], '.3f')} en el nulo de volteo "
        f"por semanas): {said}. Juzgado en modo «{mode}»."
    )
