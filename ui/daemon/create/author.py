#!/usr/bin/env python3
"""«Crear la plantilla con Claude»: run /sqx-strategy-template headless on the chat's draft brief.

The chat settles every answer; this hands its prompt to Claude Code (`core.paths.CLAUDE_BIN`,
`-p`) in the repository, so the skill checks the install's vocabulary, authors the block if it
is missing, emits and registers the template. Nobody is in front of it: an ambiguity (hard
rule 11) is not guessed, the run ends with a line `PREGUNTA: …` and exit code 2, and the window
shows it.

    python3 -m ui.daemon.create.author --name donchianUpperCrossUpH1
"""

import argparse
import json
import subprocess
import sys

from core.datapaths import template_draft
from core.paths import CLAUDE_BIN, ROOT
from ui.daemon import brief

UNATTENDED = ("\n\nLo lanza la ventana (botón «Crear la plantilla con Claude»): nadie te "
              "contesta. Si algo es ambiguo (regla dura 11), NO elijas: termina con una línea "
              "que empiece por «PREGUNTA:» con las lecturas posibles. Si la plantilla ya existe "
              "con la misma lectura, dilo en una línea que empiece por «YA EXISTE:» y no la "
              "dupliques. Al terminar, una línea «PLANTILLA: <nombre>» con la que quede.")


def main() -> None:
    """Author the draft named on the command line; exit 2 on a question for the owner."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True, help="el borrador del chat, por su nombre")
    a = ap.parse_args()
    draft = json.loads(template_draft(a.name).read_text(encoding="utf-8"))
    text = brief.prompt(draft) + UNATTENDED
    print(text, "\n---", flush=True)
    got = subprocess.run([str(CLAUDE_BIN), "-p", text, "--permission-mode", "auto",
                          "--output-format", "text"], cwd=ROOT, capture_output=True, text=True)
    print(got.stdout, got.stderr, sep="\n", flush=True)
    if got.returncode:
        sys.exit(got.returncode)
    if "PREGUNTA:" in got.stdout:
        sys.exit(2)


if __name__ == "__main__":
    main()
