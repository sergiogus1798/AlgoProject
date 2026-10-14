"""«Fondeo»: one funded run — stage A's P(pass) per combination and risk, stage B's three Monte Carlos, its verdict."""

from typing import Any, cast

import pandas as pd

from portfolio.common.construct.inputs import config
from portfolio.funded.rules import catalog
from portfolio.funded.sim import inputs as bank_inputs
from ui.daemon.portfolios import construct, parts, shelf

MAX_ROWS = 300
# The knobs the funded commands refuse without (rule 11), and what each one blocks.
KNOBS = (
    (
        "funded",
        "open_risk_cap",
        "la etapa A y la B: qué fracción de la pérdida diaria máxima del plan "
        "puede estar en riesgo a la vez",
    ),
    ("stageb", "t1_gap", "la etapa B: el modelo de huecos del Monte Carlo T1"),
    (
        "verdict",
        "pass_percentile",
        "el veredicto: sin él sale «sin criterio» y oos2 no se abre",
    ),
)
NO_B = (
    "La etapa B no ha corrido sobre esta run: solo hay la P(pasar) de la etapa A, que es una "
    "criba rápida. «Etapa B y veredicto» la mide con los tres Monte Carlo y la juzga."
)


def plans() -> list[str]:
    """The catalogue's plans the funded searches may be asked for, by firm, family and size."""
    universe = bank_inputs.load([])["universe"]
    return catalog.plans(universe["max_size"], universe["ccy"])


def missing(cfg: dict[str, Any] | None = None) -> list[str]:
    """«Falta <knob>: decisión tuya — <what it blocks>», one per unanswered knob."""
    cfg = cfg or config.load([])
    return [
        f"Falta {s}.{k}: decisión tuya — bloquea {what}."
        for s, k, what in KNOBS
        if cfg[s][k] is None
    ]


def read(pool: str = "", plan: str = "", run: str = "", **_: str) -> dict[str, Any]:
    """The tabs of the pool's newest funded run of one plan: Etapa A, Etapa B, Veredicto."""
    base = {"plans": plans(), "missing": missing()}
    if not pool:
        return (
            parts.empty(
                "No hay ningún pool declarado.",
                "marca estrategias abajo y declara uno.",
            )
            | base
        )
    found = [
        r
        for r in shelf.runs()
        if r["pool"] == pool
        and r["kind"] == "funded"
        and (not plan or r["plan"] == plan)
    ]
    found.sort(
        key=lambda r: r["stage_b"], reverse=True
    )  # stable: the newest with a stage B first
    row = next((r for r in found if r["id"] == run), found[0] if found else None)
    if row is None:
        return (
            parts.empty(
                f"El pool «{pool}» no tiene búsqueda de fondeo"
                + (f" para {plan}." if plan else "."),
                "elige el plan arriba y pulsa «Calcular etapa A».",
            )
            | base
        )
    folder, known = shelf.folder("runs", row["id"]), shelf.names()
    m = shelf.load(folder / "manifest.json")
    return base | {
        "run": row["id"],
        "plan": m["plan"],
        "relaxed": parts.relaxed(m.get("relaxed")),
        "empty": None,
        "stage_b": row["stage_b"],
        "spent": construct.spent(pool),
        "tabs": [stage_a(folder, m, known), stage_b(folder, known), verdict(folder)],
    }


def members(joined: str, known: dict[str, dict] | None = None) -> str:
    """A `+`-joined combination as the table prints it."""
    return " + ".join(
        shelf.label(i, known) if known else shelf.short(i) for i in joined.split("+")
    )


def stage_a(
    folder: shelf.Path, m: dict[str, Any], known: dict[str, dict]
) -> parts.TabBlock:
    """«Etapa A»: P(pass) on build's own days, per combination and risk per trade."""
    frame = (
        pd.read_parquet(folder / "search.parquet")
        .drop_duplicates(["members", "level"])
        .sort_values("score", ascending=False)
    )
    best, cap = frame.iloc[0], m.get("cap")
    head = (
        f"MEJOR DE LA ETAPA A — {m['plan']}: K = {len(m['best_members'])} "
        f"[{', '.join(shelf.label(i, known) for i in m['best_members'])}] · P(pasar) {m['best_score']:.1%} "
        f"arriesgando {best.level:.1%} por operación."
    )
    rows = [
        [
            n,
            members(r.members),
            len(r.members.split("+")),
            parts.pct(r.level),
            parts.pct(r.score),
        ]
        for n, r in enumerate(cast(Any, frame.head(MAX_ROWS)).itertuples(), 1)
    ]
    table = parts.table(
        "P(pasar) por combinación y riesgo",
        ["#", "miembros", "K", "riesgo %", "P(pasar) %"],
        rows,
        f"{len(frame)} parejas (combinación, riesgo) distintas de {m['n_scored']} evaluadas"
        + (
            f"; {cap['capped']} de {cap['pairs']} quedaron fuera por el tope de riesgo abierto "
            f"({m['open_risk_cap']})."
            if cap
            else "."
        ),  # a run older than the cap has no count
        [None, None, parts.WORDS["k"], parts.WORDS["risk"], parts.WORDS["p_pass"]],
        [["pass"] + [None] * 4] + [[None] * 5] * (len(rows) - 1),
    )
    return parts.tab(
        "Etapa A",
        parts.callout(head),
        table,
        note="Criba rápida: cuenta en qué parte de los días de inicio posibles de build la "
        "combinación pasa el challenge. No es todavía una probabilidad de fiar: eso es la etapa B.",
    )


def stage_b(folder: shelf.Path, known: dict[str, dict]) -> parts.TabBlock:
    """«Etapa B»: the shortlist under D, T1 and T2, and the winner's deciding figure."""
    if not (folder / "stageb.parquet").exists():
        return parts.tab("Etapa B", parts.callout(NO_B, "watch"))
    v = shelf.load(folder / "verdict.json")
    w, stable = v["winner"], v["stability"]
    head = (
        f"GANADORA DE LA ETAPA B: K = {w['k']} [{members(w['members'], known)}] · P(pasar) {w['p']:.1%} "
        f"(decide {w['flavour']}, el más pesimista) arriesgando {w['r_phase1']:.1%} por operación."
    )
    figures = parts.table(
        "La ganadora, con los tres Monte Carlo",
        ["qué", "valor", "qué es"],
        [
            ["P(pasar) · D (%)", parts.pct(w["p_D"]), parts.WORDS["D"]],
            ["P(pasar) · T1 (%)", parts.pct(w["p_T1"]), parts.WORDS["T1"]],
            ["P(pasar) · T2 (%)", parts.pct(w["p_T2"]), parts.WORDS["T2"]],
            [
                "P(pasar) repetida (%)",
                parts.pct(w["p_fresh"]),
                parts.WORDS["p_fresh"]
                + f" Aquí: {stable['runs']} repeticiones, {parts.pct(stable['spread']):.1f} puntos entre la mayor y la menor.",
            ],
            [
                "falla por pérdida máxima (%)",
                parts.pct(w["fail_max_loss"]),
                "Intentos que rompen la pérdida máxima.",
            ],
            [
                "falla por pérdida diaria (%)",
                parts.pct(w["fail_daily_loss"]),
                "Intentos que rompen la pérdida diaria.",
            ],
            [
                "sigue abierta al acabar el plazo (%)",
                parts.pct(w["p_open"]),
                "Ni pasa ni rompe nada en el horizonte.",
            ],
            [
                "días hasta pasar · mediana",
                w["t_median"],
                "La mitad de los intentos que pasan lo hace antes.",
            ],
            [
                "días hasta pasar · percentil 90",
                w["t_p90"],
                "Nueve de cada diez de los que pasan lo hacen antes.",
            ],
        ],
    )
    short = pd.read_parquet(folder / "shortlist.parquet").sort_values(
        "p", ascending=False
    )
    rows = [
        [
            members(r.members),
            r.k,
            parts.pct(r.r_phase1),
            parts.pct(r.p_D),
            parts.pct(r.p_T1),
            parts.pct(r.p_T2),
            r.flavour,
            parts.pct(r.p),
        ]
        for r in cast(Any, short).itertuples()
    ]
    table = parts.table(
        "Las finalistas",
        ["miembros", "K", "riesgo %", "D %", "T1 %", "T2 %", "decide", "P(pasar) %"],
        rows,
        "La cifra que cuenta de cada una es la del Monte Carlo más pesimista.",
        [
            None,
            parts.WORDS["k"],
            parts.WORDS["risk"],
            parts.WORDS["D"],
            parts.WORDS["T1"],
            parts.WORDS["T2"],
            "El Monte Carlo que da la cifra más baja.",
            parts.WORDS["p_pass"],
        ],
    )
    return parts.tab("Etapa B", parts.callout(head), figures, table)


def verdict(folder: shelf.Path) -> parts.TabBlock:
    """«Veredicto»: oos1 against the null searches, the oos2 line — «sin criterio» said as such."""
    if not (folder / "verdict.json").exists():
        return parts.tab("Veredicto", parts.callout(NO_B, "watch"))
    v = shelf.load(folder / "verdict.json")["verdict"]
    if not v:
        return parts.tab(
            "Veredicto",
            parts.callout("La etapa B corrió y no emitió veredicto.", "watch"),
        )
    one, two = v["oos1"], v["oos2"]
    rows = [
        [
            {"start_p": "por días de inicio", "mc_p": "Monte Carlo más pesimista"}[k]
            + (" ← decide" if k == one["measure"] else ""),
            parts.pct(x["value"]),
            parts.pct(x["null_median"]),
            parts.pct(x["null_p95"]),
            parts.pct(x["percentile"]),
            x["n"],
        ]
        for k, x in one["measures"].items()
    ]
    table = parts.table(
        "oos1: la cartera elegida contra búsquedas al azar",
        [
            "P(pasar) en oos1",
            "elegida %",
            "mediana del azar %",
            "p95 del azar %",
            "percentil %",
            "búsquedas",
        ],
        rows,
        "Cada búsqueda al azar repite la etapa A y la B sobre combinaciones admisibles al azar: "
        "es lo que saldría sin saber elegir.",
    )
    label = v["label"]
    state = "watch" if v["pass"] is None else construct.STATE[v["pass"]]
    line = parts.callout(
        f"oos2 — {construct.OOS2.get(two['state'], two['state'])}"
        + (f": {two['reason']}" if two.get("reason") else "."),
        {"pass": "pass", "fail": "fail"}.get(two["state"], "info"),
    )
    return parts.tab(
        "Veredicto", parts.callout(parts.headline(label), state), table, line
    )
