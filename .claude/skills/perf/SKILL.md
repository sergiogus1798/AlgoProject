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

## Sin argumento — la revisión completa

Launch **`perf-profiler`** and **`perf-storage`** in the background, in parallel. They do not share
state: one measures code, the other measures disk. When both return:

1. Read the profiler's regressions and the storage review's proposals.
2. Give the owner, in Spanish: the regressions with their cause, how close the heaviest target is to
   not fitting in memory, and **the single change with the best measured prize per unit of work**.
3. Ask whether to build that one. Only on a yes, launch `perf-optimizer` with the target named.

Never launch the optimizer without the owner saying which change. Choosing what to optimise is his
call; measuring what it would be worth is yours.

## `/perf catalogo` — sólo medir

`perf-profiler`. Measures, updates `history.csv`, renders the page, explains what moved.

Check the machine is idle first — `uptime`, `free -g`, and orphaned worker pools — because a
measurement taken on a busy machine goes into an append-only file and stays wrong forever.

## `/perf datos` — sólo el disco

`perf-storage`. Inventory, duplicates, format costs, proposals. Read-only over the data root.

## `/perf mejorar <módulo>` — idear y codear

`perf-optimizer`, on the named module. It measures on master, branches, changes **one** thing,
proves the output did not change, measures again, and stops with the branch unmerged. Report the two
numbers and the branch name. The merge is the owner's.

If the module has no target in `perf/inputs/targets.py`, the optimizer's first commit adds one —
without a before, there is no after.

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
