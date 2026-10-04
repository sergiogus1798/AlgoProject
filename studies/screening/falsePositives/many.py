"""The control: monkeys on every real strategy's footprint, through the chain, beside the real ones."""

import time

import pandas as pd

from core.study import blocks, result as envelope
from engines.nulls import verdict
from studies.screening.falsePositives import chain, model

MODULE = "studies.screening.falsePositives"
# Why a step, or one fact of a step, is not applied to a monkey. Owner-facing: Spanish.
NOT_APPLIED = {
    "8": "al mono no se le han construido los hechos que salen del escaneo de ticks de "
         "Darwinex (spread real, edge por coste); las reglas sin aplicar, en reglas.csv",
    "10": "el mono en los otros mercados (su huella del retest, colocada sobre las barras de "
          "cada mercado) no está construido",
    "12": "las hermanas escaladas las fabrica SQX reescalando parámetros, y un mono no tiene "
          "parámetros; además la regla nunca da Fallo",
    "14": "el estrés combinado del MC Retest es una tarea de SQX sin modelo en Python",
}


def population(inputs: dict, cfg: dict) -> tuple[pd.DataFrame, list[dict]]:
    """Every monkey's step-8 facts, donor by donor.

    Args:
        inputs: What inputs.load() returned.
        cfg: What inputs.config() returned.

    Returns:
        The facts, monkey x fact key, and the donors left out with the reason: no trades on
        one of the two samples (no footprint to match), or a P/L the bars do not reproduce
        (below `verdict.RECONCILE_FLOOR`, encargo 9 §5.2). Nothing else is left out: the
        donors are not screened. A donor's monkeys are judged in their own batch, which
        changes nothing — no fact of the gate depends on who else is in the population.
    """
    real, knobs = inputs["real"], cfg["monkeys"]
    donors = dict(tuple(real["trades"].groupby("identity", observed=True)))
    found, skipped = [], []
    for i, (key, own) in enumerate(donors.items(), 1):
        if set(own["sample"]) != set(model.SAMPLES):
            skipped.append({"donante": key, "motivo": "sin operaciones en IS o en OOS"})
            continue
        drawn, corr = model.monkeys(own, real["bars"], inputs["nullcfg"], knobs, key)
        if corr < verdict.RECONCILE_FLOOR:
            skipped.append({"donante": key, "motivo": f"no reconcilia ({corr:.4f})"})
            continue
        found.append(chain.facts8(chain.as_harvest(drawn, real), inputs["gate_cfg"]))
        envelope.progress(5 + 85 * i // len(donors), f"monos {i}/{len(donors)}")
    return pd.concat(found), skipped


def beside(monkeys: pd.DataFrame, real: pd.DataFrame, on: list[str]) -> pd.DataFrame:
    """Two funnels, or two rule tables, as one: the monkeys' columns and the real ones'."""
    return monkeys.merge(real.drop(columns=[c for c in ("segment", "rules", "applied")
                                            if c in real and c not in on]),
                         on=on, suffixes=("_monos", "_reales"))


def run(inputs: dict, cfg: dict) -> dict:
    """The side-by-side funnel and what each rule alone lets through.

    Args:
        inputs: What inputs.load() returned.
        cfg: What inputs.config() returned.

    Returns:
        {"population", "funnel", "rules", "skipped", "facts"}. The real population is put
        through the same code as the monkeys, on its own harvest, so the two columns of the
        funnel differ in the trades and in nothing else.
    """
    started, steps, tags = time.time(), inputs["steps"], inputs["tags"]
    facts, skipped = population(inputs, cfg)
    own = chain.facts8(inputs["real"], inputs["gate_cfg"])
    walked = [chain.walk({"8": f}, list(f.index), steps, tags) for f in (facts, own)]
    funnel = beside(walked[0][0], walked[1][0], ["step"])
    rules = beside(walked[0][1], walked[1][1], ["step", "rule", "applied"])
    rules["deja_pasar_monos"] = 1 - rules["fail_monos"] / rules["n_in_monos"]
    funnel["estado"] = ["sin regla" if not r else "aplicado" if a == r
                        else f"{a} de {r} reglas" for r, a in zip(funnel["rules"], funnel["applied"])]
    funnel["no_aplicado"] = [NOT_APPLIED.get(s, "") if a < r else ""
                             for s, r, a in zip(funnel["step"], funnel["rules"], funnel["applied"])]
    net = facts[["gate.scorecard.is_net_per_year_r", "gate.scorecard.oos_net_per_year_r"]]
    money = {"monos": len(facts), "donantes": facts.index.str.split("#").str[0].nunique(),
             "neto_medio_is_R_año": float(net.iloc[:, 0].mean()),
             "neto_medio_oos_R_año": float(net.iloc[:, 1].mean()),
             "con_neto_oos_positivo": float((net.iloc[:, 1] > 0).mean())}
    first = funnel.iloc[0]
    warnings = [] if inputs["source"]["frozen"] else [
        {"code": "provisional", "state": "watch", "highlight": True,
         "text": "criteria.yaml no está congelado: todas las reglas aplicadas son provisionales."}]
    result = envelope.envelope(
        MODULE, None, None, cfg, started,
        [envelope.tab("embudo", "El embudo, monos y reales", [
            blocks.table("Paso a paso", funnel,
                         "n_out = pass + limbo: un limbo sigue. Un paso sin aplicar deja pasar "
                         "a todos, y desde ahí los monos vivos son un techo, no una medida."),
            blocks.table("El mono pierde dinero", pd.DataFrame([money]),
                         "Neto medio por año en R. Si la población nula gana de media, se le "
                         "ha regalado algo (encargo 9 §5.1)."),
            blocks.table("Donantes fuera", pd.DataFrame(skipped, columns=["donante", "motivo"]))]),
         envelope.tab("reglas", "Regla a regla", [
             blocks.table("Lo que cada regla deja pasar, sola", rules,
                          "Sobre los que entran al paso. deja_pasar_monos = (pass + limbo) / "
                          "n_in: la tasa de falsos positivos de esa regla aislada.")])],
        blocks.verdict(f"{int(first['n_out_monos'])} de {int(first['n_in_monos'])} monos "
                       f"cruzan el paso {first['step']}", "watch",
                       "Cuántas estrategias sin ningún edge deja vivas la cadena. Mide la "
                       "mortalidad de los filtros, no la del generador de SQX."),
        warnings=warnings)
    envelope.progress(100, f"{len(facts)} monos")
    return {"population": result, "funnel": funnel, "rules": rules, "skipped": skipped,
            "facts": facts, "money": money}
