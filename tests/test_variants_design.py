#!/usr/bin/env python3
"""Known-answer test for the variant design: Latin hypercube, classes, size, controls (encargo 48 F)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqx.variants.design import lhs, plan

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_variants_pilot import brief, check, empty_known, settings


def main() -> None:
    """Fail loudly on any property that does not hold."""
    failures = []
    print("## size")
    cfg = {"n_min": 1000, "n_max": 5000, "per_coefficient": 8}
    for k, want, capped in [(5, 1000, False), (13, 1000, False), (15, 1088, False),
                            (20, 1848, False), (30, 3968, False), (35, 5000, True)]:
        got = plan.size(k, cfg)
        check(failures, got == (want, capped), f"k={k}: {got}")

    print("\n## hipercubo latino")
    live = {"A": [float(v) for v in range(10, 41)], "B": [0.5, 1.0, 1.5, 2.0]}
    pts = pd.DataFrame(lhs.draw(live, live, 300, 7))
    check(failures, pts["A"].between(10, 40).all() and (pts["A"] % 1 == 0).all(),
          "el entero cae en la caja y es entero")
    check(failures, pts["B"].between(0.5, 2.0).all(), "el decimal cae en la caja")
    # 31 enteros, 300 puntos: cada uno recibe 9 o 10 (estrato por columna)
    counts = pts["A"].value_counts()
    check(failures, counts.min() >= 8 and counts.max() <= 11,
          f"cobertura uniforme de los enteros ({counts.min()}-{counts.max()})")
    check(failures, pts.equals(pd.DataFrame(lhs.draw(live, live, 300, 7))), "misma semilla, mismo lote")
    kept = {"A": [v for v in live["A"] if v != 25.0], "B": live["B"]}
    check(failures, 25.0 not in set(pd.DataFrame(lhs.draw(live, kept, 300, 7))["A"]),
          "un nivel descartado por el piloto no sale")

    print("\n## plan.build")
    design = brief()
    design["parameters"].append({"name": "Shf1", "original": 3.0, "levels": [3.0], "center": 3.0,
                                 "eta2": 0.0, "class": "shift", "plateau": {"from": 3, "to": 3}})
    design["frozen"].append({"name": "Dead1", "value": 10.0, "class": "frozen"})
    names = ["Period1", "Coef1", "Shf1", "Shift1", "Dead1"]
    table, report = plan.build(design, settings(), empty_known(names))
    lhs_rows = table[table["stratum"] == "lhs"]
    check(failures, set(table["stratum"]) <= {"lhs", "origin", "canary", "inert"},
          f"estratos {sorted(set(table['stratum']))}")
    check(failures, table["variant_id"].iloc[0] == "P00000" and table["origin"].iloc[0],
          "la madre es P00000")
    check(failures, (lhs_rows["param_Shf1"] == 3.0).all() and (lhs_rows["param_Shift1"] == 1.0).all(),
          "shift y congelado quedan en el valor de la madre en todas las variantes")
    check(failures, report["asked"] == 40 and report["kept"] + report["shortfall"] == 40,
          f"tamaño pedido 40 ({report['kept']} + faltan {report['shortfall']})")
    check(failures, table["tuple_hash"].is_unique, "ninguna tupla repetida")
    check(failures, (table[table["stratum"] == "inert"]["canary_expect_same_as"] == "P00000").all()
          and (table["stratum"] == "inert").sum() == 1, "un par inerte, que debe igualar a la madre")
    check(failures, np.isclose(lhs_rows["param_Period1"].min(), 10, atol=3), "cubre el borde de la meseta")

    print()
    if failures:
        sys.exit(f"{len(failures)} propiedades rotas: {failures}")
    print("todas las propiedades se cumplen")


if __name__ == "__main__":
    main()
