"""Why a button is off, in a few plain words; the full sentences go in its tooltip."""

import re

# What SQX being busy with a run looks like in the daemon's refusals (advance/preflight,
# launch, workerguard, workflow/derive): the port answering, its processes, its log, a
# launcher still running, a step «en marcha».
BUSY = ("install ocupado", "sigue corriendo", "lanzamiento en marcha", "lanzamiento de ",
        "está en marcha", "está ahora en marcha", "empezó y no ha terminado", "se escribió hace",
        "proceso(s) de sqx", "todas sus pruebas están en marcha")
RUNNING = "el workflow ya está corriendo"
KNOWN = (("el demonio no respondió", "sin conexión: pulsa Recargar"),
         ("ningún databank vivo", "aún no hay estrategias"),
         ("sin comprobar todavía", "comprobando…"))
LIMIT = 60


def busy(text: str) -> bool:
    """Whether a refusal only says that a run is already going."""
    low = text.lower()
    return any(b in low for b in BUSY)


def brief(reasons: list[str] | str, limit: int = LIMIT) -> str:
    """The shortest honest reading of one or more refusals (owner, 2026-09-30: «no me pongas
    un textaco gigante»): a run going says only that; a known case its plain words; anything
    else its first sentence, cut at a word under `limit` characters.

    Args:
        reasons: The daemon's sentences, or one.
        limit: Characters the answer may take.

    Returns:
        Lower-case words to put after «No disponible: », or "" when there is no reason.
    """
    said = [reasons] if isinstance(reasons, str) else [r for r in reasons if r]
    if not said:
        return ""
    if any(busy(r) for r in said):
        return RUNNING
    low = said[0].lower()
    for key, words in KNOWN:
        if key in low:
            return words
    text = re.sub(r"^\w+:\s+", "", said[0].strip())      # the runner's «study: » prefix
    first = re.split(r"(?<=[.;])\s|\s·\s|\s\(", text)[0].rstrip(".;:")
    if len(first) <= limit:
        return first[:1].lower() + first[1:]
    cut = first[:limit].rsplit(" ", 1)[0]
    return cut[:1].lower() + cut[1:] + "…"


def off(reasons: list[str] | str, limit: int = LIMIT) -> str:
    """`brief` as a whole line: «No disponible: …», or "" with nothing to say."""
    words = brief(reasons, limit)
    return f"No disponible: {words}" if words else ""


def line(reasons: list[str] | str, limit: int = LIMIT) -> str:
    """`brief` as a sentence of its own, capitalised: for an error with no button beside it."""
    words = brief(reasons, limit)
    return words[:1].upper() + words[1:]


def full(reasons: list[str] | str) -> str:
    """Every sentence, one per line, for the tooltip that goes with `brief`."""
    said = [reasons] if isinstance(reasons, str) else [r for r in reasons if r]
    return "\n".join(f"· {r}" for r in said)
