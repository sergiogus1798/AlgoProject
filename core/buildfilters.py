"""The Build's acceptance filters for one asset and timeframe, resolved from assets/_study.yaml."""

import math
from pathlib import Path

import yaml

from core.assetdata import window
from core.paths import ASSETS

STUDY = ASSETS / "_study.yaml"
MODES = ("study", "calibration")
# `sample:` of the file -> the key of `sqx.projects.acceptance.READS` a condition is read with.
SAMPLES = {"IS": "is"}
YEAR_MS = 365.25 * 86400 * 1000


def _need(block: dict, key: str, where: str) -> object:
    """One value of the file, or the refusal: there is no default filter."""
    if block.get(key) is None:
        raise SystemExit(f"assets/_study.yaml: falta `{key}` en {where}. Sin ese valor no se "
                         "escribe ningún filtro de aceptación — decídelo antes de construir.")
    return block[key]


def resolved(data: dict, study: dict) -> dict:
    """The study filters of one asset: defaults, then its class's, then its own."""
    out = dict(_need(study, "defaults", "la raíz"))
    for layer in ((study.get("classes") or {}).get(data["class"]),
                  (study.get("symbols") or {}).get(data["symbol"])):
        for key, value in (layer or {}).items():
            out[key] = {**out.get(key, {}), **value} if isinstance(value, dict) else value
    return out


def filters(data: dict, timeframe: str, mode: str = "study", path: Path = STUDY) -> dict:
    """What the Build task accepts, as the conditions to write and the numbers behind them.

    Args:
        data: One asset as `core.assetdata.load` returned it.
        timeframe: SQX timeframe name, e.g. "H1".
        mode: "study" — the filters of `_study.yaml` — or "calibration", its relaxed set for an
            unselected population.
        path: The file to read; another one only for an A/B of thresholds.

    Returns:
        `mode`, `sample`, `build_years`, and `conditions` — each a dict `read`, `metric`, `op`,
        `value` as `sqx.projects.acceptance.condition` takes it. The trade bounds are totals:
        trades per year × the years of the asset's `build` segment, floor rounded up and
        ceiling down.

    Raises:
        SystemExit: A value is missing for this asset, timeframe or mode, or the file is.
    """
    if not path.exists():
        raise SystemExit(f"{path} no existe: sin él no hay filtros de aceptación que escribir.")
    study = yaml.safe_load(path.read_text(encoding="utf-8"))
    sample = _need(study, "sample", "la raíz")
    if sample not in SAMPLES:
        raise SystemExit(f"assets/_study.yaml: `sample: {sample}` no se admite. Un filtro del "
                         f"build sólo lee {', '.join(SAMPLES)}: seleccionar con el OOS lo gasta.")
    read = SAMPLES[sample]
    start, end = window(data, "build")
    years = round((end - start) / YEAR_MS, 2)
    if mode == "calibration":
        block = _need(study, "calibration", "la raíz")
        bounds = [(">=", int(_need(block, "trades_min", "`calibration`")))]
        rest = [("NetProfit", ">", _need(block, "net_profit_min", "`calibration`"))]
    else:
        block = resolved(data, study)
        where = f"`defaults` (o lo propio de {data['symbol']})"
        per_year = _need(_need(block, "trades_per_year", where), timeframe,
                         f"`trades_per_year` de {where}")
        bounds = [(">=", math.ceil(_need(per_year, "min", f"`trades_per_year.{timeframe}`")
                                   * years)),
                  ("<=", math.floor(_need(per_year, "max", f"`trades_per_year.{timeframe}`")
                                    * years))]
        rest = [("ProfitFactor", ">=", _need(block, "profit_factor_min", where)),
                ("NetProfit", ">", _need(block, "net_profit_min", where))]
    triples = [("NumberOfTrades", op, value) for op, value in bounds] + rest
    return {"mode": mode, "sample": sample, "build_years": years,
            "conditions": [{"read": read, "metric": m, "op": op, "value": v}
                           for m, op, v in triples]}
