#!/usr/bin/env python3
"""Known-answer tests of stage B of the funded search (F3): exact minutes, the rule kernel, the shortlist."""

import itertools
import json
import resource
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import archive_planted  # noqa: E402
import funding_planted  # noqa: E402

PLANTED = archive_planted.plant(
    funding_planted.plant()
)  # before anything imports core.paths

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import ledger.study as study  # noqa: E402
from core.barstore import source as bars_of  # noqa: E402
from portfolio.common.construct import funded_b  # noqa: E402
from portfolio.common.construct.equity import store, universe as builder  # noqa: E402
from portfolio.common.construct.inputs import config, pool, source  # noqa: E402
from portfolio.common.construct.mc import judge, paths  # noqa: E402
from portfolio.common.construct.search import (
    shortlist,
    stagea,
    stagea_data,
    stageb,  # noqa: E402
    stageb_data,
    stageb_run,
    trials,
)
from portfolio.funded.rules import catalog, machine  # noqa: E402
from test_portfolio_mc_paths import bar_world, lenient_plan  # noqa: E402

ARCHIVED, VERSION = PLANTED["identity"], PLANTED["version"]
BUILD = (pd.Timestamp("2021-01-04"), pd.Timestamp("2021-12-31"))


def small_cfg(**stageb_knobs: object) -> dict:
    """The engine's config with a small risk grid, a short horizon and few paths."""
    cfg = {**config.load(), "compute": {"max_ram_gb": 8, "worker_ram_gb": 1.5}}
    cfg["equity"]["firm_clocks"]["test"] = "UTC"
    cfg["funded"].update(
        risk_grid=[0.002, 0.005, 0.01], horizon_days=40, open_risk_cap=100.0
    )  # never binds
    cfg["stageb"].update(
        dict(
            shortlist_size=4,
            shared_of="smaller",
            t1_gap="close_to_open_blocks",
            n_paths=400,
            sweep_days=[5, 20],
            stability_runs=3,
            stability_tol=0.2,
        ),
        **stageb_knobs,
    )
    cfg["verdict"].update(null_draws=3)
    return cfg


def searched(
    world: dict, plan: dict, cfg: dict, sizes: tuple[int, ...] = (2, 3)
) -> pd.DataFrame:
    """A stage-A `search.parquet` for a synthetic world: every combination of the given sizes."""
    ids = world["identities"]
    prepared = stagea_data.prepare(
        world["universe"],
        world["firm"],
        ids,
        world["calendar"],
        world["factors"],
        world["min_size"],
    )
    sets = [c for k in sizes for c in itertools.combinations(range(len(ids)), k)]
    combos = np.array(
        [list(c) + [-1] * (max(sizes) - len(c)) for c in sets], dtype=np.int32
    )
    best_p, best_r = stagea.best(
        stagea.evaluate(prepared, combos, plan, cfg), cfg["funded"]["risk_grid"]
    )
    return pd.DataFrame(
        {
            "members": ["+".join(ids[i] for i in c) for c in sets],
            "score": best_p,
            "level": best_r,
        }
    )


def complete(world: dict, plan: dict, cfg: dict, calendar: dict) -> dict:
    """A `bar_world` finished into what `funded_b.build` reads: plan, calendar, graph, search."""
    n = len(world["identities"])
    world.update(
        plan=plan,
        calendar=calendar,
        pool_name="synthetic",
        graph=~np.eye(n, dtype=bool),
        base=cfg,
        meta={
            m: {"symbol": "TESTSYM", "timeframe": "M30", "family": "testFamily"}
            for m in world["identities"]
        },
    )
    world["search"] = searched(world, plan, cfg)
    return world


def test_kernel_equals_the_machine() -> None:
    """Outcome, stages passed, day and rule equal `machine.challenge` on random paths, risk per phase."""
    rng = np.random.default_rng(1)
    plans = [
        p
        for p in map(catalog.plan, catalog.plans(10000, "USD"))
        if all(s["min_days"] is not None for s in p["stages"])
    ]
    assert len(plans) >= 5
    seen = set()
    for plan in plans:
        names = judge.stage_names(plan)
        drawn = {
            "closed": rng.normal(0.3, 2.0, (40, 60)),
            "float_end": rng.normal(0, 1.0, (40, 60)),
            "low": -np.abs(rng.normal(0, 2.0, (40, 60))),
            "high": np.abs(rng.normal(0, 2.0, (40, 60))),
            "opened": rng.integers(0, 3, (40, 60)).astype(np.int32),
        }
        risk = rng.choice([40.0, 90.0, 160.0], size=(6, len(names)))
        got = judge.outcomes(drawn, plan, risk)
        for c, p in itertools.product(range(6), range(40)):
            row = {
                k: v[p].astype(np.int64) if k == "opened" else v[p]
                for k, v in drawn.items()
            }
            want = machine.challenge(row, plan, dict(zip(names, risk[c])), 0, 60)
            code = {"pass": 1, "fail": 0, "open": -1}[want["outcome"]]
            rule = 0 if want["rule"] is None else 1 + judge.RULES.index(want["rule"])
            assert (
                got["code"][c, p],
                got["passed"][c, p],
                got["day"][c, p],
                got["rule"][c, p],
            ) == (code, len(want["stage_days"]), want["day"], rule), (
                plan["plan_key"],
                c,
                p,
                want,
            )
            seen.add((code, rule))
    assert {(1, 0), (0, 1), (0, 2), (-1, 0)} <= seen, seen


def test_exact_minutes_against_blocks_and_bound() -> None:
    """Joint low: sum of the members' day lows <= M5 blocks <= exact M1; one member equals its table."""
    world = bar_world(31, 4, "2021-01-04", "2021-07-01")
    ids = world["identities"]
    table = world["universe"]["days"]["test"]
    span = (pd.Timestamp("2021-01-04"), pd.Timestamp("2021-07-01"))
    data = stageb_data.prepare(
        world["sources"],
        world["bars"],
        table,
        "UTC",
        span,
        {m: 1.0 for m in ids},
        world["min_size"],
        small_cfg(),
    )
    index = pd.DatetimeIndex(data["days"])
    own_low, own_high = np.zeros(len(index)), np.zeros(len(index))
    for row, name in enumerate(ids):
        rows = (
            table[table["identity"] == name].set_index("day").reindex(index).fillna(0)
        )
        one = stageb_data.joint(data, [row])
        assert (
            max(
                np.abs(one[k] - rows[k].to_numpy()).max()
                for k in ("low", "high", "closed")
            )
            < 1e-3
        )
        own_low, own_high = own_low + one["low"], own_high + one["high"]
    exact = stageb_data.joint(data, np.arange(len(ids)))
    m5 = world["universe"]["m5"]["test"]
    keep = np.isin(m5["block_days"], data["days"])
    by_day = pd.DataFrame(
        {k: sum(m5[k][m][keep] for m in ids) for k in ("low", "high")}
    ).groupby(np.searchsorted(data["days"], m5["block_days"][keep]))
    low5, high5 = by_day["low"].min().to_numpy(), by_day["high"].max().to_numpy()
    assert (own_low <= low5 + 1e-3).all() and (low5 <= exact["low"] + 1e-3).all()
    assert (own_high >= high5 - 1e-3).all() and (high5 >= exact["high"] - 1e-3).all()
    assert (
        exact["low"] - own_low
    ).max() > 1.0  # the bound really is deeper on some day
    replay = paths.history(
        data["units"]
    )  # whole trades per block: also M5, never above M1
    assert (replay["low"] <= exact["low"] + 1e-3).all()


def test_golden_archived_strategy() -> None:
    """The planted USDJPY strategy: stage B's exact M1 day low and high equal the universe's stored ones.

    The one-member universe is built here in a temp root from the planted archive, so both paths
    price the member with the same card and the same clock (`universe._commission`).
    """
    with tempfile.TemporaryDirectory() as tmp:
        pool.ROOT, store.ROOT = Path(tmp) / "pool", Path(tmp) / "universe"
        pool.declare(
            "uno", [{"identity": ARCHIVED, "version": VERSION}], added_by="test"
        )
        cfg = small_cfg()
        universe = store.load(builder.build("uno", cfg))
    s = source.load(ARCHIVED, VERSION)
    table = universe["days"]["ftmo"]
    span = (table["day"].min(), table["day"].max())
    data = stageb_data.prepare(
        {ARCHIVED: s},
        {s["feed"]: bars_of(s["feed"], ["High", "Low", "Close"])},
        table,
        cfg["equity"]["firm_clocks"]["ftmo"],
        span,
        {ARCHIVED: 1.0},
        {ARCHIVED: 0.01},
        cfg,
    )
    stored = table.set_index("day").reindex(pd.DatetimeIndex(data["days"]))
    got = stageb_data.joint(data, [0])
    gaps = [np.abs(got[k] - stored[k].to_numpy()).max() for k in ("low", "high")]
    print(
        f"     {len(stored)} server days: largest gap low {gaps[0]:.4f} $, high {gaps[1]:.4f} $"
    )
    assert max(gaps) < 0.05


def test_shortlist_is_diverse() -> None:
    """Best first, duplicates once, and «more than half» read on the smaller or the larger set."""
    search = pd.DataFrame(
        {
            "members": ["a+b+c+d", "a+b+c+d", "a+b", "a+b+e+f", "c+d+e+f", "g+h"],
            "score": [0.9, 0.9, 0.8, 0.7, 0.6, np.nan],
            "level": 0.005,
        }
    )
    ranking = shortlist.ranked(search)
    assert list(ranking["members"]) == ["a+b+c+d", "a+b", "a+b+e+f", "c+d+e+f"]
    small = shortlist.diverse(ranking, 10, 0.5, "smaller")
    large = shortlist.diverse(ranking, 10, 0.5, "larger")
    assert list(small["members"]) == [
        "a+b+c+d",
        "a+b+e+f",
        "c+d+e+f",
    ]  # a+b is wholly inside the first
    assert list(large["members"]) == [
        "a+b+c+d",
        "a+b",
        "a+b+e+f",
        "c+d+e+f",
    ]  # 2 of 4 is not more than half
    assert list(shortlist.diverse(ranking, 10, 0.4, "larger")["members"]) == ["a+b+c+d"]


def test_decide_takes_the_most_pessimistic() -> None:
    """Per setting the lowest P(pass) over flavours and lengths counts; the best such setting is kept."""
    rows = pd.DataFrame(
        {
            "flavour": ["D", "D", "T1", "T2"] * 2,
            "length": [5, 20, 0, 5] * 2,
            "setting": [0] * 4 + [1] * 4,
            "r_phase1": [0.002] * 4 + [0.01] * 4,
            "p_pass": [0.50, 0.40, 0.60, 0.45, 0.70, 0.30, 0.80, 0.75],
        }
    )
    got = stageb.decide(rows)
    assert (got["p"], got["setting"], got["flavour"], got["length"]) == (
        0.40,
        0,
        "D",
        20,
    )
    assert got["risk"] == {"phase1": 0.002} and got["by_flavour"] == {
        "D": 0.40,
        "T1": 0.60,
        "T2": 0.45,
    }
    assert np.isnan(stageb.decide(rows.assign(p_pass=np.nan))["p"])


def test_unset_knobs_are_refused() -> None:
    """A run with `shared_of`, `t1_gap` or the open-risk cap left empty stops before reading anything."""
    for section, key in (
        ("stageb", "shared_of"),
        ("stageb", "t1_gap"),
        ("funded", "open_risk_cap"),
    ):
        cfg = small_cfg()
        cfg[section][key] = None
        try:
            funded_b.refuse_unset(cfg)
            raise AssertionError(f"{key} unset was accepted")
        except SystemExit as stop:
            assert key in str(stop)
    shipped = config.load()
    assert (shipped["stageb"]["t1_gap"], shipped["funded"]["open_risk_cap"]) == (
        "close_to_open_blocks",
        0.5,
    )  # both the owner's: the cap 2026-10-14, the gap model 2026-10-15
    assert shipped["stageb"]["shared_of"] == "larger"  # owner, 2026-10-05


def test_stage_b_end_to_end() -> None:
    """A synthetic pool through `funded_b.build`: figures per phase, the ledger row, the files."""
    cfg = small_cfg()
    plan = lenient_plan(target=0.04, max_loss=0.10, phases=2, daily_loss=0.05)
    world = complete(
        bar_world(41, 5, "2021-01-04", "2022-01-01", edge=6.0),
        plan,
        cfg,
        {"build": BUILD},
    )
    start = time.perf_counter()
    result = funded_b.build(world, cfg, np.random.default_rng(7))
    wall, b = time.perf_counter() - start, result["stage_b"]
    assert b["n_settings"] == 9
    for _, own in b["rows"].groupby("members"):
        lengths = own.groupby("flavour")[
            "length"
        ].nunique()  # the sweep, plus its own measured one
        assert lengths["T1"] == 1 and lengths["D"] == lengths["T2"] >= 2
        assert len(own) == 9 * (2 * lengths["D"] + 1) and {5, 20} <= set(own["length"])
    assert (
        b["rows"].groupby("members")["measured"].any().all()
    )  # Politis-White read for each
    assert {
        "r_phase1",
        "r_phase2",
        "p_stage1",
        "p_stage2",
        "t_median",
        "fail_daily_loss",
    } <= set(b["rows"])
    assert (b["rows"]["p_stage2"] <= b["rows"]["p_stage1"] + 1e-12).all()
    w = b["winner"]
    floor = b["rows"][
        (b["rows"]["members"] == w["members"]) & (b["rows"]["setting"] == w["setting"])
    ]
    assert (
        w["p"]
        == floor["p_pass"].min()
        == min(w["p_D"], w["p_T1"], w["p_T2"])
        == b["table"]["p"].max()
    )
    shared = [
        len(set(a.split("+")) & set(c.split("+")))
        / min(a.count("+") + 1, c.count("+") + 1)
        for a, c in itertools.combinations(b["table"]["members"], 2)
    ]
    assert max(shared) <= 0.5
    assert result["verdict"] is None and "oos1" in result["reason"]
    assert result["stability"]["runs"] == 3 and not result["stability"]["unstable"]
    assert funded_b.build(world, cfg, np.random.default_rng(7))["stage_b"][
        "rows"
    ].equals(b["rows"])

    real_path = study.path
    with tempfile.TemporaryDirectory() as tmp:
        study.path = lambda s: Path(tmp) / "ledger" / f"{s}.jsonl"
        try:
            members = funded_b._union([b["table"]])
            rows = trials.record_b(
                b,
                {"hash": "feedface" * 8},
                plan["plan_key"],
                {m: world["meta"][m] for m in members},
            )
        finally:
            study.path = real_path
        assert (
            rows[0]["n_scored"] == len(b["table"]) * 9 and rows[0]["segment"] == "build"
        )
        assert rows[0]["study"].startswith("PORTFOLIO_") and len(rows) == 1 + len(
            members
        )
        funded_b.write(Path(tmp), result, {"root_seed": 7})
        assert len(pd.read_parquet(Path(tmp) / "stageb.parquet")) == len(b["rows"])
        assert len(pd.read_parquet(Path(tmp) / "shortlist.parquet")) == len(b["table"])
        assert json.loads((Path(tmp) / "verdict.json").read_text())["verdict"] is None
    assert (
        funded_b.summarise(world, result)
        .splitlines()[-1]
        .startswith("Decisión: NINGUNA")
    )

    tight = dict(
        world, min_size={m: 0.0036 for m in world["identities"]}
    )  # lot 1.2e-4 per unit
    data = funded_b._prepare(tight, world["identities"][:2], BUILD, cfg)
    rows = stageb.evaluate(
        data,
        np.array([0, 1]),
        plan,
        cfg,
        stageb.risk_grid(plan, cfg),
        np.random.default_rng(1),
    )
    low = (rows["r_phase1"] < 0.005) | (rows["r_phase2"] < 0.005)
    assert (
        rows.loc[low, "p_pass"].isna().all() and rows.loc[~low, "p_pass"].notna().all()
    )

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print(
        f"     {len(b['table'])} combinations x 9 risks x {len(b['rows']) // 9 // len(b['table'])} path sets of "
        f"{cfg['stageb']['n_paths']} in {wall:.1f} s (prepare and stability included), peak {peak:.0f} MB"
    )
    assert stageb_run.risk_of(w, plan).shape == (1, 2)


def main() -> None:
    """Run every case; an assertion stops it."""
    for name, case in [(n, c) for n, c in globals().items() if n.startswith("test_")]:
        case()
        print(f"OK   {name}")
    print("test_portfolio_stageb: ok")


if __name__ == "__main__":
    main()
