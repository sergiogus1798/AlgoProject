#!/usr/bin/env python3
"""The Estrategia routes on a real project: metadata, basic stats, and OOS2 open to a human but shut to an autonomous agent."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from core.assetdata import AUTONOMOUS  # noqa: E402
from ui.daemon.app import APP  # noqa: E402

PROJECT, DATABANK = "Test_USDJPY_donchianUpperCrossUp_M30", "Results"
# Strategy 13.14.82: one of the 21 left in Results by the window walk of 2026-09-29 (the
# 5.16.75 pinned before was cut with the other 178).
IDENTITY = "47da0743d600c27cedda1f78cc30de3ebd4935f6624d8ffbf4e9cc0e0e6140dd"
LOCKED = "reservado: se abre tras los pasos 17, 18 y 19"
NO_EXPORT = "OOS2 abierto, sin export: exporta el retest oos2"      # no oos2 cosecha exists yet


def main() -> None:
    """Ask the three routes in-process (never a live port) and check what the ficha paints."""
    client = TestClient(APP)
    q = {"project": PROJECT, "databank": DATABANK, "identity": IDENTITY}
    meta = client.get("/api/strategy/meta", params=q).json()
    assert meta["identity"] == IDENTITY and meta["direction"] == "long", meta.get("error")
    assert meta["entries"] and meta["last_test"]["costs"]["spread"] == "0.1"
    assert meta["backtest"][0]["task"] == "Build strategies 2"       # read under the databank's name
    stats = client.get("/api/strategy/stats", params=q).json()
    is_ = stats["samples"]["IS"]
    assert is_["rows"][0] == {"label": "Operaciones", "value": 1344, "unit": ""}
    shape = {r["label"]: r for r in is_["returns"]["USD por lote"]["rows"]}
    assert abs(shape["curtosis (exceso)"]["value"] - 3.032) < 0.01 and stats["default_unit"] == "USD por lote"
    assert list(shape) == ["media", "desviación típica", "asimetría", "curtosis (exceso)"], list(shape)
    assert shape["media"]["unit"] == "$/lote"
    both = stats["samples"]["IS+OOS1"]["rows"]
    assert both[0]["value"] == 1344 + stats["samples"]["OOS1"]["rows"][0]["value"], both[0]
    assert abs(both[1]["value"] - is_["rows"][1]["value"] - stats["samples"]["OOS1"]["rows"][1]["value"]) < 0.01
    os.environ.pop(AUTONOMOUS, None)               # a human: open (owner, 2026-09-28)
    assert stats["samples"]["OOS2"]["blocked"] == NO_EXPORT, stats["samples"]["OOS2"]
    sheet = client.get("/api/tearsheet", params=q | {"sample": "OOS2"}).json()
    assert sheet["blocked"] == NO_EXPORT and "tabs" not in sheet
    os.environ[AUTONOMOUS] = "1"                   # an autonomous agent: still shut
    shut = client.get("/api/strategy/stats", params=q).json()
    assert shut["samples"]["OOS2"]["blocked"] == LOCKED
    sheet = client.get("/api/tearsheet", params=q | {"sample": "OOS2"}).json()
    assert sheet["blocked"] == LOCKED and "tabs" not in sheet
    os.environ.pop(AUTONOMOUS)
    print("ok: metadatos (long, costes, tarea del build), estadísticas IS con curtosis, IS+OOS1 "
          "sumando las dos, OOS2 abierto a un humano y cerrado a un agente autónomo")


if __name__ == "__main__":
    main()
