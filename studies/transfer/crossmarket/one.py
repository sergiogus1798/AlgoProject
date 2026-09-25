"""One strategy across every market, returned as the contract's data: what the window paints."""

import time

from core.study import blocks, result as envelope
from studies.transfer.crossmarket.contract import (backtest, nulls, portfolio, shared, sweep,
                                                   tests, words)
from studies.transfer.crossmarket.orchestrate import strategy
from studies.transfer.crossmarket.verdict import alerts, breadth

MODULE = "studies.transfer.crossmarket"


def verdict(summary: dict, cfg: dict) -> dict:
    """The breadth screen as a verdict block, the other readings as its parts."""
    call, reason = breadth.judge(summary, cfg["verdict"]["breadth_floor"])
    n = summary["markets"]
    return blocks.verdict(
        call, "pass" if call == "MANTENER" else "fail", reason + ". Es la única criba del "
        "estudio; los p-valores se leen al lado y no deciden nada.", summary["fraction"],
        [{"label": "mercados bajo alpha (1a)", "state": "info",
          "value": summary["under_alpha"], "note": f"de {n}"},
         {"label": "mercados bajo alpha (1b)", "state": "info",
          "value": summary["paired_under_alpha"], "note": f"de {n}"},
         {"label": "peor PF", "state": "info", "value": summary["worst_market"]["pf"],
          "note": summary["worst_market"]["market"]}])


def run(name: str, inputs: dict, cfg: dict, only: str | None = None) -> dict:
    """Everything the study says about one strategy.

    Args:
        name: Strategy name, exactly as SQX has it.
        inputs: What load.load() returned.
        cfg: What config.load() returned.
        only: One market feed to run on its own. The result then holds that market's
            per-market blocks and says the strategy-level views — correlation, portfolio,
            joint null, OOS stretch — were not rebuilt: they need every market at once, so a
            partial result never carries a stale version of them.

    Returns:
        The contract dict: the breadth verdict, twelve tabs, warnings and glossary.
    """
    started = time.time()
    record = strategy.analyse_strategy(
        inputs, cfg, name, only, lambda what, share: envelope.progress(share * 100, what))
    rows = record["rows"]
    warn = [{"code": f"{r['feed']}:{k}", "state": "watch",
             "text": shared.text(alerts.TEXTS[k][0])} for r in rows for k in r["warnings"]]
    if only:
        warn.append({"code": "parcial", "state": "info",
                     "text": f"Sólo se recorrió {only}. Correlación, portfolio, nulo conjunto y "
                             f"tramo OOS no se reconstruyen con un mercado suelto: corre la "
                             f"estrategia entera para verlos."})
        tabs = [nulls.random_tab(record, cfg), sweep.tab(record, cfg),
                tests.stress_tab(record, cfg), tests.fingerprint_tab(record)]
        return envelope.envelope(MODULE, name, inputs["identity"].get(name), cfg, started,
                                 tabs, warnings=warn, glossary=words.GLOSSARY)
    tabs = [backtest.tab(record, cfg), nulls.random_tab(record, cfg),
            nulls.oos_tab(record, cfg), nulls.models_tab(record, cfg), sweep.tab(record, cfg),
            tests.paired_tab(record), tests.exposure_tab(record),
            tests.stress_tab(record, cfg), tests.fingerprint_tab(record),
            portfolio.portfolio_tab(record, cfg), portfolio.warnings_tab(record)]
    return envelope.envelope(MODULE, name, inputs["identity"].get(name), cfg, started, tabs,
                             verdict(record["summary"], cfg), warn, words.GLOSSARY,
                             summary={"verdict": breadth.judge(
                                 record["summary"], cfg["verdict"]["breadth_floor"])[0]})
