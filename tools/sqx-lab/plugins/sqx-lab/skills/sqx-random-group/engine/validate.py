"""validate.py — lint a random-group set before import.

  python engine/validate.py <set>.xml
  python engine/validate.py <set>.xml --install "C:\\StrategyQuantX144"
  python engine/validate.py <set>.xml --catalog catalog.json

Checks (root must be <RandomGroups>):
  [1/8] well-formed XML, root <RandomGroups>
  [2/8] non-empty set — at least one <Group> (an empty file imports as NOTHING)
  [3/8] no empty group — every <Group> holds at least one <Item> (a 0-item pool is
        dead weight the builder samples nothing from)
  [4/8] unique <Param> keys within each item
  [5/8] group shape — id/name/type/strategyType present; type in {Condition, Value};
        names + ids unique; item returnType matches the group type
        (Condition -> boolean; Value -> price/pricerange/number/pricenumber)
  [6/8] flat items — no AND/OR joiner inside a group item (compound logic belongs in a
        custom block, then pooled by reference)
  [7/8] operator operands — every <Block> operand slot holds a keyed <Item>
  [8/8] hybrid CBlock_* keys resolve — a dead pool (a key its source cannot resolve)
        is a FAILURE, not a warning. Resolution source, in priority order:
          1. LIVE install — --install, else the stored shared install
             (reads <install>/user/settings/customBlocks.xml, the import-time truth)
          2. --catalog    — the bootstrap catalog's "blocks" section
        With neither source available the check DEGRADES to a warning that says why.

Warnings (allowed — do not fail the build):
  - <Group> missing status/action (AlgoWizard tolerates absence; a UI-made group omits them)
  - a frozen numeric knob — an int/double <Param> (not shift, not combo) without
    generate="random": the builder won't vary it; legitimate, but flagged
  - oppositeBlockKey pointing outside this file (cross-file hybrid; CBlock_null is ignored)
  - hybrid keys UNVERIFIED because neither a live install nor a catalog was available

Exit 0 if no failures (warnings allowed), 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Shared install state + validation live in sqx_common at the plugin root.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sqx_common import (  # noqa: E402
    SUBPATHS, install_error, load_shared_install, validate_install)

VALUE_RETURN_TYPES = {"price", "pricerange", "number", "pricenumber"}


def _hybrid_keys(root: ET.Element) -> dict[str, int]:
    """Every CBlock_* item key referenced anywhere in the tree (top-level hybrid items
    AND nested references inside comparison operands), with occurrence counts."""
    out: dict[str, int] = {}
    for it in root.iter("Item"):
        k = it.get("key") or ""
        if k.startswith("CBlock_") or (k and it.get("categoryType") == "Custom blocks"):
            out[k] = out.get(k, 0) + 1
    return out


def _resolve_blocks_source(args) -> tuple[str, str, set[str] | None, list[str]]:
    """Where hybrid CBlock_* keys are resolved from: ("live"|"catalog"|"none", desc,
    keys, notes). Priority: --install / stored shared install (the LIVE
    customBlocks.xml) > --catalog blocks > nothing (degraded).
    An explicitly given but unusable --install is a hard SystemExit — never a silent
    downgrade; an unusable STORED install only downgrades, with a printed note."""
    notes: list[str] = []
    root = args.install or load_shared_install()
    if root:
        via = "--install" if args.install else "stored shared install"
        info = validate_install(root)
        if info["is_sqx"]:
            cb = info["resolved"].get("custom_blocks")
            if cb is None:
                desc = (f"{Path(info['root']) / SUBPATHS['custom_blocks']} — the {via} "
                        f"install has NO customBlocks.xml, so no CBlock_* key can resolve")
                return "live", desc, set(), notes
            try:
                keys = {it.get("key")
                        for it in ET.parse(cb).getroot().findall("Item") if it.get("key")}
                return "live", cb, keys, notes
            except ET.ParseError as e:
                if args.install:
                    raise SystemExit(f"FAIL: cannot parse live customBlocks.xml ({cb}): {e}")
                notes.append(f"note: stored install's customBlocks.xml unparseable ({e}) "
                             f"— falling back to --catalog")
        else:
            if args.install:
                raise SystemExit(install_error(
                    info, rerun='python engine/validate.py <set>.xml --install "<SQX folder>"'))
            notes.append(f"note: stored install unusable ({info.get('reason', '?')}: "
                         f"{info['root']}) — falling back to --catalog")
    if args.catalog:
        p = Path(args.catalog)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise SystemExit(f"FAIL: cannot read catalog {p}: {e}")
        if isinstance(data, dict) and "blocks" in data:
            return "catalog", str(p), set(data["blocks"]), notes
        notes.append(f"note: {p} has no 'blocks' section — not an sqx-random-group "
                     f"catalog (rebuild it: python engine/bootstrap.py)")
    return ("none", "no live install (--install / stored) and no usable --catalog",
            None, notes)


def _validate(root: ET.Element, blocks_source: tuple[str, str, set[str] | None]) -> int:
    mode, src_desc, known_keys = blocks_source
    groups = root.findall("Group")
    items = root.findall("Group/Item")
    print(f"PASS [1/8] well-formed XML ({len(groups)} <Group>, {len(items)} <Item>, root <RandomGroups>)")

    failures: list[str] = []
    warnings: list[str] = []

    # [2/8] non-empty set — an empty file imports as NOTHING but still "succeeds"
    if groups:
        print(f"PASS [2/8] non-empty set ({len(groups)} group(s))")
    else:
        failures.append("FAIL [2/8] empty set — no <Group> in the file; importing it changes "
                        "NOTHING. Generate at least one group.")

    # [3/8] no empty group — a 0-item pool is dead weight in the builder
    empty_groups = [g.get("name") or "<no-name>" for g in groups if not g.findall("Item")]
    if empty_groups:
        failures.append("FAIL [3/8] empty group(s) — 0 items, the builder would sample from "
                        "NOTHING:\n  " + "\n  ".join(empty_groups))
    elif groups:
        print("PASS [3/8] every group holds at least one item")

    # [4/8] unique param keys within each item
    dup = []
    for it in items:
        keys = [k for p in it.findall("Param") if (k := p.get("key"))]
        d = {k for k in keys if keys.count(k) > 1}
        if d:
            dup.append(f"{it.get('key')}: {sorted(d)}")
    if dup:
        failures.append("FAIL [4/8] duplicate param keys within item:\n  " + "\n  ".join(dup))
    else:
        print("PASS [4/8] no duplicate param keys within items")

    # [5/8] group shape
    shape: list[str] = []
    seen_names: dict[str, int] = {}
    seen_ids: dict[str, int] = {}
    for g in groups:
        gname = g.get("name") or "<no-name>"
        for attr in ("id", "name", "type", "strategyType"):
            if g.get(attr) is None:
                shape.append(f"group {gname!r} missing attr {attr!r}")
        for attr in ("status", "action"):
            if g.get(attr) is None:
                warnings.append(f"WARN group {gname!r} missing recommended attr {attr!r} (tolerated; emit for explicitness)")
        gtype = g.get("type")
        if gtype not in ("Condition", "Value"):
            shape.append(f"group {gname!r} type={gtype!r} not in {{Condition, Value}}")
        if g.get("name"):
            seen_names[gname] = seen_names.get(gname, 0) + 1
        gid = g.get("id")
        if gid:
            seen_ids[gid] = seen_ids.get(gid, 0) + 1
        for it in g.findall("Item"):
            rt = it.get("returnType")
            if gtype == "Condition" and rt != "boolean":
                shape.append(f"group {gname!r} (Condition): item {it.get('key')!r} returnType={rt!r}, expected 'boolean'")
            elif gtype == "Value" and rt not in VALUE_RETURN_TYPES:
                shape.append(f"group {gname!r} (Value): item {it.get('key')!r} returnType={rt!r}, expected one of {sorted(VALUE_RETURN_TYPES)}")
    for name, c in seen_names.items():
        if c > 1:
            shape.append(f"duplicate group name {name!r} ({c}x)")
    for gid, c in seen_ids.items():
        if c > 1:
            shape.append(f"duplicate group id {gid!r} ({c}x)")
    if shape:
        failures.append("FAIL [5/8] group-shape problems:\n  " + "\n  ".join(shape))
    else:
        print("PASS [5/8] group-shape rules satisfied")

    # [6/8] flat items — no AND/OR joiner anywhere inside an item
    compound = []
    for it in items:
        if any(sub.get("key") in ("AND", "OR") for sub in it.iter("Item")):
            compound.append(it.get("key") or "<no-key>")
    if compound:
        failures.append("FAIL [6/8] compound items (AND/OR not allowed in a group item — "
                        "put the logic in a custom block, then pool it):\n  " + "\n  ".join(compound))
    else:
        print("PASS [6/8] all items flat (single rule / comparison)")

    # [7/8] operator operands — every <Block> slot must hold a keyed <Item> operand
    badop = []
    for it in items:
        for b in it.iter("Block"):
            kids = b.findall("Item")
            if not kids:
                badop.append(f"{it.get('key')}: <Block key={b.get('key')!r}> holds no operand <Item>")
            else:
                badop.extend(f"{it.get('key')}: <Block key={b.get('key')!r}> operand <Item> has no key"
                             for c in kids if not c.get("key"))
    if badop:
        failures.append("FAIL [7/8] empty operator operand(s) — the rule would compare against "
                        "NOTHING:\n  " + "\n  ".join(badop))
    else:
        print("PASS [7/8] operator operands all present and keyed")

    # [8/8] hybrid CBlock_* keys resolve (dead pools FAIL — they import as items the
    # builder can never use; that is P0-3, previously a warning at best)
    hybrid = _hybrid_keys(root)
    if not hybrid:
        print("PASS [8/8] no hybrid CBlock_* references (nothing to resolve)")
    elif mode == "none":
        warnings.append(
            f"WARN [8/8] DEGRADED — {len(hybrid)} hybrid CBlock_* key(s) NOT verified: "
            f"{src_desc}.\n  Pass --install \"<SQX folder>\" (preferred, checks the LIVE "
            f"customBlocks.xml) or --catalog catalog.json to enable the dead-pool check.")
    else:
        label = "LIVE install customBlocks.xml" if mode == "live" else "catalog blocks"
        unknown = sorted(k for k in hybrid if k not in (known_keys or set()))
        if unknown:
            failures.append(
                f"FAIL [8/8] dead hybrid pool — {len(unknown)} of {len(hybrid)} CBlock_* "
                f"key(s) do not exist in the {label}\n  ({src_desc}):\n  "
                + "\n  ".join(unknown)
                + "\n  An item referencing a missing block imports as DEAD WEIGHT the builder "
                  "can never sample.\n  Re-author the block(s) with the sqx-custom-block skill, "
                  "or drop these items and regenerate.")
        else:
            print(f"PASS [8/8] all {len(hybrid)} hybrid CBlock_* key(s) resolve against the {label}")

    # warnings — cross-file opposite (CBlock_null ignored)
    by_key = {it.get("key") for it in items}
    cross = [f"{it.get('key')} -> {it.get('oppositeBlockKey')}"
             for it in items
             if it.get("oppositeBlockKey") and it.get("oppositeBlockKey") not in ("CBlock_null",)
             and it.get("oppositeBlockKey") not in by_key]
    if cross:
        warnings.append("WARN oppositeBlockKey resolves outside this file (cross-file hybrid — normal):\n  " + "\n  ".join(cross))

    # warnings — frozen optimizer knobs: ANY numeric knob (type int/double, or a
    # period param), excluding bar-shift and combo picks. The old period/double-only
    # gate was blind to every custom-block #IntN# knob (P0-13).
    inert = []
    for it in items:
        for p in it.iter("Param"):
            numeric = p.get("type") in ("int", "double") or p.get("paramType") == "period"
            if not numeric or p.get("paramType") == "shift" or p.get("controlType") == "combo":
                continue
            if p.get("generate") != "random" or not p.get("randomValue"):
                inert.append(f"{it.get('key')}.{p.get('key')}")
    if inert:
        warnings.append("WARN frozen params (no generate=\"random\" — builder won't optimize these; "
                        "fine if intended):\n  " + "\n  ".join(inert))

    if warnings:
        print()
        for w in warnings:
            print(w)
    if failures:
        print()
        for f in failures:
            print(f)
        return 1
    return 0


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Validate a random-group set XML.")
    ap.add_argument("path", help="the <RandomGroups> .xml to check")
    ap.add_argument("--install", help="SQX install root — resolve hybrid CBlock_* keys "
                                      "against its LIVE user/settings/customBlocks.xml "
                                      "(default: the stored shared install, if any)")
    ap.add_argument("--catalog", help="catalog.json fallback for hybrid-key resolution "
                                      "(used when no live install is available)")
    args = ap.parse_args(argv)

    xml_path = Path(args.path)
    if not xml_path.exists():
        print(f"FAIL: file not found: {xml_path}")
        return 1
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as e:
        print(f"FAIL XML parse error: {e}")
        return 1
    if root.tag != "RandomGroups":
        print(f"FAIL unknown root <{root.tag}> (expected <RandomGroups>)")
        return 1

    mode, desc, keys, notes = _resolve_blocks_source(args)
    for n in notes:
        print(n)

    rc = _validate(root, (mode, desc, keys))
    if rc == 0:
        if mode == "none" and _hybrid_keys(root):
            print(f"\n7/8 CHECKS PASSED — {xml_path.name}: hybrid CBlock_* keys UNVERIFIED "
                  f"(no live install and no catalog; see WARN [8/8] above)")
        else:
            print(f"\nALL CHECKS PASSED — {xml_path.name} is ready to import")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
