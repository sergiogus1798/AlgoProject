"""Step 18.5 as the contract's blocks: the call, the joint rho against its null, the markets, the premium, the power."""

from typing import Any
import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.optimisation.marketSurfaces.contract import words as w

WINDOW = {
    "principal": "build+oos1 en los otros mercados",
    "oos2": "oos2 en los otros mercados",
}


def es(value: float | None, pattern: str = "{:.2f}") -> str:
    """A number inside a sentence, decimal comma; «sin dato» when there is none."""
    return (
        "sin dato"
        if value is None or not np.isfinite(value)
        else pattern.format(value).replace(".", ",")
    )


def verdict(facts: dict, state: str, main: str, cfg: dict) -> dict[str, Any]:
    """The step's state, its label and the sentence of each reading that made it."""
    order, premium = facts["orden"], facts["prima"]
    said = order.get("estado", "sin_dato")
    meaning = w.MEANING[said].format(
        main=main,
        p_mas=es(order["p_mas"], "{:.3f}"),
        p_menos=es(order["p_menos"], "{:.3f}"),
        peso=es(order["mercados"]),
        need=es(cfg["markets"]["min_weight"], "{:g}"),
    )
    parts = [
        {
            "label": "Orden conjunto (decide)",
            "value": order["rho"],
            "note": w.ORDER[said],
            "state": {"perverso": "fail", "sin_dato": "watch"}.get(said, "pass"),
        }
    ]
    low = premium.get("bajo_p5")
    if low:
        meaning += w.LOW.format(
            share=es(100 * cfg["premium"]["top_share"], "{:g}"),
            main=main,
            pi=es(premium["valor"]),
            cut=es(premium["nulo_p5"]),
            pct=es(cfg["premium"]["percentile"], "{:g}"),
        )
    parts.append(
        {
            "label": "Prima del top (neto)",
            "value": premium["valor"],
            "state": "none" if low is None else "watch" if low else "pass",
            "note": f"corte del nulo {es(premium['nulo_p5'])}",
        }
    )
    if "oos2" in facts:
        bad = facts["oos2"].get("perverso", 0)
        blind = facts["oos2"]["sin_dato"]
        meaning += w.LATER.format(p_menos=es(facts["oos2"]["p_menos"], "{:.3f}")) * bad
        parts.append(
            {
                "label": "Orden en oos2",
                "value": facts["oos2"]["rho"],
                "state": "watch" if bad or blind else "pass",
                "note": f"p− {es(facts['oos2']['p_menos'], '{:.3f}')}",
            }
        )
    return blocks.verdict(
        w.LABEL[state, state == "pass" and said == "positivo"],
        state,
        meaning,
        f"ρ {es(order['rho'])}",
        parts,
    )


def joint(found: dict, title: str, note: str) -> list[dict]:
    """The joint rho marked on its null; nothing when no market entered the mean."""
    if not len(found["nulo"]):
        return []
    return [
        blocks.distribution(
            title,
            "",
            found["nulo"],
            found["orden"]["rho"],
            note,
            p=found["orden"]["p_mas"],
            sign_shade=False,
        )
    ]


def per_market(found: dict, cfg: dict) -> dict[str, Any]:
    """One row per declared market: its rho, its tails, its common set, its weight. Decides nothing."""
    m = found["mercados"]
    frame = pd.DataFrame(
        {
            "Mercado": m["feed"],
            "Categoría": m["category"].map(lambda c: w.CATEGORY.get(c, c)),
            "ρ": m["rho"],
            "p+": m["p_mas"],
            "p−": m["p_menos"],
            "Variantes comunes": m["n"],
            "Empates (%)": 100 * m["ties"],
            "Peso": m["weight"],
            "Prima π": m["prima"],
            "Madre (%)": m["madre"],
            "Entra": np.where(m["included"], "sí", "no"),
        }
    )
    note = w.MARKETS_NOTE.format(
        common=cfg["markets"]["min_common"],
        ties=es(100 * cfg["markets"]["max_ties"], "{:g}"),
    )
    return blocks.table(w.MARKETS_TITLE, frame, note, digits=3) | {
        "compact": True,
        "help": [w.MARKETS[c] for c in frame.columns],
    }


def categories(found: dict) -> dict[str, Any]:
    """The joint rho of each category of `_markets.yaml` on its own."""
    rows = [
        [
            w.CATEGORY.get(c, c),
            got["rho"],
            got["p_mas"],
            got["p_menos"],
            got["peso"],
            got["mercados"],
        ]
        for c, got in found["categorias"].items()
    ]
    frame = pd.DataFrame(
        rows,
        columns=pd.Index(["Categoría", "ρ conjunta", "p+", "p−", "Peso", "Mercados"]),
    )
    return blocks.table(
        w.CATEGORIES_TITLE,
        frame.astype({"ρ conjunta": float, "p+": float, "p−": float}),
        w.CATEGORIES_NOTE,
        digits=3,
    ) | {"compact": True, "help": w.CATEGORIES}


def order(found: dict, name: str, main: str, lede: str, cfg: dict) -> dict[str, Any]:
    """One reading's tab: the joint rho on its null, the markets, the categories."""
    note = w.JOINT_NOTE.format(main=main, draws=cfg["null"]["draws"])
    return envelope.tab(
        name,
        f"El orden en otros mercados — {WINDOW[name]}",
        [
            *joint(found, w.JOINT_TITLE.format(window=WINDOW[name]), note),
            per_market(found, cfg),
            categories(found),
        ],
        note=lede,
    )


def premium(found: dict, main: str, cfg: dict) -> dict[str, Any]:
    """The premium tab: the joint premium marked on its own null."""
    share, pct = (
        es(v, "{:g}")
        for v in (100 * cfg["premium"]["top_share"], cfg["premium"]["percentile"])
    )
    note = w.PREMIUM_NOTE.format(
        share=share, main=main, pct=pct, cut=es(found["prima"]["nulo_p"])
    )
    draws = found["prima_nulo"]
    shown = (
        [
            blocks.distribution(
                w.PREMIUM_TITLE.format(share=share),
                "RIC",
                draws,
                found["prima"]["valor"],
                note,
            )
        ]
        if np.isfinite(draws).any()
        else []
    )
    return envelope.tab(
        "prima", f"La prima del {share} % mejor, en dinero", shown, note=note
    )


def reference(facts: dict, main: str, cfg: dict) -> dict[str, Any]:
    """The reference tab: the main market against itself, and the power curve."""
    auto, alpha = facts["auto"], cfg["null"]["alpha"]
    frame = pd.DataFrame(
        [[auto["rho"], facts["orden"]["rho"], auto.get("cociente")]],
        columns=pd.Index(
            ["ρ propia (build → oos1)", "ρ conjunta entre mercados", "Cociente"]
        ),
    ).astype(float)
    table = blocks.table(
        w.REFERENCE_TITLE.format(main=main),
        frame,
        w.REFERENCE_NOTE.format(
            main=main, floor=es(cfg["reference"]["min_rho"], "{:g}")
        ),
        digits=3,
    ) | {"compact": True, "help": w.REFERENCE}
    bars = {
        "kind": "bars",
        "title": w.POWER_TITLE,
        "unit": "%",
        "reference": 100 * alpha,
        "note": w.POWER_NOTE.format(
            draws=cfg["power"]["draws"], main=main, alpha=es(alpha, "{:g}")
        ),
        "items": [
            {
                "label": f"ρ verdadera {es(int(k[1:]) / 10, '{:.1f}')}",
                "value": 100 * v,
                "error": None,
                "state": "info",
            }
            for k, v in facts["potencia"].items()
        ],
    }
    return envelope.tab("referencia", "Referencia y potencia", [table, bars])


def tabs(measured: dict, facts: dict, main: str, cfg: dict) -> list[dict]:
    """The tabs of the small result: the deciding order, the premium, the reference, and oos2 when read."""
    m = measured["principal"]["mercados"]
    cats = ", ".join(
        f"{n} {w.CATEGORY.get(c, c)}"
        for c, n in m["category"].value_counts(sort=False).items()
    )
    lede = {
        k: w.TAB_NOTE.format(main=main, n=len(m), cats=cats, window=WINDOW[k])
        for k in WINDOW
    }
    return [
        order(measured["principal"], "principal", main, lede["principal"], cfg),
        premium(measured["principal"], main, cfg),
        reference(facts, main, cfg),
        *(
            [order(measured["oos2"], "oos2", main, lede["oos2"], cfg)]
            if measured["oos2"]
            else []
        ),
    ]


def warnings(
    measured: dict, facts: dict, provisional: list[str], cfg: dict
) -> list[dict]:
    """What colours the result without changing its state."""
    m, out = measured["principal"]["mercados"], []
    absent = list(m.loc[m["n"] == 0, "feed"])
    left = [
        f"{r.feed} ({r.n} comunes, {es(100 * r.ties, '{:.0f}')} % empates)"
        for r in m.itertuples()
        if not r.included and r.n
    ]
    off = [k for k, v in measured["gaps"].items() if v > cfg["costs"]["max_share"]]
    for code, state, text, names in (
        ("costs_provisional", "watch", w.COSTS, provisional),
        ("market_absent", "watch", w.ABSENT, absent),
        ("market_out", "info", w.OUT, left),
        ("cost_gap", "watch", w.GAP, off),
    ):
        if names:
            out.append(
                {
                    "code": code,
                    "state": state,
                    "text": text.format(
                        markets=", ".join(names),
                        share=es(100 * cfg["costs"]["max_share"], "{:g}"),
                    ),
                }
            )
    if measured["dos_semanas"]:
        out.append(
            {
                "code": "weekend_straddle",
                "state": "watch",
                "text": w.STRADDLE.format(
                    share=es(100 * measured["straddle"], "{:.1f}"),
                    limit=es(100 * cfg["null"]["straddle_max"], "{:g}"),
                    again=w.ORDER[facts["orden"].get("estado_2sem", "sin_dato")],
                ),
            }
        )
    return out
