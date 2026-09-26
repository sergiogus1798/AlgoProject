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

## La tanda de validación — los seis del PDF `IMPROVEMENTS`, 2026-09-24

Salen de la revisión del PDF del dueño. **El 8 es el cimiento y va primero**: los otros cinco
escriben en él.

| fichero | qué construye | depende de |
|---|---|---|
| `8-ledger-global.md` | ✅ **construido el 2026-09-24** salvo la migración de umbrales; ver su §ESTADO | — |
| `9-monos-de-punta-a-punta.md` | el control negativo: 10.000 monos por los 20 pasos, y cuántos llegan | 8 |
| `10-spa-stepm.md` | SPA de Hansen y StepM de Romano–Wolf sobre la población superviviente | 8 · gate |
| `11-edge-por-coste.md` | edge en unidades de spread y coste de breakeven | 8 |
| `13-alfa-beta.md` | **interrogante aparcado**, no encargo: nadie lo coge hasta cerrar la secuencia individual | — |

## La tanda del PDF `PARAMETER_SPACE_TESTS`, 2026-09-24

Del PDF del dueño sobre la nube de clones. Lo implementable **ya está implementado** y vive en
`studies/optimisation/cloud/` (A1, A2, A3, B2, C1) y en `engines/nulls/filter.py` (la mitad del D1 que no
necesita SQX). Aquí quedan los dos que exigen cosas que hoy no tenemos:

| fichero | qué construye | qué lo bloquea |
|---|---|---|
| `12-tests-estructurales.md` | ablación de reglas, inversión de señal y el mono dentro de SQX | hace falta editar la *lógica* del `.sqx`; la ruta XML ya está investigada dentro |
| `15-superficies-multimercado.md` | una superficie de parámetros por mercado, y si la región buena coincide | los costes de 16 activos (`OPEN.md` §27) y CPU del custodio |

**Orden recomendado: 8 → 10 → 11 → 9**, y el 8 ya está. Los tres primeros leen de la misma cosecha que la puerta ya
hace y no gastan CPU de SQX.

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

## Perfilado de la capa de Python, 2026-09-24

| fichero | qué construye | estado de partida |
|---|---|---|
| `18-profiling-python.md` | perfilar y optimizar los análisis de Python, con la población de 500 ya construida y medida | 11 de 23 módulos medidos, dos puntos calientes localizados con línea, y la paralelización del crossmarket como único cambio de 90x |

Es el único encargo que **ya trae sus propias medidas**: lo que hay dentro no son hipótesis, son
números con su método al lado, incluidas **dos optimizaciones que se probaron y no funcionan**, para
que nadie las repita.

## La tanda del PDF `TRADE_LEVEL_TESTS`, 2026-09-24

Siete tests sobre listas de operaciones y datos M1, ninguno necesita SQX. **Cinco están
construidos** — `studies/readings/profitShape/` (items 1, 2 y 7) y `studies/readings/entryQuality/` (item 3 y
el tier 1 del 4). Quedan tres:

| fichero | qué construye | qué lo bloquea |
|---|---|---|
| `16-replay-de-operaciones.md` | el tier 2 del retraso: reejecutar cada operación desde una entrada desplazada | hay que recalcular stops, y **esta población no tiene ninguno** con el que validarlo |
| `17-calidad-del-feed.md` | anomalías del M1 y qué parte del beneficio las toca | los umbrales `K`, `m`, `L`, `w` son del dueño |
| `14-mapa-condicional.md` | rendimiento por régimen, sesión y día | nada técnico; va el último **a propósito**: es el único que fabrica hipótesis |

## El stop loss para MT5, 2026-09-25

| fichero | qué construye | qué lo bloquea |
|---|---|---|
| `20-atr-calculator.md` | el paso 22: el stop X·ATR de cada superviviente, leído del MAE de sus operaciones, **sin optimizar** — MT5 lo exige y la cadena genera sin stop | injertar un stop ATR en un `.sqx` que no lo tiene (sin investigar); decisiones del dueño cerradas; y hace falta alguna superviviente |

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

> Lee `docs/encargos/8-ledger-global.md` y ejecútalo entero. Es tu encargo completo: no necesitas
> leer el plan grande ni los otros encargos. Si algo te bloquea, párate y dímelo.

## Protocolo anticolisión

Tres ficheros son compartidos y los tocan varios agentes:

- **`docs/DEPENDENCIES.md` se regenera, nunca se fusiona.** Si hay conflicto, `python3
  tools/depmap.py` y se queda lo que salga.
- **`requirements.txt`: se añade línea, nunca se reordena.**
- **`ledger/thresholds.yaml` (encargo 8) lo leen todos y no lo escribe ninguno.** Mover un umbral
  es del dueño.

## Qué devuelve cada agente

Todos cierran igual: **qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por
qué · qué descubrió que merezca ir a `knowhow/`.**

## Idioma

Español, como el resto de `docs/` cuyo lector es el dueño. El código, los `README.md` de carpetas de
código y `knowhow/` siguen en inglés (`CLAUDE.md`).
