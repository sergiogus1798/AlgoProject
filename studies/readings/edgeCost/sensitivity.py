"""How far the edge moves with each cost: the cost tables, the ×0..×3 sensitivity, the breakeven.

Edge per trade = `gross_price` (the price move plus the spread that was inside the fill, before
any swap) minus the four costs MODELLED at the asset card's rates: commission, swap, spread,
slippage. Each cost is multiplied alone (the others stay at ×1) or all together.
"""

import numpy as np
import pandas as pd

COSTS = {"commission": "commission_cost", "swap": "swap_cost", "spread": "spread_today",
         "slippage": "slippage_cost"}
MULTIPLES = [0, 0.5, 1, 1.5, 2, 3]
ALL = "todos"


def components(priced: pd.DataFrame) -> pd.DataFrame:
    """The four modelled costs per trade, positive = paid (swap can be a credit)."""
    return pd.DataFrame({k: priced[c] for k, c in COSTS.items()})


def net(priced: pd.DataFrame, mult: dict | float = 1.0) -> pd.Series:
    """Edge per trade with each cost scaled: `mult` is one factor for all or {cost: factor}."""
    c = components(priced)
    f = pd.Series({k: (mult if not isinstance(mult, dict) else mult.get(k, 1.0)) for k in COSTS})
    return priced["gross_price"] - (c * f).sum(axis=1)


def profit_factor(x: pd.Series) -> float:
    """Sum of wins over sum of losses; inf when there are none."""
    loss = -x[x < 0].sum()
    return float(x[x > 0].sum() / loss) if loss > 0 else float("inf")


def breakeven(priced: pd.DataFrame, which: str = ALL) -> float:
    """The multiplier at which the mean edge reaches 0, the other costs at ×1.

    Args:
        which: One cost name, or "todos" to scale all together.

    Returns:
        nan when the cost's mean is ≤ 0 (a free or credited cost never bites), the multiple
        otherwise — it can be negative when the edge is already negative at ×0 of that cost.
    """
    c = components(priced).mean()
    gross = priced["gross_price"].mean()
    if which == ALL:
        return float(gross / c.sum()) if c.sum() > 0 else float("nan")
    return float((gross - (c.sum() - c[which])) / c[which]) if c[which] > 0 else float("nan")


def cost_table(priced: pd.DataFrame) -> pd.DataFrame:
    """One row per cost (and the total): mean, median, min per trade, and the edge left in it.

    "Edge que queda" is the mean gross minus that cost alone; for the total, minus all four.
    """
    c = components(priced)
    c = c.assign(total=c.sum(axis=1))
    g = priced["gross_price"]
    rows = [[k, g.mean(), g.median(), g.min(), c[k].mean(), c[k].median(), c[k].min(),
             g.mean() - c[k].mean()] for k in c.columns]
    return pd.DataFrame(rows, columns=["coste", "bruto medio", "bruto mediano", "bruto mínimo",
                                       "coste medio", "coste mediano", "coste mínimo",
                                       "edge que queda"])


def swap_split(priced: pd.DataFrame) -> pd.DataFrame:
    """Swap by side: trades, nights, mean nights, mean and median swap cost per trade."""
    rows = []
    for name, side in (("largos", 1), ("cortos", -1)):
        g = priced[priced["direction"] == side]
        rows.append([name, len(g), g["nights"].sum(), g["nights"].mean() if len(g) else np.nan,
                     g["swap_cost"].mean() if len(g) else np.nan,
                     g["swap_cost"].median() if len(g) else np.nan])
    return pd.DataFrame(rows, columns=["lado", "operaciones", "noches", "noches por operación",
                                       "swap medio", "swap mediano"])


def sensitivity(priced: pd.DataFrame) -> pd.DataFrame:
    """Mean edge and net PF at every multiple, per cost alone and all together."""
    rows = []
    for which in [*COSTS, ALL]:
        for m in MULTIPLES:
            x = net(priced, m if which == ALL else {which: m})
            rows.append([which, m, x.mean(), profit_factor(x)])
    return pd.DataFrame(rows, columns=["coste", "multiplicador", "edge por operación",
                                       "profit factor neto"])


def breakeven_table(priced: pd.DataFrame) -> pd.DataFrame:
    """Each cost's breakeven multiple, ordered so the one that bites first is on top."""
    rows = [[k, breakeven(priced, k)] for k in [*COSTS, ALL]]
    t = pd.DataFrame(rows, columns=["coste", "múltiplo de punto muerto"])
    return t.sort_values("múltiplo de punto muerto", na_position="last")


def bites_first(priced: pd.DataFrame) -> str:
    """The single cost whose breakeven multiple is smallest (the tightest margin), "" if none."""
    got = {k: breakeven(priced, k) for k in COSTS}
    got = {k: v for k, v in got.items() if v == v}
    return min(got, key=got.get) if got else ""
