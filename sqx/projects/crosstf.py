#!/usr/bin/env python3
"""Write the cross-timeframe check: the same asset and costs, read on other timeframes."""

import argparse
import re
import zipfile
from pathlib import Path

from core.assetdata import doctrine, load, sqx_settings
from sqx.projects.crosschecks import silence_block
from sqx.projects.setups import span

BLOCK = re.compile(r"<RetestOnAdditionalMarkets\b.*?</RetestOnAdditionalMarkets>", re.S)
SETUPS = re.compile(r"(<RetestOnAdditionalMarkets\b[^>]*>\s*<Settings>\s*)"
                    r"<Setups\b[^>]*>.*?</Setups>", re.S)
MAIN_CHART = re.compile(r'<Chart symbol="([^"]+)" timeframe="([^"]+)"')
MAIN_DATES = re.compile(r'<Setup dateFrom="([^"]+)" dateTo="([^"]+)"')

# The timeframe is the ONLY thing a Setup owns here, and that is the whole design: the
# comparison is valid only if the blocks differ in nothing else. Contrast crossmarket.py,
# where the costs and the window are the market's own because the market IS the variable.
INHERIT = ('timeframe="false" dates="true" subcharts="false" precision="true" '
           'distance="true" spread="true" slippage="true" commissions="true" '
           'swap="true" session="true"')


def main_chart(text: str) -> tuple[str, str]:
    """The feed and timeframe the task's own main test runs on.

    Args:
        text: A task XML.

    Returns:
        (feed, timeframe). Read from the task rather than asked for, because this is the
        block every other block is compared against and guessing it wrong is silent.
    """
    found = MAIN_CHART.search(text)
    return found.group(1), found.group(2)


def one_timeframe(feed: str, data: dict, segment: str, timeframe: str,
                  precision: int, engine: str, window: tuple[str, str]) -> str:
    """One extra timeframe as the <Setup> the cross-check runs it with.

    Args:
        feed: SQX feed name -- the same one the main test uses.
        data: The asset file, as load() returned it.
        segment: Which segment's costs to write.
        timeframe: The timeframe this block reads.
        precision: testPrecision.
        engine: Backtest engine name.
        window: (dateFrom, dateTo). Written even though `MainTestValues` makes the main
            test's dates the live ones: SQX parses the attributes before it reads the
            mask, and a Setup without them fails the whole task with "Cannot load settings
            of Cross check 'RetestOnAdditionalMarkets'" (measured 2026-09-23).

    Returns:
        The <Setup> element. Its costs are written from assets/ so the file states what it
        charges, but `MainTestValues` makes the main test's values the live ones: the same
        instrument does not get a different spread for being resampled.
    """
    s = sqx_settings(data, segment)
    c, sw = s["commission"], s["swap"]
    methods = "".join(
        f'<Method type="{m}" use="{str(m == c["method"]).lower()}"><Params>'
        f'<Param key="{"Commission" if m == "SizeBased" else "CommissionPct"}" '
        f'className="{m}">{c["value"] if m == c["method"] else 0}</Param></Params></Method>'
        for m in ("SizeBased", "PercentageBased"))
    return (f'<Setup dateFrom="{window[0]}" dateTo="{window[1]}" '
            f'testPrecision="{precision}" session="No Session" '
            f'slippage="{s["defaultSlippage"]}" minDist="10" engine="{engine}">'
            f'<Chart symbol="{feed}" timeframe="{timeframe}" spread="{s["defaultSpread"]}" />'
            f"<Commissions>{methods}</Commissions>"
            f'<Swap use="true" type="{sw["type"]}" long="{sw["long"]}" short="{sw["short"]}" '
            f'tripleSwapOn="{sw["triple_swap_on"]}" rolloutHour="{sw["rollout_hour"]}" />'
            f"<MainTestValues {INHERIT} /></Setup>")


def main_window(text: str) -> tuple[str, str]:
    """The window the task's own main test runs on.

    Args:
        text: A task XML.

    Returns:
        (dateFrom, dateTo). This is the window the extra timeframes actually run, because
        `INHERIT` carries `dates="true"`: the dates written into their own <Setup> are
        inert and the main test's are the live ones. Reading it back is the only way to
        tell whether the task honours `crosstf.segment`.
    """
    found = MAIN_DATES.search(text)
    return found.group(1), found.group(2)


def set_timeframes(text: str, symbol: str,
                   timeframes: list[str] | None = None) -> tuple[str, list[str], int, str]:
    """Turn the cross-check on and give it one block per extra timeframe.

    Args:
        text: A task XML.
        symbol: The asset, for its declared costs.
        timeframes: The extra timeframes, in the order they become blocks 1, 2, ... None
            takes the doctrine's list.

    Returns:
        The task, the timeframe of every result block in order (block 0 first), how many
        acceptance conditions were silenced, and a warning about the window — empty when
        the task already runs the declared span. The block order is what
        `studies/transfer/crossTF/config.yaml` has to agree with, and getting it wrong prices
        every cell on the wrong bars with no error anywhere.
    """
    d = doctrine()
    study = d["crosstf"]
    if study["conditions"]:
        raise SystemExit("`crosstf.conditions` de assets/_build.yaml ya no esta vacio: esta "
                         "prueba es una medicion, no una puerta, y escribir condiciones no "
                         "esta implementado. Quitalas o dilo explicitamente.")
    timeframes = timeframes or study["timeframes"]
    feed, native = main_chart(text)
    data = load(symbol)
    start, end, costs = span(data, study["segment"])
    body = "".join(one_timeframe(feed, data, costs, tf, study["precision"], d["engine"],
                                 (start, end))
                   for tf in timeframes)
    text = SETUPS.sub(rf'\g<1><Setups detailed="true">{body}</Setups>', text, count=1)
    text = re.sub(r'(<RetestOnAdditionalMarkets\b[^>]*?)use="[^"]*"',
                  r'\g<1>use="true"', text, count=1)
    text, silenced = silence_block(text, "RetestOnAdditionalMarkets")
    live = main_window(text)
    warning = ("" if live == (start, end) else
               f"⚠️  la tarea corre {live[0]} a {live[1]}, no {start} a {end}. Las fechas de "
               f"los <Setup> extra son INERTES (MainTestValues dates=\"true\"): manda el test "
               f"principal. Configura la tarea con el segmento `{study['segment']}` o los "
               "timeframes se leeran sobre otra ventana.")
    return text, [native] + timeframes, silenced, warning


def main() -> None:
    """Write the cross-timeframe Setups into one task, and report the block order."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("symbol")
    ap.add_argument("--cfx", required=True, type=Path)
    ap.add_argument("--task", required=True, help="task XML file, e.g. Retest-Task3.xml")
    ap.add_argument("--timeframes", nargs="+",
                    help="los timeframes extra, en orden de bloque; por defecto, la doctrina")
    a = ap.parse_args()

    with zipfile.ZipFile(a.cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    text, blocks, silenced, warning = set_timeframes(members[a.task].decode("utf-8"), a.symbol,
                                                     a.timeframes)
    members[a.task] = text.encode("utf-8")
    with zipfile.ZipFile(a.cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)

    study = doctrine()["crosstf"]
    print(f"{a.task}: {len(blocks) - 1} timeframes anadidos, costes de {a.symbol} a "
          f"`{study['segment']}`")
    print(f"{silenced} condiciones de aceptacion apagadas — esto es evidencia, no un filtro")
    if warning:
        print(warning)
    print("\nPon esto en studies/transfer/crossTF/config.yaml, run.blocks:")
    print(f"  blocks: [{', '.join(blocks)}]")


if __name__ == "__main__":
    main()
