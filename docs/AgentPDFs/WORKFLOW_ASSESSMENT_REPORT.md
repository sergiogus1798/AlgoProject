# Evaluación y optimización del workflow (pasos 6 a 25)

2026-10-05 · Nikkei 225, M30, Simple Strategy largos · custodio `SQX_w2` · modo de prueba (`--smoke`), semilla fija 20261004

## 1. En una frase

El workflow entero, del paso 6 al 25, ha pasado de **230 minutos a 159** (−31 %) y ahora corre **de principio a fin con un solo comando, sin intervención y sin fallos**. Con los dos arreglos encontrados en el último run, que están aplicados y probados por separado pero no medidos juntos en un run completo, la estimación es de **unos 140 minutos**. Los cálculos de SQX y de los estudios no se han tocado: todo el ahorro sale de lo que rodea a SQX (abrirlo, cerrarlo, cargar, exportar, esperar).

| ejecución | qué es | minutos | intervenciones a mano |
|---|---|---|---|
| referencia (`_ref`) | el workflow como estaba el 4 de octubre | 230,2 | 4 relanzamientos por fallos |
| fase 4 (`_auto`) | mismas optimizaciones, SQX abriendo y cerrando en cada paso | 214,5 | ninguna |
| sesión única (`_live`) | SQX se abre una vez y se queda abierto todo el run | 160,1 | ninguna |
| **run final (`_fin`)** | lo anterior más el export corregido; lanzado con el comando tal cual queda | **159,4** | ninguna |
| estimación con los dos últimos arreglos | reabrir SQX antes de SPP y WFM; cierre final sin re-exportar | ≈140 | — |

El comando es `bin/workflow.sh` (apartado 6) y es **regla dura 19** del proyecto: el workflow se corre con él, nunca paso a paso a mano.

## 2. Antes y después, paso a paso

Segundos de reloj. «Referencia» es la suma de los cuatro lanzamientos que hicieron falta.

| paso | qué hace | referencia | fase 4 | sesión única | comentario |
|---|---|---|---|---|---|
| — | arrancar SQX (una vez) | — | — | 71 | en las otras rutas va repartido dentro de cada paso |
| 6+7 | construcción + OOS | 1.336 | 1.405 | 1.407 | casi todo es SQX calculando (≈1.215 s) |
| 8 | estudios sobre la población | 297 | 323 | 157 | el estudio de falsos positivos ahora usa todos los núcleos |
| 9 | mercados adicionales | 94 | 98 | 94 | 8 s de SQX; el resto era export (ya corregido, sin medir) |
| 10 | lectura | 8 | 7 | 7 | |
| 11 | otros marcos temporales | 113 | 108 | 136 | 4 s de SQX; el resto era export (ya corregido, sin medir) |
| 12 | lectura | 6 | 6 | 6 | |
| 13 | Monte Carlo (7 tareas) | 866 | 860 | 888 | SQX ≈790 s |
| 14 | lectura del Monte Carlo | 103 | 103 | 103 | |
| 15 | SPP IS + OOS | 880 | 970 | 1.489 | lento por la sesión con horas abierta; arreglado, ver §5.3 |
| 16 | lectura del SPP | 19 | 21 | 23 | |
| **16.5** | **variantes (10 madres × 500)** | **7.324** | **6.139** | **2.606** | **el gran ahorro: −79 minutos** |
| 17 | lectura | 17 | 17 | 4 | |
| 18 | lectura | 50 | 52 | 51 | |
| 18.5 | lectura a ciegas | 546 | 575 | 252 | sus pruebas corren ahora en paralelo |
| 19 | WFM | 1.348 | 1.466 | 1.884 | igual que el SPP; arreglado, ver §5.3 |
| 20-22 | lecturas | 35 | 37 | 38 | |
| 23 | pruebas estructurales | 260 | 184 | 70 | |
| 24 | parada y reprueba | 603 | 492 | 237 | |
| 25 | finalistas | 8 | 8 | 8 | |
| — | cerrar SQX y export final | — | — | 72 | |
| **total** | | **13.814 (230,2 min)** | **12.870 (214,5 min)** | **9.604 (160,1 min)** | |

## 3. SQX calculando frente a todo lo demás

| | referencia | sesión única |
|---|---|---|
| SQX calculando | ≈128 min | ≈125 min |
| todo lo demás | ≈102 min | ≈35 min |

En la referencia casi la mitad del tiempo se iba en cosas que no eran calcular. Ahora es alrededor de una quinta parte. (En la sesión única el reparto del paso 16.5 es aproximado: su tabla de tiempos no separa el cálculo de SQX del resto; la cifra sale de medir aparte que 500 variantes × 3 tareas tardan unos 215 s.)

Lo que SQX calcula no se puede acelerar sin cambiar los resultados (precisión, número de simulaciones, número de variantes). Eso no se ha tocado: es decisión tuya.

Dónde está lo que queda de «todo lo demás» (≈35 min):

1. Estudios de Python: ≈11 min (paso 8: 157 s; 14: 103 s; 18.5: 252 s; 18: 51 s).
2. Exports tras cada paso de SQX: 770 s (≈13 min) en el run medido; con la corrección de 910e2ad deberían bajar a unos 6 min.
3. Paso 16.5 fuera de SQX: ≈7 min (carga, volcado a disco, equity, collect).
4. Arrancar y cerrar SQX: 2,4 min.

## 4. Las optimizaciones, una por una

Cada una en su commit, para poder deshacerla sola.

| commit | qué cambia | efecto medido |
|---|---|---|
| e87b025 | **sesión única por defecto**: SQX se abre una vez; `--restart` es la marcha atrás | de 214,5 a 160,1 min en total |
| 77ec141, d42f474 | paso 16.5: los pilotos de todas las madres van primero, solo sobre el mercado principal y solo la tarea que leen | pilotos de 2.400 s a 105 s (mismos recuentos, 300 de 300) |
| 51c13c3 | las tres tareas de variantes vuelcan a disco a la vez | 17 MB/s frente a 9 |
| caccb79 | las paradas de tandas y pilotos ya no lanzan el export posterior | ≈62 s por parada, 20 paradas en la referencia |
| c5a2cc3, e33540b | sondeos cada 2-3 s en vez de 5-10 (los topes en segundos no cambian) | unos segundos por paso |
| 12cfb6a | la espera del volcado crece con el tamaño de la tanda | evita un fallo falso con tandas grandes |
| ebfbed9 | falsos positivos (paso 8): los «monos» de los donantes en todos los núcleos, mismos resultados y mismo orden | paso 8 de ≈320 s a ≈155 s |
| (sin commit, `blind.py`) | paso 18.5: las pruebas ligeras en paralelo | de 575 s a 252 s |
| 910e2ad | el export tras un paso lee solo el proyecto que corrió | exports del run de 770 s a 539 s (medido en el run final) |
| c6da321 | SQX se cierra y se reabre justo antes del SPP y del WFM | ≈8-10 min por paso, a cambio de ≈100 s; probado suelto, sin medir en run completo |
| 8c4c05b | el cierre final exporta solo el proyecto del run | ≈3,5 min; sin medir en run completo |
| f7ec276 | el volcado a disco espera mientras sigan llegando ficheros | permite madres de 5.000 variantes en una carga |
| d2854f5 | `bin/workflow.sh`, las skills `/workflow-simple` y `/workflow-template`, regla dura 19 | un comando para todo |
| bf3c257 | el log del día (452 MB) se lee desde el último arranque de proyecto, no desde medianoche | de 15 s a 0,4 s por lectura |
| bedd862, ffac0ff | la huella de las bases de 20 ficheros o más se calcula en todos los núcleos | segundos por export |
| 230c856 | la huella ya no cambia cuando SQX reordena un fichero interno | evita re-exportar bases que no han cambiado |
| 4679912, 71c8032, 3b0d539 | un aborto transitorio de SQX repite el paso una vez, quitando antes lo que el intento dejó a medias | quita los relanzamientos a mano de la referencia |
| 5a6321d, ceb6768 | `--smoke`: prueba funcional de un `Test_` (solo juzgan las reglas de legibilidad) | permite medir el workflow entero con pocas estrategias |
| c90c3b4 | tabla de tiempos por fase en cada run (`tiempos.md`) | es lo que ha permitido medir todo lo demás |

## 5. Problemas encontrados y qué se hizo

### 5.1 Corregidos

1. **Con las reglas reales, las 1.000 estrategias caían en el paso 8.** Para poder medir el workflow completo se añadió `--smoke`. Las reglas reales no se han tocado.
2. **SQX aborta solo de vez en cuando** (un fallo interno conocido). Antes había que relanzar a mano; ahora el paso se repite una vez. En la fase 3 ese reintento dejó estrategias duplicadas en la base de salida: ahora, antes de repetir, se quita lo que el intento fallido había añadido.
3. **Tras un aborto, el plan daba el paso 24 por hecho** y el 25 se rompía. Cubierto por el mismo reintento.
4. **El export tras cada paso recorría toda la instalación**, incluido `Trade_NIKKEI225_M30_volatilidadL` (solo lectura: no se modificó ni se borró nada de ese proyecto). Ahora lee solo el proyecto que acaba de correr.
5. **La espera del volcado de variantes era fija** y se quedaba corta con tandas grandes. Ahora crece con el tamaño.

### 5.2 Variantes: cuántas caben en una carga

En las pruebas cada madre lleva 500 variantes; en los runs reales serán unas 5.000. He probado si una madre real cabe entera en una carga (5.000 variantes × 3 tareas × 12 mercados):

| ruta | carga | resultado |
|---|---|---|
| antigua (`--restart`) | 2.500 | bien |
| antigua (`--restart`) | 5.000 | **pierde resultados**: 3.952 de 5.000 en la tarea IS, al azar. Causa sin encontrar |
| sesión única | 5.000 | **bien, dos veces**: 5.000 de 5.000 en las tres tareas, y los 15.000 ficheros en disco |

Una madre real en la sesión única cuesta: cargar 11 s, calcular 1.564-1.709 s (26-28 min), volcar a disco 206 s (3,6 GB), vaciar 11 s. En total **unos 32 minutos por madre**, de los que 28 son SQX calculando. La memoria de SQX llegó a 53 GB de sus 80: hay margen, y eso descarta que la pérdida de la ruta antigua fuese por falta de memoria.

**Decisión:** con la sesión única, una madre de 5.000 va entera en una carga, como proponías (cargar, correr las tres tareas seguidas, exportar todo). No hace falta partirla. Con `--restart`, no pasar de 2.500 por carga.

De paso apareció un fallo mío: la espera del volcado en la sesión única tenía un tope fijo de 120 s, corto para 3,6 GB. Ahora espera mientras sigan llegando ficheros (commit f7ec276).

No he probado juntar varias madres reales en una carga (10.000 o más): con 53 GB para 5.000 no cabrían dos.

### 5.3 SPP y WFM van lentos cuando SQX lleva horas abierto — arreglado

En los dos runs de sesión única, SPP y WFM tardaron bastante más que por la ruta antigua. Por la mañana lo atribuí a un análisis mío que ocupaba la máquina: **era un error**. En el run final no había nada mío corriendo y salieron igual de lentos.

Tiempo de SQX calculando, mismas estrategias y mismos núcleos:

| tarea | ruta antigua | sesión con horas abierta | sesión recién abierta |
|---|---|---|---|
| SPP IS | 530 s | 873 s y 894 s | 442 s y 466 s |
| WFM (mismo proyecto) | 1.222 s | 1.837 s | 1.275 s |

La sesión única no es el problema; lo es que lleve horas abierta y cargada. La causa dentro de SQX no la he encontrado (el log no muestra nada distinto). El arreglo: el autopiloto **cierra y vuelve a abrir SQX justo antes del SPP y antes del WFM** (commit c6da321). Cuesta unos 100 s cada vez y recupera unos 8-10 minutos en cada paso. Probado por el camino real del autopiloto con el SPP; **no medido aún dentro de un run completo**.

### 5.3 bis El cierre final tardó 243 s

Al cerrar SQX al final del run se volvía a exportar toda la instalación, incluido otro proyecto de prueba (229 s de los 243). Ahora exporta solo el proyecto del run (commit 8c4c05b). Tampoco medido aún en un run completo.

### 5.3 ter El log de SQX crece mucho

Cada WFM escribe 46.800 veces el mismo error interno de SQX (`ParameterCount`), por las dos rutas. Por eso el log del día llegó a 853 MB y el script de parada avisa de «tormenta de errores». No cambia tiempos ni resultados que yo haya visto, pero no he investigado qué columna deja de calcularse.

### 5.4 Sin resolver

- La base del SPP se vuelve a exportar en el paso 19 (15 s) aunque no ha cambiado.
- La guarda de la ingesta del Monte Carlo (paso 14) salta con poblaciones pequeñas: en modo prueba se le pasa su propia opción de tolerancia; con reglas reales sigue como estaba. **Decisión tuya** si esa regla debe depender del tamaño de la población.
- La construcción se corta por tiempo antes de llegar a 1.000 estrategias en algunos runs: el tope de tiempo y el objetivo no cuadran para este activo.

## 6. Cómo lanzarlo (para ti o para cualquier agente)

Un solo comando, desde `~/Desktop/AlgoProject`, con el custodio libre. Tres formas:

```bash
# Estrategia simple (sin plantilla): crea el proyecto, aplica la paleta y corre todo
bin/workflow.sh simple Test_NIKKEI225_M30_simpleL_x NIKKEI225 M30 long tendencia_base_v3 "para qué es" 1000 20

# Con plantilla ya escrita: lo mismo, desde su .sqx («-» en la paleta si no tiene hueco aleatorio)
bin/workflow.sh template Trade_XAUUSD_H1_ideaL XAUUSD H1 /ruta/template.sqx tendencia_base_v3 "para qué es" 1000 20

# Un proyecto que ya existe: sigue desde donde esté
bin/workflow.sh run Test_NIKKEI225_M30_simpleL_x
```

- `plan` en vez de `run` enseña lo que haría, sin correr nada. `--smoke` al final es la prueba funcional de un `Test_`. `--restart` es la ruta antigua, solo si la sesión única fallara.
- Cada decisión es un argumento obligatorio; si falta alguno o algo no cuadra, el comando se niega y dice por qué.
- Para un agente hay dos skills que son la receta mecánica (qué pedir, qué lanzar, qué leer, qué hacer si falla): **`/workflow-simple`** y **`/workflow-template`**, en `.claude/skills/`. Están escritas para que las siga cualquier modelo sin interpretar nada.
- Qué lee y qué llena cada paso (cómo se mueven las estrategias entre bases): `.claude/skills/workflow-simple/steps.md`.
- Al acabar: `AlgoData/autopilot/<PROYECTO>/<fecha-hora>/resumen.md` (una línea por paso), `tiempos.md` y, si algo falló, `fallo.md`.
- Mientras corre no se lanza nada pesado en la máquina.
- El run se para solo antes del paso 26 (MT5).

Para ti está el capítulo 105 del manual, en `docs/manual/04-sqx-plantillas-y-proyectos.pdf`.

**No probado:** la forma `template` no la he ejecutado creando un proyecto de verdad (solo sus comprobaciones de argumentos); la creación con plantilla usa el mismo constructor que ya usabas. La forma `simple` sí: es la del run final.

## 7. Mejoras pendientes

Ordenadas por lo que ahorrarían. Ninguna cambia resultados.

| mejora | ahorro estimado | estado |
|---|---|---|
| un run completo con los dos últimos arreglos (reabrir SQX antes de SPP y WFM; cierre final) | confirmar los ≈140 min | aplicado, sin medir junto |
| probar `bin/workflow.sh template` con una plantilla real | — | sin probar |
| exportar las operaciones de varias bases en un solo arranque de Java | 1,5-2 min por run | idea, sin probar |
| saltar la cosecha del paso 9 y la de la primera parada, que nadie lee | ≈1 min | idea, sin probar |
| estudio de calidad del feed (paso 8) en paralelo | ≈1 min | idea, sin probar |
| paso 18.5: limitar los hilos de cálculo de cada prueba (el paralelo dio menos de lo esperado) | 1-2 min | idea, sin probar |
| pasos 21 y 22 por madre en paralelo | segundos | idea |
| paso 26 (MT5) dentro del autopiloto | — | fuera de este encargo |

Cosas que sí cambiarían resultados y por eso **no he tocado** (son decisiones tuyas): precisión de los backtests, número de simulaciones del Monte Carlo, variantes por madre, cuántas estrategias pasan cada corte.

## 8. Estado en que queda todo

- Proyectos de prueba en el custodio, sin borrar, como pediste: `Test_NIKKEI225_M30_simpleL_ref`, `_val`, `_auto`, `_live`, `_fin`. Las bases SPP de `_live` y `_fin` tienen duplicados de mis repeticiones de control. `Trade_NIKKEI225_M30_volatilidadL` no se ha usado ni tocado.
- Cambios míos **sin commit**: `pipeline/autopilot/call.py`, `closing.py` y `blind.py` (son ficheros nuevos de otra sesión que aún no están en git; mis cambios van dentro), este informe, la referencia de tiempos, las fichas de knowhow de la noche, el README del autopiloto, la skill y el capítulo 80 del manual.
- `pipeline/autopilot/criteria.yaml`: la semilla fija de las pruebas ya está otra vez en `null`.
