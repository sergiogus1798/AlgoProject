#!/usr/bin/env python3
"""Synthetic anomalies of known size planted in a copy of a real feed: what the detector finds.

The design is the owner's (answer 2.16): amplitudes {0.5..3}·K, 500 per cell for spikes and
200 for runs, spaced apart, in session hours outside the rollover, away from real spikes.
"""

import argparse
import json

import numpy as np
import pandas as pd

from core import fanout
from core.paths import feed_quality_dir
from engines.market.feed import scale, session
from studies.data.feedQuality import detect, inputs

GRID = [("cierre", a, 500) for a in (0.5, 0.75, 1, 1.25, 1.5, 2, 3)] + \
       [("mecha", a, 500) for a in (0.5, 0.75, 1, 1.25, 1.5, 2, 3)] + \
       [("vuelta parcial", f, 500) for f in (0.9, 0.8, 0.7, 0.6)] + [("sin vuelta", 1.5, 500)] + \
       [("congelado", d, 200) for d in (5, 8, 9, 10, 11, 12, 20, 30)] + \
       [("hueco", d, 200) for d in (3, 4, 5, 6, 10, 30)]
SPAN, SPACING, QUIET = 42, 60, 5.0
CFG: dict = {}
SHARE = [1.0]


def positions(b: dict, got: dict, counted: np.ndarray, n: int, rng: np.random.Generator
              ) -> np.ndarray:
    """Bars where an event can be planted without touching the session edge or a real spike."""
    at = b["at"]
    whole = np.zeros(len(at), bool)
    whole[1:-SPAN] = at[1 + SPAN:] - at[:-SPAN - 1] == SPAN + 1
    inside = pd.Series(counted[at % scale.WEEK]).rolling(SPAN + 2).min().shift(-SPAN).to_numpy()
    loud = pd.Series(np.maximum(got["z_close"], got["z_wick"])).rolling(SPAN + 10).max()
    calm = loud.shift(-SPAN).to_numpy() < QUIET
    ok = np.flatnonzero(whole & (inside == 1) & calm & np.isfinite(got["sigma"]))
    picked = np.sort(rng.choice(ok, min(len(ok), 3 * n), replace=False))
    spaced = [picked[0]]
    for i in picked[1:]:
        if i - spaced[-1] >= SPACING:
            spaced.append(i)
    return rng.permutation(np.array(spaced))[:n]


def plant(b: dict, got: dict, k: float, plan: pd.DataFrame, rng: np.random.Generator) -> dict:
    """A copy of the bars with every planned event written in."""
    o, h, low, c = (b[x].copy() for x in "ohlc")
    shift, keep, sig = np.zeros(len(c)), np.ones(len(c), bool), got["sigma"]
    # Jumps that stay come in pairs, in time order, of equal size and opposite sign — each
    # 1.5 K times the larger of the two scales — so the price level comes back exactly: the
    # tick floor moves with the price, and unpaired jumps walked it 14 % off on silver.
    stay = plan[plan["cls"] == "sin vuelta"].sort_values("i")
    size = {}
    for a, b_ in zip(stay.index[::2], stay.index[1::2]):
        x = rng.choice([-1.0, 1.0]) * stay.loc[[a, b_], "param"].max() * k * max(
            sig[stay.at[a, "i"]], sig[stay.at[b_, "i"]])
        size[a], size[b_] = x, -x
    for row, (cls, p, i) in zip(plan.index, plan[["cls", "param", "i"]].itertuples(index=False)):
        s = rng.choice([-1.0, 1.0])
        if cls == "cierre" or cls == "vuelta parcial":
            x = s * (p if cls == "cierre" else 1.5) * k * sig[i]
            c[i] = c[i - 1] * np.exp(x)
            if cls == "vuelta parcial":
                o[i + 1:i + 4] = c[i]
                c[i + 1:i + 3] = c[i]
                c[i + 3] = c[i - 1] * np.exp((1 - p) * x)
                h[i + 1:i + 4] = np.maximum(o[i + 1:i + 4], c[i + 1:i + 4])
                low[i + 1:i + 4] = np.minimum(o[i + 1:i + 4], c[i + 1:i + 4])
            h[i], low[i] = max(h[i], c[i], o[i]), min(low[i], c[i], o[i])
        elif cls == "mecha":
            if s > 0:
                h[i] = max(o[i], c[i]) * np.exp(p * k * sig[i])
            else:
                low[i] = min(o[i], c[i]) * np.exp(-p * k * sig[i])
        elif cls == "sin vuelta":
            shift[i] += size.get(row, s * p * k * sig[i])
        elif cls == "congelado":
            for arr in (o, h, low, c):
                arr[i:i + int(p)] = arr[i]
        else:
            keep[i:i + int(p)] = False
    f = np.exp(np.cumsum(shift))
    return {"t": b["t"][keep], "at": b["at"][keep],
            **{x: (arr * f)[keep] for x, arr in zip("ohlc", (o, h, low, c))}}


def merged(b: dict, cls: str, p: float, i: int) -> bool:
    """Whether a planted frozen run or gap touches a real bar identical to its own.

    Such a run joins the real flat bars beside it and is scored by what it became, not by
    what was planted: an 8-minute run next to two identical real bars is a real 10-bar run.
    """
    if cls != "congelado":
        return False
    same = [all(b[x][j] == b[x][i] for x in "ohlc") for j in (i - 1, i + int(p))]
    return any(same)


def found(ev: pd.DataFrame, cls: str, at_i: int, p: float) -> tuple[bool, bool]:
    """Whether one planted event was detected, and whether it was read as spike-and-revert."""
    if cls in ("congelado", "hueco"):
        # A planted run can merge with identical real bars next to it: it is found when a
        # detected run covers the planted span, wherever that run starts.
        cover = ev[(ev["kind"] == cls) & (ev["start_min"] <= at_i)
                   & (ev["end_min"] >= at_i + int(p) - 1)]
        return len(cover) > 0, False
    kind = "mecha" if cls == "mecha" else "cierre"
    hit = ev[(ev["kind"] == kind) & (ev["start_min"] == at_i)]
    return len(hit) > 0, bool((hit["cls"] == "vuelta").any())


def run_feed(feed: str) -> dict:
    """Plant the whole grid in one feed and score the detector on it."""
    rng = np.random.default_rng(17)
    cal = json.loads((feed_quality_dir() / "calibration.json").read_text())[feed]
    k, mask = cal["K"], session.mask(cal["session"])
    b = inputs.bars(feed)
    tick = inputs.tick(b, CFG["session"]["years"])
    got = detect.measure(b, tick, CFG)
    counted = session.without_hours(mask, CFG["rollover_hours"])
    cells = [(cls, p, max(1, int(n * SHARE[0]))) for cls, p, n in GRID]
    where = positions(b, got, counted, sum(n for *_, n in cells), rng)
    plan = pd.DataFrame([(cls, p) for cls, p, n in cells for _ in range(n)], columns=["cls", "param"])
    plan["i"] = where[:len(plan)]
    plan["at"] = b["at"][plan["i"]]
    plan["merged"] = [merged(b, c, p, i) for c, p, i in plan[["cls", "param", "i"]].itertuples(index=False)]
    before = detect.events(b, got, k, mask, CFG)
    b2 = plant(b, got, k, plan, rng)
    after = detect.events(b2, detect.measure(b2, tick, CFG), k, mask, CFG)
    hits = [found(after, c, a, p) for c, p, a in plan[["cls", "param", "at"]].itertuples(index=False)]
    plan["found"], plan["as_revert"] = [h[0] for h in hits], [h[1] for h in hits]
    lo, hi = plan["at"].to_numpy() - 2, plan["at"].to_numpy() + plan["param"].clip(lower=1).to_numpy() + 8
    lo_s, hi_s = np.sort(lo), np.sort(hi)

    def outside(ev: pd.DataFrame) -> pd.DataFrame:
        """The events that start outside every planted event's footprint."""
        at = ev["start_min"].to_numpy()
        return ev[np.searchsorted(lo_s, at, "right") - np.searchsorted(hi_s, at, "right") == 0]

    key = ["kind", "start_min"]
    real_b, real_a = outside(before), outside(after)
    new = real_a.merge(real_b[key], on=key, how="left", indicator=True)
    new = new[new["_merge"] == "left_only"]
    j = np.searchsorted(b["at"], new["start_min"].to_numpy())
    was = np.where(new["kind"] == "mecha", got["z_wick"][j], got["z_close"][j])
    scored = plan[~plan["merged"]]
    table = scored.groupby(["cls", "param"], sort=False).agg(
        n=("found", "size"), recall=("found", "mean"), as_revert=("as_revert", "mean")).reset_index()
    return {"feed": feed, "K": k, "table": table.to_dict("records"),
            "merged_excluded": int(plan["merged"].sum()), "false_marks": len(new), "false_marks_near_k": int(np.sum(was >= 0.95 * k)),
            "real_before": len(real_b), "real_after": len(real_a)}


def accept(res: dict) -> dict:
    """The owner's acceptance criteria (2.16), each a bool."""
    t = pd.DataFrame(res["table"]).set_index(["cls", "param"])
    r = t["recall"]
    return {"recall ≥ 95 % a 1,25·K": bool(min(r["cierre", 1.25], r["mecha", 1.25]) >= 0.95),
            "recall ≥ 99 % a 1,5·K": bool(min(r["cierre", 1.5], r["mecha", 1.5]) >= 0.99),
            "congelados ≥ 10 min ≥ 99 %": bool(all(r["congelado", d] >= 0.99 for d in (10, 11, 12, 20, 30))),
            "congelados ≤ 9 min = 0 %": bool(all(r["congelado", d] == 0 for d in (5, 8, 9))),
            "huecos ≥ 5 min ≥ 99 %": bool(all(r["hueco", d] >= 0.99 for d in (5, 6, 10, 30))),
            "huecos ≤ 4 min = 0 %": bool(all(r["hueco", d] == 0 for d in (3, 4))),
            "vuelta ≥ 80 % leída como tal ≥ 99 %": bool(min(t.loc[("vuelta parcial", 0.9), "as_revert"],
                                                            t.loc[("vuelta parcial", 0.8), "as_revert"]) >= 0.99),
            "vuelta ≤ 70 % leída como tal ≤ 1 %": bool(max(t.loc[("vuelta parcial", 0.7), "as_revert"],
                                                           t.loc[("vuelta parcial", 0.6), "as_revert"]) <= 0.01),
            "cero detecciones nuevas": res["false_marks"] == 0,
            "recuento real cambia ≤ 2 %": abs(res["real_after"] - res["real_before"]) <= 0.02 * res["real_before"]}


def main() -> None:
    """Run the injection on every feed (or the ones named) and print each one's acceptance."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--feed", action="append", default=[])
    ap.add_argument("--share", type=float, default=1.0, help="fraction of the grid's counts")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    CFG.update(inputs.config([]))
    SHARE[0] = a.share
    feeds = a.feed or inputs.feeds()
    out = {}
    for feed, res in fanout.run(run_feed, {f: 1 for f in feeds}, a.workers):
        res["accept"] = accept(res)
        out[feed] = res
        failed = [k for k, v in res["accept"].items() if not v]
        print(f"{feed:26s} K={res['K']}  nuevas {res['false_marks']} (a < 5 % de K: "
              f"{res['false_marks_near_k']})  real {res['real_before']}"
              f"→{res['real_after']}  {'ACEPTA' if not failed else 'FALLA: ' + '; '.join(failed)}")
    (feed_quality_dir() / "injection.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"-> {feed_quality_dir() / 'injection.json'}")


if __name__ == "__main__":
    main()
