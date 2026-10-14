"""The optional second MT5 pass on real ticks: its backtest, its verdict beside the chosen model's, and the merged tab with three curves per firm."""

from typing import Any

import pandas as pd

from core.study import result as study_result
from mt5.verify import judge, mt5side, sidebyside

# Model=4, «Every tick based on real ticks»: the broker's own recorded ticks with their real
# spread. «Every tick» (Model=0) interpolates synthetic ticks from the M1 bars, so it adds time
# and no fidelity over OHLC M1 — the extra pass is always this one (owner, 2026-10-04).
MODEL = "real_ticks"
NAMES = {
    "ohlc_m1": "OHLC M1",
    "every_tick": "Every tick",
    "open_prices": "Open prices",
    MODEL: "Real ticks",
}
MARK = "\x00ticks"  # the suffix that carries a firm's second piece through `combined_chart`


def backtest(
    expert: str,
    row: dict,
    timeframe: str,
    window: tuple[str, str],
    deposit: float,
    leverage: int,
    firm: str,
    cfg: dict,
) -> pd.DataFrame:
    """The EA's trades on real ticks on one firm's account.

    Args:
        expert: The compiled EA.
        row: The firm's row of `firms.usable`: `symbol` and `account`.
        timeframe, window, deposit, leverage: As the first pass.
        firm: Firm key; the run is tagged `<firm>_ticks`.
        cfg: The `mt5` block of config.yaml; `ticks_max_minutes` replaces `max_minutes`.
    """
    study_result.progress(80, f"backtest en MT5 con Real ticks en la cuenta de {firm}")
    slow = {**cfg, "max_minutes": cfg["ticks_max_minutes"]}
    return mt5side.backtest(
        expert,
        row["symbol"],
        timeframe,
        window,
        MODEL,
        deposit,
        leverage,
        row["account"],
        f"{firm}_ticks",
        slow,
    )["trades"]


def named(piece: dict, model: str) -> list[dict]:
    """A piece's verdict and unpaired table, each saying which tester model it judged."""
    name = NAMES.get(model, model)
    verdict = {
        **piece["verdict"],
        "label": f"{piece['verdict']['label']} · {name}",
        "meaning": f"MT5 en {name}. {piece['verdict']['meaning']}",
    }
    lonely = {**piece["lonely"], "title": f"{piece['lonely']['title']} · {name}"}
    return [verdict, lonely]


def keep(pieces: dict, summaries: dict, firm: str, piece: dict, report: str) -> None:
    """File one judged pass of a firm: the first is the firm's piece, the second its `ticks`.

    Each pass is its own look at the data, judged on the same five rows. The firm's state —
    what the pool and the run's light read — stays the first pass's, the model the owner
    chose; the real-ticks figures go beside it in the summary under `ticks_`.
    """
    if firm in pieces:
        pieces[firm]["ticks"] = piece
        summaries[firm] |= {
            f"ticks_{k}": v for k, v in piece["summary"].items() if k != "firm"
        }
    else:
        pieces[firm] = piece
        summaries[firm] = {**piece["summary"], "report": report}


def chart(pieces: dict[str, dict], model: str) -> dict[str, Any]:
    """The merged P&L chart; with a real-ticks piece, three curves per firm.

    Args:
        pieces: {firm: `judge.firm_result`}, some with a second piece under `"ticks"`.
        model: The tester model of the first pass, named in its series when there are two.

    Returns:
        `judge.combined_chart`'s block: per firm SQX, MT5 at `model` and MT5 on real ticks, all
        tagged with the firm so its light hides the three.
    """
    extra = {f"{firm}{MARK}": p["ticks"] for firm, p in pieces.items() if "ticks" in p}
    block = judge.combined_chart({**pieces, **extra})
    if not extra:
        return block
    series = []
    for s in block["series"]:
        second = s["firm"].endswith(MARK)
        if second and s["role"] == "real":
            continue  # the same SQX retest, already drawn
        if s["role"] != "real":
            s = {
                **s,
                "label": s["label"].replace(
                    "MT5", f"MT5 {NAMES[MODEL if second else model]}", 1
                ),
            }
        series.append({**s, "firm": s["firm"].removesuffix(MARK)})
    return {**block, "series": series}


def tab(params: dict, pieces: dict[str, dict], model: str) -> dict[str, Any]:
    """The Verificación tab: parameters, the merged chart, the side-by-side trades, each verdict.

    Args:
        params: `judge.params_table`'s block.
        pieces: {firm: `judge.firm_result`}, some with a second piece under `"ticks"`.
        model: The first pass's tester model.
    """
    blocks = [params, chart(pieces, model), sidebyside.table(pieces)]
    for piece in pieces.values():
        both = "ticks" in piece
        blocks += named(piece, model) if both else [piece["verdict"], piece["lonely"]]
        blocks += named(piece["ticks"], MODEL) if both else []
    return {
        "name": "verificacion",
        "title": "Verificación",
        "note": "Criterios de aceptación (verde: superado, rojo: fallido) y P&L por "
        "empresa; la lucecita de cada empresa en la ventana enciende o apaga "
        "su curva y sus criterios.",
        "blocks": blocks,
    }
