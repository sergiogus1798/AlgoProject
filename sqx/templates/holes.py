#!/usr/bin/env python3
"""Which parts of a template the builder fills at random, and what each one may sample."""

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.paths import MASTER
from core.sqxfile import INNER
from sqx.inspect.template_check import blocks, rules

GROUPS_REL = "user/settings/blockGroups.xml"

# The two random blocks a template can point at a pool. The rest of the randomBlock family
# — SameCondition, NegatedCondition, OppositeValue — repeat or invert another hole rather
# than drawing from anywhere, so they carry no group and nothing can narrow them.
HOLES = {"RandomCondition": "condition", "RandomValue": "value"}
LOGIC = {"AND", "OR", "Not"}


def group_names(install: Path) -> dict[str, str]:
    """Random group id to its name.

    Args:
        install: Top-level install folder.

    Returns:
        The map a template needs to be read: a hole stores its group as the group's id,
        not its name, so a template alone cannot say what it is bound to. Empty when the
        install is absent — a machine with no SQX, Windows included — and every bound hole
        then reads as bound to a group this install does not have.
    """
    if not (install / GROUPS_REL).exists():
        return {}
    root = ElementTree.parse(install / GROUPS_REL).getroot()
    return {g.get("id"): g.get("name") for g in root}


def shape(path: Path, install: Path = MASTER) -> dict:
    """What one template leaves to the builder and what it nails down.

    Args:
        path: A template .sqx.
        install: The install whose groups resolve the holes' ids.

    Returns:
        `holes`, one entry per random block with the group it is bound to or None, and
        `fixed`, the blocks the template writes in literally. The distinction is the whole
        point: a palette of building blocks reaches a free hole and nothing else — a bound
        hole samples its group and a fixed block is part of the skeleton, neither of which
        the switches can touch (`knowhow/authoring/builder-block-switches.md`, 2026-09-24).
    """
    names = group_names(install)
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read(next(n for n in z.namelist() if n.endswith(INNER))))
    found = []
    for item in root.iter("Item"):
        if item.get("key") not in HOLES:
            continue
        group = next((p.text for p in item if p.get("key") == "#Group#"), None)
        found.append({"id": next((p.text for p in item if p.get("key") == "#Identification#"),
                                 item.get("key")),
                      "kind": HOLES[item.get("key")],
                      "group": names.get(group, group) if group else None,
                      "unknown_group": bool(group) and group not in names})
    return {"holes": found, "fixed": sorted(blocks(rules(path)))}


def _count(item: ElementTree.Element, got: dict[str, int]) -> None:
    """Add one node of a signal's tree to the count, walking through AND, OR and Not."""
    if item.get("key") in LOGIC:
        for child in item.findall("Block/Item"):
            _count(child, got)
    elif item.get("categoryType") == "randomBlock":
        bound = any(p.get("key") == "#Group#" and (p.text or "").strip() for p in item)
        got["bound" if bound else "free"] += 1
    else:
        # Owner, 2026-10-05: the same condition twice on two periods (double ROC, double Vortex)
        # is ONE idea, so a side counts each distinct block shape once.
        twin = tuple(i.get("key") for i in item.iter("Item"))
        got["fixed"] += twin not in got.setdefault("_twins", set())
        got["_twins"].add(twin)


def conditions(path: Path) -> dict[str, dict[str, int]]:
    """How many conditions a template nails down and how many it leaves open, per side.

    Args:
        path: A template .sqx.

    Returns:
        `entry` and `exit`, each `fixed` (a literal condition), `bound` (a random block tied to
        a group — how this project fixes an idea and still draws its periods, `build.group_xml`)
        and `free` (a random block with no group: the hole a palette governs). A side is read
        off the signal variable's name (`LongEntrySignal`, `ShortExitSignal`…); of a side's
        signals the fullest one counts, since one strategy trades one direction (rule 13).
    """
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read(next(n for n in z.namelist() if n.endswith(INNER))))
    names = {v.findtext("id"): v.findtext("name") or "" for v in root.iter("variable")}
    out = {side: {"fixed": 0, "bound": 0, "free": 0} for side in ("entry", "exit")}
    for signal in root.iter("signal"):
        got = {"fixed": 0, "bound": 0, "free": 0}
        for item in signal.findall("Item"):
            _count(item, got)
        side = "exit" if "Exit" in names.get(signal.get("variable"), "") else "entry"
        got.pop("_twins", None)
        if sum(got.values()) > sum(out[side].values()):
            out[side] = got
    return out


def reach(shape_of: dict) -> str:
    """One sentence on whether a palette can do anything to this template.

    Args:
        shape_of: A shape().

    Returns:
        Spanish, because it is rendered straight into the window. The count of free holes
        is the only number that decides it.
    """
    free = [h for h in shape_of["holes"] if not h["group"]]
    bound = [h for h in shape_of["holes"] if h["group"]]
    if not shape_of["holes"]:
        return "Sin huecos aleatorios: el builder no sortea nada y la paleta no la toca."
    if not free:
        return (f"Los {len(bound)} huecos están atados a grupos "
                f"({', '.join(sorted({h['group'] for h in bound}))}). "
                "La paleta NO la toca: para estrecharla hay que cambiar el grupo.")
    return (f"{len(free)} hueco(s) libre(s): la paleta sí los gobierna."
            + (f" Otros {len(bound)} están atados a un grupo y se le escapan." if bound else ""))
