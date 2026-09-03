"""validate.py — lint a custom-block batch before importing into AlgoWizard.

Stdlib + the plugin's shared sqx_common helpers. Auto-detects <CustomBlocks> (block
mode) vs <RandomGroups> (group mode). Block mode runs 7 checks; the last two encode
lessons that have bitten real batches, as automated gates rather than prose:

  1) Well-formed XML            (also catches unescaped < > & " in help/display)
  2) No duplicate Item keys
  3) Long/short pairs symmetric (A.opposite==B and B.opposite==A)
  4) Every #ParamN# in <Contents> is declared as a top-level <Param>
  5) Unique <Param> keys within each block
  6) Block name does NOT end in _<digits>... suffix  (AlgoWizard UI strips that,
     breaking opposite-block links — name suffix lesson)
  7) [needs catalog] every multi-output atom used carries a #Line# param, and no
     talib_* atom is used (multi-output + Stockpicker-NPE lessons)

Usage:
  python engine/validate.py out.xml                            # checks 1-6 + a
                                                               # visible check-7 SKIPPED note
  python engine/validate.py out.xml --catalog catalog.json     # enables check 7

A --catalog path that does not exist falls back to the skill's own catalog
(sqx_common.find_catalog); if none exists either, this is a HARD FAIL (exit 1,
paths searched printed) — never a silent 6-check "ALL CHECKS PASSED".

Exit 0 = all checks pass (warnings allowed), 1 = a failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Shared helpers live in sqx_common at the plugin root (3 levels up from engine/).
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from sqx_common import find_catalog, utf8_stdout  # noqa: E402

PARAM_REF_RE = re.compile(r"#[A-Za-z][A-Za-z0-9]*#")
NUMBERED_PARAM_RE = re.compile(r"#(Period|Double|Int|Shift|Chart)\d+#")
# _<digits> followed by a letter then anything alphanumeric: _144Native, _2v3,
# _2V3, _3x ... (the old r"_\d+[A-Za-z]+$" missed _2v3 — the example every doc cites)
NAME_SUFFIX_RE = re.compile(r"_\d+[A-Za-z][A-Za-z0-9]*$")
VALUE_RETURN_TYPES = {"price", "pricerange", "number", "pricenumber"}


def _unique_param_keys(items, label_attr="key"):
    dups = []
    for it in items:
        keys = [k for k in (p.get("key") for p in it.findall("Param")) if k is not None]
        d = {k for k in keys if keys.count(k) > 1}
        if d:
            dups.append(f"{it.get(label_attr) or '<no-key>'}: {sorted(d)}")
    return dups


def _validate_blocks(root, catalog=None):
    items = root.findall("Item")
    n = 7 if catalog else 6
    print(f"PASS [1/{n}] well-formed XML ({len(items)} <Item> blocks)")
    failures, warnings = [], []

    keys = [k for k in (it.get("key") for it in items) if k is not None]
    dups = {k for k in keys if keys.count(k) > 1}
    print(f"{'FAIL' if dups else 'PASS'} [2/{n}] "
          + (f"duplicate keys: {sorted(dups)}" if dups else "no duplicate keys"))
    if dups:
        failures.append(f"duplicate keys: {sorted(dups)}")

    by_key = {it.get("key"): it for it in items}
    asym = []
    for it in items:
        opp = it.get("oppositeBlockKey")
        if not opp or opp == "CBlock_null":
            continue
        partner = by_key.get(opp)
        if partner is None:
            asym.append(f"{it.get('key')} -> {opp} (partner not in batch)")
        elif partner.get("oppositeBlockKey") != it.get("key"):
            asym.append(f"{it.get('key')} <-> {opp} (back-link {partner.get('oppositeBlockKey')!r})")
    print(f"{'FAIL' if asym else 'PASS'} [3/{n}] opposite pairs symmetric")
    if asym:
        failures.append("asymmetric opposites:\n  " + "\n  ".join(asym))

    undeclared = []
    for it in items:
        top = {p.get("key") for p in it.findall("Param") if p.get("key")}
        top.add("#Chart1#")
        contents = it.find("Contents")
        xml = ET.tostring(contents, encoding="unicode") if contents is not None else ""
        refs = {r for r in PARAM_REF_RE.findall(xml) if NUMBERED_PARAM_RE.match(r)}
        missing = refs - top
        if missing:
            undeclared.append(f"{it.get('key')}: {sorted(missing)}")
    print(f"{'FAIL' if undeclared else 'PASS'} [4/{n}] every param reference declared")
    if undeclared:
        failures.append("undeclared params:\n  " + "\n  ".join(undeclared))

    intra = _unique_param_keys(items)
    print(f"{'FAIL' if intra else 'PASS'} [5/{n}] unique param keys within blocks")
    if intra:
        failures.append("duplicate param keys:\n  " + "\n  ".join(intra))

    bad_names = [it.get("name") for it in items
                 if it.get("name") and NAME_SUFFIX_RE.search(it.get("name"))]
    print(f"{'FAIL' if bad_names else 'PASS'} [6/{n}] no _<digits><letters> name suffixes")
    if bad_names:
        failures.append("names ending _<digits><letters> (AlgoWizard strips these): "
                        + ", ".join(bad_names))

    if catalog:
        line_missing, talib_used = [], []
        for it in items:
            for atom in it.iter("Item"):
                k = atom.get("key")
                ce = catalog.get(k)
                if not ce:
                    continue
                if not ce.get("usable_single_symbol", True):
                    talib_used.append(f"{it.get('key')} uses talib atom {k}")
                if ce.get("multi_output") and not any(
                    p.get("key") == "#Line#" for p in atom.findall("Param")
                ):
                    line_missing.append(f"{it.get('key')} uses multi-output {k} without #Line#")
        problems = line_missing + talib_used
        print(f"{'FAIL' if problems else 'PASS'} [7/{n}] multi-output #Line# present & no talib atoms")
        if problems:
            failures.append("catalog checks:\n  " + "\n  ".join(problems))

    if warnings:
        print()
        for w in warnings:
            print("WARN", w)
    if failures:
        print()
        for f in failures:
            print("FAIL:", f)
        return 1
    return 0


def main(argv):
    utf8_stdout()
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--catalog", help="catalog.json — enables the multi-output/talib check")
    args = ap.parse_args(argv)

    p = Path(args.path)
    if not p.exists():
        print(f"FAIL: file not found: {p}")
        return 1
    try:
        root = ET.parse(p).getroot()
    except ET.ParseError as e:
        print(f"FAIL XML parse error (often an unescaped < > & or \" in help/display): {e}")
        return 1

    catalog = None
    if args.catalog:
        catalog_path = Path(args.catalog)
        if not catalog_path.exists():
            fallback = find_catalog(__file__)
            if fallback is not None:
                # Not silent: say what was asked for and what is actually used.
                print(f"note: --catalog {catalog_path} not found — "
                      f"falling back to {fallback}")
                catalog_path = fallback
            else:
                # HARD FAIL. The old behaviour — quietly skipping check 7 (the two
                # AlgoWizard build-crash gates) and still printing ALL CHECKS
                # PASSED — is exactly the silent lie the audit flagged (P0-11).
                skill = Path(__file__).resolve().parent.parent
                print(f"FAIL: --catalog {catalog_path} not found, and no fallback "
                      f"catalog.json exists. Paths searched:")
                for cand in (catalog_path, Path.cwd() / "catalog.json",
                             skill / "catalog.json", skill / "engine" / "catalog.json"):
                    print(f"  {cand}")
                print("Check 7 (multi-output #Line# + talib gate) cannot run without it.")
                print('Bootstrap one first:  python engine/bootstrap.py --install "<SQX folder>"')
                return 1
        catalog = json.loads(catalog_path.read_text(encoding="utf-8")).get("atoms", {})

    if root.tag == "CustomBlocks":
        rc = _validate_blocks(root, catalog)
        if catalog is None:
            print("\nNOTE: check 7 SKIPPED (multi-output #Line# + talib gate) — "
                  "no --catalog given.")
            print("      Re-run with  --catalog <skill>/catalog.json  for full coverage.")
        if rc == 0:
            print(f"\nALL CHECKS PASSED — {p.name} is ready to import")
        return rc
    print(f"FAIL unexpected root <{root.tag}> (expected <CustomBlocks>)")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
