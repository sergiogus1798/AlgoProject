#!/usr/bin/env python3
"""Install authored custom blocks or random groups into a stopped SQX install's settings."""

import argparse
import shutil
import socket
import time
from pathlib import Path
from xml.etree import ElementTree

from core.paths import MASTER, WORKERS

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


def is_running(port: int) -> bool:
    """Whether something answers on an install's command port.

    Args:
        port: The install's sqcli port.

    Returns:
        True when the port is listening. SQX rewrites user/settings on exit, so a write
        while it is up is silently undone — this is the guard against that.
    """
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


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
    tree.write(store, encoding="UTF-8", xml_declaration=True)
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
    if is_running(target["port"]):
        raise SystemExit(f"{target['path'].name} is running on port {target['port']}. It "
                         "rewrites user/settings on exit, so this write would be lost. "
                         f"Stop it first: bin/sqx-worker.sh --role {args.role} stop")

    rel = store_of(args.blocks)[0]
    kept = backup(target["path"] / rel)
    done = install(args.blocks, target["path"])
    total = len(ElementTree.parse(target["path"] / rel).getroot())
    print(f"{target['path'].name}: added {done['added']}, replaced {done['replaced']}")
    print(f"  {Path(rel).name} now holds {total}; previous copy kept at {kept}")


if __name__ == "__main__":
    main()
