"""The retest universe `assets/_markets.yaml` declares, and the cross-asset notes in `assets/special/`."""

from pathlib import Path
from typing import Any

from core.assetdata import EXPECTED_SIGN, MARKETS, _read
from core.paths import ASSETS


def markets(symbol: str) -> dict[str, Any]:
    """The declared retest universe of one main asset: main, timeframe and categories
    ({family, structural} → [{feed, data_from}]); {} when it is not a declared main."""
    return {} if symbol == EXPECTED_SIGN else _read(MARKETS).get(symbol, {})


def expected_sign() -> dict[str, dict[str, str]]:
    """{idea family: {family: positive, structural: control | none}}; not an asset (owner, 2026-10-12)."""
    return _read(MARKETS).get(EXPECTED_SIGN, {})


def special_notes() -> list[Path]:
    """Cross-asset special cases that apply to every project, sorted."""
    return sorted((ASSETS / "special").glob("*.md"))
