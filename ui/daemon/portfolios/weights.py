"""«Pesos» and «Incubación»: the weight walk-forward's decision, and the incubation reading if one exists."""

import json
from typing import Any

import pandas as pd

from portfolio.common.construct.incubation import record
from portfolio.common.construct.inputs import config
from ui.daemon.portfolios import parts, shelf

ARMS = {
    "fixed": "pesos fijados en build",
    "reestimated": "pesos re-estimados en cada ventana",
}
METHODS = {
    "equal": "iguales",
    "risk_parity": "paridad de riesgo (1/σ)",
    "min_variance": "mínima varianza",
    "hrp": "HRP (jerárquico)",
}
STATES = {
    "inside": "DENTRO de la banda",
    "below": "POR DEBAJO de la banda",
    "above": "POR ENCIMA de la banda",
    "no_band": "sin banda",
}
IDLE = "La incubación no está corriendo: no hay cartera elegida ni cuenta."


def read(pool: str = "", run: str = "", **_: str) -> dict[str, Any]:
    """The newest weight walk-forward of the selected portfolio (or of the pool): its table and decision."""
    cfg = config.load([])
    lacks = (
        []
        if cfg["wf"]["confidence"] is not None
        else [
            "Falta wf.confidence: decisión tuya — bloquea el walk-forward de pesos (el intervalo que una "
            "diferencia de Sharpe tiene que superar para «ganar»)."
        ]
    )
    found = sorted((shelf.ROOT / "weights_wf").glob("*/result.json"), reverse=True)
    docs = [(f.parent, shelf.load(f)) for f in found]
    docs = [
        (d, r)
        for d, r in docs
        if (not run or r["source"] == run) and (not pool or r["pool"] == pool)
    ]
    if not docs:
        return parts.empty(
            "No hay walk-forward de pesos"
            + (f" de la cartera «{run}»." if run else "."),
            "elige abajo una cartera del camino real y pulsa «Calcular walk-forward».",
        ) | {"missing": lacks}
    folder, doc = docs[0]
    known = shelf.names()
    frame = pd.read_parquet(folder / "table.parquet")
    rows, states = [], []
    for r in frame.to_dict("records"):
        base = r["method"] == "equal"
        rows.append(
            [
                METHODS.get(r["method"], r["method"]),
                ARMS[r["arm"]],
                r["sharpe"],
                None if base else r["diff"],
                None if base else r["lo"],
                None if base else r["hi"],
                "referencia" if base else "sí" if r["beats"] else "no",
            ]
        )
        states.append([None] * 6 + [None if base else "pass" if r["beats"] else "fail"])
    table = parts.table(
        "Cada método contra pesos iguales, en oos1",
        [
            "método",
            "brazo",
            "Sharpe diario",
            "diferencia",
            "intervalo: desde",
            "hasta",
            "¿gana?",
        ],
        rows,
        f"{len(doc['windows'])} ventanas de prueba sobre {doc['test_days']} días de oos1; "
        f"intervalo al {doc['wf']['confidence']:.0%}, sin corregir por el número de comparaciones.",
        [
            None,
            "Fijo: los pesos de build no se tocan. Re-estimado: se recalculan al empezar cada "
            "ventana con todo lo anterior.",
            parts.WORDS["sharpe"],
            parts.WORDS["diff"],
            parts.WORDS["diff"],
            parts.WORDS["diff"],
            None,
        ],
        states,
    )
    held = pd.read_parquet(folder / "weights.parquet")
    first = held[held["window"] == held["window"].min()]
    grid = first.pivot_table(
        index="identity", columns="method", values="weight", aggfunc="first"
    )
    wrows = [
        [
            shelf.label(i, known),
            *[
                parts.clean(float(grid.loc[i].get(m, float("nan"))))
                for m in grid.columns
            ],
        ]
        for i in grid.index
    ]
    wtable = parts.table(
        "Los pesos que da cada método (primera ventana)",
        ["estrategia", *[str(METHODS.get(m, m)) for m in grid.columns]],
        wrows,
        "Suman 1 por método. Solo «iguales» puede elegirse hoy; los demás se comparan.",
    )
    return {
        "run": doc["source"],
        "relaxed": parts.relaxed(doc.get("relaxed")),
        "empty": None,
        "missing": lacks,
        "tabs": [
            parts.tab(
                "Decisión",
                parts.callout(
                    doc["sentence"],
                    "watch" if doc["selected_method"] == "equal" else "pass",
                ),
                table,
            ),
            parts.tab("Pesos por método", wtable),
        ],
    }


def incubation(**_: str) -> dict[str, Any]:
    """Each registered portfolio's last reading against its band; the plain statement when there is none."""
    folders = (
        sorted(p.parent for p in record.ROOT.glob("*/record.json"))
        if record.ROOT.exists()
        else []
    )
    if not folders:
        return {"tabs": [], "empty": IDLE, "relaxed": ""}
    tabs, marks = [], {}
    for folder in folders:
        rec = shelf.load(folder / "record.json")
        marks |= rec["portfolio"].get("relaxed_thresholds") or {}
        file = folder / "readings.jsonl"
        reads = (
            [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines()]
            if file.exists()
            else []
        )
        rows = [
            [
                r["ts"][:16].replace("T", " "),
                f"{r['from']} … {r['to']}",
                r["days"],
                r["value"],
                r["low"],
                r["high"],
                r["percentile"],
                STATES.get(r["state"], r["state"]),
                r["source"],
            ]
            for r in reads
        ]
        states = [
            [None] * 7 + ["watch" if r["flagged"] else "pass", None] for r in reads
        ]
        cmp = rec["comparison"]
        tabs.append(
            parts.tab(
                f"Cartera {rec['portfolio_hash'][:8]}",
                parts.callout(record.NOT_RUNNING, "watch"),
                parts.callout(
                    f"Registrada el {rec['registered'][:10]} desde {rec['portfolio']['run_id']} · "
                    f"veredicto: {rec['portfolio']['verdict']} · se lee «{cmp['figure']}» contra los tramos "
                    f"{', '.join(cmp['history'])}, banda de percentiles {cmp['band']}."
                ),
                parts.table(
                    "Lecturas",
                    [
                        "leída",
                        "tramo",
                        "días",
                        "valor",
                        "banda: desde",
                        "hasta",
                        "percentil",
                        "estado",
                        "origen",
                    ],
                    rows,
                    parts.WORDS["band"]
                    + " Origen «paper» o «live»; las de hoy son filas SINTÉTICAS de prueba del código.",
                    states=states,
                )
                if rows
                else parts.callout("Sin lecturas todavía."),
            )
        )
    return {"tabs": tabs, "empty": None, "relaxed": parts.relaxed(marks)}
