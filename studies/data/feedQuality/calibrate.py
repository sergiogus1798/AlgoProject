#!/usr/bin/env python3
"""Per-feed K*, session and stable year, measured once when a feed enters the library.

Proposes; never writes the ledger. Its output is the evidence each `feedQuality.K.<feed>` and
`feedQuality.sessions.<feed>` row of ledger/thresholds.yaml is written from, by hand, before
any strategy is looked at (owner's answer 2.15).
"""

import argparse
import json
from datetime import date

import numpy as np

from core import fanout
from core.paths import feed_quality_dir
from core.study.result import progress
from engines.market.feed import session
from studies.data.feedQuality import calendar, detect, inputs, summary

CFG: dict = {}
MASKS: dict = {}
RUNS = None


def quantisation(b: dict, got: dict, tick: float) -> dict:
    """Whether the scale collapses to a tick or two: the silver and CADJPY question (3.3).

    Returns:
        The share of contiguous M1 returns that move exactly one tick, the 1st percentile
        of the unfloored scale in ticks, and the share of bars the floors lifted.
    """
    prev = np.r_[b["c"][0], b["c"][:-1]]
    fin = np.isfinite(got["r"])
    moves = np.rint(np.abs(b["c"] - prev)[fin] / tick)
    raw_ticks = (got["raw"] * prev / tick)[np.isfinite(got["raw"])]
    return {"one_tick_share": float(np.mean(moves == 1)),
            "raw_sigma_p1_ticks": float(np.percentile(raw_ticks, 1)),
            "floored_share": float(np.mean(got["sigma"][np.isfinite(got["raw"])]
                                           > got["raw"][np.isfinite(got["raw"])]))}


def one_feed(feed: str) -> dict:
    """Everything the ledger rows of one feed are written from."""
    b = inputs.bars(feed)
    tick = inputs.tick(b, CFG["session"]["years"])
    got = detect.measure(b, tick, CFG)
    yearly_k = detect.yearly_counts(b, got, CFG["k"]["candidates"])
    k, medians = summary.k_star(yearly_k, CFG)
    ev = detect.events(b, got, k or max(CFG["k"]["candidates"]), MASKS[feed], CFG)
    holes = (ev["kind"] == "hueco") & (ev["cls"] == calendar.OWN)
    ev.loc[holes, "cls"] = calendar.classify(ev[holes], RUNS)
    yearly = summary.counts(ev, "Y")
    stable, grade = summary.stability(yearly, CFG)
    last_full = int(b["t"][-1].year) - 1
    lo, hi = CFG["k"]["quiet_years"]
    quiet = yearly[(yearly.index >= lo) & (yearly.index <= hi)]
    return {"feed": feed, "tick": tick, "K": k, "quiet_medians": medians,
            "per_year_by_K": {int(y): {int(c): int(v) for c, v in row.items()}
                              for y, row in yearly_k.iterrows()},
            "session": session.text(MASKS[feed]),
            "stable_from": stable, "grade": grade,
            "residual_gaps_per_year": summary.residual_gaps(yearly, CFG, last_full),
            "spike_revert_quiet_median": float(quiet["cierre y vuelta"].median()),
            "wick_revert_quiet_median": float(quiet["mecha y vuelta"].median()),
            "frozen_quiet_median": float(quiet["congelado"].median()),
            "quantisation": quantisation(b, got, tick)}


def ledger_rows(found: dict, today: str) -> str:
    """The rows to append to ledger/thresholds.yaml, as text for a person to paste."""
    lo, hi = CFG["k"]["quiet_years"]
    s = CFG["scale"]
    out = []
    for feed, f in found.items():
        med = ", ".join(f"N{k}={v:g}" for k, v in f["quiet_medians"].items())
        out.append(f"""
  - key: feedQuality.K.{feed}
    value: {f['K']}
    source: studies/data/feedQuality/config.yaml#K.{feed}
    set_by: agente
    set_on: {today}
    why: >-
      criterio de la decisión 3 medido por studies.data.feedQuality.calibrate: medianas de
      picos de cierre por año {lo}–{hi} {med}; escala {s['window_weeks']} semanas
      retrospectiva, arranque {s['min_weeks']}, suelo {s['floor_ticks']} ticks y
      {s['floor_rel']} × mediana. Año estable {f['stable_from']}. Se recalcula sólo si
      cambia el proveedor del feed

  - key: feedQuality.sessions.{feed}
    value: "{f['session']}"
    source: studies/data/feedQuality/config.yaml#sessions.{feed}
    set_by: agente
    set_on: {today}
    why: >-
      deducida del feed (pregunta del {today}): minutos con vela en al menos
      {CFG['session']['share']} de las semanas de {CFG['session']['years'][0]}–{CFG['session']['years'][1]}""")
    return "\n".join(out)


def main() -> None:
    """Measure every feed of the library and print the ledger rows it proposes."""
    global RUNS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="section.key=value")
    ap.add_argument("--workers", type=int, default=13)
    a = ap.parse_args()
    CFG.update(inputs.config(a.set))
    y0, y1 = CFG["session"]["years"]
    feeds, at = inputs.feeds(), {}
    for feed in feeds:
        at[feed] = inputs.bars(feed)["at"]
        MASKS[feed] = session.deduce(at[feed], inputs.year_minute(y0), inputs.year_minute(y1 + 1),
                                     CFG["session"]["share"])
    progress(10, "calendario")
    RUNS = calendar.silences({f: (at[f], session.without_hours(MASKS[f], CFG["rollover_hours"]))
                              for f in inputs.calendar_feeds()}, CFG)
    del at
    found = {}
    for n, (feed, got) in enumerate(fanout.run(one_feed, {f: 1 for f in feeds}, a.workers)):
        found[feed] = got
        progress(10 + 90 * (n + 1) // len(feeds), feed)
    found = {f: found[f] for f in feeds}
    out = feed_quality_dir()
    out.mkdir(parents=True, exist_ok=True)
    (out / "calibration.json").write_text(json.dumps(found, indent=1, ensure_ascii=False))
    RUNS.to_parquet(out / "calendar.parquet")
    for f in found.values():
        print(f"{f['feed']:26s} K*={f['K']}  {f['quiet_medians']}  estable {f['stable_from']}  "
              f"huecos resid. {f['residual_gaps_per_year']:g}/año  "
              f"vuelta cierre {f['spike_revert_quiet_median']:g}/año  "
              f"1 tick {f['quantisation']['one_tick_share']:.2f}")
    print(ledger_rows(found, date.today().isoformat()))
    print(f"-> {out / 'calibration.json'}")


if __name__ == "__main__":
    main()
