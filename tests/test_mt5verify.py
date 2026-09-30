#!/usr/bin/env python3
"""MT5 Bridge's step 26 on known answers: the clock, the five rows, a firm's costs and the project it writes."""

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata
from core.datapaths import projects_backup
from mt5 import tester
from mt5.verify import conditions, firms, judge, mt5side
from sqx.projects import mt5verify

DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
FEED = "XAUUSD_DukasM1_Infinox"
COSTS = {"defaultSpread": 41.0, "defaultSlippage": 0,
         "commission": {"method": "PercentageBased", "value": 0.0014},
         "swap": {"type": "points", "long": -90.35, "short": -4.2, "triple_swap_on": "WEDNESDAY",
                  "rollout_hour": "23:00"}}


def trades(n: int, seed: int) -> pd.DataFrame:
    """n trades 37 h apart, alternating sides, P&L drawn around a small edge."""
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp("2025-01-02 10:00")
    return pd.DataFrame([{"Type": "Buy" if i % 2 else "Sell",
                          "Open time": t0 + pd.Timedelta(hours=37 * i), "Open price": 2000.0,
                          "Size": 1.0, "Close time": t0 + pd.Timedelta(hours=37 * i + 5),
                          "Close price": 2001.0, "Profit/Loss": float(rng.normal(20, 100))}
                         for i in range(n)])


def judged(failures: list[str]) -> None:
    """A copy an hour late passes with the hour read; a scrambled P&L fails rows 2-3; nothing on
    one side fails row 1 and never raises."""
    cfg = firms.config()
    sqx = trades(60, 1)
    late = judge.shifted(sqx, 1)
    late["Profit/Loss"] += np.random.default_rng(2).normal(0, 1, len(late))
    got = judge.firm_result("ftmo", sqx, late, "H1", 100000, cfg, "XAUUSD")["summary"]
    if got["state"] != "pass" or got["clock_h"] != 1:
        failures.append(f"una copia una hora tarde no pasa con reloj +1: {got}")
    scrambled = late.copy()
    scrambled["Profit/Loss"] = np.random.default_rng(3).normal(20, 100, len(late))
    got = judge.firm_result("ftmo", sqx, scrambled, "H1", 100000, cfg, "XAUUSD")["summary"]
    if got["state"] != "fail" or got["row_1"] != 1.0 or got["row_2"] <= 0.05:
        failures.append(f"un P&L barajado no falla la fila 2 con todo emparejado: {got}")
    got = judge.firm_result("ftmo", sqx, sqx.iloc[:0], "H1", 100000, cfg, "XAUUSD")["summary"]
    if got["state"] != "fail" or got["row_1"] != 0.0:
        failures.append(f"sin operaciones en MT5 no falla la fila 1: {got}")


def priced(failures: list[str]) -> None:
    """FTMO's gold as its server gave it on 2026-09-29, in SQX's units; Hantec refused on gold."""
    data = assetdata.load("XAUUSD")
    info = {"name": "XAUUSD", "spread": 41, "point": 0.01, "swap_mode": 1, "swap_long": -90.35,
            "swap_short": -4.2, "swap_rollover3days": 3}
    got, _ = conditions.for_sqx(data, "ftmo", info, 0)
    if got != COSTS:
        failures.append(f"los costes de FTMO en unidades de SQX: {got}")
    try:
        conditions.for_sqx(data, "hantec", {**info, "name": "XAUUSD.h"}, 0)
        failures.append("Hantec sin comisión confirmada en el oro no se rechaza")
    except conditions.Refused:
        pass
    try:
        conditions.for_sqx(data, "ftmo", {**info, "swap_mode": 2}, 0)
        failures.append("un swap en la divisa base (modo 2) no se rechaza")
    except conditions.Refused:
        pass


def written(failures: list[str]) -> None:
    """On a copy of the frozen donor: only the firms' retests and the export on, each at its
    firm's costs over the window, the strategy's own settings, no cross-check."""
    cfg = firms.config()["sqx"]
    with tempfile.TemporaryDirectory() as tmp:
        cfx = Path(tmp) / "project.cfx"
        shutil.copy(DONOR, cfx)
        done = mt5verify.configure(cfx, FEED, ("2025-01-01", "2026-09-01"),
                                   {"ftmo": COSTS, "hantec": {**COSTS, "defaultSpread": 26.0}},
                                   Path(tmp) / "mq5", cfg,
                                   {"method": "FixedSize", "params": {"Size": "0.1"}})
        with zipfile.ZipFile(cfx) as z:
            config = z.read("config.xml").decode()
            tasks = {r["firm"]: z.read(r["member"]).decode() for r in done["tasks"]}
            save = z.read(mt5verify.SAVE_MEMBER).decode()
    on = re.findall(r'<Task\b[^>]*active="true"[^>]*title="([^"]*)"', config)
    if sorted(on) != ["MQL5", "MT5 FTMO", "MT5 HANTEC"]:
        failures.append(f"tareas activas: {on}")
    for firm, spread in (("ftmo", "41.0"), ("hantec", "26.0")):
        text = tasks[firm]
        if f'<Chart symbol="{FEED}" timeframe="M30" spread="{spread}"' not in text:
            failures.append(f"{firm}: el spread de su empresa no está en su Setup")
        if 'dateFrom="2025.01.01" dateTo="2026.09.01"' not in text:
            failures.append(f"{firm}: la ventana no está en su Setup")
        on = re.findall(r'<Method type="(\w+)" use="true"', text.split("</MoneyManagement>")[0])
        size = re.search(r'<Param key="Size" className="FixedSize">([^<]*)', text).group(1)
        if on != ["FixedSize"] or size != "0.1" or '<CrossChecks use="false"' not in text:
            failures.append(f"{firm}: no opera el FixedSize 0.1 de la estrategia ({on}, {size}) "
                            "o deja un cross-check")
        if f'value="MT5Verify_{firm}"' not in text:
            failures.append(f"{firm}: no escribe en su databank")
    if f'<SaveSourceCode type="{cfg["generator"]}">true' not in save:
        failures.append("la exportación no pide el generador de MQL5")


def ini(failures: list[str]) -> None:
    """The tester's ini names the account in a [Common] section before [Tester]."""
    text = tester._ini("AlgoProject\\X.ex5", "XAUUSD", "H1", "2025-01-01", "2026-09-01",
                       "ohlc_m1", 100000, 50, "r", {"login": 541350656, "server": "FTMO-Server4"})
    if not text.startswith("[Common]\r\nLogin=541350656\r\nServer=FTMO-Server4\r\n[Tester]"):
        failures.append(f"el ini no cambia de cuenta: {text[:80]!r}")


def lots(failures: list[str]) -> None:
    """The EA's own sizing is replaced by the strategy's fixed lot, or refused when it cannot be."""
    source = "input bool UseMoneyManagement = true;\ninput double mmLotsIfNoMM = 0.01;\n"
    if mt5side.fixed_lots(source, "0.1") != ("input bool UseMoneyManagement = false;\n"
                                             "input double mmLotsIfNoMM = 0.1;\n"):
        failures.append("el EA no queda en el lote fijo de la estrategia")
    try:
        mt5side.fixed_lots("input double mmLotsIfNoMM = 0.01;\n", "0.1")
        failures.append("un EA sin UseMoneyManagement no se rechaza")
    except SystemExit:
        pass


def main() -> None:
    """Run the five checks."""
    failures = []
    for check in (judged, priced, written, ini, lots):
        check(failures)
    print("\n".join(failures) or
          "ok: el reloj se lee de las operaciones (+1 h), un P&L barajado falla la fila 2 y un "
          "lado vacío la 1; FTMO se traduce a unidades de SQX y Hantec sin comisión confirmada "
          "se rechaza; el proyecto solo enciende las dos empresas y la exportación, cada una a "
          "sus costes, con el FixedSize de la estrategia; el ini del tester cambia de cuenta; el EA "
          "queda en el lote fijo de la estrategia")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
