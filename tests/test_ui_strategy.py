#!/usr/bin/env python3
"""The Estrategia routes on a real project: metadata, basic stats, and OOS2 open to a human but shut to an autonomous agent."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from unittest import mock  # noqa: E402

from core import paths  # noqa: E402
from core.assetdata import AUTONOMOUS  # noqa: E402
from ui.daemon import progress  # noqa: E402
from ui.daemon.app import APP  # noqa: E402
from ui.daemon.loader import find  # noqa: E402
from ui.daemon.tearsheet import borrow, harvest, oos2  # noqa: E402

# A self-contained copy of one Test_ project that has since been retired: its project.cfx, one
# strategy (4.8.424) and the harvest rows of that strategy alone, laid out as the routes look.
ROOT = Path(__file__).resolve().parent / "fixtures" / "ui_strategy"
PROJECT, DATABANK = "Test_XAUUSD_H1_ruptura_mcptR", "Results"
IDENTITY = "c46024907a20d055132d0ce3509c17af133b85a2de07d5f5ebdb7dbe5ede8b98"
LOCKED = "reservado: se abre tras los pasos 17, 18 y 19"
NO_EXPORT = (
    "OOS2 abierto, sin export: exporta el retest oos2"  # no oos2 cosecha exists yet
)


def main() -> None:
    """Point the lookups at the fixture root, then ask the routes in-process (never a live port)."""
    data = ROOT / "AlgoData"
    with (
        mock.patch.object(progress, "installs", lambda: {"fixture": ROOT / "SQX"}),
        mock.patch.object(paths, "DATA", data),
        mock.patch.object(find, "DATA", data),
        mock.patch.object(borrow, "DATA", data),
        mock.patch.object(harvest, "DATA", data),
        mock.patch.object(oos2, "DATA", data),
    ):
        check()


def check() -> None:
    """Check what the ficha paints."""
    client = TestClient(APP)
    q = {"project": PROJECT, "databank": DATABANK, "identity": IDENTITY}
    meta = client.get("/api/strategy/meta", params=q).json()
    assert meta["identity"] == IDENTITY and meta["direction"] == "long", meta.get(
        "error"
    )
    assert meta["entries"] and meta["last_test"]["costs"]["spread"] == "13.33"
    assert (
        meta["backtest"][0]["task"] == "Build strategies 2"
    )  # read under the databank's name
    stats = client.get("/api/strategy/stats", params=q).json()
    is_ = stats["samples"]["IS"]
    assert is_["rows"][0] == {"label": "Operaciones", "value": 354, "unit": ""}
    shape = {r["label"]: r for r in is_["returns"]["USD por lote"]["rows"]}
    assert (
        abs(shape["curtosis (exceso)"]["value"] - 13.680) < 0.01
        and stats["default_unit"] == "USD por operación"
    )
    assert list(shape) == [
        "media",
        "desviación típica",
        "asimetría",
        "curtosis (exceso)",
    ], list(shape)
    assert shape["media"]["unit"] == "$/lote"
    both = stats["samples"]["IS+OOS1"]["rows"]
    assert both[0]["value"] == 354 + stats["samples"]["OOS1"]["rows"][0]["value"], both[
        0
    ]
    assert (
        abs(
            both[1]["value"]
            - is_["rows"][1]["value"]
            - stats["samples"]["OOS1"]["rows"][1]["value"]
        )
        < 0.01
    )
    os.environ.pop(AUTONOMOUS, None)  # a human: open (owner, 2026-09-28)
    assert stats["samples"]["OOS2"]["blocked"] == NO_EXPORT, stats["samples"]["OOS2"]
    sheet = client.get("/api/tearsheet", params=q | {"sample": "OOS2"}).json()
    assert sheet["blocked"] == NO_EXPORT and "tabs" not in sheet
    os.environ[AUTONOMOUS] = "1"  # an autonomous agent: still shut
    shut = client.get("/api/strategy/stats", params=q).json()
    assert shut["samples"]["OOS2"]["blocked"] == LOCKED
    sheet = client.get("/api/tearsheet", params=q | {"sample": "OOS2"}).json()
    assert sheet["blocked"] == LOCKED and "tabs" not in sheet
    os.environ.pop(AUTONOMOUS)
    print(
        "ok: metadatos (long, costes, tarea del build), estadísticas IS con curtosis, IS+OOS1 "
        "sumando las dos, OOS2 abierto a un humano y cerrado a un agente autónomo"
    )


if __name__ == "__main__":
    main()
