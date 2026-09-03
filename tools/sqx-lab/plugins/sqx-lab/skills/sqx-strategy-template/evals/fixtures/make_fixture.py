"""Generate the committed eval fixture: a minimal synthetic SQX install.

The template generator only ever reads two files from an install:
    user/settings/blockGroups.xml     (_install_groups)
    user/settings/customBlocks.xml    (_avail)
so a fixture is just those two, and the structure harness can then run on ANY machine
instead of SKIPping wherever the user hasn't populated their real install yet.

Coverage the fixture is built to give:
    3 clean inline Condition groups  -> filter + trigger + veto (role_market needs 3)
    1 clean inline Value group       -> the stop/limit price pool (stop* / mtf_filter*)
    1 clean HYBRID Condition group   -> exercises the CBlock_* resolution path
    1 BROKEN group                   -> exercises exclusion + the repair_manifest path

Run once; the emitted XML is committed as static test data.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path(sys.argv[1])          # the validated 3-group ShortKit XML
OUT = Path(sys.argv[2])          # …/evals/fixtures/install

HEADER = ("\n<!-- GENERATED TEST FIXTURE — not a real install. Synthetic groups over stock\n"
          "     indicator rules, used by evals/run_evals.py so the structure harness runs\n"
          "     on any machine. Do not point SQX at this. -->\n")


def main():
    groups = list(ET.fromstring(SRC.read_text(encoding="utf-8")).iter("Group"))
    by_type = {"Condition": [], "Value": []}
    for g in groups:
        by_type.get(g.get("type"), []).append(g)

    cond, val = by_type["Condition"], by_type["Value"]
    if len(cond) < 2 or not val:
        raise SystemExit(f"need >=2 Condition and >=1 Value in {SRC}")

    out = ET.Element("Groups")
    names = ["FixtureFilter", "FixtureTrigger", "FixtureVeto"]
    # 3 clean inline Condition groups — reuse the two real pools, then split the larger
    # one so the third is still genuinely distinct (role_market needs 3 DISTINCT groups).
    picks = [cond[0], cond[1], cond[0]]
    for i, (nm, src) in enumerate(zip(names, picks)):
        g = ET.fromstring(ET.tostring(src))
        g.set("name", nm)
        g.set("id", f"f1x7u4e0-0000-4000-8000-00000000000{i}")
        g.set("category", "Fixtures")
        if i == 2:                                  # make the veto pool differ from filter
            for extra in list(g)[1:]:
                g.remove(extra)
        out.append(g)

    gv = ET.fromstring(ET.tostring(val[0]))
    gv.set("name", "FixtureLevels")
    gv.set("id", "f1x7u4e0-0000-4000-8000-00000000000v")
    gv.set("category", "Fixtures")
    out.append(gv)

    # HYBRID group -> its CBlock_* exists in customBlocks.xml below (stays CLEAN)
    hyb = ET.Element("Group", {"id": "f1x7u4e0-0000-4000-8000-0000000000h0",
                               "name": "FixtureHybrid", "type": "Condition",
                               "strategyType": "Standard", "category": "Fixtures",
                               "status": "0", "action": "add"})
    ET.SubElement(hyb, "Item", {"key": "CBlock_FixtureSignal", "name": "FixtureSignal",
                                "display": "Close > HighD[1]", "returnType": "boolean",
                                "type": "Condition", "category": "Fixtures",
                                "oppositeBlockKey": "CBlock_null", "customSnippet": "false"})
    out.append(hyb)

    # BROKEN group -> references a CBlock that is deliberately absent
    brk = ET.Element("Group", {"id": "f1x7u4e0-0000-4000-8000-0000000000b0",
                               "name": "FixtureBroken", "type": "Condition",
                               "strategyType": "Standard", "category": "Fixtures",
                               "status": "0", "action": "add"})
    ET.SubElement(brk, "Item", {"key": "CBlock_FixtureMissing", "name": "FixtureMissing",
                                "display": "Close < LowD[1]", "returnType": "boolean",
                                "type": "Condition", "category": "Fixtures",
                                "oppositeBlockKey": "CBlock_null", "customSnippet": "false"})
    out.append(brk)

    cb = ET.Element("CustomBlocks")
    ET.SubElement(cb, "Item", {"key": "CBlock_FixtureSignal", "name": "FixtureSignal",
                               "display": "Close > HighD[1]", "returnType": "boolean",
                               "type": "Condition", "category": "Fixtures",
                               "oppositeBlockKey": "CBlock_null", "categoryType": "customBlock"})

    d = OUT / "user" / "settings"
    d.mkdir(parents=True, exist_ok=True)
    for root, fn in ((out, "blockGroups.xml"), (cb, "customBlocks.xml")):
        ET.indent(root, space="  ")
        body = ET.tostring(root, encoding="unicode")
        (d / fn).write_text(HEADER.lstrip("\n") + body + "\n", encoding="utf-8")
        print(f"wrote {d / fn}")

    # config.xml is the install IDENTITY marker (sqx_common.validate_install). The template
    # generator never parses it, but shipping a stub means the fixture is a genuine minimal
    # install and the harness exercises the real validation path instead of bypassing it.
    cfg = OUT / "internal" / "web" / "SQWIZARD" / "branding" / "global"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "config.xml").write_text(
        HEADER.lstrip("\n") + "<Config><Items /></Config>\n", encoding="utf-8")
    print(f"wrote {cfg / 'config.xml'}")

    print(f"\ngroups: {[g.get('name') for g in out]}")


if __name__ == "__main__":
    main()
