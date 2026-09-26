"""Read the builder's reachable blocks off an install and a donor's Build task."""

from pathlib import Path

from core.cfx import task_xml, tasks
from sqx.inspect.vocabulary import pooled_by

# The three switches a Build task carries over the same vocabulary, one per role the block
# can play. The catalogue says what the install knows; this says what the builder may draw.
ROLES = {"signals": "signal", "indicators": "indicator", "stopLimitBlocks": "level"}


def builder_roles(cfx: Path) -> dict[str, list[str]]:
    """Which roles each block may play, read off a project's Build task.

    Args:
        cfx: A project.cfx holding a Build task.

    Returns:
        Block key to its roles. The task namespaces the value blocks — `Indicators.ATR`
        and `Stop/Limit Price Ranges.ATR` are the single `ATR` of the catalogue seen in
        two roles — so the prefix is stripped and the roles collected under one key.
    """
    member = next(t["file"] for t in tasks(str(cfx)) if t["type"] == "Build")
    found: dict[str, list[str]] = {}
    for block in task_xml(str(cfx), member).find(".//Blocks/BuildingBlocks"):
        found.setdefault(block.get("key").rsplit(".", 1)[-1], []).append(
            ROLES[block.get("category")])
    return found


def with_newer_own(roles: dict[str, list[str]], vocab: dict) -> list[str]:
    """Add the owner's blocks the donor's list predates, in place.

    Args:
        roles: builder_roles() of the donor, modified.
        vocab: A vocabulary() of the install.

    Returns:
        The keys added. A donor is frozen, so a block authored after it was taken is not
        in its `<BuildingBlocks>` — and SQX builds with it anyway, measured on the Keltner
        blocks of 2026-09-22. Without this the taxonomy silently loses every block
        authored since, which is exactly the set being worked on.
    """
    added = []
    for key, block in vocab["custom"].items():
        if key not in roles:
            roles[key] = ["level" if block["section"] == "Price level" else "signal"]
            added.append(key)
    return sorted(added)


def entry(key: str, vocab: dict, roles: list[str]) -> tuple[str, dict]:
    """One block's row: what it is, where it sits, and an empty label to fill.

    Args:
        key: Block key, native or CBlock_ prefixed.
        vocab: A vocabulary() of the install.
        roles: The roles the builder lets it play.

    Returns:
        Its category, then the derived half of the row plus an empty `archetypes`. `form`
        is the block's written display and `help` is SQX's own sentence about it — together
        they are what settles whether a block tests a transition or a state, which is the
        distinction the whole labelling turns on. `help` is omitted when SQX ships none,
        which is the case for 317 of the 767.
    """
    known = vocab["native"].get(key) or vocab["custom"][key]
    row = {"roles": roles,
           "origin": "native" if key in vocab["native"] else "own",
           "form": " ".join((known["display"] or key).split()),
           "groups": pooled_by(vocab, key),
           "archetypes": {}}
    if known.get("help"):
        row["help"] = " ".join(known["help"].split())
    return known["category"], row


def grouped(vocab: dict, roles: dict[str, list[str]]) -> dict[str, dict]:
    """Every reachable block, nested under its SQX category.

    Args:
        vocab: A vocabulary() of the install.
        roles: builder_roles() of the donor.

    Returns:
        Category name to its blocks, both sorted. A flat map of 767 keys is unreadable and
        a category is the unit somebody labelling actually works in — the sixteen Keltner
        conditions are one decision, not sixteen.
    """
    out: dict[str, dict] = {}
    for key, played in roles.items():
        category, row = entry(key, vocab, played)
        out.setdefault(category, {})[key] = row
    return {cat: dict(sorted(blocks.items())) for cat, blocks in sorted(out.items())}
