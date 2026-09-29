#!/usr/bin/env python3
"""Known-answer test for the variant pilot (OPEN.md #41): synthetic inputs, no SQX."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.variants.design import pilot, plan

PILOT_CFG = {"sample": 256, "seed": 20260929, "min_trades": 30, "min_support": 5}
LIVE = {"Period1": [10.0, 20.0, 30.0, 40.0], "Coef1": [1.0, 2.0, 3.0]}


def check(failures: list, ok: bool, said: str) -> None:
    """Record one property and say how it went."""
    print(f"  {'ok  ' if ok else 'FALLA'} {said}")
    if not ok:
        failures.append(said)


def brief(n_target: int = 40) -> dict:
    """A minimal design brief, enough for `plan.build` to run end to end."""
    return {
        "strategy": "Strategy TEST", "verdict": "no_fiable", "n_target": n_target,
        "strata": {"neighbourhood": 0.2, "factorial": 0.6, "coverage": 0.2},
        "parameters": [
            {"name": "Period1", "original": 20.0, "levels": [10.0, 20.0, 30.0, 40.0],
             "center": 20.0, "eta2": 0.6},
            {"name": "Coef1", "original": 2.0, "levels": [1.0, 2.0, 3.0],
             "center": 2.0, "eta2": 0.2}],
        "frozen": [{"name": "Shift1", "value": 1.0}]}


def settings() -> dict:
    """The `config.yaml` blocks `plan.build` reads, minimal versions."""
    return {"minimum": {"variants": 1, "widen_step": 0.05, "max_span": 0.60},
           "design": {"neighbourhood": {"radius": 2}, "factorial": {"min_levels": 2},
                      "frozen": {"span": 0.30, "steps": 5}, "seed": 20260921},
           "canaries": {"n": 3, "inert_pairs": True}}


def empty_known(names: list[str]) -> pd.DataFrame:
    """`inputs.known`'s shape with nothing in it, so the canary picks are skipped clean."""
    return pd.DataFrame(columns=[*names, "NetProfit", "NumberOfTrades"])


def main() -> None:
    """Fail loudly on any property that does not hold."""
    failures = []
    print("## design.pilot.sample")
    table = pilot.sample(LIVE, PILOT_CFG)
    check(failures, len(table) == PILOT_CFG["sample"], f"{len(table)} filas pedidas")
    check(failures, set(table.columns) == {"pilot_id", "Period1", "Coef1"},
          "sólo los parámetros que se mueven, ninguno congelado")
    check(failures, table["pilot_id"].is_unique, "un identificador por fila")
    again = pilot.sample(LIVE, PILOT_CFG)
    check(failures, table.equals(again), "misma semilla, mismo muestreo")

    print("\n## design.pilot.decide")
    # Period1=10 nunca opera; el resto sí. Coef1 no se toca -- ninguno de sus niveles cae.
    counts = {row.pilot_id: (2.0 if row.Period1 == 10.0 else 200.0)
             for row in table.itertuples()}
    banned, report = pilot.decide(table, counts, PILOT_CFG["min_trades"], PILOT_CFG["min_support"])
    check(failures, banned == {"Period1": {10.0}}, f"sólo Period1=10 descartado ({banned})")
    check(failures, "Coef1" not in banned, "Coef1 no pierde ningún nivel")
    dropped_row = next(r for r in report["rows"] if r["parameter"] == "Period1" and r["level"] == 10.0)
    check(failures, dropped_row["dropped"] and dropped_row["median_trades"] < 30,
          "la fila del manifiesto dice por qué se descartó")

    print("\n## el suelo nunca vacía un parámetro")
    two_levels = {"Coef1": [1.0, 2.0]}
    two_table = pilot.sample(two_levels, PILOT_CFG)
    all_thin = dict.fromkeys(two_table["pilot_id"], 1.0)   # todo por debajo del umbral
    banned2, report2 = pilot.decide(two_table, all_thin, 30, 1)
    check(failures, banned2 == {}, "con sólo 2 niveles, ninguno se descarta aunque los dos "
                                   f"operen poco ({banned2})")
    check(failures, any(r["kept_despite_floor"] for r in report2["rows"]),
          "el manifiesto dice que se salvó por el suelo de dos niveles")

    print("\n## poco soporte no descarta")
    sparse = {row.pilot_id: 1.0 for i, row in enumerate(table.itertuples())
             if row.Period1 == 10.0 and i < 3}   # menos que min_support
    banned3, _ = pilot.decide(table, sparse, 30, 5)
    check(failures, banned3 == {}, f"3 puntos no bastan para fiarse de la mediana ({banned3})")

    print("\n## plan.build con niveles descartados")
    design, cfg = brief(), settings()
    known = empty_known(["Period1", "Coef1", "Shift1"])
    plain, plain_report = plan.build(design, cfg, known)
    filtered, filtered_report = plan.build(design, cfg, known, banned={"Period1": {10.0}})
    check(failures, filtered_report["pilot_dropped"] == {"Period1": [10.0]},
          f"el informe nombra lo descartado ({filtered_report['pilot_dropped']})")
    check(failures, 10.0 not in set(filtered["param_Period1"]),
          "ninguna fila del lote filtrado lleva Period1=10")
    check(failures, plain_report["pilot_dropped"] == {},
          "sin `banned`, el informe no descarta nada")
    check(failures, 10.0 in set(plain["param_Period1"]),
          "sin `banned`, Period1=10 sigue en el lote")
    origin_kept = filtered[filtered["stratum"] == "origin"]
    check(failures, len(origin_kept) == 1 and origin_kept["param_Period1"].iloc[0] == 20.0,
          "el origen (Period1=20) no lo toca el descarte")

    print("\n## el origen nunca se descarta, aunque el piloto lo señale")
    banned_origin = {"Period1": {20.0}}   # 20.0 es el valor del origen en `brief()`
    _, origin_report = plan.build(design, cfg, known, banned=banned_origin)
    check(failures, origin_report["pilot_dropped"] == {},
          "un nivel que es el del origen no se descarta nunca")

    print()
    if failures:
        sys.exit(f"{len(failures)} propiedades rotas: {failures}")
    print("todas las propiedades se cumplen")


if __name__ == "__main__":
    main()
