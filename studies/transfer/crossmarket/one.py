"""One strategy across every market, returned as the contract's data: what the window paints."""

import time

from core.study import blocks, identity, result as envelope
from core.symbols import alias
from studies.transfer.crossmarket.contract import backtest, nulls, shared, sweep, tests, words
from studies.transfer.crossmarket.orchestrate import strategy
from studies.transfer.crossmarket.verdict import alerts, breadth

MODULE = "studies.transfer.crossmarket"


def verdict(summary: dict, cfg: dict) -> dict:
    """The breadth screen as a verdict block, the worst market as its one part (§4.4, owner
    2026-09-30: the two "mercados bajo alpha" parts moved out — they are p-value counts, and
    this screen does not read them; they still show in "La estrategia en una tabla"). No
    score: the header read «DESCARTAR … nota 0» with the breadth fraction as a grade, and the
    owner had it removed (2026-10-01) — the fraction is already in the meaning."""
    call, reason = breadth.judge(summary, cfg["verdict"]["breadth_floor"])
    return blocks.verdict(
        call, "pass" if call == "MANTENER" else "fail", reason + ". Es la única criba del "
        "estudio; los p-valores se leen al lado y no deciden nada.", None,
        [{"label": "Peor PF", "state": "info", "value": summary["worst_market"]["pf"],
          "note": alias(summary["worst_market"]["market"])}])


def _warnings(rows: list[dict]) -> list[dict]:
    """Every market's warnings, folded to the top of the page (§4.12, owner 2026-09-30):
    hidden keys never show (still counted elsewhere), and a KS rejection on the fitted holds
    is the one thing highlighted, since it puts a whole null model's p in doubt."""
    return [{"code": f"{alias(r['feed'])}:{k}", "state": "watch",
             "text": shared.text(alerts.TEXTS[k][0]), "highlight": k in nulls.HIGHLIGHT,
             **({"help": words.KS_HELP} if k == "bad_hold_fit" else {})}
            for r in rows for k in r["warnings"] if k not in nulls.HIDDEN]


def run(name: str, inputs: dict, cfg: dict, only: str | None = None) -> dict:
    """Everything the study says about one strategy.

    Args:
        name: Strategy name, exactly as SQX has it.
        inputs: What load.load() returned.
        cfg: What config.load() returned.
        only: One market feed to run on its own. The result then holds that market's
            per-market blocks and says the strategy-level views — correlation, joint null,
            OOS stretch — were not rebuilt: they need every market at once, so a partial
            result never carries a stale version of them.

    Returns:
        The contract dict: the breadth verdict, the tabs, warnings and glossary.
    """
    started = time.time()
    record = strategy.analyse_strategy(
        inputs, cfg, name, only, lambda what, share: envelope.progress(share * 100, what))
    rows = record["rows"]
    warn = _warnings(rows)
    warn += identity.warning(inputs["identity"].get(name))
    if only:
        warn.append({"code": "parcial", "state": "info",
                     "text": f"Sólo se recorrió {alias(only)}. Correlación, nulo conjunto y tramo OOS "
                             f"no se reconstruyen con un mercado suelto: corre la estrategia "
                             f"entera para verlos."})
        tabs = [nulls.random_tab(record, cfg), sweep.tab(record, cfg)]
        return envelope.envelope(MODULE, name, inputs["identity"].get(name), cfg, started,
                                 tabs, warnings=warn, glossary=words.GLOSSARY)
    tabs = [backtest.tab(record, cfg), nulls.random_tab(record, cfg),
            nulls.oos_tab(record, cfg), nulls.models_tab(record, cfg), sweep.tab(record, cfg),
            tests.paired_tab(record), tests.exposure_tab(record)]
    return envelope.envelope(MODULE, name, inputs["identity"].get(name), cfg, started, tabs,
                             verdict(record["summary"], cfg), warn, words.GLOSSARY,
                             summary={"verdict": breadth.judge(
                                 record["summary"], cfg["verdict"]["breadth_floor"])[0]})
