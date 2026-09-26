#!/usr/bin/env python3
"""Write the additional-markets cross-check from assets/: which markets, when, at what cost."""

import argparse
import re
import zipfile
from pathlib import Path
from datetime import date

from core.assetdata import doctrine, load, markets, sqx_settings, symbols
from sqx.projects.configure import running_install
from sqx.projects.crosschecks import member_of, silence
from sqx.projects.setups import span
from sqx.projects.stage import own

TITLE = "Retest Markets - Family"     # the donor's additional-markets task

SETUPS = re.compile(r"(<RetestOnAdditionalMarkets\b[^>]*>\s*<Settings>\s*)"
                    r"<Setups\b[^>]*>.*?</Setups>", re.S)
# What the extra market takes from the main test instead of from its own <Setup>. The costs
# and the window are its own — that is the whole point — and the shape of the test is shared.
INHERIT = ('timeframe="true" dates="false" subcharts="false" precision="true" distance="true" '
           'spread="false" slippage="false" commissions="false" swap="false" session="true"')


def feed_owner(feed: str) -> str | None:
    """Which asset file declares a feed.

    Args:
        feed: SQX feed name, e.g. "XAGUSD_DukasM1_Infinox".

    Returns:
        The asset name, or None when no file in assets/symbols/ carries that feed — which
        means its costs are undeclared and nothing may be authored for it.
    """
    return next((s for s in symbols() if feed in (load(s).get("feeds") or [])), None)


def window(main: dict, data_from: date | str, segment: str) -> tuple[str, str]:
    """The retest window for one extra market.

    Args:
        main: The main asset as load() returned it.
        data_from: First date the market has data, from `_markets.yaml`. A date, or the
            string "unknown".
        segment: The span `assets/_build.yaml` declares under `crossmarket.segment`.

    Returns:
        (dateFrom, dateTo) as YYYY.MM.DD. It runs from the start of the span — or from
        this market's own first bar when that is later — to its end. The whole history is
        used on purpose: this test asks whether the logic survives a different market, and
        cutting it to the main asset's window throws away the years that would answer it.
    """
    start, end, _ = span(main, segment)
    if isinstance(data_from, date):
        start = max(start, f"{data_from:%Y.%m.%d}")
    return start, end


def one_market(feed: str, data: dict, segment: str, window_: tuple[str, str],
               precision: int, engine: str, timeframe: str) -> str:
    """One extra market as the <Setup> the cross-check runs it with.

    Args:
        feed: SQX feed name.
        data: That market's asset file, as load() returned it.
        segment: Which segment's costs to charge it.
        window_: (dateFrom, dateTo).
        precision: testPrecision.
        engine: Backtest engine name.
        timeframe: The project's timeframe.

    Returns:
        The <Setup> element. One Setup holds one spread and one slippage while the window
        spans both segments, so the OOS figures are charged — the market that has to
        surprise us is never given the cheaper price.
    """
    s = sqx_settings(data, segment)
    c, sw = s["commission"], s["swap"]
    methods = "".join(
        f'<Method type="{m}" use="{str(m == c["method"]).lower()}"><Params>'
        f'<Param key="{"Commission" if m == "SizeBased" else "CommissionPct"}" '
        f'className="{m}">{c["value"] if m == c["method"] else 0}</Param></Params></Method>'
        for m in ("SizeBased", "PercentageBased"))
    return (f'<Setup dateFrom="{window_[0]}" dateTo="{window_[1]}" testPrecision="{precision}" '
            f'session="No Session" slippage="{s["defaultSlippage"]}" minDist="10" '
            f'engine="{engine}">'
            f'<Chart symbol="{feed}" timeframe="{timeframe}" spread="{s["defaultSpread"]}" />'
            f"<Commissions>{methods}</Commissions>"
            f'<Swap use="true" type="{sw["type"]}" long="{sw["long"]}" short="{sw["short"]}" '
            f'tripleSwapOn="{sw["triple_swap_on"]}" rolloutHour="{sw["rollout_hour"]}" />'
            f"<MainTestValues {INHERIT} /></Setup>")


def chosen(symbol: str, categories: tuple = ("family", "structural")) -> list[dict]:
    """The declared cross-check markets of one asset, with where their costs would come from.

    Args:
        symbol: The main asset.
        categories: Which categories of `_markets.yaml` to take.

    Returns:
        One row per market: its feed, category, first date, and the asset file that
        declares its costs — None when there is none. The list is what `_markets.yaml`
        fixed before any result was looked at; nothing here chooses a market.
    """
    cats = markets(symbol).get("categories") or {}
    return [{"feed": m["feed"], "category": cat, "data_from": m.get("data_from"),
             "costs_from": feed_owner(m["feed"])}
            for cat in categories for m in cats.get(cat) or []]


def set_markets(text: str, symbol: str, timeframe: str,
                categories: tuple = ("family", "structural")) -> tuple[str, list, list, int]:
    """Turn the additional-markets cross-check on and give it its markets.

    Args:
        text: A task XML.
        symbol: The main asset.
        timeframe: The project's timeframe.
        categories: Which categories of `_markets.yaml` to include.

    Returns:
        The task, the markets written, the ones that could not be — because no file in
        assets/ declares their costs — and how many acceptance conditions were silenced. A
        market in the second list is NOT written: SQX would happily run it at the default
        spread of whatever instrument it resolves to, and a cross-market result at an
        invented cost is worse than no result. The window and the costs segment come from
        `crossmarket:` in the doctrine, not from an argument: they are the same question
        for every asset and a run at a window nobody declared is unattributable.
    """
    d = doctrine()
    study = d["crossmarket"]
    main = load(symbol)
    costs = span(main, study["segment"])[2]
    used, blocked = [], []
    for m in chosen(symbol, categories):
        if not m["costs_from"]:
            blocked.append(m)
            continue
        used.append(m | {"window": window(main, m["data_from"], study["segment"])})
    if not used:
        return text, used, blocked, 0
    body = "".join(one_market(m["feed"], load(m["costs_from"]), costs, m["window"],
                              study["precision"], d["engine"], timeframe) for m in used)
    text = SETUPS.sub(rf'\g<1><Setups detailed="true">{body}</Setups>', text, count=1)
    text = re.sub(r'(<RetestOnAdditionalMarkets\b[^>]*?)use="[^"]*"',
                  r'\g<1>use="true"', text, count=1)
    if study["conditions"]:
        raise SystemExit("`crossmarket.conditions` de assets/_build.yaml ya no esta vacio: "
                         "esta prueba es una medicion, no una puerta, y escribir condiciones "
                         "no esta implementado. Quitalas o dilo explicitamente.")
    # Every condition of the task, not only this check's: 🔬 2026-09-25 a clone carried live
    # conditions elsewhere in the task (the OOS copy three, with DeleteFailedStrategies true),
    # and one live condition under evaluateAll="false" makes SQX skip the extra blocks.
    text, silenced = silence(text)
    return text, used, blocked, silenced


def main() -> None:
    """Report an asset's cross-check markets, or write them into one task of a project."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol")
    ap.add_argument("--cfx", type=Path, help="write them into this project instead of reporting")
    ap.add_argument("--task", help="task XML file to write into; by default the one titled "
                                   "`Retest Markets - Family`")
    ap.add_argument("--timeframe", help="the project's timeframe; required with --cfx")
    ap.add_argument("--categories", default="family,structural")
    a = ap.parse_args()
    cats = tuple(a.categories.split(","))

    if not a.cfx:
        for m in chosen(a.symbol, cats):
            w = window(load(a.symbol), m["data_from"], doctrine()["crossmarket"]["segment"])
            where = m["costs_from"] or "⚠️ NINGÚN fichero de assets/symbols/ declara este feed"
            when = "" if isinstance(m["data_from"], date) else "  ⚠️ data_from sin averiguar"
            print(f"{m['feed']:30} {m['category']:11} {w[0]} a {w[1]}   costes: {where}{when}")
        return

    held = running_install(a.cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al salir. "
                         f"Paralo: bin/sqx-worker.sh --role {held} stop")
    with zipfile.ZipFile(a.cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    a.task = a.task or member_of(members["config.xml"].decode("utf-8"), TITLE)
    text, used, blocked, silenced = set_markets(members[a.task].decode("utf-8"), a.symbol,
                                               a.timeframe, categories=cats)
    if blocked:
        raise SystemExit("sin escribir nada — estos mercados no tienen costes declarados en "
                         "assets/symbols/: " + ", ".join(m["feed"] for m in blocked)
                         + ".\nCrea su fichero o dime sus costes; no se copian del maestro ni "
                         "se inventan (regla dura 5).")
    members[a.task] = text.encode("utf-8")
    with zipfile.ZipFile(a.cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    for m in used:
        print(f"  {m['feed']:30} {m['category']:11} {m['window'][0]} a {m['window'][1]}")
    print(f"{silenced} condiciones de aceptacion apagadas — esto es evidencia, no un filtro")
    print(own(a.cfx, "crossmarket"))


if __name__ == "__main__":
    main()
