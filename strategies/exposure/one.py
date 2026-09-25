"""One strategy against buy and hold, priced in market time, as the contract's data."""

import time

import numpy as np
import pandas as pd

from core.study import blocks, result as envelope
from strategies.exposure import benchmark, compare, occupancy, verdict

MODULE = "strategies.exposure"
CONVENTIONS = {"one_lot": "un lote", "avg_size": "el tamaño medio de la estrategia",
               "equal_risk": "a igual riesgo (misma volatilidad diaria)"}
GLOSSARY = [
    {"term": "Exposición", "text": "La parte de las barras de la ventana con alguna posición "
     "abierta. La ventana sale de la política del activo, nunca de la primera y la última "
     "operación."},
    {"term": "Rendimiento por hora expuesta", "text": "El retorno dividido por la exposición: "
     "lo que rendiría si estuviera dentro todo el tiempo al ritmo al que rinde cuando está. "
     "Es una extrapolación: mide la calidad del tiempo, no un retorno alcanzable."},
    {"term": "Eficiencia", "text": "Ese rendimiento por hora como múltiplo del del buy and "
     "hold. 1,0 es tan productivo por hora como tener el activo."},
    {"term": "A igual riesgo", "text": "El buy and hold con el tamaño que iguala su "
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
    presence = occupancy.presence(held, np.diff(closes, append=closes[-1]))

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
    """What one strategy's return cost in market time, against buy and hold.

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
        found["verdict"], "pass" if found["verdict"] == "worth_it" else "fail",
        f"Eficiencia {found['efficiency']:.2f}x: por hora expuesta rinde eso veces lo que el "
        f"buy and hold {CONVENTIONS[head]}. Pasa desde {cfg['gate']['min_efficiency']:.2f}x.",
        found["efficiency"], [{"label": r, "state": "watch", "value": None, "note": ""}
                              for r in reasons])
    span = inputs["span"]
    trade = blocks.table("La dicotomía", pd.DataFrame(
        [["barras con posición", found["exp_share"]],
         ["horas por semana en el mercado", found["exp_hours_per_week"]],
         ["horas por semana fuera", found["hours_off"]],
         ["cuenta comprometida mientras opera (%)", found["exp_notional_when_in_pct"]],
         ["rendimiento por hora expuesta (%)", found["return_per_exposure_pct"]],
         ["eficiencia frente al buy and hold", found["efficiency"]],
         ["retorno total frente al buy and hold", found["return_ratio"]],
         ["drawdown frente al del buy and hold", found["dd_ratio"]]], columns=["", "valor"]),
        "Rendir menos que el buy and hold en total no es un fallo aquí: es la pregunta.")
    sides = blocks.table("La estrategia y el buy and hold", pd.DataFrame(
        [["la estrategia", None, found["strat_net"], found["strat_return_pct"],
          found["strat_cagr_pct"], found["strat_maxdd_pct"], found["strat_sharpe"]]]
        + [[f"buy and hold, {CONVENTIONS[c]}", found[f"lots_{c}"], found[f"bench_{c}_net"],
            found[f"bench_{c}_return_pct"], found[f"bench_{c}_cagr_pct"],
            found[f"bench_{c}_maxdd_pct"], found[f"bench_{c}_sharpe"]]
           for c in cfg["benchmark"]["report"]],
        columns=["", "lotes", "neto (USD)", "retorno (%)", "CAGR (%)", "DD (%)", "Sharpe"]),
        f"El veredicto lee la convención {CONVENTIONS[head]}.")
    presence = blocks.table("Dónde estaba cuando el mercado se movió", pd.DataFrame(
        [["parte del movimiento del mercado con posición", found["captured"]],
         ["parte alineada con su dirección", found["aligned"]]], columns=["", "valor"]),
        "Capturar mucho movimiento estando poco tiempo y poco alineada se parece más a estar "
        "presente en los tramos buenos que a una ventaja propia.")
    return envelope.envelope(
        MODULE, strategy, inputs["identity"].get(strategy), cfg, started,
        [envelope.tab("tradeoff", "Rendimiento contra exposición", [trade, sides, presence],
                      note=f"Muestra {cfg['study']['sample']}, {span[0].date()} a "
                           f"{span[1].date()}: {found['n']} operaciones.")],
        said, glossary=GLOSSARY, summary=found)
