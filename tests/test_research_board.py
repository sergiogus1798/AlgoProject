#!/usr/bin/env python3
"""Research board: the gate, the four factors, the hole rules, the proposal's refusals and the
profile's self-examination, on synthetic tables (nothing of AlgoData is read or written)."""

import copy
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest import mock

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from studies.research.board import factors, inputs, many, page, palette, proposal, selfcheck, store

CFG = inputs.CONFIG
DRAFT = json.loads((Path(__file__).parent / "fixtures" / "research_proposal_draft.json")
                   .read_text(encoding="utf-8"))
EMPTY = {"attempts": [], "ideas": [], "by_family": [], "spent": []}


def score(symbol: str, family: str, multiple: float, passes: bool, tf: str = "H4",
          direction: str = "short", trades: float = 50.0, clock: bool = False,
          significant: bool | None = None, p_raw: float = 0.01) -> dict:
    """One row of scores.csv."""
    return {"symbol": symbol, "timeframe": tf, "direction": direction, "family": family,
            "score": 40.0, "lead": "x", "p": 0.01, "p_raw": p_raw, "multiple": multiple,
            "stability": 0.8, "stable": True, "trades_per_year": trades, "passes": passes,
            "significant": passes if significant is None else significant, "needs_clock": clock}


def swept(symbol: str, family: str, plateau: bool, best: float, tf: str = "H4",
          direction: str = "short") -> dict:
    """One row of the sweep's best.csv."""
    return {"symbol": symbol, "timeframe": tf, "direction": direction, "family": family,
            "entry": "extreme", "param": 2.0, "exit": "mean20", "multiple": best,
            "trades_per_year": 60.0, "plateau_any": plateau, "max_multiple": best}


def attempt(symbol: str, family: str, outcome: str, tf: str = "H4") -> dict:
    """One row of the attempts table."""
    return {"project": f"Test_{symbol}_{family}_{outcome}", "symbol": symbol, "timeframe": tf,
            "direction": "short", "family": family, "outcome": outcome, "dev_cut": "",
            "asset_class": inputs.asset_class(symbol), "survivors": 3 * (outcome == "survivors")}


def test_gate() -> None:
    """A cell enters by the prior (Alta), by passing naked, or by a sweep plateau — and by
    nothing else: no prior and no measured support stays out, a clock family always does."""
    scores = pd.DataFrame([
        score("USDCHF", "momentum", 3.0, True),                       # no prior, passes naked
        score("USDCHF", "reversion", 50.0, False),                    # no prior, nothing: out
        score("USDCHF", "ruptura", 0.3, False),                       # no prior, sweep plateau
        score("XAUUSD", "tendencia", 0.3, False),                     # prior Alta alone
        score("EURUSD", "momentum", 0.3, False, tf="M30"),            # prior Baja, nothing: out
        score("USA500", "reversion", 0.3, False, tf="M15"),           # «(largo)»: the short is out
        score("USA500", "reversion", 0.3, False, tf="M15", direction="long"),
        score("GBPJPY", "reversion", 0.3, False, tf="H1"),            # pullback Alta, filed here
        score("EURUSD", "sesion", 9.0, True, clock=True)])            # clock: out whatever it pays
    sweep = pd.DataFrame([swept("USDCHF", "ruptura", True, 4.0)])
    board = many.run(scores, EMPTY, CFG, sweep)
    got = {(c["symbol"], c["direction"], c["family"]): c for c in board["cells"]}
    assert set(got) == {("USDCHF", "short", "momentum"), ("USDCHF", "short", "ruptura"),
                        ("XAUUSD", "short", "tendencia"), ("USA500", "long", "reversion"),
                        ("GBPJPY", "short", "reversion")}
    assert board["gated_out"] == 4
    assert got[("USDCHF", "short", "momentum")]["entered_by"] == ["desnudo"]
    assert got[("USDCHF", "short", "ruptura")]["entered_by"] == ["barrido"]
    assert got[("USDCHF", "short", "ruptura")]["trades_per_year"] == 60.0
    alone = got[("XAUUSD", "short", "tendencia")]
    assert alone["entered_by"] == ["prior"] and alone["trades_per_year"] is None
    assert got[("GBPJPY", "short", "reversion")]["pullback"]
    text = page.text(board)
    assert "sin medir" in text and "pullback: contexto de tendencia" in text


def test_order_prior_and_evidence() -> None:
    """Prior-Alta with evidence for ranks first; prior alone and a naked pass alone are
    comparable; measured against sinks and says so."""
    scores = pd.DataFrame([
        score("XAUUSD", "tendencia", 3.0, True),                              # both
        score("EURJPY", "tendencia", 0.3, False),                             # prior alone
        score("USDCHF", "momentum", 3.0, True),                               # measured alone
        score("GBPJPY", "tendencia", 0.2, False, significant=True)])          # prior, against
    cells = {c["symbol"]: c for c in many.run(scores, EMPTY, CFG, None)["cells"]}
    assert [c for c in sorted(cells, key=lambda s: cells[s]["rank"])][0] == "XAUUSD"
    assert cells["GBPJPY"]["rank"] == 4 and cells["GBPJPY"]["evidence"] == "against"
    assert abs(cells["EURJPY"]["points"] - cells["USDCHF"]["points"]) < 8
    assert cells["XAUUSD"]["points"] > cells["EURJPY"]["points"] + 15
    assert cells["GBPJPY"]["points"] < cells["EURJPY"]["points"] / 2 + 5
    assert cells["EURJPY"]["factors"]["evidence"] == 0.25 and cells["EURJPY"]["evidence"] == "none"
    assert "«medido en contra»" in page.text(many.run(scores, EMPTY, CFG, None))


def test_past_is_flat_without_closed_runs() -> None:
    """Nothing closed: every family reads the same 0.5, tried or not."""
    tried = [{"family": "ruptura", "asset_class": "metal", "attempts": 12, "closed": 0,
              "with_survivors": 0, "survivors": 0}]
    a = factors.past(tried, "ruptura", "metal", 4, 0.9)
    b = factors.past(tried, "momentum", "forex", 4, 0.9)
    assert a["rate"] == b["rate"] == 0.5 and a["low"] < 0.2 and a["high"] > 0.8


def test_past_shrinks_and_spares_the_untried() -> None:
    """One survivor of one run moves the rate less than nine of ten; an untried family sits on
    the pooled rate; the interval narrows with evidence."""
    rows = [{"family": "ruptura", "asset_class": "metal", "closed": 1, "with_survivors": 1},
            {"family": "tendencia", "asset_class": "forex", "closed": 10, "with_survivors": 9},
            {"family": "sesion", "asset_class": "forex", "closed": 10, "with_survivors": 0}]
    one = factors.past(rows, "ruptura", "metal", 4, 0.9)
    many_ = factors.past(rows, "tendencia", "forex", 4, 0.9)
    bad = factors.past(rows, "sesion", "forex", 4, 0.9)
    untried = factors.past(rows, "patron", "index", 4, 0.9)
    assert untried["rate"] == untried["pooled"] == 11 / 23
    assert untried["pooled"] < one["rate"] < many_["rate"] and bad["rate"] < untried["rate"]
    assert many_["high"] - many_["low"] < one["high"] - one["low"]


def test_factors_order_the_board() -> None:
    """Among cells alike in prior and evidence, more effect ranks first; an attempt in the cell
    or ideas spent there push it down."""
    scores = pd.DataFrame([score("USDCHF", "momentum", 8.0, True),
                           score("UKOIL", "momentum", 8.0, True),
                           score("USDCHF", "ruptura", 4.0, True),
                           score("USOIL", "momentum", 8.0, True, trades=5)])
    memory = {**EMPTY, "attempts": [attempt("UKOIL", "momentum", "unknown")],
              "spent": [{"symbol": "USOIL", "timeframe": "H4", "direction": "short",
                         "family": "", "ideas": 6}]}
    board = many.run(scores, memory, CFG, None)
    cells = {(c["symbol"], c["family"]): c for c in board["cells"]}
    top = cells[("USDCHF", "momentum")]
    assert top["rank"] == 1 and top["points"] == 60.5      # 30 evidence + 8 signal + 15 + 7.5
    assert cells[("USDCHF", "ruptura")]["points"] < top["points"]
    assert cells[("UKOIL", "momentum")]["factors"]["gap"] == 0.5 < top["factors"]["gap"]
    spent = cells[("USOIL", "momentum")]
    assert spent["factors"]["brake"] == 0.5 and spent["ideas_spent"] == 6
    assert abs(spent["points"] - top["points"] / 2) < 0.06
    assert spent["provisional_costs"] and not top["provisional_costs"]
    text = page.text(board)
    assert "costes provisionales" in text and "6 ideas (x0.50)" in text and "plano" in text
    assert "la prior las da por Alta" in text


def test_hole_rules() -> None:
    """Orthogonal families weigh most, the counter-trend next, alike and own are kept out."""
    rules = CFG["palette"]
    assert palette.relation("momentum", "session", rules) == "orthogonal"
    assert palette.relation("momentum", "mean_reversion", rules) == "counter"
    assert palette.relation("mean_reversion", "trend", rules) == "counter"
    assert palette.relation("momentum", "trend", rules) == "alike"
    assert palette.relation("momentum", "pattern", rules) == "same_data"
    assert palette.relation("momentum", "momentum", rules) == "own"
    with mock.patch.object(palette, "family_blocks", lambda f, w, role=None: {f + "Block": 3}):
        rows = {r["family"]: r for r in palette.hole("tendencia")}
    assert rows["trend"]["weight"] == rows["breakout"]["weight"] == 0 == len(rows["trend"]["blocks"])
    assert rows["volatility"]["weight"] == 3 and rows["mean_reversion"]["weight"] == 2
    assert rows["volatility"]["blocks"] == {"volatilityBlock": 3}


def test_proposal_refusals() -> None:
    """The fixture passes; two directions, a palette alike, a question without readings do not."""
    assert proposal.check(DRAFT) == []
    bad = copy.deepcopy(DRAFT)
    bad["ideas"][0]["direction"] = "long"
    bad["ideas"][1]["palette"]["families"].append({"family": "trend", "weight": 1, "reason": ""})
    bad["ideas"][2]["questions"] = [{"question": "¿cuál?", "readings": ["una"]}]
    said = " | ".join(proposal.check(bad))
    assert "una sola dirección" in said and "nunca dos iguales" in said and "sin sus lecturas" in said
    assert "tres ideas" in " ".join(proposal.check({**DRAFT, "ideas": DRAFT["ideas"][:2]}))


def test_proposal_stamp_and_launchable() -> None:
    """Python stamps K, the mark and the standing costs; a question or a veto blocks only its idea."""
    scores = pd.DataFrame([score("XAUUSD", "momentum", 26.0, True, trades=4.6)])
    memory = {**EMPTY, "spent": [{"symbol": "XAUUSD", "timeframe": "H4", "direction": "short",
                                  "family": "", "ideas": 1}]}
    p = proposal.stamp(DRAFT, many.run(scores, memory, CFG), datetime(2026, 10, 1, 12))
    assert p["id"] == "20261001-120000-XAUUSD-H4-short-momentum" and p["ideas_spent"] == 1
    assert len(p["standing_costs"]) == 2 and not p["provisional_costs"]
    assert [proposal.launchable(i)[0] for i in p["ideas"]] == [True, False, True]
    p["ideas"][1]["questions"][0]["answer"] = "Por el rango"
    p["ideas"][2]["vetoed"] = True
    assert [proposal.launchable(i) for i in p["ideas"]][1:] == [(True, ""), (False, "vetada")]
    with tempfile.TemporaryDirectory() as tmp, \
            mock.patch.object(store, "proposals_dir", lambda: Path(tmp)):
        proposal.save(p)
        assert proposal.listing() == [p["id"]] and proposal.load(p["id"]) == p
        md = (Path(tmp) / f"{p['id']}.md").read_text(encoding="utf-8")
    assert "ya van **1 ideas**" in md and "VETADA" in md and "Respuesta: Por el rango" in md
    assert "Las supervivientes se parecerán" in md and "> **Pocas operaciones.**" not in md


def test_selfcheck_known_answers() -> None:
    """Too few runs: says so. A profile that orients: keep. One that does not: reduce, with cost."""
    cfg = CFG["selfcheck"]
    few = pd.DataFrame({"score": [10.0, 60.0], "survived": [False, True]})
    got = selfcheck.judge(few, cfg)
    assert not got["enough"] and "hacen falta 20" in selfcheck.text(got, 0.5)
    good = pd.DataFrame({"score": [20.0] * 15 + [70.0] * 15,
                         "survived": [False] * 14 + [True] + [True] * 12 + [False] * 3})
    got = selfcheck.judge(good, cfg)
    assert got["decision"] == "mantener" and got["proven"] and got["p"] < 0.001
    assert got["runs_saved"] == 15 and got["survivor_runs_lost"] == 1
    flat = pd.DataFrame({"score": [20.0] * 15 + [70.0] * 15,
                         "survived": ([True] * 5 + [False] * 10) * 2})
    got = selfcheck.judge(flat, cfg)
    assert got["decision"] == "reducir" and not got["proven"] and got["survivor_runs_lost"] == 5
    assert "de 0.50 a 0.25" in selfcheck.text(got, 0.5)


def test_selfcheck_joins_only_closed_runs() -> None:
    """Dev draws, failed and unknown runs are not evidence."""
    scores = pd.DataFrame([score("XAUUSD", "momentum", 3.0, True),
                           score("EURUSD", "momentum", 3.0, False)])
    rows = [attempt("XAUUSD", "momentum", "survivors"), attempt("EURUSD", "momentum", "died@gate"),
            attempt("EURUSD", "momentum", "failed@9"), attempt("XAUUSD", "momentum", "unknown"),
            {**attempt("XAUUSD", "momentum", "survivors"), "dev_cut": "yes"}]
    runs = selfcheck.closed_runs(rows, scores)
    assert sorted(runs["survived"]) == [False, True]


def main() -> None:
    """Run every test in file order."""
    for name, test in list(globals().items()):
        if name.startswith("test_"):
            test()
            print("ok", name)


if __name__ == "__main__":
    main()
