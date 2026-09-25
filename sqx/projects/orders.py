#!/usr/bin/env python3
"""Whether a population trades with pending orders — what the builder allowed, what it emitted."""

import re
import zipfile
from pathlib import Path

# A pending order is one that sits in the book waiting for price. Those are the only ones a
# broker can refuse for being too close to the market, which is what RandomizeMinDistance
# perturbs — with market entries alone that task randomises a number nothing reads.
PENDING = ("EnterAtStop", "EnterAtLimit")
ORDER_BLOCK = re.compile(r'<Block\b[^>]*category="orderTypes"[^>]*>')
ENTRY_ITEM = re.compile(r'<Item\b[^>]*\bkey="(Enter\w+)"')
PORTFOLIO = "strategy_Portfolio.xml"


def allowed(text: str) -> set[str]:
    """The entry order types a Build task lets its generator emit.

    Args:
        text: A task XML. A task with no generator returns the empty set.

    Returns:
        The block keys switched on, e.g. {"EnterAtMarket"}. This is the ceiling on the
        population: what the generator could not emit cannot be in the databank.
    """
    on = set()
    for tag in ORDER_BLOCK.findall(text):
        key = re.search(r'key="([^"]*)"', tag).group(1)
        if re.search(r'use="true"', tag):
            on.add(key)
    return on


def carried(strategy: Path) -> set[str]:
    """The entry order types one built strategy actually uses.

    Args:
        strategy: A .sqx from a databank directory.

    Returns:
        The `Enter…` item keys its portfolio declares. Read from `strategy_Portfolio.xml`
        and not from the task that made it: a databank can hold strategies imported or
        carried over from a build with other rules.
    """
    with zipfile.ZipFile(strategy) as z:
        return set(ENTRY_ITEM.findall(z.read(PORTFOLIO).decode("utf-8", "replace")))


def population(databank: Path) -> tuple[set[str], int]:
    """What a whole databank trades with, stopping as soon as a pending order shows up.

    Args:
        databank: A project's databank directory, holding one .sqx per strategy.

    Returns:
        The order types seen and how many strategies were opened to see them. The scan
        stops at the first pending order because the question is "is there any", and a
        full databank is ten thousand zip files.
    """
    seen, read = set(), 0
    for strategy in sorted(databank.glob("*.sqx")):
        seen |= carried(strategy)
        read += 1
        if seen & set(PENDING):
            break
    return seen, read


def pending_orders(members: dict[str, bytes], databank: Path | None) -> dict:
    """Whether the MinDist task has anything to perturb, and on what evidence.

    Args:
        members: The .cfx contents by member name, for the project's Build task.
        databank: The input databank directory, when it has already been built. None or
            an empty directory falls back to what the build task allows.

    Returns:
        `pending` — True, False, or None when it cannot be settled yet — plus `types`
        (what was seen), `source` (population or generator) and `read` (strategies
        opened). The owner's rule is about the population: the task is written only when
        the build actually produced strategies with stop or limit orders. Before the build
        there is no population, and then only one answer is still certain — a generator
        that may not emit a pending order cannot have produced one. A generator that may
        leaves the question open, and open is None rather than a guess in either
        direction: writing the task costs a run that perturbs nothing, omitting it leaves
        a hole in the study, and neither is the caller's to swallow silently.
    """
    if databank and any(databank.glob("*.sqx")):
        seen, read = population(databank)
        return {"pending": bool(seen & set(PENDING)), "types": sorted(seen),
                "source": "population", "read": read}
    may = set().union(*(allowed(b.decode("utf-8", "replace")) for n, b in members.items()
                        if n.endswith(".xml") and n != "config.xml"))
    return {"pending": None if may & set(PENDING) else False, "types": sorted(may),
            "source": "generator", "read": 0}
