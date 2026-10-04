"""One strategy against buy & hold, priced in market time, as the contract's data."""

import time

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from studies.closing.exposure import benchmark, compare, occupancy, verdict

MODULE = "studies.closing.exposure"
CONVENTIONS = {"one_lot": "un lote", "avg_size": "el tamaño medio de la estrategia",
               "equal_risk": "a igual riesgo (misma volatilidad diaria)"}
# The verdict's own word (`worth_it`/`not_worth_it`, in verdict.csv for /curate) shown to the
# reader (feedback §9.3, 2026-09-30): "Aprobado" (verde) / "Suspenso" (rojo).
LABEL = {"worth_it": "Aprobado", "not_worth_it": "Suspenso"}
SHORT = {"one_lot": "un lote", "avg_size": "tamaño medio", "equal_risk": "a igual riesgo"}


def fmt(value: float | None, digits: int = 2, unit: str = "") -> str:
    """A figure the Spanish way: decimal comma, spaces between thousands, «–» when absent."""
    if value is None:
        return "–"
    text = f"{value:,.{digits}f}".replace(",", " ").replace(".", ",")
    return f"{text} {unit}".strip()


GLOSSARY = [
    {"term": "Exposición", "text": "La parte de las barras de la ventana con alguna posición "
     "abierta. La ventana sale de la política del activo, nunca de la primera y la última "
     "operación."},
    {"term": "Rendimiento por hora expuesta", "text": "El retorno dividido por la exposición: "
     "lo que rendiría si estuviera dentro todo el tiempo al ritmo al que rinde cuando está. "
     "Es una extrapolación: mide la calidad del tiempo, no un retorno alcanzable."},
    {"term": "Eficiencia", "text": "Ese rendimiento por hora como múltiplo del del buy and "
     "hold. 1,0 es tan productivo por hora como tener el activo."},
    {"term": "A igual riesgo", "text": "El buy & hold con el tamaño que iguala su "
     "volatilidad diaria a la de la estrategia: la única convención en la que «rinde menos» "
     "habla del edge y no del tamaño."}]


def measure(trades: pd.DataFrame, bars: pd.DataFrame, point_value: float, cfg: dict) -> dict:
    """Everything this study measures about one strategy.

    Args:
        trades: That strategy's trades on the chosen sample.
        bars: The window's bars, indexed by open time.
        point_value: Account currency per 1.0 of price and 1.0 of lot.
        cfg: What `inputs.config` returned.

    Returns:
        One flat row: occupancy, the strategy's own statistics, the benchmark's under each
        convention, the trade-off, where the market moved while it was holding, and the
        verdict with its reasons.
    """
    equity = compare.equity_start(trades)
    moves = benchmark.moves(bars)
    mine = benchmark.daily(trades, moves.index)
    exposure = occupancy.measure(trades, bars, point_value, equity)
    held = occupancy.held(trades, bars.index)["signed"]
    closes = bars["Close"].to_numpy()
    presence = occupancy.presence(held, np.diff(closes, prepend=closes[0]))

    strategy = compare.stats(mine, equity)
    lots = {name: benchmark.CONVENTIONS[name](trades, moves, mine, point_value)
            for name in cfg["benchmark"]["report"]}
    bench = {name: compare.stats(benchmark.profit(size, moves, point_value), equity)
             for name, size in lots.items()}
    head = cfg["benchmark"]["headline"]
    trade_off = compare.dichotomy(strategy, bench[head], exposure)
    days = (moves.index[-1] - moves.index[0]).days
    said = verdict.judge(strategy, bench[head], exposure, trade_off, presence,
                         len(trades), days, cfg)

    out = {"n": len(trades), "days": days, "equity_start": equity}
    out |= {f"exp_{key}": value for key, value in exposure.items()}
    out |= {f"strat_{key}": value for key, value in strategy.items()}
    out |= {f"bench_{name}_{key}": value
            for name, found in bench.items() for key, value in found.items()}
    out |= {f"lots_{name}": size for name, size in lots.items()}
    out |= trade_off | presence
    out |= {"verdict": said["verdict"], "reasons": " | ".join(said["reasons"])}
    return out


def run(strategy: str, inputs: dict, cfg: dict) -> dict:
    """What one strategy's return cost in market time, against buy & hold.

    Args:
        strategy: Its name in the export.
        inputs: What load.load() returned.
        cfg: What `inputs.config` returned.

    Returns:
        The contract dict: the verdict with its reasons, the trade-off, the three buy and
        hold conventions and where the market moved while it was holding.
    """
    started = time.time()
    frame = inputs["frame"]
    found = measure(frame[frame["strategy"] == strategy], inputs["bars"],
                    inputs["point_value"], cfg)
    head = cfg["benchmark"]["headline"]
    reasons = [r for r in found["reasons"].split(" | ") if r]
    said = blocks.verdict(
        LABEL[found["verdict"]], "pass" if found["verdict"] == "worth_it" else "fail",
        f"Eficiencia {fmt(found['efficiency'])}x: por hora expuesta rinde eso veces lo que el "
        f"buy & hold {CONVENTIONS[head]}. Pasa desde {fmt(cfg['gate']['min_efficiency'])}x.",
        found["efficiency"], [{"label": r, "state": "watch", "value": None, "note": ""}
                              for r in reasons])
    span = inputs["span"]
    trade = blocks.table("La dicotomía", pd.DataFrame(
        [["Barras con posición", fmt(found["exp_share"] * 100, 2, "%")],
         ["Horas por semana en el mercado", fmt(found["exp_hours_per_week"], 1)],
         ["Horas por semana fuera", fmt(found["hours_off"], 1)],
         ["Cuenta comprometida mientras opera", fmt(found["exp_notional_when_in_pct"], 1, "%")],
         ["Rendimiento por hora expuesta", fmt(found["return_per_exposure_pct"], 1, "%")],
         ["Eficiencia frente al buy & hold", fmt(found["efficiency"]) + "x"],
         ["Retorno total frente al buy & hold", fmt(found["return_ratio"]) + "x"],
         ["Drawdown frente al del buy & hold", fmt(found["dd_ratio"]) + "x"]],
        columns=["Medida", "Valor"]),
        "Rendir menos que el buy & hold en total no es un fallo aquí: es la pregunta.")
    trade["align"] = ["left", "right"]
    sides = blocks.table("La estrategia y el buy & hold", pd.DataFrame(
        [["La estrategia", "–", fmt(found["strat_net"], 0), fmt(found["strat_return_pct"], 1, "%"),
          fmt(found["strat_cagr_pct"], 1, "%"), fmt(found["strat_maxdd_pct"], 1, "%"),
          fmt(found["strat_sharpe"])]]
        + [[f"Buy & hold, {SHORT[c]}", fmt(found[f"lots_{c}"]), fmt(found[f"bench_{c}_net"], 0),
            fmt(found[f"bench_{c}_return_pct"], 1, "%"), fmt(found[f"bench_{c}_cagr_pct"], 1, "%"),
            fmt(found[f"bench_{c}_maxdd_pct"], 1, "%"), fmt(found[f"bench_{c}_sharpe"])]
           for c in cfg["benchmark"]["report"]],
        columns=["", "Lotes", "Net Profit (USD)", "Retorno", "CAGR", "Drawdown", "Sharpe"]),
        f"El veredicto lee la convención {CONVENTIONS[head]}.")
    sides["align"] = ["left"] + ["right"] * 6
    presence = blocks.table("Dónde estaba cuando el mercado se movió", pd.DataFrame(
        [["Movimiento del mercado con posición", fmt(found["captured"] * 100, 2, "%")],
         ["Parte alineada con su dirección", fmt(found["aligned"] * 100, 2, "%")]],
        columns=["Medida", "Valor"]),
        "Capturar mucho movimiento estando poco tiempo y poco alineada se parece más a estar "
        "presente en los tramos buenos que a una ventaja propia.")
    presence["align"] = ["left", "right"]
    return envelope.envelope(
        MODULE, strategy, inputs["identity"].get(strategy), cfg, started,
        [envelope.tab("tradeoff", "Rendimiento contra exposición", [trade, sides, presence],
                      note=f"Muestra {cfg['study']['sample']}, {span[0].date()} a "
                           f"{span[1].date()}: {found['n']} operaciones.")],
        said, glossary=GLOSSARY, summary=found)
