"""What every button of the window does, in one or two Spanish sentences, found by its text."""

import re

from ui.text.buttonhelp_texts import HELP

# Arrows, reload and close signs, ellipses, a quoted name («Filtros») and counts — «(3)», «17-19»,
# «0·25·50» — change while the window runs; the sentence belongs to the words that stay.
SIGNS = re.compile(r"[▶▸▾▴◂◀►■↻⟳→←↑↓+·•…&]")
QUOTED = re.compile(r"«[^»]*»")
COUNT = re.compile(r"\([^()]*\d[^()]*\)|(?<!\w)\d[\d\s.,/%\-]*")
SCOPE = " › "
OVERLAP = 0.5       # share of the shorter text's words that makes two texts one


def normalise(text: str) -> str:
    """The registry key of a button text: no signs, no counts, lower case, single spaces.

    Args:
        text: What the button says, e.g. «▶ correr marcados (3)».

    Returns:
        E.g. «correr marcados». A text that is nothing but a sign («×», «▶») keeps the sign,
        so it can still have an entry of its own.
    """
    words = " ".join(COUNT.sub(" ", SIGNS.sub(" ", QUOTED.sub(" ", text))).lower().split())
    return words or text.strip()


def key(entry: str) -> str:
    """A registry key as written («Clase › texto» or «texto») in its normalised form."""
    scope, _, text = entry.rpartition(SCOPE)
    return f"{scope}{SCOPE}{normalise(text)}" if scope else normalise(text)


KEYS = {key(k): v for k, v in HELP.items()}


def words(text: str) -> set[str]:
    """The words of a sentence of four letters or more, lower case, for comparing two."""
    return {w for w in re.findall(r"\w+", text.lower()) if len(w) >= 4}


def merge(said: str, tip: str) -> str:
    """One text for the «?» from the registry sentence and the button's own tooltip.

    Args:
        said: The registry's (or the `help` property's) sentence, '' when none.
        tip: The button's tooltip, '' when none.

    Returns:
        Both, the sentence first, when the tooltip adds something (why the button is off,
        which default it would pick); only the longer when half the tooltip's words are
        already in the sentence or the other way round — a near-copy said twice is noise.
    """
    if not said or not tip:
        return said or tip
    a, b = words(said), words(tip)
    shared = len(a & b) / max(1, min(len(a), len(b)))
    return max(said, tip, key=len) if shared >= OVERLAP else f"{said}\n\n{tip}"


def help_for(text: str, scopes: list[str] = ()) -> str:
    """The sentence for a button text, '' when the registry has none.

    Args:
        text: What the button says.
        scopes: The class names of the widgets holding it, nearest first; an entry scoped to
            one of them wins over the plain one.
    """
    bare = normalise(text)
    return next((KEYS[f"{s}{SCOPE}{bare}"] for s in scopes if f"{s}{SCOPE}{bare}" in KEYS),
                KEYS.get(bare, "")) if bare else ""
