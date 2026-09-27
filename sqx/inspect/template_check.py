#!/usr/bin/env python3
"""Check whether the strategies a project built really use the blocks its template declares."""

import argparse
import json
import random
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core.cfx import resolve, task_xml, tasks
from core.paths import MASTER, WORKERS, project_dir
from core.sqxfile import INNER

# Item categories that name a real trading block. Operators, brackets and variables are
# structure: every strategy has them whatever template built it.
# "Custom blocks" was missing until 2026-09-22 and the omission was not visible: a template
# whose only fixed block is a custom one signed as MarketPositionIsLong instead, which every
# strategy carries, so the check reported a confident pass about the wrong block.
BLOCK_CATEGORIES = ("indicator", "simpleRules", "priceValue", "priceRange", "Custom blocks")

# A random block is the hole the builder fills, so what it contains is not fixed by the
# template and must not enter the signature.
RANDOM_CATEGORY = "randomBlock"

SAMPLE = 0          # strategies opened per databank; 0 is all of them


def blocks(node: ElementTree.Element) -> set[str]:
    """Trading blocks fixed by a rule tree, ignoring what random blocks will contain.

    Args:
        node: A Rules element, from a template or from a built strategy.

    Returns:
        Item keys such as {"Vortex", "StdDevLower"}. Descendants of a random block are
        skipped: the builder chooses those, so they say nothing about the template.
    """
    found = set()
    for child in node:
        if child.tag == "Item":
            if child.get("categoryType") == RANDOM_CATEGORY:
                continue
            if child.get("categoryType") in BLOCK_CATEGORIES:
                found.add(child.get("key"))
        found |= blocks(child)
    return found


def rules(path: Path) -> ElementTree.Element:
    """The Rules element of a .sqx, template or strategy alike.

    Args:
        path: A .sqx file.

    Returns:
        Root of the rule tree — entries, exits and their conditions.
    """
    with zipfile.ZipFile(path) as z:
        inner = next(n for n in z.namelist() if n.endswith(INNER))
        return ElementTree.fromstring(z.read(inner)).find(".//Rules")


def signature(template: Path) -> set[str]:
    """The blocks a template fixes: written in literally, or as the only item of its hole's group.

    Args:
        template: A template .sqx.

    Returns:
        Item keys every strategy it builds must carry. Since 2026-09-26 the owner's condition
        sits in a one-item random group, so its period is drawn per strategy (a frozen block
        would carry one period everywhere): that hole is random in form and fixed in content.
        Without it the only fixed block left was MarketPositionIsLong, which every strategy
        carries, and the check passed about the wrong block.
    """
    with zipfile.ZipFile(template) as z:
        root = ElementTree.fromstring(z.read(next(n for n in z.namelist() if n.endswith(INNER))))
    groups = {g.get("id"): [i.get("key") for i in g.findall("Item")]
              for g in root.iter("Group")}
    bound = {p.text for p in root.find(".//Rules").iter("Param")
             if p.get("key") == "#Group#" and p.text}
    return blocks(root.find(".//Rules")) | {groups[g][0] for g in bound
                                            if len(groups.get(g, [])) == 1}


def carried(path: Path) -> set[str]:
    """Every block key a built strategy's rules hold, filled holes included.

    Args:
        path: A strategy .sqx.

    Returns:
        Item keys. A block the builder drew into a hole carries no categoryType, so
        `blocks()` would not see the owner's condition in the very strategies it built.
    """
    return {i.get("key") for i in rules(path).iter("Item")}


def build_settings(project: str) -> dict:
    """What the project's first Build task says it builds.

    Args:
        project: Project name on the master, or a path to a .cfx.

    Returns:
        The StrategyType attributes — `type` ("simple" or "template") and `templateFile`
        — or None when the project has no Build task.
    """
    for t in tasks(project):
        if t["type"] == "Build":
            node = task_xml(project, t["file"]).find("WhatToBuild/StrategyType")
            return dict(node.attrib)
    return None


def databanks(project: str, install: Path = MASTER) -> dict[str, list[Path]]:
    """Every .sqx a project has on disk, by the databank holding it.

    Args:
        project: Project name.
        install: Which install holds it; the master by default.

    Returns:
        Databank name to its files. Empty when the project's databanks live only in
        memory — see knowhow/databanks/sync-deletes-unloaded-files.md. An "Existing portfolio" databank holds
        strategies imported from elsewhere, so it says nothing about this builder.
    """
    root = project_dir(project, install) / "databanks"
    found = {}
    for f in sorted(root.rglob("*.sqx")):
        found.setdefault(f.relative_to(root).parts[0], []).append(f)
    return found


def verdict(project: str, sample: int, seed: int, install: Path = MASTER) -> dict:
    """Whether one project's strategies on disk carry its template's blocks.

    Args:
        project: Project name on the master.
        sample: How many strategies to open per databank, drawn at random; 0 opens all.
        seed: Seed for that draw, so a rerun reports the same figure.
        install: Which install holds the project; the master by default. A template built
            on a worker has to be checked on that worker — the master knows nothing of it.

    Returns:
        The declared type and template, the blocks the template fixes, and per databank
        how many of the sampled strategies contain all of them.
    """
    settings = build_settings(str(project_dir(project, install) / "project.cfx"))
    if settings is None:
        return {"project": project, "note": "no build task"}
    template = Path(settings.get("templateFile", ""))
    row = {"project": project, "declared": settings.get("type"), "template": template.name}
    if not template.is_absolute() or not template.exists():
        return {**row, "note": "template file missing"}

    fixed = signature(template)
    row["signature"] = sorted(fixed)
    if not fixed:
        return {**row, "note": "template fixes no blocks, only random groups"}
    found = databanks(project, install)
    if not found:
        return {**row, "note": "no strategies on disk"}

    rng = random.Random(seed)
    row["databanks"] = {}
    for name, pool in found.items():
        picked = rng.sample(pool, min(sample, len(pool))) if sample else pool
        row["databanks"][name] = {"checked": len(picked),
                                  "carrying": sum(fixed <= carried(p) for p in picked)}
    return row


def main() -> None:
    """Report every project on the master, or the ones named."""
    ap = argparse.ArgumentParser()
    ap.add_argument("projects", nargs="*", help="project names; default is all of them")
    ap.add_argument("-n", "--sample", type=int, default=SAMPLE)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--role", choices=sorted(WORKERS), help="check a worker's projects instead")
    a = ap.parse_args()

    install = WORKERS[a.role]["path"] if a.role else MASTER
    names = a.projects or sorted(d.name for d in (install / "user/projects").iterdir()
                                 if (d / "project.cfx").exists())
    rows = [verdict(n, a.sample, a.seed, install) for n in names]

    if a.json:
        print(json.dumps(rows, indent=2))
        return
    for r in rows:
        head = f"{r['project']:22} {r.get('declared') or '-':9} {r.get('template') or '-'}"
        if "databanks" not in r:
            print(f"{head}\n    {r['note']}")
            continue
        print(f"{head}\n    template fixes {', '.join(r['signature'])}")
        for name, c in sorted(r["databanks"].items()):
            mark = "ok" if c["carrying"] == c["checked"] else "TEMPLATE NOT APPLIED"
            print(f"    {name:28} {c['carrying']:>4}/{c['checked']:<4} carry it   {mark}")


if __name__ == "__main__":
    main()
