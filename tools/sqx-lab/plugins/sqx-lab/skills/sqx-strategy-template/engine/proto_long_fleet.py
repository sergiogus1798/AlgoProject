"""PROTO (pending build-confirm): derive LONG-ONLY variants of the two-sided fleet skeletons.

The `stop` / `market` / `mtf_filter` skeletons are all two-sided: their Signal rule carries a
LongEntry signal AND a mirrored ShortEntry signal (NegatedCondition / OppositeValue), plus Long
and Short entry/exit IfThen rules. This deriver produces a LONG-ONLY twin of each by the SAME safe
strip-short move proven in `proto_long_stop.py` — only whole-rule removal + emptying the short
signal, never touching the deep IfThen condition tree or the long side:

  1. delete the `Short entry` + `Short exit` IfThen rules
  2. empty the ShortEntry signal (the short var STAYS, present-but-false, so the Long entry's
     Not(ShortEntrySignal) gate remains valid)

Unlike proto_long_stop (which also reduced AND(RC1,RC2) -> RC1), we KEEP both conditions, so the
long-only twin has the exact same filter+trigger (+value) signature as its two-sided parent.

  stop_skeleton.sqx        -> stop_long_skeleton.sqx          (filter + trigger + value stop price)
  market_skeleton.sqx      -> market_long_skeleton.sqx        (filter + trigger, market fill)
  mtf_filter_skeleton.sqx  -> mtf_filter_long_skeleton.sqx    (daily filter + trigger + value stop)

Usage:  python proto_long_fleet.py
"""
import os, zipfile, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKEL = os.path.join(HERE, "skeletons")

SHORT_ENTRY_VAR = "33333333-2222-1111-3333-333333333333"

PAIRS = [
    ("stop_skeleton.sqx",        "stop_long_skeleton.sqx"),
    ("market_skeleton.sqx",      "market_long_skeleton.sqx"),
    ("mtf_filter_skeleton.sqx",  "mtf_filter_long_skeleton.sqx"),
]


def strip_to_long(src, dst, new_name=None):
    """Strip the short mirror from a two-sided .sqx (skeleton OR generated template).

    Works on any .sqx sharing the fleet signal structure (LongEntry/ShortEntry signals + Long/Short
    entry/exit rules). Removes the Short entry+exit rules and empties the ShortEntry signal; leaves
    the long side, all variables, and any embedded <RandomGroups> untouched. If new_name is given,
    also renames the strategy (StrategyName + Strategy@name)."""
    zin = zipfile.ZipFile(src)
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
        raise SystemExit(f"{os.path.basename(src)}: expected Short entry+exit, removed {removed}")

    # 2) empty the ShortEntry signal (leave the var declared, false)
    sig_rule = next((r for r in root.iter("Rule") if r.get("type") == "Signal"), None)
    if sig_rule is None:
        raise SystemExit(f"{os.path.basename(src)}: no Signal rule")
    short_done = False
    for sig in sig_rule.iter("signal"):
        if sig.get("variable") == SHORT_ENTRY_VAR:
            for c in list(sig):
                sig.remove(c)
            short_done = True
    if not short_done:
        raise SystemExit(f"{os.path.basename(src)}: ShortEntry signal not found")

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
    print(f"wrote {os.path.basename(dst):32} (removed {removed})")


def main():
    for src, dst in PAIRS:
        strip_to_long(os.path.join(SKEL, src), os.path.join(SKEL, dst))


if __name__ == "__main__":
    main()
