"""Read a .sqx strategy without SQX. It is a ZIP; everything useful is in its inner XML."""

import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

INNER = "strategy_Portfolio.xml"
RESULTS_RE = re.compile(r"Results/[^:]*:\s*([A-Z0-9]+)_([^/]*)/")


def identity(path: Path) -> str:
    """Stable identity of a strategy.

    Args:
        path: A .sqx file.

    Returns:
        SHA-256 of the inner strategy_Portfolio.xml. Never hash the .sqx itself: the ZIP
        embeds timestamps, so identical strategies get different file hashes.
    """
    with zipfile.ZipFile(path) as z:
        inner = next(n for n in z.namelist() if n.endswith(INNER))
        return hashlib.sha256(z.read(inner)).hexdigest()


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
