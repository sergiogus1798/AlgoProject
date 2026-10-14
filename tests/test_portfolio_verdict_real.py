#!/usr/bin/env python3
"""Known answers of the real path's verdict (M5, Q11 d): the oos1 bar, its calibration, the one read of oos2."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import ledger.study as study  # noqa: E402
from core.surface import plateau  # noqa: E402
from ledger import gate, record as ledger_record  # noqa: E402
from portfolio.common.construct import many, oos2  # noqa: E402
from portfolio.common.construct.inputs import config  # noqa: E402
from portfolio.common.construct.search import random_k  # noqa: E402
from portfolio.common.construct.verdict import decide_real, deflate, null  # noqa: E402

CALENDAR = {
    "build": (pd.Timestamp("2015-01-01"), pd.Timestamp("2019-12-31")),
    "oos1": (pd.Timestamp("2020-01-01"), pd.Timestamp("2021-12-31")),
    "oos2": (pd.Timestamp("2022-01-01"), pd.Timestamp("2023-12-29")),
}
DAYS = pd.bdate_range(CALENDAR["build"][0], CALENDAR["oos2"][1])
POOL = {"hash": "0ddba11" * 9 + "0"}
FAILURES = []


def check(name: str, ok: bool) -> None:
    """Print one line per case; remember the failures."""
    print(f"{'OK   ' if ok else 'FALLO'}  {name}")
    if not ok:
        FAILURES.append(name)


def world(
    n: int, edge: dict[int, float], seed: int, chosen: list[int], oos2_edge: float = 0.0
) -> dict:
    """`report.load()`'s shape on n independent noise members; `edge` is added from oos1 on."""
    rng = np.random.default_rng(seed)
    pnl = rng.normal(0, 1, (len(DAYS), n))
    late = np.asarray(DAYS > CALENDAR["build"][1])
    last = np.asarray(DAYS > CALENDAR["oos1"][1])
    for member, drift in edge.items():
        pnl[late, member] += drift
        pnl[last, member] += oos2_edge - drift
    ids = [f"s{i:02d}" for i in range(n)]
    result = {
        "identities": ids,
        "kept": ids,
        "excluded": [],
        "floor": dict.fromkeys(ids, 0.001),
        "daily": pd.DataFrame(pnl, index=DAYS, columns=ids),
        "calendar": CALENDAR,
        "scale": np.ones(n),
        "pool_name": "sintetico",
        "graph": {
            "graph": ~np.eye(n, dtype=bool),
            "counts": {},
            "n_pairs": n * (n - 1) // 2,
            "n_admissible_pairs": n * (n - 1) // 2,
            "n_out": n,
        },
        "members_meta": {
            i: {"symbol": "NIKKEI225", "timeframe": "M30", "family": "t"} for i in ids
        },
    }
    members = [ids[i] for i in chosen]
    return {
        "result": result,
        "members": members,
        "pool": POOL,
        "table": pd.DataFrame({"members": ["+".join(members)], "score": [1.0]}),
    }


def cfg_of(**real: object) -> dict:
    """The committed config (10,000 draws, percentile 95) with `real.<knob>` overrides."""
    return config.load([f"real.{k}={v}" for k, v in real.items()])


def test_oos1_bar() -> None:
    """(i) A planted edge on oos1 beats the 95th percentile; a random portfolio does so ~5 % of the time."""
    cfg = cfg_of()
    planted = many.oos1(
        world(12, {0: 0.15, 1: 0.15, 2: 0.15}, 1, [0, 1, 2]),
        cfg,
        np.random.default_rng(1),
    )
    check(
        f"planted trio: score {planted['value']:.3f} > p95 {planted['bar']:.3f}, 10,000 draws of "
        f"{planted['n_space']} distinct trios",
        planted["state"] == "pass"
        and planted["n"] == 10000
        and planted["n_space"] == 220
        and planted["k"] == 3
        and planted["percentile"] > 0.97,
    )
    fast = cfg_of(null_draws=2000)
    states = []
    for seed in range(200):
        rng = np.random.default_rng(5000 + seed)
        pick = sorted(rng.choice(12, 3, replace=False).tolist())
        states.append(many.oos1(world(12, {}, 9000 + seed, pick), fast, rng)["state"])
    rate = np.mean([s == "pass" for s in states])
    check(
        f"noise: a random trio passes the oos1 bar in {rate:.1%} of 200 seeds (nominal 5 %, "
        "3 sigma = 4.6 points)",
        0.005 <= rate <= 0.097 and "no_discrimina" not in states,
    )


def test_small_pool_is_said() -> None:
    """(ii) Six admissible pairs: the null redraws the chosen one, and the output says so."""
    inputs = world(4, {0: 0.3, 1: 0.3}, 2, [0, 1])
    got = many.oos1(inputs, cfg_of(), np.random.default_rng(2))
    check(
        f"4 members, K=2: {got['n_space']} distinct combinations vs {got['n']} draws -> no_discrimina "
        f"(the chosen one is {got['share_chosen']:.1%} of the draws)",
        got["state"] == "no_discrimina"
        and got["n_space"] == 6
        and abs(got["share_chosen"] - 1 / 6) < 0.02,
    )
    text = "\n".join(decide_real.oos1_lines(got))
    check(
        "the sentence says NO DISCRIMINA, counts the 6 against the 10,000 and prints no percentile reading",
        "NO DISCRIMINA" in text
        and "6 combinaciones admisibles distintas" in text
        and "10 000 carteras" in text
        and "queda en el percentil" not in text,
    )
    edge = null.bar(0.9, np.r_[np.full(50, 0.9), np.linspace(0, 0.8, 950)], 95, 0.05)
    clear = null.bar(0.9, np.r_[np.full(49, 0.9), np.linspace(0, 0.8, 951)], 95, 0.049)
    check(
        "the boundary: the chosen one as 5 % of the draws cannot beat p95 (said); as 4.9 % it can",
        edge["state"] == "no_discrimina" and clear["state"] == "pass",
    )
    big = random_k.draw(~np.eye(40, dtype=bool), 3, 500, 1000, np.random.default_rng(3))
    check(
        "above the enumeration limit the draws are still admissible trios, the space uncounted",
        big["n_space"] is None
        and (big["members"].sum(axis=1) == 3).all()
        and len(big["index"]) == 500,
    )


def test_deflated_sign() -> None:
    """(iv) A known series with a known N: the sign of Sharpe minus the expected maximum."""
    rng = np.random.default_rng(4)
    returns = rng.normal(0.1, 1.0, 500)
    sharpe = returns.mean() / returns.std(ddof=1)
    one, many_n = deflate.read(returns, 0.05, 1), deflate.read(returns, 0.05, 1_000_000)
    bench = plateau.expected_max_sharpe(0.05, 1_000_000)
    check(
        f"N=1: the benchmark is 0 and the excess is the Sharpe itself ({one['excess']:+.4f}) -> pass",
        one["benchmark"] == 0.0
        and abs(one["excess"] - sharpe) < 1e-12
        and one["state"] == "pass",
    )
    check(
        f"N=1e6, sigma 0.05: benchmark {bench:.4f} > Sharpe {sharpe:.4f} -> excess "
        f"{many_n['excess']:+.4f}, fail; DSR {many_n['dsr']:.3f} < 0.5",
        abs(many_n["benchmark"] - bench) < 1e-12
        and many_n["excess"] < 0
        and many_n["state"] == "fail"
        and many_n["dsr"] < 0.5 < one["dsr"]
        and many_n["n"] == 1_000_000,
    )


def test_one_read() -> None:
    """(iii) oos1 then oos2, a row per segment, the door asked first; a second verdict reads nothing."""
    cfg = cfg_of(null_draws=2000)
    inputs = world(12, {0: 0.15, 1: 0.15, 2: 0.15}, 1, [0, 1, 2], oos2_edge=0.3)
    meta = inputs["result"]["members_meta"]
    real_path, real_allow, asked = study.path, gate.allow, []
    with tempfile.TemporaryDirectory() as tmp:
        study.path = lambda s: Path(tmp) / f"{s}.jsonl"
        gate.allow = lambda step, segment, symbol: asked.append((step, segment, symbol))
        try:
            dry = many.judge(inputs, cfg, np.random.default_rng(1))
            ledger_record.log(
                oos2.pool_study(POOL),
                {
                    "step": 27,
                    "launched_by": "real",
                    "segment": "build",
                    "n_in": 12,
                    "n_out": 3,
                    "criterion": "portfolio/ranks4/exhaustive",
                    "symbol": "NIKKEI225",
                    "timeframe": "mixed",
                },
                np.random.default_rng(0).normal(0.0, 0.02, 300),
            )
            asked.clear()
            first = many.judge(inputs, cfg, np.random.default_rng(1))
            order = [a[1] for a in asked if "+" not in a[2]]
            calls = []
            again = oos2.read(
                lambda: calls.append(1), inputs["members"], POOL, meta, "x", "t", ""
            )
            other = oos2.read(
                lambda: calls.append(1), ["s05", "s06", "s07"], POOL, meta, "x", "t", ""
            )
            second = many.judge(inputs, cfg, np.random.default_rng(7))
            loser = many.judge(
                world(12, {}, 3, [9, 10, 11]) | {"pool": {"hash": "f" * 64}},
                cfg,
                np.random.default_rng(3),
            )
            rows = study.read(oos2.pool_study(POOL))
            lost = study.read(oos2.pool_study({"hash": "f" * 64}))
        finally:
            study.path, gate.allow = real_path, real_allow
    check(
        "no build Sharpes in the pool's study: oos1 passes, oos2 is NOT opened and the label says why",
        dry["oos1"]["state"] == "pass"
        and dry["oos2"]["state"] == "no_sigma"
        and dry["pass"] is None
        and dry["label"].startswith("SIN VEREDICTO")
        and dry["cost"]["segments"] == ["oos1"],
    )
    check(
        f"first verdict: oos1 pass, oos2 read (excess {first['oos2']['excess']:+.4f}, N "
        f"{first['oos2']['n']}) -> {first['label']}",
        first["oos2"]["state"] == "pass"
        and first["pass"] is True
        and not first["oos2"]["stored"]
        and first["oos2"]["n"] == 300
        and first["cost"]["segments"] == ["oos1", "oos2"],
    )
    check(
        "the door is asked for oos1 before oos1 is read and for oos2 before oos2 is read",
        order[0] == "oos1"
        and order.index("oos2") > order.index("oos1")
        and asked[0][0] == 27,
    )
    check(
        "a second read of the same portfolio returns the stored reading and never calls the path",
        again["stored"]
        and again["excess"] == first["oos2"]["excess"]
        and not calls
        and second["oos2"]["stored"]
        and second["pass"] is True
        and "no se ha vuelto a calcular" in decide_real.sentence(second),
    )
    check(
        "another portfolio of the same pool is refused",
        other["state"] == "refused" and not calls,
    )
    looks = rows[rows["criterion"] == many.CRITERION]
    check(
        "ledger: one row per look per segment -- oos1 three times (dry, first, second), oos2 once; "
        "1 portfolio in, 1 out",
        looks["segment"].tolist() == ["oos1", "oos1", "oos2", "oos1"]
        and (looks["n_in"] == 1).all()
        and (looks["n_out"] == 1).all()
        and (looks["step"] == 27).all(),
    )
    check(
        "a portfolio that fails oos1 opens nothing else: one oos1 row with n_out 0, no oos2 row",
        loser["oos1"]["state"] == "fail"
        and loser["pass"] is False
        and loser["label"] == "NO PASA (oos1)"
        and lost["segment"].tolist() == ["oos1"]
        and lost["n_out"].tolist() == [0]
        and loser["oos2"]["state"] == "not_opened",
    )


def test_contract() -> None:
    """The population result validates, draws oos2 only when it was read, and carries the sentence."""
    cfg = cfg_of(null_draws=500)
    inputs = world(12, {0: 0.15, 1: 0.15, 2: 0.15}, 1, [0, 1, 2])
    real_path = study.path
    with tempfile.TemporaryDirectory() as tmp:
        study.path = lambda s: Path(tmp) / f"{s}.jsonl"
        try:
            got = many.run(inputs, cfg, np.random.default_rng(1))
        finally:
            study.path = real_path
    pop = got["population"]
    tabs = {t["name"]: t for t in pop["tabs"]}
    drawn = [
        s["label"]
        for b in tabs["cartera"]["blocks"]
        if b["kind"] == "lines"
        for s in b["series"]
        if s["role"] != "reference"
    ]  # the members' own lines are not segments
    check(
        "five tabs, the verdict on top, a relaxed run warned (500 draws is not the ledger's 10,000)",
        list(tabs) == ["veredicto", "universo", "parejas", "busqueda", "cartera"]
        and pop["verdict"]["meaning"] == got["sentence"]
        and pop["warnings"][0]["code"] == "relaxed",
    )
    check(
        "oos2 was not read (no sigma): its equity is not drawn",
        drawn == ["build", "oos1"],
    )


def main() -> None:
    """Run every case."""
    for name, case in list(globals().items()):
        if name.startswith("test_"):
            case()
    print(f"\n{'TODO OK' if not FAILURES else 'FALLOS: ' + ', '.join(FAILURES)}")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
