"""Level 3c of the gate: the strategy against monkeys drawn inside R3's drift window."""

import os
from typing import Any

import numpy as np
import pandas as pd

from core import fanout
from core.study import draws
from engines.nulls import lookup, verdict, windowed
from engines.nulls.model import RUNGS
from studies.screening.analysis import resample, tradelevel

FACTS = ("z_mono", "mono_p", *(f"z_mono_{rung}" for rung in RUNGS), "mono_seed")
DRAWS = "_draws"        # the key a worker hands its distributions back under; no fact
SHIFTED = "_shifted"    # ... and the z and p of the strategy with an edge planted, by edge
HEADLINE = "timing"    # the rung `z_mono` is: same trades, sides and holds, drawn moments

# What the workers read. Set by run() before the pool is built and never written again:
# `fork` hands every worker the bars and the per-trade table without pickling them.
_SHARED: dict = {}


def _one(identity: str) -> dict[str, Any]:
    """One strategy's monkeys, in a worker that inherited its inputs by fork.

    Args:
        identity: The strategy, a key of `_SHARED["oos"]`.

    Returns:
        `z_mono_<rung>` for every rung, and `z_mono` and `mono_p` from the HEADLINE rung. The
        statistic is the mean P/L per trade: the real one is the mean of the per-trade
        table's `pnl`, which the same repricer priced. The rungs share ONE stream,
        `resample.stream(root, "<identity>")`, each reading it from its start (encargo 66, N12 B;
        common random numbers): they enter at the same uniforms and differ by the rung alone,
        and `--only` one rung replays the entries the full run used.
    """
    own, shared = _SHARED["oos"][identity], _SHARED["grid"]
    at = shared["bars"].index
    mine = windowed.located(shared, at.get_indexer(own["open_time"]),
                            at.get_indexer(own["close_time"]), own["lots"].to_numpy(float),
                            own["side"].to_numpy(float), own["window"].to_numpy())
    seen, row, kept, planted = float(own["pnl"].mean()), {}, [], {edge: {} for edge in _SHARED["adds"]}
    for rung in _SHARED["rungs"]:
        drawn = windowed.means(shared, mine, _SHARED["costs"], rung, _SHARED["draws"],
                               resample.stream(_SHARED["seed"], f"{identity}|mono"))
        row[f"z_mono_{rung}"] = windowed.z(seen, drawn)
        if _SHARED["keep"]:
            kept.append(draws.record("gate.3c", f"z_mono_{rung}", seen, drawn, str(identity),
                                     raw=False, rung=rung, seed=_SHARED["seed"],
                                     p="nulls.verdict.pvalue(net)", unit="P/L medio por operación"))
        if rung == HEADLINE:
            row["z_mono"], row["mono_p"] = row[f"z_mono_{rung}"], verdict.pvalue(seen, drawn, "net")
        for edge, got in planted.items():     # the same monkeys read by the strategy with `add` more per trade
            mean = float((own["pnl"] + _SHARED["adds"][edge][identity]).mean())   # NOT mean + add: 9e-16 apart
            got[f"z_mono_{rung}"] = windowed.z(mean, drawn)
            if rung == HEADLINE:
                got["z_mono"], got["mono_p"] = got[f"z_mono_{rung}"], verdict.pvalue(mean, drawn, "net")
    return row | {DRAWS: kept, SHIFTED: planted}


def run(data: dict, alive: pd.Index, cfg: dict) -> pd.DataFrame:
    """The monkey for the strategies alive: oos1 only, at the declared costs.

    Args:
        data: The harvest as `inputs.load` gives it, plus `bars` (the strategies' own
            timeframe), `market` (reads `windows["OOS"]`), `costs` (reprice.costs of the
            feed's oos1) and `oos`, the per-trade table level 1a wrote: reads `identity`,
            `open_time`, `close_time`, `side`, `lots`, `pnl` and `window`.
        alive: Identities still in the cascade.
        cfg: The gate's config; reads `monkey.draws`, `monkey.seed` and `drift.window`.
            Keys only the control sets (`falsePositives.chain`): `keep_draws` False records no
            distribution; `rungs`, the only rungs drawn (the other columns come back empty);
            `shifts`, edge to the money per trade added to each identity, and `shifted`, the
            dict run() fills with, per edge, the facts the strategy would have had with that
            money planted: the monkeys are the same, so they are drawn once.

    Returns:
        Indexed by `alive`. `z_mono`: (the strategy's mean P/L per trade - the mean of that
        mean over its monkeys) / its standard deviation over them, the monkeys re-entering
        every trade at a uniform bar of the calendar window it opened in (`drift.window`,
        the label level 1a gave it), with its side and its hold, sized by ATR at the drawn
        bar and priced by the common repricer. `mono_p`: the empirical p of the same
        comparison. `z_mono_<rung>`: the same z with the hold redrawn, the sizing stripped,
        or both (`windowed.REDRAWS`); `z_mono_timing` is `z_mono`. `mono_seed`: the root the
        draws came from — `monkey.seed`, or fresh when null — the same on every row; given
        back as `monkey.seed` it replays the run bit for bit. Only `z_mono` is judged.
    """
    if not data:       # tests/test_gate_rules.py runs every level on an empty harvest
        return pd.DataFrame(index=alive, columns=pd.Index(FACTS), dtype=float)
    bars, knobs = data["bars"], cfg["monkey"]
    seed = resample.root(knobs["seed"])
    inside = np.arange(len(bars))[bars.index.slice_indexer(*data["market"]["windows"]["OOS"])]
    labels = tradelevel.calendar(bars.index[inside], cfg["drift"]["window"])
    oos = data["oos"][data["oos"]["identity"].isin(alive)]
    _SHARED.update(oos=dict(tuple(oos.groupby("identity", sort=False))), costs=data["costs"],
                   grid=windowed.grid(bars, inside, labels, data.get("session")), draws=knobs["draws"], seed=seed,
                   keep=data.get("keep_draws", True), rungs=data.get("rungs", RUNGS),
                   adds={edge: add.to_dict() for edge, add in data.get("shifts", {}).items()})
    lookup.warm()
    sizes = {identity: len(own) for identity, own in _SHARED["oos"].items()}
    rows = dict(fanout.run(_one, sizes, os.cpu_count() or 1))
    draws.save(data.get("out"), [d for identity in sorted(rows) for d in rows[identity].pop(DRAWS)])
    shifted = {identity: row.pop(SHIFTED) for identity, row in rows.items()}
    for edge in _SHARED["adds"]:
        data["shifted"][edge] = (pd.DataFrame.from_dict({i: got[edge] for i, got in shifted.items()}, orient="index")
                                 .reindex(index=alive, columns=pd.Index(FACTS)).assign(mono_seed=float(seed)))
    facts = pd.DataFrame.from_dict(rows, orient="index").reindex(index=alive, columns=pd.Index(FACTS))
    return facts.assign(mono_seed=float(seed))
