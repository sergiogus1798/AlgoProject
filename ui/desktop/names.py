"""The one table of family names the window shows: every stored spelling in, one English name out."""

import re
import unicodedata

# Owner, 2026-10-03: «unifica los nombres de familia y paletas», shown in English sentence case.
# Display only — the stored keys stay as each file spells them: the registry's `archetype`
# (ui/daemon/coverage.py), the taxonomy's column (sqx/blocks/taxonomy.yaml), the research
# memory's family (studies/research/memory/config.yaml) and the Spanish label of
# `sqx.blocks.palette.FAMILY_ES`. One row per family, in the coverage's order.
#         registry, taxonomy, research, Spanish label, shown, short
TABLE = [("breakout", "breakout", "ruptura", "Ruptura", "Breakout", "BRK"),
         ("meanReversion", "mean_reversion", "reversion", "Reversión a la media", "Mean reversion", "REV"),
         ("trendFollowing", "trend", "tendencia", "Tendencia", "Trend following", "TRN"),
         ("momentum", "momentum", "momentum", "Momentum", "Momentum", "MOM"),
         ("volatility", "volatility", "volatilidad", "Volatilidad", "Volatility", "VOL"),
         ("pattern", "pattern", "patron", "Patrón", "Pattern", "PAT"),
         ("session", "session", "sesion", "Sesión", "Session", "SES")]
REGISTRY, TAXONOMY, RESEARCH, SPANISH, SHOWN, SHORT = range(6)


def fold(text: str) -> str:
    """A spelling reduced to what identifies it: no case, no accents, no separators."""
    plain = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", plain.lower())


ROW = {fold(cell): row for row in TABLE for cell in row[:SHORT]}


def spelt(key: str, column: int) -> str | None:
    """One family in another file's spelling.

    Args:
        key: The family in any spelling of `TABLE`.
        column: `REGISTRY`, `TAXONOMY`, `RESEARCH`, `SPANISH`, `SHOWN` or `SHORT`.

    Returns:
        That spelling, or None when `key` names none of the seven.
    """
    row = ROW.get(fold(key))
    return row[column] if row else None


def family(key: str) -> str:
    """The name of a family as the window shows it.

    Args:
        key: Any stored spelling — `meanReversion`, `mean_reversion`, `reversion`, «Reversión a
            la media».

    Returns:
        «Mean reversion». A key that is none of the seven (`free`, the calibration shells) comes
        back with a capital and nothing else changed; an empty one is «Sin familia».
    """
    text = str(key or "")
    return spelt(text, SHOWN) or (text[:1].upper() + text[1:] if text else "Sin familia")


def short(key: str) -> str:
    """A family in the few letters a map cell has room for; an unknown key, as it came."""
    return spelt(key, SHORT) or str(key)


# Longest first, so «Reversión a la media» is not cut by «Reversión».
WORDS = sorted([(row[SPANISH], row[SHOWN]) for row in TABLE if row[SPANISH] != row[SHOWN]]
               + [("Reversión", "Mean reversion")], key=lambda pair: -len(pair[0]))


def palette(label: str) -> str:
    """A palette's stored label with the family words in it shown like everywhere else.

    Args:
        label: The label in the palette's YAML — «Ruptura — base (v3, 90-150)».

    Returns:
        «Breakout — base (v3, 90-150)». A lower-case family word inside a label («tendencia +
        reversión») keeps its lower case.
    """
    for spanish, shown in WORDS:
        label = label.replace(spanish, shown).replace(spanish.lower(), shown.lower())
    return label
