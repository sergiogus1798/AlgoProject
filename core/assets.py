"""The preflight every project needs: one asset read out loud, and the index of all of them."""

import csv
import io
import re
import sys

from core.assetcheck import (REQUIRED, before_data, mc_pending, past_data, pending,
                             provisional, segments_pending, validate)
from core.assetdata import (MARKETS, POLICY, RESERVED, classes, fields, load, markets,
                            mc_retest, policy, schema, special_notes, sqx_settings,
                            symbols, window)
from core.paths import ASSETS


def _day(bound: int | object, end: bool) -> str:
    """One segment bound as the day it means, for reading.

    Args:
        bound: A year, meaning that whole year, or an explicit date meaning that day.
        end: True for the closing bound, so a bare year renders as its 31 December.

    Returns:
        An ISO date.
    """
    return f"{bound}-12-31" if isinstance(bound, int) and end else (
        f"{bound}-01-01" if isinstance(bound, int) else str(bound))


def report(symbol: str) -> str:
    """The text a session must read out before authoring anything for this asset.

    Args:
        symbol: Asset name.

    Returns:
        Markdown: every cost with its unit, every segment, and what is still undecided.
    """
    data = load(symbol)
    s = schema(data)
    units = {**{f: s["spread"]["unit"] for f in s["spread"]["fields"]},
             s["commission"]["field"]: s["commission"]["unit"],
             s["slippage"]["field"]: s["slippage"]["unit"],
             **{f: s["swap"]["unit"] for f in s["swap"]["fields"]}}
    lines = [f"# {symbol} — clase `{data['class']}`, overrides a aplicar", "",
             f"SQX symbol: {data['sqx_symbol']}   verificado: {data['verified']}", ""]
    for f in fields(data):
        spec = data["costs"][f]
        use = spec["use"] if spec["use"] is not None else "SIN DECIDIR"
        lines.append(f"- **{f}**: usar `{use}` {units[f]}"
                     f" (SQX lleva hoy `{spec['sqx_now']}`) — {spec['why']}")
    span = data["data"]
    lines.append(f"- **datos en SQX**: {span['from']} a {span['to']}" if span else
                 f"- **datos en SQX**: ⚠️ NINGUNO — `{data['sqx_symbol']}` no existe")
    for name, seg in data["segments"].items():
        mark = "  ⚠️ RESERVADO para " + ", ".join(seg[RESERVED]) if RESERVED in seg else ""
        if seg["from"] is None or seg["to"] is None:
            lines.append(f"- **segmento {name}**: SIN DECIDIR{mark}")
            continue
        a, b = window(data, name)
        lines.append(f"- **segmento {name}**: {_day(seg['from'], False)} a {_day(seg['to'], True)} "
                     f"inclusive (dateFrom {a}, dateTo {b}){mark}")
    for name, r in mc_retest(data).items():
        span = f"{r['min']} a {r['max']}" if r["min"] is not None else "SIN DECIDIR"
        lines.append(f"- **MC Retest {name}**: sortea {span} puntos "
                     f"(SQX lleva hoy `{data['mc_retest'][name]['sqx_now']}`)")
    for cat, feeds in (markets(symbol).get("categories") or {}).items():
        lines.append(f"- **retest {cat}**: {', '.join(m['feed'] for m in feeds) or '(vacío)'}")
    for note in data.get("notes", []):
        lines.append(f"- nota: {note}")
    for f in special_notes():
        lines.append(f"- leer también: assets/special/{f.name}")
    return "\n".join(lines)


def main() -> None:
    """Print one asset's overrides; exit non-zero if the asset is unknown or undecided."""
    if sys.argv[1] == "--index":
        print(f"indexados {write_index()} activos")
        return
    if sys.argv[1] == "--dataranges":
        moved = write_dataranges()
        print("\n".join(moved) if moved else "sin cambios: _policy.yaml ya está al día")
        return
    symbol = sys.argv[1]
    data = load(symbol)
    broken = validate(data)
    if broken:
        print(f"ESQUEMA ROTO en assets/{symbol}.yaml: " + "; ".join(broken))
        sys.exit(3)
    print(report(symbol))
    for line in past_data(data):
        print(f"AVISO: {line}", file=sys.stderr)
    if segments_pending(data):
        print(f"\nAVISO: los tramos {', '.join(segments_pending(data))} no tienen fechas.\n"
              "Están en assets/_policy.yaml, bajo `segments:`, con los datos que SQX tiene al lado.")
    loose = mc_pending(data)
    if loose:
        print(f"\nAVISO: los rangos MC Retest {', '.join(loose)} no están decididos. No bloquea,\n"
              "pero esa tarea del MC Retest no es interpretable hasta que el dueño los fije.")
    missing = pending(data)
    if missing:
        print(f"\nBLOQUEADO: {', '.join(missing)} sin valor pactado. Pregúntale al dueño.")
        sys.exit(2)


def write_dataranges() -> list[str]:
    """Refresh every asset's `data:` line in _policy.yaml from what SQX holds today.

    Returns:
        One line per asset whose range moved, empty when nothing changed. Asks the
        conductor, whose `user/data` is rsynced from the master on every start, so this
        reflects the master's own store the moment the owner has updated it.
    """
    # Imported here and not at the top: the preflight is a file read and must not drag in
    # the worker driver, which refuses to run on a non-POSIX host.
    from core import exportdrv

    rows = {r[0]: r for r in csv.reader(io.StringIO(exportdrv.symbols())) if len(r) > 7}
    path = ASSETS / POLICY
    text, changed = path.read_text(encoding="utf-8"), []
    for symbol in symbols():
        feed = load(symbol)["sqx_symbol"]
        row = rows.get(feed)
        if row:
            bars = f"{int(row[7]):,}".replace(",", ".")
            new = (f"    data: {{from: {row[4].replace('.', '-')}, "
                   f"to: {row[5].replace('.', '-')}}}   # {feed}, {bars} barras {row[2]}")
        else:
            new = f"    data: null   # \u26a0\ufe0f {feed} NO EXISTE en SQX \u2014 no hay hist\u00f3rico que partir"
        block = re.search(rf"^  {symbol}:\n    data: .*$", text, re.M)
        old = block.group().split("\n")[1]
        if old != new:
            changed.append(f"{symbol}: {old.strip()}  \u2192  {new.strip()}")
            text = text.replace(block.group(), f"  {symbol}:\n{new}")
    path.write_text(text, encoding="utf-8")
    return changed


def write_index() -> int:
    """Regenerate assets/INDEX.md, one line per asset.

    Returns:
        How many assets were listed, so a session sees what is decided without opening 17.
    """
    lines = ["# assets — índice", "",
             "Generado por `python3 -m core.assets --index`. Leer `RULES.md` primero.", "",
             "| activo | clase | bróker | símbolo SQX | decidido | pendiente |",
             "|---|---|---|---|---|---|"]
    for symbol in symbols():
        d = load(symbol)
        miss = pending(d)
        mark = "—" if miss else ("⚠️ provisional" if provisional(d) else "✅")
        lines.append(f"| `{symbol}` | `{d['class']}` | {d['broker']} | `{d['sqx_symbol']}` "
                     f"| {mark} | {', '.join(miss) or '—'} |")
    (ASSETS / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines) - 6


if __name__ == "__main__":
    main()
