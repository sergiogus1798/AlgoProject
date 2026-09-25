---
name: wfm
description: Configure and run the Walk Forward Matrix task of a custom SQX project — the 30-cell grid over a window that ends in the reserved oos2, the ten per-cell conditions and the area rule that decide whether a strategy survives, and the two owner's rules it enforces (every look spends the window, and nothing is read until steps 17, 18 and 19 are all done). Use when the owner asks to set up, configure or run the WFM or walk-forward matrix in SQX, or step 19 of the workflow.
---

# /wfm

Paso 19 del workflow, y **el último paso que mira datos**. Deja la tarea `WFM` de un custom project
configurada y lista para correr. Leerla es `strategies/walkForwardMatrix/` — y eso ya es el paso 20,
que va ciego hasta que el 17, el 18 y el 19 estén los tres hechos.

## Las dos reglas del dueño que este comando hace cumplir

**1. Acaba en `oos2`, y `oos2` es una puerta de un solo sentido.** La ventana es `build..oos2` —el
walk-forward necesita histórico delante para optimizar—, y lo que se gasta es la cola:
`assets/_policy.yaml` la reserva para el WFC y la WFM; `sqx/projects/configure.py` **aborta** si se lo pides para cualquier
otra cosa. Esta tarea es la excepción, porque es aquello para lo que está reservado. Cada mirada lo
gasta y no se repite: del 7 al 16 se mira `oos1` una y otra vez, así que al llegar aquí es lo único
virgen que queda.

**2. No se LEE hasta que 17, 18 y 19 estén los tres hechos.** Si se leen el WFC y el CSCV antes de
decidir si se corre la WFM —y con qué parámetros—, esa decisión ya está contaminada por lo visto, y
la última bala se gasta en un test elegido a posteriori. El comando lo canta en cada ejecución;
forzarlo de verdad es trabajo del ledger, que todavía no existe (`WORKFLOW.md`).

Si el dueño pide correr la WFM y el 17 o el 18 no están hechos: **decírselo y preguntar**, no
correrla. Es la única muestra que queda.

## Qué escribe

30 celdas: 5 porcentajes de fuera de muestra (20→40 de 5 en 5) × 6 números de pasadas (6→16 de 2 en
2), `MaxTests` 5.000 por paso, ±35 % en pasos del 4 % (`maxSteps=18`), sólo los parámetros
**recomendados** por SQX, precisión 2, fidelidad `exact_is_exact_oos` —el "Walk-Forward type" de la
GUI: cada paso hace su propia optimización real sobre su ventana, no un recorte— y la ventana
`build..oos2` tanto en los `<Setup>` como en `<Resources><Symbol>`.

El reparto entre los dos mandos es deliberado (dueño, 2026-09-24): `MaxTests` bajó de 15.000 a 5.000
porque compra una elección mejor por paso y nada legible después, mientras que `wf_type` cambia lo
que significa el número que sí se guarda.

⚠️ **Se cobra a `oos1`, no al último tramo** (`wfm.costs_segment`, decisión del dueño 2026-09-24):
son 18,7 años de los que `oos2` es la cola de 3,7. Es la excepción a la convención de los spans, y
el comando lo canta en su salida. Hoy `oos1` y `oos2` comparten spread, así que el número no cambia.

Y el criterio, que es lo que la tarea del maestro no tenía: **diez condiciones por casilla**, una
casilla aprueba con el 80 % de ellas cumplidas, y la estrategia aprueba si hay un rectángulo de 4x4
casillas con 12 aprobadas. Están en `assets/_build.yaml`, `wfm.conditions`, con el % de las 150
casillas reales del maestro que cumple cada umbral al lado; la disección de las fórmulas de SQX está
en `knowhow/conditions/wfm-acceptance.md`.

⚠️ **Con condiciones activas esto FILTRA**: SQX descarta a quien no encuentre el área y no lo
escribe en el databank de salida, al margen de `DeleteFailedStrategies`. Es la excepción a "el
veredicto se toma en Python". Para el modo mapa —puntuar las 30 casillas sin tirar a nadie—,
`min_squares: 0`.

Cuenta la factura antes de lanzar: 5.000 backtests por paso × 6–16 pasos por celda × 30 celdas ×
estrategia, a precisión 2. La WFM del maestro terminó con 500 sobre cinco años.

## Correrlo

```bash
python3 -m core.assets <SIMBOLO>                       # preflight, BLOQUEANTE
python3 -m sqx.projects.wfm <SIMBOLO> \
    --cfx <install>/user/projects/<PROYECTO>/project.cfx --input <databank>
```

`--input` son los supervivientes que han llegado al paso 19 y no tiene default.

El proyecto tiene que llevar la tarea titulada `WFM`, que viene del donante congelado: si no la
lleva, el comando se niega en vez de fabricarla — el bloque y sus condiciones vienen de una tarea
que escribió SQX. Y el `.cfx` no puede estar abierto por una instancia (regla dura 4).

Después, en el custodio, una sola cosa a la vez, y avisando antes de tocar W2 (`ListAgents`,
`ls -lt user/projects`, el log — el `stop` mata lo de cualquier sesión):

`<PROYECTO>` es el del workflow (`/template-run --workflow`): el comando de arriba deja su paso
como **el único activo**, porque `action=start` corre todas las tareas activas. El `stop` antes del
`start` no sobra: en un proyecto que ya corrió, un segundo `start` sin él no hace nada, en silencio.

```bash
bin/sqx-worker.sh --role custodian start
python3 -c "from core import worker; worker.call('-project action=stop name=<PROYECTO>','custodian')"
python3 -c "from core import worker; worker.call('-project action=start name=<PROYECTO>','custodian')"
# mientras corre, sólo -project action=status; el final es `Project finished` en el log de SQX
bin/sqx-worker.sh --role custodian stop
```

## Qué mirar en la salida

- **Las fechas.** Tienen que ser las de `oos2` (2023.01.01→2026.08.30 en XAUUSD). Si aparece
  2018–2022, la tarea está releyendo la muestra gastada y no es fuera de muestra de nada.
- **`30 celdas`.** Otro número significa que alguien tocó los ejes en `_build.yaml`: no es un error,
  es un estudio distinto.
- **`13 del donante apagadas y 10 propias escritas`** — el 13 es lo normal en un clon del donante y
  un 0 avisa de que ese `.cfx` no viene de él. Si el segundo número no es el de `wfm.conditions`, la
  matriz juzga con otra cosa.
- **`⚠️ ESTO FILTRA`** — con `min_squares` distinto de 0 la tarea tira estrategias.
- **`⚠️ esta tarea corre ademas: …`** — ese `.cfx` no pasó por la doctrina y correría otros
  crosschecks a la vez, cada uno con su factura.

⚠️ La ventana entera son 18,7 años en XAUUSD, de los que `oos2` es la cola de 3,7. Con 16 pasadas
cada tramo fuera de muestra ronda el año; con 6, tres años y medio. Mirarlo antes de leer una
correlación por celda. En un activo con `oos2: {from: null}` no hay ventana y el comando
revienta, que es lo correcto.

## Dónde se cambia qué

| qué | dónde |
|---|---|
| los dos ejes, `MaxTests`, ±% y el paso, precisión, la ventana | `assets/_build.yaml`, bloque `wfm:` |
| la fidelidad del walk-forward (`type`) | `assets/_build.yaml`, `wfm.wf_type` |
| el criterio por casilla y el área que ha de encontrar | `assets/_build.yaml`, `wfm.conditions`, `threshold_pct`, `grid_passing_size`, `min_squares` |
| qué tramo es `oos2` en cada activo | `assets/_policy.yaml`, `segments:` |
| el título `WFM` | **contrato** con el donante y con `export_wfm` |

Exportar desde un worker: `python3 -m sqx.export.export_wfm --project <P> --databank WFM --role custodian`.

Medido el 2026-09-25 sobre 3 madres de USDJPY H1 (`knowhow/sqx-drive/wfm-end-to-end.md`): la matriz, ~4-5 min
por madre y un JVM de 45 GB; export 20 s; análisis 2 s. **SQX no da ninguna señal de avance** mientras
corre: `Running time 0 ms` y el databank quieto hasta que termina cada madre.

Manual: `docs/manual/34-wfm.md`. Exportar: `docs/manual/09-wfm.md`. Leerlo:
`docs/manual/14-walkforwardmatrix.md`.
