"""The news filter's tester mode on synthetic releases: the server clock, each firm's list, and the with/without reading."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mt5.newsfilter import cross, gaps, reading, testerfile, windows
from mt5.newsfilter.firms import FIRMS
from mt5.newsfilter.patch import blocks

T = pd.Timestamp


def calendar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """A made-up MT5 history and a made-up Forex Factory one, both in UTC."""
    row = lambda utc, country, cur, code, imp, mode="exact": {   # noqa: E731
        "utc": T(utc), "stamp": T(utc) + pd.Timedelta(hours=3), "country": country, "currency": cur,
        "code": code, "name": code, "importance": imp, "time_mode": mode}
    mt5 = pd.DataFrame([
        row("2025-01-10 13:30", "US", "USD", "nonfarm-payrolls", 3),       # US winter: New York 08:30
        row("2025-03-12 12:30", "US", "USD", "consumer-price-index-yy", 3),  # US summer, Europe still winter
        row("2025-07-03 12:30", "US", "USD", "nonfarm-payrolls", 3),       # summer on both sides
        row("2025-01-08 19:00", "US", "USD", "fomc-minutes", 2),           # FTMO's, MT5 rates it medium
        row("2025-01-09 13:30", "US", "USD", "initial-jobless-claims", 3),  # HIGH, not FTMO's
        row("2025-01-15 00:00", "WW", "ALL", "g20-meeting", 3, "Event takes all day"),    # no minute: 00:00 UTC
        row("2025-01-20 00:00", "US", "USD", "midnight-release", 3),                     # timed, and at 00:00 UTC
        row("2025-02-18 03:30", "AU", "AUD", "rba-interest-rate-decision", 3, "Event takes all day")])  # filed all-day, real time
    ff = pd.DataFrame({"utc": [T("2025-01-10 13:30"), T("2025-01-15 13:30"), T("2025-01-16 13:30")],
                       "currency": ["USD", "USD", "USD"], "impact": ["High", "High", "Medium"],
                       "event": ["Non-Farm Employment Change", "CPI m/m", "Retail Sales m/m"]})
    return mt5, ff


def check_clock() -> None:
    """08:30 New York is 15:30 on an EETUS server all year — also in the weeks only the US has changed hour;
    an all-day event stamped 00:00 UTC has no minute and is not in the file; a timed release at 00:00 UTC
    is, and so is the RBA decision, which MetaQuotes files as all-day with its real time."""
    mt5, ff = calendar()
    hantec = testerfile.releases(FIRMS["hantec"], mt5, ff)
    times = set(hantec["time"])
    for day in ("2025-01-10", "2025-03-12", "2025-07-03"):
        assert T(f"{day} 15:30") in times, (day, sorted(times))
    assert T("2025-03-12 14:30") not in times and T("2025-01-10 16:30") not in times
    assert T("2025-01-15 02:00") not in times and T("2025-01-20 02:00") in times and T("2025-02-18 05:30") in times


def check_firm_lists() -> None:
    """Hantec: every MT5 HIGH plus the red folder, one row where both name the minute. FTMO: its codes only,
    the medium one included, nothing from Forex Factory. The file survives its own round trip."""
    mt5, ff = calendar()
    hantec = testerfile.releases(FIRMS["hantec"], mt5, ff).set_index("time")
    assert len(hantec) == 7 and hantec.loc[T("2025-01-10 15:30"), "source"] == "FF+MT5"
    assert hantec.loc[T("2025-01-15 15:30"), "source"] == "FF" and T("2025-01-16 15:30") not in hantec.index
    assert T("2025-01-08 21:00") not in hantec.index                      # medium: not Hantec's
    ftmo = testerfile.releases(FIRMS["ftmo"], mt5, ff)
    assert sorted(ftmo["time"]) == [T("2025-01-08 21:00"), T("2025-01-10 15:30"), T("2025-02-18 05:30"),
                                    T("2025-03-12 15:30"), T("2025-07-03 15:30")], ftmo
    text = testerfile.text(ftmo)
    assert text.splitlines()[0] == "2025.01.08 21:00;USD;MT5;fomc-minutes" and text.endswith("\r\n")
    tmp = Path(__file__).parent / "_newsfilter_roundtrip.csv"
    tmp.write_bytes(text.encode("ascii"))
    back = testerfile.read(tmp)
    tmp.unlink()
    assert list(back["time"]) == list(ftmo["time"]) and list(back["tag"]) == list(ftmo["tag"])


def check_symbols() -> None:
    """A release counts for a symbol through its name or its country; FTMO leaves JP225 free."""
    rel = pd.DataFrame({"time": [T("2025-01-10 15:30"), T("2025-01-10 16:00"), T("2025-01-10 17:00")],
                        "tag": ["USD", "EUR", "JPY"], "source": "MT5", "title": ["a", "b", "c"]})
    assert list(windows.for_symbol(rel, "XAUUSD", FIRMS["hantec"])["tag"]) == ["USD"]
    assert list(windows.for_symbol(rel, "GER40.cash", FIRMS["hantec"])["tag"]) == ["EUR"]
    assert list(windows.for_symbol(rel, "JP225", FIRMS["hantec"])["tag"]) == ["JPY"]
    assert windows.for_symbol(rel, "JP225", FIRMS["ftmo"]).empty


def check_reading() -> None:
    """One release at 15:30, Hantec (close from 15:25, no entry 15:25-15:35, firm's window 15:27-15:33).

    Unfiltered run: A open across it (+100), B entered at 15:26 (-40), C two days earlier (-10), D closed
    at 15:24:59 (+5): net 55. Filtered run, by construction: A closed at 15:25:20 (+30), B absent, C and D
    the same, E a new entry at 15:36 (+7): net 32. So 2 igual, 1 cerrada antes (-70), 1 no abierta (+40),
    1 nueva por arrastre (+7), and the worst day is the 8th (-10) in both.
    """
    firm = FIRMS["hantec"]
    rel = pd.DataFrame({"time": [T("2025-01-10 15:30")], "tag": ["USD"], "source": ["MT5"], "title": ["NFP"]})
    trade = lambda side, o, c, pl: {"Type": side, "Open time": T(o), "Open price": 1.0, "Size": 0.1,   # noqa: E731
                                    "Close time": T(c), "Close price": 1.0, "Profit/Loss": pl}
    plain = pd.DataFrame([trade("Buy", "2025-01-10 10:00", "2025-01-10 16:00", 100.0),
                          trade("Sell", "2025-01-10 15:26", "2025-01-10 17:00", -40.0),
                          trade("Buy", "2025-01-08 09:00", "2025-01-08 12:00", -10.0),
                          trade("Buy", "2025-01-09 09:00", "2025-01-10 15:24:59", 5.0)])
    filtered = pd.DataFrame([trade("Buy", "2025-01-10 10:00", "2025-01-10 15:25:20", 30.0),
                             trade("Buy", "2025-01-08 09:00", "2025-01-08 12:00", -10.0),
                             trade("Buy", "2025-01-09 09:00", "2025-01-10 15:24:59", 5.0),
                             trade("Sell", "2025-01-10 15:36", "2025-01-10 18:00", 7.0)])
    told = windows.expected(plain, rel, firm)
    assert list(told["fate"]) == ["cut", "blocked", "kept", "kept"], list(told["fate"])
    assert told["cut_at"].iloc[0] == T("2025-01-10 15:25") and told["release"].iloc[1] == T("2025-01-10 15:30")
    got = reading.compare(plain, filtered, rel, firm)
    s = got["summary"]
    assert {f: v["trades"] for f, v in s["by_fate"].items()} == {
        "igual": 2, "cerrada antes": 1, "no abierta": 1, "cambia por arrastre": 0, "nueva por arrastre": 1}, s
    assert s["by_fate"]["cerrada antes"]["pl_change"] == -70.0 and s["by_fate"]["no abierta"]["pl_change"] == 40.0
    assert s["by_fate"]["nueva por arrastre"]["pl_change"] == 7.0 and s["by_fate"]["igual"]["pl_change"] == 0.0
    assert s["net"] == [55.0, 32.0] and s["net_change"] == -23.0 and s["trades"] == [4, 4]
    assert s["worst_day"] == [{"day": "2025-01-08", "pl": -10.0}, {"day": "2025-01-08", "pl": -10.0}]
    assert s["releases_in_span"] == 1 and got["violations"].empty, got["violations"]
    # the unfiltered run does break the rule, and exactly where it was built to
    broke = windows.violations(plain, rel, firm)
    assert sorted(zip(broke["Open time"], broke["breach"])) == [
        (T("2025-01-10 10:00"), "open across the release"), (T("2025-01-10 15:26"), "entry in block window"),
        (T("2025-01-10 15:26"), "open across the release")], broke
    # a close inside the firm's own window is a breach of its own
    hit = pd.DataFrame([trade("Buy", "2025-01-10 15:00", "2025-01-10 15:28", 1.0)])
    assert list(windows.violations(hit, rel, firm)["breach"]) == ["close in the firm's window"]


def check_gaps() -> None:
    """The EA's "thin history" lines of its LAST run become stretches (a weekend does not split one), another
    EA's lines and an earlier run's are ignored, and a trade open at any moment inside a stretch is left out."""
    line = lambda ea, sim, msg: f"CS\t0\t14:23:37.038\t{ea} (USDJPY,H1)\t{sim}   {msg}"   # noqa: E731
    thin = lambda day: f"News filter (tester): thin history {day} 96 ticks"                 # noqa: E731
    text = "\n".join([
        line("S_Hantec", "2022.06.01 00:07:30", "News filter (tester): 8974 releases that move USDJPY read from x.csv, a to b"),
        line("S_Hantec", "2023.01.03 00:00:00", thin("2023.01.02")),                         # an earlier run
        line("S_Hantec", "2022.06.01 00:07:30", "News filter (tester): 8974 releases that move USDJPY read from x.csv, a to b"),
        line("S_Hantec", "2022.06.03 16:40:00", "News filter: closing positions and pending orders before 'PMI' (USD) at 2022.06.03 16:45"),
        line("S_Hantec", "2023.09.21 00:00:00", thin("2023.09.20")), line("Other_Hantec", "2023.09.21 00:00:00", thin("2023.03.01")),
        line("S_Hantec", "2023.09.22 00:00:00", thin("2023.09.21")), line("S_Hantec", "2023.09.25 00:00:00", thin("2023.09.22")),
        line("S_Hantec", "2023.09.26 00:00:00", thin("2023.09.25")), line("S_Hantec", "2023.11.13 00:00:00", thin("2023.11.10"))])
    got = gaps.stretches(gaps.thin_days(text, "S_Hantec"))
    assert list(zip(got["start"], got["end"], got["days"])) == [
        (T("2023-09-20"), T("2023-09-26"), 4), (T("2023-11-10"), T("2023-11-11"), 1)], got
    trades = pd.DataFrame({"Open time": [T("2023-09-19 10:00"), T("2023-09-22 10:00"), T("2023-09-26 00:00"), T("2023-11-10 08:00")],
                           "Close time": [T("2023-09-20 03:00"), T("2023-09-22 19:00"), T("2023-09-26 09:00"), T("2023-11-10 17:00")]})
    kept, counts = gaps.outside(trades, got)
    assert counts == [2, 1] and list(kept["Open time"]) == [T("2023-09-26 00:00")], (counts, kept)
    assert gaps.stretches([]).empty and len(gaps.outside(trades, gaps.stretches([]))[0]) == 4


def check_cross() -> None:
    """The cross names each disagreement: same minute, rated lower, a few minutes apart, an hour apart, alone."""
    mine = pd.DataFrame({"currency": "USD", "utc": [T("2025-01-10 13:30"), T("2025-01-11 13:30"), T("2025-01-12 13:30"),
                                                    T("2025-01-13 13:30"), T("2025-01-14 13:30")]})
    high = pd.DataFrame({"currency": "USD", "utc": [T("2025-01-10 13:30"), T("2025-01-12 13:40"), T("2025-01-13 12:30")]})
    anyrank = pd.concat([high, pd.DataFrame({"currency": "USD", "utc": [T("2025-01-11 13:30")]})])
    assert list(cross.classify(mine, high, anyrank)) == cross.CLASSES


def check_template() -> None:
    """The EA reads the firm's file in the tester and nothing else changes live: the tester no longer
    returns early, the live path still refreshes its calendars, and an empty file name switches it off."""
    for _key, firm in FIRMS.items():
        inputs, helpers = ("\n".join(b) for b in blocks(firm))
        assert f'NewsTesterFile         = "AlgoProjectNews_{firm["label"]}.csv";' in inputs
        assert "MQLInfoInteger(MQL_TESTER)) return false" not in helpers
        assert 'if(!EnableNewsFilter || (tester && NewsTesterFile == "")) return false;' in helpers
        assert "if(!tester) newsRefresh();" in helpers and "FILE_COMMON" in helpers
        assert "% 86400 == 0) continue;" in helpers and "CALENDAR_TIMEMODE_DATE" in helpers and "thin history" in helpers
        assert "datetime now = tester ? TimeCurrent() : TimeTradeServer();" in helpers
        assert testerfile.name(firm) == f"AlgoProjectNews_{firm['label']}.csv"


if __name__ == "__main__":
    check_clock()
    check_firm_lists()
    check_symbols()
    check_reading()
    check_gaps()
    check_cross()
    check_template()
    print("ok")
