"""gen_group_spike.py — prove the random-group engine against a real 144 export.

For two of the user's real groups — BreakoutChannels (HYBRID, 13 CBlock_* refs) and
ConditionsExample (INLINE, 4 simpleRules + 1 operator) — regenerate EVERY item from
first principles:
  - HYBRID items  from the install's customBlocks.xml (the block-index)
  - INLINE items  from the install's config.xml templates
…reading only the user's scalar CHOICES (which knobs are optimized + their ranges,
the shift, combo picks) from the export. The XML STRUCTURE is built entirely by the
engine. Then canonically diff each regenerated item against the export item.

A PASS means: given a block library + config catalog + the user's choices, the engine
reproduces AlgoWizard's own export — so anything the engine emits will import.

Run:
  python gen_group_spike.py
  python gen_group_spike.py <config.xml> <customBlocks.xml> <export.xml> <out.xml>
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.groups import (  # noqa: E402
    load_templates, load_blocks, load_catalog, inline_item, compare, hybrid_ref,
    make_group, wrap_groups, _params_of, _esc_attr,
)

INSTALL = r"C:\StrategyQuantX"
DEF_CONFIG = INSTALL + r"\internal\web\SQWIZARD\branding\global\config.xml"
DEF_BLOCKS = INSTALL + r"\user\settings\customBlocks.xml"
DEF_EXPORT = str(Path(__file__).resolve().parent.parent / "blockGroups_144_export.xml")
DEF_OUT = str(Path(__file__).resolve().parent.parent / "blockGroups_spike.xml")


# -- read the user's scalar choices off an export item -----------------------
def derive_optimize(item: ET.Element) -> dict[str, str]:
    return {p.get("key"): p.get("randomValue")
            for p in _params_of(item)
            if p.get("generate") == "random" and p.get("randomValue") and p.get("key")}


def derive_shift(item: ET.Element) -> str:
    for p in _params_of(item):
        if p.get("paramType") == "shift":
            return (p.text or "1").strip() or "1"
    return "1"


def derive_picks(item: ET.Element) -> dict[str, str]:
    picks = {}
    for p in _params_of(item):
        if p.get("controlType") == "combo" or p.get("key") == "#Line#":
            picks[p.get("key")] = (p.text or p.get("defaultValue", "0") or "0").strip()
    return picks


# -- canonical (escaping/whitespace/attr-order agnostic) tree compare --------
def canon(e: ET.Element):
    return (e.tag, dict(e.attrib), (e.text or "").strip(), [canon(c) for c in e])


def diff(a: ET.Element, b: ET.Element, path: str = "") -> list[str]:
    """First-order differences between two elements (a=mine, b=export)."""
    out: list[str] = []
    here = f"{path}/{b.tag}[{b.get('key', '')}]"
    if a.tag != b.tag:
        return [f"{here}: tag {a.tag!r} != {b.tag!r}"]
    aa, ba = dict(a.attrib), dict(b.attrib)
    for k in sorted(set(aa) | set(ba)):
        if aa.get(k) != ba.get(k):
            out.append(f"{here} @{k}: mine={aa.get(k)!r} export={ba.get(k)!r}")
    if (a.text or "").strip() != (b.text or "").strip():
        out.append(f"{here} text: mine={(a.text or '').strip()!r} export={(b.text or '').strip()!r}")
    ac, bc = list(a), list(b)
    if len(ac) != len(bc):
        out.append(f"{here}: child count mine={len(ac)} export={len(bc)}")
    else:
        for ca, cb in zip(ac, bc):
            out.extend(diff(ca, cb, here))
    return out


def regen_inline(item: ET.Element, T: dict[str, ET.Element]) -> str:
    key = item.get("key", "")
    if key not in T:
        raise KeyError(f"no config template for inline atom {key!r}")
    return inline_item(T[key], optimize=derive_optimize(item),
                       shift=derive_shift(item), picks=derive_picks(item))


def regen_item(item: ET.Element, T, B) -> str:
    ct, key = item.get("categoryType"), item.get("key", "")
    if ct == "Custom blocks":
        if key not in B:
            raise KeyError(f"block {key!r} not in customBlocks.xml")
        return hybrid_ref(B[key], optimize=derive_optimize(item))
    if ct == "operators":
        operands = [b.find("Item") for b in item.findall("Block")]
        if len(operands) < 2 or operands[0] is None or operands[1] is None:
            raise KeyError(f"operator {key!r} missing operands")
        left = regen_inline(operands[0], T)
        right = regen_inline(operands[1], T)
        return compare(key, _esc_attr(item.get("name", "")),
                       _esc_attr(item.get("display", "")), left, right)
    return regen_inline(item, T)


def main(argv):
    cat_path = None
    if "--catalog" in argv:
        i = argv.index("--catalog")
        cat_path = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    config = argv[0] if len(argv) > 0 else DEF_CONFIG
    blocks_xml = argv[1] if len(argv) > 1 else DEF_BLOCKS
    export_xml = argv[2] if len(argv) > 2 else DEF_EXPORT
    out_xml = argv[3] if len(argv) > 3 else DEF_OUT

    print(f"export  : {export_xml}")
    if cat_path:
        _, T, B = load_catalog(cat_path)
        print(f"source  : catalog {cat_path} -> {len(T)} templates, {len(B)} blocks\n")
    else:
        print(f"config  : {config}\nblocks  : {blocks_xml}")
        T = load_templates(config)
        B = load_blocks(blocks_xml)
        print(f"source  : raw XML -> {len(T)} templates, {len(B)} blocks\n")

    exp_root = ET.parse(export_xml).getroot()
    exp_groups = {g.get("name"): g for g in exp_root.findall("Group")}

    targets = ["BreakoutChannels", "ConditionsExample"]
    my_groups, built, total, matched = [], [], 0, 0

    for gname in targets:
        eg = exp_groups.get(gname)
        if eg is None:
            print(f"!! export has no group {gname!r}; skipping")
            continue
        my_items, problems = [], []
        for it in eg.findall("Item"):
            total += 1
            try:
                xml = regen_item(it, T, B)
            except KeyError as ex:
                problems.append(f"  REGEN-FAIL {it.get('key')}: {ex}")
                continue
            mine = ET.fromstring(xml)
            d = diff(mine, it)
            if d:
                problems.append(f"  DELTA {it.get('key')}:\n    " + "\n    ".join(d))
            else:
                matched += 1
            my_items.append(xml)
        built.append((eg, my_items))
        my_groups.append(make_group(
            name=eg.get("name"), type_=eg.get("type"), items=my_items,
            category=eg.get("category", "No category"), group_id=eg.get("id"),
            status=eg.get("status"), action=eg.get("action")))
        n = len(eg.findall("Item"))
        ok = n - sum(1 for p in problems)
        print(f"[{gname}] {eg.get('type')} — {ok}/{n} items canonically identical to export")
        for p in problems:
            print(p)
        print()

    Path(out_xml).write_text(wrap_groups(my_groups), encoding="utf-8")
    print(f"wrote {out_xml}  (byte-faithful reproduction; reuses your group ids)")

    # safe-to-import variant: NEW uuids + "_Spike" names + status/action, so importing
    # ADDS two fresh groups without touching your existing BreakoutChannels/ConditionsExample
    import_groups = [make_group(
        name=eg.get("name") + "_Spike", type_=eg.get("type"), items=items,
        category=eg.get("category", "No category"), status="0", action="add")
        for eg, items in built]
    import_path = out_xml.replace(".xml", "_import.xml")
    Path(import_path).write_text(wrap_groups(import_groups), encoding="utf-8")
    print(f"wrote {import_path}  (new ids + _Spike names — safe to import as new groups)")

    print(f"\nTOTAL: {matched}/{total} items reproduced byte-for-byte (canonical) from "
          f"templates + block-index + the user's choices")
    return 0 if matched == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
