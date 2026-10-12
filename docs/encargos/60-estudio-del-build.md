# 60 · Estudio del build — qué configuración deja más supervivientes por encima del mono

**Tu oficio:** diseño experimental y estadística sobre lo que el autopiloto ya escribe; SQX sólo a través
de `bin/workflow.sh` y del custodio. **Opus** para el diseño, el módulo del estudio y el veredicto;
**Sonnet** para lanzar las corridas, esperar y tabular (regla 17).
**Tu encargo:** una decisión — **qué métrica de fitness y qué modo de generación (genético o aleatorio)
quedan escritos en `assets/_build.yaml`** — medida por las supervivientes del paso 8 de cada lote **menos**
lo que deja el control de monos con el mismo `criteria.yaml`, con al menos 3 réplicas por brazo, sobre una
celda **nueva**. Y, de paso, el registro que hoy no existe: el exceso sobre el mono **por celda y
plantilla**. «Ninguna configuración se distingue del ruido entre réplicas: se queda la heredada, ahora
escrita» es un resultado válido.

Lee `CLAUDE.md` (reglas 1-7, 9-11, 14-20) · `CODESTYLE.md` · `studies/CLAUDE.md` · `.claude/skills/new-study/SKILL.md`
· `.claude/skills/workflow-simple/steps.md` (pasos 6 a 8) · `studies/readings/monkey/README.md` ·
`knowhow/research/ga-target-choice.md` (cabecera) · `ledger/README.md`.

## Estado del plan (lo actualiza cada sesión al cerrar)

| fase | qué | modelo | depende de | estado |
|---|---|---|---|---|
| F0 | preguntas 1 a 4 contestadas; `criteria.yaml` congelado y anotado | Opus | el dueño | sin empezar |
| F1 | la métrica y el modo, argumentos de `bin/workflow.sh`, leídos de `_build.yaml` | Opus | F0 | sin empezar |
| F2 | el estudio (`/new-study`): lee los lotes, resta el mono, anota el ledger | Opus | F0 | sin empezar |
| F3 | el control de monos de la celda, una vez | Sonnet | F0 | sin empezar |
| F4 | las corridas: brazos × réplicas, hasta el paso 8 | Sonnet | F1, F3, custodio libre | sin empezar |
| F5 | veredicto y `_build.yaml` | Opus | F2, F4, el «sí» del dueño | sin empezar |

### Bitácora

- 2026-10-11 — Encargo escrito desde la revisión del dueño de los pasos 1 a 7 (§6.4, §1 y §0).

---

## 0 · De dónde sale

Revisión del dueño del 2026-10-11 (`~/Desktop/revision-pasos-01-07-2026-10-11.md`). §6.4, «ESTUDIO NUEVO
(pedido por el dueño)»: «¿Qué configuración del build produce candidatas con más ventaja real, medida por
cuántas supervivientes del paso 8 superan al azar?». §1: «Medir cada idea por su exceso sobre el control de
monos en el paso 8, por celda y plantilla. Es la retroalimentación que el paso 1 no tiene». §0: «El paso 8
no distingue la corrida real del azar» — el control de entrada aleatoria por el mismo `criteria.yaml` deja
unas 66 de cada 10.000 (33 de 5.000; Clopper-Pearson 45-93) y los cinco lotes reales de `doubleROCLong` en
USDJPY M30 dieron 56, 48, 10, 31 y 72 (`docs/AgentPDFs/criterios-implementados-2026-10-12.md:53,528,555`;
fuente `falsePositives/funnel.csv`, fila `nula,8`). §6.3 es decisión tomada: el databank lleno sigue
reemplazando por la métrica de fitness — la pregunta es **cuál**.

Lo que se comprobó en el código el 2026-10-11, y corrige la revisión:

- **El suelo de 35 operaciones al año ya está** en `assets/_study.yaml:44-48` (M15, M30 y H1 = 35; H4 = 20;
  sin techo, dueño 2026-10-09) y coincide con `pipeline/autopilot/criteria.yaml:80`. No se toca.
- **`MonteCarloManipulation` ya no existe:** el código lo rechaza (`sqx/projects/resources.py:147`).
- **La métrica de fitness no la escribe ningún módulo.** El bloque `<BuildMode>` entero se copia de
  `sqx/projects/buildmode_model.xml` (mira `:24,31`); lo cargado es lo que traía el donante (Ret/DD según
  el dossier, líneas 47 y 461 — **compruébalo en el XML, no lo des por hecho**).
- **El modo de generación** es `builder --random` (`sqx/projects/patch.py:15`, `GENERATIONS`).
- **El ruido entre corridas iguales (~16 puntos) supera el efecto de cualquier métrica** dentro de muestra
  (`knowhow/research/ga-target-choice.md`): sin réplicas el estudio no dice nada.
- **El control de monos** se lanza con `python3 -m studies.readings.monkey.report --project P --databank D`.
  **No hay registro por celda ni por plantilla** de supervivientes del paso 8 frente al control, ni un
  enlace confirmado del estudio de monos a `criteria.yaml`: F3 empieza por averiguar cómo pasó el control
  de 5.000 por el paso 8 (`grep -rn 'falsePositives' --include=*.py --include=*.md . | head`).
- No hay comparación vigente genético/aleatorio: la de septiembre salió de la calibración borrada el
  2026-10-04 (dossier, línea 246).

## 1 · F1 — La métrica y el modo, por argumento (Opus)

Regla 19: una corrida no se configura a mano ni editando el XML. Hoy `bin/workflow.sh simple|template`
(`bin/workflow.sh:6`) no deja elegir la métrica. Construye lo mínimo:

- `assets/_build.yaml` gana, junto a `money_management` (`:61-62`), la métrica de fitness y el modo de
  generación **con el valor que hoy se hereda** (ningún cambio de comportamiento al añadirlos).
- `sqx/projects/builder.py` los escribe en el `<BuildMode>` que copia de `buildmode_model.xml`, y acepta
  un `--fitness <X>` junto al `--random` que ya existe; `bin/workflow.sh` lo pasa. Averigua los valores
  que SQX admite leyendo el XML de un proyecto del conductor en disco (parado), nunca del master.
- Un test (`tests/test_build_fitness.py`): con el valor por defecto el `project.cfx` generado es idéntico
  byte a byte al de hoy; con otro, sólo cambia ese nodo. Su línea en el capítulo del manual de `workflow.sh`.

**El sorteo de desarrollo** (`pipeline/autopilot/criteria.yaml:52-55`, `dev.sample`) inventa supervivientes
en el paso 8: comprueba si sigue encendido; el estudio corre con él apagado en todos los brazos. Si no hay
forma de apagarlo por corrida, el encargo 58 (§1.d) pide esa misma opción: úsala si existe, constrúyela una
sola vez si no.

## 2 · F2 — El estudio (Opus, por `/new-study`)

`/new-study` lo coloca y le da su forma (módulo, catálogo de la ventana, umbrales en el ledger, test,
capítulo del manual). Lo que debe hacer:

- **Leer** de cada corrida `AlgoData/autopilot/<P>/<stamp>/resumen.md` y `paso-8/hechos.parquet`: tamaño
  del databank, supervivientes del paso 8 (Pasa y Limbo por separado), y la t en `oos1` de cada una.
- **La medida:** supervivientes del lote − (tasa del control de la celda × tamaño del lote), con su
  intervalo (el control es una binomial: Clopper-Pearson; entre réplicas, la dispersión observada). Además
  la distribución de la t en `oos1` de las supervivientes, y **qué entra en el databank** en cada brazo
  (operaciones al año, nº de lógicas distintas): la revisión §6.2 dice que no se sabe qué ocupa el sitio de
  las de menos de 35 operaciones.
- **El veredicto:** un brazo gana sólo si su diferencia con el heredado supera la dispersión entre réplicas
  del propio brazo; di el tamaño de efecto que 3 réplicas pueden ver y cuál no.
- **El registro por celda y plantilla:** una fila por lote en un fichero propio bajo `AlgoData/` (regla 7)
  con celda, plantilla, brazo, réplica, supervivientes, esperadas por el control y exceso. Que sirva a
  cualquier corrida futura, no sólo a este estudio: es la retroalimentación del paso 1.
- **La selección se anota:** cada brazo lee el `oos1` de la celda en el paso 8, y elegir configuración
  mirándolo es una selección más. Una fila por brazo en el libro de búsqueda (`ledger/record.py`,
  `ledger/tried.py` — «lo que se probó, no sólo lo que se eligió»), con N = nº de brazos.

## 3 · F3 — El control de monos de la celda (Sonnet)

Una vez por celda, con el `criteria.yaml` congelado: la población de entrada aleatoria de esa celda por el
paso 8, del mismo tamaño o mayor que un lote. Entrega la tasa con su intervalo. Si pasar monos por el paso 8
exige una pieza que no existe, **para y dilo**: es el punto 1 del encargo `53-monos-y-nulos.md`, no se
duplica aquí.

## 4 · F4 — Las corridas (Sonnet)

Antes: `python3 -m core.assets <SÍMBOLO>` (regla 5) y `.claude/skills/sqx-wait/preflight.sh` (quién tiene
el custodio). Un proyecto por lote (regla 10), todos `Test_` (regla 6), con el **mismo** comando y sólo el
brazo y la réplica cambiados:

```
bin/workflow.sh <simple|template> Test_<SIM>_<TF>_<idea>_fit<Métrica>_r<n> <SIM> <TF> <long|short> <PALETA|PLANTILLA> "estudio del build" 10000 90 --until 8 [--fitness <X>] [--random]
```

Los argumentos exactos, de `sed -n 2,26p bin/workflow.sh`. Un lote a la vez por servidor, nada pesado al
lado (regla 19); la espera, con `/sqx-wait` (regla 18); el segundo servidor, sólo por
`bin/remote.sh gorilla --detach …` (regla 12). Cada `Test_` se retira al cosechar
(`python3 -m sqx.projects.retire <P> --role custodian --yes`, worker parado), sin `/store-save`.

**Horas de custodio** (builds de 90 minutos, tope 10.000; pasos 7 y 8 aparte):

| diseño | lotes | horas |
|---|---|---|
| 3 métricas × 3 réplicas, genético | 9 | 14-15 |
| + brazo aleatorio con la métrica heredada, 3 réplicas | 12 | ~19-20 |
| 3 métricas × 2 modos × 3 réplicas | 18 | ~28-30 |
| el control de monos de la celda (F3) | 1 | por medir; anótalo |

Con gorilla en paralelo, la mitad de reloj. Un lote que falla tiene los tres intentos de la skill y después
un informe — nunca un paso a mano ni un cambio en `criteria.yaml`.

## 5 · F5 — El veredicto y `_build.yaml` (Opus)

La tabla por brazo (media y rango del exceso sobre el mono, t en `oos1`, qué entra en el databank), la
decisión que propones con **su coste en estrategias junto a su ganancia**, y — sólo tras el «sí» del dueño
— el valor en `assets/_build.yaml` con un comentario fechado que cite el estudio.

## Lo que no tocas

El master · `pipeline/autopilot/criteria.yaml` (congelado todo el estudio: anota su hash en la bitácora al
empezar) · `oos2` (las corridas acaban en el paso 8, `--until 8`) · la celda `doubleROCLong` USDJPY M30
(`oos1` cribado cuatro veces, `oos2` abierto) · el suelo de 35 operaciones · el tope de 10.000 y el
reemplazo por fitness (decisión §6.3) · el money management (encargo 61) · los costes (encargo 59) · el
mono por los pasos 10 a 20 (encargo 53) y la fábrica contra series sintéticas (encargo 58): este estudio
acaba en el paso 8.

## 6 · Decisiones del dueño — pregúntalas (regla 11)

1. **Qué celda.** Activo, marco, dirección y plantilla (o Simple Strategy con qué paleta). Debe ser nueva:
   sin `oos1` cribado ni `oos2` abierto. Trae tres candidatas con lo que el registro dice de cada una
   (encargo 62 si ya existe; si no, `AlgoData/projects/registry.csv`, `AlgoData/campaign/ledger.jsonl` y
   `AlgoData/ledger/<SIM>_<TF>_*.jsonl`) y pregunta.
2. **Qué métricas.** La heredada (la que diga el XML) frente a cuáles: la revisión pone «por ejemplo
   Sharpe y SQN». Lista las que SQX ofrece y pregunta cuáles dos — o si son más de dos.
3. **El brazo aleatorio.** (a) fuera; (b) dentro, sólo con la métrica heredada (12 lotes); (c) cruzado con
   las tres métricas (18 lotes) — aunque en modo aleatorio la métrica sólo ordena el reemplazo del databank
   lleno: dilo al preguntar.
4. **Qué cuenta como superviviente.** Pasa, o Pasa + Limbo (el control de 5.000 dejó 2 y 31).
5. **Réplicas.** 3 por brazo es el mínimo de la revisión: ¿3, o 5 si la dispersión de las primeras lo pide?
6. **El resultado.** Si ningún brazo se distingue: ¿se escribe la heredada en `_build.yaml` tal cual?

## Objetivo — un comando

```
python3 tools/depmap.py && python3 tools/checks.py \
  && python3 -m pytest tests/test_build_fitness.py tests/test_<estudio>.py -q \
  && python3 -m <módulo del estudio>.report --cell <celda>
```

`report` sale ≠ 0 mientras falte una réplica de cualquier brazo o el control de la celda; «ningún brazo se
distingue» es un veredicto y sale 0. Sustituye los dos nombres en este fichero cuando `/new-study` los fije.
F5 (escribir `_build.yaml`) se verifica a ojo, con el «sí» del dueño.

## Cómo cierras

Qué hizo · qué verificó, con la salida del Objetivo y la tabla por brazo pegadas · qué dejó sin hacer y por
qué · qué descubrió para `knowhow/` (al menos: el resultado, **editando** `knowhow/research/ga-target-choice.md`;
las horas reales por lote, en `knowhow/perf/`) · la lista de ficheros cambiados y, como última línea,
**¿Quieres hacer el commit?**

```
/loop Lee docs/encargos/60-estudio-del-build.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
```
