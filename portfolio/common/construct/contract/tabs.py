"""The portfolio run as the contract's blocks (PLAN §5.6): Veredicto, Universo, Parejas, Búsqueda, Cartera."""

from typing import Any

import numpy as np
import pandas as pd

from core.study import blocks
from core.study import result as envelope

from .. import segment
from ..equity import matrix
from . import words

MONTHS = (
    "ene",
    "feb",
    "mar",
    "abr",
    "may",
    "jun",
    "jul",
    "ago",
    "sep",
    "oct",
    "nov",
    "dic",
)


def _verdict_tab(v: dict) -> list[dict]:
    """The oos1 null with the chosen one marked, its metrics, and the oos2 reading when there is one."""
    first, second = v["oos1"], v["oos2"]
    if first["state"] == "no_discrimina":
        out = [
            {
                "kind": "callout",
                "state": "watch",
                "text": words.NO_NULL.format(
                    n=first["n_space"], k=first["k"], share=first["share_chosen"]
                ),
            }
        ]
    else:
        out = [
            blocks.distribution(
                "Puntuación por rangos en oos1: el azar y la cartera elegida",
                "",
                first["scores"],
                first["value"],
                words.NULL.format(q=first["quantile"]),
                sign_shade=False,
            )
        ]
    shown = {**first["metrics"], "sharpe": first["sharpe"]}
    out.append(
        blocks.table(
            "La cartera elegida en oos1",
            pd.DataFrame({"métrica": list(shown), "valor": list(shown.values())}),
            words.METRICS,
        )
    )
    if second["state"] in ("pass", "fail"):
        keys = ("sharpe", "benchmark", "excess", "dsr", "n", "sigma", "n_days")
        out.append(
            blocks.table(
                "La lectura de oos2",
                pd.DataFrame({"cifra": list(keys), "valor": [second[k] for k in keys]}),
                words.OOS2,
            )
        )
    return out


def _universe_tab(inputs: dict) -> list[dict]:
    """Every usable member with its floor risk and its days per segment; who was left out."""
    r = inputs["result"]
    days = {
        s: matrix.segment(r["daily"], r["calendar"], s).notna().sum()
        for s in r["calendar"]
    }
    frame = pd.DataFrame(
        [
            {
                "estrategia": i[:12],
                "símbolo": r["members_meta"][i]["symbol"],
                "marco": r["members_meta"][i]["timeframe"],
                "riesgo mínimo (%)": 100 * r["floor"][i],
                "en la cartera": "sí" if i in inputs["members"] else "no",
                **{f"días {s}": int(days[s][i]) for s in days},
            }
            for i in r["identities"]
        ]
    )
    out = [blocks.table("Miembros utilizables", frame, words.MEMBERS)]
    if r["excluded"]:
        out.append(
            blocks.table(
                "Excluidas",
                pd.DataFrame(
                    [{"estrategia": i[:12], "motivo": why} for i, why in r["excluded"]]
                ),
            )
        )
    return out


def _pairs_tab(inputs: dict, v: dict) -> list[dict]:
    """Which filter rejects how many pairs on build, and the chosen pairs out of sample."""
    graph, held = inputs["result"]["graph"], v["hold"]
    out = [
        {
            "kind": "bars",
            "title": f"Parejas rechazadas por filtro en build "
            f"({graph['n_admissible_pairs']} admisibles de {graph['n_pairs']})",
            "unit": "parejas",
            "reference": None,
            "note": words.FAILING,
            "items": [
                {"label": str(name), "value": int(n), "error": None, "state": "info"}
                for name, n in dict(graph["counts"]).items()
            ],
        }
    ]
    over = pd.DataFrame(
        held["over"], columns=pd.Index(["i", "j", "measure", "value", "threshold"])
    )
    over[["i", "j"]] = over[["i", "j"]].apply(lambda c: c.str[:12])
    out.append(
        blocks.table(
            f"Parejas de la cartera sobre algún umbral: {held['n_pairs_over']} de {held['n_pairs']}",
            over,
            words.HOLD.format(segments="+".join(v["cost"]["segments"])),
        )
    )
    return out


def _search_tab(inputs: dict) -> list[dict]:
    """The funnel in counts and every evaluated combination's build score, the chosen one marked."""
    r, table = inputs["result"], inputs["table"]
    chosen = table.loc[table["members"] == "+".join(inputs["members"]), "score"]
    funnel = pd.DataFrame(
        {
            "paso": [
                "miembros en el universo",
                "utilizables (stop y lote mínimo)",
                "con alguna pareja admisible",
                "combinaciones evaluadas en build",
                "miembros de la cartera elegida",
            ],
            "cuántas": [
                len(r["kept"]),
                len(r["identities"]),
                r["graph"]["n_out"],
                len(table),
                len(inputs["members"]),
            ],
        }
    )
    return [
        blocks.table("El embudo", funnel, words.FUNNEL),
        blocks.distribution(
            "Puntuación en build de cada combinación evaluada",
            "",
            table["score"].to_numpy(),
            float(chosen.iloc[0]) if len(chosen) else None,
            words.SCORES,
            sign_shade=False,
        ),
    ]


def _portfolio_tab(inputs: dict, v: dict, cfg: dict) -> list[dict]:
    """The chosen portfolio's cumulative P&L per segment opened, and its members."""
    r = inputs["result"]
    mask = np.isin(r["identities"], inputs["members"])[None, :]
    segments = ["build"] + v["cost"]["segments"]
    parts = {
        s: segment.paths(r["daily"], r["calendar"], r["scale"], mask, cfg, s)
        for s in segments
    }
    x = [str(d.date()) for s in segments for d in parts[s][1]]
    series, before = [], 0
    for s in segments:
        path = np.cumsum(parts[s][0][0])
        values = (
            [None] * before + path.tolist() + [None] * (len(x) - before - len(path))
        )
        series.append(
            {"label": s, "values": values, "role": "real" if s == "build" else "sim"}
        )
        before += len(path)
    held = segment.held(r["daily"], r["calendar"], r["scale"], mask, cfg)[0]
    for k in np.flatnonzero(
        mask[0]
    ):  # each member's own share of that path: same unit, same weights
        alone = (np.arange(mask.shape[1]) == k)[None, :]
        shares = [
            held[k]
            * np.cumsum(
                segment.paths(r["daily"], r["calendar"], r["scale"], alone, cfg, s)[0][
                    0
                ]
            )
            for s in segments
        ]
        values = [
            v for share in shares for v in [None, *share[1:].tolist()]
        ]  # None: the line breaks where a segment restarts
        series.append(
            {
                "label": r["identities"][k][:8],
                "values": [shares[0][0], *values[1:]],
                "role": "reference",
            }
        )
    days = pd.DatetimeIndex([d for s in segments for d in parts[s][1]])
    months = (
        pd.Series(np.concatenate([parts[s][0][0] for s in segments]), index=days)
        .groupby([days.year, days.month])  # pyright: ignore[reportAttributeAccessIssue]  # stub lacks DatetimeIndex.year/.month
        .sum()
        .unstack()
    )
    monthly = pd.DataFrame(
        {
            "año": months.index,
            **{MONTHS[m - 1]: months[m].round(2) for m in months.columns},
            "total": months.sum(axis=1).round(2),
        }
    )
    members = pd.DataFrame(
        [
            {
                "estrategia": i[:12],
                "símbolo": r["members_meta"][i]["symbol"],
                "peso": 1 / len(inputs["members"])
                if cfg["weights"]["method"] == "equal"
                else None,
                "riesgo mínimo (%)": 100 * r["floor"][i],
            }
            for i in inputs["members"]
        ]
    )
    return [
        {
            "kind": "lines",
            "title": "P&L acumulado de la cartera elegida, por tramo",
            "unit": "R",
            "x": x,
            "series": series,
            "note": words.EQUITY.format(segments=", ".join(segments)),
        },
        blocks.table(
            "Miembros de la cartera",
            members,
            f"Pesos del método «{cfg['weights']['method']}», fijados en build.",
        ),
        blocks.table(
            "P&L de la cartera por mes",
            monthly,
            words.MONTHLY.format(segments=", ".join(segments)),
        ),
    ]


def population(
    inputs: dict, v: dict, sentence: str, cfg: dict, started: float
) -> dict[str, Any]:
    """The contract dict of one portfolio run.

    Args:
        inputs: `report.load()`'s dict.
        v: `many.judge()`'s verdict.
        sentence: Its Spanish decision sentence.
        cfg: The construct config.
        started: `time.time()` when the run began.

    Returns:
        `core.study.result.envelope`'s validated result, five tabs, the verdict block on top.
    """
    judged = "oos1" in v
    tabs = [
        envelope.tab("universo", words.TABS["universo"], _universe_tab(inputs)),
        envelope.tab("busqueda", words.TABS["busqueda"], _search_tab(inputs)),
    ]
    if judged:
        tabs = [
            envelope.tab("veredicto", words.TABS["veredicto"], _verdict_tab(v)),
            tabs[0],
            envelope.tab("parejas", words.TABS["parejas"], _pairs_tab(inputs, v)),
            tabs[1],
            envelope.tab(
                "cartera", words.TABS["cartera"], _portfolio_tab(inputs, v, cfg)
            ),
        ]
    warnings = [
        {
            "code": "relaxed",
            "state": "watch",
            "text": f"AJUSTADO: umbrales relajados {cfg['relaxed']} — no es un resultado",
        }
    ] * bool(cfg["relaxed"])
    return envelope.envelope(
        words.MODULE,
        None,
        None,
        cfg,
        started,
        tabs,
        blocks.verdict(v["label"], words.STATE[v["pass"]], sentence),
        warnings,
        summary={"pass": v["pass"], "label": v["label"], "k": len(inputs["members"])},
    )
