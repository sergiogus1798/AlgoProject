"""What the window needs to draw the palette library, and the four writes it may do."""

from core.paths import TAXONOMY
from sqx.blocks import palette
from sqx.blocks.taxonomy import ARCHETYPES, flat, read
from ui.daemon.coverage import ARCHETYPES as REGISTRY_ARCHETYPES

# The registry names seven archetypes for the coverage matrix; the taxonomy labels blocks
# against three families. They are different axes and only three of the seven line up. The
# other four are left unmapped on purpose: inventing a family for `momentum` would put
# blocks into a palette nobody chose. The window shows "sin paleta" for those.
FAMILY = {"breakout": "breakout", "meanReversion": "mean_reversion", "trendFollowing": "trend"}

WIRE = ("use", "weight", "why")


def state() -> dict:
    """Everything the palette view draws, in one round trip.

    Returns:
        The flat taxonomy, one entry per palette in the library with its file, its
        resolution and its summary, the families and the map from the registry's
        archetypes to them. The resolution is trimmed to the three fields the window
        paints: roles and groups are already on the block, and sending them once per
        palette would multiply the payload by the size of the library.
    """
    all_of = palette.everything()
    for entry in all_of["palettes"].values():
        entry["resolved"] = {key: {k: r[k] for k in WIRE}
                             for key, r in entry["resolved"].items()}
    return {**all_of, "family": FAMILY, "families": list(ARCHETYPES),
            "family_labels": palette.FAMILY_ES, "archetypes": list(REGISTRY_ARCHETYPES),
            "unlabelled_policies": list(palette.UNLABELLED)}


def resolved(p: dict) -> dict:
    """One palette against the taxonomy on disk.

    Args:
        p: A loaded palette.

    Returns:
        Its resolve(), read fresh so a label written since the window opened is picked up.
    """
    return palette.resolve(p, flat(read(TAXONOMY)))


def save(name: str, unlabelled: str, overrides: dict[str, int], label: str,
         note: str) -> dict:
    """Write one palette and hand back what it now resolves to.

    Args:
        name: Its slug.
        unlabelled: "neutral" or "off".
        overrides: Block key to weight, 0 meaning off. Replaces the stored map whole — the
            window holds the complete set, so merging here would make a deletion in the
            window impossible to express.
        label: Its name on screen.
        note: What it is for, in the owner's words.

    Returns:
        The palette as written, its summary, and where the file landed.
    """
    p = palette.load(name)
    p.update({"unlabelled": unlabelled, "label": label, "note": note,
              "overrides": {k: int(v) for k, v in overrides.items()}})
    where = palette.save(p)
    return {"palette": p, "summary": palette.summary(resolved(p)), "path": str(where)}


def create(name: str, label: str, family: str, source: str | None) -> dict:
    """Add a palette to the library, empty or cloned.

    Args:
        name: Slug for the new file.
        label: What it is called on screen.
        family: Which taxonomy column it reads.
        source: Slug to clone, or None.

    Returns:
        The palette as written and its summary.
    """
    p = palette.create(name, label, family, source)
    return {"palette": p, "summary": palette.summary(resolved(p))}


def remove(name: str) -> dict:
    """Take a palette out of the library.

    Args:
        name: Its slug.

    Returns:
        What was removed, so the window can say so rather than just redraw.
    """
    palette.delete(name)
    return {"deleted": name}
