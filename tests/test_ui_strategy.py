#!/usr/bin/env python3
"""The Estrategia routes on a real project: metadata, basic stats, and OOS2 kept shut by the ledger."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from ui.daemon.app import APP  # noqa: E402

PROJECT, DATABANK = "Test_USDJPY_donchianUpperCrossUp_M30", "Results"
IDENTITY = "4d679e0c2ce2a63ee53bc6cb305830bcaf5a74997e6e6e2c1deeb4c30f307048"
LOCKED = "reservado: se abre tras los pasos 17, 18 y 19"


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
    assert is_["rows"][0] == {"label": "Operaciones", "value": 1357, "unit": ""}
    shape = {r["label"]: r["value"] for r in is_["returns"]["USD por lote"]["rows"]}
    assert abs(shape["curtosis (exceso)"] - 4.05) < 0.01 and stats["default_unit"] == "USD por lote"
    assert stats["samples"]["OOS2"]["blocked"] == LOCKED
    sheet = client.get("/api/tearsheet", params=q | {"sample": "OOS2"}).json()
    assert sheet["blocked"] == LOCKED and "tabs" not in sheet
    print("ok: metadatos (long, costes, tarea del build), estadísticas IS con curtosis, OOS2 bloqueado")


if __name__ == "__main__":
    main()
