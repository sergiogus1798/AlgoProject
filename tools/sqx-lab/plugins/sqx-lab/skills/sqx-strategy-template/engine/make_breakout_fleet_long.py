"""Derive the 24 LONG-ONLY breakout templates from the build-confirmed two-sided fleet.

This is the OFFLINE / derive-from-proven path (no live install needed): it strips the short mirror
off each already-build-confirmed `out/breakout_fleet/*.sqx` via proto_long_fleet.strip_to_long,
reusing the EXACT groups those templates already carry embedded. (The install-based equivalent is
examples/gen_breakout_fleet_long.py, for when the install is mounted and you want fresh groups.)

Naming: the execution token gets an `L` — Stop->StopL, Mkt->MktL, MTF->MTFL — so the long-only
databanks stay distinct from the two-sided fleet's.

    python make_breakout_fleet_long.py
"""
import os, glob, zipfile, xml.etree.ElementTree as ET
from proto_long_fleet import strip_to_long

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(HERE, "out", "breakout_fleet")
DST_DIR = os.path.join(HERE, "out", "breakout_fleet_long")
TOKEN = {"Stop": "StopL", "Mkt": "MktL", "MTF": "MTFL"}


def long_name(stem):
    base, _, tok = stem.rpartition("_")
    return f"{base}_{TOKEN.get(tok, tok + 'L')}"


def check(path):
    z = zipfile.ZipFile(path)
    bad = [n for n in z.namelist() if z.getinfo(n).file_size and z.read(n) is None]  # zip integrity
    root = ET.fromstring(z.read("strategy_Portfolio.xml"))
    z.close()
    rules = [r.get("name") for r in root.iter("Rule") if r.get("type") == "IfThen"]
    sig = next(r for r in root.iter("Rule") if r.get("type") == "Signal")
    short_filled = any(s.get("variable", "").startswith("33333333-2222-1111") and list(s)
                       for s in sig.iter("signal"))
    long_rcs = sum(1 for s in sig.iter("signal")
                   if s.get("variable", "").startswith("33333333-1111-1111")
                   for it in s.iter("Item") if it.get("key") == "RandomCondition")
    groups = [g.get("name") for g in root.findall(".//RandomGroups/Group")]
    refs = {p.text for p in root.iter("Param") if p.get("key") == "#Group#"}
    emb = {g.get("id") for g in root.findall(".//RandomGroups/Group")}
    ok = (rules == ["Long entry", "Long exit"] and not short_filled
          and long_rcs >= 1 and refs <= emb and not bad)
    return ok, dict(rules=rules, short_filled=short_filled, long_rcs=long_rcs,
                    groups=groups, dangling=sorted(x for x in (refs - emb) if x))


def main():
    os.makedirs(DST_DIR, exist_ok=True)
    srcs = sorted(glob.glob(os.path.join(SRC_DIR, "*.sqx")))
    if not srcs:
        raise SystemExit(f"no source templates in {SRC_DIR}")
    ok_n = bad_n = 0
    for src in srcs:
        stem = os.path.splitext(os.path.basename(src))[0]
        new_stem = long_name(stem)
        dst = os.path.join(DST_DIR, new_stem + ".sqx")
        strip_to_long(src, dst, new_name=new_stem)
        ok, info = check(dst)
        if ok:
            ok_n += 1
            print(f"  OK  {new_stem:28} groups={info['groups']}")
        else:
            bad_n += 1
            print(f"  BAD {new_stem:28} {info}")
    print(f"\n{ok_n} long-only templates written + verified, {bad_n} bad -> {DST_DIR}")


if __name__ == "__main__":
    main()
