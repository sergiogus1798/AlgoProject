"""The preflight every project needs: one asset read out loud, and the index of all of them."""

import csv
import io
import json
import re
import sys

from core.assetcheck import (REQUIRED, before_data, mc_pending, past_data, pending, provisional,
                             segments_pending, validate)
from core.assetdata import (MARKETS, POLICY, RESERVED, classes, enforced, fields, load, markets,
                            mc_retest, policy, schema, special_notes, sqx_settings, symbols,
                            window)
from core.paths import ASSETS, feed_quality_dir


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


def broker_table(brokers: dict) -> list[str]:
    """One line per broker the commission table names, for the report.

    Args:
        brokers: `costs.commission.brokers` of one asset, or `{}` when not written yet.

    Returns:
        `"<broker>: <method> <value> <unit> — <source>, <date>"`, or `"sin confirmar — <note>"`
        for an entry this session could not confirm on the firm's own page.
    """
    lines = []
    for name, b in brokers.items():
        if b.get("confirmed"):
            lines.append(f"{name}: `{b['method']} {b['value']}` {b['unit']} — {b['source']}, {b['date']}")
        else:
            lines.append(f"{name}: sin confirmar — {b.get('note', 'sin fuente propia leída')}")
    return lines


def report(symbol: str) -> str:
    """The text a session must read out before authoring anything for this asset.

    Args:
        symbol: Asset name.

    Returns:
        Markdown: every cost with its unit, every segment, and what is still undecided.
    """
    data = load(symbol)
    s = schema(data)
    units = {**{f: s["spread"]["unit"] for f in fields(data) if f.startswith("spread")},
             s["commission"]["field"]: s["commission"]["unit"],
             **{f: s["slippage"]["unit"] for f in fields(data) if f.startswith("slippage")},
             **{f: s["swap"]["unit"] for f in s["swap"]["fields"]}}
    lines = [f"# {symbol} — clase `{data['class']}`, overrides a aplicar", "",
             f"SQX symbol: {data['sqx_symbol']}   verificado: {data['verified']}", ""]
    for f in fields(data):
        spec = data["costs"][f]
        use = spec["use"] if spec["use"] is not None else "SIN DECIDIR"
        lines.append(f"- **{f}**: usar `{use}` {units[f]}"
                     f" (SQX lleva hoy `{spec['sqx_now']}`) — {spec['why']}")
        for row in broker_table(spec.get("brokers", {})):
            lines.append(f"    - {row}")
    span = data["data"]
    lines.append(f"- **datos en SQX**: {span['from']} a {span['to']}" if span else
                 f"- **datos en SQX**: ⚠️ NINGUNO — `{data['sqx_symbol']}` no existe")
    for name, seg in data["segments"].items():
        mark = ("  ⚠️ RESERVADO para " + ", ".join(seg[RESERVED])
                if RESERVED in seg and enforced() else "")
        if seg["from"] is None or seg["to"] is None:
            lines.append(f"- **segmento {name}**: SIN DECIDIR{mark}")
            continue
        a, b = window(data, name)
        lines.append(f"- **segmento {name}**: {_day(seg['from'], False)} a {_day(seg['to'], True)} "
                     f"inclusive (dateFrom {a}, dateTo {b}){mark}")
    for name, r in mc_retest(data).items():
        span = f"{r['min']} a {r['max']}" if r["min"] is not None else "SIN DECIDIR"
        lines.append(f"- **MC Retest {name}**: sortea {span} puntos — {r['source']} "
                     f"(SQX lleva hoy `{data['mc_retest'][name]['sqx_now']}`)")
    for cat, feeds in (markets(symbol).get("categories") or {}).items():
        lines.append(f"- **retest {cat}**: {', '.join(m['feed'] for m in feeds) or '(vacío)'}")
    for note in data.get("notes", []):
        lines.append(f"- nota: {note}")
    for f in special_notes():
        lines.append(f"- leer también: assets/special/{f.name}")
    return "\n".join(lines)


def feed_quality(data: dict) -> list[str]:
    """Step 4's warning about the feeds this asset builds on, from the last feed-quality scan.

    Args:
        data: load()'s dict.

    Returns:
        One line per feed with its anomalies per year and its stable year, a warning when the
        build segment starts before that year, and its provider episodes by month. Warns, never
        blocks (owner's answer 3.1). Nothing for a feed never scanned.
    """
    lines = []
    for feed in data["feeds"]:
        path = feed_quality_dir(feed) / "summary.json"
        if not path.exists():
            continue
        q = json.loads(path.read_text(encoding="utf-8"))
        lines.append(f"calidad del feed {feed}: {q['marked_per_year']:g} anomalías marcadas por año "
                     f"(mediana desde 2013, K = {q['K']}), estable desde {q['stable_from']} "
                     f"(escaneado {q['scanned_on']}).")
        start = data["segments"]["build"]["from"]
        year = start if isinstance(start, int) else start.year
        if year < q["stable_from"]:
            worse = sorted({g for y, g in q["grade"].items() if year <= int(y) < q["stable_from"]})
            lines.append(f"AVISO: la construcción empieza en {year}, antes del año estable "
                         f"{q['stable_from']}: esos años son {' y '.join(worse)}.")
        for col in sorted({e["columna"] for e in q["episodes"]}):
            months = [e["mes"] for e in q["episodes"] if e["columna"] == col]
            lines.append(f"episodios de {col}: {', '.join(months[:12])}"
                         f"{f' y {len(months) - 12} más' if len(months) > 12 else ''}.")
    return lines


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
        print(f"ESQUEMA ROTO en assets/symbols/{symbol}.yaml: " + "; ".join(broken))
        sys.exit(3)
    print(report(symbol))
    quality = feed_quality(data)
    if quality:
        print("\n" + "\n".join(quality))
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
        # A symbol with a file but no `segments:` entry is a gap in the declaration, not a
        # crash: the windows below `data:` are the owner's decision and are not invented here.
        if not block:
            changed.append(f"{symbol}: ⚠️ no está en `segments:` de _policy.yaml — "
                           "sin tramos declarados, no se le puede refrescar el rango")
            continue
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
