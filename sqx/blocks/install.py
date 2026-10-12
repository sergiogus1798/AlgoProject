#!/usr/bin/env python3
"""Install authored custom blocks or random groups into a stopped SQX install's settings."""

import argparse
import os
import shutil
import time
from pathlib import Path
from xml.etree import ElementTree

from core import worker
from core.paths import MASTER, WORKERS
from sqx.blocks import taxonomy

CUSTOM_REL = "user/settings/customBlocks.xml"
GROUPS_REL = "user/settings/blockGroups.xml"
# What each kind of element is stored in, and the attribute that names it.
STORES = {"Item": (CUSTOM_REL, "key"), "Group": (GROUPS_REL, "name")}


def targets() -> dict[str, dict]:
    """Every install this can write to, with the port that says whether it is running.

    Returns:
        Role name to its path and cli port. The master is included and carries no port:
        its GUI is the owner's and is never written to by this tool.
    """
    return {"master": {"path": MASTER, "port": None},
            **{r: {"path": w["path"], "port": w["port"]} for r, w in WORKERS.items()}}


def backup(store: Path) -> Path:
    """Copy a settings store beside itself, the way the GUI does.

    Args:
        store: Path of the install's customBlocks.xml or blockGroups.xml.

    Returns:
        Path of the copy. Named with a millisecond timestamp so it sorts with the GUI's
        own backups in the same folder.
    """
    out = store.parent / f"{store.stem}-backups" / f"{int(time.time() * 1000)}.xml"
    out.parent.mkdir(exist_ok=True)
    shutil.copy2(store, out)
    return out


def store_of(authored: Path) -> tuple[str, str]:
    """Which settings file an authored XML goes into, and the attribute that names an entry.

    Args:
        authored: Blocks (<Item key="CBlock_...">) or groups (<Group name=...>, as
            sqx-random-group emits them under <RandomGroups>).
    """
    return STORES[ElementTree.parse(authored).getroot()[0].tag]


def validate(blocks: Path, store: Path, attr: str) -> None:
    """Refuse an authored XML that does not look like what the store already holds.

    Raises:
        SystemExit: One line naming the first problem; nothing has been written.
    """
    try:
        new = ElementTree.parse(blocks).getroot()
        old = ElementTree.parse(store).getroot()
    except (ElementTree.ParseError, OSError) as err:
        raise SystemExit(f"refused {blocks.name}: cannot read it or the store ({err})")
    shape = {c.tag for c in old}
    for item in new:
        if item.tag not in shape:
            raise SystemExit(f"refused {blocks.name}: <{item.tag}> is not a <{'/'.join(shape)}> "
                             f"of {store.name}")
        key = item.get(attr)
        if not key or (attr == "key" and not key.startswith("CBlock_")):
            raise SystemExit(f"refused {blocks.name}: a <{item.tag}> has {attr}={key!r}, "
                             "custom blocks need a CBlock_ key")
    if not len(new):
        raise SystemExit(f"refused {blocks.name}: it holds no elements")


def install(blocks: Path, into: Path) -> dict[str, list[str]]:
    """Add or replace custom blocks or random groups in one install's store.

    Args:
        blocks: An XML file whose root holds <Item key="CBlock_..."> or <Group> elements.
        into: Top-level install folder.

    Returns:
        "added" and "replaced" names. One already present is replaced in place rather than
        appended twice, because SQX reads the first match and a duplicate is invisible
        until a build uses the wrong one.
    """
    rel, attr = store_of(blocks)
    store = into / rel
    validate(blocks, store, attr)
    tree = ElementTree.parse(store)
    root = tree.getroot()
    present = {item.get(attr): item for item in root}

    out = {"added": [], "replaced": []}
    for item in ElementTree.parse(blocks).getroot():
        key = item.get(attr)
        if key in present:
            root.remove(present[key])
            out["replaced"].append(key)
        else:
            out["added"].append(key)
        root.append(item)

    ElementTree.indent(tree, space="  ")
    tmp = store.with_name(store.name + ".tmp")
    tree.write(tmp, encoding="UTF-8", xml_declaration=True)
    os.replace(tmp, store)
    return out


def main() -> None:
    """Install a block XML into one install, refusing while that install is running."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("blocks", type=Path,
                    help="XML of <Item key='CBlock_...'> blocks, or of <Group> random groups")
    ap.add_argument("--role", default="conductor", choices=sorted(targets()),
                    help="which install to write to; default the conductor")
    args = ap.parse_args()

    target = targets()[args.role]
    if args.role == "master":
        raise SystemExit("the master is the owner's install; author on a worker and hand "
                         "the blocks over")
    if worker.listening(target["port"]):
        raise SystemExit(f"{target['path'].name} is running on port {target['port']}. It "
                         "rewrites user/settings on exit, so this write would be lost. "
                         f"Stop it first: bin/sqx-worker.sh --role {args.role} stop")

    rel = store_of(args.blocks)[0]
    kept = backup(target["path"] / rel)
    done = install(args.blocks, target["path"])
    total = len(ElementTree.parse(target["path"] / rel).getroot())
    print(f"{target['path'].name}: added {done['added']}, replaced {done['replaced']}")
    print(f"  {Path(rel).name} now holds {total}; previous copy kept at {kept}")
    try:
        taxonomy.refresh(args.role)
    except (FileNotFoundError, KeyError, ValueError) as err:    # donor or install files absent
        print(f"  taxonomy NOT refreshed ({err!r}): run python3 -m sqx.blocks.taxonomy "
              f"--role {args.role}")


if __name__ == "__main__":
    main()
