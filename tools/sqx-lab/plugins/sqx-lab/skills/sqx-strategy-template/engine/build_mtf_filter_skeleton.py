"""Derive the `mtf_filter` skeleton from the build-confirmed `stop` skeleton.

`mtf_filter` = a MULTI-TIMEFRAME entry: a higher-timeframe (daily) regime FILTER
AND a main-timeframe TRIGGER, entered on a stop at a price level.

    LongEntrySignal  = AND( RandomCondition1[#Chart#=1]  ,  RandomCondition2[#Chart#=0] )
                            ^ daily regime filter            ^ intraday trigger
    ShortEntrySignal = AND( NegatedCondition(RC1)       ,  NegatedCondition(RC2)       )
    Long entry       = EnterAtStop @ RandomValue(price pool)            (unchanged from stop)

WHY this is the right derivation (the lab->product loop, smallest possible delta):
  The `stop` skeleton is BUILD-CONFIRMED. mtf_filter is structurally IDENTICAL to it
  -- same positive AND(filter, trigger), same EnterAtStop + RandomValue price, same
  short mirror, same full exit stack. The ONLY new structure is multi-timeframe data,
  and that exact mechanic is build-proven by the install's own template
  `StrategyTemplates/highest_breakout_template_daily_filter.sqx`, which carries:
    - a 2-stream <Datas> (id=0 Main chart tf=0  +  id=1 'Subchart #1' tf=1440=daily), and
    - a signal RandomCondition wired to the daily subchart via <Param #Chart#>1</Param>.
  So mtf_filter = (confirmed stop structure) + (the install-proven MTF mechanic). The two
  deltas are isolated here:
    (1) append the daily subchart <data id=1> (verbatim shape from the install template), and
    (2) set the LONG RandomCondition1's #Chart# 0 -> 1 (the daily filter hole).
  The SHORT NegatedCondition(RandomCondition1) needs NO change: it mirrors RC1 by
  #Identification# with generate="opposite", so it inherits RC1's daily-chart binding.
  RandomCondition2 (trigger) and the RandomValue stop price stay on #Chart#=0 (the
  trading timeframe). One AlgoWizard import+Build confirms the shape; then the generator
  emits it at scale (it is registered in generate.py SHAPES with the same signature as
  `stop`: 2 condition holes + 1 value group).

Run:  python build_mtf_filter_skeleton.py
Writes engine/skeletons/mtf_filter_skeleton.sqx
"""
import os, zipfile, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
SKEL = os.path.join(HERE, "skeletons")
SRC = os.path.join(SKEL, "stop_skeleton.sqx")
OUT = os.path.join(SKEL, "mtf_filter_skeleton.sqx")

# The daily subchart data stream, copied from the structure proven in the install's
# highest_breakout_template_daily_filter.sqx (<data> id=1, Subchart #1, timeFrame=1440).
SUBCHART = {
    "id": "1",
    "symbol": "Main chart symbol",   # special literal: same symbol as main chart, at the subchart TF
    "chart": "Subchart #1",
    "timeFrame": "1440",             # daily (minutes)
}
DAILY_FILTER_IDENT = "RandomCondition1"   # the hole promoted to the higher timeframe


def _append_subchart(datas):
    d = ET.SubElement(datas, "data")
    for tag in ("id", "symbol", "chart", "timeFrame"):
        ET.SubElement(d, tag).text = SUBCHART[tag]


def build():
    zin = zipfile.ZipFile(SRC)
    members = {n: zin.read(n) for n in zin.namelist()}
    zin.close()
    root = ET.fromstring(members["strategy_Portfolio.xml"])

    # (1) add the daily subchart to <Datas> (skeleton has exactly one stream today)
    datas = root.find(".//Datas")
    assert datas is not None, "stop skeleton missing <Datas>"
    existing_ids = [d.findtext("id") for d in datas.findall("data")]
    assert existing_ids == ["0"], f"expected single main stream id=0, got {existing_ids}"
    _append_subchart(datas)

    # (2) promote the LONG filter hole (RandomCondition1) to the daily subchart: #Chart# 0 -> 1
    sig = next(r for r in root.iter("Rule") if r.get("type") == "Signal")
    signals_el = sig.find("signals")
    assert signals_el is not None, "Signal rule has no <signals>"
    long_signal = signals_el[0]   # first signal var = LongEntrySignal
    promoted = False
    for it in long_signal.iter("Item"):
        if it.get("key") != "RandomCondition":
            continue
        ident = next((p.text for p in it.findall("Param") if p.get("key") == "#Identification#"), None)
        if ident != DAILY_FILTER_IDENT:
            continue
        chart = next((p for p in it.findall("Param") if p.get("key") == "#Chart#"), None)
        assert chart is not None, "RandomCondition1 has no #Chart# param"
        assert chart.text == "0", f"expected RandomCondition1 #Chart#=0, got {chart.text}"
        chart.text = "1"
        promoted = True
        break
    assert promoted, f"did not find {DAILY_FILTER_IDENT} in the long signal var"
    # short-side NegatedCondition(RandomCondition1) inherits chart=1 (mirror by identification) -> no change

    members["strategy_Portfolio.xml"] = ET.tostring(root, encoding="UTF-8", xml_declaration=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)
    print("wrote", OUT)

    # self-check the written skeleton
    rr = ET.fromstring(zipfile.ZipFile(OUT).read("strategy_Portfolio.xml").decode("utf-8", "replace"))
    streams = [(d.findtext("id"), d.findtext("chart"), d.findtext("timeFrame")) for d in rr.findall(".//Datas/data")]
    charts = sorted({p.text for p in rr.iter("Param")
                     if p.get("key") == "#Chart#" and p.text is not None})
    print("  data streams :", streams)
    print("  #Chart# vals :", charts)
    assert len(streams) == 2 and ("1", "Subchart #1", "1440") in streams, "subchart missing"
    assert "1" in charts, "no hole bound to the daily subchart"
    print("  OK -- 2 streams + a daily-bound filter hole")


if __name__ == "__main__":
    build()
