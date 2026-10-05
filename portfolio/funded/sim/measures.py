"""What a batch of bank draws says: the EV three ways with its interval, the odds per phase, the cash drawdown, the rule that fails most."""

import numpy as np

from portfolio.funded.sim.kernel import C

Z90 = 1.6448536269514722
_RULES = {"ch_daily_loss": "pérdida diaria (challenge)", "ch_max_loss": "pérdida máxima (challenge)",
          "ch_time_limit": "límite de tiempo (challenge)", "fd_daily_loss": "pérdida diaria (fondeada)",
          "fd_max_loss": "pérdida máxima (fondeada)", "denied": "cobro denegado"}


def net(out: np.ndarray) -> np.ndarray:
    """Per draw, what came back to the bank minus what left it."""
    return out[:, C["received"]] - out[:, C["paid"]]


def ev(out: np.ndarray) -> float:
    """The bank's expected value over the draws' whole horizon."""
    return float(net(out).mean())


def _ratio(a: float, b: float) -> float:
    """a / b, NaN when b is 0 (a phase nobody reached, a plan nobody could afford)."""
    return float(a / b) if b else float("nan")


def summary(out: np.ndarray, horizon: int, days_per_year: float) -> dict:
    """One configuration's flat row.

    Args:
        out: `bank.simulate`'s matrix, one row per draw.
        horizon: Path days per draw.
        days_per_year: Path days in a year.

    Returns:
        `ev` (per draw, over the horizon) with `ev_se` (its standard error) and `ev_lo`/`ev_hi`
        — the 90 % interval of that mean over the draws, Monte Carlo error only —
        `net_min`/`net_p5`/`net_p95` (the spread of one bank's outcome), `fees` and `received`
        (mean cash out and back per draw), `refunds` (mean fees refunded per draw), `ev_per_purchase`, `ev_per_dollar`, `ev_per_month`, `p_phase1..3`,
        `p_first_payout` (draws that were ever paid), `purchases` (mean per draw),
        `purchases_to_first` (mean over the draws that were paid), `payouts_per_funded`,
        `funded_life_days` (censored at the horizon), `outlay_p50/p90/p99` (cash out before the
        first payout; all of it when none came), `worst_rule` and `worst_rule_share`.
    """
    x = net(out)
    total = out.sum(axis=0)
    half = Z90 * x.std(ddof=1) / np.sqrt(len(x))
    paid_draws = out[:, C["first_payout_day"]] >= 0
    fails = {name: total[C[name]] for name in _RULES}
    worst = max(fails, key=fails.get)
    row = {"ev": float(x.mean()), "ev_se": float(half / Z90), "ev_lo": float(x.mean() - half),
           "ev_hi": float(x.mean() + half), "fees": float(out[:, C["paid"]].mean()),
           "received": float(out[:, C["received"]].mean()), "refunds": float(out[:, C["refunds"]].mean()),
           "net_min": float(x.min()), "net_p5": float(np.percentile(x, 5)), "net_p95": float(np.percentile(x, 95)),
           "ev_per_purchase": _ratio(x.sum(), total[C["purchases"]]),
           "ev_per_dollar": _ratio(x.sum(), total[C["paid"]]),
           "ev_per_month": float(x.mean() / (horizon / (days_per_year / 12))),
           "p_first_payout": float(paid_draws.mean()),
           "purchases": float(out[:, C["purchases"]].mean()),
           "purchases_to_first": _ratio(out[paid_draws, C["purchases_to_first"]].sum(), paid_draws.sum()),
           "payouts_per_funded": _ratio(total[C["payouts"]], total[C["funded_accounts"]]),
           "funded_life_days": _ratio(total[C["funded_days"]], total[C["funded_accounts"]]),
           "worst_rule": _RULES[worst] if fails[worst] else "ninguna",
           "worst_rule_share": _ratio(fails[worst], sum(fails.values())),
           "budget_stop": float(out[:, C["budget_stop"]].mean())}
    for i in (1, 2, 3):
        passed, failed = total[C[f"pass_phase{i}"]], total[C[f"fail_phase{i}"]]
        row[f"p_phase{i}"] = _ratio(passed, passed + failed)
    for q in (50, 90, 99):
        row[f"outlay_p{q}"] = float(np.percentile(out[:, C["outlay_before_first"]], q))
    return row
