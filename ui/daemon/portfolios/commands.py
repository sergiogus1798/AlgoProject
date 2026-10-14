"""What each «Calcular» of the zone launches: its command, what it still lacks, and the sentence to confirm."""

import re
from typing import Any

from portfolio.common.construct.inputs import config
from portfolio.funded.sim import inputs as bank_inputs, table as bank_table
from ui.daemon import jobs
from ui.daemon.portfolios import bankjob, construct, shelf

LABEL = "portfolio"
SEED = 0  # the same in the preflight and the launch (the nonce binds argv); each run records it
SET = re.compile(r"^[a-z_0-9]+(\.[a-z_0-9]+)+=\S+$")
TITLES = {
    "universe": "Universo y parejas",
    "real": "Búsqueda de la cartera",
    "verdict": "Veredicto de la cartera",
    "stage_a": "Fondeo · etapa A",
    "stage_b": "Fondeo · etapa B y veredicto",
    "weights": "Walk-forward de pesos",
    "bank": "La caja del fondeo",
}
# The construct knobs each action refuses without (rule 11): never defaulted here either.
NEEDS = {
    "stage_a": [("funded", "open_risk_cap")],
    "stage_b": [("funded", "open_risk_cap"), ("stageb", "t1_gap")],
    "weights": [("wf", "confidence")],
}
ONCE = (
    "Si la cartera pasa oos1, esto ABRE oos2 del pool «{pool}». Esa lectura es de UN SOLO USO: una vez leído, "
    "ninguna otra cartera de este pool podrá volver a leerlo, y el resultado queda escrito en el ledger."
)


def sets(text: str) -> list[str]:
    """«--set a.b=1 --set c.d=2» (or the bare pairs) as the list the commands take."""
    return [t for t in text.split() if t != "--set"]


def unknown(overrides: list[str]) -> list[str]:
    """The well-formed overrides that name no knob of the portfolio's config nor of the bank's."""

    def names(cfg: object, path: list[str]) -> bool:
        """Whether `path` leads to a key of `cfg`."""
        return not path or (
            isinstance(cfg, dict) and path[0] in cfg and names(cfg[path[0]], path[1:])
        )

    known = (
        config.load([]),
        bank_inputs.load([]),
    )  # both have a `compute`: looked up apart, not merged
    return [
        s
        for s in overrides
        if not any(names(cfg, s.split("=", 1)[0].split(".")) for cfg in known)
    ]


def flags(overrides: list[str]) -> list[str]:
    """The overrides as argv."""
    return [x for s in overrides for x in ("--set", s)]


def plan(action: str, p: dict[str, str]) -> dict[str, Any]:
    """Whether one «Calcular» may start now.

    Args:
        action: A key of `TITLES`.
        p: `pool`, `run`, `plan`, `firm`, `horizon`, `edge_from`, `n_paths`, `sets` — strings, "" when unset.

    Returns:
        `{ok, reasons, text, confirm, argv, about}`: Spanish reasons when it may not; `confirm`
        true when the owner must say yes to `text` first (the launchers that can open oos2).
    """
    over, why, text, confirm = sets(p.get("sets", "")), [], "", False
    pool, run = p.get("pool", ""), p.get("run", "")
    if action not in TITLES:
        return {"ok": False, "reasons": [f"acción desconocida: {action}"]}
    if over and not shelf.test_root():
        why.append(
            "los ajustes --set solo se admiten en la raíz de prueba: en la real los umbrales son los del ledger"
        )
    why += [
        f"ajuste mal escrito: «{s}» (se espera sección.clave=valor)"
        for s in over
        if not SET.match(s)
    ]
    why += [
        f"ajuste desconocido: «{s}» (esa sección.clave no existe en la configuración)"
        for s in unknown([s for s in over if SET.match(s)])
    ]
    if any(j["label"] == LABEL and j["rc"] is None for j in jobs.listing()):
        why.append(
            "ya hay un cálculo de carteras en marcha o en cola: espera a que acabe"
        )
    if why:
        return {"ok": False, "reasons": why}
    row = next((r for r in shelf.runs() if r["id"] == run), None)
    wants = {
        "verdict": "real",
        "weights": "real",
        "stage_b": "funded",
        "bank": "funded",
    }.get(action)
    if wants and (row is None or row["kind"] != wants):
        why.append(
            "elige abajo, en «Carteras», una run "
            + ("del camino real" if wants == "real" else "de fondeo")
        )
    elif wants and row is not None:
        pool = row["pool"]
    if not pool:
        why.append(
            "elige un pool (abajo, en «Carteras», o declara uno desde «Estrategias»)"
        )
    if action == "stage_a" and not p.get("plan"):
        why.append("elige el plan de la empresa")
    if why:
        return {"ok": False, "reasons": why}
    firm = flags([]) + (["--firm", p["firm"]] if p.get("firm") else [])
    folder = str(shelf.folder("runs", run)) if wants else ""
    if action == "bank":
        assert (
            row is not None
        )  # `wants` is set for the bank: a missing run returned above
        why += lacks_bank(p, over, row)
        argv = [
            "-m",
            "ui.daemon.portfolios.bankjob",
            "--run",
            folder,
            "--horizon",
            p.get("horizon", ""),
            "--n-paths",
            p.get("n_paths", ""),
            "--edge-from",
            p.get("edge_from", ""),
            *flags(over),
        ]
    else:
        over = [
            s for s in over if s.split(".")[0] not in bankjob.BANK_SECTIONS
        ]  # the bank's own are not these commands'
        cfg = config.load(over)
        why += [
            f"falta {s}.{k}: decisión tuya — sin ella la orden se niega"
            for s, k in NEEDS.get(action, [])
            if cfg[s][k] is None
        ]
        module = {
            "universe": "universe",
            "real": "real",
            "verdict": "report",
            "stage_a": "funded",
            "stage_b": "funded_b",
            "weights": "wf",
        }[action]
        argv = (
            ["-m", f"portfolio.common.construct.{module}"]
            + {
                "universe": ["--pool", pool, *firm],
                "real": ["--pool", pool, *firm],
                "verdict": ["--pool", pool, "--run", folder, *firm],
                "weights": ["--pool", pool, "--run", folder, *firm],
                "stage_a": ["--pool", pool, "--plan", p.get("plan", ""), *firm],
                "stage_b": ["--run", folder],
            }[action]
            + flags(over)
        )
        if action != "universe":
            argv += ["--seed", str(SEED)]
        if action in ("verdict", "stage_b"):
            assert (
                row is not None
            )  # `wants` is set for both: a missing run returned above
            confirm, text = True, confirmation(action, pool, row, cfg)
    return {
        "ok": not why,
        "reasons": why,
        "text": text,
        "confirm": confirm,
        "argv": argv,
        "about": {
            "project": pool,
            "databank": run or p.get("plan", "") or "pool",
            "strategy": "",
            "study": TITLES[action],
        },
    }


def lacks_bank(p: dict[str, str], over: list[str], row: shelf.RunRow) -> list[str]:
    """What «Calcular la caja» still lacks: the run's verdict, the horizon, the edge's segments, the owner's inputs."""
    why = (
        []
        if row["stage_b"]
        else ["esta run no tiene etapa B ni veredicto: la cartera fondeada sale de ahí"]
    )
    if not p.get("horizon", "").isdigit():
        why.append("falta el horizonte (días que se simula la caja): decisión tuya")
    if not p.get("edge_from"):
        why.append(
            "faltan los tramos del edge (oos1, u oos1,oos2 si el veredicto lo abrió): decisión tuya"
        )
    if not p.get("n_paths", "").isdigit():
        why.append("falta el número de caminos")
    cfg = bank_inputs.load(
        [s for s in over if s.split(".")[0] in bankjob.BANK_SECTIONS]
    )
    return why + [
        f"falta {line}"
        for line in bank_inputs.refuse(cfg) + bank_table.variants(cfg)[1]
    ]


def confirmation(action: str, pool: str, row: shelf.RunRow, cfg: dict[str, Any]) -> str:
    """The sentence the owner reads before a launcher that can open oos2."""
    who = f"la cartera de la run «{row['id']}» (K = {row['k']}) del pool «{pool}»"
    once = construct.spent(pool, row["members"]) or ONCE.format(pool=pool)
    if action == "verdict":
        return f"Vas a JUZGAR {who}.\n\n{once}\n\n¿Lanzar el veredicto?"
    blind = (
        ""
        if cfg["verdict"]["pass_percentile"] is not None
        else "\n\nFalta verdict.pass_percentile (decisión tuya): el veredicto saldrá «sin criterio» y oos2 NO se abrirá."
    )
    again = (
        " Esta run ya tiene etapa B: la nueva se escribe en una run aparte y la anterior no se toca."
        if row["stage_b"]
        else ""
    )
    return (
        f"Vas a correr la ETAPA B y el veredicto de fondeo de {who}, plan {row['plan']}.\n\nUsa todos los "
        f"núcleos durante minutos.{again}\n\n{once}{blind}\n\n¿Lanzar la etapa B?"
    )
