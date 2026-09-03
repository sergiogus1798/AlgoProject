"""Rebuild market_skeleton.sqx + session_market_skeleton.sqx on the CLEAN `stop` architecture.

WHY: the old market_skeleton was cloned from the install example "3TrendUPBBNotAdvanced" — a
deliberately negated, re-entry-GUARDED strategy. Its entry IfThen carried a `BarsSinceOrderClosed(...)
< N` guard AND shoved the second condition (the trigger) INTO the entry rule (often negated). Result:
the strategy barely trades. session_market was derived from that poisoned base, so it inherited the
same disease (observed: `SessionBreakout` made no trades). The shapes that work — `stop`, `role_market`,
`mtf_filter` — all put the trigger in the SIGNAL var and keep the entry rule as a clean
"if signal and flat -> enter", with NO bars-guard.

FIX (same lab->product graft `build_role_market_skeleton.py` uses): take the CONFIRMED `stop` skeleton
(clean signal var `AND(RC1, RC2)`, clean entry rules) and borrow ONLY the `EnterAtMarket` order ITEM
from the old market skeleton (the order item itself is clean — the bug lived in the entry-rule If).

  market:         LongEntrySignal = AND(RC1, RC2)                      -> EnterAtMarket
  session_market: LongEntrySignal = AND( AND(RC1, RC2), BarDayOfWeekIsNot )  -> EnterAtMarket
                  (the time gate is non-directional: SAME on long and short, NOT negated)

Short mirrors via NegatedCondition exactly as in stop. No BarsSinceOrderClosed, no trigger-in-entry-rule,
no inversion. RC1/RC2 are bound by generate._build via #Identification#.

Run:  python build_market_skeletons.py
"""
import copy, os, zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKEL = os.path.join(HERE, "skeletons")
LONG_SIG = "33333333-1111-1111-3333-333333333333"
SHORT_SIG = "33333333-2222-1111-3333-333333333333"


def load(name):
    z = zipfile.ZipFile(os.path.join(SKEL, name))
    members = {n: z.read(n) for n in z.namelist()}
    z.close()
    return members, ET.fromstring(members["strategy_Portfolio.xml"])


def market_order(root, rule_name):
    """The clean EnterAtMarket order ITEM from a rule's <Then> (just the order, not the buggy If)."""
    rule = next(r for r in root.iter("Rule") if r.get("name") == rule_name)
    then = rule.find("Then")
    assert then is not None, f"{rule_name} has no <Then>"
    return copy.deepcopy(next(it for it in then if it.get("key") == "EnterAtMarket"))


def gate_block(root):
    """The <Block> wrapping the BarDayOfWeekIsNot time-gate atom (non-directional)."""
    for it in root.iter("Item"):
        if it.get("key") == "BarDayOfWeekIsNot":
            blk = ET.Element("Block")
            blk.append(copy.deepcopy(it))
            return blk
    raise SystemExit("no BarDayOfWeekIsNot atom in source")


def swap_orders_to_market(root, long_order, short_order):
    for rname, order in (("Long entry", long_order), ("Short entry", short_order)):
        rule = next(r for r in root.iter("Rule") if r.get("name") == rname)
        then = rule.find("Then")
        assert then is not None, f"{rname} has no <Then>"
        for it in list(then):
            then.remove(it)
        then.append(copy.deepcopy(order))


def add_gate(root, gate):
    """Wrap each entry signal's AND(RC1,RC2) into AND( AND(RC1,RC2), gate ) — gate same on both sides."""
    sig_rule = next(r for r in root.iter("Rule") if r.get("type") == "Signal")
    signals = sig_rule.find("signals")
    assert signals is not None
    for var_id in (LONG_SIG, SHORT_SIG):
        sig = signals.find(f"./signal[@variable='{var_id}']")
        assert sig is not None, f"no signal var {var_id}"
        old_and = sig.find("Item")
        assert old_and is not None, "signal var has no AND item"
        new_and = ET.Element("Item", {"key": "AND"})
        b1 = ET.SubElement(new_and, "Block")
        b1.append(copy.deepcopy(old_and))            # keep AND(RC1, RC2)
        new_and.append(copy.deepcopy(gate))          # + the time gate (positive, non-directional)
        sig.remove(old_and)
        sig.append(new_and)


def write(members, root, name):
    ET.indent(root, space="  ")
    members["strategy_Portfolio.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    out = os.path.join(SKEL, name)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)
    return out


def audit(name):
    r = ET.fromstring(zipfile.ZipFile(os.path.join(SKEL, name)).read("strategy_Portfolio.xml").decode("utf-8", "replace"))
    xml = zipfile.ZipFile(os.path.join(SKEL, name)).read("strategy_Portfolio.xml").decode("utf-8", "replace")
    sig = next(rr for rr in r.iter("Rule") if rr.get("type") == "Signal")
    long_sig = sig.find("signals")[0]  # type: ignore[index]
    rc_in_sig = [it.get("key") for it in long_sig.iter("Item") if it.get("key") in ("RandomCondition", "BarDayOfWeekIsNot")]
    entry = next(rr for rr in r.iter("Rule") if rr.get("type") == "IfThen" and rr.get("name") == "Long entry")
    iff = entry.find("If")
    rc_in_entry = [it.get("key") for it in iff.iter("Item") if it.get("key") == "RandomCondition"] if iff is not None else []
    print(f"  {name}: signal-var holes={rc_in_sig}  RandomCondition-in-entry-If={rc_in_entry}  "
          f"BarsSinceOrderClosed={'YES(BAD)' if 'BarsSinceOrderClosed' in xml else 'no'}")
    assert not rc_in_entry, "trigger leaked into the entry rule!"
    assert "BarsSinceOrderClosed" not in xml, "re-entry guard present!"


# grab the time-gate block from the OLD session skeleton BEFORE overwriting it
_, old_session = load("session_market_skeleton.sqx")
GATE = gate_block(old_session)

# clean EnterAtMarket order items (the ITEM is clean; only the old entry-If was buggy)
_, old_market = load("market_skeleton.sqx")
mkt_long = market_order(old_market, "Long entry")
mkt_short = market_order(old_market, "Short entry")

# --- clean market = stop signal var + EnterAtMarket -----------------------------
stop_members, stop = load("stop_skeleton.sqx")
swap_orders_to_market(stop, mkt_long, mkt_short)
write(stop_members, stop, "market_skeleton.sqx")

# --- clean session_market = clean market + the time gate ------------------------
sess_members, sess = load("market_skeleton.sqx")
add_gate(sess, GATE)
write(sess_members, sess, "session_market_skeleton.sqx")

print("rebuilt clean skeletons:")
audit("market_skeleton.sqx")
audit("session_market_skeleton.sqx")
