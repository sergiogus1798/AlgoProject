"""Pool -> per-member equity, reconciled against SQX, cached under its pool hash and config fingerprint."""

from datetime import datetime, timezone as tz
from itertools import groupby
from pathlib import Path

import pandas as pd

from core import assetdata, fanout
from core.barstore import source as bars_of
from core.manifest import code_version
from core.study.config import fingerprint

from . import blocks, days, excursions, matrix, paths, reconcile, sqxcurve, store
from ..inputs import calendar as calendar_mod
from ..inputs import pool, source

SEGMENT_OF_SAMPLE = sqxcurve.SAMPLE_TO_SEGMENT  # {"IS": "build", "OOS": "oos1"}

# What every worker reads, set before the pool forks so nothing is pickled on the way in: the
# feed's M1 bars (~1 GB, shared copy-on-write), the members' sources, the config, the M5 grid.
_STATE: dict = {}


def _span(data: dict, has_oos: bool) -> tuple[pd.Timestamp, pd.Timestamp]:
    """A member's own asset's build start to the end of its last segment with trades."""
    lo = pd.Timestamp(assetdata.window(data, "build")[0], unit="ms")
    last = "oos1" if has_oos else "build"
    hi = pd.Timestamp(assetdata.window(data, last)[1], unit="ms") - pd.Timedelta(days=1)
    return lo, hi


def _reconcile_rows(identity: str, s: dict, bars: pd.DataFrame, feed_days: pd.DataFrame,
                    cfg: dict) -> tuple[list[dict], bool]:
    """Per-leg reconciliation against SQX's curve, plus the MAE/MFE licence.

    Args:
        feed_days: The member's whole-history server days on its feed's own clock. Each SQX leg
            restarts at 0, so a leg's rebuilt low equity is the whole path's minus the P&L of
            the legs before it (every earlier leg's trades are closed when the next opens).

    Returns:
        One `reconcile.csv` row per segment the member has trades for, and whether the
        member is excluded (any segment "out", or the excursion licence refused).
    """
    tol, share = cfg["equity"]["excursion_tolerance"], cfg["equity"]["excursion_min_share"]
    licence = excursions.licence(s["trades"], excursions.rebuild(s["trades"], bars, s["point_value"]),
                                 tol, share)
    sqx = sqxcurve.from_harvest(s["sqx_equity"], s["symbol"])
    low = reconcile.low_equity(feed_days)
    rows, excluded, before = [], not licence["licensed"], 0.0
    reasons = [] if licence["licensed"] else [f"licencia MAE/MFE ({licence['mae_exact']:.2f}/"
                                              f"{licence['mfe_exact']:.2f})"]
    for sample, segment in SEGMENT_OF_SAMPLE.items():
        leg = s["trades"][s["trades"]["sample"] == sample]
        if leg.empty:
            continue
        got = reconcile.curve(low - before, sqx.loc[sqx["segment"] == segment, "low"], tol, share)
        before += float(leg["Profit/Loss"].sum())
        if got["verdict"] == "out":
            excluded = True
            reasons.append(f"reconcile {segment} ({got['exact']:.2f})")
        rows.append({"identity": identity, "segment": segment, **got,
                     "mae_exact": licence["mae_exact"], "mfe_exact": licence["mfe_exact"],
                     "licensed": licence["licensed"]})
    for row in rows:
        row["excluded"], row["reason"] = excluded, "; ".join(reasons)
    return rows, excluded


def _member(identity: str) -> dict:
    """One member, in a worker: its minute path built once, used for everything, never returned.

    Returns:
        Reconciliation rows, daily P&L on the reference clock, the server-day table and the
        float32 M5 arrays per firm clock — megabytes, where the path is ~250 MB.
    """
    s, bars, cfg = _STATE["sources"][identity], _STATE["bars"], _STATE["cfg"]
    path = paths.minute_path(s["trades"], bars, s["point_value"])
    feed_days = days.server_days(path, s["clock"], s["clock"])
    rows, excluded = _reconcile_rows(identity, s, bars, feed_days, cfg)
    ref_days = days.server_days(path, s["clock"], cfg["equity"]["reference_clock"])
    firm_days, m5 = {}, {}
    for firm, zone in cfg["equity"]["firm_clocks"].items():
        firm_days[firm] = days.server_days(path, s["clock"], zone)  # then blocks: same cached frame
        m5[firm] = blocks.blocks(path, s["clock"], zone, _STATE["grid"])
    return {"identity": identity, "symbol": s["symbol"], "feed": s["feed"], "clock": s["clock"],
            "excluded": excluded, "rows": rows, "span": _STATE["spans"][identity],
            "daily_pnl": days.daily_pnl(ref_days), "firm_days": firm_days, "m5": m5,
            "n_nat": int(ref_days.attrs["n_nat"])}


def _workers(bars: pd.DataFrame, n_members: int, cfg: dict) -> int:
    """Processes that fit the RAM ceiling; `fanout` caps it at the physical cores.

    What stays in the parent is taken off first: the shared bars and every member's M5
    arrays (float32, low and high, per firm clock) that accumulate as results land.
    """
    m5_gb = n_members * len(cfg["equity"]["firm_clocks"]) * 2 * len(_STATE["grid"]) * 4 / 1e9
    free = cfg["compute"]["max_ram_gb"] - bars.memory_usage(deep=True).sum() / 1e9 - m5_gb
    return max(1, int(free / cfg["compute"]["worker_ram_gb"]))


def _firm_day_table(kept: list[dict], firm: str) -> pd.DataFrame:
    """Long-form day table for one firm clock: day, identity, closed, float_end, low, high, opened, open_end."""
    parts = []
    for m in kept:
        frame = m["firm_days"][firm].reset_index(names="day")
        frame.insert(1, "identity", m["identity"])
        parts.append(frame)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(
        columns=["day", "identity", "closed", "float_end", "low", "high", "opened", "open_end"])


def _m5_blob(kept: list[dict], firm: str, zone: str, grid: pd.DatetimeIndex) -> dict:
    """One firm's M5 grid and every kept member's block arrays on it (contract M)."""
    return {"grid_start": int(grid[0].value), "n_blocks": len(grid),
            "block_days": blocks.block_days(grid, zone),
            "low": {m["identity"]: m["m5"][firm]["low"] for m in kept},
            "high": {m["identity"]: m["m5"][firm]["high"] for m in kept}}


def _processed(loaded: dict, cfg: dict) -> tuple[list[dict], pd.DatetimeIndex]:
    """Every member through `_member`, one feed's bars in RAM at a time, members in parallel."""
    spans = {i: _span(assetdata.load(s["symbol"]), "OOS" in set(s["trades"]["sample"]))
             for i, s in loaded.items()}
    grid = blocks.grid(min(lo for lo, _ in spans.values()),
                       max(hi for _, hi in spans.values()) + pd.Timedelta(days=1),
                       cfg["equity"]["block_minutes"])
    _STATE.update(sources=loaded, cfg=cfg, spans=spans, grid=grid)
    out = []
    by_feed = sorted(loaded, key=lambda i: loaded[i]["feed"])
    for feed, group in groupby(by_feed, key=lambda i: loaded[i]["feed"]):
        _STATE["bars"] = bars_of(feed, ["High", "Low", "Close"])
        costs = {i: len(loaded[i]["trades"]) for i in group}
        out += [got for _, got in fanout.run(_member, costs, _workers(_STATE["bars"], len(loaded), cfg))]
    _STATE.clear()
    return out, grid


def build(pool_name: str, cfg: dict) -> Path:
    """Build (or report the existing cache of) one pool's universe.

    Args:
        pool_name: A declared pool's name (`inputs.pool.declare`).
        cfg: `inputs.config.load()`'s result.

    Returns:
        `store.ROOT/<pool_hash>-<config_fingerprint>/` — the cache key is pool hash AND
        config fingerprint together, so a config change always gets its own folder and
        never silently reuses another run's numbers.
    """
    declared = pool.read(pool_name, cfg.get("pool", {}).get("firm"))
    out = store.folder(declared["hash"], fingerprint(cfg))
    if store.cached(out):
        return out

    loaded = {r["identity"]: source.load(r["identity"], r["version"]) for r in declared["members"]}
    processed, grid = _processed(loaded, cfg)
    kept = [m for m in processed if not m["excluded"]]
    excluded = [m for m in processed if m["excluded"]]
    daily = matrix.stack({m["identity"]: m["daily_pnl"] for m in kept},
                         {m["identity"]: m["span"] for m in kept})
    reconcile_rows = pd.DataFrame([row for m in processed for row in m["rows"]])
    firms = cfg["equity"]["firm_clocks"]
    days_by_firm = {firm: _firm_day_table(kept, firm) for firm in firms}
    m5_by_firm = {firm: _m5_blob(kept, firm, zone, grid) for firm, zone in firms.items()}

    cal = calendar_mod.portfolio(sorted({m["symbol"] for m in processed}))
    manifest = {
        "pool": {"name": pool_name, "hash": declared["hash"]},
        "config_fingerprint": fingerprint(cfg),
        "calendar": {k: [str(v[0]), str(v[1])] for k, v in cal.items()},
        "clock": {"reference": cfg["equity"]["reference_clock"], "firms": firms,
                  "feeds": {m["feed"]: m["clock"] for m in processed}},
        "unconfirmed_clocks": cfg["equity"]["unconfirmed_clocks"],
        "n_nat": {m["identity"]: m["n_nat"] for m in processed},
        "members": {"kept": [m["identity"] for m in kept],
                    "excluded": [{"identity": m["identity"],
                                  "reason": m["rows"][0]["reason"] if m["rows"] else "sin segmentos"}
                                 for m in excluded]},
        "borrowed": {m["symbol"]: calendar_mod.borrowed(cal, m["symbol"]) for m in processed},
        "code_version": code_version(),
        "built_at": datetime.now(tz.utc).isoformat(),
    }
    store.write(out, daily, matrix.monthly(daily), reconcile_rows, days_by_firm, m5_by_firm, manifest)
    return out


def load(pool_hash_dir: Path) -> dict:
    """Read a built universe back (`store.load`)."""
    return store.load(pool_hash_dir)
