"""THE COMMAND of M9: register a judged portfolio for incubation, or read a file of its fresh days against the band."""

import argparse
import hashlib
import json
from datetime import datetime, timezone as tz
from pathlib import Path

import pandas as pd

from ..funded import _member_meta, size_members
from ..inputs import config
from ..search import trials
from ..verdict import decide
from . import band, record as record_mod

STATE = {"inside": "DENTRO de la banda", "below": "POR DEBAJO de la banda — señalada",
         "above": "POR ENCIMA de la banda — señalada",
         "no_band": "SIN BANDA: el tramo tiene menos de 2 días o es más largo que la historia registrada"}


def head(record: dict) -> str:
    """Who the record is and what was fixed when it was registered, in Spanish."""
    p, c = record["portfolio"], record["comparison"]
    relaxed = f"AJUSTADO: cartera de una run con umbrales relajados {p['relaxed_thresholds']} — no es un resultado\n" if p["relaxed_thresholds"] else ""
    return (f"{relaxed}Cartera {record['portfolio_hash'][:12]} (pool {p['pool']}, K={len(p['weights'])} "
            f"[{', '.join(i[:8] for i in p['weights'])}], veredicto «{p['verdict']}») registrada el {record['registered'][:10]}.\n"
            f"Comparación fijada al registrar: figura «{c['figure']}», banda = percentiles {c['band']} de las ventanas de "
            f"igual longitud de su propia historia en {c['history']} ({record['history']['from']}…{record['history']['to']}, "
            f"{record['history']['days']} días).")


def read(record: dict, folder: Path, rows: pd.DataFrame, meta: dict, origin: str) -> dict:
    """One reading: the rows validated, the stretch read against the band, the ledger row, the log line.

    Args:
        record, folder: `record.load()`'s pair.
        rows: The whole fresh stretch of one source, in the record's row contract.
        meta: identity -> `{symbol, timeframe, family}` of the members.
        origin: Where the rows came from (a file name and its hash), kept in the log.

    Returns:
        `band.read()`'s dict plus `source`, `from`, `to`; appended to `<folder>/readings.jsonl`.

    Raises:
        SystemExit: The rows break the contract; every problem is named.
    """
    if problems := record_mod.validate(record, rows):
        raise SystemExit("las filas no cumplen el contrato de incubación:\n  " + "\n  ".join(problems))
    rows = rows.assign(day=pd.to_datetime(rows["day"]))
    trials.admit(meta, [record_mod.SEGMENT])
    history = record_mod.path(record, pd.read_parquet(folder / "history.parquet"))
    fresh = record_mod.path(record, rows)
    c = record["comparison"]
    got = {**band.read(history.to_numpy(), fresh.to_numpy(), c["figure"], c["band"]),
           "source": rows["source"].iloc[0], "from": str(fresh.index[0].date()), "to": str(fresh.index[-1].date())}
    trials.record_rows({"hash": record["portfolio"]["pool_hash"]}, meta, {
        "launched_by": "incubation", "segment": record_mod.SEGMENT, "n_in": 1, "n_out": 0 if got["flagged"] else 1,
        "criterion": f"portfolio/incubation/{c['figure']}", "thresholds": got,
        "note": f"{got['source']} {got['from']}…{got['to']}: {got['state']}; relaxed={record['portfolio']['relaxed_thresholds'] or 'no'}"})
    with (folder / "readings.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"ts": datetime.now(tz.utc).isoformat(timespec="seconds"), "rows": origin, **got},
                             ensure_ascii=False) + "\n")
    return got


def words(record: dict, got: dict) -> str:
    """A reading in Spanish, each number said, and what it does not decide."""
    lines = [f"Tramo leído ({got['source']}): {got['from']}…{got['to']}, {got['days']} días."]
    if got["state"] != "no_band":
        lines.append(f"{record['comparison']['figure']} = {got['value']:+.4f} (por unidad de riesgo); banda [{got['low']:+.4f}, "
                     f"{got['high']:+.4f}]; el tramo queda en el percentil {got['percentile']:.0f} de {decide.grouped(got['windows'])} ventanas de "
                     f"{got['days']} días de la historia, de las que solo {got['independent']} no comparten ningún día.")
    lines += [f"LECTURA: {STATE[got['state']]}.",
              "Qué se hace con una lectura señalada (cuántas seguidas retiran la cartera o a un miembro, cuánto dura la "
              "incubación) no está decidido: es del dueño. Cada lectura es una mirada más y queda en el ledger."]
    return "\n".join(lines)


def main() -> None:
    """`register --run <folder>` freezes a portfolio and its comparison; `read --portfolio <hash> [--rows <file>]` reads."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="verb", required=True)
    reg = sub.add_parser("register", help="congela la cartera de una run juzgada y la comparación")
    reg.add_argument("--run", type=Path, required=True, help="carpeta de una run con handoff/")
    reg.add_argument("--set", dest="overrides", action="append", default=[])
    rd = sub.add_parser("read", help="lee un fichero de días nuevos contra la banda; sin --rows, el estado")
    rd.add_argument("--portfolio", required=True, help="prefijo del hash de la cartera registrada")
    rd.add_argument("--rows", type=Path, help="parquet o csv con day, identity, pnl, segment, source")
    args = parser.parse_args()
    print(record_mod.NOT_RUNNING)
    if args.verb == "register":
        cfg = config.load(args.overrides)
        if bad := record_mod.missing(cfg):
            raise SystemExit("la comparación no tiene valor y no lleva defecto (regla 11): --set "
                             + " --set ".join(f"incubation.{b}=…" for b in bad))
        members = list(json.loads((args.run / "handoff" / "portfolio.json").read_text(encoding="utf-8"))["weights"])
        factors, excluded = size_members(members)
        if excluded:
            raise SystemExit(f"miembros sin stop del paso 24, sin unidad de riesgo: {excluded}")
        got = record_mod.register(args.run, {k: cfg["incubation"][k] for k in record_mod.KNOBS},
                                  {i: float(factors[i]["factor"]) for i in members})
        print(head(got))
        print(f"Registro: {record_mod.ROOT / got['portfolio_hash'][:12]} (record.json, history.parquet). No se ha leído ningún día nuevo.")
        return
    record, folder = record_mod.load(args.portfolio)
    print(head(record))
    if args.rows is None:
        done = (folder / "readings.jsonl").read_text(encoding="utf-8").splitlines() if (folder / "readings.jsonl").exists() else []
        print(f"Lecturas hechas: {len(done)}." + (f" Última: {json.loads(done[-1])['state']} ({json.loads(done[-1])['to']})." if done else ""))
        return
    rows = pd.read_parquet(args.rows) if args.rows.suffix == ".parquet" else pd.read_csv(args.rows)
    origin = f"{args.rows.name} sha256:{hashlib.sha256(args.rows.read_bytes()).hexdigest()[:16]}"
    got = read(record, folder, rows, {i: _member_meta(i) for i in record["portfolio"]["weights"]}, origin)
    print(words(record, got))


if __name__ == "__main__":
    main()
