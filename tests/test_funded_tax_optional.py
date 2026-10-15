"""Tax is an optional extra (encargo 73): null = nothing about it anywhere; a rate = shown beside, never decides."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import funding_planted  # noqa: E402

funding_planted.plant()  # before anything imports core.paths

from portfolio.funded.decide import choose
from portfolio.funded.decide import run as decide_run
from portfolio.funded.sim import inputs, report

BASE = {"haircuts": [0, 0.5, 1], "haircut_decides": 0.5}


def _row(plan: str, ev: float) -> dict:
    """A table row with every key the printed lines read."""
    return dict(
        plan=plan, rebuy="none", ev=ev, ev_se=1.0, ev_monkey=ev - 5, outlay_p90=99.0,
        budget_usd=1100.0, ev_h0=ev + 10, ev_h50=ev, ev_h100=ev - 10, price_usd=100.0,
        risk_phase1=0.01, risk_phase2=0.01, risk_phase3=None, risk_funded=0.01,
        p_first_payout=0.5, fees=100.0, ev_per_month=ev / 12, breakeven_h=None, members=["a"], advantage=5.0, ev_lo=0.0, ev_hi=1.0,
    )  # fmt: skip


def _book() -> dict:
    """Two own plans, A and B, each with one row and a passed verdict."""
    return {p: {"own": True, "table": {"manifest": {"paths": {"source": {"plan": p, "verdict_pass": True, "verdict_label": "PASA", "edge_oos": 0.1, "members": ["a"]}}}}, "rows": [_row(p, ev)]} for p, ev in (("A", 30.0), ("B", 50.0))}  # fmt: skip


def test_tax_optional() -> None:
    """Off by default and without a key or a word; on, as before; the choice is the same."""
    cfg = inputs.load([])["owner"]
    assert cfg["tax_rate"] is None, "off by default"
    assert not any("tax_rate" in x for x in inputs.refuse(inputs.load([]))), (
        "null refuses nothing"
    )
    off = choose.decide(_book(), {**BASE, "tax_rate": None}, ignore_verdict=False)
    on = choose.decide(_book(), {**BASE, "tax_rate": 0.4}, ignore_verdict=False)
    assert all("ev_net" not in r for r in off["rows"]), "off: no tax key"
    assert all(abs(r["ev_net"] - 0.6 * r["ev"]) < 1e-9 for r in on["rows"]), (
        "on: as before"
    )
    assert (off["chosen"]["plan"], [r["plan"] for r in off["rows"]]) == (
        on["chosen"]["plan"],
        [r["plan"] for r in on["rows"]],
    ), "same decision"
    for owner, res, word in (
        ({**BASE, "tax_rate": None}, off, False),
        ({**BASE, "tax_rate": 0.4}, on, True),
    ):
        text = "\n".join(
            [*decide_run.lines(res, owner), decide_run.sentence(res, owner)]
        ).lower()
        assert ("imp" in text) is word, (word, text)
    best = {**_row("A", 30.0), "advantage": 5.0, "ev_lo": 0.0, "ev_hi": 1.0}
    for rate, word in ((None, False), (0.4, True)):
        owner = {
            **BASE,
            "tax_rate": rate,
            "budget_eur": 1000,
            "eurusd": 1.12,
            "rebuy": ["none"],
        }
        text = report.sentence({"rows": [best]}, owner).lower()
        assert ("impuestos" in text) is word, (rate, text)
