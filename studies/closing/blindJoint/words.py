"""The words of another study's call, as the owner reads them: Spanish, sentence case, decimal comma."""

import re

STATE = {"pass": "Pasa", "fail": "Falla", "watch": "Vigilar", "none": "Sin juicio",
         "info": "Info"}
CALL = {"blind": "Ciega", "predicts": "Predice", "perverse": "Perversa",
        "pasa": "Pasa", "limbo": "Limbo", "no_pasa": "No pasa"}


def call(label: str) -> str:
    """A piece's call with a capital, its English word (an old WFM `blind`) or a snake_case state (`no_pasa`) in Spanish."""
    label = CALL.get(label, label)
    return label[:1].upper() + label[1:]


def sentence(text: str) -> str:
    """A sentence another study wrote, read the Spanish way.

    Args:
        text: E.g. «rho 0.45, intervalo [0.35, 0.53] entero por encima de 0.3».

    Returns:
        «ρ = 0,45, intervalo [0,35; 0,53] entero por encima de 0,3»: ρ for rho, decimal
        comma, a percentage as «38,5 %», the list separator a semicolon inside brackets.
    """
    text = re.sub(r"\brho\s+(?=[-+\d])", "ρ = ", text)
    text = re.sub(r"\[([^\]]*)\]", lambda m: "[" + m[1].replace(", ", "; ") + "]", text)
    text = re.sub(r"(\d)\.(\d)", r"\1,\2", text)
    return re.sub(r"(\d)%", r"\1 %", text)


def reading(pair: tuple[str, str]) -> str:
    """A reading as the owner reads it: «sin fallo + entrantes»."""
    return " + ".join(part.replace("_", " ") for part in pair)
