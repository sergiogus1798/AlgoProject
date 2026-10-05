"""«Calcular la caja» as one job: the portfolio's paths, the bank table on them, then the decision."""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from core.datapaths import portfolio_dir
from portfolio.funded.sim import inputs

# A `--set` of one of these sections is the bank's; the rest are the construct overrides the run was built under.
BANK_SECTIONS = set(inputs.load([])) - {"compute"}


def step(n: int, what: str, argv: list[str]) -> None:
    """Run one command of the chain, its output into this job's log; stop the chain if it fails."""
    print(f"\n=== {n}/3 · {what} ===\nPROGRESS {33 * (n - 1)} {what}", flush=True)
    done = subprocess.run([sys.executable, "-m", *argv], check=False)
    if done.returncode:
        sys.exit(f"La cadena se para en el paso {n} ({what}): salió con código {done.returncode}.")


def main() -> None:
    """Parse, then `sim.frompool` → `sim.run` → `decide.run` on that one table."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--run", type=Path, required=True, help="funded run folder with verdict.json")
    parser.add_argument("--horizon", type=int, required=True)
    parser.add_argument("--n-paths", type=int, required=True)
    parser.add_argument("--edge-from", required=True, metavar="SEG[,SEG]")
    parser.add_argument("--set", action="append", default=[], metavar="section.key=value")
    args = parser.parse_args()
    bank = [s for s in args.set if s.split(".")[0] in BANK_SECTIONS]
    built = [s for s in args.set if s not in bank]
    paths = portfolio_dir() / "bank" / "paths" / f"{args.run.name}_{datetime.now():%Y%m%d_%H%M%S}.npz"
    step(1, "caminos de la cartera", [
        "portfolio.funded.sim.frompool", "--run", str(args.run), "--horizon", str(args.horizon), "--n-paths",
        str(args.n_paths), "--edge-from", args.edge_from, "--out", str(paths), *[x for s in built for x in ("--set", s)]])
    source = inputs.paths(paths)[1]["source"]
    before = set((portfolio_dir() / "bank").glob("*/manifest.json"))
    step(2, "la caja por plan", [
        "portfolio.funded.sim.run", "--paths", str(paths), "--study", source["study"], "--symbol", source["symbol"],
        "--segment", source["edge_from"][-1], *[x for s in bank for x in ("--set", s)]])
    table = (set((portfolio_dir() / "bank").glob("*/manifest.json")) - before).pop().parent
    step(3, "la decisión", ["portfolio.funded.decide.run", "--bank", str(table)])


if __name__ == "__main__":
    main()
