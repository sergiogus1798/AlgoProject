"""Read a StrategyQuant X install -> catalog of usable random groups (+ block count).

The research agent reasons over this catalog; the generator binds to it.
Usage:  python discover.py [INSTALL_PATH]
Writes catalog.json next to this file and prints a summary.

A group is CLEAN when every CBlock_* it references exists in the install's
customBlocks.xml. Inline groups (native atoms, no CBlock_*) are clean by definition.
"""
import sys, os, re, json, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

# Shared per-machine state + install validation live in sqx_common at the plugin root.
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..")))
from sqx_common import (  # noqa: E402
    load_shared_install, save_shared_install, validate_install, install_error)

CATALOG = os.path.join(HERE, "catalog.json")


def load(install):
    """Groups in this install, each marked clean/broken.

    A broken group references a CBlock_* that isn't in customBlocks.xml — usually the
    group was imported (or survived a reinstall) but its blocks weren't. We keep the
    full item metadata for the missing ones so the group can actually be REPAIRED
    (see repair_manifest) instead of just silently vanishing from the catalog.
    """
    settings = os.path.join(install, "user", "settings")
    bg = ET.parse(os.path.join(settings, "blockGroups.xml")).getroot()
    cb_raw = open(os.path.join(settings, "customBlocks.xml"),
                  encoding="utf-8", errors="replace").read()
    avail = set(re.findall(r'key="(CBlock_[A-Za-z0-9_]+)"', cb_raw))
    groups = []
    for g in bg.iter("Group"):
        items = g.findall("Item")
        cbk = [it.get("key") for it in items if (it.get("key") or "").startswith("CBlock_")]
        miss = [k for k in cbk if k not in avail and k != "CBlock_null"]
        blocks = [dict(key=it.get("key"), display=it.get("display"),
                       type=it.get("type")) for it in items]
        groups.append(dict(
            id=g.get("id"), name=g.get("name"), type=g.get("type"),
            category=g.get("category"), n=len(items),
            mode="inline" if not cbk else "hybrid",
            clean=(len(miss) == 0), missing=miss,
            blocks=blocks,
            # what a repair would have to rebuild: key + the human rule + return type
            missing_specs=[b for b in blocks if b["key"] in miss],
        ))
    return groups, len(avail)


def repair_manifest(groups):
    """The broken groups, shaped as a work order for the sqx-custom-block skill.

    Every missing block still carries its `display` (the rule in AlgoWizard's own
    words, e.g. "Close crosses above Prior Day High") and its return type — which is
    enough to re-author it. Without this a broken group is a dead end: discover just
    dropped it and never said what would fix it.
    """
    out = []
    for g in groups:
        if g["clean"] or not g["missing_specs"]:
            continue
        out.append(dict(
            group=g["name"], group_type=g["type"], category=g["category"],
            rebuild=[dict(key=b["key"], rule=b["display"] or "(no display text)",
                          block_type=("Price level" if g["type"] == "Value" else "Condition"))
                     for b in g["missing_specs"]],
        ))
    return out


def main():
    install = sys.argv[1] if len(sys.argv) > 1 else load_shared_install()
    if not install:
        raise SystemExit('usage: python engine/discover.py "<install folder>"\n'
                         '(no SQX install stored yet — pass the folder once; it is then '
                         'shared across all sqx-lab skills)')
    # Validate before touching the filesystem: a wrong folder used to surface as a raw
    # FileNotFoundError traceback out of ET.parse.
    info = validate_install(install, need=("block_groups", "custom_blocks"))
    if not info["ok"]:
        raise SystemExit(install_error(
            info, rerun='python engine/discover.py "<your SQX install folder>"'))
    install = info["root"]

    groups, nblocks = load(install)
    clean = [g for g in groups if g["clean"]]
    cond = [g for g in clean if g["type"] == "Condition"]
    val = [g for g in clean if g["type"] == "Value"]
    broken = [g for g in groups if not g["clean"]]
    repairs = repair_manifest(groups)
    # meta: mtimes (epoch floats) of the two source files this catalog was built from,
    # so doctor can flag a catalog that predates the current install state (stale
    # catalogs otherwise fail three steps later as "group not in install").
    settings = os.path.join(install, "user", "settings")
    meta = dict(
        blockgroups_mtime=os.path.getmtime(os.path.join(settings, "blockGroups.xml")),
        customblocks_mtime=os.path.getmtime(os.path.join(settings, "customBlocks.xml")))
    out = dict(install=install, n_custom_blocks=nblocks,
               clean_condition_groups=cond, clean_value_groups=val,
               broken_groups=broken, repair_manifest=repairs, meta=meta)
    json.dump(out, open(CATALOG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"install: {install}")
    print(f"custom blocks: {nblocks}\n")
    print(f"CLEAN Condition groups ({len(cond)}) -- usable as filters/triggers:")
    for g in cond:
        print(f"   {g['name']:28} {g['n']:2} items  [{g['mode']:6}]  {g['category']}")
    print(f"\nCLEAN Value groups ({len(val)}) -- usable as stop/limit price pools:")
    for g in val:
        print(f"   {g['name']:28} {g['n']:2} items  [{g['mode']:6}]  {g['category']}")

    if broken:
        print(f"\nBROKEN — excluded from every design ({len(broken)}):")
        for g in broken:
            print(f"   {g['name']:28} {g['type']:9} missing {len(g['missing'])} of "
                  f"{g['n']} blocks")
        n_rebuild = sum(len(r["rebuild"]) for r in repairs)
        print(f"\n   These groups reference {n_rebuild} CBlock_* that are not in this")
        print("   install's customBlocks.xml — the group was imported but its blocks")
        print("   were not. catalog.json now carries a `repair_manifest` with each")
        print("   missing block's rule text: hand it to the sqx-custom-block skill to")
        print("   re-author them, import the XML, then re-run this discover.")

    # The shapes that need a price pool (stop / stop_long / mtf_filter) are the
    # build-confirmed ones — say so loudly rather than letting the user discover it
    # as a mysterious "SKIP" three steps later.
    if not val:
        broken_val = [g["name"] for g in broken if g["type"] == "Value"]
        print("\nWARNING: no CLEAN Value group -> the shapes that need a price pool")
        print("         (stop, stop_long, mtf_filter — the build-confirmed ones) cannot")
        print("         be generated. Only market-entry shapes are available.")
        if broken_val:
            print(f"         Repairing {', '.join(broken_val)} would unlock them.")
    if len(cond) < 2:
        print("\nWARNING: fewer than 2 CLEAN Condition groups -> most shapes need a")
        print("         filter AND a trigger. Build more with sqx-random-group.")

    print(f"\nwrote {CATALOG}")
    save_shared_install(install)


if __name__ == "__main__":
    main()
