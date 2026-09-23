"""Read a .sqx strategy without SQX. It is a ZIP; everything useful is in its inner XML."""

import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

INNER = "strategy_Portfolio.xml"
# 🔬 2026-09-23: a retest rewrites `makeExternal` on every <variable> and changes nothing
# else. Hashing the raw XML therefore gives a strategy one identity in the build databank
# and another in the retest one -- 0 of 115 matched. Stripping it: 115 of 115.
COSMETIC = re.compile(r'\s*makeExternal="[^"]*"')
BLOCK_KEY = re.compile(r'<Item[^>]*\bkey="([^"]+)"')
RESULTS_RE = re.compile(r"Results/[^:]*:\s*([A-Z0-9]+)_([^/]*)/")


def identity(path: Path) -> str:
    """Stable identity of a strategy.

    Args:
        path: A .sqx file.

    Returns:
        SHA-256 of the inner strategy_Portfolio.xml with SQX's own bookkeeping stripped.
        Never hash the .sqx itself: the ZIP embeds timestamps, so identical strategies get
        different file hashes. And never hash the XML raw either — a retest flips
        `makeExternal` on every variable, so the same strategy carries one hash in the
        build databank and a different one in the retest databank, which is exactly the
        join those two databanks have to be paired on.
    """
    return hashlib.sha256(COSMETIC.sub("", rules(path)).encode("utf-8")).hexdigest()


def rules(path: Path) -> str:
    """The strategy's definition, as text.

    Args:
        path: A .sqx file.

    Returns:
        The inner strategy_Portfolio.xml decoded. Everything that says what the strategy
        DOES is in here; the rest of the archive is results.
    """
    with zipfile.ZipFile(path) as z:
        inner = next(n for n in z.namelist() if n.endswith(INNER))
        return z.read(inner).decode("utf-8", "replace")


def structure(path: Path) -> str:
    """Identity of a strategy's LOGIC, ignoring what its parameters are set to.

    Args:
        path: A .sqx file.

    Returns:
        SHA-256 over the ordered block keys of the strategy. Two strategies share it when
        they are the same rules at different settings — a moving average of 14 and one of
        90 are one idea, not two. On the 115 of a sample build that is 24 distinct shapes,
        two of them holding 32 strategies each: the population is a sixth as diverse as
        its count suggests.
    """
    return hashlib.sha256("|".join(BLOCK_KEY.findall(rules(path))).encode()).hexdigest()


def symbol(path: Path) -> tuple[str, str]:
    """Symbol and data feed a strategy was tested on.

    Args:
        path: A .sqx file.

    Returns:
        (symbol, feed), e.g. ("XAUUSD", "DukasM1_Infinox_LOM_M30"), read from the ZIP
        entry names. Far cheaper than opening the multi-MB settings.xml.
    """
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            m = RESULTS_RE.search(name)
            if m:
                return m.group(1), m.group(2)
    return "", ""


def xml(path: Path) -> ElementTree.Element:
    """Parsed strategy definition.

    Args:
        path: A .sqx file.

    Returns:
        Root element of strategy_Portfolio.xml — the rules, parameters and orders.
    """
    with zipfile.ZipFile(path) as z:
        inner = next(n for n in z.namelist() if n.endswith(INNER))
        return ElementTree.fromstring(z.read(inner))


def parameters(path: Path) -> dict[str, str]:
    """Every named parameter of a strategy and its value.

    Args:
        path: A .sqx file.

    Returns:
        Parameter name to value as stored, e.g. {"#Size#": "0.1"}. The value is the
        element's text, not an attribute.
    """
    return {p.get("key"): (p.text or "").strip()
            for p in xml(path).iter("Param") if p.get("key")}
