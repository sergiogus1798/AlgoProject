"""The control: a null population and the same one with a planted edge, through the chain, beside the real one."""

import json
import time
from typing import Any, TypedDict

import numpy as np
import pandas as pd

from core import fanout
from core.study import blocks, result as envelope
from engines.nulls import lookup, verdict
from pipeline.autopilot import criteria
from studies.screening.analysis import resample
from studies.screening.falsePositives import chain, model
from studies.screening.falsePositives.inputs import Loaded
from studies.screening.gate.cascade import PREFIX

MODULE = "studies.screening.falsePositives"
NULL, REAL = "nula", "reales"     # the populations beside the planted ones, named by their edge
# Why a step is not applied to a monkey. Owner-facing: Spanish.
NOT_APPLIED = {
    "10": "el mono en los otros mercados (su huella del retest, colocada sobre las barras de "
          "cada mercado) no está construido",
    "12": "las hermanas escaladas las fabrica SQX reescalando parámetros, y un mono no tiene "
          "parámetros; además la regla nunca da Fallo",
    "14": "el estrés combinado del MC Retest es una tarea de SQX sin modelo en Python",
}
# What a rule's count on monkeys is NOT, by the fact it reads. Owner-facing: Spanish.
INHERITED = "hereda de la donante (mismo número de operaciones): no se mide"
CENTRED = "centrada sobre todos, con la cascada apagada: diagnóstico"
POSITIVE = "la retención sólo existe con exceso medio positivo: el resto, sin dato"
NOTES = {"presencia_passed": "un mono siempre está en el retest: no se mide",
         "sanidad_passed": INHERITED, "sanidad_value": INHERITED, "is_trades_per_year": INHERITED,
         "z_frec": f"{INHERITED}; {CENTRED}", "t_b": CENTRED, "e_fin": CENTRED,
         "ret_datos": POSITIVE, "retraso_ret_min": POSITIVE}

_SHARED: dict = {}     # what `_donor` reads: set before the fan-out, handed over by fork


def _donor(key: str) -> pd.DataFrame | str:
    """One donor's monkeys as trade lists, or the reason it is left out."""
    inputs = _SHARED["inputs"]
    drawn, corr = model.monkeys(_SHARED["donors"][key], inputs["real"]["bars"], inputs["nullcfg"],
                                _SHARED["knobs"], key)
    return drawn if corr >= verdict.RECONCILE_FLOOR else f"no reconcilia ({corr:.4f})"


def population(inputs: Loaded, cfg: dict) -> tuple[pd.DataFrame, list[dict]]:
    """The monkeys every population is made of, donor by donor.

    Args:
        inputs: What inputs.load() returned.
        cfg: What inputs.config() returned.

    Returns:
        The monkeys' trades on both samples, and the donors left out with the reason: no
        trades on one of the two samples (no footprint to match), or a P/L the bars do not
        reproduce (below `verdict.RECONCILE_FLOOR`, encargo 9 §5.2). `population.per_level`
        / `monkeys.per_donor` donors are drawn, by the run's seed, among those with both
        samples; the donors are not screened. One donor per process (`core.fanout`).
    """
    donors = dict(tuple(inputs["real"]["trades"].groupby("identity", observed=True)))
    whole = [k for k, own in donors.items() if set(own["sample"]) == set(model.SAMPLES)]
    knobs, want = cfg["monkeys"], -(-cfg["population"]["per_level"] // cfg["monkeys"]["per_donor"])
    rng = np.random.default_rng([inputs["source"]["seed"], 8])
    picked = [whole[i] for i in rng.permutation(len(whole))[:want]]
    _SHARED.update(inputs=inputs, knobs=knobs, donors=donors)
    resample.warm()
    lookup.warm()
    got = {}
    for i, (key, res) in enumerate(fanout.run(_donor, {k: len(donors[k]) for k in picked},
                                              fanout.CORES), 1):
        got[key] = res
        envelope.progress(5 + 35 * i // len(picked), f"monos {i}/{len(picked)}")
    _SHARED.clear()
    skipped = [{"donante": k, "motivo": "sin operaciones en IS o en OOS"}
               for k in donors if k not in whole]
    skipped += [{"donante": k, "motivo": got[k]} for k in picked if isinstance(got[k], str)]
    return (pd.concat([got[k] for k in picked if not isinstance(got[k], str)],
                      ignore_index=True), skipped)


def shares(rules: pd.DataFrame, order: list[str], state: str) -> pd.DataFrame:
    """Rule x population: the share of a step's entrants the rule alone leaves in `state`."""
    done = rules[rules["applied"]]
    wide = pd.Series(done[state] / done["n_in"]).groupby([done["label"], done["nivel"]]).first().unstack()
    return (wide.reindex(index=list(dict.fromkeys(done["label"])), columns=order)
            .rename_axis("regla").reset_index())


class Money(TypedDict):
    """What the null monkeys earn per year in R: they must lose."""
    monos: int
    donantes: int
    neto_medio_is_R_año: float
    neto_medio_oos_R_año: float
    con_neto_oos_positivo: float


class Control(TypedDict):
    """The control's result: the page, both rule tables, the donors left out, the facts."""
    population: dict[str, Any]
    funnel: pd.DataFrame
    rules: pd.DataFrame
    skipped: list[dict]
    facts: pd.DataFrame
    money: Money


def run(inputs: Loaded, cfg: dict) -> Control:
    """Every population's funnel and what each rule alone does to each.

    Args:
        inputs: What inputs.load() returned.
        cfg: What inputs.config() returned.

    Returns:
        {"population", "funnel", "rules", "skipped", "facts", "money"}. `funnel` and `rules`
        are chain.walk()'s with `nivel` in front: "nula", each planted edge ("0.05"…) and
        "reales". The planted populations are the null monkeys themselves with the edge
        added, and the real population goes through the same code on its own harvest, so
        two rows differ in the trades and in nothing else. `rules` also carries each
        state's share of `n_in` and `nota`, what the count is not.
    """
    started, steps, tags, gate_cfg = time.time(), inputs["steps"], inputs["tags"], inputs["gate_cfg"]
    trades, skipped = population(inputs, cfg)
    harvest = chain.as_harvest(trades, inputs["real"])
    edges = {NULL: 0.0} | {f"{edge:.2f}": edge for edge in cfg["population"]["edges"]}
    names, done = {edge: name for name, edge in edges.items()}, []
    got = chain.facts_edges(harvest, gate_cfg, tuple(edges.values()), lambda edge: (done.append(edge), envelope.progress(
        40 + 45 * len(done) // len(edges), f"cadena, ventaja {names[edge]}"))[1])
    facts = {name: got[edge] for name, edge in edges.items()}
    facts[REAL] = chain.facts8(inputs["real"], gate_cfg)
    walked = {name: chain.walk({"8": f}, list(f.index), steps, tags, inputs["batches"])
              for name, f in facts.items()}
    funnel, rules = (pd.concat({name: got[i] for name, got in walked.items()}, names=["nivel"])
                     .reset_index("nivel").reset_index(drop=True) for i in (0, 1))
    for state in criteria.RANK:
        rules[f"pct_{state}"] = rules[state] / rules["n_in"]
    rules["nota"] = ["; ".join(dict.fromkeys(NOTES[f.removeprefix(PREFIX)] for f in sorted(
        criteria.reads([rule])) if f.removeprefix(PREFIX) in NOTES))
        for rule in map(json.loads, rules["rule"])]
    funnel["estado"] = ["sin regla" if not r else "aplicado" if a == r
                        else f"{a} de {r} reglas" for r, a in zip(funnel["rules"], funnel["applied"])]
    funnel["no_aplicado"] = [NOT_APPLIED.get(s, "") if a < r else ""
                             for s, r, a in zip(funnel["step"], funnel["rules"], funnel["applied"])]
    net = facts[NULL][[PREFIX + "is_net_per_year_r", PREFIX + "oos_net_per_year_r"]]
    money = Money(monos=len(net), donantes=facts[NULL].index.str.split("#").str[0].nunique(),
                  neto_medio_is_R_año=float(net.iloc[:, 0].mean()),
                  neto_medio_oos_R_año=float(net.iloc[:, 1].mean()),
                  con_neto_oos_positivo=float((net.iloc[:, 1] > 0).mean()))
    first = funnel[funnel["step"] == funnel["step"].iloc[0]].set_index("nivel")
    warnings = [] if inputs["source"]["frozen"] else [
        {"code": "provisional", "state": "watch", "highlight": True,
         "text": "criteria.yaml no está congelado: todas las reglas aplicadas son provisionales."}]
    notes = rules.loc[rules["nota"] != "", ["label", "nota"]].drop_duplicates()
    result = envelope.envelope(
        MODULE, None, None, cfg, started,
        [envelope.tab("embudo", "El embudo, por población", [
            blocks.table("Paso a paso", funnel.drop(columns=["segment", "rules", "applied"]),
                         "nivel = la ventaja plantada (Sharpe por operación, neto de costes); «nula» no lleva "
                         "ninguna. n_out = pass + limbo: un limbo sigue. Un paso sin aplicar "
                         "deja pasar a todos, y desde ahí los vivos son un techo, no una medida."),
            blocks.table("El mono pierde dinero", pd.DataFrame([money]),
                         "Población nula, neto medio por año en R. Si gana de media es la "
                         "deriva del activo (largos sobre un índice), que R3 descuenta, o se "
                         "le ha regalado algo (encargo 9 §5.1)."),
            blocks.table("Donantes fuera", pd.DataFrame(skipped, columns=pd.Index(["donante", "motivo"])))]),
         envelope.tab("reglas", "Regla a regla", [
             blocks.table("Pasa: lo que cada regla, sola, da por bueno", shares(rules, list(facts), "pass"),
                          "Proporción de las que entran al paso. En «nula» es lo que se cuela; "
                          "en las plantadas, lo que se conserva.", 3),
             blocks.table("Falla: lo que cada regla, sola, elimina", shares(rules, list(facts), "fail"),
                          "En las plantadas es la potencia que esa regla cuesta. Lo que no es "
                          "ni Pasa ni Falla es Limbo, y sigue.", 3),
             blocks.table("Lo que una cifra no es", notes,
                          "Con la cascada apagada cada regla se calcula para todas.")])],
        blocks.verdict(
            " · ".join(f"{name}: {int(first.loc[name, 'n_out'])} de {int(first.loc[name, 'n_in'])}"
                       for name in facts) + f" cruzan el paso {funnel['step'].iloc[0]}", "watch",
            "Cuántas estrategias sin ventaja deja vivas la cadena, y cuántas con una ventaja "
            "plantada conserva. Mide los filtros, no el generador de SQX."),
        warnings=warnings)
    envelope.progress(100, f"{len(net)} monos por población")
    return Control(population=result, funnel=funnel, rules=rules, skipped=skipped,
                   facts=pd.concat(facts, names=["nivel", "identity"]), money=money)
