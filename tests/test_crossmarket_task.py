#!/usr/bin/env python3
"""Step 9's task as `sqx.projects.crossmarket` writes it, on files (a project built into a
temp dir, no install): every extra market runs ITS OWN build..oos1 window — never a day of
its `oos2`, whatever the main asset's dates — at its own card's costs; every Setup of the
task, the main test included, is on `crossmarket.precision`; and every extra feed carries its
<Symbol>, <InstrumentInfo> and <Broker>, loading exactly the window its Setup trades."""

import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

from core.assetdata import doctrine, load, sqx_settings, symbols  # noqa: E402
from core.paths import ASSETS  # noqa: E402
from core.datapaths import projects_backup  # noqa: E402
from sqx.projects import builder, crossmarket, resources  # noqa: E402
from sqx.projects.crosschecks import member_of  # noqa: E402
from sqx.projects.setups import bounds  # noqa: E402

MAINS = yaml.safe_load((ASSETS / "_markets.yaml").read_text(encoding="utf-8"))
DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
SETUP = re.compile(r'<Setup dateFrom="([\d.]+)" dateTo="([\d.]+)" testPrecision="(\d)"[^>]*>'
                   r'<Chart symbol="([^"]+)"[^>]*spread="([^"]+)"')


def test_every_market_runs_its_own_window() -> None:
    """Whatever `_markets.yaml` lists today: no window leaves the market's own build..oos1."""
    segment = doctrine()["crossmarket"]["segment"]
    seen = 0
    for main in sorted(set(symbols()) & set(MAINS)):
        for m in crossmarket.chosen(main):
            if not m["costs_from"]:
                continue                    # a market with no card yet: skipped, never dated
            card = load(m["costs_from"])
            a, b = crossmarket.window(card, m["data_from"], segment)
            assert a >= bounds(card, "build")[0] and b == bounds(card, "oos1")[1], (main, m)
            assert b < bounds(card, "oos2")[0], (main, m["feed"], b)
            seen += 1
    assert seen


def configured(symbol: str, install: str) -> tuple[str, list]:
    """A workflow project of `symbol` built into `install`, its step-9 task forced to one-minute
    precision as an older project carries it, then configured: (the task, the markets)."""
    builder.worker_dir = lambda role: Path(install)
    done = builder.build(name=f"Test_fixture_cm_{symbol}", template=None, symbol=symbol,
                         role="custodian", timeframe="H1", strategies=50, minutes=5,
                         donor=DONOR, workflow=True, side="long")
    with zipfile.ZipFile(done["cfx"]) as z:
        task = z.read(member_of(z.read("config.xml").decode(), crossmarket.TITLE)).decode()
    task = re.sub(r'testPrecision="\d"', 'testPrecision="2"', task)
    text, used, blocked, _ = crossmarket.set_markets(task, symbol, "H1")
    assert used and all(not m["costs_from"] for m in blocked)    # only a market with no card
    assert not any(f'symbol="{m["feed"]}"' in text for m in blocked)
    return text, used


def test_task_on_files() -> None:
    """An index main (oos1 to 2023) and gold (to 2022), each with markets of the other kind."""
    for symbol in ("DAX40", "XAUUSD"):
        with tempfile.TemporaryDirectory(prefix="sqx-test-install-") as install:
            text, used = configured(symbol, install)
        assert set(re.findall(r'testPrecision="(\d)"', text)) == {"1"}, symbol
        assert 'RetestOnAdditionalMarkets use="true"' in text
        setups = {m.group(4): m.groups() for m in SETUP.finditer(text)}
        blocks = {m.group(1): m.group(0) for m in resources.SYMBOL.finditer(text)}
        held = text.split("<Resources>")[1]
        for m in used:
            card = load(m["costs_from"])
            a, b, _, _, spread = setups[m["feed"]]
            assert (a, b) == m["window"] and b == bounds(card, "oos1")[1], (symbol, m["feed"])
            assert float(spread) == sqx_settings(card, "oos1")["defaultSpread"], m["feed"]
            block = blocks[m["feed"]]                       # the feed is defined in the task
            instrument = re.search(r'<InstrumentInfo\b[^>]*?instrument="([^"]+)"', block)
            assert f'instrument="{instrument.group(1)}"' in held.split("<Instruments>")[1]
            broker = re.match(r'<Symbol\b[^>]*broker="([^"]+)"', block).group(1)
            assert f'<Broker id="{broker}"' in held
            day = lambda ms: f"{datetime.fromtimestamp(int(ms) / 1000, timezone.utc):%Y.%m.%d}"
            assert day(re.search(r'dateFrom="(\d+)"', block).group(1)) == a, m["feed"]
            assert day(int(re.search(r'dateTo="(\d+)"', block).group(1)) - 1) == b, m["feed"]


def test_the_study_cuts_each_market_to_its_own_window() -> None:
    """An export written with the main's dates: gold's 2023 trades (its oos2) are not read,
    an index's are (its oos1 runs to 2023); a straddler goes; an unknown feed is left whole."""
    import pandas as pd
    from studies.transfer.crossmarket import load as cm_load
    day = pd.Timestamp
    rows = [("XAUUSD_M1", "2022-06-01", "2022-06-02"), ("XAUUSD_M1", "2023-03-01", "2023-03-02"),
            ("XAUUSD_M1", "2022-12-30", "2023-01-02"), ("XAUUSD_M1", "2007-05-01", "2007-05-02"),
            ("DAX40_M1", "2023-03-01", "2023-03-02"), ("DAX40_M1", "2024-01-03", "2024-01-04"),
            ("NOPE_M1", "2025-01-01", "2025-01-02")]
    trades = pd.DataFrame({"Symbol": [r[0] for r in rows], "Open time": [day(r[1]) for r in rows],
                           "Close time": [day(r[2]) for r in rows]})
    kept = cm_load.within(trades, ["XAUUSD_M1", "DAX40_M1", "NOPE_M1"])
    assert list(kept.index) == [0, 4, 6], list(kept.index)


if __name__ == "__main__":
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok", name)
