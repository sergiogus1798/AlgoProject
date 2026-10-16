#!/usr/bin/env python3
"""Known-answer tests of the funded verdict (F4): the selected null, its calibration, what is said without a bar."""

import ast
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# first: test_portfolio_stageb plants the data root, which must precede every project import
from test_portfolio_stageb import small_cfg  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from portfolio.common.construct import funded_b  # noqa: E402
from portfolio.common.construct.pairs import table as pairs_table  # noqa: E402
from portfolio.common.construct.search import shortlist, stagea, stageb_null, stageb_run  # noqa: E402
from portfolio.common.construct.verdict import decide, hold, null  # noqa: E402
from test_portfolio_mc_paths import _member, lenient_plan  # noqa: E402

VERDICT_DIR = Path(funded_b.__file__).parent / "verdict"
PLAN = lenient_plan(target=0.04, max_loss=0.10, daily_loss=0.05)


def _flat(pnl: np.ndarray) -> tuple[dict, dict]:
    """A pool with one same-day trade a day per member, as stage A's and stage B's arrays."""
    n, d = pnl.shape
    low, high = (
        np.minimum(pnl, 0).astype(np.float32),
        np.maximum(pnl, 0).astype(np.float32),
    )
    shared = {
        "identities": np.array([f"s{i}" for i in range(n)]),
        "days": np.arange(d),
        "closed": pnl,
        "float_end": np.zeros((n, d)),
        "opened": np.ones((n, d), np.int64),
        "lot_unit": np.ones(n),
    }
    stage_a = {
        **shared,
        "low5": low,
        "high5": high,
        "block_day": np.arange(d, dtype=np.int32),
    }
    stage_b = {
        **shared,
        "low1": low,
        "high1": high,
        "minute_day": np.arange(d, dtype=np.int32),
        "units": [_member(row) for row in pnl],
    }
    return stage_a, stage_b


def _experiment(
    rng: np.random.Generator,
    edge: np.ndarray,
    n_null: int,
    n_candidates: int,
    cfg: dict,
) -> dict:
    """One pool, searched for real (every pair) and by the null, both judged on a later stretch."""
    n = len(edge)
    stage_a, build = _flat(rng.normal(0, 1, (n, 250)) + edge[:, None])
    _, later = _flat(rng.normal(0, 1, (n, 250)) + edge[:, None])
    ids = list(build["identities"])
    sb = cfg["stageb"]

    def score(combos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Stage A's objective on the build arrays."""
        return stagea.best(
            stagea.evaluate(stage_a, combos, PLAN, cfg), stagea.levels(PLAN, cfg)
        )

    def judged(short: pd.DataFrame) -> dict:
        """Stage B on a shortlist, its winner read on the later stretch."""
        winner = stageb_run.run(short, build, PLAN, cfg, rng)["winner"]
        got = stageb_run.judged(
            later, winner["members"], PLAN, cfg, stageb_run.risk_of(winner, PLAN), rng
        )
        return {
            "members": winner["members"],
            "start_p": got["start_p"],
            "mc_p": got["mc_p"],
        }

    pairs = np.array(list(itertools.combinations(range(n), 2)), dtype=np.int32)
    best_p, best_r = score(pairs)
    frame = pd.DataFrame(
        {
            "members": ["+".join(ids[i] for i in c) for c in pairs],
            "score": best_p,
            "level": best_r,
        }
    )
    chosen = judged(
        shortlist.diverse(
            shortlist.ranked(frame),
            sb["shortlist_size"],
            sb["max_shared"],
            sb["shared_of"],
        )
    )
    graph = ~np.eye(n, dtype=bool)
    nulls = [
        judged(
            stageb_null.shortlisted(
                score, graph, ids, np.array([2]), n_candidates, cfg, rng
            )
        )
        for _ in range(n_null)
    ]
    read = null.read({k: chosen[k] for k in ("start_p", "mc_p")}, nulls)
    return {"chosen": chosen, "nulls": nulls, "read": read}


def _fast_cfg() -> dict:
    """A config small enough to repeat a whole search and its null many times."""
    cfg = small_cfg(shortlist_size=2, n_paths=200, sweep_days=[5])
    cfg["funded"].update(risk_grid=[0.1, 0.2], horizon_days=30)
    return cfg


def test_percentile_is_a_mid_rank() -> None:
    """Strictly below counts whole, a tie half: the chosen one among copies of itself sits at 0.5."""
    assert null.percentile(0.5, np.array([0.1, 0.2, 0.3, 0.9])) == 0.75
    assert null.percentile(0.5, np.full(7, 0.5)) == 0.5
    assert null.percentile(0.0, np.array([0.0, 0.0, 0.4, 0.6])) == 0.25
    got = null.read({"x": 0.3}, [{"x": 0.1}, {"x": 0.3}, {"x": 0.5}])["x"]
    assert got["percentile"] == 0.5 and got["null_median"] == 0.3 and got["n"] == 3


def test_noise_is_calibrated() -> None:
    """A pool of pure noise: the chosen combination's percentile in the null is uniform over seeds."""
    cfg = _fast_cfg()
    got = {"start_p": [], "mc_p": []}
    for seed in range(40):
        read = _experiment(np.random.default_rng(1000 + seed), np.zeros(8), 9, 28, cfg)[
            "read"
        ]
        for name in got:
            got[name].append(read[name]["percentile"])
    for name, values in got.items():
        values = np.array(values)
        print(
            f"     {name}: mean percentile {values.mean():.3f}, share at or above 0.9: "
            f"{(values >= 0.9).mean():.3f} (40 seeds, 9 null searches each)"
        )
        assert abs(values.mean() - 0.5) < 0.15, (
            name,
            values.mean(),
        )  # 3 sigma of a uniform's mean
        assert (values >= 0.9).mean() <= 0.25, (name, values)  # nominal 0.10 + 3 sigma


def test_planted_edge_lands_in_the_top_tail() -> None:
    """Two members with an edge on both stretches: found by the search, above a null that looks at few."""
    edge = np.array([0.3, 0.3] + [0.0] * 10)
    got = _experiment(np.random.default_rng(5), edge, 15, 3, _fast_cfg())
    assert got["chosen"]["members"] == "s0+s1"
    print(
        f"     planted pair: start_p percentile {got['read']['start_p']['percentile']:.2f}, "
        f"mc_p percentile {got['read']['mc_p']['percentile']:.2f} (15 null searches of 3 pairs)"
    )
    assert (
        got["read"]["start_p"]["percentile"] >= 0.8
        and got["read"]["mc_p"]["percentile"] >= 0.8
    )


def test_null_that_covers_the_pool_finds_the_same() -> None:
    """A null search with as many candidates as the pool has pairs picks the planted pair too."""
    edge = np.array([0.3, 0.3] + [0.0] * 4)
    got = _experiment(np.random.default_rng(6), edge, 9, 200, _fast_cfg())
    same = np.mean([n["members"] == got["chosen"]["members"] for n in got["nulls"]])
    print(
        f"     {same:.0%} of the null searches chose the chosen pair: start_p percentile "
        f"{got['read']['start_p']['percentile']:.2f} — the edge is real and this null cannot show it"
    )
    assert got["chosen"]["members"] == "s0+s1" and same >= 0.8
    assert 0.3 <= got["read"]["start_p"]["percentile"] <= 0.7


def test_candidates_are_admissible() -> None:
    """Every random combination is a clique of the graph, sized like the search's own."""
    rng = np.random.default_rng(7)
    graph = rng.random((20, 20)) < 0.5
    graph = (graph | graph.T) & ~np.eye(20, dtype=bool)
    combos = stageb_null.candidates(graph, np.array([1, 2, 3, 3]), 300, rng)
    sizes = (combos >= 0).sum(axis=1)
    assert combos.shape == (300, 3) and sizes.min() >= 1 and set(sizes) == {1, 2, 3}
    for row in combos:
        members = row[row >= 0]
        assert len(set(members)) == len(members)
        assert all(graph[a, b] for a, b in itertools.combinations(members, 2))


def test_did_the_diversification_hold() -> None:
    """A pair that moves together on the judging stretch is named; an independent one is not."""
    rng = np.random.default_rng(8)
    days = pd.bdate_range("2021-01-01", "2023-12-29")
    a = rng.normal(0, 1, len(days))
    daily = pd.DataFrame(
        {
            "a": a,
            "b": 0.9 * a + 0.3 * rng.normal(0, 1, len(days)),
            "c": rng.normal(0, 1, len(days)),
        },
        index=days,
    )
    cfg = small_cfg()
    pairs = pairs_table.table(
        daily, daily.groupby(daily.index.to_period("M")).sum(), cfg
    )
    got = hold.held(pairs, ["a", "b", "c"], cfg)
    named = {(o["i"], o["j"]) for o in got["over"]}
    assert ("a", "b") in named and got["n_pairs"] == 3 and not got["held"]
    assert {o["measure"] for o in got["over"] if (o["i"], o["j"]) == ("a", "b")} >= {
        "pearson_daily",
        "spearman_daily",
        "pearson_monthly",
    }
    assert got["effective_n"]["average"] < 2.6 and not got["short"]
    alone = hold.held(pairs[(pairs["i"] == "a") & (pairs["j"] == "c")], ["a", "c"], cfg)
    assert alone["n_pairs_over"] == len({(o["i"], o["j"]) for o in alone["over"]})
    brief = hold.held(pairs.assign(n_overlap_months=12), ["a", "b", "c"], cfg)
    assert (
        brief["held"] and len(brief["short"]) == 3
    )  # under 24 shared months: not judged


def test_no_criterion_is_said() -> None:
    """No bar: «sin criterio (falta <knob>)», never a silent None; supplied, oos1 reads the named percentile."""
    chosen = {"members": ["a", "b"], "risk": {"phase1": 0.005}, "build_p": 0.6}
    read = null.read(
        {"start_p": 0.5, "mc_p": 0.4},
        [{"start_p": s, "mc_p": 0.5} for s in (0.1, 0.2, 0.9)],
    )
    held = {
        "over": [],
        "short": [],
        "n_pairs": 1,
        "n_pairs_over": 0,
        "held": True,
        "effective_n": None,
    }
    cost = {
        "n_pool": 9,
        "n_stage_a": 500,
        "n_shortlist": 4,
        "n_settings": 10,
        "null_draws": 3,
        "null_candidates": 500,
        "segments": ["oos1"],
    }
    cfg = small_cfg()
    assert (
        cfg["verdict"]["pass_percentile"] == 0.95
        and cfg["verdict"]["pass_measure"] == "mc_p"
    )  # owner 2026-10-05 (measure), 2026-10-14 (percentile)
    cfg["verdict"]["pass_percentile"] = None  # the no-bar case this test is about
    first = decide.funded_oos1(read, 0, cfg)
    none = decide.verdict(chosen, first, decide.UNOPENED, held, cost)
    assert first["state"] == "sin_criterio" and none["pass"] is None
    assert none["label"] == "SIN CRITERIO (falta verdict.pass_percentile)"
    text = decide.sentence(none)
    assert text.splitlines()[-1].startswith(
        "Veredicto: SIN CRITERIO (falta verdict.pass_percentile)"
    )
    assert "500 combinaciones" in text and "oos2: no se lee" in text
    for measure, bar, same, want in (
        ("start_p", 0.6, 0, "pass"),
        ("start_p", 0.7, 0, "fail"),
        ("mc_p", 0.1, 0, "fail"),
        ("start_p", 0.6, 2, "no_discrimina"),
    ):
        cfg["verdict"].update(pass_measure=measure, pass_percentile=bar)
        got = decide.funded_oos1(read, same, cfg)
        assert got["state"] == want, (measure, bar, same, got["state"])
    passed = decide.verdict(
        chosen,
        decide.funded_oos1(
            read,
            0,
            cfg | {"verdict": {"pass_measure": "start_p", "pass_percentile": 0.6}},
        ),
        {
            "state": "fail",
            "sharpe": 0.01,
            "benchmark": 0.03,
            "excess": -0.02,
            "dsr": 0.2,
            "n": 99,
            "sigma": 0.01,
            "n_days": 250,
            "stored": False,
            "read_on": "2026-10-05T00:00:00",
        },
        held,
        cost,
    )
    assert (
        passed["pass"] is False
        and passed["label"] == "NO PASA (oos2)"
        and "N = 99" in decide.sentence(passed)
    )


def test_verdict_imports_no_search_no_equity() -> None:
    """PLAN §3: `verdict/` never imports `search/` or `equity/`."""
    for file in VERDICT_DIR.glob("*.py"):
        for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [getattr(node, "module", "") or ""] + [
                    a.name for a in node.names
                ]
                assert not any(
                    part in ("search", "equity") for n in names for part in n.split(".")
                ), (file.name, names)


def main() -> None:
    """Run every case; an assertion stops it."""
    for name, case in list(globals().items()):
        if name.startswith("test_"):
            case()
            print(f"OK   {name}")
    print("test_portfolio_verdict: ok")


if __name__ == "__main__":
    main()
