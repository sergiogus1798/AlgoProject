#!/usr/bin/env python3
"""Onboard an asset: its segments, spreads, slippage, commission, swap and MC Retest range, by the owner's rules.

The whole cost «mini-study» of 2026-09-27 as one command: the Darwinex spread per segment (measured
where there are ticks, modelled back by `onboard.<kind>.model`, times the safety factor), slippage
at half of it, the owner's default commission and swap for the kind of asset, the triple-swap
night, and the MC Retest's spread range from the real dispersion. Prints the plan; with --write it
creates or updates the asset through `core.assetwrite` — the only module of this study that writes
`assets/`, and only when the owner asked for it (the `/asset-onboard` skill).
"""

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from core import assetwrite
from core.assetdata import SYMBOLS, load, policy, window
from core.assets import report
from core.assetyaml import read, write
from studies.data.spread import fundedswap, inputs, measure, registry, verdict

CONFIG = Path(__file__).with_name("config.yaml")
HALVES = {"build": "is", "oos1": "oos", "oos2": "oos2"}


def segments(rules: dict, start: date) -> dict:
    """The kind's segments as `_policy.yaml` writes them; `build: data` starts with the data."""
    s = rules["segments"]
    first = start if s["build"] == "data" else max(pd.Timestamp(f"{s['build']}-01-01").date(), start)
    return {"build": {"from": first, "to": s["build_to"]},
            "oos1": {"from": s["oos1"][0], "to": s["oos1"][1]},
            "oos2": {"from": s["oos2"][0], "to": s["oos2"][1]}}


def _oos1_price(m: pd.DataFrame, oos1_window: tuple) -> float:
    """The reference price for a `no_forex` unit conversion (owner, 2026-09-29): the MEDIAN
    price of the OOS1 segment being charged, not the last close — a last-close reference swings
    the converted % by up to 5× against what the tested window actually pays (OPEN.md #36).

    Args:
        m: `inputs.minutes()`'s tick-derived minute table, with `bid_close`.
        oos1_window: (dateFrom, dateTo) in epoch ms, from `windows["oos1"]`.

    Returns:
        The median `bid_close` inside the window; the last close when the ticks do not
        reach that far back (a brand-new onboard with no OOS1 ticks yet).
    """
    a, b = pd.Timestamp(oos1_window[0], unit="ms"), pd.Timestamp(oos1_window[1], unit="ms")
    part = m["bid_close"][(m.index >= a) & (m.index < b)]
    return float(part.median()) if len(part) else float(m["bid_close"].iloc[-1])


def plan(symbol: str, kind: str, bars: str, ticks: str, cfg: dict) -> dict:
    """Everything the asset should carry, computed and not written."""
    rules, factor = cfg["onboard"][kind], cfg["safety"]["factor"]
    inst = registry.instrument(bars)
    tick, start = inst["tick_size"], registry.data_range(bars)[0]
    segs = segments(rules, start)
    windows = {k: window({"symbol": symbol, "segments": segs}, k) for k in segs}
    m, vol = inputs.minutes(ticks), inputs.volatility(bars)
    days = measure.days(m, vol, cfg["day"]["min_minutes"])
    yearly = measure.yearly(m, tick)
    errors = verdict.validate(days, cfg["model"]["candidates"], cfg["model"]["split"])
    name = rules["model"] or verdict.choose(
        verdict.constancy(yearly, "pb media", cfg["constancy"]["tolerance"]), errors)
    daily = verdict.reconstruct(days, vol, name)
    points = daily["rel"] * daily["price"] / tick
    per = {k: round(float(points[(daily.index >= pd.Timestamp(a, unit="ms"))
                                  & (daily.index < pd.Timestamp(b, unit="ms"))].mean() * factor), 2)
           for k, (a, b) in windows.items()}
    forex = kind == "forex"
    # One per segment for every kind (owner, 2026-09-30): forex used to get one mean.
    spreads = {f"spread_{HALVES[k]}": v for k, v in per.items()}
    slips = {f"slippage_{HALVES[k]}": round(v / 2, 2) for k, v in per.items()}
    price = _oos1_price(m, windows["oos1"])
    usd = cfg["onboard"]["commission_usd_per_lot"]
    commission = (float(rules["commission"]) if rules["commission"] != "usd_per_lot"
                  else float(usd) if forex else round(usd / (inst["point_value"] * price) * 100, 6))
    if rules["swap"] == "funded_worst":   # owner, 2026-10-01: worst of the funded accounts, live
        swaps = (fundedswap.worst(symbol) if (SYMBOLS / f"{symbol}.yaml").exists()
                 and load(symbol).get("mt5") else {"pending": "sin `mt5:` en su ficha todavía"})
    elif rules["swap"] == "brokers":
        swaps = registry.broker_swaps(symbol, tick)
    else:
        swaps = {"long": float(rules["swap"][0]), "short": float(rules["swap"][1])}
    k = verdict.mc_multiples(days, name, [cfg["band"]["quantiles"][0], cfg["band"]["quantiles"][-1]])
    base = spreads["spread_is"]
    mc_spread, mc_slippage = mc_range(base, k, cfg["mc"])
    return {"symbol": symbol, "kind": kind, "class": "forex" if forex else "no_forex", "bars": bars,
            "ticks": ticks, "broker": registry.broker(bars), "instrument": inst, "segments": segs,
            "data": registry.data_range(bars), "model": name, "per_segment": per, "spreads": spreads,
            "slippage": slips, "commission": commission, "price": price, "swap": swaps,
            "triple_swap_on": rules["triple_swap_on"], "mc_spread": mc_spread,
            "mc_slippage": mc_slippage, "mc_multiples": k, "factor": factor}


def mc_range(base: float, k: dict, cfg: dict) -> tuple[tuple[float, float], tuple[float, float]]:
    """The MC Retest's spread and slippage ranges, widened to a floor SQX can actually draw from.

    Args:
        base: The build segment's own declared spread (points), what the multiples scale.
        k: `verdict.mc_multiples()`'s {"min", "max"} ratios.
        cfg: The `mc` section of config.yaml (`grain`, `min_steps`).

    Returns:
        `(spread, slippage)`, each a `(min, max)` in points. SQX's `RandomizeSpread` and
        `RandomizeSlippage` draw on a grain of about `cfg["grain"]` points (measured on
        USDJPY, `knowhow/costs/mc-retest-ranges.md`): a band narrower than `min_steps` of
        that grain gives too few distinct outcomes for the task to have a shape
        (`tarea_sin_dispersion`) — a low-spread pair's multiplicative band (≈0.65x-1.47x of a
        small `base`) is exactly where this bites. The band is widened around its own centre,
        never shifted, so the multiplicative quantiles still say what they said; a floor that
        would push the low end below zero pulls the whole band up instead, since a negative
        spread is not a thing SQX can draw. Slippage is declared as half the spread everywhere
        else in this module (`slips` above), so its range is exactly half of the (already
        floored) spread range — not floored again on its own, since halving it never worsens
        the same grain check for the spread task, which is the one seen jammed at ~35-39k in
        practice (2026-09-30 feedback §6).
    """
    lo, hi = base * k["min"], base * k["max"]
    floor = cfg["grain"] * cfg["min_steps"]
    if hi - lo < floor:
        mid = (lo + hi) / 2
        lo, hi = mid - floor / 2, mid + floor / 2
    if lo < 0:
        hi -= lo
        lo = 0.0
    spread = (round(lo, 2), round(hi, 2))
    slippage = (round(lo / 2, 2), round(hi / 2, 2))
    return spread, slippage


def apply(p: dict, cfg: dict, spread_only: bool) -> None:
    """Write the plan into `assets/` and teach the study the new asset's feeds.

    Args:
        p: plan().
        cfg: inputs.config().
        spread_only: Write only spreads, slippage and the MC Retest range, and leave the
            segments, commission and swap an existing asset already carries.
    """
    s, day = p["symbol"], "onboard " + pd.Timestamp.now().strftime("%Y-%m-%d")
    if not (SYMBOLS / f"{s}.yaml").exists():
        assetwrite.create(s, p["class"], p["broker"], p["bars"], None, p["instrument"])
    if not spread_only:
        for seg, bounds in p["segments"].items():
            for edge, value in bounds.items():
                assetwrite.set_value("policy", ["segments", s, seg, edge], value)
        assetwrite.set_value("policy", ["segments", s, "data"], {"from": p["data"][0], "to": p["data"][1]})
    how = f"× factor {p['factor']}, modelo `{p['model']}` donde no hay ticks ({p['ticks']})"
    assetwrite.rename_cost(s, "spread", "spread_is")        # a forex file before 2026-09-30
    for i, (f, v) in enumerate(p["spreads"].items()):
        assetwrite.set_cost(s, f, float(v), f"{day} — spread medio de Darwinex del tramo {how}. "
                            "studies.data.spread.onboard", after=list(p["spreads"])[i - 1])
    for i, (f, v) in enumerate(p["slippage"].items()):
        assetwrite.set_cost(s, f, float(v), f"{day} — la mitad del spread de su tramo, default del dueño.",
                            after=list(p["slippage"])[i - 1])
    if not spread_only:
        _commission_and_swap(p, cfg, day)
    assetwrite.set_value(s, ["mc_retest", "spread", "min"], float(p["mc_spread"][0]))
    assetwrite.set_value(s, ["mc_retest", "spread", "max"], float(p["mc_spread"][1]))
    assetwrite.set_value(s, ["mc_retest", "slippage", "min"], float(p["mc_slippage"][0]))
    assetwrite.set_value(s, ["mc_retest", "slippage", "max"], float(p["mc_slippage"][1]))
    doc = read(CONFIG)
    doc["assets"][s] = {"ticks": p["ticks"], "bars": p["bars"]}
    doc["band"]["assets"][s] = p["ticks"]
    if cfg["onboard"][p["kind"]]["model"]:
        doc["model"]["fixed"][s] = p["model"]
    write(CONFIG, doc)


def _commission_and_swap(p: dict, cfg: dict, day: str) -> None:
    """The owner's default commission, swap and triple-swap night for the kind of asset."""
    s = p["symbol"]
    assetwrite.set_cost(s, "commission", p["commission"], f"{day} — default del dueño para `{p['kind']}`: "
                        f"{cfg['onboard']['commission_usd_per_lot']} USD por lote ida y vuelta "
                        f"(en % al último precio Darwinex {p['price']:g} si no es forex; 0 en índices).")
    if "pending" in p["swap"]:
        print(f"swap NO escrito: {p['swap']['pending']} — fija `mt5:` y vuelve a correr --write")
    else:
        src = (f"media de {p['swap']['n']} brokers del registro de SQX" if "n" in p["swap"]
               else f"peor caso de {' y '.join(p['swap']['raw'])} leído hoy de sus servidores MT5 "
                    f"(puntos MT5 largo/corto {p['swap']['raw']}); cambia con los tipos, revisar"
               if "raw" in p["swap"] else "default del dueño, % anual")
        for f, k in (("swap_long", "long"), ("swap_short", "short")):
            assetwrite.set_cost(s, f, float(p["swap"][k]), f"{day} — {src}.")
    if p["triple_swap_on"] != policy()["swap"]["triple_swap_on"]:
        assetwrite.set_value(s, ["swap"], {"triple_swap_on": p["triple_swap_on"], "rollout_hour": "23:00"})


def main() -> None:
    """Plan an asset's costs and, with --write, put them in `assets/`."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbol", required=True, help="e.g. EURGBP")
    ap.add_argument("--kind", required=True, choices=["index", "metal", "forex"])
    ap.add_argument("--bars", default="", help="the Dukascopy M1 feed when there are several")
    ap.add_argument("--ticks", default="", help="the Darwinex tick feed when there are several")
    ap.add_argument("--write", action="store_true", help="write it; without it, only print")
    ap.add_argument("--spread-only", action="store_true",
                    help="existing asset: write spreads, slippage and MC range, keep segments, commission, swap")
    a = ap.parse_args()
    cfg = inputs.config([])
    found = registry.feeds(a.symbol)
    bars, ticks = a.bars or found["bars"], a.ticks or found["ticks"]
    bars, ticks = [bars] if isinstance(bars, str) else bars, [ticks] if isinstance(ticks, str) else ticks
    if len(bars) != 1 or len(ticks) != 1:
        raise SystemExit(f"{a.symbol}: feeds M1 {found['bars']}, TICK {found['ticks']} — "
                         "hace falta exactamente uno de cada: elige con --bars y --ticks")
    p = plan(a.symbol, a.kind, bars[0], ticks[0], cfg)
    rows = [("modelo del build", p["model"]), ("spread por tramo (puntos, × factor)", p["per_segment"]),
            ("spreads a declarar", p["spreads"]), ("slippage", p["slippage"]),
            ("comisión", p["commission"]), ("swap largo/corto", (p["swap"]["long"], p["swap"]["short"])),
            ("triple swap", p["triple_swap_on"]), ("MC Retest spread (puntos)", p["mc_spread"]),
            ("MC Retest slippage (puntos)", p["mc_slippage"]),
            ("  en múltiplos", {k: round(v, 2) for k, v in p["mc_multiples"].items()}),
            ("tramos", p["segments"]), ("instrumento", p["instrument"])]
    print(f"{a.symbol} ({a.kind}) — {p['bars']} + {p['ticks']}")
    print("\n".join(f"  {k:36} {v}" for k, v in rows))
    if a.write:
        apply(p, cfg, a.spread_only)
        print("\n" + report(a.symbol))
    else:
        print("\n(sin escribir: --write para aplicarlo)")


if __name__ == "__main__":
    main()
