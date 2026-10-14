#!/usr/bin/env python3
"""The chain's false-positive control: monkeys on a real population's footprint, step by step."""

import argparse
import hashlib
from datetime import date
from pathlib import Path

import pandas as pd

from core.manifest import write as write_manifest
from core.paths import report_dir
from core.study import output
from ledger import record, steprows
from pipeline.autopilot import judge
from studies.screening.falsePositives import inputs, many

SHOWN = ["nivel", "step", "estado", "n_in", "pass", "limbo", "n_out"]


def to_ledger(project: str, funnel: pd.DataFrame, source: dict) -> str:
    """One ledger row per step a rule was applied at, in the real population's own study.

    Args:
        project: The real population's project; the registry names its study.
        funnel: What many.run() returned as `funnel`.
        source: What inputs.load() returned as `source`.

    Returns:
        The line to print: the null population's rows only. They carry no `n_scored`:
        monkeys are a look at the segment, which `ledger.spend` counts, and not candidates,
        which would raise the study's N.
    """
    signed = steprows.signed(project)
    if signed is None:
        return "Ledger: el proyecto no tiene plantilla en registry.csv: no se apunta"
    sid, row = signed
    sha = hashlib.sha256(Path(source["criteria"]).read_bytes()).hexdigest()
    done = pd.DataFrame(funnel[(funnel["applied"] > 0) & (funnel["nivel"] == many.NULL)])
    for r in done.to_dict("records"):
        record.log(sid, {"step": float(r["step"]), "launched_by": "falsePositives",
                         "symbol": row["symbol"], "timeframe": row["timeframe"],
                         "segment": r["segment"], "n_in": int(r["n_in"]),
                         "n_out": int(r["n_out"]), "seeds": source["seed"],
                         "criterion": f"monos: criteria.yaml paso {r['step']} ({r['estado']})",
                         "config_hash": sha, "note": f"monos · {source['harvest']}"})
    return f"Ledger: {len(done)} filas de monos en {sid}"


def main() -> None:
    """Draw the monkeys, walk every population through the chain, and write the funnel."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--databank", required=True, help="the databank the gate harvest is under")
    ap.add_argument("--feed", required=True, help="SQX feed name, e.g. USDJPY_M1")
    ap.add_argument("--harvest", type=Path, default=None,
                    help="the harvest folder to read; the databank's newest when omitted")
    ap.add_argument("--criteria", type=Path, default=judge.CRITERIA,
                    help="the rules to judge by; the autopilot's criteria.yaml when omitted")
    ap.add_argument("--seed", type=int, default=None,
                    help="root of every draw; omitted, population.seed, else a fresh one")
    ap.add_argument("--ledger", action="store_true", help="write the monkeys' rows to the ledger")
    ap.add_argument("--set", action="extend", nargs="+", default=[], help="monkeys.per_donor=50")
    a = ap.parse_args()

    cfg = inputs.config(a.set)
    seed = cfg["population"]["seed"] if a.seed is None else a.seed
    loaded = inputs.load(a.project, a.databank, a.feed, seed, a.criteria, a.harvest)
    source = loaded["source"] | {"overrides": a.set}
    got = many.run(loaded, cfg)

    out = report_dir(a.project, a.databank, date.today().isoformat()) / "falsePositives"
    output.population(out, "falsePositives", got["population"],
                      f"Monos por la cadena — {a.project} / {a.databank}")
    got["funnel"].to_csv(out / "funnel.csv", index=False)
    got["rules"].to_csv(out / "reglas.csv", index=False)
    got["facts"].reset_index().to_parquet(out / "hechos_monos.parquet", compression="zstd")
    write_manifest(out, source,
                   f"python3 -m studies.screening.falsePositives.report --project {a.project} "
                   f"--databank '{a.databank}' --feed {a.feed} "
                   f"--harvest {source['harvest']} --criteria {a.criteria} "
                   f"--seed {source['seed']}" + (f" --set {' '.join(a.set)}" if a.set else ""),
                   got["money"] | {"donantes_fuera": len(got["skipped"])})

    print(got["funnel"][SHOWN].to_string(index=False))
    for r in pd.DataFrame(got["funnel"][got["funnel"]["nivel"] == many.NULL]).to_dict("records"):
        if r["no_aplicado"]:
            print(f"paso {r['step']} · {r['estado']}: {r['no_aplicado']}")
    for state in ("pass", "fail"):
        print(f"\n{state}, cada regla sola:")
        print(many.shares(got["rules"], list(dict.fromkeys(got["rules"]["nivel"])), state)
              .to_string(index=False, float_format="{:.1%}".format))
    money = got["money"]
    print(f"\n{money['monos']} monos de {money['donantes']} donantes "
          f"({len(got['skipped'])} fuera) · neto medio OOS {money['neto_medio_oos_R_año']:+.2f} "
          f"R/año · {money['con_neto_oos_positivo']:.1%} con neto OOS positivo")
    if a.ledger:
        print(to_ledger(a.project, got["funnel"], source))
    print(f"semilla {source['seed']} -> {out}")


if __name__ == "__main__":
    main()
