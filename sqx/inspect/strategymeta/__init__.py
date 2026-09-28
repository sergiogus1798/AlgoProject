"""A strategy's metadata as fields, read off its .sqx (and its project.cfx) without SQX.

`read(sqx_path, project_cfx=None) -> dict`, keys in this order:

- `file`, `name`, `identity` (core.sqxfile.identity), `feed` and `timeframe` of the last test's
  chart (settings.xml says `Portfolio` for the symbol on 135 of 609 real strategies).
- `direction`: "long" | "short" | "both", from sqx.structural.logic.direction.
- `entries`, `exits`: one row per condition — `signal`, `operator`, `index`, `block`,
  `params` (variables resolved to their values), `text` (`Block(Param=value, …)`).
- `signals`: each signal as one line, terms joined by AND/OR.
- `indicators`: SQX's own summary, {"entry": [...], "exit": [...]}.
- `orders`: per entry order — `type`, `direction`, `stop_loss`, `profit_target`,
  `trailing_stop`, `break_even` (None or {"formula", …values}), `exit_after_bars`.
- `order_types`: sorted Enter… keys (sqx.projects.orders.carried).
- `money_management`: `from` ("strategy" or "task"), `method`, `params`, `initial_capital`.
- `friday_close`: {"on", "time" HH:MM, "key": "ExitOnFriday"}.
- `trading_options`: `weekend`, `end_of_day`, `time_range`, `max_trades_per_day`, `session`.
- `last_test`: the task the stored results ran under, from the .sqx's lastSettings.xml —
  `input`, `output`, `window`, `oos`, `chart`, `timeframe`, `precision`, `engine`,
  `setup_from` (Data or CustomData), `costs` {spread, slippage, min_distance, commission (a list
  of the methods switched on), swap or None}, `money_management`.
- `backtest`: only with `project_cfx` — a list, one entry per task of the project writing
  the .sqx's databank (its folder name), same shape as `last_test` plus `project`, `task`,
  `type`, `active`. `costs` is None for a task with no setup of its own (CustomAnalysis);
  a task whose member the .cfx lacks is an entry with `error` only. Never raises.
- `asset`, `asset_card_sha256`: the assets/symbols file declaring the feed, hashed TODAY.
- `notes`: Spanish sentences the reader must see next to the numbers.
"""

from pathlib import Path
from xml.etree import ElementTree

from core import sqxfile
from sqx.inspect.strategymeta import rules, settings
from sqx.projects import orders

CARD_NOTE = "asset_card_sha256: ficha de costes actual, no la del backtest (no existe la histórica)"


def read(sqx_path: Path, project_cfx: Path | None = None) -> dict:
    """Every field the strategy panel shows, from files only — never a call to SQX.

    Args:
        sqx_path: A .sqx, normally inside a databank folder.
        project_cfx: The project.cfx that owns that databank, for the task's costs today.

    Returns:
        The dict the module docstring lays out.
    """
    portfolio = sqxfile.rules(sqx_path)
    root = ElementTree.fromstring(portfolio)
    stamp, last = settings.stamped(sqx_path), settings.task_view(settings.last_settings(sqx_path))
    entries, exits = rules.conditions(root, False), rules.conditions(root, True)
    own = stamp["MoneyManagement.UseFromStrategy"] == "true"
    trading = settings.options(stamp)
    asset, card = settings.asset_card(last["chart"])
    out = {"file": sqx_path.name, "name": stamp["StrategyName"],
           "identity": sqxfile.identity(sqx_path), "feed": last["chart"],
           "timeframe": last["timeframe"], "direction": rules.direction(portfolio),
           "entries": entries, "exits": exits, "signals": rules.rule_lines(entries + exits),
           "indicators": {k: [i for i in stamp.get(f"{k.title()}Indicators", "").split(",") if i]
                          for k in ("entry", "exit")},
           "orders": rules.orders(root), "order_types": sorted(orders.carried(sqx_path)),
           "money_management": ({"from": "strategy",
                                 **settings.sizing(root.find("Strategy/MoneyManagement"))}
                                if own else {"from": "task", **last["money_management"]}),
           "friday_close": trading.pop("friday_close"), "trading_options": trading,
           "last_test": last}
    notes = [CARD_NOTE]
    if project_cfx is not None:
        out["backtest"] = settings.producers(project_cfx, sqx_path.parent.name)
        notes += _task_notes(out["backtest"], last)
    return {**out, "asset": asset, "asset_card_sha256": card, "notes": notes}


def _task_notes(tasks: list[dict], last: dict) -> list[str]:
    """What the reader must know about the project's tasks next to the stored test."""
    read = [t for t in tasks if "error" not in t]
    notes = [f"la tarea «{t['task']}» no se pudo leer ({t['error']}): no se sabe si escribe "
             "en este databank" for t in tasks if "error" in t]
    if not read:
        return notes + ["ninguna tarea del proyecto escribe en este databank"]
    if len(read) > 1:
        notes.append(f"{len(read)} tareas escriben en este databank: "
                     + ", ".join(f"{t['task']} ({'activa' if t['active'] else 'inactiva'})"
                                 for t in read))
    notes += [f"la tarea «{t['task']}» ({t['type']}) no lleva costes en su XML: valen los de "
              "last_test" for t in read if t["costs"] is None]
    notes += [f"la tarea «{t['task']}» ({t['type']}) lee sus costes de CustomData"
              for t in read if t["setup_from"] == "CustomData"]
    notes += [f"los costes de «{t['task']}» hoy no son los del último test guardado en el .sqx"
              for t in read if t["costs"] is not None and t["costs"] != last["costs"]]
    return notes
