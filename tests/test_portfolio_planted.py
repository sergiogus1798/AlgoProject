#!/usr/bin/env python3
"""Seeded known answers of the rank search: a planted portfolio, the shifted minimum, sequence admission."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

import portfolio.common.construct.real as real
import portfolio.common.construct.search.admission as admission
import portfolio.common.construct.search.choose as choose
import portfolio.common.construct.search.genetic as genetic
import portfolio.common.construct.search.objective as objective
import portfolio.common.construct.verdict.metrics as metrics
from portfolio_planted import CALENDAR, NAMES, planted_pool, planted_cfg

FAILURES = []
A, B, DUP, HEDGE = 0, 1, 2, 3


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def chosen(found: dict) -> list[str]:
    """The names of the best combination."""
    return [NAMES[i] for i in np.flatnonzero(found["members"][found["best"]])]


def test_planted_portfolio() -> None:
    """The real path from daily P&L on: pair screen at 0.30, every clique, the shifted ranks."""
    got = real.on_build(planted_pool(), CALENDAR, np.ones(len(NAMES)), planted_cfg())
    graph, failing = got["graph"]["graph"], got["graph"]["failing"]
    why = {(r.i, r.j): set() for r in failing.itertuples()}
    for r in failing.itertuples():
        why[(r.i, r.j)].add(r.filter)
    check(
        "no threshold is relaxed: the planted pair clears the owner's 0.30 on every filter",
        not got["graph"]["relaxed"] and graph[A, B],
    )
    check(
        "the duplicate of A is not admissible with A",
        not graph[A, DUP] and "pearson_daily" in why[("A", "A_dup")],
    )
    check(
        "the strong hedge (rho -0.64) is refused with A and with B by |rho| (owner, Q6) -- and "
        "not by the one-sided tail and co-loss filters",
        not graph[A, HEDGE]
        and not graph[B, HEDGE]
        and "pearson_daily" in why[("A", "hedge")]
        and not {"tail", "co_loss"} & why[("A", "hedge")],
    )

    found = choose.choose(
        got["unit"], got["dates"], graph, planted_cfg(), np.random.default_rng(0)
    )
    check(
        "the search returns exactly the planted {A, B}",
        found["mode"] == "exhaustive" and chosen(found) == ["A", "B"],
    )
    members, table = (
        found["members"],
        objective.worst(
            objective.measure(
                got["unit"], got["dates"], found["members"], planted_cfg()
            )
        ),
    )
    best = found["best"]
    check(
        "every combination scored is a clique; none holds A with its duplicate or the hedge",
        all(genetic.is_clique(graph, m) for m in members)
        and not (members[:, A] & (members[:, DUP] | members[:, HEDGE])).any(),
    )
    check(
        "{A, B} has the top R-cubed and gain-to-pain and the lowest P(losing year); RAR is a "
        "mean of its members', so only a single can sit above it",
        table["r_cubed"].argmax() == best
        and table["gain_to_pain"].argmax() == best
        and table["p_losing_year"][best] == table["p_losing_year"].min()
        and members[table["rar"] > table["rar"][best]].sum(axis=1).max() == 1,
    )
    print(
        f"       {len(members)} combinaciones; {{A, B}} puntúa {found['score'][best]:.3f}, "
        f"la segunda {np.sort(found['score'])[-2]:.3f}"
    )

    signed = graph.copy()
    signed[HEDGE, [A, B]] = signed[[A, B], HEDGE] = True
    wrong = choose.choose(
        got["unit"], got["dates"], signed, planted_cfg(), np.random.default_rng(0)
    )
    check(
        "the check has teeth: were the hedge let in, the search would pick {A, B, hedge}",
        chosen(wrong) == ["A", "B", "hedge"],
    )


def test_shifted_windows() -> None:
    """Four windows, each the build with its start a month later; the minimum on a hand table."""
    daily = planted_pool().loc[: CALENDAR["build"][1]]
    unit, dates = daily.to_numpy().T, daily.index
    members = np.eye(len(NAMES), dtype=bool)[:3]
    tables = objective.measure(unit, dates, members, planted_cfg())
    check("shift_months=3 (owner, R3): four windows", len(tables) == 4)
    ok = True
    for months, table in enumerate(tables):
        keep = dates >= dates[0] + pd.DateOffset(months=months)
        slow = metrics.table(unit[:3][:, keep], dates[keep], "calendar")
        ok &= all(np.allclose(table[k], slow[k]) for k in slow)
    check(
        "window m is the build from its first day plus m calendar months, measured alone",
        ok,
    )
    check(
        "the Sharpe kept for the ledger is the whole window's",
        np.array_equal(objective.worst(tables)["sharpe"], tables[0]["sharpe"]),
    )

    flat = {
        "r_cubed": np.ones(3),
        "gain_to_pain": np.ones(3),
        "p_losing_year": np.zeros(3),
        "sharpe": np.ones(3),
    }
    hand = [
        {**flat, "rar": np.array([10.0, 20.0, 30.0])},  # window 0: C > B > A
        {**flat, "rar": np.array([9.0, 8.0, 7.0])},
    ]  # window 1: A > B > C, all lower
    by_metric, table = objective.score(hand, hand)
    check(
        "each RAR at its worst (9, 8, 7), ranked once -> A wins (owner, 2026-10-05)",
        table["rar"].tolist() == [9.0, 8.0, 7.0] and by_metric.argmax() == 0,
    )
    worst = objective.worst(
        [
            {**flat, "rar": np.ones(3), "p_losing_year": np.array([0.1, 0.0, 0.2])},
            {**flat, "rar": np.ones(3), "r_cubed": np.array([np.nan, 0.5, 2.0])},
        ]
    )
    check(
        "worst: the highest P(losing year), the lowest of the rest, a window with no drawdown skipped",
        worst["p_losing_year"].tolist() == [0.1, 0.0, 0.2]
        and worst["r_cubed"].tolist() == [1.0, 0.5, 1.0],
    )

    argv, sys.argv = (
        sys.argv,
        [
            "real",
            "--pool",
            "no_existe",
            "--seed",
            "0",
            "--set",
            "real.shift_minimum=score",
        ],
    )
    try:
        real.main()
        refused = ""
    except SystemExit as stop:
        refused = str(stop)
    finally:
        sys.argv = argv
    check(
        "the command refuses a real.shift_minimum other than the owner's «metric»",
        "real.shift_minimum" in refused,
    )


def test_sequence_admission() -> None:
    """Two clones each help the base alone and not together: the fixed base and the sequence differ."""
    d = 2500
    noise = np.random.default_rng(11).normal(size=(d, 3))
    noise = np.linalg.qr(noise - noise.mean(axis=0))[0].T * np.sqrt(
        d - 1
    )  # exactly: mean 0, sd 1, rho 0
    base, idea, other = 0.05 + noise[0], 0.05 + noise[1], 0.04 + noise[2]
    unit = np.vstack(
        [base, idea, idea - 0.001, other]
    )  # 0 base, 1 and 2 clones, 3 another idea
    graph = ~np.eye(4, dtype=bool)
    fixed = admission.judge(unit, graph, np.array([0]), np.array([1, 2, 3]), "finite")
    check(
        "fixed base: the two clones and the third idea would all enter",
        fixed["enters"].all(),
    )

    got = admission.sequence(unit, graph, np.array([0]), np.array([1, 2, 3]), "finite")
    entered = got.loc[got["enters"], "candidate"].tolist()
    check(
        "in sequence: the better clone first, then the other idea; its twin never",
        entered == [1, 3] and got["round"].tolist() == [1, 1, 1, 2, 2, 3],
    )
    last = got.iloc[-1]
    check(
        "the twin could enter in round 1 only: beside its clone it lowers the Sharpe "
        "(round 3: 0.189 / sqrt(6) against 0.14 / sqrt(3))",
        last["candidate"] == 2
        and got[got["candidate"] == 2]["admissible"].tolist() == [True, False, False]
        and np.isclose(last["increment"], 0.189 / np.sqrt(6) - 0.14 / np.sqrt(3)),
    )
    second = got[(got["round"] == 2) & (got["candidate"] == 3)]["increment"].iloc[0]
    check(
        "round 2's increment is measured against the NEW base {0, 1}: 0.14 / sqrt(3) - 0.10 / sqrt(2)",
        np.isclose(second, 0.14 / np.sqrt(3) - 0.10 / np.sqrt(2)),
    )
    check("one ledger trial per judgement: 3 + 2 + 1", len(got) == 6)

    graph[1, 2] = graph[2, 1] = False
    vetoed = admission.sequence(unit, graph, np.array([0]), np.array([1, 2]), "finite")
    check(
        "pair filters are read against the NEW base: once its clone is in, the twin is blocked by it",
        vetoed["blocked_by"].tolist() == [[], [], [1]]
        and vetoed["enters"].tolist() == [True, False, False],
    )
    check(
        "no candidates, no rounds",
        admission.sequence(
            unit, graph, np.array([0]), np.array([], dtype=int), "finite"
        ).empty,
    )


def main() -> None:
    """Run every case; exit non-zero on any failure."""
    test_planted_portfolio()
    test_shifted_windows()
    test_sequence_admission()
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
