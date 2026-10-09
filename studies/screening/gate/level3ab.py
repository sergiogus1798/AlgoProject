"""Level 3a and 3b of the gate: homogeneity of the excess across quarters, and the drawdown against its resampled own."""

import numpy as np
import pandas as pd

from core.study import draws
from studies.screening.analysis import resample, tradelevel

FACTS = ("q_p", "q_seed", "dd_p", "dd_esperado_r", "dd_seed")


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """R7 and R6 for the strategies alive.

    Args:
        data: The harvest as `inputs.load` gives it, plus `oos`, the per-trade table of oos1
            (`operaciones.parquet`), `build`, the same table of the build's trades (`identity`
            and `pnl`, in close-time order within each identity), and `market["risk"]`, 1R.
        alive: Identities still in the cascade.
        cfg: The gate's config; reads `homogeneity` and `drawdown`.

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
    if not data:       # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=list(FACTS), dtype=float)
    spread, fall, risk = cfg["homogeneity"], cfg["drawdown"], data["market"]["risk"]
    q_seed, dd_seed = resample.root(spread["seed"]), resample.root(fall["seed"])
    oos = data["oos"][data["oos"]["identity"].isin(alive)]
    period = tradelevel.calendar(oos["open_time"], spread["period"])
    build = {key: pnl.to_numpy(float) for key, pnl in data["build"].groupby("identity")["pnl"]}
    rows, kept = {}, []
    for identity, mine in oos.assign(period=period).groupby("identity", sort=False):
        order = np.argsort(mine["period"].to_numpy(), kind="stable")
        sizes = resample.periods(mine["period"].to_numpy(), spread["min_trades"])
        row = {"q_p": np.nan}
        if len(sizes) >= 2:
            between, seen, slack = resample.q_null(
                mine["excess"].to_numpy(float)[order], sizes, spread["permutations"],
                resample.stream(q_seed, str(identity)))
            row["q_p"] = resample.p_upper(between, seen, slack)
            kept.append(draws.record("gate.3b", "q_p", seen, between, str(identity), seed=q_seed,
                                     p="resample.p_upper", unit="Q entre periodos"))
        if identity in build:
            pnl = mine["pnl"].to_numpy(float)
            simulated = resample.drawdowns(build[identity], pnl.mean(), len(pnl), fall["block"],
                                           fall["sequences"], resample.stream(dd_seed, str(identity)))
            row["dd_p"] = resample.p_upper(simulated, resample.max_drawdown(pnl))
            row["dd_esperado_r"] = np.percentile(simulated, fall["percentile"]) / risk
            kept.append(draws.record("gate.3a", "dd_p", float(resample.max_drawdown(pnl)), simulated,
                                     str(identity), seed=dd_seed, p="resample.p_upper",
                                     unit="drawdown máximo, divisa de la cuenta", risk=risk))
        rows[identity] = row
    draws.save(data.get("out"), kept)
    facts = pd.DataFrame.from_dict(rows, orient="index").reindex(index=alive, columns=list(FACTS))
    return facts.assign(q_seed=float(q_seed), dd_seed=float(dd_seed))
