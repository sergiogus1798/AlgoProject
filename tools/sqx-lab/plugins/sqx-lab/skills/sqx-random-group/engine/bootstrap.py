"""bootstrap.py — derive a random-group catalog from a user's OWN install.

A random group pools two kinds of item, so the catalog has two kinds of source:

  INLINE templates  (from config.xml) — the atoms a fresh item is built from:
     • rules  = boolean rule templates   (categoryType="simpleRules": "HMA is falling", …)
     • values = value atoms              (indicator / priceValue / priceRange: EMA, Close, ATR…)
  HYBRID blocks     (from user/settings/customBlocks.xml) — the user's CBlock_* custom blocks,
     re-exported into a pool by reference.

Each entry is stored as a clean <Item> (paramCategory flattened for templates; <Contents>
dropped for blocks) so the proven emitters in groups.py rebuild it byte-faithfully.

Output:
  catalog.json   machine catalog (rules / values / blocks) -> consumed by groups.load_catalog
  catalog.md     human report (your blocks by category; available rules; available value atoms)

Usage:
  python engine/bootstrap.py --install "C:\\StrategyQuantX144"
  python engine/bootstrap.py <config.xml> --blocks <customBlocks.xml>
  python engine/bootstrap.py --install <root> --out-dir .
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

try:                                    # works whether run as a script or imported
    from engine.discover import resolve_install, find_installs, SUBPATHS
except ImportError:
    from discover import resolve_install, find_installs, SUBPATHS

# Shared per-machine state + install validation live in sqx_common at the plugin root.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sqx_common import (  # noqa: E402
    load_shared_install, save_shared_install, install_file, skill_dir,
    validate_install, install_error)

SKILL_DIR = skill_dir(__file__)

# categoryTypes harvested as INLINE value atoms (operands / bare value items).
VALUE_CATEGORY_TYPES = {"indicator", "priceValue", "priceRange"}
VALUE_RETURN_TYPES = {"price", "pricerange", "number", "pricenumber"}


def _params_of(item: ET.Element) -> list[ET.Element]:
    """Direct-child <Param>s plus those nested in <paramCategory> (config form)."""
    out: list[ET.Element] = []
    for child in item:
        if child.tag == "Param":
            out.append(child)
        elif child.tag == "paramCategory":
            out.extend(pc for pc in child if pc.tag == "Param")
    return out


def _clean_item(item: ET.Element, params: list[ET.Element]) -> str:
    """Rebuild a minimal <Item attribs> + given <Param>s (flattened, no paramCategory,
    no <Contents>) and return its XML string."""
    clean = ET.Element("Item", dict(item.attrib))
    for p in params:
        clean.append(copy.deepcopy(p))
    return ET.tostring(clean, encoding="unicode")


def harvest_templates(config_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """From config.xml: {rule_key: xml} (simpleRules) and {value_key: xml} (value atoms).
    Keeps the richest schema per key; flattens paramCategory."""
    root = ET.parse(config_path).getroot()
    rules: dict[str, str] = {}
    values: dict[str, str] = {}
    rule_np: dict[str, int] = {}
    value_np: dict[str, int] = {}
    for item in root.iter("Item"):
        key = item.get("key")
        if not key:
            continue
        params = _params_of(item)
        if not params:                              # weight-preset stubs have none
            continue
        ct = item.get("categoryType")
        if ct == "simpleRules":
            if rule_np.get(key, -1) < len(params):
                rules[key] = _clean_item(item, params)
                rule_np[key] = len(params)
        elif ct in VALUE_CATEGORY_TYPES and item.get("returnType") in VALUE_RETURN_TYPES:
            if value_np.get(key, -1) < len(params):
                values[key] = _clean_item(item, params)
                value_np[key] = len(params)
    return rules, values


def harvest_blocks(blocks_path: Path) -> tuple[dict[str, str], dict[str, dict]]:
    """From customBlocks.xml: {CBlock_key: xml} (attribs + TOP-LEVEL params only, <Contents>
    dropped) plus a small meta dict per block (type, category, returnType, oppositeBlockKey)
    for the human report."""
    root = ET.parse(blocks_path).getroot()
    blocks: dict[str, str] = {}
    meta: dict[str, dict] = {}
    for it in root.findall("Item"):
        key = it.get("key")
        if not key:
            continue
        blocks[key] = _clean_item(it, it.findall("Param"))   # top-level params only
        meta[key] = {
            "name": it.get("name", ""),
            "type": it.get("type", ""),                  # Condition | Price level
            "returnType": it.get("returnType", ""),
            "category": it.get("category", ""),
            "opposite": it.get("oppositeBlockKey", ""),
            "display": it.get("display", ""),
        }
    return blocks, meta


def build_catalog(config_path: Path, blocks_path: Path | None,
                  install_root: str | None = None) -> dict:
    rules, values = harvest_templates(config_path)
    blocks, block_meta = harvest_blocks(blocks_path) if blocks_path else ({}, {})
    # group blocks by (type, category) for the report
    by_cat: dict[str, list[str]] = {}
    for k, m in block_meta.items():
        bucket = f"{m['type'] or 'Condition'} / {m['category'] or 'No category'}"
        by_cat.setdefault(bucket, []).append(k)
    return {
        # provenance — meta.skill lets load_catalog name the owner of a wrong-flavour
        # file; the top-level "install" is what doctor.py reads for its
        # which-install/stale-catalog check (it was missing here: P0-2).
        "install": str(install_root) if install_root else None,
        "meta": {
            "skill": "sqx-random-group",
            "install": str(install_root) if install_root else None,
            "config_path": str(config_path),
            "blocks_path": str(blocks_path) if blocks_path else None,
            "rules_count": len(rules),
            "values_count": len(values),
            "blocks_count": len(blocks),
            "blocks_by_bucket": {b: sorted(ks) for b, ks in sorted(by_cat.items())},
        },
        "rules": rules,
        "values": values,
        "blocks": blocks,
        "block_meta": block_meta,
    }


def _render_md(catalog: dict) -> str:
    m = catalog["meta"]
    bm = catalog["block_meta"]
    lines = [
        "# Random-group catalog — discovered from this install",
        "",
        f"- config.xml: `{m['config_path']}`",
        f"- customBlocks.xml: `{m['blocks_path']}`" if m["blocks_path"] else "- customBlocks.xml: (none — hybrid pools unavailable)",
        f"- **{m['blocks_count']} of YOUR custom blocks** (poolable by reference, HYBRID mode)",
        f"- **{m['rules_count']} inline rule templates** + **{m['values_count']} inline value atoms** (INLINE mode)",
        "",
        "A **Condition** group pools boolean items (custom blocks of type Condition, simpleRules,",
        "or operator comparisons). A **Value** group pools price/number items (Price-level custom",
        "blocks, or value atoms). An item is FLAT — a single rule or one comparison; compound",
        "AND/OR logic belongs in a custom block, then pooled via HYBRID.",
        "",
    ]
    # YOUR custom blocks, grouped — the hybrid pool source
    lines.append(f"## ⭐ YOUR custom blocks — poolable via HYBRID ({m['blocks_count']})")
    lines.append("")
    if not bm:
        lines.append("_None found — point bootstrap at your install's customBlocks.xml to enable hybrid pools._")
        lines.append("")
    else:
        for bucket, keys in m["blocks_by_bucket"].items():
            lines.append(f"### {bucket}  ({len(keys)})")
            lines.append("")
            lines.append("| key | name | returnType | opposite |")
            lines.append("|---|---|---|---|")
            for k in keys:
                e = bm[k]
                opp = e["opposite"] or ""
                lines.append(f"| `{k}` | {e['name']} | {e['returnType']} | {opp} |")
            lines.append("")
    # inline rules
    lines.append(f"## Inline rule templates — boolean, for Condition groups ({m['rules_count']})")
    lines.append("")
    lines.append("Build with `inline_item(T[key], optimize={...})`. Each is a single boolean rule.")
    lines.append("")
    lines.append("`" + "`, `".join(sorted(catalog["rules"])) + "`" if catalog["rules"] else "_none_")
    lines.append("")
    # inline values
    lines.append(f"## Inline value atoms — price/number, for Value groups or comparison operands ({m['values_count']})")
    lines.append("")
    lines.append("Build with `inline_item(T[key], ...)`; combine two via `is_greater(left, right)` etc.")
    lines.append("")
    lines.append("`" + "`, `".join(sorted(catalog["values"])) + "`" if catalog["values"] else "_none_")
    lines.append("")
    return "\n".join(lines)


def write_catalog(catalog: dict, out_dir: Path) -> tuple[Path, Path]:
    out_json = out_dir / "catalog.json"
    out_md = out_dir / "catalog.md"
    out_json.write_text(json.dumps(catalog, indent=1, ensure_ascii=False), encoding="utf-8")
    out_md.write_text(_render_md(catalog), encoding="utf-8")
    return out_json, out_md


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Derive a random-group catalog from a user's install.")
    ap.add_argument("config", nargs="?", help="path to config.xml (or use --install / --auto)")
    ap.add_argument("--install", help="SQX install root — derives config + customBlocks paths")
    ap.add_argument("--auto", action="store_true", help="auto-discover the SQX install (CLI convenience)")
    ap.add_argument("--blocks", help="override path to customBlocks.xml (the hybrid block source)")
    # Defaults to the SKILL folder, not the cwd — see the same note in
    # sqx-custom-block/engine/bootstrap.py.
    ap.add_argument("--out-dir", default=str(SKILL_DIR),
                    help="where to write catalog.json / catalog.md (default: the skill folder)")
    args = ap.parse_args(argv)

    config_path = blocks_path = None
    install_root = None

    if not (args.auto or args.install or args.config):
        shared = load_shared_install()
        if shared:
            print(f"using stored SQX install ({install_file()}): {shared}")
            args.install = shared

    if args.auto or args.install:
        if args.install:
            check = validate_install(args.install)
            if not check["is_sqx"]:
                print(install_error(check, rerun='python engine/bootstrap.py '
                                                 '--install "<your SQX install folder>"'))
                return 1
            info = resolve_install(Path(args.install))
        else:
            real = [i for i in find_installs() if i["is_sqx_install"]]
            if not real:
                print("FAIL: no SQX install auto-discovered. Use --install <folder>.")
                return 1
            if len(real) > 1:
                print("Multiple installs found — pick one with --install:")
                for i in real:
                    print(f'  python engine/bootstrap.py --install "{i["root"]}"')
                return 1
            info = real[0]
            print(f"discovered SQX install: {info['root']}")
        install_root = info["root"]
        config_path = Path(info["config"])
        blocks_path = Path(info["export"]) if info["export"] else None   # export == customBlocks.xml
    elif args.config:
        config_path = Path(args.config)
    else:
        # First contact for a brand-new user: give the fix, not an argparse usage dump.
        print("No StrategyQuant X install is set up yet.\n")
        print("  Easiest:  run  /sqx-setup   (points all four sqx-lab skills at your install)")
        print("  Or here:  python engine/bootstrap.py --install \"<your SQX folder>\"\n")
        print("The folder wanted is the TOP-LEVEL StrategyQuant X folder — the one containing")
        print("internal\\ and user\\ (e.g. C:\\StrategyQuantX144).")
        print("\n  python engine/discover.py     will suggest installs found on this machine.")
        return 2

    if args.blocks:
        blocks_path = Path(args.blocks)
    if not config_path.exists():
        print(f"FAIL: config.xml not found: {config_path}")
        return 1
    if blocks_path and not blocks_path.exists():
        print(f"  note: no customBlocks.xml at {blocks_path} — hybrid pools unavailable")
        blocks_path = None

    catalog = build_catalog(config_path, blocks_path, install_root)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    j, md = write_catalog(catalog, out_dir)
    m = catalog["meta"]
    print(f"OK  {m['blocks_count']} custom blocks (hybrid) + {m['rules_count']} rules + "
          f"{m['values_count']} value atoms (inline)")
    print(f"    {j}")
    print(f"    {md}")
    if install_root and not save_shared_install(install_root):
        print(f"    note: could not store the install path in {install_file()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
