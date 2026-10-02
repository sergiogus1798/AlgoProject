"""What MT5 Bridge › Verificar reads and checks: past checks, the strategy's file, and whether one may start now."""
import json
import re
from datetime import date, timedelta
from pathlib import Path

from core import assetdata, sqxfile
from core.archive import read as archive
from core.paths import MT5_ACCOUNTS, MT5_DATA, STRATEGY_POOLS, archive_dir
from mt5 import tester, wine
from mt5.verify import firms
from ui.daemon.advance import preflight as advance
from ui.daemon.strategy import locate

RUNS = MT5_DATA / "verify"
DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HISTORY_FALLBACK_YEARS = 4       # mt5.verify.run.FALLBACK, when no server says its depth
DEEPEST = "MT5"                  # Desde = the deepest history every firm's server holds


def listing() -> list[dict]:
    """Every check ever run, newest first: its run.json, which says how it ended."""
    out = []
    for f in sorted(RUNS.glob("*/run.json"), reverse=True) if RUNS.is_dir() else []:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except ValueError:
            continue      # a run.json being written this instant
    return out


def result(run: str) -> dict:
    """One check's result.json (the study contract) and its run.json."""
    folder = RUNS / run
    if not re.fullmatch(r"[\w.-]+", run) or not (folder / "run.json").exists():
        return {"error": f"No hay ninguna verificación «{run}»."}
    meta = json.loads((folder / "run.json").read_text(encoding="utf-8"))
    body = folder / "result.json"
    return {"meta": meta,
            "result": json.loads(body.read_text(encoding="utf-8")) if body.exists() else None}


def folder_listing() -> list[dict]:
    """Every `.sqx` under the owner's BanquilloEstrategias pool (encargo §3.1), newest first.

    A cheap glob, never opened or probed — the pool holds under a hundred files. `strategy_pools`
    is optional; a machine without it (or without that entry) offers an empty list, not an error.
    """
    root = STRATEGY_POOLS.get("banquillo")
    if root is None or not root.is_dir():
        return []
    found = sorted(root.rglob("*.sqx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"path": str(p), "name": f"{p.parent.name}/{p.stem}"} for p in found]


def options() -> dict:
    """What the form offers: the firms with a saved account, the tester's models, the archive."""
    shelf = {}
    for row in archive.listing():
        shelf[row["identity"]] = row          # the newest version wins: listing() is oldest first
    return {"firms": [{"firm": f, "label": firms.label(f), "server": a["server"]}
                      for f, a in MT5_ACCOUNTS.items()],
            "models": sorted(tester.MODELS),
            "archive": sorted(shelf.values(), key=lambda r: r["archived_at"], reverse=True),
            "folder": folder_listing()}


def hasta_default(asset: str) -> str:
    """The day before the last `assets/symbols/<asset>.yaml` says SQX holds data for, or "" if
    undecided: a window closing on SQX's last day never starts (`mt5.verify.run.latest`)."""
    data = assetdata.load(asset).get("data") or {}
    return str(data["to"] - timedelta(days=1)) if data.get("to") else ""


def desde_default(hasta: str) -> str:
    """«MT5»: the confirmed job reads each firm's history depth once the terminal is open
    (`mt5.verify.run.earliest`) and starts where all of them and SQX have bars;
    `HISTORY_FALLBACK_YEARS` before Hasta only when no server answers (owner, 2026-09-29 §3.2).
    Probing it here would open the terminal outside the confirmed job."""
    return DEEPEST if DAY.match(hasta or "") else ""


def strategy_file(source: str, identity: str, version: str = "", project: str = "",
                  databank: str = "") -> tuple[Path | None, str]:
    """The .sqx to verify, from the archive, a project's databank, or the Banquillo folder.

    Returns:
        (the file or None, a sentence saying where it came from or why it was not found).
    """
    if source == "archive":
        held = archive.versions(identity)
        if not held:
            return None, "esa estrategia no está en el archivo"
        chosen = version or held[-1]
        path = archive_dir() / identity / chosen / "strategy.sqx"
        return (path, f"archivo, versión {chosen}") if path.exists() else (None, f"{path} no existe")
    if source == "folder":
        root = STRATEGY_POOLS.get("banquillo")
        path = Path(identity)
        if root is None or root not in path.resolve().parents:
            return None, "esa ruta no está dentro de BanquilloEstrategias"
        return (path, "BanquilloEstrategias") if path.exists() else (None, f"{path} no existe")
    if source == "databank":
        if not (project and databank and identity):
            return None, "elige una estrategia en el panel de databanks de Proyecto"
        return locate.sqx(project, databank, identity)
    return None, f"origen «{source}» desconocido"


def check(path: Path | None, start: str, end: str, model: str, chosen: list[str]) -> dict:
    """Whether a check may start now, and the sentence the owner confirms.

    Returns:
        {"ok", "reasons", "text", "asset", "timeframe"}. Refused while the conductor is taken
        by anyone (`advance.busy`), while the MT5 terminal is open — the owner may be looking
        at it; the job opens and closes it itself — and until the window and the tester's
        model are chosen: neither has a default (owner, 2026-09-29: some firms' data is poor).
    """
    reasons = []
    if not MT5_ACCOUNTS:
        reasons.append("config/machine.yaml no tiene `mt5_accounts`: ninguna cuenta que usar")
    deepest = (start or "").upper() == DEEPEST
    if not ((deepest or DAY.match(start or "")) and DAY.match(end or "")):
        reasons.append("escribe las dos fechas de la ventana, AAAA-MM-DD (Desde puede ser MT5)")
    elif not deepest and date.fromisoformat(start) >= date.fromisoformat(end):
        reasons.append("la ventana acaba antes de empezar")
    if model not in tester.MODELS:
        reasons.append("elige el modelo del tester de MT5")
    unknown = [f for f in chosen if f not in MT5_ACCOUNTS]
    if not chosen:
        reasons.append("marca al menos una empresa")
    elif unknown:
        reasons.append(f"sin cuenta guardada: {', '.join(unknown)}")
    asset = timeframe = None
    if path is None:
        reasons.append("no hay estrategia que verificar")
    else:
        asset, rest = sqxfile.symbol(path)
        timeframe = rest.rsplit("_", 1)[-1]
        for firm in chosen:
            why = firms.usable(asset).get(firm, {}).get("why")
            if why:
                reasons.append(why)
    reasons += advance.busy("conductor", "")
    if wine.terminal_running():
        reasons.append("el terminal de MT5 está abierto: ciérralo; la verificación lo abre y "
                       "lo cierra ella misma, una cuenta tras otra")
    since = ("lo más antiguo que tengan todos los servidores y SQX" if deepest else
             f"el {start}")
    text = (f"Se va a verificar {path.stem if path else '—'} ({asset} {timeframe}) desde {since} "
            f"hasta el {end} en {', '.join(chosen) or '—'}:\n"
            "1. MT5 abre cada cuenta con su contraseña guardada y lee el spread y el swap del "
            "símbolo en ese momento; después se cierra.\n"
            "2. En el conductor se crea un proyecto Test_ con un retest por empresa a esas "
            "condiciones, más la exportación del EA a MQL5; el conductor se arranca, corre y "
            "se para, y el proyecto se retira.\n"
            f"3. El EA se compila y se backtestea en el tester de MT5 (modelo «{model}») en la "
            "cuenta de cada empresa. El terminal queda en la última cuenta usada. No se opera "
            "nada: solo backtests.\n"
            "4. Se comparan las dos listas de operaciones con los criterios de aceptación del paso 26.")
    return {"ok": not reasons, "reasons": reasons, "text": text, "asset": asset,
            "timeframe": timeframe}
