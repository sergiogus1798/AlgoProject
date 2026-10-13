"""Encargo 66 §7.1/7.4b: wait in the background for every project's databanks to load; save them at once (always on, owner 2026-10-13: the exit goes 52 s -> 15 s)."""

import re
import sys
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from sqx.projects.liveapi import call, kill

LOAD_S = 300        # s the databanks of every project may take to load (as `live.start` always allowed)
SAVE_S = 600        # s the parallel saves may take
NEVER_S = 30        # s the presave waits for a «saved» line; a bank with files == memory that writes none is clean (nothing pending)
JOIN_S = LOAD_S + SAVE_S + 60   # s `settle` waits for the thread at most: a hung one never blocks an exit
_RUNS: dict[str, tuple[threading.Thread, dict]] = {}


def _banks(role: str, project: str, only_never: bool = False) -> dict[tuple[str, str], int]:
    """(project, databank) -> strategies in memory, of every project of the session but the run's own.

    The run's project is skipped (its task fills memory ahead of the files for the whole build, by
    design). The «Auto-sync never» databanks (the genetic pool never reaches disk) are left out of the
    load wait; `only_never` returns exactly those, which the presave still saves."""
    return {(p["name"], d["name"]): d["records"] for p in call(role, "list")["projects"] if p["name"] != project
            for d in call(role, "databankList", projectName=p["name"])["databanks"]
            if (d.get("syncType") == "Auto-sync never") == only_never}


def _off(role: str, project: str, files: Callable) -> bool:
    """Whether some watched databank has a file count different from its memory right now."""
    return any(files(p, role, b) != n for (p, b), n in _banks(role, project).items())


def _work(role: str, project: str, box: dict, _files: Callable, _log: Callable) -> None:
    """Wait until memory == disk in every OTHER project; then save them in parallel, so the exit has nothing to write.

    Presave = every databank of every project but the run's own, «Auto-sync never» and stock ones
    included (what makes the exit slow), each only where files == memory at that moment (rule 1); the
    run's project is never synced (two syncs of one databank at once is the documented loss path).
    A bank that writes no «saved» line (nothing pending, or «never») is waited for NEVER_S s, then logged if files == memory, else an error. Results land in `box`; no
    `box["loaded_s"]` means the load is not confirmed and `settle` rechecks it; a failure is `box["error"]`.
    """
    try:
        began = time.monotonic()
        while (mem := _banks(role, project)) and any(_files(p, role, b) != n for (p, b), n in mem.items()):
            if time.monotonic() - began > LOAD_S:
                return
            time.sleep(1)
        box["loaded_s"] = time.monotonic() - began
        log, offset = _log(role), _log(role).stat().st_size
        # 🔬 2026-10-13: a «never» bank with files (stock `Retester/Results`) is still loading when the others
        # are done, and skipped it kept its 5.4 s at the exit: wait while it holds fewer than its files.
        held = _banks(role, project, True)
        while any(_files(p, role, b) > n for (p, b), n in held.items()) and time.monotonic() - began < LOAD_S:
            time.sleep(1)
            held = _banks(role, project, True)
        never = [k for k, n in held.items() if n and _files(k[0], role, k[1]) == n]
        counts = {**mem, **held}
        todo = [k for k, n in mem.items() if n and _files(k[0], role, k[1]) == n]   # empty: no «saved» line
        began = time.monotonic()
        with ThreadPoolExecutor(len(todo + never) or 1) as pool:
            list(pool.map(lambda k: call(role, "synchronizeDatabank", projectName=k[0], databankName=k[1]), todo + never))
        while time.monotonic() - began < SAVE_S:
            text = log.read_bytes()[offset:].decode("utf-8", "replace")
            done = {m.groups() for m in re.finditer(r"Databank '([^/']+)/([^']+)' saved [^\n]*API request", text)}
            miss = {*todo, *never} - done
            # 🔬 2026-10-13: a sync with nothing pending writes NO «saved» line. After NEVER_S s, a bank that
            # wrote none counts as clean ONLY if its files still == its memory (as when it was listed); one
            # that differs keeps waiting, and fails loudly at SAVE_S. Ceiling: a silent rewrite > NEVER_S s.
            if not miss or (time.monotonic() - began > NEVER_S and all(_files(p, role, b) == counts[p, b] for p, b in miss)):
                if miss:
                    print(f"{role}: sin «saved» en {NEVER_S} s (nada que guardar): {sorted(miss)}", file=sys.stderr)
                box["clean"] = {*todo, *never}
                box["saved"] = {"banks": len(done & {*todo, *never}), "s": time.monotonic() - began}
                return
            time.sleep(0.5)
        box["error"] = f"{role}: {len(set(todo) - done)} databank(s) sin «saved» tras {SAVE_S} s"
    except BaseException as e:          # a thread's exception would vanish: `settle` reports it
        box["error"] = f"{role}: {e!r}"


def begin(role: str, project: str, files: Callable, log: Callable) -> None:
    """Start the background wait (and the save) for the session `role` just opened on `project`.

    `files(project, role, bank)` and `log(role)` are `live`'s own (it cannot be imported from here)."""
    box: dict = {"project": project, "files": files}
    thread = threading.Thread(target=_work, args=(role, project, box, files, log), daemon=True)
    _RUNS[role] = (thread, box)
    thread.start()


def settle(role: str) -> dict:
    """Join the background wait before anything exits the session; its figures, `{}` when none ran.

    Only a wait that CONFIRMED the load (`loaded_s`) lets the exit go on. A wait that timed out, died or
    hung is judged by looking again: a databank unloaded right now -> killed by PID (an exit would save
    half-loaded memory over the files, rule 1) and SystemExit; all loaded -> go on; cannot look -> the
    error propagates, the session stays up (neither exit nor kill). Later failures (the save) are reported only.
    """
    thread, box = _RUNS.pop(role, (None, {}))
    if thread:
        thread.join(JOIN_S)
        if "loaded_s" not in box:
            if _off(role, box["project"], box["files"]):
                kill(role)
                raise SystemExit(f"{role}: los databanks de otros proyectos no cargaron "
                                 f"({box.get('error', f'en {LOAD_S} s')}); sesión matada por PID, ficheros intactos")
        elif thread.is_alive():
            box["error"] = f"{role}: la espera en segundo plano no terminó en {JOIN_S} s"
    if "error" in box:
        print(box["error"], file=sys.stderr)
    return box
