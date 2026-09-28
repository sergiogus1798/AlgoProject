"""How a strategy was tested: its trading options, costs and sizing, off the .sqx and the .cfx."""

import hashlib
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from core import assetdata, cfx

SCALAR = re.compile(r'<([A-Za-z.]+) type="(?:String|Boolean|Integer|Double|Long)">([^<]*)</\1>')


def stamped(path: Path) -> dict[str, str]:
    """The flat settings SQX stamps on a strategy in settings.xml.

    Args:
        path: A .sqx file.

    Returns:
        Every scalar entry by name, as text, e.g. {"ExitOnFriday.FridayExitTime": "2100",
        "Symbol": "XAUUSD_DukasM1_Infinox"}. Times here are HHMM; lastSettings.xml holds the
        same ones in seconds after midnight.
    """
    with zipfile.ZipFile(path) as z:
        return dict(SCALAR.findall(z.read("settings.xml").decode("utf-8", "replace")))


def last_settings(path: Path) -> ElementTree.Element:
    """lastSettings.xml: the whole task configuration the strategy's last test ran under."""
    with zipfile.ZipFile(path) as z:
        return ElementTree.fromstring(z.read("lastSettings.xml"))


def _hhmm(value: str) -> str:
    """An HHMM integer as text, "2100" -> "21:00"."""
    return f"{int(value) // 100:02d}:{int(value) % 100:02d}"


def options(s: dict[str, str]) -> dict:
    """The trading options: Friday close, weekends, end of day, time range, session.

    Args:
        s: stamped().

    Returns:
        `friday_close`, `weekend`, `end_of_day` and `time_range`, each with `on`, its times
        and the SQX `key`; `max_trades_per_day` (0 is no cap) and `session`.
    """
    on = lambda k: s[k] == "true"
    return {"friday_close": {"on": on("ExitOnFriday.ExitOnFriday"), "key": "ExitOnFriday",
                             "time": _hhmm(s["ExitOnFriday.FridayExitTime"])},
            "weekend": {"on": on("DontTradeOnWeekends.DontTradeOnWeekends"),
                        "key": "DontTradeOnWeekends",
                        "friday_close": _hhmm(s["DontTradeOnWeekends.FridayCloseTime"]),
                        "sunday_open": _hhmm(s["DontTradeOnWeekends.SundayOpenTime"])},
            "end_of_day": {"on": on("ExitAtEndOfDay.ExitAtEndOfDay"), "key": "ExitAtEndOfDay",
                           "time": _hhmm(s["ExitAtEndOfDay.EODExitTime"])},
            "time_range": {"on": on("LimitTimeRange.LimitTimeRange"), "key": "LimitTimeRange",
                           "from": _hhmm(s["LimitTimeRange.SignalTimeRangeFrom"]),
                           "to": _hhmm(s["LimitTimeRange.SignalTimeRangeTo"]),
                           "exit_at_end": on("LimitTimeRange.ExitAtEndOfRange")},
            "max_trades_per_day": int(s["MaxTradesPerDay"]),
            "session": s.get("MarketOpenSession")}


def sizing(node: ElementTree.Element) -> dict:
    """The one sizing method in use under a `<MoneyManagement>`, with its parameters.

    Args:
        node: A `<MoneyManagement>`, of a task or of the strategy itself — both ship every
            method and switch one on.

    Returns:
        `method`, `params` (by key, `#` stripped) and `initial_capital`.
    """
    method = next((m for m in node.findall("Method") if m.get("use") == "true"), None)
    if method is None:
        return {"method": None, "params": {}, "initial_capital": node.findtext("InitialCapital")}
    return {"method": method.get("type"),
            "params": {p.get("key").strip("#"): (p.text or "").strip()
                       for p in method.iter() if p.tag in ("Param", "Parameter")},
            "initial_capital": node.findtext("InitialCapital")}


SETUPS = ("Data/Setups/Setup", "CustomData/Setups/Setup")


def _costs(setup: ElementTree.Element) -> dict:
    """One `<Setup>`'s costs: the `<Chart>` spread in points, slippage, minimum distance,
    every commission method switched on (on 3 of 609 real strategies both are), and the
    swap, None when the setup carries none."""
    swap = setup.find("Swap")
    return {"spread": setup.find("Chart").get("spread"), "slippage": setup.get("slippage"),
            "min_distance": setup.get("minDist"),
            "commission": [{"method": m.get("type"), "value": m.findtext(".//Param")}
                           for m in setup.iter("Method") if m.get("use") == "true"],
            "swap": None if swap is None else dict(swap.attrib)}


def task_view(root: ElementTree.Element) -> dict:
    """What one task tests with: window, precision, costs and sizing, as SQX has them.

    Args:
        root: A task's `<Settings>` — a member of a project.cfx or a strategy's
            lastSettings.xml, which share the layout.

    Returns:
        `input`/`output` databanks, `setup_from`, `window` and `oos` ranges, `chart`,
        `timeframe`, `precision`, `engine`, `costs` and `money_management`. The main test's
        setup is `Data/Setups/Setup`; an AutomaticRetest (MC, SPP, WFM, retest on markets)
        keeps its own under `CustomData` — a cross-check's additional markets are not this
        backtest. A task with neither (CustomAnalysis) has `setup_from`, the window, the
        chart and `costs` None, and so has `money_management` without `RiskMoneyManagement`.
    """
    where = next((w for w in SETUPS if root.find(w) is not None), None)
    setup = root.find(where) if where else None
    chart = setup.find("Chart") if setup is not None else None
    node = root.find("RiskMoneyManagement/MoneyManagement")
    risk = root.find("RiskMoneyManagement/RiskManagement")
    bank = lambda name: next((d.get("value") for d in root.iter("Databank")
                              if d.get("name") == name), None)
    at = lambda el, key: None if el is None else el.get(key)
    return {"input": bank("Input"), "output": bank("Output"),
            "setup_from": where and where.split("/")[0],
            "window": None if setup is None else [setup.get("dateFrom"), setup.get("dateTo")],
            "oos": [[r.get("dateFrom"), r.get("dateTo")]
                    for r in root.findall("Data/OutOfSample/Range")],
            "chart": at(chart, "symbol"), "timeframe": at(chart, "timeframe"),
            "precision": at(setup, "testPrecision"), "engine": at(setup, "engine"),
            "costs": None if setup is None else _costs(setup),
            "money_management": None if node is None else {**sizing(node),
                                                           "max_drawdown": at(risk, "maxDrawdown")}}


def producers(project_cfx: Path, databank: str) -> list[dict]:
    """Every task of a project that writes into this databank, as task_view() reads it.

    Args:
        project_cfx: A project.cfx, read off the disk.
        databank: The databank's name — the folder a .sqx sits in.

    Returns:
        One entry per task, with `project`, `task`, `type` and `active` on top of its view.
        Several tasks may write one databank (an inactive twin, a build and its rerun);
        all are returned and none is chosen here. A task whose XML member the archive
        lacks (the corruption of OPEN.md issue 3) cannot say where it writes: it is
        returned with an `error` and nothing else, never skipped in silence.
    """
    with zipfile.ZipFile(project_cfx) as z:
        members = set(z.namelist())
    out = []
    for task in cfx.tasks(str(project_cfx)):
        head = {"project": project_cfx.parent.name, "task": task["name"],
                "type": task["type"], "active": task["active"]}
        if task["file"] not in members:
            out.append({**head, "error": f"falta {task['file']} en el .cfx"})
            continue
        root = cfx.task_xml(str(project_cfx), task["file"])
        if cfx.output_databank(root) == databank:
            out.append({**head, **task_view(root)})
    return out


def asset_card(feed: str) -> tuple[str | None, str | None]:
    """The asset file that declares this feed, and the sha256 of its bytes today.

    Args:
        feed: SQX symbol, e.g. "XAUUSD_DukasM1_Infinox".

    Returns:
        (asset, sha256), or (None, None) when no file in assets/symbols claims the feed.
        It is today's card: assets/ keeps no history, so it is not the backtest's.
    """
    asset = assetdata.symbol_for(feed)
    if asset is None:
        return None, None
    return asset, hashlib.sha256((assetdata.SYMBOLS / f"{asset}.yaml").read_bytes()).hexdigest()
