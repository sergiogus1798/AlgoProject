"""The siblings table and the mothers table: every sibling measured in each window, then judged."""

from typing import Any, cast

import numpy as np
import pandas as pd

from core import fanout
from core.study import draws
from engines.market import reprice
from studies.screening.analysis import centred
from studies.transfer.crossTF.tf import null, rules

TEST = "crossTF.tf"
BAR = {"M15": 900, "M30": 1800, "H1": 3600, "H4": 14400, "D1": 86400}  # seconds per bar
MEASURED = [
    "n_oos1",
    "n_mother_oos1",
    "e_oos1",
    "e_mother_oos1",
    "z_delta",
    "overlap_oos1",
    "n_build",
    "n_mother_build",
    "e_build",
    "e_mother_build",
    "z_build",
    "overlap_build",
    "phi",
]
SIBLINGS = [
    "mother",
    "sibling",
    "timeframe",
    "role",
    "ratio",
    "rounding_shift",
    "clamped",
    "unverified",
    "t0",
    *MEASURED[:6],
    "ret",
    "t2a",
    "t2a_why",
    *MEASURED[6:12],
    "t2b",
    "t2b_why",
    "ret_build",
    "ret_build_pct",
    "phi",
    "z_frec",
    "t1",
    "t1_why",
]
MOTHERS = [
    "strategy",
    "identity",
    "source_tf",
    "t1",
    "t2a",
    "t2b",
    "t3",
    "phase1",
    "state",
    "why",
    "seed",
    "draws",
]


def windows(cuts: dict) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """The two windows as [start, end), from the asset's cuts."""
    return {"oos1": (cuts["oos1"], cuts["end"]), "build": (cuts["build"], cuts["oos1"])}


def _phi(build: pd.DataFrame, mothers: list[str], cuts: dict, f: dict) -> pd.Series:
    """The bounded overdispersion of each mother's yearly trade counts in the build."""
    exposure = centred.calendar_exposure(
        cuts["build"], cuts["oos1"] - pd.Timedelta(seconds=1)
    )
    mine = build[build["strategy"].isin(mothers)]
    by_year = pd.crosstab(
        mine["strategy"].astype(str), cast(pd.Series, mine["Open time"]).dt.year
    ).reindex(index=mothers, columns=exposure.index, fill_value=0)
    return centred.dispersion(by_year, exposure, f["phi_min"], f["phi_max"]).where(
        by_year.sum(axis=1) > 0
    )


def measure(
    made: pd.DataFrame,
    trades: dict[str, pd.DataFrame | None],
    bars: dict[str, pd.DataFrame],
    costs: dict[str, reprice.Costs],
    cuts: dict,
    params: dict,
    tf: dict,
    source: str,
    sink: list | None = None,
) -> pd.DataFrame:
    """Every sibling against her mother through the joint random runs, window by window.

    Args:
        made: One row per sibling: `mother`, `sibling` (her name), `timeframe`, and what the
            fabrication did (`ratio`, `rounding_shift`, `clamped`, `unverified`).
        trades: {"oos1": frame, "build": frame or None}; each frame holds `strategy` (a mother's
            or a sibling's name), `Open time`, `Close time`, `Type`. None = that window was
            not run: its columns stay empty.
        bars: {timeframe: the asset's bars}, the mothers' timeframe and every sibling's.
        costs: {"oos1": ..., "build": ...}, the asset's `reprice.costs` at each segment.
        cuts: `build`, `oos1`, `end` of the asset.
        params: The doctrine's money management.
        tf: The `tf` section of config.yaml.
        source: The mothers' timeframe.
        sink: When given, the `core.study.draws` rows of every `z_build` and `z_delta` are
            appended to it (observed = the real total R, or delta per trade).

    Returns:
        `made` plus MEASURED. A strategy with no row in a window's frame has no data there
        (NaN), never 0 trades.
    """
    cal, shifts = null.calendar(
        cast(pd.Timestamp, min(b.index[0] for b in bars.values())),
        cast(pd.Timestamp, max(b.index[-1] for b in bars.values())),
        cuts,
        tf["runs"],
    )
    out = made.reindex(columns=[*made.columns, *MEASURED]).astype(
        {k: float for k in MEASURED}
    )
    for window, span in windows(cuts).items():
        got = trades.get(window)
        if got is None:
            continue
        got = got[(got["Open time"] >= span[0]) & (got["Open time"] < span[1])]
        grid = null.grids(bars, costs[window], params, cal, shifts, span, tf["runs"])
        by = {
            k: g.reset_index(drop=True)
            for k, g in got.groupby("strategy", observed=True)
        }
        groups = dict(tuple(made.groupby("mother")))
        _SHARED.update(
            groups=groups,
            by=by,
            source=source,
            grid=grid,
            cal=cal,
            shifts=shifts,
            tf=tf,
        )
        # One mother with her siblings per task: they share a run, nothing is shared between mothers.
        ran = dict(
            fanout.run(_mother, {m: len(h) for m, h in groups.items()}, fanout.CORES)
        )
        for mother, hers in groups.items():
            members = {source: by.get(mother)} | {
                r.timeframe: by.get(r.sibling) for r in cast(Any, hers.itertuples())
            }
            cells = ran[mother]
            mum = cells.get(source)
            for r in cast(Any, hers.itertuples()):
                me = cells.get(r.timeframe)
                if mum:
                    out.loc[r.Index, [f"n_mother_{window}", f"e_mother_{window}"]] = (
                        mum["n"],
                        null.edge(mum),
                    )
                if me:
                    out.loc[r.Index, [f"n_{window}", f"e_{window}"]] = (
                        me["n"],
                        null.edge(me),
                    )
                where: dict[str, Any] = dict(
                    strategy=r.sibling,
                    mother=mother,
                    sibling=r.sibling,
                    timeframe=r.timeframe,
                    window=window,
                    seed=tf["runs"]["seed"],
                )
                if window == "build" and me:
                    out.loc[r.Index, "z_build"] = null.z_total(me)
                    if sink is not None and me["n"] > 0:
                        sink.append(
                            draws.record(
                                TEST, "z_build", float(me["real"]), me["null"], **where
                            )
                        )
                if mum and me:
                    out.loc[r.Index, f"overlap_{window}"] = rules.overlap(
                        cast(pd.DataFrame, members[source])["Open time"].to_numpy(),
                        cast(pd.DataFrame, members[r.timeframe])[
                            "Open time"
                        ].to_numpy(),
                        BAR[source],
                    )
                    if window == "oos1":
                        out.loc[r.Index, "z_delta"] = null.z_delta(mum, me)
                        diff = null.delta(mum, me)
                        if sink is not None and diff is not None:
                            sink.append(draws.record(TEST, "z_delta", *diff, **where))
    built = trades.get("build")
    if built is not None:
        phi = _phi(built, sorted(made["mother"].unique()), cuts, tf["frequency"])
        out["phi"] = out["mother"].map(phi)  # pyright: ignore[reportArgumentType]  # pandas stubs reject a Series mapper
    return out


_SHARED: dict = {}  # set by `measure` before the fork, read by `_mother` in the workers


def _mother(mother: str) -> dict:
    """`null.runs` of one mother and her siblings in one window, in a worker that inherited the inputs."""
    g = _SHARED
    members = {g["source"]: g["by"].get(mother)} | {
        r.timeframe: g["by"].get(r.sibling)
        for r in cast(Any, g["groups"][mother].itertuples())
    }
    return null.runs(
        {k: v for k, v in members.items() if v is not None},
        g["grid"],
        g["cal"],
        g["shifts"],
        g["tf"]["runs"],
    )


def blank(made: pd.DataFrame) -> pd.DataFrame:
    """The table of a batch nothing could be measured on (no cost card): MEASURED all empty."""
    return made.reindex(columns=[*made.columns, *MEASURED]).astype(
        {k: float for k in MEASURED}
    )


def judge(table: pd.DataFrame, tf: dict, source: str, reason: str = "") -> pd.DataFrame:
    """T0, T1, T2a and T2b for every sibling, each state with why it has no data.

    Args:
        table: What measure() or blank() returned.
        tf: The `tf` section of config.yaml.
        source: The mothers' timeframe.
        reason: Why the whole batch has no data ("no_cost_card", ...); "" when it has.

    Returns:
        SIBLINGS. A state without data is "limbo" and its `_why` says what is missing; "" in
        `_why` means the state was measured. The population of T1's centre and of the build
        retention's percentile is this batch's comparable siblings of the same timeframe.
    """
    t, c, f = cast(Any, table.copy()), tf["comparable"], tf["frequency"]
    t["role"] = np.select(
        [
            t["timeframe"].isin(tf["neighbours"].get(source, [])),
            t["timeframe"] == tf["far"].get(source),
        ],
        ["neighbour", "far"],
        "note",
    )
    t["t0"] = rules.comparable(t, c["rounding_shift"])
    base = pd.Series(reason, index=t.index)
    least = c["min_trades"]
    no_build = pd.Series(
        np.where(t["n_build"].isna(), "no_build_data", ""), index=t.index
    )

    positive = pd.Series(
        np.where(t["e_mother_oos1"] > 0, "", "mother_e_not_positive"), index=t.index
    )
    t["t2a_why"] = rules.why(
        base,
        t["t0"],
        rules.few(t["n_oos1"], least),
        rules.few(t["n_mother_oos1"], least, "mother_few_trades"),
        positive,
    )
    t["ret"] = (t["e_oos1"] / t["e_mother_oos1"]).where(t["e_mother_oos1"] > 0)
    live = t["t2a_why"] == ""
    t["t2a"] = rules.t2a(
        t["ret"].where(live), t["z_delta"].where(live), tf["retention"]
    )

    t["t2b_why"] = rules.why(base, t["t0"], no_build, rules.few(t["n_build"], least))
    t["t2b"] = rules.t2b(t["z_build"].where(t["t2b_why"] == ""), tf["build"])
    ok = (t["t2b_why"] == "") & (t["e_mother_build"] > 0)
    t["ret_build"] = (t["e_build"] / t["e_mother_build"]).where(ok)
    t["ret_build_pct"] = rules.percentile(
        t["ret_build"], t["timeframe"], f["min_population"]
    )

    n_s, n_m = t["n_build"] + t["n_oos1"], t["n_mother_build"] + t["n_mother_oos1"]
    no_mother = pd.Series(
        np.where(t["n_mother_build"].isna(), "no_build_data", ""), index=t.index
    )
    before = rules.why(
        base,
        t["t0"],
        no_build,
        no_mother,
        rules.few(n_s, least),
        rules.few(n_m, least, "mother_few_trades"),
    )
    log_ratio = np.log(n_s / n_m).where(before == "")
    m_pop = rules.centre(log_ratio, t["timeframe"], f["min_population"])
    t["z_frec"] = rules.z_frec(n_m, n_s, t["phi"], m_pop).where(before == "")
    t["t1_why"] = rules.why(
        before,
        pd.Series(np.where(m_pop.notna(), "", "population_below_min"), index=t.index),
    )
    t["t1"] = rules.t1(t["z_frec"].where(t["t1_why"] == ""), f)
    return t[SIBLINGS]


def mothers(
    siblings: pd.DataFrame, tf: dict, source: str, identity: dict
) -> pd.DataFrame:
    """One row per mother: §6 over her siblings, and the draw it was measured with.

    Args:
        siblings: What judge() returned.
        tf: The `tf` section of config.yaml.
        source: The mothers' timeframe.
        identity: Mother name to identity; a missing one stays empty.

    Returns:
        MOTHERS.
    """
    expected, low = len(tf["neighbours"].get(source, [])), tf["retention"]["low"]
    rows = [
        {
            "strategy": m,
            "identity": identity.get(m),
            "source_tf": source,
            **rules.mother(g, expected, low),
            "seed": tf["runs"]["seed"],
            "draws": tf["runs"]["draws"],
        }
        for m, g in siblings.groupby("mother")
    ]
    return pd.DataFrame(rows, columns=pd.Index(MOTHERS))
