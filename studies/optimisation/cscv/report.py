#!/usr/bin/env python3
"""Step 18 over variant batches: the CSCV's four outputs against their null, the state, the ledger's looks."""

from typing import Any
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from core.study import blocks, draws, output, result as envelope, verdicts
from core.study.config import fingerprint
from engines.variants import look
from engines.variants.panel import SEGMENTS
from studies.optimisation.cscv import contract, many, words
from studies.optimisation.cscv.inputs import batch, config

MODULE = "studies.optimisation.cscv"
STEP = 18
# The sixteen blocks cover the whole history, so every look reads the three segments, oos2
# included: the step belongs to the blind block.
READS = SEGMENTS
SUMMARY = (
    "estado",
    "n",
    "p_perdida",
    "pbo",
    "pbo_p",
    "pbo_sobre_p95",
    "orden_estable",
    "beta",
    "r2",
    "hc",
    "duplicados_pct",
)
PARTITIONS, DRAWS = "cscv_particiones.parquet", "cscv_sorteos.parquet"
NO_TRADES = (
    "{work}: no hay variant_trades.parquet. El paso 18 lee el exceso semanal de las "
    "operaciones de cada variante; vuelve a recoger el lote con /variants (paso 16.5)."
)


def result(
    name: str, got: dict, perf: dict, cells: batch.Weekly, cfg: dict, started: float
) -> dict[str, Any]:
    """The contract's result of one mother, with the facts the autopilot judges.

    Args:
        name: The batch folder's name, the mother's with underscores.
        got: One mother of `many.run`.
        perf: The queue's own numbers.
        cells: What `inputs.batch.read` returned: its wall time and whether it was the cache.
        cfg: The study's config.
        started: time.time() when the run began.

    Returns:
        The validated result plus `facts` (the plan's contract for step 18) and
        `rendimiento`: wall and CPU seconds of each part, processes, draws and peak memory.
    """
    facts = got["facts"]
    cost = {
        "panel_s": cells["wall_s"],
        "panel_de_cache": cells["cached"],
        **perf,
        "cpu_s": got.get("cpu_s", {}),
        "presupuesto_s": cfg["perf"]["budget_s"],
    }
    out = envelope.envelope(
        MODULE,
        name,
        None,
        cfg,
        started,
        contract.tabs(got, perf, cfg),
        contract.verdict(facts, cfg),
        glossary=words.GLOSSARY,
        warnings=[
            {"code": "cscv", "state": "watch", "text": note} for note in got["notes"]
        ],
        summary={k: facts.get(k) for k in SUMMARY} | facts.get("potencia", {}),
    )
    return out | {"facts": blocks.plain(facts), "rendimiento": blocks.plain(cost)}


def detail(out: Path, got: dict) -> None:
    """The heavy detail nobody loads to decide: one row per partition, one per draw.

    Args:
        out: The batch's `estudios/`.
        got: One measured mother of `many.run`.
    """
    found = got["found"]
    rows = {
        "variante": got["names"][found["pick"]],
        "sr_dentro": found["sr_in"] * contract.YEAR,
        "sr_fuera": found["sr_out"] * contract.YEAR,
        "omega": found["omega"],
        "lambda": np.log(found["omega"] / (1 - found["omega"])),
    }
    if "track_out" in found:
        rows |= {
            "madre_sr_fuera": found["track_out"] * contract.YEAR,
            "madre_omega": found["track_omega"],
        }
    pd.DataFrame(rows).to_parquet(out / PARTITIONS)
    pd.concat(got["draws"], names=["tipo", "sorteo"]).reset_index().to_parquet(
        out / DRAWS
    )


def record(name: str, got: dict, seed: int) -> list[dict]:
    """The nulls behind `pbo_p`, `beta_p`, the gross `pbo_p` and `p_perdida_sobre_p95`."""
    real, gross, null = got["read"]["real"], got["read"]["bruto"], got["draws"]
    where = {"strategy": name, "seed": seed}
    return [
        draws.record(
            "cscv", metric, seen, null[kind][field], **where, p="flip.tails", unit=unit
        )
        for metric, seen, kind, field, unit in (
            ("pbo_p", real["pbo"], "nulo", "pbo", "PBO"),
            ("beta_p", real["beta"], "nulo", "beta", "beta del logit de omega"),
            ("pbo_bruto_p", gross["pbo"], "nulo_bruto", "pbo", "PBO en celdas brutas"),
            (
                "p_perdida",
                real["p_perdida"],
                "nulo",
                "p_perdida",
                "probabilidad de pérdida",
            ),
        )
    ]


def main() -> None:
    """Ask the door and the seal, build the panels, run the one queue, write each mother's result."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--work",
        required=True,
        type=Path,
        nargs="+",
        help="la carpeta del lote: metrics.parquet y variant_trades.parquet; varias "
        "carpetas comparten una sola cola de procesos",
    )
    ap.add_argument(
        "--family",
        required=True,
        help="la familia de plantillas del lote: la tercera parte del estudio del "
        "ledger, donde se apunta la mirada, un renglón por tramo",
    )
    ap.add_argument("--set", dest="overrides", action="extend", nargs="+", default=[])
    a = ap.parse_args()
    started = time.time()
    cfg = config.load(a.overrides)
    batches: dict[Path, tuple[pd.DataFrame, batch.Weekly]] = {}
    for work in a.work:
        if not (work / batch.TRADES).exists():
            raise SystemExit(NO_TRADES.format(work=work))
        symbol, timeframe = look.market(work)
        look.admit(STEP, READS, symbol)  # before anything of oos2 is opened
        batches[work] = (
            pd.read_parquet(work / "metrics.parquet"),
            batch.read(work, symbol, timeframe, cfg["perf"]["workers"]),
        )
        envelope.progress(
            5,
            f"{symbol} {timeframe}: exceso semanal de {work.name}"
            + (" (de la caché)" if batches[work][1]["cached"] else ""),
        )
    step = {"at": 0}

    def progress(share: float) -> None:
        """One PROGRESS line per twentieth of the queue."""
        if int(share * 20) > step["at"]:
            step["at"] = int(share * 20)
            envelope.progress(
                10 + int(share * 80), "CSCV real, nulo y control positivo"
            )

    measured, perf = many.run(batches, cfg, progress)
    for work, got in measured.items():
        metrics, cells = batches[work]
        found = result(work.name, got, perf, cells, cfg, started)
        out = work / "estudios"
        output.population(
            out,
            "cscv",
            found,
            f"CSCV — {work.name.replace('_', ' ')}",
            "¿Elegir la mejor variante del pasado sirve fuera?",
        )
        if "found" in got:
            detail(out, got)
            draws.save(out, record(work.name, got, cfg["cscv"]["seed"]))
        facts = got["facts"]
        said = (
            f"P pérdida {facts['p_perdida']:.3f} · PBO {facts['pbo']:.3f} (nulo p5 "
            f"{facts['nulo']['pbo_p5']:.3f}, p95 {facts['nulo']['pbo_p95']:.3f})"
            if "pbo" in facts
            else "sin dato"
        )
        verdicts.write(
            out,
            pd.DataFrame(
                [{"strategy": work.name, "identity": None, "verdict": facts["estado"]}]
            ),
            work,
            " ".join(sys.argv),
            a.overrides,
        )
        look.log(
            work,
            a.family,
            {
                "step": STEP,
                "launched_by": "cscv",
                "config_hash": fingerprint(cfg),
                "n_in": len(metrics),
                "n_out": len(metrics),
                "criterion": "cscv/p_perdida+pbo_p95",
                "thresholds": cfg["state"]
                | {"blocks": cfg["cscv"]["blocks"], "draws": cfg["null"]["draws"]},
                "note": f"{facts['estado']} · {said} sobre {facts['n']} variantes",
            },
            READS,
        )
        print(
            f"{words.LABEL[facts['estado']]}: {said}, {facts['n']} variantes -> {out / 'cscv.html'}"
        )
        for note in got["notes"]:
            print(f"  aviso: {note}")
    envelope.progress(
        100,
        f"{len(measured)} madre(s), cola de {perf.get('wall_s', 0):.1f} s en "
        f"{perf.get('procesos', 0)} procesos",
    )


if __name__ == "__main__":
    main()
