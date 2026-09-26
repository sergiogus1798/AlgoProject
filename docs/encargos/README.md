# docs/encargos — un fichero por instancia de agente

Cada fichero de esta carpeta es **un encargo autocontenido**: lo que una sola instancia necesita
para hacer su parte, y nada más. Se despacha diciéndole al agente que lea **su** fichero, no el
plan entero.

El plan completo vive en `docs/AgentPDFs/plan-ejecucion-2026-09-21.md` y la secuencia manda desde
`docs/AgentPDFs/WORKFLOW.md`. **Los encargos son la versión ejecutable de una parte de ellos.**
Donde discrepen, manda el WORKFLOW — y se arregla el encargo.

**Un encargo cumplido se borra.** No se marca como hecho ni se deja «por si acaso»: lo que se
aprendió haciéndolo ya está en `knowhow/`, en el manual y en el código. Limpieza del 2026-09-24:
salieron los encargos 1, 2, 3, 4 y 7, verificados uno a uno contra el repositorio. El 25-09 salió
el 19 (el contrato de datos de la ventana): vive en `core/study/CONTRACT.md` y `studies/CLAUDE.md`.
Y el 18 (perfilado de Python): hecho en los commits `c9011a2` y `3923010`; lo que no pudo medirse
porque gasta `oos2` está en `OPEN.md` §42. El 26-09, en una tanda de cinco frentes en paralelo con
un revisor detrás de cada uno, salieron el **8** (los 19 umbrales se leen de `ledger/thresholds.yaml`),
el **11** (`studies/readings/edgeCost/`, pasos 8 y 25), el **12** (`sqx/structural/` +
`studies/readings/structure/`, paso 23; el mono dentro de SQX es imposible,
`knowhow/conditions/no-seeded-hash-in-sqx.md`), el **14** (`studies/readings/conditionalMap/`, paso 22)
y el **15** (`studies/optimisation/marketSurfaces/`, paso 18.5). Lo que dejaron abierto está en
`OPEN.md` §43–§48.

## La tanda de validación — los seis del PDF `IMPROVEMENTS`, 2026-09-24

Salen de la revisión del PDF del dueño. **El 8 es el cimiento y va primero**: los otros cinco
escriben en él.

| fichero | qué construye | depende de |
|---|---|---|
| `9-monos-de-punta-a-punta.md` | el control negativo: 10.000 monos por los 25 pasos, y cuántos llegan. **No se implementa por ahora** (dueño, 2026-09-26) | — |
| `10-spa-stepm.md` | ✅ **parte A construida el 2026-09-25** (detrás de la puerta, anota); queda la B, la prueba ciega del paso 20, que espera a una población que llegue allí | gate |
| `13-alfa-beta.md` | **interrogante aparcado**, no encargo: nadie lo coge hasta cerrar la secuencia individual | — |

## La tanda del PDF `PARAMETER_SPACE_TESTS`, 2026-09-24

Del PDF del dueño sobre la nube de clones. Lo implementable **ya está implementado** y vive en
`studies/optimisation/cloud/` (A1, A2, A3, B2, C1) y en `engines/nulls/filter.py` (la mitad del D1 que no
necesita SQX). Los dos que quedaban —el 12 y el 15— se construyeron el 2026-09-26.

**El punto 5 del PDF (perturbación de zona horaria) se ha retirado.** Decisión del dueño,
2026-09-24: no le sirve. Su encargo se ha borrado.

**El punto 6 se ha convertido en otra cosa y ya está construido.** En vez de la descomposición
alfa/beta, el dueño pidió medir la dicotomía **rendimiento contra exposición al mercado** — una
estrategia que saca un 5 % estando dentro una hora a la semana contra un buy and hold que saca un
10 % estando dentro siempre. Es `studies/closing/exposure/`, el **paso 21** del `WORKFLOW.md`, con su
página de manual `docs/manual/38-exposicion.md`. La alfa y la beta quedan como interrogante dentro
de esa misma carpeta, en `13-alfa-beta.md`.

**El punto 2 del PDF (permutaciones de Masters) no tiene encargo propio, a propósito.** Se
investigó: la API de SQX no tiene verbo de import, el almacén de datos está compartido por symlink
con el maestro y `strategies/translate/` está vacío. El encargo 9 responde la misma pregunta —la
tasa de falsos positivos de la cadena— con la maquinaria de monos que ya existe. Decisión del
dueño, 2026-09-24: **«monos se ha dicho»**.

## La tanda del PDF `TRADE_LEVEL_TESTS`, 2026-09-24

Siete tests sobre listas de operaciones y datos M1, ninguno necesita SQX. **Seis están
construidos** — `studies/readings/profitShape/` (items 1, 2 y 7), `studies/readings/entryQuality/` (item 3 y
el tier 1 del 4) y `studies/readings/conditionalMap/` (item 6, paso 22). Quedan dos:

| fichero | qué construye | qué lo bloquea |
|---|---|---|
| `16-replay-de-operaciones.md` | el tier 2 del retraso: reejecutar cada operación desde una entrada desplazada | hay que recalcular stops, y **esta población no tiene ninguno** con el que validarlo |
| `17-calidad-del-feed.md` | anomalías del M1 y qué parte del beneficio las toca: detección como aviso en el paso 4, atribución como criba en el 8 | **en pausa**: sus umbrales están en consulta, `docs/AgentPDFs/consulta-calidad-del-feed-2026-09-26.md` |

## El stop loss para MT5, 2026-09-25

| fichero | qué construye | qué lo bloquea |
|---|---|---|
| `20-atr-calculator.md` | el paso 24 (era el 22 antes del 26-09): el stop X·ATR de cada superviviente, leído del MAE de sus operaciones, **sin optimizar** — MT5 lo exige y la cadena genera sin stop | ✅ construido y probado en SQX (rama `feat/atr-calculator`, sin fusionar); falta correrlo sobre una superviviente real |

## Encargos vivos de tandas anteriores

| fichero | agente | posee | estado |
|---|---|---|---|
| `6-taxonomia-bloques.md` | etiquetador | **solo el campo `archetypes` de `sqx/blocks/taxonomy.yaml`** | 🔴 sin empezar: los 767 bloques siguen con `archetypes: {}` |

No toca código, no toca SQX, no gasta CPU. Se puede lanzar en paralelo con cualquier otra cosa.
Su hermano, el encargo 7 (las tres paletas por defecto), **está hecho** — 180 / 177 / 148 bloques
nombrados con `unlabelled: off` — y por eso ya no está aquí.

## Lo que no es un encargo

| fichero | qué es |
|---|---|
| `5-nulos.md` | informe de cierre del módulo `studies/readings/monkey/`, con cinco cosas pendientes en su §6. Se queda hasta que esas cinco estén resueltas o descartadas |
| `CONTEXTO-curacion-de-poblaciones.md` | estado del terreno para quien diseñe la curación desde la UI |
| `CONTEXTO-ecosistema-skills-sqx.md` | estado del terreno para quien diseñe skills de SQX |
| `ejemplo-IS-OOS-XAUUSD.md` | el proyecto de ejemplo con IS y OOS en dos databanks, citado desde `docs/manual/28-builder.md` |

## Cómo se despacha

> Lee `docs/encargos/16-replay-de-operaciones.md` y ejecútalo entero. Es tu encargo completo: no necesitas
> leer el plan grande ni los otros encargos. Si algo te bloquea, párate y dímelo.

## Protocolo anticolisión

Tres ficheros son compartidos y los tocan varios agentes:

- **`docs/DEPENDENCIES.md` se regenera, nunca se fusiona.** Si hay conflicto, `python3
  tools/depmap.py` y se queda lo que salga.
- **`requirements.txt`: se añade línea, nunca se reordena.**
- **`ledger/thresholds.yaml`: un módulo nuevo añade sus filas al final de su sección y lee el valor
  con `ledger:<clave>`** (`knowhow/eng/thresholds-live-in-the-ledger.md`). Mover un umbral es del dueño.

## Qué devuelve cada agente

Todos cierran igual: **qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por
qué · qué descubrió que merezca ir a `knowhow/`.**

## Idioma

Español, como el resto de `docs/` cuyo lector es el dueño. El código, los `README.md` de carpetas de
código y `knowhow/` siguen en inglés (`CLAUDE.md`).
