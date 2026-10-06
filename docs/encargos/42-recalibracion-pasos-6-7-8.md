# 42 · Recalibrar los pasos 6, 7 y 8 por activo × marco × familia — encargo autocontenido

**Tu oficio:** jefe de un equipo de agentes. Estadística y diseño: **Opus** para ti, para la síntesis
y para el equipo rojo; **Sonnet** para lo mecánico (lanzar poblaciones, exportar, tabular) — regla 17.
**Tu encargo:** devolver al dueño **la receta de filtros** de su fábrica, medida y no supuesta:
(a) qué pedir en el *in-sample* del Build de SQX (paso 6) y (b) qué reglas Pasa / Limbo / Falla poner
en el primer cribado *out-of-sample* (pasos 7-8), **cada umbral con lo que gana y lo que cuesta en
estrategias al lado**, por activo × marco × familia allí donde los datos obliguen a separarlo y
global donde no. «Este filtro apenas ayuda» es una respuesta válida: dila.

Lee `CLAUDE.md` (reglas 3, 10, 11, 13-19) · `docs/AgentPDFs/WORKFLOW.md` (pasos 5-8) ·
`pipeline/autopilot/README.md` · la cabecera de `pipeline/autopilot/criteria.yaml` ·
`assets/_study.yaml` · `assets/_build.yaml` · `assets/FAMILIAS.md` · `OPEN.md` §93
(`grep -n '^## 93' OPEN.md`) · las cabeceras de `knowhow/research/gate-t-scales.md`,
`knowhow/research/post-selection-bias.md`, `knowhow/sqx-drive/unselected-build-population.md`,
`knowhow/perf/review-path-after-sqx.md`, `knowhow/perf/per-strategy-readings-ram.md`,
`knowhow/market-profile/market-profile-blind-spots.md`, `knowhow/eng/nulls-seed-fresh-per-run.md`.

---

## 0 · De dónde sale

- **Las palabras del dueño (2026-10-02):** «qué criterios he de poner, sobre todo en el IS de SQX, y
  en el primer cribado de OOS en la aplicación, para que (1) me salga un OOS robusto — esto depende
  mucho del IS — y (2) los tests del mono y demás cosas del paso 8 salgan aceptables». Y para el IS,
  una receta concreta: «cuántos trades he de pedir (suelo de 35 por año), si he de pedir un PF
  mínimo, un KER, un Sharpe, o qué métricas he de usar».
- **Por qué se rehace entera.** La primera calibración (2026-10-01/02) rompía las reglas 14 y 15. La
  segunda (2026-10-04, 203 poblaciones) corrió con el spread mal y el dueño la borró entera: datos,
  registro, nulos y herramientas (`OPEN.md:764`, «un fiasco»). **No queda nada reutilizable en
  disco**: ni la cola, ni el toolkit, ni los nulos. Los costes ya están corregidos (commit `3b71384`:
  el spread más ancho de FTMO, Hantec y FundingPips, slippage al 35 % del spread).
- **Lo que hoy dice ser criterio y no lo es:** las cifras de los pasos 6 y 8 de `assets/_study.yaml`
  y `criteria.yaml`, y los dossiers `docs/AgentPDFs/criterios-pasos-6-y-8-2026-10-02.md` y
  `criterios-pasos-6-a-12-2026-10-04.md`. Salen de datos borrados: se leen por su **método**, no por
  sus números, y ninguno de los dos lleva el aviso.
- Este encargo sustituye a `docs/AgentPDFs/prompt-recalibracion-pasos-6-7-8-2026-10-02.md` (borrado;
  en git hasta `936e394`).

## 1 · Antes de gastar una hora de CPU

1. **Los costes de los activos.** `python3 -m core.assets <SYMBOL>` de cada activo que vayas a
   construir (regla 5): informa de los overrides y para si sale distinto de cero.
2. **El spread de cada ficha.** La sospecha de las dos fórmulas de «puntos» se cerró el 2026-10-06
   (`docs/OPEN-closed.md` §106): hay una sola, `studies.data.spread.verdict.points`. Una calibración
   ya se tiró por el spread: enseña al dueño el spread por tramo de cada activo que vayas a
   construir (`python3 -m core.assets <SYMBOL>`) **antes** de construir nada.
3. **Qué activos se construyen.** Las sesiones ya salen del `data.db` de SQX
   (`sqx/projects/sessiondb.py`, `tests/test_session_from_db.py`) y las 19 fichas tienen la suya;
   pero **ninguno de los 17 activos nuevos ha corrido todavía en SQX** (`OPEN.md` §93). Una
   población de prueba por activo, de cinco minutos, antes del barrido: cuenta estrategias y
   operaciones, no lo supongas.
4. **Quién más usa los workers** (regla 3): `ListAgents`, `.claude/skills/sqx-wait/preflight.sh`.
   Hay otra sesión con la campaña: no corras a la vez que ella (regla 19: nada pesado al lado).

## 2 · El carril: cómo se construye una población sin seleccionar

Hace falta una población **sin seleccionar** (aceptación mínima: ≥ 100 operaciones en la ventana del
build y beneficio > 0; nada que lea el OOS; el databank **nunca lleno**, porque lleno reemplaza por
Ret/DD del IS y eso ya es una selección) y, en un subconjunto, su **gemela de generación aleatoria**,
que es el control que dice si una celda está enriquecida o es azar.

Las piezas existen — `sqx.projects.builder --acceptance calibration` (`core/buildfilters.py:65-68`,
`assets/_study.yaml:65-71`) y `--random` (`sqx/projects/builder.py:184`) — pero `bin/workflow.sh` no
las pasa (`:55-56`), y la regla 19 prohíbe conducir los pasos a mano. **Es la decisión D1: no la
tomes tú.** Con la respuesta, el carril hace por población: Build → retest OOS (paso 7, costes de
`oos1`, precisión de 1 minuto, sin condiciones de aceptación) → cosecha → gate, edgeCost,
snoopingScreen, spread (donde haya scan) y mono **con semilla fija** (`--seed`,
`studies/readings/monkey/report.py:68`) → hechos (`python3 -m pipeline.autopilot.facts --project P
--step 8`). **No** feedQuality, profitShape ni entryQuality (dueño, 2026-10-02).

Reglas del carril:
- Un trabajo a la vez en el custodio; arranque y parada sólo por `bin/sqx-worker.sh`; la espera, por
  `/sqx-wait` (regla 18). Sin agente en el bucle: un script suelto que avanza la lista y deja un
  fichero de marca.
- Proyectos `Test_Calib_<ACTIVO>_<TF>_<familia><L|S>[_rnd]`; cada uno se retira al completarse
  (`python3 -m sqx.projects.retire <P> --role custodian --yes`, regla 6).
- Tras aplicar una paleta, **cuenta los bloques encendidos** en el Build y **cuenta las condiciones**
  de cada estrategia: ninguna pasa de 2 entradas y 2 salidas (regla 14). Si una pasa, para.
- Mide la caja de tiempo: con 250 × 20 islas una generación son 5.000 individuos. Dimensiónala para
  que la búsqueda genética evolucione de verdad sin que el databank se llene, y dile al dueño cuánto
  dura una población antes de lanzar el barrido.
- Datos a `AlgoData` (regla 7); borra el `raw/` de una población cuando su cosecha esté escrita y di
  lo que pesa el total. Como mucho 8-12 procesos de Python y 25 GB libres. Nunca `pkill -f`.

## 3 · Los nulos, sobre la misma estadística

Los nulos anteriores se borraron. Es el punto **1.5** de `docs/encargos/41-fases-0-y-1.md` (léelo:
`sed -n 188,197p`): hazlo aquí y actualiza su fila en la tabla de estado. Estrategias sin ventaja
simuladas con la doctrina y los costes de cada activo, más su gemela a coste cero (el punto muerto:
la referencia honesta de «tiene ventaja»). Sobre ellas se calcula **exactamente** lo que el pipeline
calcula sobre las reales — `gate.scorecard.drift_excess_t`, `trade_t`, la misma contabilidad, el
mismo ajuste de deriva, el mismo N efectivo —; una tasa de falsos positivos medida sobre otra
estadística no vale nada. De aquí salen las líneas de la t por marco y la suerte del PF según el
número de operaciones.

## 4 · El diseño

- **Celdas:** activo (≥ 10-12) × marco (M30, H1) × dirección (largo y corto, poblaciones separadas:
  regla 13) × familia (sólo las que `assets/FAMILIAS.md` lista para ese activo y marco) × generación
  (genética con el bloque del dueño, que ya va en todo proyecto — `tests/test_builder_simple.py` —
  y no se toca; aleatoria en el subconjunto de control).
- **Sin plantilla:** Simple Strategy, 1..2 entradas y 1..2 salidas (`assets/_build.yaml:23-29`).
- **Prioridad si el tiempo aprieta:** primero las celdas donde el prior y el perfil de mercado
  coinciden (ruptura y momentum, largo, H1 y M30: DJ30, XAUUSD, GBPJPY, USDJPY, EURJPY); después las
  que el prior recomienda sin medida; las «medido en contra» sólo si el dueño lo dice (D4).

Sobre las poblaciones:
1. **Paso 6, dosis-respuesta.** Para cada métrica del IS que SQX pueda poner como condición del
   Build (`knowhow/columns/`): operaciones por año (prueba 20, 25, 30, 35, 40 y 50, y di qué cuesta y
   qué compra el 35), PF, KER, Sharpe, Ret/DD, SQN, estabilidad, estancamiento, % de aciertos y
   operación media contra el coste. Cuáles predicen un OOS robusto, cuáles no, y cuáles son el mismo
   eje con otro nombre. Si el mejor predictor no es una columna de SQX, dilo y da la más cercana.
2. **Paso 8, embudo.** Cada regla candidata con: qué deja pasar, qué parte de lo bueno pierde, su
   elevación, un intervalo de confianza agrupado por estructura de estrategia, su tasa de falsos
   positivos en los nulos y su **efecto en solitario** (las que sólo ella degrada). Y, junto a cada
   una, la parte de supervivientes que pasa el mono a p ≤ 0,05 y el resto de pruebas del paso 8.
3. **«Buena» se define con datos que la regla no lee**, y la conclusión se comprueba con dos o tres
   etiquetas alternativas. **Tasas, no recuentos.**
4. **A/B dentro y fuera del Build**, con réplicas: cada filtro recomendado, puesto como condición
   del Build y como corte después en Python. La vez anterior, dentro perdía estrategias buenas, con
   un solo build por brazo.
5. **La prueba que nadie ha corrido:** un build largo que llena el databank y sigue reemplazando por
   Ret/DD todo su tiempo, contra uno corto.
6. **La familia:** ¿la que `FAMILIAS.md` recomienda da más supervivientes OOS que el azar en ese
   activo, contra su gemela aleatoria y su nulo? ¿Cambian los umbrales por familia (frecuencia,
   duración, riesgo flotante en R)? Las celdas sin enriquecimiento son un hallazgo: se listan.
   Los índices, contra comprar y mantener a la misma exposición, no contra cero.
7. **Riesgo flotante** como eje propio (peor día, peor MAE y drawdown sobre neto anual, en R): las
   cuentas de fondeo se juzgan por el flotante.
8. **Equipo rojo.** Un agente con contexto limpio recalcula la propuesta por su cuenta y devuelve
   CONFIRMADO / FALSO / EXAGERADO / SIN APOYO por afirmación. Cuenta con que cambie cifras.
9. **Por el camino real del código** (`facts.per_strategy` → `criteria.resolved` →
   `criteria.outcomes`) en cada población: el embudo, por población y agrupado.

## 5 · Lo que entregas

- **El dossier**, en castellano, en `docs/AgentPDFs/` con su PDF (`/dossier-pdf`): la receta del IS,
  las reglas del OOS, cada umbral con ganancia y coste, qué varía por activo, marco o familia y qué
  es global, las celdas sin ventaja, y qué segmento gastó cada cifra. Sustituye a los dos dossiers de
  criterios anteriores: pon en la cabecera de ambos una línea que diga que sus cifras no valen y
  apunte al nuevo.
- **Las reglas escritas donde aplican** — `assets/_study.yaml`, `pipeline/autopilot/criteria.yaml` —
  marcadas como **propuesta de un agente**, provisionales hasta que el dueño firme (punto 1.2 del
  plan 41). Si los criterios han de variar por familia, hace falta una clave `by:` de familia en
  `criteria.yaml`, que hoy no existe (sólo marco, símbolo y clase de activo): añádela con su test.
- **Las poblaciones, como filas** de la memoria de investigación (`python3 -m
  studies.research.memory.report --close <run_dir>`).
- **Una ficha de `knowhow/`** por cada hecho no obvio; `OPEN.md` §93 anotado con `/open-close`; el
  capítulo del manual de cualquier comando que cambie (regla 8).

## Decisiones del dueño — pregúntalas (regla 11)

- **D1 · El carril.** (a) `bin/workflow.sh` aprende a construir poblaciones de calibración
  (aceptación mínima, gemela aleatoria, parada antes de llenar el databank) y todo pasa por él; o
  (b) autoriza para este estudio la llamada directa al builder con `--acceptance calibration` y
  `--random`, fuera de la regla 19. Son dos fábricas distintas: (a) deja una pieza que se mantiene.
- **D2 · Las paletas.** Hay tres juegos en `sqx/blocks/palettes/`: los originales (148-180 bloques,
  con bloques de reloj y de stop/limit), los `_v2` (6-13 bloques, «la familia y nada más») y los
  `_v3` (99-127, con `pullback_base_v3`). ¿Cuál usa la calibración? Ninguno consta como aprobado.
- **D3 · La familia `sesion`.** ¿`SessionHigh/Low/Open`, `HighD/LowD/OpenD` y el VWAP anclado
  cuentan como leer el reloj (regla 15)? Hasta que responda, no se corre.
- **D4 · Celdas «medido en contra»** de `FAMILIAS.md` (7): ¿se gastan builds en ellas?
- **D5 · Operaciones por año en índices × reversión.** El suelo de 35 quita justo la reversión diaria
  de índices que la literatura documenta (5-8 operaciones al año). ¿Excepción, agrupar por clase de
  activo, o se asume la pérdida? Llévale el coste medido.
- **D6 · La salida.** ¿Toda estrategia debe llevar regla de salida (`exits.condition_required`)
  también con plantilla? Hoy sólo es obligatoria en Simple Strategy.
- **D7 · El presupuesto de máquina.** El 2026-10-02 dijo que 40 horas de builds eran aceptables:
  confírmalo con la duración por población que midas en §2.
- **D8 · `oos1` ya fue leído** dos veces para elegir umbrales en USDJPY y XAUUSD. ¿Se vuelve a leer,
  sabiéndolo y diciéndolo en el dossier?

## Lo que no tocas

- El master (`~/Desktop/SQX`), ni para leer su configuración de tareas.
- **`oos2`.** Reservado. La calibración del día 4 lo usó de validación; ésta no.
- El bloque genético del dueño (`sqx/projects/buildmode_model.xml`).
- `dev.on` de `criteria.yaml` y la firma de los criterios: son suyos.
- La campaña y sus ficheros (`pipeline/campaign/`): los lleva otra sesión.
- `ledger/thresholds.yaml` salvo filas nuevas al final de su sección.

## Verificación

- `python3 -m pipeline.autopilot.facts --project <P> --step 8` sobre una población: todos los hechos
  de las reglas propuestas existen (una regla sobre un número que el autopilot no ve es siempre Limbo).
- El recuento de condiciones por estrategia y de bloques encendidos por población, pegado.
- La tabla de falsos positivos de cada regla sobre los nulos, y el informe del equipo rojo.
- `ls ~/Desktop/SQX_w2/user/projects | grep -c Test_Calib` → 0 al terminar.
- `python3 tools/depmap.py && python3 tools/checks.py`.

## Cómo cierras

Qué hiciste · qué verificaste, con la salida pegada · qué dejaste sin hacer y por qué · qué
descubriste para `knowhow/` · la fila 1.5 del plan 41 al día · los ficheros cambiados y, como última
línea, **¿Quieres hacer el commit?**
