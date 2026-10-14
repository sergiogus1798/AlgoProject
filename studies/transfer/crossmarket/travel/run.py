"""The runner of the travel test: one export in, verdict.csv, markets.parquet, crossmarket.json and distribuciones.parquet out, in a folder it is given."""

import json
from pathlib import Path
from typing import Any, TypedDict, cast

import numpy as np
import pandas as pd

from core import assetmarkets, fanout, paths
from core.study import draws
from studies.research.memory import sources
from studies.transfer.crossmarket import load
from studies.transfer.crossmarket.inputs import config, markets
from studies.transfer.crossmarket.travel import cells, frequency, records, rules, shift, sizing, stat, tensor, units, validity

VERDICT = ["strategy", "markets", "markets_valid", "invalid_fraction", "fixed_distance", "freq_off",
           "freq_off_fraction", "z_conj", "p_conj", "z_conj_v2", "z_conj_v0", "z_conj_v1", "z_conj_v0v2",
           "z_minus_market", "minus_market", "p_breadth", "breadth_count", "tau_half", "e_principal",
           "worse", "worse_fraction", "z_beta", "e_end", "beta", "e_end_ratio", "net_t_pooled",
           "trades"]
MARKETS = ["strategy", "market", "z", "p", "e", "trades", "z_freq", "valid", "invalid_reason"]
OUTPUTS = ("verdict.csv", "markets.parquet", "crossmarket.json")
SEGMENT = "oos1"       # the card segment priced at: what step 9's task charges each market
MAIN_DATABANK = "Results"   # where the harvest keeps the main asset's own build and oos1 trades


def _free(out: Path, project: str, databank: str, export: str) -> None:
    """Refuse a folder that already holds a result, or is the live study's reports folder."""
    live = paths.report_dir(project, databank, export).resolve()
    if live in (out.resolve(), *out.resolve().parents) or any((out / f).exists() for f in OUTPUTS):
        raise FileExistsError(f"{out} holds a result or is the live study's folder; pass a new one")


class Travelled(TypedDict):
    """The export judged on the other markets: the verdict and markets frames, §7.1's row per market and the draws rows."""

    verdict: pd.DataFrame
    markets: pd.DataFrame
    checks: list[dict[str, Any]]
    draws: list[dict[str, Any]]


def _checks(inputs: load.Inputs, cfg: dict, params: dict) -> tuple[list[dict], dict]:
    """§7.1 for every market of the list: its row, and what the valid ones are priced with."""
    t, found, ready = cfg["travel"], [], {}
    for m in inputs["universe"]["markets"]:
        feed = m["feed"]
        costs, why = validity.card(feed, SEGMENT)
        span = markets.own_window(feed)
        if costs and span:
            bars = inputs["bars"][feed]
            bars = cast(pd.DataFrame, bars[(bars.index >= span["from"])
                                           & (bars.index < pd.Timestamp(span["to"]) + pd.Timedelta(days=1))])
            mine = cast(pd.DataFrame, inputs["trades"][inputs["trades"]["Symbol"] == feed]).reset_index(drop=True)
            row = validity.check(feed, mine, bars, costs, t["validity"]["point_value_margin"],
                                 t["validity"]["flat_atr_fraction"],
                                 t["validity"]["max_fill_error"], params["ATRPeriod"])
            ready[feed] = (bars, costs)
        else:
            row = {"market": feed, "valid": False, "invalid_reason": why or "no_cost_card"}
        found.append(row)
    found += [{"market": f, "valid": False, "invalid_reason": "not_in_export"}
              for f in inputs["universe"]["absent"]]
    return found, {r["market"]: ready[r["market"]] for r in found if r["valid"]}


def _frequency(inputs: load.Inputs, strategies: list[str], feeds: list[str], cuts: dict, t: dict,
               by: dict) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """P2: z_freq per strategy and valid market, how many strategies' markets it flags, counts."""
    counts = pd.DataFrame({f: [len(by.get((s, f), ())) for s in strategies] for f in feeds},
                          index=pd.Index(strategies))
    years = pd.Series({f: cast(pd.Timedelta, pd.Timestamp(cast(dict, markets.own_window(f))["to"]) + pd.Timedelta(days=1)
                           - pd.Timestamp(cast(dict, markets.own_window(f))["from"])) / cast(pd.Timedelta, pd.Timedelta(days=365.25))
                       for f in feeds})
    folder = paths.harvest_dir(inputs["project"], MAIN_DATABANK, inputs["export"])
    nan = pd.DataFrame(np.nan, index=pd.Index(strategies), columns=pd.Index(feeds))
    if not (folder / "trades.parquet").is_file():
        return nan, pd.Series(np.nan, index=strategies), counts
    main = pd.read_parquet(folder / "trades.parquet", columns=["identity", "Open time"])
    name = {i: s for s, i in inputs["identity"].items() if i}
    main = main.assign(strategy=main["identity"].map(name)).dropna(subset=["strategy"])  # pyright: ignore[reportArgumentType]  # pandas stubs reject a dict mapper
    z = frequency.z_freq(counts, years, main, cuts, t["frequency"])
    off = ((z.abs() > t["frequency"]["z"]) | (counts == 0)).sum(axis=1).astype(float)
    return z, off.where(main.groupby("strategy").size().reindex(strategies).gt(0)), counts


def _home(inputs: load.Inputs, params: dict, cal: pd.DataFrame, t: dict) -> tuple[str, tensor.Market | None]:
    """The main market on its own window, priced like any other: (feed, `tensor.market`'s or None)."""
    feed = inputs["universe"]["main"]
    (costs, _), span, bars = validity.card(feed, SEGMENT), markets.own_window(feed), inputs["bars"][feed]
    if not costs or not span:
        return feed, None
    bars = cast(pd.DataFrame, bars[(bars.index >= span["from"]) & (bars.index < pd.Timestamp(span["to"]) + pd.Timedelta(days=1))])
    with np.errstate(divide="ignore"):
        return feed, tensor.market(bars, costs, params, cal, t["validity"]["flat_atr_fraction"])


def _e_principal(trades: pd.DataFrame, home: tuple[str, tensor.Market | None], cal: pd.DataFrame,
                 shifts: np.ndarray, t: dict) -> float:
    """P7's denominator, §4.3: the main's e on oos1 (V2), the same `rules.per_market` e as every e_j."""
    feed, priced = home
    if priced is None:
        return np.nan
    one = tensor.build({feed: trades}, {feed: priced}, cal, shifts, t["shift_step"], t["judge_on"])
    return float(rules.per_market(one, rules.windows(cal)["V2"])["e"].iloc[0])


def _net_t(trades: dict[str, pd.DataFrame]) -> float:
    """The t of the weekly net P/L (SQX's) summed over the markets: annotated, judges nothing."""
    weeks = [stat.weekly(m["Profit/Loss"].to_numpy(), m["Close time"].to_numpy().astype("datetime64[D]"))
             for m in trades.values() if len(m)]
    return stat.t(pd.concat(weeks, axis=1).sort_index().fillna(0.0).sum(axis=1).to_numpy()) if weeks else np.nan


def _clean(x: object) -> object:
    """A JSON-safe copy: NaN and inf become null, numpy scalars plain numbers."""
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else None
    return x.item() if isinstance(x, np.generic) else x


_SHARED: dict = {}     # set by `run` before the fork, read by `_strategy` in the workers


def _strategy(s: str) -> tuple[dict, list[pd.DataFrame], object, list]:
    """One strategy's verdict row, market rows, d_y and draws rows, in a worker that inherited `run`'s inputs."""
    g = _SHARED
    t, inputs, feeds, found, by, empty = g["t"], g["inputs"], g["feeds"], g["found"], g["by"], g["empty"]
    mine = {f: by.get((s, f), empty).reset_index(drop=True) for f in feeds}
    one = tensor.build(mine, g["fixed"], g["cal"], g["shifts"], t["shift_step"], t["judge_on"])
    got = rules.evaluate(one, g["cal"], t, _e_principal(by.get((s, g["home"][0]), empty).reset_index(drop=True),
                                                       g["home"], g["cal"], g["shifts"], t), g["role"])
    kept = records.rows(one, rules.windows(g["cal"]), got, s, inputs["identity"].get(s) or "", t["seed"])
    valid, listed = len(feeds), len(found)
    verdict = {"strategy": s, "markets": listed, "markets_valid": valid,
               "invalid_fraction": 1 - valid / listed, "fixed_distance": g["distance"][s],
               "freq_off": g["off"][s], "freq_off_fraction": g["off"][s] / valid,
               "net_t_pooled": _net_t(mine), **got["verdict"]}
    rows = [got["markets"].assign(strategy=s, z_freq=g["z_freq"].loc[s].to_numpy(), valid=True,
                                  invalid_reason=""),
            pd.DataFrame([{"strategy": s, "market": r["market"], "valid": False,
                           "invalid_reason": r["invalid_reason"]} for r in found if not r["valid"]])]
    return verdict, rows, got["d_y"], kept


def run(project: str, databank: str, asset: str, export: str, out: Path,
        overrides: list[str] | None = None) -> Travelled:
    """Judge an export's strategies on the other markets and write the three files.

    Args:
        project, databank, asset, export: As `load.load` takes them.
        out: A folder that holds no result; it is created. Never the live study's reports folder.
        overrides: Dotted `--set` overrides of config.yaml.

    Returns:
        `verdict` and `markets` (the frames written), `checks` (§7.1's row per market) and `draws`.
        Written: `verdict.csv`, `markets.parquet`, `distribuciones.parquet` and `crossmarket.json` (config, windows, the
        §7.1 table and each strategy's d_y).
    """
    _free(out, project, databank, export)
    cfg = config.load(overrides)
    t, params = cfg["travel"], sizing.doctrine()
    inputs = load.load(project, databank, asset, export)
    cuts = cells.cuts(asset)
    found, ready = _checks(inputs, cfg, params)
    feeds, strategies = list(ready), inputs["strategies"]
    bars = [b for b, _ in ready.values()]
    cal = cells.table(min(b.index[0] for b in bars), max(b.index[-1] for b in bars), cuts,
                      t["shift_unit"], t["shift_step"])
    shifts = shift.draws(cal, t["seed"], t["draws"])
    with np.errstate(divide="ignore"):      # lots on a flat bar are inf: `usable` never sizes there
        fixed = {f: tensor.market(b, c, params, cal, t["validity"]["flat_atr_fraction"])
                 for f, (b, c) in ready.items()}
    left = []       # the (market, cell) pairs the probe leaves out: §7.1 per cell, bars only
    for f, m in fixed.items():
        gone = tensor.exclude(m, cal, shifts, t["shift_step"], t["validity"]["max_displaced_share"])
        left += [{"market": f, "cell": f"{cal['start'][i]:%Y-%m-%d} {cal['window'][i]}",
                  "displaced_share": float(m["share"][i])} for i in np.flatnonzero(gone)]  # pyright: ignore[reportTypedDictNotRequiredAccess]  # tensor.exclude sets it in this loop
    by = {k: g for k, g in inputs["trades"].groupby(["strategy", "Symbol"], observed=True)}
    empty = inputs["trades"].iloc[:0]
    z_freq, off, counts = _frequency(inputs, strategies, feeds, cuts, t, by)
    distance = units.fixed(project, strategies, inputs["identity"])
    home = _home(inputs, params, cal, t)
    role = rules.roles(feeds, markets.classify(asset), sources.family_of(project), assetmarkets.expected_sign())
    _SHARED.update(inputs=inputs, feeds=feeds, found=found, by=by, empty=empty, fixed=fixed, cal=cal,
                   shifts=shifts, t=t, params=params, home=home, role=role, distance=distance,
                   z_freq=z_freq, off=off)
    # One strategy per task: the work is the tensor, and nothing is drawn but `shifts`, made above.
    done = dict(fanout.run(_strategy, {s: len(inputs["trades"]) for s in strategies}, fanout.CORES))
    verdict, rows, series, kept = [], [], {}, []
    for s in strategies:
        v, r, d_y, k = done[s]
        verdict.append(v)
        rows += r
        series[s] = d_y
        kept += k
    out.mkdir(parents=True, exist_ok=True)
    verdict, rows = cast(pd.DataFrame, pd.DataFrame(verdict)[VERDICT]), cast(pd.DataFrame, pd.concat(rows, ignore_index=True)[MARKETS])
    verdict.to_csv(out / "verdict.csv", index=False)
    rows.to_parquet(out / "markets.parquet", index=False)
    draws.save(out, kept)
    (out / "crossmarket.json").write_text(json.dumps(_clean({
        "config": t, "cuts": {k: str(v) for k, v in cuts.items()}, "cells": len(cal),
        "checks": found, "excluded": left, "d_y": series, "project": project, "databank": databank,
        "export": export, "asset": asset}), indent=1), encoding="utf-8")
    return Travelled(verdict=verdict, markets=rows, checks=found, draws=kept)
