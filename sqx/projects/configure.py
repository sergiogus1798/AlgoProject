#!/usr/bin/env python3
"""Write an asset's declared costs and one segment's window into every task of a project.cfx."""

import argparse
import re
import zipfile
from pathlib import Path

from core.assetcheck import mc_pending, pending, provisional
from core.assetdata import load, sqx_settings, window
from sqx.projects.ranges import set_ranges
from core.paths import WORKERS

# SQX names an InstrumentInfo <uSymbol>_<broker>, not by the feed. The feed names the
# <Symbol> element instead, and that is where the backtest window lives.
INSTRUMENT = '<InstrumentInfo instrument="{key}"'
SYMBOL = '<Symbol name="{feed}"'


def running_install(cfx: Path) -> str | None:
    """The role whose install holds this file, when that install is up.

    Args:
        cfx: Path of a project.cfx.

    Returns:
        Role name when the file lives inside a headless install that is answering, else
        None. SQX rewrites a project.cfx on save and exit, so a patch applied while it is
        up is silently lost — hard rule 4.
    """
    import socket
    for role, w in WORKERS.items():
        if w["path"] in cfx.parents:
            with socket.socket() as s:
                s.settimeout(0.5)
                if s.connect_ex(("127.0.0.1", w["port"])) == 0:
                    return role
    return None


def set_attr(text: str, opening: str, attr: str, value: str) -> tuple[str, int]:
    """Replace one attribute on every element whose opening tag starts with a given string.

    Args:
        text: A task XML.
        opening: The start of the opening tag, e.g. '<InstrumentInfo instrument="X_Y"'.
        attr: Attribute name.
        value: Its new value, already escaped.

    Returns:
        The text and how many elements were changed. Zero means the element is not in this
        task, which is normal: a project's tasks do not all carry every symbol.
    """
    tags = re.findall(re.escape(opening) + r"[^>]*>", text)
    for tag in tags:
        text = text.replace(tag, re.sub(f'{attr}="[^"]*"', f'{attr}="{value}"', tag, count=1), 1)
    return text, len(tags)


def apply(text: str, data: dict, segment: str) -> tuple[str, dict[str, int]]:
    """Put one segment's window and costs into one task XML.

    Args:
        text: The task XML.
        data: One asset as load() returned it.
        segment: Segment name.

    Returns:
        The patched text and a count per attribute touched.

    ⚠️ The costs written here must ALSO be in SQX's instrument registry, or the project
    refuses to start. Measured 2026-09-23: task and registry must agree field by field,
    and the same segment must run across every task — a 15-task project with the Build at
    spread 5.0 and the retests at 10.0 is unresolved even when the registry matches one of
    them. It is one segment per PROJECT, not per task. `instrument_edit()` gives the
    command that puts the registry in step.
    """
    a, b = window(data, segment)
    s = sqx_settings(data, segment)
    feed = SYMBOL.format(feed=data["sqx_symbol"])
    key = INSTRUMENT.format(key=f'{data["symbol"]}_{data["broker"]}')
    counts = {}
    for opening, attr, value in ((feed, "dateFrom", a), (feed, "dateTo", b),
                                 (key, "defaultSpread", s["defaultSpread"]),
                                 (key, "defaultSlippage", s["defaultSlippage"])):
        text, n = set_attr(text, opening, attr, str(value))
        counts[attr] = n
    ranges = set_ranges(text, data)
    text = ranges.pop("text")
    counts.update({f"mc_{k}": v for k, v in ranges.items()})
    return text, counts


def instrument_edit(data: dict, segment: str) -> str:
    """The sqcli command that puts this asset's declared costs into SQX's own registry.

    Args:
        data: One asset as load() returned it.
        segment: Segment name, which picks the spread on a no_forex asset.

    Returns:
        A `-instrument action=edit …` command line, to run on the live install before the
        project is started: the task and the registry must agree field by field. The
        registry is global, so one install holds one segment's costs at a time — which is
        why a run is one project per segment. `defaultslippage` is **not in the CLI's own
        help** and works anyway, measured 2026-09-23.
    """
    s = sqx_settings(data, segment)
    return (f'-instrument action=edit instrument={data["symbol"]}_{data["broker"]} '
            f'defaultspread={s["defaultSpread"]} '
            f'defaultslippage={s["defaultSlippage"]}')


def ignored_templates(members: dict[str, bytes]) -> list[str]:
    """Tasks that name a template and will silently not use it.

    Args:
        members: The .cfx contents by member name.

    Returns:
        One line per task whose StrategyType names a templateFile but declares
        type="simple". SQX then builds generically and ignores the template, with no error
        anywhere — `OPEN.md` issue 9, 0 of 642. Free: reading the attribute before the
        build costs nothing, proving the same afterwards costs the build.
    """
    out = []
    for name, blob in members.items():
        if not name.endswith(".xml") or name == "config.xml":
            continue
        for m in re.finditer(r"<StrategyType[^>]*>", blob.decode("utf-8")):
            if 'templateFile="' in m.group(0) and 'type="template"' not in m.group(0):
                kind = re.search(r'type="([^"]*)"', m.group(0))
                out.append(f"{name}: names a templateFile but declares "
                           f"type=\"{kind.group(1) if kind else '?'}\"")
    return out


def configure(cfx: Path, symbol: str, segment: str = "build") -> dict[str, tuple]:
    """Rewrite every task of a project so it prices and dates this asset as assets/ says.

    Args:
        cfx: Path of a project.cfx. Must not be held by a running install.
        symbol: Asset name, e.g. "XAUUSD".
        segment: Which segment the whole project runs on. One project, one segment:
            SQX resolves the instrument once per project and every task must agree.

    Returns:
        Task member name to (segment, what changed). The donor a project is cloned from
        carries the master's own live settings, which are NOT the declared policy: on
        XAUUSD it charges SizeBased 8 where assets/ says PercentageBased, and no slippage
        where assets/ says five points. Nothing errors if this is skipped.
    """
    data = load(symbol)
    with zipfile.ZipFile(cfx) as z:
        members = {n: z.read(n) for n in z.namelist()}
    for line in ignored_templates(members):
        print(f"  ⚠️ TEMPLATE IGNORADA — {line}")
    out = {}
    for name, blob in members.items():
        if not name.endswith(".xml") or name == "config.xml":
            continue
        text, counts = apply(blob.decode("utf-8"), data, segment)
        members[name] = text.encode("utf-8")
        if any(counts.values()):
            out[name] = (segment, counts)
    with zipfile.ZipFile(cfx, "w", zipfile.ZIP_DEFLATED) as z:
        for name, blob in members.items():
            z.writestr(name, blob)
    return out


def main() -> None:
    """Configure one project from assets/, refusing when a value is undecided."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cfx", type=Path)
    ap.add_argument("symbol")
    ap.add_argument("--segment", default="build", choices=("build", "oos1", "oos2"),
                    help="which segment the whole project runs on; one project, one segment")
    args = ap.parse_args()

    data = load(args.symbol)
    if args.segment == "oos2":
        raise SystemExit("oos2 está reservado para el WFC y la WFM. Cada mirada lo gasta; "
                         "si de verdad hace falta, que lo diga el dueño.")
    held = running_install(args.cfx)
    if held:
        raise SystemExit(f"el {held} tiene este proyecto abierto y reescribe el .cfx al salir. "
                         f"Párala: bin/sqx-worker.sh --role {held} stop")
    missing = pending(data)
    if missing:
        raise SystemExit(f"{args.symbol}: {', '.join(missing)} sin valor pactado. "
                         "Pregúntale al dueño antes de configurar nada.")

    changed = configure(args.cfx, args.symbol, args.segment)
    print(f"{args.cfx.name}  {args.symbol}")
    print("  ⚠️ los costes NO se escriben en la tarea: una InstrumentInfo que no coincida con")
    print("     el registro de SQX deja el proyecto irresoluble. Aplícalos en el registro:")
    for seg in sorted({s for s, _ in changed.values()}):
        print(f"     {instrument_edit(data, seg)}")
    for seg in sorted({s for s, _ in changed.values()}):
        s, (a, b) = sqx_settings(data, seg), window(data, seg)
        tasks = [n for n, (sg, _) in changed.items() if sg == seg]
        print(f"  {seg}: spread {s['defaultSpread']}, slippage {s['defaultSlippage']}, "
              f"{s['commission']['method']} {s['commission']['value']}, "
              f"swap {s['swap']['type']} {s['swap']['long']}/{s['swap']['short']}, "
              f"ventana {a} a {b}")
        print(f"    {len(tasks)} tarea(s): " + ", ".join(sorted(tasks)))
    if not changed:
        print("  NADA CAMBIADO — ni el instrumento ni el feed aparecen en estas tareas")
    if provisional(data):
        print(f"  ⚠️ PROVISIONAL: {', '.join(provisional(data))} — cifras de trabajo, no "
              "pactadas con el bróker. Todo resultado de este proyecto lo arrastra")
    if mc_pending(data):
        print(f"  ⚠️ rangos MC Retest sin decidir: {', '.join(mc_pending(data))}")


if __name__ == "__main__":
    main()
