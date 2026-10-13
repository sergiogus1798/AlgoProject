#!/usr/bin/env python3
"""The family palettes are lists of real blocks with no clock, no calendar and no stop/limit level: seven short ones, five v3 of 90-150."""

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
DUAL_ROLE = {"sesion_base": {"Close",
                             "OpenD", "HighD", "LowD"}}


# The owner's order of 2026-10-02 on seeing the 6-13 block lists: «yo esperaba al menos 90/100
# hasta 150». The five `_v3` are built for Simple Strategy populations, where the one palette
# feeds the entry and the exit: weight 3 the family's own signals, 2 its context, 1 the
# orthogonal kinds. Counted on what `resolve` returns, values and comparators included.
V3 = {"breakout": "ruptura_base_v3", "mean_reversion": "reversion_base_v3",
      "trend": "tendencia_base_v3", "momentum": "momentum_base_v3",
      "volatility": "volatilidad_base_v3"}
V3_BAND = (90, 150)

# Pullback is not a family of its own: trend context AND reversion trigger, both at weight 3.
# The analysis calls a strategy a pullback when its entry holds one block of each part, so
# each part must stay inside the weight-3 set of the family palette it comes from.
PULLBACK = "pullback_base_v3"
V3_ALL = [*V3.values(), PULLBACK]

# The dual-role values a v3 palette may switch on as indicators: channels, averages and
# plain prices, none of them cut by a time band. `buildingblocks.rewrite` is what keeps
# their stop/limit twin off; a palette only must not grow this set unnoticed.
V3_DUAL: dict[str, set] = {}   # 2026-10-02: v3 palettes carry named signal blocks only, no value blocks

# Prices and levels that exist only inside a time band — the session's, the day's, the
# week's, an anchored VWAP, a volume profile, pivots. The owner has not ruled on them.
BANDED = re.compile(r"^Session|^(Open|High|Low|Close)[DWM]$|^(Highest|Lowest)InRange$|^AnchoredVWAP|AnchoredVWAP$"
                    r"|^VolumeProfile|^TPOProfile|^Pivots$|TimeBreakout|^VP[A-Z]")

# Blocks nobody can vouch for: an all-zero label, and a body in price units behind a
# candle name (read in customBlocks.xml, 2026-10-02).
UNVOUCHED = {"CBlock_BarsLargerRSI", "CBlock_BarsLargerRSI_2",
             "CBlock_BullishMarubozu", "CBlock_BullishMarubozu_2"}


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


def test_v3_each_is_its_list_of_90_to_150_real_blocks() -> None:
    """Five v3 palettes, each exactly its list, every block real, weighted 1-3, 90-150 on."""
    assert set(V3) == set(ARCHETYPES) - {"pattern", "session"}
    for family, name in V3.items():
        p = palette.load(name)
        assert p["family"] == family and p["name"] == name and p["unlabelled"] == "off"
        assert p["note"].strip() and p["based_on"], f"{name}: no reasoning or no parent"
        overrides = p["overrides"]
        missing = sorted(k for k in overrides if k not in BLOCKS)
        assert not missing, f"{name}: not in the taxonomy: {missing}"
        bad = {k: w for k, w in overrides.items() if w not in (1, 2, 3)}
        assert not bad, f"{name}: weights outside 1-3: {bad}"
        switched = on(name)
        assert set(switched) == set(overrides), f"{name}: resolves to more or less than its list"
        assert V3_BAND[0] <= len(switched) <= V3_BAND[1], f"{name}: {len(switched)} blocks on"
        assert palette.summary(palette.resolve(p, BLOCKS))["conditions_ok"], f"{name}: conditions"


def test_v3_no_clock_no_banded_price_no_stop_limit_no_unvouched() -> None:
    """Rule 15 on the v3 lists, plus the session/day prices and the blocks left out on purpose."""
    for name in V3_ALL:
        switched = on(name)
        clock = sorted(k for k in switched
                       if BLOCKS[k]["category"] == CLOCK_CATEGORY or CLOCK.match(k))
        assert not clock, f"{name}: clock or calendar blocks: {clock}"
        banded = sorted(k for k in switched if BANDED.search(k))
        assert not banded, f"{name}: prices or levels of a time band: {banded}"
        only_level = sorted(k for k, r in switched.items() if r["roles"] == ["level"])
        assert not only_level, f"{name}: stop/limit-only blocks: {only_level}"
        dual = {k for k, r in switched.items() if "level" in r["roles"]}
        assert dual == V3_DUAL.get(name, set()), f"{name}: undeclared level role: {sorted(dual)}"
        assert not UNVOUCHED & set(switched), f"{name}: {sorted(UNVOUCHED & set(switched))}"
    for key in ("SessionHigh", "HighD", "CloseW", "HighestInRange", "AnchoredVWAP",
                "CloseAboveAnchoredVWAP", "VPRisingPOC", "CBlock_TimeBreakoutLong"):
        assert BANDED.search(key), key
    for key in ("Close", "High", "Highest", "CloseAboveVWAP", "SuperTrendInRange"):
        assert not BANDED.search(key), key


def test_v3_family_label_means_something() -> None:
    """No block is a weight-3 signal of two families; each family has plenty of its own."""
    own = {name: {k for k, w in palette.load(name)["overrides"].items() if w == 3}
           for name in V3.values()}
    names = sorted(own)
    for i, a in enumerate(names):
        assert len(own[a]) >= 25, f"{a}: only {len(own[a])} weight-3 blocks"
        for b in names[i + 1:]:
            assert not own[a] & own[b], f"{a} and {b} share weight 3: {sorted(own[a] & own[b])}"


def test_pullback_is_trend_context_plus_reversion_trigger_in_band() -> None:
    """Its weight 3 is two identifiable parts, one from each parent's weight 3, and it is 90-150."""
    def own(name: str) -> set[str]:
        """The weight-3 blocks of one palette."""
        return {k for k, w in palette.load(name)["overrides"].items() if w == 3}

    p = palette.load(PULLBACK)
    assert p["unlabelled"] == "off" and p["note"].strip()
    switched = on(PULLBACK)
    assert set(switched) == set(p["overrides"])
    assert set(p["overrides"].values()) <= {1, 2, 3}
    assert V3_BAND[0] <= len(switched) <= V3_BAND[1], f"{len(switched)} blocks on"
    assert palette.summary(palette.resolve(p, BLOCKS))["conditions_ok"]
    trend, reversion = own(V3["trend"]), own(V3["mean_reversion"])
    mine = own(PULLBACK)
    assert mine <= trend | reversion, f"weight 3 from neither parent: {sorted(mine - trend - reversion)}"
    assert len(mine & trend) >= 30 and len(mine & reversion) >= 30
    events = sorted(k for k in mine & trend if "Cross" in k or "Flip" in k)
    assert not events, f"trend context must be states, not events: {events}"


def main() -> None:
    """Run every test in file order."""
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok", name)


if __name__ == "__main__":
    main()
