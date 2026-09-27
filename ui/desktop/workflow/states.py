"""The rail's six step states as colour and word, borrowed from the contract's map where they mean the same."""

from ui.desktop.blocks import states
from ui.desktop.theme import T

# A step's state is not a contract state, so it gets its own keys — but a finished step is
# drawn in «pasa» green and a blocked one in «falla» red, so one colour keeps one meaning.
# `missing` is the one exception: the contract's near-black would vanish on the rail.
STEP_COLOUR = {"done": states.colour("pass"), "running": states.colour("info"),
               "pending": states.colour("none"), "blocked": states.colour("fail"),
               "sealed": states.colour("watch"), "missing": T["faint"]}
STEP_LABEL = {"done": "hecho", "running": "corriendo", "pending": "pendiente",
              "blocked": "bloqueado", "sealed": "sellado", "missing": "sin dato"}
KIND_LABEL = {"sqx": "SQX", "python": "PY", "person": "TÚ"}
KIND_HELP = {"sqx": "corre en StrategyQuant X", "python": "corre en Python",
             "person": "lo haces tú, en el chat"}


def colour(state: str) -> str:
    """The colour of one step state, the contract's grey for a word the rail does not know."""
    return STEP_COLOUR.get(state, states.colour(state))


def label(state: str) -> str:
    """The Spanish word for one step state, the raw value quoted when unknown."""
    return STEP_LABEL.get(state, f"«{state}»")
