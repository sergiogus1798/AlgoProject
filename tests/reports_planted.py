"""The stored reports of the planted project (IS/OOS, cross-market with a partial re-run, gate on two days):
part of `harvest_planted`, not a test itself. Contract results with the keys `core.study.blocks` asks of a report."""

from pathlib import Path
from typing import Any

import numpy as np

from harvest_planted import (
    CROSS_NAME,
    FEED,
    ISOOS_NAME,
    MARKETS,
    NAMES,
    OLD_DAY,
    PROJECT,
    identity_of,
    write,
)


def result(
    module: str,
    strategy: str | None,
    tabs: list[dict[str, Any]],
    verdict: dict[str, Any] | None = None,
    **extra: object,
) -> dict[str, Any]:
    """A contract result (`core.study.blocks`): the keys every report carries, with the tabs given."""
    return {
        "module": module,
        "strategy": strategy,
        "identity": identity_of(strategy.removesuffix("(1)")) if strategy else None,
        "config_hash": "planted",
        "computed_at": "2026-09-27T12:00:00",
        "wall_s": 1.0,
        "verdict": verdict,
        "tabs": tabs,
        "warnings": [],
        "glossary": [],
        "summary": {},
        **extra,
    }


def _distribution(
    title: str, unit: str | None, seed: int, select: dict[str, Any] | None = None
) -> dict[str, Any]:
    """A small distribution block, tagged `select` when given."""
    rng = np.random.default_rng(seed)
    counts, bins = np.histogram(rng.normal(0, 1, 400), bins=12)
    block = {
        "kind": "distribution",
        "title": title,
        "unit": unit,
        "bins": [round(float(b), 3) for b in bins],
        "counts": counts.tolist(),
        "real": None,
        "median": 0.0,
        "band": [-1.6, 1.6],
        "percentiles": {"5": -1.6, "50": 0.0, "95": 1.6},
        "p": 0.3,
        "note": "",
    }
    return block | ({"select": select} if select else {})


def _isoos(root: Path) -> None:
    """The IS/OOS report of `ISOOS_NAME`: four blocks on screen (USD ones + a table), eleven in the file."""
    units = ["USD", "% del saldo", "USD por lote"]
    blocks = [
        _distribution(f"Retorno {u}", u, k, {"unidad": u}) for k, u in enumerate(units)
    ]
    blocks.append(
        {"kind": "table", "title": "Resumen", "columns": ["a", "b"], "rows": [["x", 1]]}
    )
    blocks += [
        _distribution(f"Racha {u}", u, 9 + k, {"unidad": u})
        for k, u in enumerate(units)
    ]
    blocks += [
        _distribution(f"Pérdida {u}", u, 5 + k, {"unidad": u})
        for k, u in enumerate(units)
    ]
    tab = {
        "name": "trades",
        "title": "Operaciones",
        "note": "",
        "selectors": [
            {
                "key": "unidad",
                "label": "Unidad del dinero",
                "options": units,
                "default": "USD",
            }
        ],
        "blocks": blocks,
    }
    folder = root / "reports" / PROJECT / "Results" / OLD_DAY / "isOos"
    write(
        folder / "estrategias" / f"{ISOOS_NAME}.json",
        result("isOos", ISOOS_NAME, [tab]),
    )


def _cross(root: Path) -> None:
    """The cross-market report of `CROSS_NAME` with a stored 'random' tab per market and one partial re-run of the last."""

    def tab(markets: list[str]) -> dict[str, Any]:
        """A 'random' tab holding one tagged distribution per market and null model."""
        models = ["Shuffled Sequence", "Calendar Shift"]
        return {
            "name": "random",
            "title": "Aleatorio",
            "note": "",
            "selectors": [
                {
                    "key": "mercado",
                    "label": "Mercado",
                    "options": markets,
                    "default": markets[0],
                },
                {
                    "key": "modelo",
                    "label": "Modelo nulo",
                    "options": models,
                    "default": models[0],
                },
            ],
            "blocks": [
                _distribution(
                    f"{m} · {mod}", None, 3 * i + j, {"mercado": m, "modelo": mod}
                )
                for i, m in enumerate(markets)
                for j, mod in enumerate(models)
            ],
        }

    verdict = {
        "kind": "verdict",
        "label": "ROBUSTA",
        "state": "pass",
        "score": None,
        "meaning": "x",
        "parts": [],
    }
    folder = (
        root / "reports" / PROJECT / "Retest_Markets_-_Family" / OLD_DAY / "crossmarket"
    )
    write(
        folder / "estrategias" / f"{CROSS_NAME}.json",
        result("crossmarket", CROSS_NAME, [tab(MARKETS)], verdict),
    )
    census = {  # the population result, which names each strategy it judged in a `strategy` column
        "kind": "table",
        "title": "Por estrategia",
        "columns": ["strategy", "veredicto"],
        "rows": [[n, "ROBUSTA"] for n in NAMES],
    }
    top = {
        "name": "census",
        "title": "Censo",
        "note": "",
        "selectors": [],
        "blocks": [census],
    }
    write(folder / "crossmarket.json", result("crossmarket", None, [top], verdict))
    only = MARKETS[-1]
    part = result("crossmarket", CROSS_NAME, [tab([only])], None, only=only)
    part["computed_at"] = "2026-09-28T07:24:42"
    write(
        folder
        / "parciales"
        / "20260928-072442_GBPUSD"
        / "estrategias"
        / f"{CROSS_NAME}.json",
        part,
    )


def _gate(root: Path) -> None:
    """The gate of `PROJECT` on two days: the population result, one result per strategy (every other one dies)."""
    for day in (OLD_DAY, "2026-09-28"):
        folder = root / "reports" / PROJECT / "Results" / day / "gate"
        funnel = {
            "kind": "table",
            "title": "Criba a criba",
            "columns": ["criba", "entran", "pasan"],
            "rows": [["presencia", 6, 6]],
        }
        tab = {
            "name": "funnel",
            "title": "El embudo",
            "note": "",
            "selectors": [],
            "blocks": [funnel],
        }
        top = {
            "kind": "verdict",
            "label": "3 de 6 sobreviven",
            "state": "pass",
            "score": None,
            "meaning": "x",
            "parts": [],
        }
        write(folder / "gate.json", result("gate", None, [tab], top))
        rows = ["strategy,verdict,identity,reason"]
        for k, name in enumerate(NAMES):
            keep = k % 2 == 0
            label, state = ("MANTENER", "pass") if keep else ("ELIMINAR", "fail")
            one = {
                "kind": "verdict",
                "label": label,
                "state": state,
                "score": None,
                "meaning": "Pasó todas las cribas duras."
                if keep
                else "Elimina: no pasa la criba de estáticas.",
                "parts": [],
            }
            table = {
                "kind": "table",
                "title": "Cada criba",
                "columns": ["criba", "valor"],
                "rows": [["presencia", 1.0]],
            }
            body = {
                "name": "screens",
                "title": "Cribas",
                "note": "",
                "selectors": [],
                "blocks": [table],
            }
            res = result(
                "gate",
                name,
                [body],
                one,
                summary={"survives": keep, "died_at": "" if keep else "estaticas"},
            )
            write(folder / "estrategias" / f"{name}.json", res)
            rows.append(f"{name},{label},{identity_of(name)},")
        (folder / "verdict.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
        write(
            folder / "manifest.json",
            {
                "date": day,
                "source": {"project": PROJECT, "databank": "Results", "feed": FEED},
            },
        )


def plant_reports(root: Path) -> None:
    """Write every stored report of the planted project under `root/reports/`."""
    _isoos(root)
    _cross(root)
    _gate(root)
