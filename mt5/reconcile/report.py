"""Write a week's reconciliation as result.json (the study contract) and say it in Spanish."""
import json
from pathlib import Path

import pandas as pd

from core.study import blocks, result as study_result
from ledger import thresholds
from mt5.reconcile import judge

MODULE = "mt5.reconcile"
PAIRS = {"ticket_sqx": "ticket SQX", "type": "tipo", "open_sqx": "entrada SQX",
         "open_live": "entrada real", "entry_gap_min": "desfase entrada (min)",
         "entry_gap_pts": "precio real − SQX (puntos)",
         "entry_slip_pts": "deslizamiento en contra (puntos)",
         "pnl_pts_sqx": "P&L SQX (puntos)", "pnl_pts_live": "P&L real (puntos)",
         "pnl_gap_pts": "diferencia P&L (puntos)", "pnl_gap_cur": "diferencia P&L (divisa)",
         "mae_sqx": "MAE SQX", "mae_live": "MAE real", "mae_gap": "diferencia MAE"}
ROW = {"sqx_trades": "SQX", "live_trades": "real", "paired": "emparejadas",
       "sqx_only": "solo SQX", "live_only": "solo real", "live_open": "abiertas",
       "clock_h": "reloj (h)", "entry_gap_min_mean_abs": "desfase entrada (min)",
       "entry_slip_pts_mean": "deslizamiento (puntos)", "pnl_pts_sqx": "P&L SQX (puntos)",
       "pnl_pts_live": "P&L real (puntos)", "pnl_gap_pts_paired": "dif. P&L (puntos)",
       "pnl_cur_live": "P&L real (divisa)", "pnl_gap_cur_paired": "dif. P&L (divisa)",
       "mae_gap_mean": "dif. MAE media", "mae_pairs": "con M1"}


def reference() -> str:
    """Step 26's bars for the same quantities, shown beside and never applied (owner pending)."""
    return ("Sin listón: aquí no se aprueba ni se suspende nada. Como referencia, el paso 26 "
            f"(SQX contra el tester) pide {thresholds.value('mt5verify.matched_min'):.0%} de "
            "operaciones emparejadas con una tolerancia de entrada de "
            f"{thresholds.value('mt5verify.entry_tolerance_bars')} barra(s).")


def _times(frame: pd.DataFrame) -> pd.DataFrame:
    """Datetime columns as «YYYY-MM-DD HH:MM», empty where there is none."""
    out = frame.copy()
    for c in out.columns[[str(t).startswith("datetime") for t in out.dtypes]]:
        out[c] = out[c].dt.strftime("%Y-%m-%d %H:%M").fillna("")
    return out


def tabs(week: str, pieces: dict[tuple[str, str], dict], strays: pd.DataFrame) -> list[dict]:
    """The summary tab — one row per live strategy and the week's totals — and the trades tab."""
    rows = [{"empresa": firm, "estrategia": name, **{ROW[k]: p["summary"][k] for k in ROW}}
            for (firm, name), p in pieces.items()]
    total = judge.totals([p["summary"] for p in pieces.values()])
    rows.append({"empresa": "", "estrategia": "TOTAL", **{ROW[k]: total.get(k) for k in ROW}})
    head = [blocks.table(f"Semana {week}: cada estrategia en real contra su backtest de SQX",
                         pd.DataFrame(rows, columns=["empresa", "estrategia", *ROW.values()]),
                         "Puntos: movimiento del precio en ticks del activo, sin tamaño. Divisa: "
                         "la de la cuenta, con el backtest puesto al tamaño de cada operación "
                         "real. Diferencias: real − SQX. " + reference())]
    if len(strays):
        head.append(blocks.table("Operaciones de la cuenta con un magic que el registro no nombra",
                                 _times(strays), "No se asignan a ninguna estrategia."))
    detail = []
    for (firm, name), p in pieces.items():
        tag = f"{name} · {firm}"
        detail.append(blocks.table(f"{tag}: operaciones emparejadas",
                                   _times(p["pairs"])[list(PAIRS)].rename(columns=PAIRS),
                                   "Horas en el reloj del servidor."))
        detail.append(blocks.table(f"{tag}: en SQX y no en la cuenta", _times(p["sqx_only"]),
                                   "El backtest abrió y el EA en real no."))
        detail.append(blocks.table(f"{tag}: en la cuenta y no en SQX", _times(p["live_only"]),
                                   "El EA en real abrió y el backtest no."))
    return [study_result.tab("resumen", "Resumen", head),
            study_result.tab("operaciones", "Operaciones", detail)]


def finish(work: Path, week: str, cfg: dict, started: float, pieces: dict[tuple[str, str], dict],
           strays: pd.DataFrame) -> dict:
    """Write `result.json` and `pairs.parquet` in the week's folder.

    Returns:
        The result dict: no verdict (the study describes), `summary` holding each strategy's
        figures under «firm/strategy» and the week's `totals`.
    """
    summary = {"week": week, "totals": judge.totals([p["summary"] for p in pieces.values()]),
               "strategies": {f"{firm}/{name}": p["summary"] for (firm, name), p in pieces.items()},
               "unregistered_trades": len(strays)}
    out = study_result.envelope(MODULE, None, None, cfg, started, tabs(week, pieces, strays),
                                None, summary=summary)
    work.mkdir(parents=True, exist_ok=True)
    (work / "result.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    both = [p["pairs"].assign(firm=firm, strategy=name) for (firm, name), p in pieces.items()]
    if both:
        pd.concat(both, ignore_index=True).to_parquet(work / "pairs.parquet", index=False)
    return out


def say(week: str, pieces: dict[tuple[str, str], dict], strays: pd.DataFrame) -> str:
    """The week in a few Spanish lines, for the terminal and the cron log."""
    def num(value: float | None, unit: str = "") -> str:
        """A figure, or a dash when there is none."""
        return "—" if value is None else f"{value:+.2f}{unit}"

    lines = [f"Reconciliación de la semana {week}"]
    for (firm, name), p in pieces.items():
        s = p["summary"]
        if not s["sqx_trades"] and not s["live_trades"]:
            lines.append(f"  {name} ({firm}): sin operaciones en ninguno de los dos lados")
            continue
        lines.append(
            f"  {name} ({firm}): {s['paired']} emparejadas de {s['sqx_trades']} de SQX y "
            f"{s['live_trades']} reales; solo en SQX {s['sqx_only']}, solo en real "
            f"{s['live_only']}; reloj {s['clock_h']:+d} h")
        lines.append(
            f"    entrada: {num(s['entry_slip_pts_mean'], ' puntos')} de deslizamiento medio en "
            f"contra · P&L real − SQX: {num(s['pnl_gap_pts_paired'], ' puntos')}, "
            f"{num(s['pnl_gap_cur_paired'])} en divisa · MAE real − SQX: "
            f"{num(s['mae_gap_mean'])} de media en {s['mae_pairs']} con barras M1")
        for _, t in p["sqx_only"].iterrows():
            lines.append(f"    falta en real: ticket {int(t['Ticket'])} de SQX, {t['Type']} "
                         f"{t['Open time']:%Y-%m-%d %H:%M}")
        for _, t in p["live_only"].iterrows():
            lines.append(f"    falta en SQX: {t['Type']} real {t['Open time']:%Y-%m-%d %H:%M}")
    total = judge.totals([p["summary"] for p in pieces.values()])
    lines.append(f"  TOTAL: {total['paired']} emparejadas, {total['sqx_only']} solo en SQX, "
                 f"{total['live_only']} solo en real; P&L real − SQX "
                 f"{total['pnl_gap_pts_paired']:+.2f} puntos, "
                 f"{total['pnl_gap_cur_paired']:+.2f} en divisa")
    if not total["sqx_trades"] and not total["live_trades"]:
        lines.append("  Semana sin operaciones.")
    if len(strays):
        lines.append(f"  {len(strays)} operaciones con un magic que el registro no nombra")
    lines.append("  " + reference())
    return "\n".join(lines)
