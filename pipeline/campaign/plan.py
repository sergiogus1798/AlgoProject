"""The campaign's next batch: the board's admitted cells x the clean long templates of that family, never one already queued."""

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

from core.assetdata import load
from core.datapaths import campaign_dir, template_dir, template_registry
from core.paths import DATA, ROOT, feed_quality_dir
from pipeline.campaign import ledger

HERE = Path(__file__).parent
BOARD = DATA / "research" / "board" / "board.json"
MEMORY = ROOT / "studies" / "research" / "memory" / "config.yaml"
PROJECTS = DATA / "projects" / "registry.csv"


def _templates(direction: str) -> dict[str, list[dict]]:
    """The library's templates of one direction with no flag, by the board's family key."""
    family = yaml.safe_load(MEMORY.read_text(encoding="utf-8"))["archetype_family"]
    out: dict[str, list[dict]] = {}
    for file in sorted(template_dir("x").parent.glob("*/manifest.json")):
        doc = json.loads(file.read_text(encoding="utf-8"))
        if doc["direction"] == direction and not doc["flags"]:
            out.setdefault(family[doc["archetype"]], []).append(doc)
    return out


def _launched() -> set[str]:
    """Cells a Trade_ or Research_ project already ran outside the campaign, as ledger keys of any direction."""
    with PROJECTS.open(encoding="utf-8") as src:
        return {f"{Path(r['template']).parent.name or r['template']}|{r['symbol']}|{r['timeframe']}"
                for r in csv.DictReader(src) if r["name"].startswith(("Trade_", "Research_"))}


def _costed(symbol: str) -> bool:
    """Whether the asset can run: its cost card is complete (hard rule 5) and its feed was scanned.

    Step 8's feedQuality reads the feed's `summary.json`; without it the run dies after the build.
    """
    return (feed_quality_dir(load(symbol)["sqx_symbol"]) / "summary.json").exists() and subprocess.run(
        [sys.executable, "-m", "core.assets", symbol], cwd=ROOT, capture_output=True).returncode == 0


def candidates() -> list[dict]:
    """Every cell the campaign could still run, in the order it would run them.

    Returns:
        Rows with the ledger's key, the board's family, points and prior, the project name and
        the palette: `experto` (the buildingBlocksExpert chooses it when the cell runs; owner,
        2026-10-05) or `-` for a template with no free hole. Board cells by points; the first pass gives each cell one template, the
        second its next one, so no cell takes ten runs before another gets its first.
    """
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    pool = _templates(cfg["direction"])
    board = [c for c in json.loads(BOARD.read_text(encoding="utf-8"))["cells"]
             if c["direction"] == cfg["direction"] and c["timeframe"] in cfg["timeframes"]
             and c["family"] in pool]
    costed = {s: _costed(s) for s in sorted({c["symbol"] for c in board})}
    board = sorted((c for c in board if costed[c["symbol"]]), key=lambda c: -c["points"])
    seen = {k for k, r in ledger.cells().items() if not r.get("test")}     # a test is not the cell's run
    launched, out = _launched(), []
    for turn in range(max(len(v) for v in pool.values())):
        for i, cell in enumerate(board):
            own = pool[cell["family"]]
            if turn >= len(own):
                continue
            doc = own[(i + turn) % len(own)]
            if cfg["asset_class"].get(doc["name"], cell["asset_class"]) != cell["asset_class"]:
                continue
            holes = doc["conditions"]["entry"]["free"] + doc["conditions"]["exit"]["free"]
            row = {"template": doc["name"], "symbol": cell["symbol"], "timeframe": cell["timeframe"],
                   "direction": cfg["direction"], "family": cell["family"],
                   "palette": "experto" if holes else "-",
                   "points": cell["points"], "prior": cell["prior"], "evidence": cell["evidence"],
                   "project": f"Trade_{cell['symbol']}_{cell['timeframe']}_{doc['name']}"}
            if ledger.key(row) not in seen and ledger.key(row).rsplit("|", 1)[0] not in launched:
                out.append(row)
    return out


def queue(n: int) -> list[dict]:
    """Freeze the next `n` candidates as one batch: written to `batches/` whole, then to the ledger as pending."""
    rows = candidates()
    batch = datetime.now().strftime("%Y%m%d-%H%M%S")
    file = campaign_dir() / "batches" / f"{batch}.json"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"batch": batch, "board": str(BOARD), "candidates": len(rows),
                                "queued": rows[:n], "not_queued": [ledger.key(r) for r in rows[n:]]},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    return [ledger.mark(row, "pending", batch=batch, **row) for row in rows[:n]]


def test(template: str, symbol: str, timeframe: str) -> dict:
    """Queue one test cell: the board's cell of that template's family there, config.yaml's short build, a Test_ project."""
    cfg = yaml.safe_load((HERE / "config.yaml").read_text(encoding="utf-8"))
    if not _costed(symbol):
        sys.exit(f"{symbol}: ficha de costes incompleta o feed sin escanear (studies.data.feedQuality): no se encola")
    family = next(f for f, docs in _templates(cfg["direction"]).items() if template in [d["name"] for d in docs])
    cell = next(c for c in json.loads(BOARD.read_text(encoding="utf-8"))["cells"]
                if (c["symbol"], c["timeframe"], c["direction"], c["family"]) == (symbol, timeframe, cfg["direction"], family))
    row = {"template": template, "symbol": symbol, "timeframe": timeframe, "direction": cfg["direction"],
           "family": family, "palette": "experto", "points": cell["points"], "prior": cell["prior"],
           "evidence": cell["evidence"], "project": f"Test_{symbol}_{timeframe}_{template}",
           "test": True, **cfg["test"]}
    return ledger.mark(row, "pending", **row)


def _table(rows: list[dict]) -> None:
    """Print cells one per line, in Spanish."""
    for r in rows:
        print(f"  {r['symbol']:<10} {r['timeframe']:<4} {r['family']:<12} {r['template']:<36} "
              f"nota {r['points']:>5}  prior {r['prior'] or '-':<6} {r.get('state', '')}")


def main() -> None:
    """Without arguments, the ledger and what would come next; `--queue N` freezes the next N."""
    p = argparse.ArgumentParser(prog="python3 -m pipeline.campaign.plan")
    p.add_argument("--queue", type=int, metavar="N", help="congela las N siguientes como un lote")
    p.add_argument("--show", type=int, default=15, metavar="N", help="cuántas candidatas enseñar")
    p.add_argument("--test", nargs=3, metavar=("PLANTILLA", "ACTIVO", "TF"), help="encola una celda de prueba")
    args = p.parse_args()
    if args.test:
        _table([test(*args.test)])
        return
    if args.queue:
        print(f"Lote congelado, {args.queue} celdas pendientes:")
        _table(queue(args.queue))
        return
    done = list(ledger.cells().values())
    print(f"Registro: {len(done)} celdas — " + ", ".join(
        f"{sum(r['state'] == s for r in done)} {s}" for s in sorted({r["state"] for r in done})))
    _table([r for r in done if r["state"] != "done"])
    rows = candidates()
    print(f"\nCandidatas sin lanzar: {len(rows)} (tablero del "
          f"{json.loads(BOARD.read_text(encoding='utf-8'))['generated']}). Las {args.show} primeras:")
    _table(rows[:args.show])


if __name__ == "__main__":
    main()
