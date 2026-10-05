"""The hand-off package encargo 33 receives (PLAN §2.2): the chosen portfolio, its daily P&L, its trades."""

import json
from pathlib import Path

import pandas as pd

from . import oos2
from .inputs import source


def write(run: Path, pool_name: str, pool: dict, members: list[str], weights: dict[str, float],
          daily: pd.DataFrame, calendar: dict, verdict: dict, sentence: str, cfg: dict) -> Path:
    """Write `<run>/handoff/`: `portfolio.json`, `daily.parquet`, `trades.parquet`.

    Args:
        run: The run folder; its name is the `run_id`.
        pool_name, pool: The declared pool and `inputs.pool.declared()`'s dict of it.
        members: The chosen identities.
        weights: identity -> weight, by `cfg["weights"]["method"]`.
        daily: days x members daily mark-to-market P&L (the universe's, reference clock).
        calendar: The portfolio calendar.
        verdict: The verdict (`label`, `pass`).
        sentence: Its Spanish decision sentence.
        cfg: The construct config (`relaxed`, `pool.firm`, `equity.reference_clock`).

    Returns:
        The folder. `daily.parquet` is long -- `day, identity, pnl, segment, source` -- and
        `source` is always "rebuild": the universe's table is the engine's M1 rebuild.
        `trades.parquet` is each member's archived trades (orderstocsv schema) + `identity`.
    """
    out = run / "handoff"
    out.mkdir(parents=True, exist_ok=True)
    version = {m["identity"]: m["version"] for m in pool["members"]}
    sources = {i: source.load(i, version[i]) for i in members}
    counted = oos2.counted()
    blob = {"run_id": run.name, "pool": pool_name, "pool_hash": pool["hash"],
            "firm": cfg.get("pool", {}).get("firm"),
            "members": [{"identity": i, "version": version[i], "symbol": s["symbol"],
                         "timeframe": s["timeframe"], "feed": s["feed"], "clock": s["clock"]}
                        for i, s in sources.items()],
            "weights": weights, "weight_method": cfg["weights"]["method"],
            "reference_clock": cfg["equity"]["reference_clock"],
            "verdict": verdict["label"], "pass": verdict["pass"], "sentence": sentence,
            "ledger_study": oos2.pool_study(pool), "ledger_n": counted["n"],
            "relaxed": bool(cfg["relaxed"]), "relaxed_thresholds": cfg["relaxed"],
            "development": any(s["development"] for s in sources.values())}
    (out / "portfolio.json").write_text(json.dumps(blob, indent=2, ensure_ascii=False, default=str),
                                        encoding="utf-8")
    long = (daily[members].rename_axis("day").reset_index()
            .melt("day", var_name="identity", value_name="pnl").dropna(subset=["pnl"]))
    long["segment"] = None
    for name, (lo, hi) in calendar.items():
        long.loc[long["day"].between(lo, hi), "segment"] = name
    long.assign(source="rebuild").to_parquet(out / "daily.parquet", index=False)
    pd.concat([s["trades"].assign(identity=i) for i, s in sources.items()],
              ignore_index=True).to_parquet(out / "trades.parquet", index=False)
    return out
