"""Step 26 as an autopilot action: the window's preflight over a list of finalists, one check each, the pool filled."""
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from core import assetdata, sqxfile
from core.paths import MT5_ACCOUNTS, ROOT, WORKERS
from mt5.verify import firms, pool
from ui.daemon.mt5bridge import runs

ROLE = "conductor"              # where mt5.verify.run builds its Test_ project (its config.yaml)
KEYS = ("strategy", "identity", "mother", "sqx", "symbol", "timeframe")
PARAMS = {"start": "el primer día de la ventana, AAAA-MM-DD o MT5",
          "end": "el último día de la ventana, AAAA-MM-DD",
          "model": "el modelo del tester de MT5",
          "firms": "las empresas en las que se verifica"}


def unfit(finalist: dict) -> list[str]:
    """Why one finalist cannot be handed to the check as it is described; empty when it can.

    The file is the truth: what the autopilot says about it (asset, timeframe, identity)
    must be what the file holds, or the pool would file a verdict under another strategy.
    """
    name = finalist.get("strategy", "?")
    missing = [k for k in KEYS if k not in finalist]
    if missing:
        return [f"{name}: a la finalista le falta {', '.join(missing)}"]
    file = Path(finalist["sqx"])
    if not (file.is_absolute() and file.is_file()):
        return [f"{name}: su .sqx no existe en {file}"]
    asset, rest = sqxfile.symbol(file)
    held = (asset, rest.rsplit("_", 1)[-1], sqxfile.identity(file))
    said = (finalist["symbol"], finalist["timeframe"], finalist["identity"])
    if held != said:
        return [f"{name}: el .sqx es {held[0]} {held[1]} {held[2][:12]}…, y la finalista dice "
                f"{said[0]} {said[1]} {str(said[2])[:12]}…"]
    if asset not in assetdata.symbols():
        return [f"{name}: opera {asset}, que no tiene ficha en assets/symbols/"]
    return []


def uncommissioned(asset: str, chosen: list[str]) -> list[str]:
    """The firms whose commission on this asset is not confirmed in `assets/` — the refusal
    `conditions.for_sqx` gives inside the job, said here before anything starts."""
    brokers = assetdata.load(asset)["costs"]["commission"].get("brokers") or {}
    return [f"{asset} no tiene comisión confirmada de {firms.label(f)} en "
            f"assets/symbols/{asset}.yaml (costs.commission.brokers.{f}): complétala en la "
            "zona Activos; no se adivina"
            for f in chosen if f in MT5_ACCOUNTS and ((brokers.get(f) or {}).get("method") is None
                                                      or (brokers.get(f) or {}).get("value") is None)]


def check(project: str, finalists: list[dict], params: dict, own_log: bool = False) -> dict[str, Any]:
    """Whether step 26 may start now for these finalists, and the sentence the owner confirms.

    Args:
        project: The workflow project the finalists come from.
        finalists: `{strategy, identity, mother, sqx, symbol, timeframe}`.
        params: `{start, end, model, firms}` — the owner's, each time; none has a default —
            and the optional `ticks`: a second tester pass on real ticks (`mt5.verify.ticks`).
        own_log: The autopilot's earlier steps wrote the conductor's log: a recent write is
            its own, not a refusal (`advance.busy`).

    Returns:
        {"ok", "reasons", "text"}. The reasons are the window's own (`mt5bridge.runs.check`:
        dates, model, firms, a saved account and an `mt5:` symbol per firm, the conductor
        free, the MT5 terminal closed) for every finalist, plus a missing parameter, a
        finalist that does not match its file and a firm's unconfirmed commission.
    """
    reasons = [f"falta «{k}» ({what}): lo dice el dueño cada vez, no se adivina"
               for k, what in PARAMS.items() if not params.get(k)]
    start, end, model = (str(params.get(k) or "") for k in ("start", "end", "model"))
    chosen = list(params.get("firms") or [])
    ready = []
    for f in finalists:
        why = unfit(f)
        reasons += why
        ready += [] if why else [f]
    for f in ready or [None]:
        reasons += runs.check(Path(f["sqx"]) if f else None, start, end, model, chosen,
                              bool(params.get("ticks")), own_log)["reasons"]
        reasons += uncommissioned(f["symbol"], chosen) if f else []
    reasons = list(dict.fromkeys(reasons))
    worker = WORKERS[ROLE]
    since = ("lo más antiguo que tengan todos los servidores y SQX" if start.upper() == runs.DEEPEST
             else f"el {start or '—'}")
    listed = "\n".join(f"  · {f.get('strategy')} ({f.get('symbol')} {f.get('timeframe')}, madre "
                       f"{f.get('mother')})" for f in finalists)
    accounts = "; ".join(f"{firms.label(f)}: cuenta {MT5_ACCOUNTS[f]['login']} en "
                         f"{MT5_ACCOUNTS[f]['server']}" for f in chosen if f in MT5_ACCOUNTS)
    text = (f"Paso 26 de {project}: se van a verificar {len(finalists)} estrategias desde {since} "
            f"hasta el {end or '—'}, modelo del tester «{model or '—'}»"
            + (" y, además, Real ticks (mucho más lento)" if params.get("ticks") else "") + ", en "
            f"{', '.join(firms.label(f) for f in chosen) or '—'}:\n{listed}\n"
            f"SQX: el conductor ({worker['path'].name}, puerto {worker['port']}). Por cada "
            "estrategia se crea un proyecto Test_ con un retest por empresa a sus condiciones y "
            "la exportación del EA; el conductor se arranca, corre y se para, y el proyecto se "
            "retira.\n"
            f"MT5: {accounts or '—'}. El terminal entra solo en cada cuenta, lee el spread y "
            "el swap, backtestea el EA y queda en la última cuenta usada. No se opera nada: "
            "solo backtests.\n"
            f"Cada veredicto se anota en el pool validado ({pool.ROOT}, un registro por "
            "empresa). Una estrategia que no valida es un resultado y se sigue con la "
            "siguiente; una verificación que se cae para el autopiloto.")
    return {"ok": not reasons, "reasons": reasons, "text": text}


def job(argv: list[str], log: Path) -> int:
    """One `mt5.verify.run`, as the window's job launches it; its output appended to `log`.

    Returns:
        Its exit code. Cancelled from above (the autopilot's SIGTERM), the job is given the
        same signal and waited for: its `finally` stops the conductor it started.
    """
    with log.open("a", encoding="utf-8") as sink:
        proc = subprocess.Popen([sys.executable, *argv], cwd=ROOT, stdout=sink,
                                stderr=subprocess.STDOUT)
        try:
            return proc.wait()
        finally:
            if proc.poll() is None:     # cancelled from above: give the job the signal, wait for its `finally`
                proc.terminate()
                proc.wait()


def run(project: str, finalists: list[dict], params: dict, out: Path) -> str:
    """Verify every finalist on every firm and record each verdict in the pool register.

    Args:
        project, finalists, params: As `check`, which is run again here before anything.
        out: The autopilot's folder for this step: `mt5verify.log` (the jobs' output) and
            `verificados.csv` (one row per finalist and firm, rewritten after each finalist).

    Returns:
        One summary line. Raises SystemExit when the preflight refuses or a job crashes
        (non-zero exit, or no finished check of that file on disk); a finalist that does
        not validate is recorded and the loop goes on.
    """
    got = check(project, finalists, params, own_log=True)
    if not got["ok"]:
        raise SystemExit("paso 26: no se lanza:\n  " + "\n  ".join(got["reasons"]))
    start = "mt5" if str(params["start"]).upper() == runs.DEEPEST else params["start"]
    out.mkdir(parents=True, exist_ok=True)
    seen = []
    for f in finalists:
        before = {p.parent.name for p in pool.RUNS.glob("*/run.json")}
        code = job(["-m", "mt5.verify.run", "--strategy", f["sqx"], "--from", start,
                    "--to", params["end"], "--model", params["model"],
                    "--firms", ",".join(params["firms"]),
                    *(["--also-real-ticks"] if params.get("ticks") else [])],
                   out / "mt5verify.log")
        metas = [json.loads(p.read_text(encoding="utf-8"))
                 for p in sorted(pool.RUNS.glob("*/run.json")) if p.parent.name not in before]
        mine = [m for m in metas if Path(m["file"]) == Path(f["sqx"]).resolve()]
        if code != 0 or not mine or mine[-1]["state"] != "done":
            why = mine[-1].get("error", "") if mine else "no dejó ninguna verificación en disco"
            raise SystemExit(f"paso 26: la verificación de {f['strategy']} se cayó (código "
                             f"{code}): {why} — detalle en {out / 'mt5verify.log'}")
        rows = pool.rows_of(pool.RUNS / mine[-1]["run"], project, f)
        pool.record(rows)
        seen += [{"strategy": r["strategy"], "firm": r["firm"], "verdict": r["verdict"],
                  "run": r["run"], "note": ""} for r in rows]
        seen += [{"strategy": f["strategy"], "firm": firm, "verdict": "sin veredicto",
                  "run": mine[-1]["run"], "note": "pocas operaciones de SQX"}
                 for firm, st in mine[-1]["firms"].items() if st == "none"]
        seen += [{"strategy": f["strategy"], "firm": firm, "verdict": "sin verificar",
                  "run": mine[-1]["run"], "note": why}
                 for firm, why in mine[-1]["refused"].items()]
        pd.DataFrame(seen).to_csv(out / "verificados.csv", index=False)
    parts = [f"{firms.label(firm)} {sum(s['firm'] == firm and s['verdict'] == pool.VALID for s in seen)}"
             f" de {len(finalists)}" for firm in params["firms"]]
    loose = sum(s["verdict"] == "sin verificar" for s in seen)
    return (f"{len(finalists)} verificadas; validadas: {', '.join(parts)}"
            + (f"; {loose} sin verificar (empresa rechazada)" if loose else "")
            + f"; pool en {pool.ROOT}")
