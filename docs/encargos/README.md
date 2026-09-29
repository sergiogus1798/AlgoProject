# docs/encargos — un fichero por instancia de agente

Cada fichero de esta carpeta es **un encargo autocontenido**: lo que una sola instancia necesita
para hacer su parte, y nada más. Se despacha diciéndole al agente que lea **su** fichero, no el
plan entero.

La secuencia manda desde `docs/AgentPDFs/WORKFLOW.md`. **Los encargos son la versión ejecutable de una parte de ellos.**
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
`OPEN.md` §43–§48. Y en la limpieza de `docs/` del mismo día salió el **21** (la prueba
del workflow entero): su informe es `docs/AgentPDFs/profiling-workflow-2026-09-26.md`. Con él
salieron el ejemplo USDJPY del 24-09, al que ese informe supera, y los dos `CONTEXTO-*`: las
skills de SQX y `/curate` ya existen. Ese mismo día salieron también el **20** (el ATR calculator,
paso 24: lo que decía vive en `docs/manual/10-cierre.pdf`, cap. 54-atr-calculator) y la ficha del
proyecto de ejemplo IS/OOS, que ahora es `knowhow/locations/xau-isoos-example-project.md`.

## La tanda de validación — los seis del PDF `IMPROVEMENTS`, 2026-09-24

Salen de la revisión del PDF del dueño. **El 8 es el cimiento y va primero**: los otros cinco
escriben en él.

| fichero | qué construye | depende de |
|---|---|---|
| `9-monos-de-punta-a-punta.md` | el control negativo: 10.000 monos por los 25 pasos, y cuántos llegan. **No se implementa por ahora** (dueño, 2026-09-26) | — |
| `10-spa-stepm.md` | ✅ **A (2026-09-25) y B (2026-09-26) construidas**: la B es el paso 20, `studies/closing/blindJoint/`, corrida sobre USDJPY (ninguna madre pasa). Quedan tres decisiones del dueño: qué es pasar el 20, si el 20 puede leer `oos2`, y el CSCV leyendo `oos2` fuera de la política | gate |
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
página de manual `docs/manual/10-cierre.pdf` (cap. 38-exposicion). La alfa y la beta quedan como interrogante dentro
de esa misma carpeta, en `13-alfa-beta.md`.

**El punto 2 del PDF (permutaciones de Masters) no tiene encargo propio, a propósito.** Se
investigó: la API de SQX no tiene verbo de import, el almacén de datos está compartido por symlink
con el maestro y `strategies/translate/` está vacío. El encargo 9 responde la misma pregunta —la
tasa de falsos positivos de la cadena— con la maquinaria de monos que ya existe. Decisión del
dueño, 2026-09-24: **«monos se ha dicho»**.

## La tanda del PDF `TRADE_LEVEL_TESTS`, 2026-09-24

Siete tests sobre listas de operaciones y datos M1, ninguno necesita SQX. **Seis están
construidos** — `studies/readings/profitShape/` (items 1, 2 y 7), `studies/readings/entryQuality/` (item 3 y
el tier 1 del 4), `studies/readings/conditionalMap/` (item 6, paso 22) y, el 2026-09-26,
`studies/data/feedQuality/` (item 5, el **17**: calidad del feed, pasos 4 y 8, sobre las respuestas
del dueño a las 16 decisiones; lo que quedó abierto está en su `POSSIBLE_IMPROVEMENTS.md`). Queda uno:

| fichero | qué construye | qué lo bloquea |
|---|---|---|
| `16-replay-de-operaciones.md` | el tier 2 del retraso: reejecutar cada operación desde una entrada desplazada | hay que recalcular stops, y **esta población no tiene ninguno** con el que validarlo |

## El rediseño de la ventana, 2026-09-27 — retirado el 2026-09-28

Los encargos **22** (rediseño de la ventana), **23** (archivo de estrategias) y el plan **24** que los
ejecutó se retiraron el 2026-09-28: 21 frentes en cuatro olas, cada uno con un revisor detrás, y una
auditoría final contra los dos encargos. Lo que enseñaron vive en `ui/README.md` (las zonas y las
seis decisiones del dueño), `core/archive/README.md`, `docs/manual/02-la-ventana.pdf`, `knowhow/`
(eng, locations, sqx-drive, research) y `OPEN.md` §81-§82 (las decisiones que quedan en manos del
dueño y la prueba en vivo de «Continuar workflow», pendiente de su autorización).

## La tanda de las ideas de internet y de los libros, 2026-09-28

Salen del dossier `docs/AgentPDFs/ideas-de-internet-y-libros-2026-09-27.md`, elegidas por el dueño.

| fichero | qué construye | depende de |
|---|---|---|
| `27-criba-mae-profundo.md` | en el paso 8, sobre `build` y `oos1`: qué estrategias viven de operaciones anómalas, las que se fueron 3-4 ATR en contra y además duraron más de media + 2,5 desviaciones (dueño, 2026-09-28); marca antes de que el paso 24 dé sorpresas | — |
| `28-hueco-aleatorio-a-prueba.md` | ¿aporta el hueco aleatorio de SQX? A: A/B fija contra fija + hueco, automatizado con la skill `/ab-hueco`; B: atribución fija contra hueco en el paso 23; C: bloque de ruido y barrido de complejidad | el custodio libre para A y C |
| `29-meseta-en-el-tiempo.md` | la región buena de parámetros, ¿en el mismo sitio en `build`, `oos1` y `oos2` por separado? Ampliación del paso 18.5, de mercado contra mercado a tramo contra tramo; y la tabla que dirá si la meseta predice supervivencia | un lote de variantes retesteado; lectura ciega del paso 20 |
| `30-monos-seleccionados-en-sqx.md` | monos de entrada aleatoria construidos y seleccionados por el Builder de SQX con el bloque RAND, pasados por la cadena real: la tasa de falsos positivos con la selección incluida. Construye además `RandomEntrySeeded`, el bloque con semilla. Reabierto por el dueño el 2026-09-28 | instalar los bloques en el custodio; 28 C depende de él |
| `31-mapa-ventaja-sobre-el-mono.md` | una capa nueva del paso 18.5: la rejilla mercado × parámetro coloreada por la ventaja sobre el mono de cada celda, no por el beneficio neto, con corrección por pruebas múltiples. Necesita exportar operaciones del lote por mercado: medir antes lo que cuesta | un lote de variantes retesteado en los mercados; un worker libre para el export |
| `32-registrar-todo-lo-probado.md` | que todo barrido de parámetros, umbrales o configuraciones deje escrito lo que probó y cuál eligió: contrato L2 del ledger, detección de reejecuciones con `--set`, orden `ledger.tried` para barridos a mano y procedencia de cada idea; el N del Sharpe deflactado lo usa | — |
| `33-economia-del-fondeo.md` | el fondeo como flujo de caja banco ↔ empresa: catálogo de planes y add-ons extraído (Hantec ya, 44 planes), reglas como máquina de estados sobre equity flotante, ciclo compra → fases → fondeada → cobros simulado por bloques, contra el mono y con recorte del edge; devuelve qué plan, add-ons y riesgo comprar. Contesta `portfolio/DECISIONS.md` #6 | una cartera en el archivo; los huecos del catálogo confirmados por el dueño |

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
