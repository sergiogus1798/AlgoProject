r"""Strip a two-sided skeleton .sqx to SHORT-ONLY.

DERIVED FROM WORKING TEMPLATES, not from the grammar. The reference is the hand-corrected
`gold-templates-short6-FIXED` set (4x stop_short + 2x mtf_filter_short): this transform
reproduces their architecture exactly. Structure verified against them by
evals/run_evals.py.

## Why the obvious approach is wrong

The tempting reading of a two-sided skeleton is "shorts already exist — just delete the
long rules and keep the mirror":

    LONG  signal (generate="random")   -> AND(RandomCondition1, RandomCondition2)
    SHORT signal (generate="opposite") -> AND(NegatedCondition1, NegatedCondition2)

That was this file's original behaviour and it produces templates that do not work. The
mirror resolves each pooled block through its `oppositeBlockKey`, which only exists for
DIRECTIONAL blocks. A session/time filter is non-directional and carries
`oppositeBlockKey="CBlock_null"` — so a NegatedCondition over it has nothing to resolve
to, and any pool containing one silently breaks. (Two of the six reference templates are
session-based, which is how this surfaced.)

## What actually works

Keep the LONG machinery and point it short:

  1. delete the original `Short entry` / `Short exit` rules (the mirror-driven ones),
  2. rename `Long entry` -> `Short entry`, `Long exit` -> `Short exit`,
  3. flip `#Direction#` 1 -> -1 in those renamed rules,
  4. EMPTY the mirror signal (nothing references it any more).

The result fires on the PRIMARY signal — i.e. on the groups the design actually chose.

## Consequence for the design spec (load-bearing)

A short template built this way trades its chosen groups DIRECTLY. So a short design must
name genuinely BEARISH pools ("prior-low breakdown", "trend-down filter"). It is NOT a
long design flipped — nothing mirrors it for you any more. See research_agent.md.

Usage:  python proto_short_fleet.py <in.sqx> <out.sqx> [new_name]
        (or import strip_to_short)
"""
import os, sys, zipfile, xml.etree.ElementTree as ET

# Signal variable IDs are fixed by the skeleton family.
LONG_ENTRY_SIGNAL = "33333333-1111-1111-3333-333333333333"
MIRROR_SIGNAL = "33333333-2222-1111-3333-333333333333"   # generate="opposite"

RENAME = {"Long entry": "Short entry", "Long exit": "Short exit"}
DROP = ("Short entry", "Short exit")


def strip_to_short(src, dst, new_name=None):
    zin = zipfile.ZipFile(src)
    members = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    root = ET.fromstring(members["strategy_Portfolio.xml"])
    parent = {c: p for p in root.iter() for c in p}

    # 1. drop the mirror-driven short rules (must happen BEFORE the rename, or the
    #    names collide and we cannot tell the two pairs apart)
    dropped = []
    for rule in list(root.iter("Rule")):
        if rule.get("type") == "IfThen" and rule.get("name") in DROP:
            parent[rule].remove(rule)
            dropped.append(rule.get("name"))
    if sorted(dropped) != ["Short entry", "Short exit"]:
        raise SystemExit(f"{os.path.basename(src)}: expected Short entry+exit to drop, "
                         f"found {dropped} — is this a two-sided skeleton?")

    # 2 + 3. rename the long rules and flip their direction to short
    renamed, flipped = [], 0
    for rule in root.iter("Rule"):
        new = RENAME.get(rule.get("name") or "")
        if not new:
            continue
        rule.set("name", new)
        renamed.append(new)
        for p in rule.iter("Param"):
            if p.get("key") == "#Direction#":
                p.text = "-1"
                flipped += 1
    if sorted(renamed) != ["Short entry", "Short exit"]:
        raise SystemExit(f"{os.path.basename(src)}: expected Long entry+exit to rename, "
                         f"found {renamed}")
    if not flipped:
        raise SystemExit(f"{os.path.basename(src)}: no #Direction# param found to flip")

    # 4. empty the mirror signal — unreferenced now, and leaving it populated is exactly
    #    the bug this rewrite exists to remove
    emptied = False
    for sig in root.iter("signal"):
        if sig.get("variable") == MIRROR_SIGNAL:
            for child in list(sig):
                sig.remove(child)
            emptied = True
    if not emptied:
        raise SystemExit(f"{os.path.basename(src)}: mirror signal {MIRROR_SIGNAL} not found")

    if new_name:
        sn = root.find(".//StrategyName")
        if sn is not None:
            sn.text = new_name
        st = root.find("Strategy")
        if st is not None:
            st.set("name", new_name)

    ET.indent(root, space="  ")
    members["strategy_Portfolio.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)
    print(f"wrote {os.path.basename(dst):34} "
          f"(dropped {dropped}, renamed->short, {flipped} direction flips, mirror emptied)")


if __name__ == "__main__":
    strip_to_short(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
