"""Every strategy of one export measured on «does the logic travel?»: travel.run's files, read as one result.

The study no longer calls MANTENER or DESCARTAR: it writes the facts (P1-P9, encargo 46) and
`pipeline/autopilot/criteria.yaml` step 10 decides.
"""

import json
import tempfile
import time
from pathlib import Path
from typing import Any, TypedDict, cast

import pandas as pd

from core import paths
from core.study import blocks, result as envelope
from studies.transfer.crossmarket import load
from studies.transfer.crossmarket.travel import run as travel

WORD = "info"  # the `verdict` column verdict.csv and /curate require: measured, no call made here
HEAD = ["strategy", "identity", "verdict"]


class Measured(travel.Travelled):
    """`travel.run`'s result read back with the cells it left out and P9's series per strategy."""

    excluded: list[dict[str, Any]]
    d_y: dict[str, list[dict[str, Any]]]


class Ran(TypedDict):
    """The export's result, one row per strategy, the draws rows and one row per strategy and market."""

    population: dict[str, Any]
    table: pd.DataFrame
    draws: list[dict[str, Any]]
    markets: pd.DataFrame


def measure(inputs: load.Inputs, overrides: list[str] | None = None) -> Measured:
    """One `travel.run` over the whole export, read back.

    Args:
        inputs: What load.load() returned (only project, databank, asset and export are used).
        overrides: The `--set` values the cfg was loaded with; `travel.run` loads its own.

    Returns:
        `verdict` and `markets` (frames), `checks` (§7.1 per market), `excluded` ((market, cell)
        pairs left out) and `d_y` (P9's series per strategy).
    """
    scratch = (
        paths.DATA / "scratch"
    )  # travel.run refuses the live reports folder: it writes here
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix="crossmarket_") as tmp:
        out = Path(tmp) / "travel"
        got = travel.run(
            inputs["project"],
            inputs["databank"],
            inputs["asset"],
            inputs["export"],
            out,
            overrides,
        )
        info = json.loads((out / "crossmarket.json").read_text(encoding="utf-8"))
    return Measured(**got, excluded=info["excluded"], d_y=info["d_y"])


def population(
    table: pd.DataFrame, got: Measured, cfg: dict, started: float
) -> dict[str, Any]:
    """The export read as one result: every strategy's numbers and the market checks."""
    checks = pd.DataFrame(got["checks"])
    return envelope.envelope(
        "studies.transfer.crossmarket",
        None,
        None,
        cfg,
        started,
        [
            envelope.tab(
                "summary",
                "Resumen",
                [
                    {
                        "kind": "bars",
                        "title": "z conjunta frente al azar, por estrategia",
                        "unit": "z",
                        "reference": 0.0,
                        "items": [
                            {
                                "label": r.strategy,
                                "value": r.z_conj,
                                "error": None,
                                "state": "info",
                            }
                            for r in cast(Any, table.itertuples())
                            if r.z_conj == r.z_conj
                        ],
                    },
                    blocks.table(
                        "Estrategia a estrategia", table.drop(columns=["identity"])
                    ),
                ],
            ),
            envelope.tab(
                "markets",
                "Mercados",
                [
                    blocks.table(
                        "Controles previos de cada mercado",
                        checks,
                        "Un mercado no válido queda fuera de todas las pruebas.",
                    ),
                    blocks.table(
                        "Pares (mercado, celda) sin dato",
                        pd.DataFrame(
                            got["excluded"],
                            columns=pd.Index(["market", "cell", "displaced_share"]),
                        ),
                        "Celdas con huecos de datos: se leen como sin dato, nunca como 0.",
                    ),
                ],
            ),
        ],
        blocks.verdict(
            f"{len(table)} medidas",
            "info",
            f"{len(table)} estrategias medidas. El estudio no decide: lo hace el juez, "
            f"con las reglas P1-P9 de criteria.yaml.",
        ),
    )


def run(
    inputs: load.Inputs, cfg: dict, workers: int = 0, overrides: list[str] | None = None
) -> Ran:
    """Measure every strategy of the export in one pass.

    Args:
        inputs: What load.load() returned.
        cfg: What config.load(overrides) returned; it signs the result.
        workers: Kept for the command line; the travel run fans out over every physical core.
        overrides: The same `--set` values cfg was loaded with.

    Returns:
        {"population": the export's result, "table": one row per strategy (verdict.csv),
        "markets": one row per strategy and market (markets.parquet), "draws": the rows of
        `travel.records` (distribuciones.parquet)}.
    """
    started = time.time()
    got = measure(inputs, overrides)
    ident = inputs["identity"]
    table = got["verdict"].assign(
        identity=lambda t: t["strategy"].map(ident), verdict=WORD
    )
    table = cast(
        pd.DataFrame, table[[*HEAD, *table.columns.difference(HEAD, sort=False)]]
    )
    markets = got["markets"].assign(identity=lambda t: t["strategy"].map(ident))
    envelope.progress(100, f"{len(table)} estrategias medidas")
    return Ran(
        population=population(table, got, cfg, started),
        table=table,
        draws=got["draws"],
        markets=cast(
            pd.DataFrame,
            markets[
                [
                    "strategy",
                    "identity",
                    *markets.columns.difference(["strategy", "identity"], sort=False),
                ]
            ],
        ),
    )
