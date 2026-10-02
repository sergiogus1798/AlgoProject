#!/usr/bin/env python3
"""The block taxonomy carries seven weights 0-3 on every block, and the palettes still resolve."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.paths import TAXONOMY  # noqa: E402
from sqx.blocks import palette  # noqa: E402
from sqx.blocks.taxonomy import ARCHETYPES, family_blocks, flat, read  # noqa: E402
from ui.daemon import palettes as daemon_palettes  # noqa: E402

BLOCKS = flat(read(TAXONOMY))


def test_seven_families_in_the_registry_order() -> None:
    """Seven families in the registry order."""
    assert ARCHETYPES == ("breakout", "mean_reversion", "trend", "momentum", "volatility",
                          "pattern", "session")


def test_every_block_has_exactly_seven_weights_in_range() -> None:
    """Every block has exactly seven weights in range."""
    bad = {k: r["archetypes"] for k, r in BLOCKS.items()
           if set(r["archetypes"]) != set(ARCHETYPES)
           or any(w not in (0, 1, 2, 3) for w in r["archetypes"].values())}
    assert len(BLOCKS) == 767 and not bad, f"{len(bad)} blocks off-schema, first: {list(bad.items())[:3]}"


def test_a_zero_is_rare_and_all_zero_blocks_are_the_listed_ones() -> None:
    """A zero is rare and all zero blocks are the listed ones."""
    all_zero = sorted(k for k, r in BLOCKS.items() if not any(r["archetypes"].values()))
    assert all_zero == ["CBlock_BarsLargerRSI", "CBlock_BarsLargerRSI_2"]
    zeros = sum(w == 0 for r in BLOCKS.values() for w in r["archetypes"].values())
    assert zeros < 0.03 * len(BLOCKS) * len(ARCHETYPES)


def test_family_blocks_filters_by_weight_and_role() -> None:
    """Family blocks filters by weight and role."""
    top = family_blocks("breakout", 3)
    assert "CBlock_BreakoutDonchianLong" in top and all(w == 3 for w in top.values())
    assert set(family_blocks("session", 2)) >= set(family_blocks("session", 3))
    assert all("signal" in BLOCKS[k]["roles"] for k in family_blocks("pattern", 3, role="signal"))


def test_the_labelled_before_keep_their_breakout_weight() -> None:
    """The labelled before keep their breakout weight."""
    assert BLOCKS["Highest"]["archetypes"]["breakout"] == 3
    assert BLOCKS["ATRRising"]["archetypes"]["breakout"] == 2


def test_the_palettes_load_and_resolve_against_seven_families() -> None:
    """The palettes load and resolve against seven families."""
    library = palette.catalogue()
    assert {p["family"] for p in library} <= set(ARCHETYPES) and library
    assert set(palette.FAMILY_ES) == set(ARCHETYPES)
    for p in library:
        resolved = palette.resolve(p, BLOCKS)
        assert len(resolved) == len(BLOCKS) and palette.summary(resolved)["signal"]["on"] > 0
    assert set(daemon_palettes.FAMILY.values()) == set(ARCHETYPES)
