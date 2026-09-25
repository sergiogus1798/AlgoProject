"""Every strategy of one export through one.run, and the databank read as one result."""

import os
import time

import pandas as pd

from core import fanout
from core.study import blocks, result as envelope
from strategies.monteCarlo import one
from strategies.monteCarlo.contract.shapes import TIER_STATE
from strategies.monteCarlo.contract.words import TITLES
from strategies.monteCarlo.simulate import engine, kernel
from strategies.monteCarlo.verdict import scoring

# What every strategy's worker reads, set before the fork.
_SHARED: dict = {}
COLUMNS = ["strategy", "identity", "verdict", "trades", "composite", "score_A", "score_B",
           "score_C", "score_D", "score_E", "net", "dd_pct", "ret_dd", "dd_pct_95", "dd_pct_99",
           "inflation", "net_5", "pf_5", "oos_ratio", "outlier_share", "windows_ok",
           "high_vol_net", "stitched_dd_pct", "psr", "gates", "flags", "confidence"]


def _strategy(name: str) -> dict:
    """One strategy's whole result, in a worker process of its own."""
    return one.run(name, _SHARED["inputs"], _SHARED["cfg"])


def table(members: list[dict]) -> pd.DataFrame:
    """One row per strategy: its verdict and the numbers every gate read."""
    rows = [{"strategy": m["strategy"], "identity": m["identity"],
             "verdict": m["summary"]["tier"], **m["summary"]} for m in members]
    return pd.DataFrame(rows)[COLUMNS].sort_values("composite", ascending=False)


def population(members: list[dict], inputs: dict, cfg: dict, started: float) -> dict:
    """The databank read as one result: how many passed, why the rest fell, every row."""
    rows = table(members)
    fired = pd.DataFrame([f for m in members for f in m["summary"]["fired"]],
                         columns=["family", "test", "value", "limit", "gate"])
    vetoes = fired[fired.gate.astype(bool)].test.value_counts()
    passed = int(rows.verdict.isin(scoring.VERDICTS[:3]).sum())
    stab = inputs["shared"]["stability"]
    counts = rows.verdict.value_counts()
    verdict = blocks.verdict(
        f"{passed} de {len(rows)}", "pass" if passed else "fail",
        f"{passed} estrategias pasan sin ningún veto con {cfg['global']['n_sims']:,} "
        f"simulaciones por prueba. Cada una llega aquí ya con edge: esto mide de qué depende, "
        f"no si existe.")
    tabs = [envelope.tab("summary", "Resumen", [
        {"kind": "bars", "title": "Veredictos", "unit": "estrategias", "reference": None,
         "items": [{"label": t, "value": int(counts.get(t, 0)), "error": None,
                    "state": TIER_STATE[t]} for t in scoring.VERDICTS]},
        {"kind": "bars", "title": "Lo que tumbó a las que cayeron", "unit": "estrategias",
         "reference": None, "note": "Cada veto, cuántas estrategias descartó.",
         "items": [{"label": TITLES[t], "value": int(n), "error": None, "state": "fail"}
                   for t, n in vetoes.items()]}]),
        envelope.tab("strategies", "Estrategia a estrategia", [blocks.table(
            "Todas, de mayor a menor compuesto", rows.drop(columns=["identity"]))]),
        envelope.tab("method", "Estabilidad del propio Monte Carlo", [blocks.table(
            "Cuánto se mueve cada número que decide", pd.DataFrame(
                [[k, v["mean"], v["spread"]] for k, v in stab["by_number"].items()],
                columns=["número", "media", "dispersión relativa"]),
            f"{stab['runs']} repeticiones sobre {inputs['reference']}. "
            + ("Demasiado: sube n_sims." if stab["unstable"] else
               "Por debajo de la tolerancia: las cifras que deciden son estables."))])]
    warnings = ([{"code": "inestable", "state": "fail",
                  "text": f"{stab['worst']} se mueve un {stab['worst_spread']:.1%} entre "
                          f"repeticiones: sube global.n_sims."}] if stab["unstable"] else [])
    return envelope.envelope(one.MODULE, None, None, cfg, started, tabs, verdict, warnings)


def run(inputs: dict, cfg: dict) -> dict:
    """Every strategy, one process each, the longest first.

    Args:
        inputs: What load.load() returned.
        cfg: What config.load() returned.

    Returns:
        {"population": the databank's result, "members": one result per strategy}.
    """
    started = time.time()
    streams = inputs["streams"]
    engine.SERIAL = len(streams) > 1
    # 🔬 2026-09-25: one strategy per process with its sub-tests serial inside beat giving
    # each sub-test 10 to 50 chunks, which left most of 96 cores idle. The stability pool
    # is shut first: a pool's threads must not be forked.
    engine.close()
    kernel.prime()
    _SHARED.update(inputs=inputs, cfg=cfg)
    costs = {n: int(s["pnl"].size) for n, s in streams.items()}
    workers = cfg["global"]["max_workers"] or os.cpu_count()
    members = {}
    for i, (name, got) in enumerate(fanout.run(_strategy, costs, workers), 1):
        members[name] = got
        envelope.progress(100 * i // len(streams),
                          f"{name}: {got['summary']['tier']} {got['summary']['composite']:.0f}")
    ordered = [members[n] for n in streams]
    return {"population": population(ordered, inputs, cfg, started), "members": ordered}
