"""Every strategy of one export judged on breadth: the verdict /curate applies, as one result."""

import os
import time
from functools import lru_cache

import pandas as pd

from core import fanout, tradestore
from core.study import blocks, result as envelope
from studies.transfer.crossmarket.mechanics import envelope as window
from studies.transfer.crossmarket.orchestrate import market as market_run
from studies.transfer.crossmarket.simulate import backtest
from studies.transfer.crossmarket.verdict import breadth, inference

COLUMNS = ["strategy", "identity", "verdict", "reason", "markets", "cleared", "fraction",
           "under_alpha", "paired_under_alpha", "edge_r", "worst_pf", "pf_cv", "family",
           "missing", "warnings"]

# What the workers read: the whole export and every feed's bars, which is gigabytes. Set
# once before the pool is built and never written again, so `fork` hands each worker the
# same pages instead of pickling them one per strategy.
_SHARED: dict = {}


@lru_cache(maxsize=4)
def _base(name: str) -> dict:
    """The strategy on its own base asset, which every market's fingerprint compares against.

    Cached because the same worker usually draws several markets of one strategy: the tasks
    are queued longest first, and a strategy's markets are close in length.
    """
    got = _SHARED["inputs"]
    main = got["universe"]["main"]
    trades = tradestore.market(got["trades"], name, main)
    bars = window.window(trades, got["bars"][main])
    return {**backtest.setting(trades, bars, _SHARED["cfg"]), "bars": bars}


def _market(task: tuple[str, str]) -> dict:
    """One strategy on one market, in a worker that inherited the export by fork.

    The unit of work is the market, not the strategy: 🔬 2026-09-25, on 96 strategies the
    largest one alone took 453 s and set the wall clock from 24 processes up, while its nine
    markets are independent — every model and test seeds its own generator.
    """
    name, feed = task
    got = _SHARED["inputs"]
    market = next(m for m in got["universe"]["markets"] if m["feed"] == feed)
    return market_run.verdict_row(_SHARED["cfg"], market,
                                  tradestore.market(got["trades"], name, feed),
                                  got["bars"][feed], _base(name))


def row(name: str, rows: list[dict], missing: int, inputs: dict, cfg: dict) -> dict:
    """One strategy's line: its breadth, its verdict, and the numbers beside it."""
    per_market = pd.DataFrame(rows)
    got = {"family": inference.family(per_market), "missing": missing,
           **breadth.summary(per_market, cfg["diagnostics"]["alpha"])}
    verdict, reason = breadth.judge(got, cfg["verdict"]["breadth_floor"])
    return {"strategy": name, "identity": inputs["identity"].get(name), "verdict": verdict,
            "reason": reason, "markets": got["markets"], "cleared": got["cleared"],
            "fraction": round(got["fraction"], 4), "under_alpha": got["under_alpha"],
            "paired_under_alpha": got["paired_under_alpha"], "edge_r": round(got["edge_r"], 6),
            "worst_pf": round(got["worst_market"]["pf"], 4), "pf_cv": round(got["pf_cv"], 4),
            "family": got["family"], "missing": got["missing"], "warnings": got["warnings"]}


def population(table: pd.DataFrame, cfg: dict, started: float) -> dict:
    """The export read as one result: how many kept, and every strategy's breadth."""
    kept = int((table.verdict == "MANTENER").sum())
    floor = cfg["verdict"]["breadth_floor"]
    return envelope.envelope(
        "studies.transfer.crossmarket", None, None, cfg, started,
        [envelope.tab("summary", "Amplitud", [
            {"kind": "bars", "title": "Fracción de mercados con la esperanza sobre cero",
             "unit": "", "reference": floor,
             "items": [{"label": r.strategy, "value": r.fraction, "error": None,
                        "state": "pass" if r.verdict == "MANTENER" else "fail"}
                       for r in table.itertuples()]},
            blocks.table("Estrategia a estrategia", table.drop(columns=["identity"]))])],
        blocks.verdict(f"{kept} de {len(table)}", "pass" if kept else "fail",
                       f"{kept} estrategias con al menos el {floor:.0%} de sus mercados con el "
                       f"intervalo de la esperanza por encima de cero. Es la única criba; los "
                       f"p-valores no deciden."))


def run(inputs: dict, cfg: dict, workers: int = 0) -> dict:
    """Every (strategy, market) it traded on, one task each, longest first.

    Args:
        inputs: What load.load() returned.
        cfg: What config.load() returned.
        workers: Markets studied at once; 0 is every core. Each holds its own null batches,
            so this is the knob that trades RAM for wall clock.

    Returns:
        {"population": the export's result, "table": one row per strategy}. No per-strategy
        contract: judging breadth needs the headline null only, and the full analysis of a
        strategy — one.run() — is minutes of simulation the verdict never reads.
    """
    started = time.time()
    feeds = {m["feed"] for m in inputs["universe"]["markets"]}
    trades = inputs["trades"][inputs["trades"]["Symbol"].isin(feeds)]
    counts = trades.groupby(["strategy", "Symbol"], observed=True).size()
    traded = trades.groupby("strategy", observed=True).size()
    # A strategy that never fired on one of the other markets has nothing to judge; it is a
    # result about the strategy, written as one, and it never reaches a worker.
    silent = [{**dict.fromkeys(COLUMNS, ""), "strategy": n, "identity": inputs["identity"].get(n),
               "verdict": "DESCARTAR", "markets": 0, "cleared": 0, "fraction": 0.0,
               "missing": len(feeds), "reason": f"no disparó ni una vez en ninguno de los "
                                                f"{len(feeds)} mercados: no hay nada que juzgar"}
              for n in inputs["strategies"] if int(traded.get(n, 0)) == 0]
    wanted = [n for n in inputs["strategies"] if int(traded.get(n, 0))]
    order = [m["feed"] for m in inputs["universe"]["markets"]]
    costs = {(n, f): int(counts.get((n, f), 0)) for n in wanted for f in order
             if counts.get((n, f), 0) > 0}
    left = {n: sum(1 for k in costs if k[0] == n) for n in wanted}
    _SHARED.update(inputs=inputs, cfg=cfg)
    # The smallest task, run here first: every kernel specialisation gets compiled in the
    # parent, and the fork hands the machine code to every worker instead of each compiling.
    _market(min(costs, key=costs.get))
    done, rows = {n: {} for n in wanted}, list(silent)
    for (name, feed), market_row in fanout.run(_market, costs, workers or os.cpu_count()):
        done[name][feed] = market_row
        if len(done[name]) < left[name]:
            continue
        line = row(name, [done[name][f] for f in order if f in done[name]],
                   len(feeds) - left[name], inputs, cfg)
        del done[name]
        rows.append(line)
        envelope.progress(100 * (len(rows) - len(silent)) // max(len(wanted), 1),
                          f"{name} {line['verdict']} — {line['reason']}")
    table = pd.DataFrame(rows)[COLUMNS].sort_values(
        "strategy", key=lambda s: s.map(inputs["strategies"].index))
    return {"population": population(table, cfg, started), "table": table}
