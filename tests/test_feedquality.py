"""Known answers for the feed-quality detector and its alarm, then the injection on a real feed."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.market.feed import scale, session  # noqa: E402
from studies.data.feedQuality import alarm, calendar, detect, inject, inputs, summary, touch  # noqa: E402

CFG = inputs.config([])
K = 20
WEEKDAYS = session.mask("Mon 00:00-Sat 00:00")


def synthetic(weeks: int = 40, seed: int = 3) -> dict:
    """A Monday-to-Friday M1 random walk with a known scale, as inputs.bars() returns it."""
    rng = np.random.default_rng(seed)
    at = np.arange(weeks * scale.WEEK)
    at = at[WEEKDAYS[at % scale.WEEK]] + 10 * scale.WEEK
    c = 100 * np.exp(np.cumsum(rng.normal(0, 1e-4, len(at))))
    o = np.r_[c[0], c[:-1]]
    h, low = np.maximum(o, c) * (1 + 2e-5), np.minimum(o, c) * (1 - 2e-5)
    t = pd.to_datetime((at + scale.ORIGIN) * scale.MINUTE_NS)
    return {"t": t, "at": at, "o": o, "h": h, "l": low, "c": c}


def at_hour(b: dict, week: int, day: int, hour: int) -> int:
    """Index of the bar opening a given hour of a given week of the series."""
    return int(np.searchsorted(b["at"], b["at"][0] + week * scale.WEEK + day * 1440 + hour * 60))


def detector() -> None:
    """Each planted event is found or missed exactly as its size says."""
    b = synthetic()
    got = detect.measure(b, 1e-5, CFG)
    sig = got["sigma"]
    plan = {}
    i = at_hour(b, 20, 1, 10)                      # close spike of 2K, back at once
    b["c"][i] = b["c"][i - 1] * np.exp(2 * K * sig[i])
    b["h"][i] = b["c"][i]
    plan["spike_revert"] = b["at"][i]
    i = at_hour(b, 21, 1, 10)                      # 0.5K: no spike
    b["c"][i] = b["c"][i - 1] * np.exp(0.5 * K * sig[i])
    plan["small"] = b["at"][i]
    i = at_hour(b, 22, 2, 10)                      # a wick of 2K, close untouched
    b["h"][i] = max(b["o"][i], b["c"][i]) * np.exp(2 * K * sig[i])
    plan["wick"] = b["at"][i]
    i = at_hour(b, 23, 2, 10)                      # a jump that stays
    b["c"][i:] *= np.exp(2 * K * sig[i])
    b["o"][i + 1:] *= np.exp(2 * K * sig[i])
    b["h"][i:] *= np.exp(2 * K * sig[i])
    b["l"][i:] *= np.exp(2 * K * sig[i])
    plan["stay"] = b["at"][i]
    for name, week, n in (("frozen10", 24, 10), ("frozen9", 25, 9)):
        i = at_hour(b, week, 3, 10)
        for x in "ohlc":
            b[x][i:i + n] = b[x][i]
        plan[name] = b["at"][i]
    i = at_hour(b, 26, 3, 0)                       # frozen inside the rollover hours
    for x in "ohlc":
        b[x][i:i + 12] = b[x][i]
    plan["frozen_rollover"] = b["at"][i]
    keep = np.ones(len(b["at"]), bool)
    for name, week, n in (("gap5", 27, 5), ("gap4", 28, 4)):
        i = at_hour(b, week, 3, 10)
        keep[i:i + n] = False
        plan[name] = b["at"][i]
    b = {k: v[keep] for k, v in b.items()}
    ev = detect.events(b, detect.measure(b, 1e-5, CFG), K, WEEKDAYS, CFG)

    def one(kind: str, where: int) -> pd.DataFrame:
        """The events of one kind starting at one minute."""
        return ev[(ev["kind"] == kind) & (ev["start_min"] == where)]

    assert list(one("cierre", plan["spike_revert"])["cls"]) == ["vuelta"]
    assert one("cierre", plan["small"]).empty
    assert list(one("mecha", plan["wick"])["cls"]) == ["vuelta"]
    assert one("cierre", plan["wick"]).empty
    assert list(one("cierre", plan["stay"])["cls"]) == ["extremo"]
    assert list(one("congelado", plan["frozen10"])["cls"]) == ["congelado"]
    assert one("congelado", plan["frozen9"]).empty
    assert list(one("congelado", plan["frozen_rollover"])["cls"]) == ["rollover"]
    assert list(one("hueco", plan["gap5"])["size"]) == [5]
    assert one("hueco", plan["gap4"]).empty
    extra = ev[~ev["start_min"].isin(list(plan.values()))
               & ~ev["start_min"].isin([plan["spike_revert"] + 1])]
    assert extra[extra["kind"] != "hueco"].empty, extra  # the only echo is the spike's return


def the_alarm() -> None:
    """Chance reads no alarm, the best trades read one, and few flagged read «insuficiente»."""
    rng = np.random.default_rng(1)
    pnl = rng.normal(0, 10, 600)
    random = np.zeros(600, bool)
    random[rng.choice(600, 30, replace=False)] = True
    best = np.zeros(600, bool)
    best[np.argsort(pnl)[-30:]] = True
    assert alarm.test(pnl, random, CFG, "a")["verdict"] == alarm.QUIET
    assert alarm.test(pnl, best, CFG, "b")["verdict"] == alarm.ALARM
    assert alarm.test(pnl, best & (np.cumsum(best) <= 5), CFG, "c")["verdict"] == alarm.SHORT
    assert alarm.test(pnl, np.ones(600, bool), CFG, "d")["p"] == 1.0


def the_rest() -> None:
    """Interval counting, the session text, the calendar's three silences, the stable year."""
    spans = (np.array([10, 20, 40]), np.array([11, 25, 41]))
    assert list(touch.hits(spans, np.array([0, 11, 24, 25, 41]), np.array([10, 20, 25, 40, 50]))) \
        == [0, 0, 1, 0, 0]
    for text in ("Mon 00:00-Sat 00:00", "Mon 01:00-Tue 00:00, Fri 01:00-Sat 00:00"):
        assert session.text(session.mask(text)) == text
    at = np.arange(3 * scale.WEEK)
    at = at[WEEKDAYS[at % scale.WEEK]]
    silent = ((at >= 1440 + 600) & (at < 1440 + 630)) | ((at >= 2 * 1440 + 600) & (at < 2 * 1440 + 800)) \
        | ((at >= scale.WEEK + 2 * 1440) & (at < scale.WEEK + 3 * 1440))
    runs = calendar.silences({"a": (at[~silent], WEEKDAYS), "b": (at[~silent], WEEKDAYS)}, CFG)
    assert list(runs["cls"]) == [calendar.OUTAGE, calendar.PARTIAL, calendar.HOLIDAY]
    assert list(runs["minutes"]) == [30, 200, 1440]
    yearly = pd.DataFrame({"hueco": [900, 25, 2, 3, 29, 2, 5], "caída del proveedor": 0},
                          index=range(2011, 2018))
    assert summary.stability(yearly, CFG)[0] == 2012   # 29 passes the floor of 30


def injection() -> None:
    """The owner's grid (2.16), a fifth of its counts, planted in a copy of the gold feed."""
    inject.CFG.update(CFG)
    inject.SHARE[0] = 0.2
    res = inject.run_feed("XAUUSD_M1")
    ok = inject.accept(res)
    assert all(v for k, v in ok.items() if k != "cero detecciones nuevas"), ok
    assert res["false_marks"] <= 0.001 * res["real_before"], res["false_marks"]


if __name__ == "__main__":
    detector()
    the_alarm()
    the_rest()
    print("synthetic: ok")
    injection()
    print("injection on XAUUSD: ok")
