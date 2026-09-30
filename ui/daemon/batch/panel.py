"""One mother's variant batch as the parallel-coordinates view draws it: build, oos1 and, when the batch has it, oos2."""

import math
from pathlib import Path

import pyarrow.parquet as pq

from core.datapaths import variants_dir
from ledger import gate
from pipeline.ledger.state import work_dir
from ui.daemon.runner import where

# The one-way door, shut only for an autonomous agent (`ledger.gate.enforced`; owner,
# 2026-09-28): then a column naming any of these is never read. `ALL` and `oos1+oos2` both
# include the reserved segment; `oos2` is it.
SEALED = ("oos2", "ALL")
OUTCOMES = ("NetProfit (oos1)", "NetProfit (build)")
OPTIONAL = ("NetProfit (oos2)",)          # drawn when the batch was retested over it
LABELS = ("variant_id", "stratum", "origin")


def sealed(name: str) -> bool:
    """Whether a column or a text touches the reserved segment.

    Args:
        name: A column name or any text about to leave the daemon.

    Returns:
        True when the door is shut and it names `oos2`, `ALL` or `oos1+oos2`; always False
        for a human.
    """
    return gate.enforced() and any(s in name for s in SEALED)


def folders(project: str, strategy: str) -> list[Path]:
    """The batch folders that exist for one mother, factory first, then pipeline.

    Args:
        project: Project name.
        strategy: The mother as SQX spells it ("Strategy 18.13.59") or as its folder does.

    Returns:
        Existing folders, possibly none.
    """
    name = strategy.replace("_", " ")
    return [d for d in (variants_dir(project, name), work_dir(project, name)) if d.is_dir()]


def columns(path: Path) -> list[str]:
    """The columns the view needs, sealed ones never among them.

    Args:
        path: A batch's `metrics.parquet`.

    Returns:
        Labels, every `param_*` and the outcomes present, in the file's order.
    """
    names = pq.read_schema(path).names
    keep = [c for c in names
            if c in LABELS or c.startswith("param_") or c in OUTCOMES + OPTIONAL]
    return [c for c in keep if not sealed(c)]


def clean(v: object) -> object:
    """A cell as JSON carries it and the window prints it: NaN as None, 20.0 as 20."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return int(v) if isinstance(v, float) and v.is_integer() else v


def read(path: Path) -> dict:
    """The batch panel from one `metrics.parquet`, oos2 among the outcomes when it has one.

    Args:
        path: The file.

    Returns:
        `{"variants", "stratum", "mother", "axes", "fixed", "outcomes", "note"}` or
        `{"error": sentence}` when the file lacks the two NetProfit columns.
    """
    cols = columns(path)
    if not all(o in cols for o in OUTCOMES):
        return {"error": f"el metrics.parquet de {path.parent.name} no tiene las columnas "
                         f"{' y '.join(OUTCOMES)}: este lote no se puede dibujar aquí"}
    t = pq.read_table(path, columns=cols).to_pydict()
    n = len(t[OUTCOMES[0]])
    axes, fixed = [], []
    for c in (c for c in cols if c.startswith("param_")):
        vals = [clean(v) for v in t[c]]
        seen = sorted({v for v in vals if v is not None})
        (axes if len(seen) > 1 else fixed).append(
            {"key": c, "label": c.removeprefix("param_"), "values": vals, "levels": seen})
    strata = t.get("stratum", [""] * n)
    origin = t.get("origin", [False] * n)
    mother = next((i for i, o in enumerate(origin) if o), None)
    counts = {s: strata.count(s) for s in dict.fromkeys(strata)}
    fixed_text = ", ".join(f"{f['label']} = {f['levels'][0] if f['levels'] else '—'}"
                           for f in fixed) or "ninguno"
    note = (f"{n} variantes del lote ({', '.join(f'{k} {v}' for k, v in counts.items())}). "
            f"Un eje por parámetro que varía; el último es el NetProfit del tramo elegido. "
            f"Parámetros con un solo valor, sin eje: {fixed_text}. "
            + ("Tramos: build, oos1 y oos2." if OPTIONAL[0] in cols else "Tramos: build y oos1."))
    return {"variants": [str(v) for v in t.get("variant_id", range(n))],
            "stratum": [str(s) for s in strata], "mother": mother,
            "axes": [{k: a[k] for k in ("key", "label", "values")} for a in axes],
            "fixed": [{"label": f["label"], "value": f["levels"][0] if f["levels"] else None}
                      for f in fixed],
            "outcomes": {o: [clean(v) for v in t[o]] for o in OUTCOMES + OPTIONAL if o in cols},
            "note": note}


def batch(project: str, strategy: str) -> dict:
    """What `GET /api/batch` answers for one mother.

    Args:
        project: Project name.
        strategy: The mother, spaces or underscores.

    Returns:
        `{"has_batch": bool, "folder": str, ...read()}`, or with `error` when there is no
        batch, no `metrics.parquet`, or one in each of the two places.
    """
    found = folders(project, strategy)
    if not found:
        return {"has_batch": False,
                "error": f"{strategy} no tiene lote de variantes en este proyecto (skill /variants)"}
    if not any((d / "metrics.parquet").exists() for d in found):
        return {"has_batch": True,
                "error": f"el lote de {strategy} existe (en {found[0].parent.parent.name}/) pero aún no tiene "
                         "metrics.parquet: falta retestearlo y cosecharlo (skill /variants)"}
    work = where.batch(project, strategy.replace("_", " "), ("metrics.parquet",))
    if isinstance(work, str):
        return {"has_batch": True, "error": work}
    return {"has_batch": True, "folder": str(work), **read(work / "metrics.parquet")}
