"""The bank table as the owner reads it: the Spanish text the command prints and the study-contract result."""

from typing import Any

import pandas as pd

from core.study import blocks, result
from portfolio.funded.sim import measures
from portfolio.funded.sim.table import Built

MODULE = "portfolio.funded.sim"
_PHASES = ("phase1", "phase2", "phase3")


def _pct(value: float | None, digits: int = 0) -> str:
    """A fraction as a percentage, «—» when there is none."""
    return "—" if value is None or value != value else f"{100 * value:.{digits}f}%"


def _risk(row: dict) -> str:
    """Risk per phase as «f1/f2/f3 → fondeada», in % of the initial balance."""
    phases = "/".join(
        f"{100 * row[f'risk_{p}']:g}" for p in _PHASES if row[f"risk_{p}"] is not None
    )
    return f"{phases} → {100 * row['risk_funded']:g}"


def _breakeven(row: dict, hs: list[float]) -> str:
    """The break-even haircut, or which side of zero the whole curve stays on."""
    if row["breakeven_h"] is not None:
        return _pct(row["breakeven_h"])
    return (
        f">{_pct(hs[-1])}"
        if row[f"ev_h{round(100 * hs[-1])}"] > 0
        else f"<{_pct(hs[0])}"
    )


def lines(table: Built, owner: dict) -> list[str]:
    """The printed tables: the economics per plan and policy, the odds and the cash drawdown, the two re-buy policies side by side."""
    hs = owner["haircuts"]
    out = [
        f"{'plan':27} {'recompra':9} {'precio$':>8} {'riesgo % f→fond':>17} {'VE/compra':>10} {'VE/$':>6} {'VE/mes':>8} {'c/imp./mes':>10} "
        f"{'[90 %]':>17} {'mono':>8} {'ventaja':>8} {'h equil.':>8}  "
        + " ".join(f"{'h=' + _pct(h):>8}" for h in hs)
    ]
    for r in table["rows"]:
        months = r["ev"] / r["ev_per_month"] if r["ev_per_month"] else float("nan")
        band = f"[{r['ev_lo'] / months:.1f}, {r['ev_hi'] / months:.1f}]"
        out.append(
            f"{r['plan']:27} {r['rebuy']:9} {r['price_usd']:8.2f} {_risk(r):>17} {r['ev_per_purchase']:10.1f} "
            f"{r['ev_per_dollar']:6.2f} {r['ev_per_month']:8.1f} {measures.after_tax(r['ev_per_month'], owner['tax_rate']):10.1f} "
            f"{band:>17} {r['ev_monkey']:8.1f} "
            f"{r['advantage']:8.1f} {_breakeven(r, hs):>8}  "
            + " ".join(f"{r[f'ev_h{round(100 * h)}']:8.1f}" for h in hs)
        )
    out += [
        "",
        f"{'plan':27} {'recompra':9} {'P fases':>14} {'P 1er cobro':>11} {'cuotas $':>8} {'compras':>8} {'→1er cobro':>10} "
        f"{'cobros/fond':>11} {'vida d':>7} {'desembolso p50/p90/p99 $':>25} {'tope caja':>9}  regla que más suspende",
    ]
    for r in table["rows"]:
        phases = "/".join(
            _pct(r[f"p_{p}"]) for p in _PHASES if r[f"risk_{p}"] is not None
        )
        outlay = f"{r['outlay_p50']:.0f}/{r['outlay_p90']:.0f}/{r['outlay_p99']:.0f}"
        out.append(
            f"{r['plan']:27} {r['rebuy']:9} {phases:>14} {_pct(r['p_first_payout']):>11} {r['fees']:8.1f} {r['purchases']:8.2f} "
            f"{r['purchases_to_first']:10.2f} {r['payouts_per_funded']:11.2f} {r['funded_life_days']:7.0f} "
            f"{outlay:>25} "
            f"{_pct(r['budget_stop']):>9}  {r['worst_rule']} ({_pct(r['worst_rule_share'])})"
        )
    if table["addons"]:
        out += [
            "",
            f"{'add-ons':27} {'recompra':9} {'conjunto':42} {'precio$':>8} {'VE':>9} {'ΔVE (ya neto del precio)':>25}",
        ]
        out += [
            f"{a['plan']:27} {a['rebuy']:9} {a['options']:42} {a['price_usd']:8.2f} {a['ev']:9.1f} {a['delta_ev']:25.1f}"
            for a in table["addons"]
        ]
    return out + side_by_side(table["rows"], owner)


def side_by_side(rows: list[dict], owner: dict) -> list[str]:
    """Each plan's EV at the deciding haircut under every re-buy policy, with its Monte Carlo standard error."""
    policies = owner["rebuy"]
    by = {(r["plan"], r["rebuy"]): r for r in rows}
    out = [
        "",
        f"{'recompra, lado a lado':27} "
        + " ".join(f"{'VE ' + p + ' ± e.t.':>22}" for p in policies)
        + (f" {'diferencia':>11}  ¿dentro del error?" if len(policies) == 2 else ""),
    ]
    for plan in dict.fromkeys(r["plan"] for r in rows):
        got = [by[plan, p] for p in policies]
        line = f"{plan:27} " + " ".join(
            f"{'%.1f ± %.1f' % (r['ev'], r['ev_se']):>22}" for r in got
        )
        if len(got) == 2:
            # ponytail: the two policies share paths and hazards, so this quadrature sum overstates
            # the error of the difference; pair the draws if a «no» here ever decides something
            gap, se = (
                got[0]["ev"] - got[1]["ev"],
                (got[0]["ev_se"] ** 2 + got[1]["ev_se"] ** 2) ** 0.5,
            )
            line += f" {gap:11.1f}  {'sí' if abs(gap) < 2 * se else 'no'}"
        out.append(line)
    return out


def sentence(table: Built, owner: dict) -> str:
    """The decision-shaped sentence of encargo 33 §4, as a function of the h and the budget given."""
    h, lo = owner["haircut_decides"], owner["haircuts"][0]
    given = (
        f"Con h = {_pct(h)}, una caja de {owner['budget_eur']:g} € (1 € = {owner['eurusd']:g} $) y "
        f"las políticas de recompra comparadas ({', '.join(owner['rebuy'])})"
    )
    best = table["rows"][0]
    if best["ev"] <= 0:
        return f"{given}: ningún plan tiene VE_banco positivo con esta cartera."
    live = (
        "cualquier"
        if best["breakeven_h"] is None
        else f"al menos el {_pct(1 - best['breakeven_h'])} del"
    )
    only_full = [
        f"{r['plan']} ({r['rebuy']})"
        for r in table["rows"]
        if r["ev"] <= 0 < r[f"ev_h{round(100 * lo)}"]
    ]
    tail = (
        f" Positivos sólo con h = {_pct(lo)} y no con h = {_pct(h)}: {', '.join(only_full)}."
        if only_full
        else ""
    )
    return (
        f"{given}: el VE_banco más alto es {best['plan']} con recompra «{best['rebuy']}», riesgo {_risk(best)} % por operación "
        f"(fases → fondeada), VE {best['ev_per_month']:+.1f} $/mes ({measures.after_tax(best['ev_per_month'], owner['tax_rate']):+.1f} con impuestos) [{best['ev_lo']:.0f}, {best['ev_hi']:.0f}] $ "
        f"en el horizonte; sigue positivo con {live} edge del OOS; ventaja sobre el mono "
        f"{best['advantage']:+.1f} $.{tail} Esto ordena, no decide: el criterio robusto de compra "
        f"(encargo 33 §3.5.6) es tuyo."
    )


def contract(
    table: Built, cfg: dict, meta: dict, flags: dict[str, dict], started: float
) -> dict[str, Any]:
    """The run as a study result: the table, the add-ons, the curve EV(h), every unconfirmed rule a warning.

    Args:
        table: `table.build()`'s dict.
        cfg: The config it ran under.
        meta: The path set's `label`.
        flags: rule_key -> `{status, text, plans}` over every plan simulated.
        started: `time.time()` when the run began.
    """
    owner = cfg["owner"]
    hs = owner["haircuts"]
    rows = pd.DataFrame(table["rows"])
    curve = {
        "kind": "lines",
        "title": "VE_banco según el recorte h del edge",
        "unit": "USD",
        "x": [round(100 * h) for h in hs],
        "series": [
            {
                "label": f"{r['plan']} · {r['rebuy']}",
                "role": "sim",
                "values": [r[f"ev_h{round(100 * h)}"] for h in hs],
            }
            for r in table["rows"]
        ],
    }
    note = (
        "VE en USD por banco simulado sobre todo el horizonte; el intervalo al 90 % es sólo error "
        "de Monte Carlo. ΔVE de un add-on ya descuenta su precio en cada compra."
    )
    tabs = [
        result.tab(
            "tabla",
            "La caja por plan",
            [
                {"kind": "callout", "text": sentence(table, owner), "state": "info"},
                blocks.table(
                    "Un plan y una política de recompra por fila, ordenado por VE_banco con el recorte elegido",
                    rows,
                    note,
                ),
                *(
                    [
                        blocks.table(
                            "Add-ons: ΔVE contra el plan sin add-ons",
                            pd.DataFrame(table["addons"]),
                            note,
                        )
                    ]
                    if table["addons"]
                    else []
                ),
            ],
        ),
        result.tab(
            "recorte",
            "VE(h)",
            [curve],
            note="Cuánto edge puede perderse antes de que la caja pierda.",
        ),
    ]
    warnings = [
        {
            "code": key,
            "state": "watch",
            "text": f"sin confirmar ({f['status']}) — {', '.join(sorted(f['plans']))}: {f['text']}",
        }
        for key, f in flags.items()
    ]
    return result.envelope(
        MODULE,
        meta["label"],
        None,
        cfg,
        started,
        tabs,
        warnings=warnings,
        summary={
            "best": table["rows"][0]["plan"],
            "rebuy": table["rows"][0]["rebuy"],
            "ev": table["rows"][0]["ev"],
        },
    )
