#!/usr/bin/env python3
"""MetaTracker's stage progress on the firm's clock, the payout, the EA comparison, the strategy record and the cross-account pairing."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mt5.fleet.app import eas, floors, health, progress, strategies

GMT = 1790979700            # 2026-10-02 22:21:40 UTC
OFF = 10800
PRAGUE = GMT - 1300         # UTC epoch of Prague's midnight (22:00 UTC)
DAY = 86400
BEAT = {"written_gmt": GMT, "server_time": GMT + OFF, "balance": 10600.0, "deposit_time": 0}
CHALLENGE = {"size": 10000.0, "target": 0.10, "min_days": 3, "min_days_kind": "trading", "profitable_pct": None,
             "consistency": 0.0, "consistency_kind": None}
HANTEC = {**CHALLENGE, "min_days_kind": "profitable", "profitable_pct": 0.005, "consistency": 0.35,
          "consistency_kind": "best_over_total"}
FUNDED = {**CHALLENGE, "target": 0.0}


def deal(server_utc: int, net: float, typ: int = 0, entry: int = 1, pos: int = 1, magic: int = 7, comment: str = "Strategy_3_23_151",
         side_buy: bool = True) -> dict:
    """A deal at a UTC instant (stored on the server's clock) worth `net` with no costs."""
    return {"time": server_utc + OFF, "type": typ, "entry": entry, "position": pos, "profit": net, "swap": 0.0,
            "commission": 0.0, "fee": 0.0, "symbol": "" if typ == 2 else "EURUSD", "magic": magic, "comment": comment,
            "volume": 1.0}


def trade(open_utc: int, hold: int, net: float, pos: int, side: str = "buy", magic: int = 7) -> list[dict]:
    """An entry deal and an exit deal."""
    t = 0 if side == "buy" else 1
    return [deal(open_utc, 0.0, t, 0, pos, magic), deal(open_utc + hold, net, 1 - t, 1, pos, magic)]


def check_days() -> None:
    """A day is the firm's: a deal one minute either side of Prague's midnight lands on two days."""
    rows = [*trade(PRAGUE - 3600, 1800, 100.0, 1), *trade(PRAGUE + 60, 60, 80.0, 2), deal(PRAGUE - DAY * 3, 5000.0, 2, 0, 0)]
    days = progress.by_day(rows, OFF, "Europe/Prague")
    assert days == {PRAGUE - DAY: 100.0, PRAGUE: 80.0}                              # the deposit is no trading day
    assert progress.by_day([deal(GMT - 60, 10.0)], OFF, None) == {(GMT + OFF - 60) // DAY * DAY - OFF: 10.0}
    # The server's own midnight is an hour before Prague's: 23:30 UTC-1h... a deal at 21:30 UTC is yesterday for the server only.
    late = deal(PRAGUE - 1800, 1.0)
    assert progress.day_of(late["time"], OFF, "Europe/Prague") == PRAGUE - DAY
    assert progress.day_of(late["time"], OFF, None) == (PRAGUE - 1800 + OFF) // DAY * DAY - OFF


def check_progress() -> None:
    """Profit against the target, trading and profitable days, and the consistency ratio."""
    rows = [deal(PRAGUE - 5 * DAY, 10000.0, 2, 0, 0), *trade(PRAGUE - 4 * DAY + 3600, 600, 600.0, 1),
            *trade(PRAGUE - 3 * DAY + 3600, 600, 40.0, 2), *trade(PRAGUE - 2 * DAY + 3600, 600, -50.0, 3)]
    r = progress.reading(BEAT, CHALLENGE, {"reward_share": None, "payout_days": None}, rows, "Europe/Prague")
    assert r["profit"] == 600.0 and r["target"] == 1000.0 and abs(r["done"] - 0.6) < 1e-9
    assert r["trading_days"] == 3 and r["profitable_days"] == 2 and r["days_ok"] is True and r["payout"] is None
    h = progress.reading(BEAT, HANTEC, {"reward_share": None, "payout_days": None}, rows, "Europe/Prague")
    assert h["profitable_days"] == 1 and h["days_ok"] is False                      # only 600 reaches 0.5 % of 10 000 = 50
    c = h["consistency"]
    assert abs(c["ratio"] - 600.0 / 590.0) < 1e-9 and not c["ok"] and c["limit"] == 0.35
    assert progress.consistency({}, HANTEC) is None and progress.consistency({1: 5.0}, CHALLENGE) is None
    assert "NO se cumple" in progress.lines(h)[-1]


def check_payout() -> None:
    """The last withdrawal, the next date one cycle later, and what is payable now."""
    pay = deal(PRAGUE - 20 * DAY, -300.0, 2, 0, 0)
    out = progress.payouts([pay], PRAGUE - 40 * DAY + OFF, 0.8, 14, 10600.0, 10000.0)
    assert out["last"] == (pay["time"], 300.0) and out["next"] == pay["time"] + 14 * DAY
    assert abs(out["payable"] - 480.0) < 1e-9
    first = progress.payouts([], PRAGUE, 0.8, 14, 9900.0, 10000.0)                  # no payout yet: from the first trade
    assert first["last"] is None and first["next"] == PRAGUE + 14 * DAY and first["payable"] == 0.0
    assert progress.payouts([], None, None, None, 1.0, 1.0) == {"last": None, "next": None, "payable": None}
    f = progress.reading({**BEAT, "balance": 10480.0}, FUNDED, {"reward_share": 0.9, "payout_days": 14}, [pay], "Europe/Prague")
    assert f["target"] is None and abs(f["payout"]["payable"] - 432.0) < 1e-9


def check_eas() -> None:
    """Expected against mounted, the magics, and a strategy that went quiet."""
    sheet = [{"symbol": "EURUSD", "tf": "M30", "strategy": "3.29.126"}, {"symbol": "USA500", "tf": "D1", "strategy": "9.5.175"}]
    charts = [{"symbol": "EURUSD.h", "period": "M30", "expert": "Strategy 3.29.126"},
              {"symbol": "GBPUSD", "period": "H1", "expert": "Strategy 7.7.7"}]
    now = GMT + OFF
    trades = [{"magic": 11, "comment": "Strategy_3_29_126", "open": now - 40 * DAY, "close": now - 40 * DAY + 60}]
    rows = {r["strategy"]: r for r in eas.compare(sheet, charts, trades, [], {11: "Strategy 3.29.126"}, now)}
    assert rows["3.29.126"]["flags"] == ["sin operar hace 39 d"] and rows["3.29.126"]["magic"] == 11
    assert rows["9.5.175"]["flags"] == ["esperada y no montada"]
    assert rows["7.7.7"]["flags"] == ["montada y no esperada"]
    stray = eas.compare(None, None, [{"magic": 99, "comment": "x", "open": now, "close": None}], [], {11: "Strategy 3.29.126"}, now)
    assert stray[0]["flags"] == ["magic sin registrar"] and stray[0]["expected"] is None
    assert eas.strategy_key("Strategy_3_23_151") == eas.strategy_key("Strategy 3.23.151") == "3.23.151"


def check_pairs() -> None:
    """Entries pair across accounts by side and ±5 min; the unpaired are listed with who is missing."""
    t0 = GMT - 2 * DAY

    def acct(label: str, offset: int, times: list[tuple[int, str]]) -> dict:
        """An account whose magic 7 entered at these (UTC epoch, side)."""
        return {"login": label, "label": label, "offset": offset, "excursions": None,
                "trades": [{"magic": 7, "comment": "Strategy_3_23_151", "side": s, "open": t + offset, "close": t + offset + 60,
                            "net": 10.0} for t, s in times]}
    a = acct("A", OFF, [(t0, "buy"), (t0 + DAY, "sell"), (t0 + 2 * DAY - 7200, "buy")])
    b = acct("B", 7200, [(t0 + 300, "buy"), (t0 + DAY + 301, "sell"), (t0 + 2 * DAY - 7200, "sell")])   # 300 s pairs, 301 s does not
    out = strategies.pairing([a, b], {}, GMT)[0]
    assert out["complete"] == 1 and len(out["lonely"]) == 4
    assert sorted((g["side"], tuple(g["missing"])) for g in out["lonely"]) == [("buy", ("B",)), ("sell", ("A",)), ("sell", ("A",)), ("sell", ("B",))]
    old = [acct("A", OFF, [(GMT - 9 * DAY, "buy")]), acct("B", OFF, [(GMT - 9 * DAY, "buy")])]   # outside the 7 days
    assert strategies.pairing(old, {}, GMT)[0]["lonely"] == []
    assert strategies.pairing([a], {}, GMT) == []                                  # one account is no pair
    rec = strategies.record([a, b], {})[0]
    assert rec["accounts"] == 2 and rec["trades"] == 6 and rec["net"] == 60.0 and rec["strategy"] == "3.23.151"
    assert rec["win_rate"] == 1.0 and rec["worst_mae"] is None
    groups = strategies.group([(0, "A"), (100, "B"), (200, "B"), (900, "A")], ["A", "B"], 300)
    assert groups == [[(0, "A"), (100, "B")], [(200, "B")], [(900, "A")]]


def check_health() -> None:
    """Disconnection episodes and minutes since the server's midnight."""
    frame = pd.DataFrame({"server_time": [10, 20, 30, 40, 50, 60, 70], "connected": [0, 1, 0, 0, 1, 0, 1]})
    assert health.disconnections(frame, 0) == (3, 4)
    assert health.disconnections(frame, 25) == (2, 3)                              # the first episode is before `since`
    assert health.disconnections(None, 0) is None
    assert floors.server_offset({"server_time": GMT + OFF + 20, "written_gmt": GMT}) == OFF


def main() -> None:
    """Run every check; an assertion names what broke."""
    for check in (check_days, check_progress, check_payout, check_eas, check_pairs, check_health):
        check()
    print("test_fleet_progress: ok")


if __name__ == "__main__":
    main()
