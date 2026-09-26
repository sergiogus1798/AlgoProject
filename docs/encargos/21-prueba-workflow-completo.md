# 21 · El workflow entero, de punta a punta, con profiling de cada paso — encargo autocontenido

**Tu oficio:** operador y medidor. Corres los 25 pasos del `WORKFLOW.md` uno detrás de otro sobre
una población nueva, compruebas que cada uno funciona, y **mides lo que cuesta cada paso**: tiempo,
memoria, CPU y disco, SQX incluido. **No optimizas nada y no arreglas código.** Lo que se rompa se
anota con su error y se sigue con lo que no dependa de ello.

El dueño estará fuera unas horas: **no hay nadie a quien preguntar**. Donde algo sea ambiguo, eliges
lo más conservador, lo escribes en el informe como decisión tomada por ti, y sigues.

---

## 0 · Espera a la señal — no arranques antes

Otra sesión (`algoproject-f8`) está terminando dos cambios que este encargo prueba: las **sesiones**
en el mapa condicional (paso 22) y que el **paso 18.5 pueda leer `oos2`**. **No lances nada de SQX
ni de Python del workflow hasta que exista el fichero**
`~/Desktop/AlgoProject_worktrees/_coord/LISTO-workflow.md`. Lo que sí puedes hacer mientras: leer
todo lo de §0.1 en adelante y preparar el plan y las estimaciones de tiempo.

Para esperar sin gastar: carga la herramienta Monitor (`ToolSearch "select:Monitor"`) y vigila con un
bucle `until [ -f ~/Desktop/AlgoProject_worktrees/_coord/LISTO-workflow.md ]; do sleep 60; done`,
y vuelve a armarla si caduca. Cuando aparezca, **léelo**: dice el commit de `docs/knowhow-fichas`
sobre el que corres y cualquier cambio de última hora. Si en 4 horas no ha aparecido, no corras nada:
deja el plan escrito en el informe y termina.

## 0.1 · Lee antes de tocar nada

1. `CLAUDE.md` entero — **las reglas duras 1 a 11 mandan sobre este encargo**. Sobre todo: la 1
   (snapshot de `user/projects` antes de cualquier cosa que reinicie SQX), la 2 y la 3 (nunca el
   maestro; sólo el custodio `SQX_w2` en el 5070; un trabajo cada vez; entre start y collect sólo
   `-project action=status`; `ListAgents` y el log del día antes de arrancar), la 5 (`python3 -m
   core.assets USDJPY` antes de crear el proyecto) y la 10 (un solo custom project para todo el
   workflow, `builder --workflow`, y cada paso enciende sólo su tarea con `stage`).
2. `docs/AgentPDFs/WORKFLOW.md` — la secuencia de 25 pasos. Manda sobre cualquier otro orden.
3. `docs/encargos/ejemplo-workflow-USDJPY.md` — **la corrida anterior del 2026-09-24 con esta misma
   plantilla**: qué funcionó, qué se rompió y cómo se cortó el embudo. Es tu modelo.
4. `docs/manual/00-empezar.md`, `docs/manual/47-proyecto-workflow.md`, `docs/manual/12-rendimiento.md`
   y `perf/README.md` (cómo mide el proyecto: memoria de todo el árbol de procesos, no `ru_maxrss`).
5. `docs/SKILLS.md` — cada paso de SQX tiene su skill (`/template-run`, `/oos-gate`, `/crossmarket`,
   `/crosstf`, `/mcretest`, `/spp`, `/variants`, `/wfm`). **Úsalos**: son el procedimiento probado.
6. La página de manual de cada paso antes de correrlo. **Los módulos nuevos del 26-09 y su
   comando** (la página trae el ejemplo completo, con sus argumentos):

   | paso | módulo | manual | comando |
   |---|---|---|---|
   | 8 | snooping (SPA/StepM), tras la puerta | `49-snooping.md` | `python3 -m studies.screening.snoopingScreen.report --project … --databank …` |
   | 8 y 25 | edge por coste | `50-edge-por-coste.md` | `python3 -m studies.readings.edgeCost.report --project … --databank … --feed …` (con `--strategy` en el 25) |
   | 18.5 | superficies por mercado | `52-superficies-mercado.md` | `python3 -m studies.optimisation.marketSurfaces.report --work <carpeta del lote> --family …` |
   | 22 | mapa condicional (sesiones y días) | `53-mapa-condicional.md` | `python3 -m studies.readings.conditionalMap.report --harvest … --strategy …` |
   | 23 | tests estructurales | `51-estructura.md` | `python3 -m sqx.structural.make …`, el run en el custodio y `python3 -m studies.readings.structure.report …` |
   | 24 | stop ATR | `54-atr-calculator.md` | el de la página: la X leída del MAE, el lote de variantes con stop y su retest en el custodio |
   | todos | el ledger | `43-ledger.md` | `python3 -m ledger.report` al final, para ver el embudo registrado |

**Dónde trabajas:** `~/Desktop/AlgoProject`, rama `docs/knowhow-fichas`, en el commit que diga
`LISTO-workflow.md` o uno posterior. **No cambies de rama ahí**: otras sesiones commitean en esa
carpeta.

## 1 · Qué corres

- **Activo:** USDJPY, `USDJPY_DukasM1_the5ers`, **H1**.
- **Plantilla:** `emaCloseAbove` — la misma de la corrida del 24-09 (§0.3). No autores ninguna nueva.
- **Proyecto:** uno nuevo, `USDJPY_workflow_profiling_v1`, en el custodio, con `builder --workflow`.
- **Costes:** los que declare el activo hoy (provisionales, comisión cero). No los toques: el dueño
  los revisará aparte. Todo resultado lleva ese aviso.
- **Tamaño de la población:** el suficiente para que **cada paso reciba estrategias**, no para
  encontrar una buena. Parte de ~200 estrategias en el build. En cada paso donde la criba real deje
  pasar demasiadas para lo que viene después, recorta **por net profit con `/curate`**, como el 24-09,
  y anótalo. Hasta el paso 15 lleva como máximo **8** estrategias; del 15 en adelante, como máximo
  **3 madres**. Antes de lanzar cada paso de SQX, **estima su duración** con el catálogo de `perf/` y
  los tiempos del 24-09, y escríbela; si un paso fuese a pasar de ~6 h, reduce su población y dilo.
- **`oos2`:** los pasos 17, 18, 18.5, 19 y 24 lo leen. Está autorizado (dueño, 2026-09-26), y el ledger
  lo permite para esos cinco. El paso 20
  es la lectura conjunta ciega: haz la lectura de 17, 18, 18.5 y 19 **sólo cuando los cuatro hayan
  corrido**.

### Los pasos, y qué hacer con los que no se pueden correr

| paso | qué |
|---|---|
| 1–3 | idea, vocabulario, plantilla: ya existen; sólo compruébalos (`/sqx-doctor`, vocabulario) |
| 4 | preflight `core.assets` |
| 5–7 | proyecto, build, retest OOS |
| 8 | puerta OOS (`/oos-gate`) **+ snooping (SPA/StepM) + edge por coste**, los tres |
| 9–12 | crossmarket y su análisis; variantes escaladas, crossTF y su lectura |
| 13–14 | MC Retest (`/mcretest`) y su análisis |
| 15–16 | SPP (`/spp`) y `sppUltra` |
| 16.5 | variantes (`/variants`), mínimo de 1.000 por madre (regla vigente) |
| 17, 18, 18.5, 19 | WFC, CSCV, superficies por mercado, WFM (`/wfm`) |
| 20 | lectura conjunta ciega. `studies/closing/blindJoint/` **no está construido**: lee los cuatro resultados juntos a mano y di qué harías; no lo construyas |
| 21 | exposición |
| 22 | mapa condicional (por sesiones y por día de la semana) |
| 23 | tests estructurales (`sqx/structural/` en el custodio + `studies/readings/structure/`) |
| 24 | stop ATR (`studies/closing/atrCalculator/` + el lote `stopgrid` en el custodio), fusionado el 26-09: sigue `docs/manual/54-atr-calculator.md` sobre cada superviviente |
| 25 | edge por coste sobre la versión que se operaría |
| —  | el 17 de calidad del feed y el 9 de monos **no se corren** (en pausa por decisión del dueño) |

## 2 · Qué mides, y cómo

**Cada paso, una fila.** Para los pasos de Python (todo lo que lee o escribe CSV/Parquet y calcula):

- **tiempo de pared**, **CPU** (usuario + sistema) y **pico de memoria de todo el árbol de procesos**
  (el mismo criterio que `perf/`: la suma del árbol, no el `ru_maxrss` del padre). Usa lo que
  `perf/measure/` ya ofrece; si no encaja para un comando, `/usr/bin/time -v` más un muestreo del
  árbol cada segundo;
- **E/S**: MB leídos y escritos, y cuánto creció el disco bajo `AlgoData`;
- **tamaño de la entrada**: estrategias, operaciones, variantes, filas — para comparar por unidad de
  trabajo.

Para los pasos de **SQX**:

- **tiempo** desde el `action=start` hasta `Project finished` en el log de SQX, y el reparto
  build/retest/export si se ve;
- **la JVM**: PSS muestreado cada 30 s contra el techo de `-Xmx80g`, y CPU;
- **ritmo**: backtests hechos de N por minuto (del log o de `action=status`);
- **disco** del proyecto antes y después.

**Pulso cada ~3 minutos** durante los pasos largos, escrito en el log de la corrida (el dueño lo lee
al volver): backtests hechos de N, JVM contra 80 GB, CPU, RAM libre.

Si un paso falla: guarda el comando, la salida y la traza; **no toques el código**; sigue con los
pasos que no dependan de él. Lo que se rompa va al informe con lo mínimo para reproducirlo.

## 3 · Dónde escribes

- **Datos crudos:** `~/Desktop/AlgoData/profiling/workflow-2026-09-26/` — un `steps.csv` (una fila por
  paso: paso, comando, entrada, n_in, n_out, pared_s, cpu_s, pico_mb, leído_mb, escrito_mb,
  disco_mb, estado, error), los muestreos de memoria de cada paso, y el log de la corrida con los
  pulsos.
- **El informe**, en español: `docs/AgentPDFs/profiling-workflow-2026-09-26.md`. Debe tener:
  1. el embudo entero (como el del 24-09): cuántas entran y salen de cada paso y cómo se cortó;
  2. **la tabla de profiling** paso a paso, con los de SQX y los de Python separados;
  3. **dónde se va el tiempo y dónde la memoria**: los cinco pasos más caros en cada eje, y el coste
     por unidad de trabajo;
  4. **lo que se rompió**, con su error y cómo reproducirlo;
  5. las decisiones que tomaste tú por no poder preguntar;
  6. **«por dónde empezar»**: la sección para el siguiente agente, el que sí optimizará — qué medir
     primero, con qué comando y sobre qué datos.
- Un hecho no obvio que descubras → una ficha en `knowhow/<dominio>/` en la misma tarea
  (formato en `knowhow/INDEX.md`).

**No commitees en `docs/knowhow-fichas` sin decirlo:** haz tus commits en una rama propia en un
worktree (`git worktree add ~/Desktop/AlgoProject_worktrees/workflow-profiling -b
docs/profiling-workflow`), sólo el informe y las fichas. Nada de código.

## 4 · Cómo cierras

Custodio parado (`bin/sqx-worker.sh --role custodian stop`), sin `sqcli` colgado. Devuelve: qué
corrió y qué no, la tabla de profiling resumida, lo que se rompió, y la ruta del informe y de los
datos.
