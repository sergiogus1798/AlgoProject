"""PROTO (pending build-confirm): a LONG-ONLY template with TWO INDEPENDENT entry legs.

Two entry conditions on two different signal variables (two RandomCondition holes = two random
groups, "different logic"), each firing its own EnterAtMarket with a DISTINCT MagicNumber and a
DISTINCT ExitAfterBars. Long-only, no other exits ("nothing more"). The two legs run in parallel
and can be open simultaneously (distinct magic + AllowDuplicateTrades=false).

This is the most novel structure in the skill — no single install template proves it. It is
COMPOSED from verified primitives:
  - clean single-condition long-only base    : stop_long_single_skeleton (Signal[RC1] + a pure
                                                variable-consuming IfThen, no embedded cond/cooldown)
  - the EnterAtMarket order Item              : copied from market_skeleton (proven param shape)
  - distinct MagicNumber var per entry rule   : the GridExample1 pattern (int var, id = a UUID,
                                                #MagicNumber# references it), AllowDuplicateTrades=false
MUST be build-confirmed; most likely of all shapes to need a second pass on import.

Output: engine/skeletons/two_entry_market_skeleton.sqx  (bars-exit A=10, B=30 by default).
Usage:  python proto_two_entries.py
"""
import os, copy, zipfile, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKEL = os.path.join(HERE, "skeletons")
BASE = os.path.join(SKEL, "stop_long_single_skeleton.sqx")
MKT = os.path.join(SKEL, "market_skeleton.sqx")
DST = os.path.join(SKEL, "two_entry_market_skeleton.sqx")

LONG_ENTRY = "33333333-1111-1111-3333-333333333333"
ENTRY2 = "33333333-1111-3333-3333-333333333333"     # fresh boolean var for leg B
MAGIC_A = "11111111-aaaa-1111-1111-111111111111"
MAGIC_B = "11111111-bbbb-1111-1111-111111111111"
BARS_A, BARS_B = "10", "30"


def _set_param(item, key, text, drop_generate=False):
    p = next((p for p in item.iter("Param") if p.get("key") == key), None)
    if p is None:
        raise SystemExit(f"param {key} not found on {item.get('key')}")
    p.text = text
    if drop_generate:
        for a in ("generate", "randomValue"):
            p.attrib.pop(a, None)


def _make_variable(vid, name, vtype, value):
    v = ET.Element("variable", {"makeExternal": "false"})
    for tag, val in (("id", vid), ("name", name), ("type", vtype), ("value", value)):
        ET.SubElement(v, tag).text = val
    ET.SubElement(v, "paramType")
    ET.SubElement(v, "makeExternal").text = "false"
    return v


def _market_order():
    z = zipfile.ZipFile(MKT)
    r = ET.fromstring(z.read("strategy_Portfolio.xml"))
    z.close()
    em = next(it for it in r.iter("Item") if it.get("key") == "EnterAtMarket")
    return copy.deepcopy(em)


def _config_order(order, magic, bars, ident):
    _set_param(order, "#Direction#", "1")
    _set_param(order, "#MagicNumber#", magic)
    _set_param(order, "#AllowDuplicateTrades#", "false")
    _set_param(order, "#ExitAfterBars.ExitAfterBars#", bars, drop_generate=True)
    idp = next((p for p in order.findall("Param") if p.get("key") == "#Identification#"), None)
    if idp is not None:
        idp.text = ident


def main():
    z = zipfile.ZipFile(BASE)
    members = {n: z.read(n) for n in z.namelist()}
    z.close()
    root = ET.fromstring(members["strategy_Portfolio.xml"])
    pmap = {c: p for p in root.iter() for c in p}

    # --- variables: add leg-B signal var + two distinct magic-number vars ---
    variables = next(root.iter("Variables"))
    variables.append(_make_variable(ENTRY2, "Entry2Signal", "boolean", "false"))
    variables.append(_make_variable(MAGIC_A, "MagicNumberA", "int", "22222"))
    variables.append(_make_variable(MAGIC_B, "MagicNumberB", "int", "33333"))

    # --- signal rule: keep LongEntry=RC1, add Entry2=RC2 ---
    sig_rule = next(r for r in root.iter("Rule") if r.get("type") == "Signal")
    long_sig = next(s for s in sig_rule.iter("signal") if s.get("variable") == LONG_ENTRY)
    rc1 = next(it for it in long_sig.iter("Item") if it.get("key") == "RandomCondition")
    rc2 = copy.deepcopy(rc1)
    _set_param(rc2, "#Identification#", "RandomCondition2")
    grp = next((p for p in rc2.findall("Param") if p.get("key") == "#Group#"), None)
    if grp is not None:
        grp.text = None
    sig2 = next((s for s in sig_rule.iter("signal") if not list(s)), None)  # reuse an empty slot
    if sig2 is None:
        raise SystemExit("no empty signal slot to reuse for leg B")
    sig2.set("variable", ENTRY2)
    sig2.append(rc2)

    # --- rules: leg A = swap order to market; drop Long exit; add leg B ---
    event = pmap[sig_rule]  # the <Event> holding the rules
    long_entry = next(r for r in root.iter("Rule")
                      if r.get("type") == "IfThen" and r.get("name") == "Long entry")

    # leg A order -> EnterAtMarket
    then_a = long_entry.find("Then")
    assert then_a is not None, "Long entry has no <Then>"
    for it in list(then_a):
        if (it.get("key") or "").startswith("EnterAt"):
            then_a.remove(it)
    order_a = _market_order()
    _config_order(order_a, MAGIC_A, BARS_A, "EnterAtMarket1")
    then_a.append(order_a)
    long_entry.set("name", "Entry A")

    # drop Long exit (exit is via ExitAfterBars only)
    for r in list(root.iter("Rule")):
        if r.get("type") == "IfThen" and r.get("name") == "Long exit":
            pmap[r].remove(r)

    # leg B = clone leg A, repoint the TRUE signal var, own order
    leg_b = copy.deepcopy(long_entry)
    leg_b.set("name", "Entry B")
    iff = leg_b.find("If")
    assert iff is not None, "leg B has no <If>"
    # the first BooleanVariable referencing LONG_ENTRY is the "must be true" trigger -> Entry2
    for it in iff.iter("Item"):
        if it.get("key") == "BooleanVariable":
            vp = next((p for p in it.findall("Param") if p.get("key") == "#Variable#"), None)
            if vp is not None and vp.text == LONG_ENTRY:
                vp.text = ENTRY2
                break
    then_b = leg_b.find("Then")
    assert then_b is not None, "leg B has no <Then>"
    order_b = next(it for it in then_b if (it.get("key") or "").startswith("EnterAt"))
    _config_order(order_b, MAGIC_B, BARS_B, "EnterAtMarket2")
    # insert leg B right after leg A
    idx = list(event).index(long_entry)
    event.insert(idx + 1, leg_b)

    ET.indent(root, space="  ")
    members["strategy_Portfolio.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)
    print("wrote skeleton:", DST)
    print(f"  leg A: RandomCondition1 -> EnterAtMarket magic=MagicNumberA exitbars={BARS_A}")
    print(f"  leg B: RandomCondition2 -> EnterAtMarket magic=MagicNumberB exitbars={BARS_B}")


if __name__ == "__main__":
    main()
