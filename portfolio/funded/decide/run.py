"""THE COMMAND: which challenge to buy — the bank tables read by encargo 33 §3.5, the decision in Spanish with its cost beside its gain."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from core.paths import portfolio_dir
from portfolio.funded.decide import choose, tables
from portfolio.funded.sim import inputs

OPEN = (
    "«cuyo puesto no cambie mucho al mover h» (§3.5.6): cuánto es mucho no está dicho — se enseña el puesto en cada h y no se juzga",
    "el listón es VE > 0 y VE > mono con la media simulada; no se exige que el intervalo de Monte Carlo quede por encima",
    "un plan simulado con la cartera elegida para otro plan se enseña pero no se puede comprar (una cartera por plan, PLAN §14)",
    "el horizonte de la simulación (días por camino) lo fija quien genera los caminos: el VE es «sobre ese horizonte»",
    "con qué datos no vistos se valida la combinación elegida (DECISIONS #11): esta decisión no se ha validado en ninguno",
)


def consistent(used: list[dict]) -> dict:
    """The one config every table was simulated under; refuses a mix, a stale table or a missing input."""
    cfgs = [t["manifest"]["config"] for t in used]
    owner, now = cfgs[0]["owner"], inputs.load([])["owner"]
    if any((c["owner"], c["gaps"]) != (owner, cfgs[0]["gaps"]) for c in cfgs):
        sys.exit("No decido: las tablas de caja se simularon con valores distintos (owner.* o gaps.*) y sus "
                 "VE no se pueden comparar. Vuelve a simularlas con los mismos, o pásalas con --bank.")
    stale = {k: (owner[k], v) for k, v in now.items() if v is not None and owner[k] != v}
    if stale or None in owner.values():
        sys.exit(f"No decido: la tabla no se simuló con tus decisiones vigentes (tabla, config): {stale}; "
                 f"sin dar: {[k for k, v in owner.items() if v is None]}. Vuelve a correr funded.sim.run.")
    return cfgs[0]


def _risk(row: dict) -> str:
    """Risk per phase as «f1/f2/f3 → fondeada», % of the initial balance."""
    phases = "/".join(f"{100 * row[f'risk_phase{i}']:g}" for i in (1, 2, 3) if row[f"risk_phase{i}"] == row[f"risk_phase{i}"]
                      and row[f"risk_phase{i}"] is not None)
    return f"{phases} → {100 * row['risk_funded']:g}"


def lines(result: dict, owner: dict) -> list[str]:
    """The table of every row judged: its gain, its cost, its place at each haircut, and whether it may be bought."""
    hs = owner["haircuts"]
    out = [f"{'plan':27} {'recompra':9} {'precio$':>8} {'riesgo % f→fond':>17} {'VE ± e.t. $':>14} {'mono':>7} "
           f"{'ventaja':>7} {'P cobro':>7} {'cuotas$':>7} {'desemb. p90':>11} {'puesto h=' + '/'.join(f'{h:g}' for h in hs):>26}  ¿se puede comprar?"]
    for r in result["rows"]:
        place = "/".join(str(r[f"rank_h{round(100 * h)}"]) for h in hs)
        out.append(f"{r['plan']:27} {r['rebuy']:9} {r['price_usd']:8.2f} {_risk(r):>17} "
                   f"{'%+.1f ± %.1f' % (r['ev'], r['ev_se']):>14} {r['ev_monkey']:7.1f} {r['advantage']:7.1f} "
                   f"{r['p_first_payout']:7.0%} {r['fees']:7.1f} {r['outlay_p90']:11.0f} {place:>26}  "
                   f"{'SÍ' if r['reason'] is None else 'no: ' + r['reason']}")
    return out


def sentence(result: dict, owner: dict) -> str:
    """The decision: what to buy with its cost next to its gain, or that nothing is to be bought and why."""
    best, h = result["chosen"], owner["haircut_decides"]
    if best is None:
        own = [r for r in result["rows"] if r["is_own"]] or result["rows"]
        near = own[0]
        why = ("el valor esperado no supera al mono" if all("mono" in r["reason"] for r in own)
               else "ningún plan pasa todos los filtros")
        return (f"DECISIÓN: ninguno — {why}. El más cercano, {near['plan']} con recompra «{near['rebuy']}»: "
                f"costaría {near['fees']:.0f} $ de cuotas esperadas por un VE_banco de {near['ev']:+.1f} ± "
                f"{near['ev_se']:.1f} $ con h = {h:.0%} (mono {near['ev_monkey']:+.1f} $); no se compra porque "
                f"{near['reason']}.")
    live = ("cualquier fracción" if best["breakeven_h"] is None or best["breakeven_h"] != best["breakeven_h"]
            else f"al menos el {1 - best['breakeven_h']:.0%}")
    tie = (f" OJO: el segundo ({result['runner_up']['plan']}, «{result['runner_up']['rebuy']}», "
           f"{result['runner_up']['ev']:+.1f} $) está dentro del error de Monte Carlo: entre los dos la simulación "
           f"no distingue." if result["tie"] else "")
    return (f"DECISIÓN: compra {best['plan']} a precio de lista ({best['price_usd']:.2f} $), recompra "
            f"«{best['rebuy']}», con la cartera {', '.join(m[:8] for m in best['members'])}, riesgo {_risk(best)} % "
            f"por operación (fases → fondeada). CUESTA {best['fees']:.0f} $ de cuotas esperadas (p90 del desembolso "
            f"antes del primer cobro {best['outlay_p90']:.0f} $ de una caja de {best['budget_usd']:.0f} $). GANA un "
            f"VE_banco de {best['ev']:+.1f} ± {best['ev_se']:.1f} $ con h = {h:.0%} ({best['ev_per_month']:+.1f} $/mes), "
            f"{best['advantage']:+.1f} $ sobre el mono, P(primer cobro) {best['p_first_payout']:.0%}; sigue positivo "
            f"con {live} del edge fuera de muestra.{tie}")


def main() -> None:
    """Read the tables, refuse a mix, judge, print, write the decision."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--bank", type=Path, action="append",
                        help="a funded.sim.run folder; repeat it. Default: every run under AlgoData/portfolio/bank")
    parser.add_argument("--ignore-verdict", action="store_true",
                        help="prueba de cableado: no exige el veredicto favorable de la cartera (sale AJUSTADO)")
    parser.add_argument("--out", type=Path, help="the decision .json (default AlgoData/portfolio/bank/decisions/…)")
    args = parser.parse_args()
    found = sorted((tables.read(f) for f in args.bank), key=lambda t: t["folder"].name, reverse=True) \
        if args.bank else tables.runs()
    if not found:
        sys.exit("No decido: no hay ninguna tabla de caja sobre caminos reales. Primero "
                 "portfolio.funded.sim.frompool y portfolio.funded.sim.run.")
    per_plan = tables.per_plan(found)
    used = list({id(e["table"]): e["table"] for e in per_plan.values()}.values())
    owner = consistent(used)["owner"]
    result = choose.decide(per_plan, owner, args.ignore_verdict)
    relaxed = [t["folder"].name for t in used if t["manifest"]["paths"]["synthetic"]
               or (t["manifest"]["paths"].get("source") or {}).get("relaxed")]
    print(f"Decisión de fondeo (encargo 33 §3.5) — h = {owner['haircut_decides']:.0%} · caja "
          f"{owner['budget_eur']:g} € a {owner['eurusd']:g} $/€ · precios de lista · recompra comparada: "
          f"{', '.join(owner['rebuy'])}")
    if args.ignore_verdict or relaxed:
        print(f"AJUSTADO: {'veredicto de la cartera ignorado; ' if args.ignore_verdict else ''}"
              f"{'caminos sintéticos o de una corrida con umbrales relajados; ' if relaxed else ''}no es un resultado")
    print(f"Con los valores que diste: colchón {owner['payout_cushion']:.0%}, impuestos {owner['tax_rate']:.0%}, "
          f"comisión de cobro {owner['payout_fee']:.0%}, cobro denegado {owner['p_payout_denied']:.0%}, cierre de la "
          f"empresa {owner['p_firm_closes_year']:.0%}/año")
    print("Tablas: " + "; ".join(f"{t['folder'].name} ({t['manifest']['n_paths']} × {t['manifest']['horizon']} días)"
                                 for t in used) + "\n")
    print("\n".join(lines(result, owner)))
    text = sentence(result, owner)
    print(f"\n{text}\n\nVE en $ por banco sobre el horizonte, a h = {owner['haircut_decides']:.0%}; e.t. = error típico "
          f"de Monte Carlo. El riesgo de cada fila es el mejor de la rejilla: un máximo de medias con ruido, sesgado "
          f"al alza.\n\nLecturas abiertas, tuyas (no las he decidido):")
    print("\n".join(f"  - {line}" for line in OPEN))
    out = args.out or portfolio_dir() / "bank" / "decisions" / f"{datetime.now():%Y%m%d_%H%M%S}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "decided": datetime.now().isoformat("T", "seconds"), "sentence": text, "owner": owner,
        "adjusted": bool(args.ignore_verdict or relaxed), "ignore_verdict": args.ignore_verdict,
        "tables": [str(t["folder"]) for t in used], "chosen": result["chosen"], "runner_up": result["runner_up"],
        "tie": result["tie"], "rows": result["rows"], "open": list(OPEN)}, ensure_ascii=False, default=str, indent=1),
        encoding="utf-8")
    print(f"\nDecisión escrita en {out}")


if __name__ == "__main__":
    main()
