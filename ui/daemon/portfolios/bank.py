"""«Banco» (encargo 33 §7.5): the bank's expected value per plan, re-buy policy and haircut, and the decision."""

import pandas as pd

from portfolio.funded.decide import tables
from portfolio.funded.sim import inputs, table as table_mod
from ui.daemon.portfolios import parts, shelf
from ui.text import numbers

REBUY = {"none": "sin recompra", "same_plan": "mismo plan"}
NEED = ("una cartera de fondeo con su etapa B (en «Fondeo»), y aquí el horizonte y los tramos del "
        "edge; después «Calcular la caja».")


def missing() -> list[str]:
    """«Falta owner.<x>: decisión tuya», one per input the bank simulation refuses without."""
    return [f"Falta {line.split(' — ')[0]}: decisión tuya — {line.split(' — ')[-1]}. Sin ella no se calcula la caja."
            for line in inputs.refuse(inputs.load([])) + table_mod.variants(inputs.load([]))[1]]


def decision() -> dict | None:
    """The newest decision `funded.decide.run` wrote, None while there is none."""
    found = sorted((shelf.ROOT / "bank" / "decisions").glob("*.json"))
    return shelf.load(found[-1]) if found else None


def read(bank: str = "", plan: str = "", **_: str) -> dict:
    """The tabs of one bank table: Decisión, Tabla VE, VE(h), Supuestos."""
    base = {"missing": missing(), "banks": [t["folder"].name for t in tables.runs()]}
    if not base["banks"]:
        return parts.empty("No hay ninguna tabla del banco.", NEED) | base
    folder = shelf.folder("bank", bank if bank in base["banks"] else base["banks"][0])
    m = shelf.load(folder / "manifest.json")
    src, owner = m["paths"]["source"], m["config"]["owner"]
    hs = [f"ev_h{int(round(parts.pct(h)))}" for h in owner["haircuts"]]
    at = f"ev_h{int(round(parts.pct(owner['haircut_decides'])))}"
    frame = pd.read_parquet(folder / "table.parquet").sort_values(at, ascending=False)
    plan = plan if plan in set(frame["plan"]) else frame["plan"].iloc[0]
    rows = [[r["plan"], REBUY.get(r["rebuy"], r["rebuy"]), r["price_usd"], *[round(r[h], 1) for h in hs], round(r["ev_monkey"], 1), round(r["ev_se"], 1),
             None if pd.isna(r["breakeven_h"]) else parts.pct(r["breakeven_h"]), parts.pct(r["p_first_payout"]),
             round(r["purchases"], 2), round(r["fees"], 1)] for r in frame.to_dict("records")]
    heads = ["plan", "recompra", "precio $", *[f"VE $ con h = {int(round(parts.pct(h)))} %" for h in owner["haircuts"]],
             "mono $", "± error $", "h de equilibrio %", "P(1.er cobro) %", "compras", "cuotas $"]
    helps = [None, "Mismo plan: se recompra el mismo plan mientras quede caja. Sin recompra: una sola compra.",
             "Lo que cuesta la cuenta hoy.", *[parts.WORDS["ev"] + " " + parts.WORDS["h"]] * len(hs),
             parts.WORDS["monkey"], parts.WORDS["se"], parts.WORDS["breakeven_h"], parts.WORDS["p_first_payout"],
             parts.WORDS["purchases"], "Lo que se paga en cuotas de media en el horizonte."]
    edge = (f"Edge fuera de muestra ({'+'.join(src['edge_from'])}): {src['edge_oos'] / src['edge_build']:.0%} "
            f"del de build.")
    facts = (f"Cartera de {src['plan']} (K = {len(src['members'])}) · {numbers.num(m['n_paths'])} caminos de {m['horizon']} "
             f"días · {numbers.num(m['configurations'])} configuraciones probadas · 1 € = {m['eurusd']} $ · {edge}")
    table = parts.table(f"VE del banco por plan y política de recompra, ordenado por h = "
                        f"{owner['haircut_decides']:.0%}", heads, rows,
                        "En dólares por caja, sobre todo el horizonte. Un plan cuya cartera es de OTRO plan se "
                        "valora con caminos prestados: la decisión no lo admite. No compares tablas de horizontes "
                        "distintos.", helps)
    return base | {"bank": folder.name, "plan": plan, "plans": list(dict.fromkeys(frame["plan"])),
                   "relaxed": parts.relaxed(src.get("relaxed")), "empty": None,
                   "tabs": [decided(), parts.tab("Tabla VE", parts.callout(facts), table),
                            curve(frame, plan, owner, hs), assumed(folder)]}


def decided() -> dict:
    """«Decisión»: the sentence of `funded.decide.run`, in the owner's words, and each plan's gate."""
    d = decision()
    if d is None:
        return parts.tab("Decisión", parts.callout("Todavía no hay decisión escrita: «Calcular la caja» la "
                                                   "escribe al acabar.", "watch"))
    rows = [[r["plan"], REBUY.get(r["rebuy"], r["rebuy"]), round(r["ev"], 1), round(r["ev_se"], 1), round(r["ev_monkey"], 1), r["reason"]] for r in d["rows"]]
    states = [[None] * 5 + ["pass" if r["reason"] == "sí" else None if r["reason"].startswith("cartera de otro plan")
                            else "fail"] for r in d["rows"]]       # another plan's portfolio is a filter, not a failure
    table = parts.table(f"Cada plan contra los filtros, con h = {d['rows'][0]['h']:.0%}" if d["rows"] else "Sin planes",
                        ["plan", "recompra", "VE $", "± error $", "mono $", "¿se compra?"], rows,
                        "«Sí», o el primer filtro que no pasa.",
                        [None, None, parts.WORDS["ev"], parts.WORDS["se"], parts.WORDS["monkey"], None], states)
    waits = parts.table("Lecturas que siguen abiertas (tuyas)", ["lectura"], [[line] for line in d.get("open", [])])
    marks = [parts.callout("AJUSTADO: la decisión sale de corridas de prueba o sin exigir veredicto — no es un "
                           "resultado.", "watch")] if d.get("adjusted") else []
    return parts.tab("Decisión", *marks, parts.callout(d["sentence"], "pass" if d.get("chosen") else "watch"),
                     table, waits, note=f"Decidido el {d['decided'].replace('T', ' ')}.")


def curve(frame: pd.DataFrame, plan: str, owner: dict, hs: list[str]) -> dict:
    """«VE(h)»: one plan's EV against the haircut, a line per re-buy policy, and its monkey."""
    mine = frame[(frame["plan"] == plan) & (frame["options"] == "")]
    series = [{"label": f"{REBUY.get(r['rebuy'], r['rebuy'])} (± {r['ev_se']:.1f} $ de error)", "role": "sim",
               "values": [float(r[h]) for h in hs]} for r in mine.to_dict("records")]
    series += [{"label": f"mono · {REBUY.get(r['rebuy'], r['rebuy'])}", "role": "reference", "values": [float(r["ev_monkey"])] * len(hs)}
               for r in mine.to_dict("records")]
    lines = {"kind": "lines", "title": f"VE del banco de {plan} según el recorte h del edge", "unit": "USD",
             "x": [int(round(parts.pct(h))) for h in owner["haircuts"]], "series": series, "zero_shade": True,
             "x_label": "recorte h del edge (%)", "y_label": "VE del banco ($)",
             "note": parts.WORDS["h"] + " " + parts.WORDS["monkey"] + " Una curva por debajo de su mono "
                     "(línea gris) no gana nada que la suerte no dé."}
    return parts.tab("VE(h)", lines, note="El plan se elige arriba, en «Plan».")


def assumed(folder: shelf.Path) -> dict:
    """«Supuestos»: what the table took for granted — the catalogue facts still unconfirmed."""
    doc = shelf.load(folder / "result.json")
    rows = [[w["code"], w["text"]] for w in doc.get("warnings", [])]
    return parts.tab("Supuestos", parts.table("Lo que la tabla da por bueno sin confirmar", ["regla", "supuesto"],
                                              rows, "Cada fila es un hecho de la empresa que el catálogo no tiene "
                                              "confirmado; cambia el resultado si resulta ser otro."))
