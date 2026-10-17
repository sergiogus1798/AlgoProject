#!/usr/bin/env python3
"""MT5 Bridge's step 26 on known answers: the clock, the five rows, a firm's costs and the project it writes."""

import re
import shutil
import sys
import tempfile
import zipfile
from unittest import mock
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import assetdata
from core.datapaths import projects_backup
from mt5 import compare, guard, tester
from mt5.verify import conditions, firms, judge, mt5side, sizing
from sqx.projects import cfxio, mt5verify
from sqx.projects.resources import definitions, main_feed, one_task

DONOR = projects_backup("XAUUSD_base_2026-09-21") / "project.cfx"
FEED = "XAUUSD_M1"
COSTS = {
    "defaultSpread": 41.0,
    "defaultSlippage": 0,
    "commission": {"method": "PercentageBased", "value": 0.0014},
    "swap": {
        "type": "points",
        "long": -90.35,
        "short": -4.2,
        "triple_swap_on": "WEDNESDAY",
        "rollout_hour": "23:00",
    },
}


def trades(n: int, seed: int) -> pd.DataFrame:
    """n trades 37 h apart, alternating sides, P&L drawn around a small edge."""
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp("2025-01-02 10:00")
    pnl = rng.normal(20, 100, n)
    return moved(
        pd.DataFrame(
            [
                {
                    "Type": "Buy" if i % 2 else "Sell",
                    "Open time": t0 + pd.Timedelta(hours=37 * i),
                    "Open price": 2000.0,
                    "Size": 1.0,
                    "Close time": t0 + pd.Timedelta(hours=37 * i + 5),
                    "Profit/Loss": float(pnl[i]),
                }
                for i in range(n)
            ]
        )
    )


def moved(frame: pd.DataFrame) -> pd.DataFrame:
    """Close prices that move exactly the trade's P&L at `INST`'s point value: the criteria
    read the price move (`mt5.compare.in_points`), not the booked USD."""
    side = np.where(frame["Type"] == "Buy", 1.0, -1.0)
    return frame.assign(
        **{
            "Close price": frame["Open price"]
            + side * frame["Profit/Loss"] / (INST["point_value"] * frame["Size"])
        }
    )


INST = {"tick_size": 0.01, "point_value": 100.0}


def judged(failures: list[str]) -> None:
    """A copy an hour late passes with the hour read; a scrambled P&L fails rows 2-3; nothing on
    one side fails row 1 and never raises."""
    cfg = firms.config()
    sqx = trades(60, 1)
    late = judge.shifted(sqx, 1)
    late["Profit/Loss"] += np.random.default_rng(2).normal(0, 1, len(late))
    late = moved(late)
    got = judge.firm_result(
        "ftmo", sqx, late, "H1", 100000, cfg, "XAUUSD", INST, ("EETUS", "EETUS")
    )["summary"]
    if got["state"] != "pass" or got["clock_h"] != 1:
        failures.append(f"una copia una hora tarde no pasa con reloj +1: {got}")
    scrambled = late.copy()
    scrambled["Profit/Loss"] = np.random.default_rng(3).normal(20, 100, len(late))
    scrambled = moved(scrambled)
    got = judge.firm_result(
        "ftmo", sqx, scrambled, "H1", 100000, cfg, "XAUUSD", INST, ("EETUS", "EETUS")
    )["summary"]
    if got["state"] != "fail" or got["row_1"] != 1.0 or got["row_2"] <= 0.05:
        failures.append(
            f"un P&L barajado no falla la fila 2 con todo emparejado: {got}"
        )
    got = judge.firm_result(
        "ftmo", sqx, sqx.iloc[:0], "H1", 100000, cfg, "XAUUSD", INST, ("EETUS", "EETUS")
    )["summary"]
    if got["state"] != "fail" or got["row_1"] != 0.0:
        failures.append(f"sin operaciones en MT5 no falla la fila 1: {got}")
    # row 1 is the worse of the two ways against 90 %: 60/66 = 90.9 % still passes, 60/67 does not
    extra = (
        trades(67, 1)
        .iloc[60:]
        .assign(
            **{
                "Open time": lambda f: f["Open time"] + pd.Timedelta(days=900),
                "Close time": lambda f: f["Close time"] + pd.Timedelta(days=900),
            }
        )
    )
    got = judge.firm_result(
        "ftmo",
        sqx,
        pd.concat([sqx, extra], ignore_index=True),
        "H1",
        100000,
        cfg,
        "XAUUSD",
        INST,
        ("EETUS", "EETUS"),
    )["summary"]
    if got["state"] != "fail" or not got["row_1"] < 0.90:
        failures.append(f"7 operaciones de más en MT5 no fallan la fila 1: {got}")
    got = judge.firm_result(
        "ftmo",
        sqx.iloc[:20],
        sqx.iloc[:20],
        "H1",
        100000,
        cfg,
        "XAUUSD",
        INST,
        ("EETUS", "EETUS"),
    )["summary"]
    if got["state"] != "none":
        failures.append(
            f"menos operaciones de SQX que el mínimo no dan «sin veredicto»: {got}"
        )


def gapped(failures: list[str]) -> None:
    """MT5 has no trades in a month its server has no bars for: row 1 fails unless that month
    is left out of both sides; `holes` finds it from the tester's M1 bars per month."""
    cfg = firms.config()
    sqx = trades(60, 1)
    month = sqx["Open time"].dt.strftime("%Y-%m")
    hole = month.value_counts().index[0]
    mt5 = sqx[month != hole]
    args = ("H1", 100000, cfg, "XAUUSD", INST, ("EETUS", "EETUS"))
    bare = judge.firm_result("ftmo", sqx, mt5, *args)["summary"]
    got = judge.firm_result("ftmo", sqx, mt5, *args, gaps=[hole])["summary"]
    if bare["state"] != "fail" or got["row_1"] != 1.0 or got["excluded_sqx"] <= 0:
        failures.append(f"un mes sin barras no se excluye de la fila 1: {bare} {got}")
    per = {f"2024-{m:02d}": 40000 for m in range(1, 13)} | {"2024-06": 1200}
    if conditions.holes(per, ("2024-01-01", "2024-12-31")) != ["2024-06"]:
        failures.append("holes no encuentra junio con casi sin barras M1")
    if conditions.holes(per, ("2024-01-15", "2024-06-10")) != []:
        failures.append("holes juzga meses parciales o inventa huecos")


def priced(failures: list[str]) -> None:
    """FTMO's gold as its server gave it on 2026-09-29, in SQX's units; Hantec at its card's
    commission; a firm whose commission the card does not have is refused."""
    data = assetdata.load("XAUUSD")
    info = {
        "name": "XAUUSD",
        "spread": 41,
        "point": 0.01,
        "swap_mode": 1,
        "swap_long": -90.35,
        "swap_short": -4.2,
        "swap_rollover3days": 3,
    }
    got, _ = conditions.for_sqx(data, "ftmo", info, 0)
    if got != COSTS:
        failures.append(f"los costes de FTMO en unidades de SQX: {got}")
    # Hantec's gold commission is confirmed since 2026-10-01 (encargo 55 §1.4); the5ers' is not
    got, _ = conditions.for_sqx(data, "hantec", {**info, "name": "XAUUSD.h"}, 0)
    if got["commission"] != {"method": "SizeBased", "value": 5.0}:
        failures.append(
            f"Hantec no lleva al oro su comisión de la ficha: {got['commission']}"
        )
    try:
        conditions.for_sqx(data, "the5ers", info, 0)
        failures.append("una empresa sin comisión confirmada en el oro no se rechaza")
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
        # as production arrives: the builder has already pointed the clone at the current feed
        members = cfxio.members(cfx)
        donor_feed, blocks = (
            main_feed(members, cfg["donor_members"][0]),
            definitions(None, FEED),
        )
        for m in cfg["donor_members"]:
            members[m] = one_task(
                members[m].decode("utf-8"), donor_feed, blocks
            ).encode("utf-8")
        cfxio.write(cfx, members)
        done = mt5verify.configure(
            cfx,
            FEED,
            ("2025-01-01", "2026-09-01"),
            {"ftmo": COSTS, "hantec": {**COSTS, "defaultSpread": 26.0}},
            Path(tmp) / "mq5",
            cfg,
            {"method": "FixedSize", "params": {"Size": "0.1"}},
        )
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
        on = re.findall(
            r'<Method type="(\w+)" use="true"', text.split("</MoneyManagement>")[0]
        )
        size = re.search(
            r'<Param key="Size" className="FixedSize">([^<]*)', text
        ).group(1)
        if (
            on != ["FixedSize"]
            or size != "0.1"
            or '<CrossChecks use="false"' not in text
        ):
            failures.append(
                f"{firm}: no opera el FixedSize 0.1 de la estrategia ({on}, {size}) "
                "o deja un cross-check"
            )
        if f'value="MT5Verify_{firm}"' not in text:
            failures.append(f"{firm}: no escribe en su databank")
    if f'<SaveSourceCode type="{cfg["generator"]}">true' not in save:
        failures.append("la exportación no pide el generador de MQL5")


def ini(failures: list[str]) -> None:
    """The tester's ini names the account in a [Common] section before [Tester]."""
    text = tester._ini(
        "AlgoProject\\X.ex5",
        "XAUUSD",
        "H1",
        "2025-01-01",
        "2026-09-01",
        "ohlc_m1",
        100000,
        50,
        "r",
        {"login": 541350656, "server": "FTMO-Server4"},
    )
    if not text.startswith(
        "[Common]\r\nLogin=541350656\r\nServer=FTMO-Server4\r\n[Tester]"
    ):
        failures.append(f"el ini no cambia de cuenta: {text[:80]!r}")


def protected(failures: list[str]) -> None:
    """A real account (fleet.vps.accounts, not in mt5_verify_logins) never reaches the terminal."""
    real = {"login": 8063673, "server": "HantecMarketsMU-MT5"}
    with (
        mock.patch.object(guard, "MT5_REAL_LOGINS", {8063673, 541350656}),
        mock.patch.object(guard, "MT5_VERIFY_LOGINS", {541350656}),
        mock.patch.object(tester.wine, "terminal_running", side_effect=AssertionError),
        mock.patch.object(tester.subprocess, "Popen", side_effect=AssertionError),
        mock.patch.object(firms, "MT5_ACCOUNTS", {"hantec": real}),
        mock.patch.object(firms, "names", return_value={"hantec": "X"}),
    ):
        try:
            tester.start(
                "E", "X", "H1", "2025-01-01", "2025-02-01", "ohlc_m1", 1, 1, real
            )
            failures.append("el tester arranca con una cuenta fondeada")
        except guard.Protected:
            pass
        except AssertionError:
            failures.append("la guarda actúa después de tocar el terminal")
        try:
            conditions.read("X", real)
            failures.append("conditions.read entra en una cuenta fondeada")
        except guard.Protected:
            pass
        if firms.usable("XAUUSD")["hantec"]["why"] != guard.WHY:
            failures.append(
                "la empresa protegida no sale como «sin cuenta de verificación»"
            )
        if guard.is_protected({"login": 541350656, "server": "S"}):
            failures.append("un login de mt5_verify_logins se rechaza")


def lots(failures: list[str]) -> None:
    """The EA's own sizing is replaced by the strategy's fixed lot, or refused when it cannot be."""
    source = (
        "input bool UseMoneyManagement = true;\ninput double mmLotsIfNoMM = 0.01;\n"
    )
    if mt5side.fixed_lots(source, "0.1") != (
        "input bool UseMoneyManagement = false;\ninput double mmLotsIfNoMM = 0.1;\n"
    ):
        failures.append("el EA no queda en el lote fijo de la estrategia")
    try:
        mt5side.fixed_lots("input double mmLotsIfNoMM = 0.01;\n", "0.1")
        failures.append("un EA sin UseMoneyManagement no se rechaza")
    except SystemExit:
        pass


def zoned(failures: list[str]) -> None:
    """the5ers' Asia/Jerusalem to the firms' EETUS: +1 h in the weeks the US has changed hour
    and Israel not yet (2024-03-15), 0 h in summer (2024-07-01); the skipped hour is NaT."""
    t = pd.DataFrame(
        {
            "Open time": pd.to_datetime(
                ["2024-03-15 10:00", "2024-07-01 10:00", "2024-03-29 02:30"]
            ),
            "Close time": pd.to_datetime(
                ["2024-03-15 12:00", "2024-07-01 12:00", "2024-03-29 04:00"]
            ),
        }
    )
    got = compare.to_zone(t, "Asia/Jerusalem", "EETUS")["Open time"]
    if list(got[:2]) != [
        pd.Timestamp("2024-03-15 11:00"),
        pd.Timestamp("2024-07-01 10:00"),
    ] or not pd.isna(got[2]):
        failures.append(f"Asia/Jerusalem → EETUS no convierte por fecha: {list(got)}")


def modes(failures: list[str]) -> None:
    """Encargo 61-4d: the two sizings, the size row, the loss-cap row and the combined state."""

    if mt5verify.mode_sizing("risk", 1000) != {
        "method": "FixedAmount",
        "params": {"RiskedMoney": "1000"},
    } or mt5verify.mode_sizing("lot", 1.0)["params"] != {"Size": "1"}:
        failures.append("mode_sizing no escribe FixedAmount/FixedSize")
    if not mt5verify.has_stop(Path(__file__).parent / "fixtures" / "strategy.sqx"):
        failures.append("has_stop no ve el stop de la estrategia con stop")
    src = (
        "input bool UseMoneyManagement = false;\ninput double mmRiskedMoney = 100.0;\n"
    )
    if mt5side.fixed_risk(src, "1000") != (
        "input bool UseMoneyManagement = true;\ninput double mmRiskedMoney = 1000;\n"
    ):
        failures.append("fixed_risk no fija el riesgo por operación")
    try:
        mt5side.fixed_risk("input double mmLots = 1;\n", "1000")
        failures.append("un EA sin mmRiskedMoney no se rechaza")
    except SystemExit:
        pass
    risk_rows(failures)


def risk_rows(failures: list[str]) -> None:
    """Rows 6 and 7 and the combination of the two modes' states."""
    from mt5.verify import ticks

    cfg = firms.config()
    th = cfg["thresholds"]
    try:
        sizing.require_cap({**th, "loss_cap_usd": None})
        failures.append("sin loss_cap_usd el juez no se niega")
    except SystemExit as why:
        if "mt5verify.loss_cap_usd" not in str(why):
            failures.append(f"el rechazo no nombra la clave: {why}")
    sqx = trades(60, 1)
    args = (
        "H1",
        100000,
        {**cfg, "thresholds": {**th, "loss_cap_usd": 1e9}},
        "XAUUSD",
        INST,
    )
    zone = ("EETUS", "EETUS")
    ok = judge.firm_result("ftmo", sqx, sqx, *args, zone, "risk")["summary"]
    if ok["state"] != "pass" or ok["row_6"] != 0 or "row_7" not in ok:
        failures.append(f"una copia exacta en modo riesgo no pasa filas 6 y 7: {ok}")
    capped = {**cfg, "thresholds": {**th, "loss_cap_usd": 1.0}}
    got = judge.firm_result(
        "ftmo", sqx, sqx, "H1", 100000, capped, "XAUUSD", INST, zone, "risk"
    )["summary"]
    if got["state"] != "fail":
        failures.append(f"una pérdida sobre el tope no falla la estrategia: {got}")
    halved = moved(
        sqx.assign(Size=sqx["Size"] * 0.8, **{"Profit/Loss": sqx["Profit/Loss"] * 0.8})
    )
    halved = halved.assign(Size=sqx["Size"] * 0.8)
    got = judge.firm_result("ftmo", sqx, halved, *args, zone)["summary"]
    if not got["row_6"] > th["size_gap_max_pct"]:
        failures.append(f"un tamaño un 20 % distinto no sube la fila 6: {got}")
    pieces = {"ftmo": {}}
    summaries = {"ftmo": {"state": "pass"}}
    ticks.keep_risk(pieces, summaries, "ftmo", sizing.no_stop("ftmo"))
    if (
        summaries["ftmo"]["state"] != "pass"
        or summaries["ftmo"]["risk_state"] != "skip"
    ):
        failures.append(f"sin SL el modo de riesgo no se salta: {summaries}")
    for lot in ("fail", "none"):
        summaries = {"ftmo": {"state": lot}}
        ticks.keep_risk(pieces, summaries, "ftmo", sizing.no_stop("ftmo"))
        if summaries["ftmo"]["state"] != lot:
            failures.append(f"sin SL el veredicto no es el del lote fijo ({lot})")
    summaries = {"ftmo": {"state": "pass"}}
    ticks.keep_risk(pieces, summaries, "ftmo", {"summary": {"state": "fail"}})
    if summaries["ftmo"]["state"] != "fail":
        failures.append("un modo fallido no falla la empresa")


class _Stop(Exception):
    """Raised by the stubbed first step after run.json, to end main() early."""


def _stop(*args: object, **kwargs: object) -> None:
    """Replace `say`: the first call comes right after run.json is written."""
    raise _Stop


def started(failures: list[str]) -> None:
    """main() creates its run folder before writing run.json (p70d: it did not, step 26 died)."""
    from mt5.verify import run as verifyrun

    tmp = Path(tempfile.mkdtemp())
    argv = ["run", "--strategy", str(tmp / "S 1.2.3(1).sqx"), "--from", "2020-01-01"]
    argv += ["--to", "2021-01-01", "--model", sorted(tester.MODELS)[0]]
    with (
        mock.patch.object(verifyrun, "RUNS", tmp / "verify"),
        mock.patch.object(verifyrun, "identify", lambda s: ("XAUUSD", "H1")),
        mock.patch.object(verifyrun, "say", _stop),
        mock.patch.object(verifyrun.mt5verify, "own_sizing", lambda s: None),
        mock.patch.object(verifyrun.assetdata, "load", lambda a: {}),
        mock.patch.object(verifyrun.sqxfile, "identity", lambda s: "x"),
        mock.patch.object(sys, "argv", argv),
    ):
        try:
            verifyrun.main()
        except (_Stop, FileNotFoundError):
            pass
    if not list((tmp / "verify").glob("*/run.json")):
        failures.append("main() no dejó run.json en la carpeta de la corrida")
    shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    """Run the checks."""
    failures = []
    for check in (
        judged,
        gapped,
        zoned,
        priced,
        written,
        ini,
        protected,
        lots,
        modes,
        started,
    ):
        check(failures)
    print(
        "\n".join(failures)
        or "ok: el reloj se lee de las operaciones (+1 h) y se convierte de zona fecha a fecha, un P&L barajado falla la fila 2 y un "
        "lado vacío la 1; FTMO se traduce a unidades de SQX, Hantec lleva su comisión y una empresa sin "
        "comisión confirmada se rechaza; el proyecto solo enciende las dos empresas y la exportación, cada una a "
        "sus costes, con el FixedSize de la estrategia; el ini del tester cambia de cuenta; una cuenta fondeada no llega al terminal; el EA "
        "queda en el lote fijo de la estrategia; los dos modos (1 lote y riesgo fijo) juzgan tamaño y tope de pérdida"
    )
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
