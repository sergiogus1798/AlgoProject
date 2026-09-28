"""The one way the window prints a number: never scientific, thousands grouped, K and M when large."""

import math

SIGNIFICANT = 4         # digits kept below 1 000, as `.4g` did, but always written out in full
FLOOR = 1e-10           # below this a figure prints as 0: no metric here lives down there
P_FLOOR = 0.0001        # the smallest p-value printed as a number; below it «< 0.0001»


def _grouped(whole: int) -> str:
    """An integer with its thousands split by a space: «12 345»."""
    return f"{whole:,}".replace(",", " ")


def _plain(v: float) -> str:
    """A float with four significant digits written in full, trailing zeros dropped."""
    a = abs(v)
    if a < FLOOR:
        return "0"
    if a >= 1000 or float(v).is_integer():
        return _grouped(round(v))
    decimals = min(SIGNIFICANT - 1 - math.floor(math.log10(a)), 10)
    return f"{v:.{decimals}f}".rstrip("0").rstrip(".")


def _scaled(v: float) -> str:
    """A figure of 100 000 or more as K or M, one decimal: «123.5 K», «2.4 M»."""
    a = abs(v)
    if a < 1e5:
        return _plain(v)
    size, suffix = (1e6, "M") if a >= 999_950 else (1e3, "K")   # «1000 K» reads as «1 M»
    head = v / size
    text = _grouped(round(head)) if abs(head) >= 1000 else f"{head:.1f}".rstrip("0").rstrip(".")
    return f"{text} {suffix}"


def num(value: object, unit: str = "") -> str:
    """A value as every view prints it.

    Args:
        value: A number, None (missing), NaN (missing) or text, which passes through.
        unit: Appended after a space («%», «pips», «días»). The unit «p» marks a p-value:
            four decimals, and «< 0.0001» below that, instead of a unit written out.

    Returns:
        The text; «—» for a missing value. Never scientific notation: under 1e-4 `.4g`
        switched to «1e-05», which the owner cannot read at a glance.
    """
    if value is None:
        return "—"
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "sí" if value else "no"
    v = float(value)
    if math.isnan(v):
        return "—"
    if math.isinf(v):
        return "∞" if v > 0 else "−∞"
    if unit == "p":
        return f"< {P_FLOOR}" if v < P_FLOOR else f"{v:.4f}"
    text = _scaled(v)
    return f"{text} {unit}" if unit else text
