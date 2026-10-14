"""The cell's palette, chosen by the buildingBlocksExpert in one headless session before its project exists."""

import re
import subprocess

from core.datapaths import template_dir
from core.paths import CLAUDE_BIN, ROOT

MINUTES = 30  # a session that has not answered by then is a failure, not a wait


def choose(cell: dict) -> tuple[str | None, str]:
    """Ask the expert for this template's free hole on this asset and timeframe.

    Args:
        cell: The ledger row.

    Returns:
        (palette name, "") when it ended with its `PALETA:` line; (None, why) when it asked a
        question (hard rule 11), ended without the line or ran out of time. The palette is written
        to `sqx/blocks/palettes/` and not applied: `bin/workflow.sh template` applies it.
    """
    name = f"{cell['template']}_{cell['symbol']}_{cell['timeframe']}"
    prompt = (
        "Sigue .claude/agents/buildingBlocksExpert.md al pie de la letra.\n\n"
        f"Plantilla: {cell['template']} ({template_dir(cell['template'])}; su brief.md es la idea)\n"
        f"Activo: {cell['symbol']} · Timeframe: {cell['timeframe']} · Dirección: {cell['direction']}\n"
        f"Familia de la condición fija: {cell['family']} (prior del dueño: {cell['prior'] or 'sin prior'}; "
        f"evidencia medida: {cell['evidence']}). Lo que encaja en este activo: assets/FAMILIAS.md.\n"
        "El proyecto AÚN NO EXISTE: escribe la paleta y NO la apliques (la aplica bin/workflow.sh).\n"
        f"Guárdala como sqx/blocks/palettes/{name}.yaml. Reglas duras 14 y 15: sin bloques de reloj "
        "ni de calendario, sin bloques de entrada stop/limit, nunca la paleta entera.\n\n"
        "Lo lanza la campaña desatendida: nadie te contesta. Si algo es ambiguo (regla dura 11), NO "
        "elijas: termina con una línea que empiece por «PREGUNTA:» con las lecturas posibles. "
        f"Al terminar, una línea «PALETA: {name}»."
    )
    try:
        out = subprocess.run(
            [
                str(CLAUDE_BIN),
                "-p",
                prompt,
                "--model",
                "opus",
                "--permission-mode",
                "auto",
                "--output-format",
                "text",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=MINUTES * 60,
        ).stdout
    except subprocess.TimeoutExpired:
        return None, f"el buildingBlocksExpert no contestó en {MINUTES} min"
    if "PREGUNTA:" in out:
        return None, out[out.index("PREGUNTA:") :].splitlines()[0]
    if (
        not re.search(rf"^PALETA: {name}\s*$", out, re.M)
        or not (ROOT / "sqx" / "blocks" / "palettes" / f"{name}.yaml").exists()
    ):
        return None, "el buildingBlocksExpert no dejó su paleta: " + out.strip()[-300:]
    return name, ""
