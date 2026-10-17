"""Level 3a and 3b of the gate: homogeneity of the excess across quarters, and the drawdown against its resampled own."""

import os
from typing import Any

import numpy as np
import pandas as pd

from core import fanout, metrics
from core.study import draws
from engines.market import tradelevel
from studies.screening.analysis import resample

FACTS = ("q_p", "q_seed", "dd_p", "dd_esperado_r", "dd_seed")
DRAWS = "_draws"  # the key a worker hands its distributions back under; no fact

# What the workers read. Set by run() before the pool is built and never written again:
# `fork` hands every worker the per-trade tables without pickling them.
_SHARED: dict = {}


def _one(identity: str) -> dict[str, Any]:
    """One strategy's two resamplings, in a worker that inherited its inputs by fork.

    Args:
        identity: The strategy, a key of `_SHARED["oos"]`.

    Returns:
        `q_p`, `dd_p` and `dd_esperado_r` as run() defines them, and under DRAWS the
        distributions to record. Each stream is `resample.stream(root, str(identity))`: it
        depends on the root and the identity only, so the result does not depend on how many
        workers there are or in what order they run.
    """
    s, mine = _SHARED, _SHARED["oos"][identity]
    row, kept = {"q_p": np.nan}, []
    if (
        s["q_p"] is not None
    ):  # planted copy of a population already measured: Q is centred, the plant moves nothing
        row["q_p"] = s["q_p"][identity]
    else:
        order = np.argsort(mine["period"].to_numpy(), kind="stable")
        sizes = resample.periods(mine["period"].to_numpy(), s["spread"]["min_trades"])
        if len(sizes) >= 2:
            between, seen, slack = resample.q_null(
                mine["excess"].to_numpy(float)[order],
                sizes,
                s["spread"]["permutations"],
                resample.stream(s["q_seed"], str(identity)),
            )
            row["q_p"] = resample.p_upper(between, seen, slack)
            if s["keep"]:
                kept.append(
                    draws.record(
                        "gate.3b",
                        "q_p",
                        seen,
                        between,
                        str(identity),
                        seed=s["q_seed"],
                        p="resample.p_upper",
                        unit="Q entre periodos",
                    )
                )
    if identity in s["build"]:
        pnl, fall = mine["pnl"].to_numpy(float), s["fall"]
        simulated = resample.null_drawdowns(
            s["build"][identity],
            pnl.mean(),
            len(pnl),
            fall["block"],
            fall["sequences"],
            resample.stream(s["dd_seed"], str(identity)),
        )
        row["dd_p"] = resample.p_upper(
            simulated, metrics.dd_money(metrics.cumulative(pnl))
        )
        row["dd_esperado_r"] = np.percentile(simulated, fall["percentile"]) / s["risk"]
        if s["keep"]:
            kept.append(
                draws.record(
                    "gate.3a",
                    "dd_p",
                    metrics.dd_money(metrics.cumulative(pnl)),
                    simulated,
                    str(identity),
                    seed=s["dd_seed"],
                    p="resample.p_upper",
                    unit="drawdown máximo, divisa de la cuenta",
                    risk=s["risk"],
                )
            )
    return row | {DRAWS: kept}


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """R7 and R6 for the strategies alive.

    Args:
        data: The harvest as `inputs.load` gives it, plus `oos`, the per-trade table of oos1
            (`operaciones.parquet`), `build`, the same table of the build's trades (`identity`
            and `pnl`, in close-time order within each identity), and `market["risk"]`, 1R.
        alive: Identities still in the cascade.
        cfg: The gate's config; reads `homogeneity` and `drawdown`. A strategy per process
            (`core.fanout`); `data["keep_draws"]` False records no distribution (the control
            nobody reads), and `data["q_p"]`, a Series by identity, is taken as `q_p` instead
            of drawn again (the same population with an edge planted).

    Returns:
        Indexed by `alive`. `q_p`: permutation p of the Q of homogeneity of the oos1 excess
        across the calendar periods the trades opened in (`homogeneity.period`, periods under
        `homogeneity.min_trades` joined to the next). `dd_p`: the share of block-bootstrapped
        sequences of the build's P/L, shifted to oos1's mean and as long as oos1, whose maximum
        drawdown reaches oos1's own; `dd_esperado_r`: their `drawdown.percentile`
        (95 as shipped), in R. `q_seed`
        and `dd_seed` are the roots each resampling used — the config's, or fresh when null.
        A strategy with no build trades has no `dd_*`; one with a single period, no `q_p`.
    """
    if not data:  # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=pd.Index(FACTS), dtype=float)
    spread, fall, risk = cfg["homogeneity"], cfg["drawdown"], data["market"]["risk"]
    q_seed, dd_seed = (
        resample.root(spread["seed"]),
        resample.root(fall["seed"]),
    )  # once, here: a worker never draws its own
    oos = data["oos"][data["oos"]["identity"].isin(alive)]
    period = tradelevel.calendar(oos["open_time"], spread["period"])
    mine = {
        identity: own
        for identity, own in oos.assign(period=period).groupby("identity", sort=False)
    }
    cached = data.get("q_p")
    _SHARED.update(
        oos=mine,
        build={
            key: pnl.to_numpy(float)
            for key, pnl in data["build"].groupby("identity")["pnl"]
        },
        spread=spread,
        fall=fall,
        risk=risk,
        q_seed=q_seed,
        dd_seed=dd_seed,
        keep=data.get("keep_draws", True),
        q_p=None if cached is None else cached.to_dict(),
    )
    resample.warm()
    rows = dict(
        fanout.run(
            _one,
            {identity: len(own) for identity, own in mine.items()},
            os.cpu_count() or 1,
        )
    )
    draws.save(
        data.get("out"),
        [d for identity in sorted(rows) for d in rows[identity].pop(DRAWS)],
    )
    facts = pd.DataFrame.from_dict(rows, orient="index").reindex(
        index=alive, columns=pd.Index(FACTS)
    )
    return facts.assign(q_seed=float(q_seed), dd_seed=float(dd_seed))
