"""PROTO (pending build-confirm): derive a LONG-ONLY, SINGLE-condition STOP skeleton.

From the build-confirmed `stop_skeleton.sqx` (= breakouTTemplate, long+short, 2-cond, EnterAtStop
with the stop price coming from a Value random group). We make two safe edits — only whole-rule
removal + a localized signal edit, never the deep IfThen condition tree:

  1. LONG-ONLY  — delete the `Short entry` + `Short exit` IfThen rules and empty the ShortEntry
                  signal. (The short signal var still exists/false, so the Long entry's
                  `Not(ShortEntrySignal)` gate stays valid.)
  2. SINGLE-COND — in the LongEntry signal, replace `AND(RandomCondition1, RandomCondition2)` with
                  just `RandomCondition1` (proven valid: TrendUP_CC has a lone RandomCondition in
                  its signal).

Result = one breakout Condition group (trigger) -> EnterAtStop, with the stop price sampled from a
Value group. Output: engine/skeletons/stop_long_single_skeleton.sqx.

Usage:  python proto_long_stop.py
"""
import os, zipfile, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKEL = os.path.join(HERE, "skeletons")
SRC = os.path.join(SKEL, "stop_skeleton.sqx")
DST = os.path.join(SKEL, "stop_long_single_skeleton.sqx")

LONG_ENTRY = "33333333-1111-1111-3333-333333333333"
SHORT_ENTRY = "33333333-2222-1111-3333-333333333333"


def main():
    zin = zipfile.ZipFile(SRC)
    members = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    root = ET.fromstring(members["strategy_Portfolio.xml"])
    parent = {c: p for p in root.iter() for c in p}

    # 1) remove Short entry + Short exit IfThen rules
    removed = []
    for rule in list(root.iter("Rule")):
        if rule.get("type") == "IfThen" and rule.get("name") in ("Short entry", "Short exit"):
            parent[rule].remove(rule)
            removed.append(rule.get("name"))
    if sorted(removed) != ["Short entry", "Short exit"]:
        raise SystemExit(f"expected to remove Short entry+exit, removed {removed}")

    # 2) signal edits
    sig_rule = next((r for r in root.iter("Rule") if r.get("type") == "Signal"), None)
    if sig_rule is None:
        raise SystemExit("no Signal rule")
    long_done = short_done = False
    for sig in sig_rule.iter("signal"):
        var = sig.get("variable")
        if var == SHORT_ENTRY:
            for c in list(sig):
                sig.remove(c)
            short_done = True
        elif var == LONG_ENTRY:
            # find RandomCondition1 anywhere under this signal, promote it to the signal's only child
            rc1 = None
            for it in sig.iter("Item"):
                if it.get("key") == "RandomCondition":
                    ident = next((p.text for p in it.findall("Param") if p.get("key") == "#Identification#"), "")
                    if ident == "RandomCondition1":
                        rc1 = it
                        break
            if rc1 is None:
                raise SystemExit("RandomCondition1 not found in LongEntry signal")
            for c in list(sig):
                sig.remove(c)
            sig.append(rc1)
            long_done = True
    if not (long_done and short_done):
        raise SystemExit(f"signal edits incomplete long={long_done} short={short_done}")

    ET.indent(root, space="  ")
    members["strategy_Portfolio.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)
    print("wrote skeleton:", DST)
    print("removed rules:", removed)


if __name__ == "__main__":
    main()
