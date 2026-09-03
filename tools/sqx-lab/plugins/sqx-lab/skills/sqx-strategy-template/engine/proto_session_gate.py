"""PROTO (pending build-confirm): derive a session-gated skeleton from the proven market skeleton.

New region of the design space = axis B "time/session gate". Derived from the install's OWN
proven template `highest_breakout_template_daily_filter.sqx`, whose LongEntry signal is
exactly `AND(RandomCondition, BarDayOfWeekIsNot)`. We replicate that: wrap each ENTRY signal's
condition in `AND(condition, <time gate>)`. The gate is a native `simpleRules` atom (no group,
no CBlock) so it survives group-binding untouched, and it is NON-DIRECTIONAL so long & short get
the identical gate (no mirror needed).

We touch ONLY the Signal rule's two entry signals — the deep IfThen wiring (cooldown via
BarsSinceOrderClosed, the signal-variable protocol, the short mirror) is left exactly as the
build-confirmed skeleton has it.

Output: engine/skeletons/session_market_skeleton.sqx  (a new skeleton, gate = "not Friday").
Once you import + BUILD-CONFIRM a template made from it, fold `session_market` into generate.py
SHAPES and parameterize the gate (hour / day / session).

Usage:  python proto_session_gate.py
"""
import os, zipfile, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKEL = os.path.join(HERE, "skeletons")
SRC = os.path.join(SKEL, "market_skeleton.sqx")
DST = os.path.join(SKEL, "session_market_skeleton.sqx")

LONG_ENTRY = "33333333-1111-1111-3333-333333333333"
SHORT_ENTRY = "33333333-2222-1111-3333-333333333333"


def _gate_item():
    """A fresh BarDayOfWeekIsNot atom, byte-faithful to the proven daily-filter template
    (Day=5 => 'not Friday', evaluated on the main chart, shift 1)."""
    it = ET.Element("Item", {
        "customSnippet": "false", "key": "BarDayOfWeekIsNot",
        "name": "Bar Day Of Week Is Not",
        "display": "Bar[#Shift#] day of week != #Day#",
        "returnType": "boolean", "mI": "BarAndTime",
        "categoryType": "simpleRules",
        "openingBrackets": "0", "closingBrackets": "0",
    })
    p1 = ET.SubElement(it, "Param", {
        "key": "#Chart#", "name": "Chart", "type": "data",
        "controlType": "dataVar", "defaultValue": "0"})
    p1.text = "0"
    p2 = ET.SubElement(it, "Param", {
        "key": "#Day#", "name": "Day", "type": "int", "defaultValue": "0",
        "controlType": "combo",
        "values": "Sunday=0,Monday=1,Tuesday=2,Wednesday=3,Thursday=4,Friday=5,Saturday=6",
        "builderStep": "1"})
    p2.text = "5"
    p3 = ET.SubElement(it, "Param", {
        "key": "#Shift#", "name": "Shift", "type": "int", "defaultValue": "1",
        "controlType": "jspinnerVar", "minValue": "0", "maxValue": "1000",
        "genMinValue": "-1000001", "genMaxValue": "-1000002",
        "paramType": "shift", "step": "1", "builderStep": "1", "value": "1"})
    p3.text = "1"
    return it


def main():
    zin = zipfile.ZipFile(SRC)
    members = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    root = ET.fromstring(members["strategy_Portfolio.xml"])

    sig_rule = next((r for r in root.iter("Rule") if r.get("type") == "Signal"), None)
    if sig_rule is None:
        raise SystemExit("no Signal rule in skeleton")

    gated = []
    for sig in sig_rule.iter("signal"):
        if sig.get("variable") not in (LONG_ENTRY, SHORT_ENTRY):
            continue
        cond = list(sig)  # the signal's current condition Item(s)
        if not cond:
            continue
        # wrap: AND( <existing cond>, <gate> )
        and_it = ET.Element("Item", {"key": "AND"})
        b1 = ET.SubElement(and_it, "Block")
        for c in cond:
            b1.append(c)
            sig.remove(c)
        b2 = ET.SubElement(and_it, "Block")
        b2.append(_gate_item())
        sig.append(and_it)
        gated.append(sig.get("variable"))

    if len(gated) != 2:
        raise SystemExit(f"expected to gate 2 entry signals, gated {gated}")

    ET.indent(root, space="  ")
    members["strategy_Portfolio.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)
    print("wrote skeleton:", DST)
    print("gated entry signals:", gated)


if __name__ == "__main__":
    main()
