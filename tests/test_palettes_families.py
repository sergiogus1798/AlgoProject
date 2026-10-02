#!/usr/bin/env python3
"""The seven family palettes are short lists of real blocks, with no clock, no calendar and no stop/limit level."""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import TAXONOMY  # noqa: E402
from sqx.blocks import palette  # noqa: E402
from sqx.blocks.taxonomy import ARCHETYPES, flat, read  # noqa: E402

BLOCKS = flat(read(TAXONOMY))

# One palette per family. The three `_v2` are the reviewed versions of the old bases, kept
# beside them until the owner approves the review; rename here when they replace them.
SEVEN = {"breakout": "ruptura_base_v2", "mean_reversion": "reversion_base_v2",
         "trend": "tendencia_base_v2", "momentum": "momentum_base",
         "volatility": "volatilidad_base", "pattern": "patron_base", "session": "sesion_base"}

# The owner's «no te pases con los indicadores» (2026-10-02), as a number a palette cannot
# drift past unnoticed.
MAX_BLOCKS = 15

# Rule 15: nothing that reads the clock or the calendar. The category holds every such
# block the builder can sample; the pattern catches one that arrives under another category.
CLOCK_CATEGORY = "Bar And Time"
CLOCK = re.compile(r"^(Current|Bar)(Hour|Minute|DayOf|WeekOf|Month|Time)|^IsMonth")

# A value block is one switch for two roles (`sqx/projects/buildingblocks.py`), so a price
# the session palette needs as an indicator also turns on its stop/limit twin. These seven
# are the only ones allowed, and only there: no condition block reads a session's prices.
DUAL_ROLE = {"sesion_base": {"Close", "SessionHigh", "SessionLow", "SessionOpen",
                             "OpenD", "HighD", "LowD"}}


def on(name: str) -> dict[str, dict]:
    """The blocks a palette leaves switched on, as the builder would receive them.

    Args:
        name: The palette's slug.

    Returns:
        Block key to its resolved switch, only the ones in use.
    """
    resolved = palette.resolve(palette.load(name), BLOCKS)
    return {k: r for k, r in resolved.items() if r["use"]}


def test_one_palette_per_family_and_each_loads() -> None:
    """Every one of the seven families has its palette, filed under that family."""
    assert set(SEVEN) == set(ARCHETYPES)
    for family, name in SEVEN.items():
        p = palette.load(name)
        assert p["family"] == family and p["name"] == name and p["unlabelled"] == "off"
        assert p["note"].strip(), f"{name}: no reasoning written"


def test_every_block_exists_and_carries_a_weight_from_1_to_3() -> None:
    """No palette names a block the builder cannot sample, and no weight is off the scale."""
    for name in SEVEN.values():
        overrides = palette.load(name)["overrides"]
        missing = sorted(k for k in overrides if k not in BLOCKS)
        assert not missing, f"{name}: not in the taxonomy: {missing}"
        bad = {k: w for k, w in overrides.items() if w not in (1, 2, 3)}
        assert not bad, f"{name}: weights outside 1-3: {bad}"


def test_a_palette_is_its_list_and_the_list_is_short() -> None:
    """What the builder gets is exactly the listed blocks — the taxonomy adds nothing — and few."""
    for name in SEVEN.values():
        listed = set(palette.load(name)["overrides"])
        assert set(on(name)) == listed, f"{name}: resolves to more or less than its list"
        assert 0 < len(listed) <= MAX_BLOCKS, f"{name}: {len(listed)} blocks"


def test_no_clock_or_calendar_block() -> None:
    """No CurrentHour, no day of month, nothing else that reads the clock or the calendar."""
    for name in SEVEN.values():
        bad = sorted(k for k in on(name)
                     if BLOCKS[k]["category"] == CLOCK_CATEGORY or CLOCK.match(k))
        assert not bad, f"{name}: clock or calendar blocks: {bad}"
    assert CLOCK.match("CurrentHourIs") and CLOCK.match("BarDayOfMonth")
    assert CLOCK.match("CurrentDayOfMonth") and not CLOCK.match("BarRange")


def test_no_stop_limit_block() -> None:
    """No block that is only a stop/limit level; a dual-role value only where declared."""
    for name in SEVEN.values():
        switched = on(name)
        only_level = sorted(k for k, r in switched.items() if r["roles"] == ["level"])
        assert not only_level, f"{name}: stop/limit-only blocks: {only_level}"
        dual = {k for k, r in switched.items() if "level" in r["roles"]}
        assert dual == DUAL_ROLE.get(name, set()), f"{name}: undeclared level role: {sorted(dual)}"


def test_the_shortlist_contract_holds_for_the_whole_library() -> None:
    """Every `unlabelled: off` palette with overrides resolves to its own list, old ones included."""
    for p in palette.catalogue():
        if p["unlabelled"] == "off" and p["overrides"]:
            switched = {k for k, r in palette.resolve(p, BLOCKS).items() if r["use"]}
            listed = {k for k, w in p["overrides"].items() if w > 0 and k in BLOCKS}
            assert switched == listed, f"{p['name']}: {len(switched)} on, {len(listed)} listed"


def main() -> None:
    """Run every test in file order."""
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok", name)


if __name__ == "__main__":
    main()
