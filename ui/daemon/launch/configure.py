"""Run the configurator of every chosen task still unconfigured, as its skill does, with the worker stopped."""

import subprocess
import sys
import zipfile
from collections.abc import Callable

from core.paths import ROOT
from sqx.projects import stage
from ui.daemon.launch.steps import silenced


def run(pre: dict, say: Callable[[int, str], None]) -> list[str]:
    """Configure what `steps.unconfigured` named in `pre["configure"]`, never a configured task.

    Args:
        pre: A preflight, ok: `configure` maps module → titles, `row` the registry's row,
            `cfx`, and `chosen` (the launcher's tasks with their `input`) or, from «Continuar
            workflow», `inputs` (title → input databank).
        say: The job's progress line.

    Returns:
        The MC Retest tasks its configurator left without their Monte Carlo (MinDist on a
        market-orders population): they stay off. Read after configuring — before, all eight
        are off and none is silenced.
    """
    inputs = pre.get("inputs") or {t["title"]: t["input"] for t in pre.get("chosen", [])}
    for module, titles in pre.get("configure", {}).items():
        extra = (["--timeframe", pre["row"]["timeframe"]] if module.endswith("crossmarket")
                 else ["--input", inputs[titles[0]]])
        say(8, f"configurando {', '.join(titles)} ({module})")
        got = subprocess.run([sys.executable, "-m", module, pre["row"]["symbol"], "--cfx",
                              str(pre["cfx"]), *extra], capture_output=True, text=True, cwd=ROOT)
        print(got.stdout[-3000:], flush=True)
        if got.returncode:
            sys.exit(f"{module} no configuró {', '.join(titles)} (salida {got.returncode}): "
                     f"{(got.stderr or got.stdout).strip()[-1500:]}")
    with zipfile.ZipFile(pre["cfx"]) as z:
        members = {n: z.read(n) for n in z.namelist()}
    return [t for t in silenced(members, members["config.xml"].decode("utf-8"))
            if t in stage.titles("mcretest")]
