---
name: perf
description: Measure what the project costs in time, memory and disk, find where it is worth making faster, and implement the improvement on a branch. Use when the owner asks how fast something is, why something is slow, whether a change made it worse, what AlgoData is storing, or asks to optimise a module or update the performance catalogue.
---

# /perf

```
perf/ (los instrumentos)  →  history.csv  →  rendimiento.html  →  una rama con la mejora
     mide                    sólo crece      el panel             y su número antes/después
```

Nothing here touches StrategyQuant X, and nothing here merges to master.

You do the work in this session — there are no perf subagents (retired 2026-09-25: never used, and
a cold agent re-derives what the session already knows). Read `docs/manual/12-rendimiento.md` first.

## Sin argumento — la revisión completa

`/perf catalogo`, then `/perf datos`. Give the owner, in Spanish: the regressions with their cause,
how close the heaviest target is to not fitting in memory, and **the single change with the best
measured prize per unit of work**. Ask whether to build that one; only on a yes, `/perf mejorar`.
Choosing what to optimise is his call; measuring what it would be worth is yours.

## `/perf catalogo` — sólo medir

```bash
uptime && free -g
ps -eo pid,ppid,etime,rss,cmd | grep -E 'forkserver|resource_tracker' | grep -v grep
python3 -m perf.catalogue --scaling                  # sale != 0 si algo empeoró: es un dato
python3 -m perf.catalogue --hotspots <target>        # por cada regression / improvement
python3 -m perf.render.panel
```

A load average not near zero, or orphaned pools holding gigabytes, **invalidates the measurement** —
it goes into an append-only file and stays wrong forever. Report that instead of measuring through
it; orphans are killed by PID, parent first, after telling the owner. For each thing that moved,
find the commit in `git log` that touched what the profile blames; a regression you cannot attribute
is probably the machine — say so. Change nothing outside `perf/`.

## `/perf datos` — sólo el disco

`python3 -m perf.disk.report` (cron already runs `--quick` nightly; its log is
`AlgoData/logs/disk-nightly.log`). For each big branch, `grep -rn "<branch>" --include="*.py" .` —
a branch nothing reads is a different finding from one every run reads. Every proposal carries
**what it saves** (measured), **what it costs** (which code changes) and **what is lost** (CSV is
greppable and opens in a spreadsheet; that is worth real megabytes). An export under `raw/` is
immutable and dated on purpose. **Read-only: nothing under the data root is deleted, moved or
rewritten.**

## `/perf mejorar <módulo>` — idear y codear

1. `git status --porcelain` clean; `python3 -m perf.catalogue --only <target>` and `--hotspots`.
   No target in `perf/inputs/targets.py`? The first commit adds one — without a before, no after.
2. `git checkout -b perf/<module>-<what>`. **One idea per branch.**
3. Correctness before speed: `for t in tests/test_*.py; do python3 "$t" || break; done` (no pytest),
   and compare the numbers **that decide something** — the percentiles a gate reads, the verdict —
   not a checksum. Unseeded simulation: compare distributions and say which statistic.
4. Measure again, `python3 tools/depmap.py && python3 tools/checks.py` green, commit with the
   before/after in the message. **Stop: no merge, no rebase, no second branch.** The merge is his.

The non-obvious thing learned goes into a card in `knowhow/perf/`, tagged 🔬, in the same task.

## Sin modelo: los tres comandos

The owner can run all of this himself, and should when he just wants the number:

```bash
python3 -m perf.catalogue                                 # mide todo y compara con la vez anterior
python3 -m perf.catalogue --hotspots montecarlo.analyse   # dónde se le va el tiempo a uno
python3 -m perf.disk.report                               # qué hay en AlgoData
python3 -m perf.render.panel                              # redibuja la página
```

`docs/manual/12-rendimiento.md` explains every column. `catalogue` exits non-zero on a regression,
so it can go in cron.

## Lo que hace honesta la respuesta

- **Compara por unidad de trabajo.** Un export que creció no es una regresión.
- **`noisy` no es "igual", es "no lo sé".** Nunca presentes un cambio `noisy` como resultado; si hace
  falta saberlo, sube `harness.repeats` y vuelve a medir.
- **El pico de memoria es el del árbol de procesos.** `ru_maxrss` del padre se equivoca por un orden
  de magnitud en cuanto hay trabajadores: 535 MB frente a 2.340 MB reales en `montecarlo.analyse`.
- **Una mejora sin medida previa no es una mejora.** Y una que no demuestra que los números que
  deciden siguen siendo los mismos, tampoco.
- **Las propuestas de borrado son propuestas.** Nada bajo `~/Desktop/AlgoData` se borra sin el dueño.
