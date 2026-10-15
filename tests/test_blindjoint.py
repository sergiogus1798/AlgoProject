#!/usr/bin/env python3
"""Step 20 on mothers whose answer is known: noise and random traders name nobody, a planted edge is named, the pieces veto."""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engines.market import reprice
from ledger import gate
from engines.nulls import footprint as benchmark
from studies.closing.blindJoint import inputs, many, measure, one, readings, report
from studies.closing.blindJoint.pieces import PIECES

DAYS, K, SEEDS = 1250, 5, 20
CFG = inputs.config(["bootstrap.reps=500"])
# The random-trader case: a market that drifts up, 60 one-minute bars a day, a spread to pay.
MINUTES, TRADES, DRIFT, RUNS = 60, 150, 0.004, 10
COSTS = {
    "point_value": 1.0,
    "tick_size": 0.01,
    "spread": 0.05,
    "slippage": 0.0,
    "commission_method": "SizeBased",
    "rounds": True,
    "commission": 0.0,
    "swap_long": 0.0,
    "swap_short": 0.0,
    "triple": 4,
    "rollover": 23,
}


def mothers(
    states: dict[str, list[str]], missing: dict[str, list[str]] = None
) -> pd.DataFrame:
    """A population as pieces.population returns it, with each piece's state given.

    Args:
        states: {mother: four state words, in PIECES order}.
        missing: {mother: pieces it lacks}; such a mother is incomplete and never read.

    Returns:
        The frame.
    """
    missing = missing or {}
    rows = []
    for m, words in states.items():
        lacks = missing.get(m, [])
        rows.append(
            {
                "mother": m,
                "batch": None,
                "identity": None,
                "complete": not lacks,
                "missing": lacks,
                **{
                    p: None
                    if lacks
                    else {
                        "label": w,
                        "state": w,
                        "score": None,
                        "meaning": "",
                        "summary": {},
                    }
                    for p, w in zip(PIECES, words)
                },
            }
        )
    return pd.DataFrame(rows).set_index("mother")


def market(seed: int, edge: str | None) -> dict:
    """Mothers of fat-tailed noise sharing a factor, the asset's moves, one edge planted or none.

    Args:
        seed: Seed of the draw.
        edge: The mother given a true daily Sharpe of 0.25, or None.

    Returns:
        `panel`, `benchmark` and `mc`, as report.py hands them to measure.run; the random
        traders earn nothing here, so the excess is the mother's own day.
    """
    rng = np.random.default_rng(seed)
    names = [f"m{i}" for i in range(K)]
    panel = pd.DataFrame(
        0.4 * rng.standard_t(4, (DAYS + 1, 1)) + rng.standard_t(4, (DAYS + 1, K)),
        columns=names,
    )
    if edge:
        panel[edge] += 0.25 * panel[edge].std()
    return {"panel": panel, "benchmark": 0.0 * panel, "mc": pd.Series(0.0, index=names)}


def traders(seed: int, edge: float) -> dict:
    """Mothers that ARE random traders of their own footprint, on a market that drifts up.

    Args:
        seed: Seed of the market and of the mothers.
        edge: Account currency added to every trade of `m1`, the one planted edge.

    Returns:
        What measure.run takes, plus `sum` (each mother's total excess) and `bars`. Every
        mother is long TRADES times at uniform bars, held 30 to 600 bars, priced by the
        repricer at COSTS and booked on the day she closes; her benchmark is
        `benchmark.footprint` of those trades. Long in a rising market, each of them makes
        money — and none of it is hers.
    """
    rng = np.random.default_rng(seed)
    days = pd.bdate_range("2021-01-04", periods=DAYS)
    index = pd.DatetimeIndex(
        np.add.outer(days.values, np.arange(MINUTES) * np.timedelta64(1, "m")).ravel()
    )
    price = 100 + np.cumsum(rng.normal(DRIFT, 0.05, len(index) + 1))
    bars = pd.DataFrame(
        {
            "Open": price[:-1],
            "Close": price[1:],
            "High": np.maximum(price[:-1], price[1:]) + 0.01,
            "Low": np.minimum(price[:-1], price[1:]) - 0.01,
        },
        index=index,
    )
    panel, random, mc = {}, {}, {}
    for m in (f"m{i}" for i in range(K)):
        hold = rng.integers(30, 600, TRADES)
        enter = rng.integers(0, len(index) - hold)
        net, _ = reprice.pnl(
            price[enter],
            price[enter + hold],
            index.values[enter],
            index.values[enter + hold],
            1.0,
            np.ones(TRADES),
            COSTS,
        )
        trades = pd.DataFrame(
            {
                "Open time": index[enter],
                "Close time": index[enter + hold],
                "Type": "Buy",
                "Size": 1.0,
                "Profit/Loss": net + edge * (m == "m1"),
            }
        )
        panel[m] = (
            trades.groupby(trades["Close time"].dt.normalize())["Profit/Loss"]
            .sum()
            .reindex(days, fill_value=0.0)
        )
        random[m], mc[m] = benchmark.footprint(trades, bars, COSTS, CFG["benchmark"])
    panel, random = pd.DataFrame(panel), pd.DataFrame(random)
    return {
        "panel": panel,
        "benchmark": random,
        "mc": pd.Series(mc),
        "sum": (panel - random).sum(),
        "bars": bars,
    }


def main() -> None:
    """Run the controls and exit non-zero on any failure."""
    failures = []
    passing = mothers({f"m{i}": ["pass"] * 4 for i in range(K)})
    everyone = readings.label(("ninguna", "entrantes"))

    false = sum(
        bool(
            measure.run({"population": passing, **market(s, None)}, CFG)["named"][
                everyone
            ]
        )
        for s in range(SEEDS)
    )
    # Binomial(20, 0.05): four or more false families happens 1.6 % of the time.
    if false > 3:
        failures.append(
            f"ruido: el StepM nombra a alguna madre en {false} de {SEEDS} semillas"
        )

    hits = 0
    vetoed = mothers(
        {
            "m0": ["pass"] * 4,
            "m1": ["pass", "pass", "fail", "watch"],
            **{f"m{i}": ["pass"] * 4 for i in range(2, K)},
        }
    )
    for s in range(SEEDS):
        got = measure.run({"population": vetoed, **market(s, "m1")}, CFG)
        hits += "m1" in got["named"][everyone]
        calls = got["calls"].loc["m1"]
        if (
            calls["unanimidad+entrantes"] != "fail"
            or calls["sin_fallo+supervivientes"] != "fail"
        ):
            failures.append(
                f"semilla {s}: una pieza en fail no veta a m1 ({calls.to_dict()})"
            )
        if calls[everyone] != "pass":
            failures.append(f"semilla {s}: con las piezas de contexto m1 no pasa")
    if hits < SEEDS:
        failures.append(f"edge plantado: el StepM lo nombra en {hits} de {SEEDS}")

    # The benchmark's known answer: a mother that IS a random trader of her own footprint
    # earns the drift and no excess; a constant edge per trade is excess, to the cent.
    sums, drift, named, found = [], [], 0, 0
    for s in range(RUNS):
        flat, planted = traders(s, 0.0), traders(s, 3.0)
        sums += list(flat["sum"])
        drift += list(flat["panel"].sum())
        named += bool(
            measure.run({"population": passing, **flat}, CFG)["named"][everyone]
        )
        got = measure.run({"population": passing, **planted}, CFG)
        found += got["named"][everyone] == ["m1"]
        gain = planted["sum"]["m1"] - flat["sum"]["m1"]
        if abs(gain - 3.0 * TRADES) > 1e-6 or got["table"].loc["m1", "excess_day"] <= 0:
            failures.append(
                f"semilla {s}: un edge de 3 por operación da un exceso de {gain:.2f}"
            )
        if (
            not np.allclose(planted["benchmark"], flat["benchmark"])
            or (flat["benchmark"].index != flat["panel"].index).any()
        ):
            failures.append(
                f"semilla {s}: el operador al azar depende del resultado de la madre"
            )
    sums, drift = np.array(sums), np.array(drift)
    z = sums.mean() / (sums.std(ddof=1) / np.sqrt(len(sums)))
    if abs(z) > 3 or drift.mean() < 5 * abs(sums.mean()):
        failures.append(
            f"madres al azar: exceso medio {sums.mean():.1f} (z {z:.2f}) con una "
            f"deriva de {drift.mean():.1f}: el operador al azar no la descuenta"
        )
    if named > 2 or found < RUNS:  # Binomial(10, 0.05): three or more, 1.2 %
        failures.append(
            f"madres al azar: el StepM nombra a alguna en {named} de {RUNS}; el "
            f"edge plantado sale solo en {found} de {RUNS}"
        )

    states = measure.states(vetoed)
    if readings.kept(states, "sin_fallo") != ["m0", "m2", "m3", "m4"] or readings.kept(
        states, "unanimidad"
    ) != ["m0", "m2", "m3", "m4"]:
        failures.append("readings: fail no descarta")
    watch = measure.states(mothers({"a": ["pass", "watch", "pass", "pass"]}))
    if readings.kept(watch, "sin_fallo") != ["a"] or readings.kept(watch, "unanimidad"):
        failures.append("readings: watch debe pasar sin_fallo y no unanimidad")

    blind = mothers({"a": ["pass"] * 4, "b": ["pass"] * 4}, {"b": ["wfc", "cscv"]})
    refused = {"population": blind, "refused": "política", "source": "test"}
    got = many.run(refused, CFG)
    member = {m["strategy"]: m for m in got["members"]}
    if (
        member["b"]["verdict"]["label"] != "Incompleta"
        or "b" in got["measured"]["states"].index
    ):
        failures.append("una madre incompleta se ha leído")
    if set(got["measured"]["calls"].loc["a"]) != {"none"}:
        failures.append(
            "sin oos2 la llamada de una madre que pasa las piezas debe quedar sin leer"
        )
    # owner, 2026-10-12: nobody is discarded — `pieces: null`, no reading chosen, all MANTENER
    if (
        one.chosen(CFG) is not None
        or got["population"]["verdict"]["label"] != "Sin regla"
    ):
        failures.append("el paso 20 ha elegido una lectura: debe quedar sin regla")
    three = mothers(
        {
            "cae": ["pass", "watch", "fail", "pass"],
            "duda": ["pass", "pass", "watch", "pass"],
            "sigue": ["pass"] * 4,
        }
    ).assign(identity="i")
    judged = many.run(
        {"population": three, "refused": "política", "source": "test"}, CFG
    )
    table = report.verdict_table(three, judged["measured"], CFG).set_index("strategy")[
        "verdict"
    ]
    if set(table.index) != {"cae", "duda", "sigue"} or set(table.values) != {
        "MANTENER"
    }:
        failures.append(f"sin regla el paso 20 descartó a alguien ({table.to_dict()})")
    report.need_stepm("política", CFG)  # no reading chosen: it needs no StepM
    report.need_stepm(None, {**CFG, "joint": {**CFG["joint"], "pieces": "unanimidad"}})
    try:
        report.need_stepm(
            "política", {**CFG, "joint": {**CFG["joint"], "pieces": "unanimidad"}}
        )
        failures.append("una lectura que usa el StepM debe seguir levantando sin él")
    except PermissionError:
        pass
    if (
        many.run(refused, {**CFG, "joint": {**CFG["joint"], "pieces": "sin_fallo"}})[
            "population"
        ]["verdict"]["label"]
        == "Sin regla"
    ):
        failures.append("con una lectura elegida el paso 20 sigue diciendo SIN REGLA")

    inputs.blind_door("TEST_M1_nunca_corrido")  # a human is never refused
    os.environ[gate.AUTONOMOUS] = "1"  # an autonomous agent is
    try:
        inputs.blind_door("TEST_M1_nunca_corrido")
        failures.append(
            "la puerta ciega dejó leer a un agente autónomo un estudio sin 17, 18 ni 19"
        )
    except PermissionError:
        pass
    os.environ.pop(gate.AUTONOMOUS)

    print(
        "\n".join(failures)
        or f"ok: sobre ruido el StepM nombra alguna madre en {false} de {SEEDS} semillas; el "
        f"edge plantado sale nombrado en {hits} de {SEEDS}; madres que SON operadores al azar "
        f"en un mercado con deriva ganan {drift.mean():.0f} y exceden {sums.mean():.1f} "
        f"(z {z:.2f}), nombradas en {named} de {RUNS}, y un edge por operación sale en {found} "
        f"de {RUNS}; una pieza en fail "
        f"veta bajo unanimidad y sin_fallo; una madre incompleta no se lee; sin oos2 no se "
        f"decide; y la puerta ciega se niega sin 17, 18 y 19"
    )
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
