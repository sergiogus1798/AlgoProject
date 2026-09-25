---
name: mcretest
description: Configure the eight MC Retest tasks of a custom SQX project — one perturbation each, the asset's own ranges, acceptance silenced, and the MinDistance task only when the population trades with stop or limit orders. Use when the owner asks to set up, configure or prepare the MC Retest in SQX, the MCR tasks, or the step 13 of the workflow.
---

# /mcretest

Paso 13 del workflow, la mitad de SQX. Deja las ocho tareas MC Retest de un custom project
configuradas y listas para correr. Leer lo que producen es `strategies/retest/`
(paso 14), y el Monte Carlo que reordena operaciones está FUERA del workflow a propósito.

## Lo único que hay que entender antes

Las ocho tareas existen para **atribuir**, no para filtrar. Cada una perturba una sola cosa, así
que cuando una estrategia se cae se sabe de qué dependía: del coste de entrar, del relleno, de sus
propios parámetros o del histórico exacto que le tocó ver.

Eso impone dos cosas, y las dos las escribe el comando:

- **Un solo método activo por tarea** (seis en la de estrés). Una tarea que mueve dos cosas no
  puede atribuir el daño a ninguna, y `strategies/retest/` se niega a ingerir su databank.
- **Condiciones de aceptación apagadas.** Con ellas vivas SQX borra lo que falla y cada tarea
  encadena en la siguiente: al final sólo sabes cuántas sobrevivieron. El veredicto se toma en
  Python y se aplica con `/curate`.

Por eso **las ocho leen el mismo databank**: son ocho lecturas de una población, no un embudo.

## La regla de MinDist — del dueño, 2026-09-23

`MCR 4 MinDist` **sólo** se configura si la población lleva órdenes **stop o limit**. La distancia
mínima es lo cerca del precio que el bróker deja poner una orden pendiente; con entradas a mercado
no hay ninguna, y la tarea sortearía mil veces un número que nadie lee.

El comando lo resuelve solo y dice de dónde sale la respuesta:

| fuente | cuándo | qué vale |
|---|---|---|
| `population` | el databank ya existe | abre los `.sqx` y mira qué órdenes usan. Es la respuesta buena |
| `generator` → `no` | no hay población y el builder no puede emitir pendientes | seguro: lo que no se puede generar no está |
| `generator` → `SIN RESOLVER` | no hay población y el builder **sí** puede | no se inventa: la tarea se queda sin configurar y hay que repasarlo tras el build |

Dentro de `MCR 8 Stress` pasa lo mismo con su método de distancia mínima: se cae ese método y la
tarea se escribe con los otros cinco. La condición es del método, no de la tarea.

## Correrlo

```bash
python3 -m core.assets <SIMBOLO>                       # preflight, BLOQUEANTE
python3 -m sqx.projects.mcretest <SIMBOLO> \
    --cfx <install>/user/projects/<PROYECTO>/project.cfx --input <databank>
```

`--input` es la población que se perturba y no tiene default: preguntar al dueño cuál es si no está
claro por el paso anterior (normalmente los supervivientes de `/oos-gate`, `/crossmarket` o
`/crosstf`).

Antes de escribir: **el `.cfx` no puede estar abierto por una instancia** — SQX lo reescribe al
salir (regla dura 4). El comando se niega y dice qué parar.

`<PROYECTO>` es el del workflow (`/template-run --workflow`): ya lleva las ocho tareas. El comando
las deja como **las únicas activas**, menos las que no pudo configurar (`⊘`), que se quedan
apagadas. Correrlo, en el custodio y una sola cosa a la vez (antes, `ListAgents`,
`ls -lt <install>/user/projects` y el log: el `stop` mata lo de cualquier sesión):

```bash
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=stop name=<PROYECTO>','custodian')"
python3 -c "from core import worker; worker.call('-project action=start name=<PROYECTO>','custodian')"
# mientras corre, sólo -project action=status; el final es `Project finished` en el log de SQX
bin/sqx-worker.sh --role custodian stop
```

## Qué mirar en la salida

- La línea de `ordenes`: de dónde salió el veredicto de pendientes, y cuántas estrategias se leyeron.
- Un `⊘` por tarea no configurada, **con el motivo**. Las dos razones legítimas son "no hay órdenes
  pendientes" y "rango sin decidir en `assets/symbols/`". Cualquier otra cosa es un proyecto mal
  clonado.
- `condicion(es) apagada(s)` distinto de cero en cada tarea escrita: si sale 0 en todas, el donante
  ya las traía apagadas y conviene comprobarlo.

## Dónde se cambia qué

| qué | dónde |
|---|---|
| qué perturba cada tarea, y su `simulations`, `precision` y `segment` propios | `assets/_build.yaml`, bloque `mc_retest:`. Cada tarea lleva los suyos |
| `precision` | `1` = timeframe elegido, rápido y grosero · `2` = un minuto, lento y fino. Va al revés de lo que sugiere la palabra, y el 2 cuesta el doble (medido) |
| `segment` | `build` un tramo · `build..oos1` **dos puntos**, una ventana continua que abarca los dos, cobrada al coste del último. `oos2` está prohibido y el comando se niega |
| entre qué dos valores se sortea spread, slippage y distancia mínima | `assets/symbols/<SIMBOLO>.yaml`, bloque `mc_retest:` |
| los títulos de las ocho tareas | **contrato** con `strategies/retest/inputs/tasks.py`. Cambiarlos rompe el paso 14 en silencio |

Manual: `docs/manual/32-mcretest.md`. Lectura de resultados: `docs/manual/11-retest-mc.md`.
