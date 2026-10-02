#!/usr/bin/env python3
"""«Proponer investigación»: run /research-direct headless; the director writes its own steps.

    python3 -m ui.daemon.research.direct
"""

import subprocess
import sys

from core.paths import CLAUDE_BIN, ROOT
from studies.research.board import proposal, store

PROMPT = ("/research-direct\n\nLo lanza la ventana (botón «Proponer investigación», ya "
          "confirmado por el dueño con su coste): nadie te contesta. No preguntes antes de "
          "lanzar al director. Una idea con dos lecturas (regla dura 11) NO se elige: va en "
          "la propuesta como pregunta, y el dueño la contesta en la ventana. Termina con la "
          "línea «PROPUESTA: <ruta del .json>» que imprime "
          "`python3 -m studies.research.board.proposal`.")


def main() -> None:
    """Run the skill; exit 2 when it ended without a proposal."""
    (store.proposals_dir() / "estado.json").unlink(missing_ok=True)
    print(f"PROGRESS 0 arrancando al director ({len(proposal.STEPS)} pasos)", flush=True)
    got = subprocess.run([str(CLAUDE_BIN), "-p", PROMPT, "--permission-mode", "auto",
                          "--output-format", "text"], cwd=ROOT, capture_output=True, text=True)
    print(got.stdout, got.stderr, sep="\n", flush=True)
    if got.returncode:
        sys.exit(got.returncode)
    if "PROPUESTA:" not in got.stdout:
        sys.exit(2)


if __name__ == "__main__":
    main()
