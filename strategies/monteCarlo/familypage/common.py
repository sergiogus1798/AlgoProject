"""What every family's page shares: the metric labels, the number format and the mini-verdict
header every family opens with."""

from strategies.monteCarlo import text

LABELS = {"net": "Beneficio neto", "return_pct": "Retorno", "dd": "Drawdown $",
          "dd_pct": "Drawdown %", "ret_dd": "Ret/DD", "sharpe": "Sharpe por operación",
          "pf": "Profit factor", "losing_run": "Racha perdedora"}
# stress.MODELS is code and stays in English; the report is read in Spanish.
MODELS_ES = {"skip": "Entradas que el sistema real no llega a tomar",
             "cost_shock": "Comisión y swap hasta el doble de lo que SQX cobró",
             "fill_degrade": "Ejecuciones que devuelven parte de lo que la propia operación "
                             "ya había cedido",
             "spread_widen": "Un spread más ancho que el fijo que supuso el backtest"}
MONEY = ("net", "dd")
SHARE = ("return_pct", "dd_pct")


def fmt(metric: str, value: float) -> str:
    """One statistic in the units it is read in.

    Args:
        metric: Key of LABELS.
        value: The number.

    Returns:
        A formatted cell.
    """
    if metric in MONEY:
        return f"{value:,.0f} $"
    if metric in SHARE:
        return f"{value:.2%}"
    return f"{value:,.2f}"


def family_header(name: str, verdict: dict) -> str:
    """The mini-verdict a family's own tab opens with: its sub-score and what it fired.

    Args:
        name: "A" to "E".
        verdict: What scoring.verdict() returned.

    Returns:
        A small headline block, then the list of this family's own fired checks — the same
        numbers the page-wide "Lo que falló" already carries, filtered down to this family,
        so reading one tab never requires scrolling back to the top to see whether it held.
    """
    fired = [f for f in verdict["flags"] if f["family"] == name]
    vetoes = sum(1 for f in fired if f["gate"])
    tone = "no" if vetoes else "pass"
    label = "sin vetos" if not vetoes else f"{vetoes} veto{'s' if vetoes > 1 else ''}"
    lines = "".join(
        f'<li><b>{"VETO" if f["gate"] else "Aviso"} · {text.title(f)}</b> — '
        f'{text.sentence(f)}</li>' for f in fired)
    return (f'<div class="card headline">'
            f'<div class="stat"><b>{verdict["subscores"][name]:.0f}</b>'
            f'<span>Sub-score familia {name}</span></div>'
            f'<div class="stat"><b><span class="tier {tone}">{label}</span></b>'
            f'<span>de esta familia</span></div></div>'
            + (f'<ul>{lines}</ul>' if fired else
               '<div class="note">Ninguna prueba de esta familia falló ni avisó.</div>'))
