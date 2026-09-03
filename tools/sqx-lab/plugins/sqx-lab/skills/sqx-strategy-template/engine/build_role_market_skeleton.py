"""Construct role_market_skeleton.sqx WITHOUT hand-writing novel XML.

New shape: role-structured entry  ==  regime AND trigger AND NOT veto  (3 condition holes),
market execution, short = mirror.  This is the lab->product step: it is built ONLY from
nodes copied out of two skeletons that already build, so the XML idioms are proven; only
the COMPOSITION (3 conditions, one negated) is new and must be build-confirmed.

Provenance of every borrowed idiom:
  - signal-variable architecture + entry/exit rules referencing vars  <- stop_skeleton (CONFIRMED)
  - positive AND of conditions inside the signal var                  <- stop_skeleton (CONFIRMED)
  - EnterAtMarket order item (long: random exits; short: generate=same)<- market_skeleton (via two_entry, CONFIRMED)
  - Not(RandomCondition) / Not(NegatedCondition) the veto idiom        <- market_skeleton

Result: LongEntrySignal  = AND( AND(RC1, RC2), Not(RC3) )       = RC1 AND RC2 AND NOT RC3
        ShortEntrySignal = AND( AND(!RC1, !RC2), Not(!RC3) )    = !RC1 AND !RC2 AND RC3   (mirror)
No bars-guard, no inverted condition. RC1/RC2/RC3 bound by _build via #Identification#.
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


def order_of(root, rule_name):
    rule = next(r for r in root.iter("Rule") if r.get("name") == rule_name)
    then = rule.find("Then")
    return copy.deepcopy(next(it for it in then if it.get("key") == "EnterAtMarket"))


def not_block(root, inner_key):
    """The <Block> holding Item key='Not' that wraps an Item of inner_key (RandomCondition/NegatedCondition)."""
    for it in root.iter("Item"):
        if it.get("key") == "Not":
            inner = it.find("./Block/Item")
            if inner is not None and inner.get("key") == inner_key:
                blk = ET.Element("Block")
                blk.append(copy.deepcopy(it))
                return blk
    raise SystemExit(f"no Not({inner_key}) block in source")


def set_ident(node, ident):
    p = next(p for p in node.iter("Param") if p.get("key") == "#Identification#")
    p.text = ident


stop_members, stop = load("stop_skeleton.sqx")
_, market = load("market_skeleton.sqx")

# --- borrowed nodes -------------------------------------------------------------
mkt_long_order = order_of(market, "Long entry")    # EnterAtMarket, exits generate=random
mkt_short_order = order_of(market, "Short entry")  # EnterAtMarket, exits generate=same
veto_long = not_block(market, "RandomCondition")     # Not( RandomCondition[RC2] )  -> becomes Not(RC3)
veto_short = not_block(market, "NegatedCondition")   # Not( NegatedCondition[RC2] ) -> becomes Not(!RC3)
set_ident(veto_long.find(".//Item[@key='RandomCondition']"), "RandomCondition3")
set_ident(veto_short.find(".//Item[@key='NegatedCondition']"), "RandomCondition3")

# --- rebuild the two entry signal variables ------------------------------------
sig_rule = next(r for r in stop.iter("Rule") if r.get("type") == "Signal")
signals = sig_rule.find("signals")
assert signals is not None, "Signal rule has no <signals>"


def extend_signal(var_id, veto_block):
    assert signals is not None
    sig = signals.find(f"./signal[@variable='{var_id}']")
    assert sig is not None, f"no signal var {var_id}"
    old_and = sig.find("Item")                     # AND( cond1, cond2 ) from stop
    assert old_and is not None, "signal var has no AND item"
    new_and = ET.Element("Item", {"key": "AND"})
    b1 = ET.SubElement(new_and, "Block")
    b1.append(copy.deepcopy(old_and))              # keep AND(cond1, cond2) as the first operand
    new_and.append(veto_block)                     # second operand: the Not(...) block
    sig.remove(old_and)
    sig.append(new_and)


extend_signal(LONG_SIG, veto_long)
extend_signal(SHORT_SIG, veto_short)

# --- swap EnterAtStop -> EnterAtMarket in both entry rules ----------------------
for rname, order in (("Long entry", mkt_long_order), ("Short entry", mkt_short_order)):
    rule = next(r for r in stop.iter("Rule") if r.get("name") == rname)
    then = rule.find("Then")
    assert then is not None, f"{rname} has no <Then>"
    for it in list(then):
        then.remove(it)
    then.append(order)

# --- rename + write -------------------------------------------------------------
sn = stop.find(".//StrategyName")
if sn is not None:
    sn.text = "role_market_skeleton"
st = stop.find("Strategy")
if st is not None:
    st.set("name", "role_market_skeleton")

ET.indent(stop, space=" ")
stop_members["strategy_Portfolio.xml"] = ET.tostring(stop, encoding="UTF-8", xml_declaration=True)
out = os.path.join(SKEL, "role_market_skeleton.sqx")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for n, data in stop_members.items():
        z.writestr(n, data)

# --- report structure -----------------------------------------------------------
rcs = sorted({p.text for it in stop.iter("Item") if it.get("key") == "RandomCondition"
              for p in it.findall("Param") if p.get("key") == "#Identification#" and p.text is not None})
negs = sorted({p.text for it in stop.iter("Item") if it.get("key") == "NegatedCondition"
               for p in it.findall("Param") if p.get("key") == "#Identification#" and p.text is not None})
orders = [it.get("key") for it in stop.iter("Item") if (it.get("key") or "").startswith("EnterAt")]
rvs = [it for it in stop.iter("Item") if it.get("key") == "RandomValue"]
print("wrote", out)
print("  RandomCondition idents (declared, get #Group#):", rcs)
print("  NegatedCondition idents (references):", negs)
print("  order items:", orders)
print("  RandomValue items (should be 0 for market):", len(rvs))
