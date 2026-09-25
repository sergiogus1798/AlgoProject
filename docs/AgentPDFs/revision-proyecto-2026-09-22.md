# Revisión del proyecto — 2026-09-22 (noche)

**Qué es este documento.** Una revisión completa en modo revisor: el proyecto, su encaje con SQX,
la estadística de los estudios y lo que cuesta todo en tiempo, memoria y tokens. Lo pidió el dueño
antes de dormir. **Todo lo que aquí se afirma como fallo está verificado leyendo código, ficheros
del install o datos reales de `AlgoData`; lo que es opinión va marcado como propuesta.** No se ha
tocado ningún install, ningún proyecto ni ningún dato; solo se han escrito este fichero, una
entrada en `OPEN.md` que apunta aquí, y dos ficheros de memoria del agente que estaban rancios.

**Para quién.** Para el dueño. Está ordenado por lo que decide primero: qué arreglar antes de
lanzar la corrida de las tres madres, qué cambiar del método, qué cuesta y qué le toca decidir a él.

Generado el 2026-09-22 sobre la rama `data/bar-library` (20 commits sin push, ~70 ficheros sin
commitear).

---

## 0 · Resumen para leer en dos minutos

El proyecto está muy por encima de la media en disciplina: reglas duras que evitan pérdidas
reales, `knowhow/` con procedencia, un pipeline con libro mayor que sobrevive al borrado, tests de
propiedad sobre la estadística, y un catálogo de rendimiento. **Lo grande funciona.** Lo que sigue
son las cosas que, tal como están hoy, harían que la próxima corrida larga midiera otra cosa o se
rompiera en silencio.

**Cinco cosas que haría mañana, en este orden:**

1. **No lanzar la corrida de las tres madres con la receta actual.** La etapa `ran` no reconstruye
   su arnés: hereda el que dejó `spp_oos`. Hoy el `Retester` de W2 está en estado SPP (ventana
   2008–2017 sola, SPP exhaustivo y `SequentialOptimization` los dos encendidos). Es el escenario
   de los 47 núcleos × 91 minutos, pero sobre 5.000 variantes. **§2.A.**
2. **Corregir el intervalo del WFC antes de creer ningún veredicto.** Los 1.001 puntos tienen una
   correlación mediana de 0,80 entre sí y valen ~21 pruebas independientes; el IC se calcula como
   si fueran 1.001. El `no_fiable` de `Strategy 17.9.39` no está sostenido. **§2.C.**
3. **Poner un candado al custodio y una lectura de vuelta del arnés antes de cada `start`.** Hoy
   dos sesiones pueden pisarse y `execute.py` borra los databanks de quien esté usando el install.
   **§2.D.**
4. **Decidir si el SPP sigue siendo la fase de reconocimiento.** Es el 95 % del coste (80 min por
   madre y ventana) y la propia fábrica de variantes da lo mismo en menos de un minuto, con IS y
   OOS emparejados. **§3.1.**
5. **Hacer `git push`** y commitear los ~70 ficheros que llevan dos días fuera del historial (entre
   ellos `nulls/`, la reestructura de `assets/` y siete páginas de manual). **§2.K.**

---

## 1 · Lo que está bien, para calibrar el resto

- **Las reglas duras y la topología de tres installs** han convertido la pérdida de databanks de
  riesgo permanente en imposible por construcción. Es la decisión de arquitectura más valiosa del
  proyecto y está bien argumentada en `knowhow/databanks/` y `03`.
- **La fábrica de variantes** (`sqx/variants/`) lee de vuelta lo que escribió, en vez de fiarse
  del plan, y tiene un test que exige que reescribir la tupla del padre reproduzca el padre byte a
  byte. Es la forma correcta de construir algo que falla en silencio.
- **El libro mayor del pipeline** se escribe durante la etapa, con `os.replace`, mide el coste de
  los dos árboles de procesos y sobrevive al borrado. Es exactamente la cola de trabajos que el
  demonio futuro necesita.
- **La estadística está mejor pensada que en la mayoría de proyectos de este tipo**: n efectivo por
  duplicados, centinelas filtrados, CSCV por regla de selección, PBO con su desviación bajo el nulo
  medida y escrita, Fieller donde el denominador es cero, sweeps de elecciones arbitrarias.
- **`knowhow/` con etiquetas de procedencia y secciones supersedidas conservadas.** El coste de
  aprender un fallo ya pagado es una lectura, no una tarde de CPU.
- **Los tests son de propiedad, no de cobertura**, y los ocho pasan en verde. `checks.py` sale con
  0 problemas sobre 283 ficheros.

---

## 2 · Fallos confirmados, por gravedad

### 2.A 🔴 La etapa `ran` no posee su arnés, y hoy el arnés está en estado SPP

**Qué pasa.** `pipeline/recipe.yaml` encadena `spp_is → spp_oos → spp_export → sppultra → design →
build → ran`. Las dos primeras reescriben `Retester/project.cfx` del custodio con el arnés SPP
(`sqx/variants/spp.py`, `harness.write`). La etapa `ran` (`sqx/variants/execute.py`) **no escribe
ningún arnés**: carga las variantes y hace `-project action=start` sobre lo que haya. Desde el
commit `8c26e18` (SPP dentro de la receta) nunca ha corrido la cadena entera; el único `state.json`
real (`pipeline/XAUUSD/Strategy_17-9-39`) empieza en `sppultra`.

**Evidencia, leída del install esta noche** (`SQX_w2/user/projects/Retester/project.cfx`, solo
lectura):

```
Setup dateFrom="2008.01.01" dateTo="2017.12.31" testPrecision="1"   ← IS sola, sin <OutOfSample><Range>
OptProfileSysParamPermutation use="true"  MaxTests 1000000001  ±30  Steps 12   ← exhaustivo
SequentialOptimization use="true"          ±35  Steps 5                          ← el que quemó 91 min
Output databank = SPPOut
```

Si mañana alguien lanza `pipeline.run --strategy X` sobre una madre ya diseñada (o la cadena
completa), `ran` cargará 2.000–5.000 variantes en ese arnés: **sin muestra OOS, con SPP exhaustivo
y optimización secuencial sobre cada variante.** No hay error: `collect` vería resultados distintos
entre los canarios y seguiría.

**Arreglo propuesto.** `execute.py` reconstruye su propio arnés al empezar (`harness.donor_task
("retest")` + `ungate` + costes) igual que hace `spp.py`, y **antes de `start` lee de vuelta el
proyecto** (`-project action=saveconfig`) y comprueba: ventana IS+OOS con `<Range>`, SPP y SeqOpt
apagados, `retestSelected="false"`. Esa comprobación es una puerta del pipeline, no un aviso.

### 2.B 🔴 `spp_export` lee el databank equivocado, o el perfil equivocado, y borra el anterior

Tres problemas en la misma costura, todos sin verificar porque la cadena SPP nunca corrió entera:

1. **Qué databank.** La receta exporta `--project Retester --databank Results`, que es el databank
   de **entrada** (`sqx/variants/config.yaml: execute.input`). El SPP escribe la estrategia
   reteseada con su perfil en el de **salida** (`RetestOut`). O el export no encuentra perfil
   (`profiles_found 0`, y la puerta `produces` para el run), o lo encuentra en la copia de entrada
   porque SQX comparte el objeto en memoria, cosa que nadie ha medido.
2. **Qué ventana.** El export corre **después** de `spp_oos`. Si el perfil está donde el export
   mira, es el de 2018–2022: **el `design_brief` se construiría sobre la superficie OOS**, que es
   exactamente la fuga que el protocolo prohíbe ("un diseño elegido sobre los datos que lo juzgan
   no es un diseño").
3. **Dónde escribe.** `export_spp.py` escribe en `raw/<P>/<D>/<hoy>/spp/` con `open("w")`. Cien
   madres el mismo día son cien sobreescrituras de la misma carpeta: `raw/` deja de ser inmutable,
   y el `source` de cada `design_brief` acaba apuntando a la tabla de la última madre. Además
   `inputs.source(design)` busca `<source>/../strategies/<madre>.sqx`, carpeta que `export_spp` no
   crea (la creó `export_trades` en el export del 2026-09-10): **la etapa `build` no encontraría el
   padre**.

**Arreglo propuesto.** Exportar desde `RetestOut` justo **después de `spp_is` y antes de
`spp_oos`** (o eliminar `spp_oos`, §3.2); escribir en `raw/<P>/SPP_IS/<hoy>/<madre>/spp/`; y que
`inputs.source` reciba la ruta de la madre congelada (`donors/madres-…`) en vez de derivarla.

### 2.C 🔴 El intervalo del WFC trata 1.001 variantes correlacionadas como 1.001 observaciones

`strategies/walkForwardCorrelation/measure/correlation.py:correlation` usa el intervalo de Fisher con
`n = len(kept)`. Medido esta noche sobre `pipeline/XAUUSD/Strategy_17-9-39`:

| | |
|---|---|
| puntos utilizables | 1.001 |
| correlación mediana entre las curvas semanales de dos variantes | **0,80** (p10 0,68) |
| pruebas independientes según `trials.independent` (el propio módulo) | **21** |
| IC 95 % publicado | [0,18, 0,30] |
| IC 95 % con n = 21 (misma fórmula) | ≈ [−0,22, 0,61] |

Las variantes son la misma estrategia con los parámetros movidos; comparten árbol de reglas y la
mayoría de las operaciones. El proyecto ya sabe esto: `core/surface/dedupe.py` dice literalmente
"un IC sobre filas correlacionadas es falsamente estrecho por un factor ~3" y `trials.py` cuenta
los clústeres para deflactar el Sharpe. **Pero el WFC no lo usa.** Consecuencias:

- El `no_fiable` de la corrida de 2.000 (IC [0,13, 0,25] "entero por debajo de 0,30") y el
  `indeciso` de esta no están sostenidos. La conclusión honesta hoy es "rho ≈ 0,2 y no sabemos su
  intervalo".
- El hallazgo de `knowhow/export/spp-pairing-for-wfc.md` "rho apenas se movió al multiplicar por 180 los puntos" es
  precisamente lo que se espera cuando los puntos no son independientes: se estrechó un intervalo
  que no debía estrecharse.

**Arreglo propuesto.** Bootstrap por clúster (remuestrear los `n_clusters` grupos de
`trials.independent`, no las filas), o Fisher con `n_eff`. Un ajuste secundario: el umbral de 30
operaciones se aplica igual a 10 años de IS y a 5 de OOS (`measure.points`); el protocolo §4c pide
**umbral por año**, y el absoluto sesga la muestra hacia las tuplas que más operan.

### 2.D 🔴 Sin candado, sin `stop` previo, sin timeout: el custodio se puede pisar y colgar

Leído en `sqx/variants/execute.py`:

- `awake()` devuelve `False` si el custodio ya está levantado ("alguien lo está usando") **y
  sigue**: `load()` hace `-databank action=clear` sobre `Results` y `RetestOut` sin más. Si otra
  sesión tenía un SPP de 80 minutos en marcha, se le borra el databank de salida.
- `run()` hace `-project action=start` **sin `action=stop` antes**. `knowhow/sqx-drive/running-a-task-headless.md` documenta que un
  segundo `start` no hace nada en silencio y que hay que parar siempre antes; `template-run` lo
  hace; `execute.py` no.
- `run()` es `while done < expected` sin tope. Si SQX carga menos variantes de las esperadas (no
  se verifica la carga: `load()` duerme 8 s fijos) o el `start` no arrancó, **cuelga para siempre**.
  `spp.py` sí tiene `timeout_s`; `execute.py` no.
- No hay lock. El "un trabajo cada vez" del custodio es una convención entre sesiones, y el dueño
  corre varias.

**Ocurrió a la mañana siguiente (2026-09-23, 07:26–07:33):** otra sesión arrancó y paró el custodio varias veces para un benchmark y cambió su `coreUsage`, sin saber si alguien más lo usaba. Está anotado en `knowhow/perf/smt-in-sqx-retest.md`, sección «dos sesiones sobre el custodio a la vez». Es este fallo, en vivo.

**Arreglo propuesto.** Un fichero `AlgoData/locks/custodian.json` (pid, sesión, madre, hora)
que `execute`/`spp` toman y sueltan, y que `awake()` respeta; `stop` antes de `start`; timeout en
`run()` proporcional a `n × 0,1 s` con margen; y verificar la carga con `action=export` (el único
lector seguro) antes de `start`.

### 2.E 🟠 La reanudación se rompe al pasar la medianoche

`pipeline/stages/recipe.py:context` toma `{day}` de `--report-day`, que por defecto es hoy. Los
`produces` de `spp_export` y `sppultra` llevan `{day}`. Una corrida de 100 madres interrumpida y
relanzada al día siguiente no encuentra el `design_brief` de ayer, rehace `sppultra`, genera un
brief nuevo y `gates.unchanged` para el run por `brief_hash` distinto. El libro mayor promete
reanudabilidad y aquí no la cumple. **Arreglo:** guardar `report_day` en `state.json` en
`open_run` y reutilizarlo.

### 2.F 🟠 La lista de madres sale de un export viejo, no de la carpeta de madres

`pipeline/run.py:mothers` lee `runs.csv` del último export SPP en `raw/` (hoy el de 2026-09-10 con
5 estrategias), mientras la receta reconoce `{mother}` en `donors/madres-2026-09-22/` (3
estrategias distintas). Sin `--strategy`, el run intentaría reconocer estrategias que no están en
la carpeta de madres. **Arreglo:** listar `MADRES.json`.

### 2.G 🟠 Los canarios comprueban lo que pueden, no lo que debían

`collect.canaries()` solo mira que los controles devuelvan **valores distintos**. Las expectativas
absolutas (`canary_expect_netprofit`, `canary_expect_trades`) viajan en el manifiesto y nadie las
compara. Y no pueden compararse: vienen del SPP del maestro (precisión 1 minuto, spread 5, IS sola) y
el retest usa el donante `Retest-Task1` (precisión 2, spread 0 en el donante; 10 en la última
corrida). Un retest sobre la ventana equivocada (§2.A) pasa el control de "distintos" sin
problema. **Arreglo:** o unificar precisión y spread entre SPP y retest, o generar las expectativas
con un retest previo de 3 variantes en el mismo arnés (barato: 3 × 90 ms).

### 2.H 🟠 El holdout tiene tres definiciones y ya se ha leído

| dónde | holdout |
|---|---|
| `docs/preregistro/holdout-XAUUSD-2026-09-21.md` (sin firmar) | 2022–2026 |
| `assets/_policy.yaml` → `oos2` | 2023-01-01 a 2026-08-30 |
| `docs/AgentPDFs/protocolo-robustez` | 2022–2026 |

Y dos estudios ya han leído esa ventana para XAUUSD: el **WFM** (export 2026-09-10, celdas hasta
2027, lo reconoce el propio protocolo) y el **Monte Carlo sobre `MC Trades`** (export 2026-09-19,
757 estrategias, ventana 2007-01-01 a 2026-01-01, usado por `strategies/monteCarlo` y por el
catálogo `perf`). `nulls/` se restringió a `OOS1` y está limpio.

No es reversible y no es grave si se registra: el pre-registro debe decir **qué se ha leído ya, por
quién y a qué nivel** (flota entera, no estrategia a estrategia) y elegir una sola frontera. Lo que
no vale es firmarlo como si estuviera virgen.

### 2.I 🟠 La mitad del diseño se tira

999 de 2.000 variantes operan menos de 30 veces en alguna muestra. El diseño muestrea esquinas
donde la estrategia deja de operar (y `knowhow/sqx-format/declared-parameters.md` ya lo dice: "pide el doble de puntos"). Es CPU
de retest, disco y, sobre todo, **puntos del WFC que no existen**. **Arreglo:** diseño en dos
pasadas: un piloto de ~200 tuplas Sobol, podar los niveles con menos de N operaciones por año, y
rellenar el resto del presupuesto dentro de la región viva. Coste del piloto: 200 × 90 ms.

### 2.J 🟠 Con la configuración de hoy, 5.000 variantes con cross-check no caben en el heap

`pipeline/config.yaml: sample: 5000` (el comentario del mismo fichero defiende 2.000). Medido: 2.000
variantes con XAGUSD → 21,1 GB de RSS del JVM, 1 mercado → 12 GB, escalado casi lineal. 5.000 con
dos mercados son ≈ 50 GB contra un `-Xmx48g`. Lo esperable no es un error limpio sino GC continuo
y un SPP-like "vivo pero parado". **Arreglo:** lotear `ran` en bloques de 2.000 (el propio
informe de costes lo propone) o bajar `sample` a 2.000 hasta que exista el loteo.

### 2.K 🟡 Estado del repositorio

- **20 commits sin push** (falló por credenciales; hay que hacerlo a mano).
- **~70 ficheros modificados o nuevos sin commitear**: `nulls/` entero, `assets/` reestructurado
  (`symbols/`, `_classes`, `_markets`, `_policy`), `core/assetcheck.py`, `core/assetdata.py`,
  siete páginas de manual (21–26), `knowhow/costs/`, y el borrado de las cuatro skills
  `analysis-*`. Dos días de trabajo que un `git checkout` o un disco pueden llevarse.
- La rama **`perf/montecarlo-tiles` no está fusionada**: −55 % de pico de memoria y −14 % de reloj
  en Monte Carlo, medidos.
- `.claude/settings.json` sin commitear a propósito (decisión del dueño, fine).

### 2.L 🟡 Documentación que ya miente

- `pipeline/README.md` habla de "siete etapas" y de que `ran`, `collected` y `wfc` son stubs. La
  receta tiene 12 filas reales.
- `docs/manual/17-pipeline.md` igual: "cinco de las siete etapas son marcadores de posición".
- `docs/AgentPDFs/coste-pipeline-2026-09-22.md` §2 y §7.1 dicen que el cross-check de mercado "no
  devuelve ni una columna" y proponen apagarlo. **Ya no es cierto**: el `.sqx` reteseado lleva
  `Results/AdditionalMarket: XAGUSD…/dailyEquity.bin` (comprobado en `RetestOut`) y
  `core.sqxstats.equity(path, result="AdditionalMarket")` lo lee. El estudio multi-mercado (§9 del
  protocolo) sale gratis de la cosecha de curvas; no hay que apagar nada.
- `pipeline/config.yaml`: `sample: 5000` con un comentario que argumenta 2.000.
- `docs/SKILLS.md` y `docs/manual/23-skills.md` citan skills borradas (`analysis-crossmarket`) en
  el ejemplo.

### 2.M 🟡 Pequeños, pero reales

- `trials.independent`: si ningún `k` pasa la regla "ningún clúster con la mitad", `scored` queda
  vacío y `max()` revienta. Con correlaciones medianas de 0,8 es plausible en alguna madre.
- `collect.join`: un lote cargado dos veces (`P00000(1)`) duplica filas tras quitar el sufijo y
  `n` sale inflado; el docstring dice que "los duplicados se ven" pero nada los cuenta.
- La receta lleva `XAUUSD_DukasM1_Infinox=M30=5` y `=10` a fuego en `spp_is`/`spp_oos`: símbolo,
  timeframe y spread de un proyecto concreto en un fichero que se declara genérico, y los spreads
  no coinciden con `assets/symbols/XAUUSD.yaml` (10/10). Existe `sqx.projects.configure`, que
  aplica los costes de `assets/` a un `.cfx`; `harness.py` no lo usa.
- `docs/manual/PENDIENTE.md` y `OPEN.md` con 30 hilos en estados mezclados; el auditor no corre
  desde el 2026-09-11 y `audit/state.json` todavía cita rutas `1_sqx/`.
- Memoria del agente: dos ficheros citaban `KNOWHOW.md` y `1_sqx/` (rutas de antes del
  2026-09-04). Corregidos esta noche.

---

## 3 · Optimizaciones de proceso: tiempo y memoria

### 3.1 Sustituir el SPP como reconocimiento por un lote piloto de la propia fábrica

El SPP es el 95 % del coste (80 min por madre y ventana, 24–43 GB de heap, sin progreso, un solo
SPP por install). Lo que se le pide es: (a) qué parámetros mueven el resultado (η²), (b) cuáles son
inertes (test de duplicados), (c) centro y niveles. **La fábrica ya produce lo mismo, mejor y 100×
más barato:**

| | SPP en SQX | lote piloto por la fábrica |
|---|---|---|
| muestreo | ±35 %, todos los parámetros a la vez, ~15.000 puntos | Sobol ±35 %, todos a la vez, los puntos que quieras |
| coste por punto | ≈ 320 ms (80 min / 15.000) | **47 ms** (90 con dos mercados) |
| 1.000 puntos | ~5 min de SPP, pero el SPP no se puede pedir tan corto | **47 s** |
| IS y OOS | dos corridas, no emparejables entre sí | **una corrida, emparejadas** |
| trades y curvas | no existen (el SPP guarda 152 números) | `dailyEquity.bin` de cada punto |
| trampas propias | `startOnlyTask`, elemento equivocado, `MaxTests` centinela, perfil que no persiste, `dontStoreOP3DChartsData`, export del perfil | ninguna nueva: es la misma ruta que `ran` |

Lo que hay que replicar: la lista de parámetros "recomendados" que SQX permuta. Está en
`strategy_Portfolio.xml` (todas las `<variable>` numéricas) y los cinco `permutation_params.csv`
del maestro sirven para validar que la selección coincide. `strategies/sppUltra` ya lee un grid
genérico (`inputs/export.grid`): bastaría alimentarlo con el `metrics.parquet` del piloto en lugar
de `permutations.csv`.

Resultado: **de ~2 h 48 min por madre a ~10 min**, y el arnés deja de cambiar de forma entre etapas
(desaparece el §2.A por construcción). Es la decisión con mejor relación beneficio/riesgo del
documento y es del dueño (§7).

### 3.2 Si el SPP se queda: quitar `spp_oos` de la ruta crítica

La receta dice que el OOS "se exporta para comparación y no es lo que construye la rejilla". Son
80 minutos por madre (133 horas en 100 madres) para un fichero que ningún módulo consume. Como
mínimo, opcional.

### 3.3 Lotear el retest y acotar la memoria en bytes

Ya propuesto en el informe de costes; añado el número: 5.000 × 2 mercados ≈ 50 GB (§2.J). Lotes de
2.000 dejan el pico en 21 GB sea cual sea el tamaño del diseño, y el libro mayor ya sabe reanudar
por etapa; faltaría reanudar por lote.

### 3.4 Leer el cross-check en vez de apagarlo

`sqxstats.equity(result="AdditionalMarket")` sobre los `.sqx` de `RetestOut` da la curva de plata
de cada variante en 1,5 s por lote (medido para la principal). El estudio §9 del protocolo
(¿transfiere la superficie a la familia?) sale de ahí sin un backtest extra. Lo que sí sigue
costando es el retest en sí (+90 % de tiempo); pero ahora compra algo.

### 3.5 Monte Carlo

- `n_sims: 100000` cuando el propio módulo mide que 20.000 cumple su tolerancia (5× menos tiempo,
  mismos veredictos). Decisión del dueño, pero está medida.
- Fusionar `perf/montecarlo-tiles` (−55 % de pico, −14 % de reloj).
- `max_workers: null` = 96, y el kernel actual satura a 24 (con tiras, escala a 96). Coherente solo
  tras la fusión.

### 3.6 Precisión y costes coherentes entre etapas

SPP del donante: `testPrecision 1` (barras de un minuto). Retest del donante: `testPrecision 2`.
Spread: 5 (SPP IS), 10 (SPP OOS), 0 (retest donante), 10 (última corrida real). Cada etapa mide
con una regla distinta y luego se comparan sus números. Un solo sitio (`assets/`) y una sola función
(`sqx.projects.configure` o su lógica dentro de `harness.py`) para todas las tareas del custodio.

### 3.7 Disco

- `snapshots/` 4,5 GB de un snapshot único; con presupuesto de 20 GB caben cuatro y luego hay que
  rotar. Proponer "los dos últimos".
- Dos intermedios de WFM (920 MB) marcados como reproducibles en `INDEX.md` y todavía ahí.
- Fuera de todo presupuesto: `~/Desktop/AlgoData.zip` (790 MB, del 15-09) y `~/Desktop/SQX.zip`
  (1,3 GB, de junio). Nadie los rastrea.
- El log del maestro sigue creciendo por el error horario de `Infinox_SP500ft` (55 MB/día en el
  peor caso); la poda lo contiene, pero el archivo comprimido ya es 105 MB de un solo día.

---

## 4 · Tokens: dónde se gastan y cómo bajarlos

### 4.1 El coste de arrancar un agente

Lo que `CLAUDE.md` manda leer para tocar el pipeline hoy: el plan (35 KB), el protocolo (40 KB),
`knowhow/sqx-drive/` (45 KB), `knowhow/export/` (45 KB) y `CODESTYLE` + el README de la carpeta. **Unos 45.000
tokens antes de escribir una línea**, y buena parte es narrativa o está supersedida.

Propuesta: un `docs/BRIEF.md` de dos páginas, **generado** (como `SKILLS.md` y `DEPENDENCIES.md`),
con: las nueve reglas, la topología (una tabla), las trampas de SQX en una línea cada una con enlace
a la sección, el estado del pipeline (qué etapa es real, qué falta) y las decisiones pendientes del
dueño. Es lo que `docs/encargos/CONTEXTO-ecosistema-skills-sqx.md` ya casi es, pero escrito a mano
y por tanto rancio en dos semanas.

### 4.2 `knowhow/` es referencia y diario a la vez

`07-practices.md` tiene 1.069 líneas (~18.000 tokens) y es un cuaderno de laboratorio: cada
sección cuenta cómo se llegó a un hecho. Eso es valioso y no debe borrarse, pero **no debe cargarse
para consultar un hecho**. `03-driving-sqx.md` conserva íntegras dos secciones supersedidas (~3.000
tokens) que un lector nuevo lee antes de llegar a la corrección.

Propuesta: por fichero, un bloque "hechos" arriba (una línea por hecho, con su etiqueta y un
ancla) y la narrativa debajo; y una regla de estilo: **una sección supersedida se reduce a una línea
que apunta a la que la corrige**, con el texto original movido a una carpeta `superseded/` dentro de knowhow. El
`INDEX.md` gana una columna "tokens".

### 4.3 Cuatro documentos que dicen el estado

`OPEN.md` (30 hilos), `docs/encargos/ESTADO-…` (diario), `plan-ejecucion` §7 (tabla de lotes) y
`protocolo-robustez` "Estado a 2026-09-21" (marcado como sustituido pero ahí). Cada uno cita a los
otros. Un agente que quiera saber "qué hay hecho" lee los cuatro. Propuesta: un solo `ESTADO.md`
vivo con la tabla de lotes y las decisiones pendientes; el resto, archivo fechado.

### 4.4 Skills

- Las cuatro globales de `sqx-lab` (18.000 tokens de cuerpo) están marcadas como candidatas a
  retirar desde el 22-09 y el riesgo real es el enrutado. Es una decisión de un minuto.
- Las de proyecto (7.000 tokens en total) están bien dimensionadas.

### 4.5 El gasto que de verdad duele: depurar silencios de SQX

El informe de costes lo mide: 55 % de 105.000 tokens en una sesión. La receta correcta ya está
escrita ("que el fallo hable") y hay que aplicarla sistemáticamente: **cada trampa de `knowhow/sqx-drive/`
que ya costó tokens debe existir también como puerta en código** (lectura de vuelta del arnés,
`stop` antes de `start`, verificación de carga por `export`, timeout). Cada una vale los tokens de
la próxima depuración que evita.

---

## 5 · Rigor del método, más allá de los fallos

- **La unidad de evidencia es la madre, no la variante.** Con correlaciones de 0,8 entre variantes,
  el estudio de 100 madres es un estudio de ~100 observaciones de rho, no de 100.000 puntos. El
  plan ya prevé agregar con Fisher-z; que lo haga sobre `n_eff`, y que el informe de cada madre
  lleve `n_clusters` al lado de `rho`.
- **El PBO sin intervalo** (ya en `POSSIBLE_IMPROVEMENTS.md`): con desviación 0,21 bajo el nulo,
  el umbral de 0,50 clasifica al azar cerca de él. El block-jackknife sobre los 10 bloques es la
  forma correcta y es barato.
- **Las ventanas placebo (Fase 2)** siguen sin correr, y con ellas la calibración √T que el
  protocolo exige para comparar ventanas de distinta longitud. Mientras tanto el WFC compara neto
  de 10 años contra neto de 5 en rangos (correcto) pero el filtro de operaciones no lo es (§2.C).
- **Un solo régimen en el holdout** (2022–2026, oro en subida casi continua). El protocolo lo
  avisa; añado que el mono de `nulls/` ya mide "cuánto de esto es la deriva" y sería el control
  natural del holdout: una estrategia que pasa el holdout pero no bate al mono en esa ventana no
  ha demostrado nada.
- **Costes provisionales en todo lo medido**: las estadísticas de rango (rho, PBO) aguantan; el
  neto, MinTRL y el mono no. Hasta que Infinox confirme, ningún resultado en dólares es
  comparable con nada.
- **Seed variance del GA** (±16 pp entre corridas iguales) sigue sin réplicas; cualquier
  conclusión "este target es mejor" sigue siendo ruido. Ya está registrado; lo repito porque es la
  única forma de que no se cuele en una decisión.

---

## 6 · Ideas que quizá no se han considerado

1. **Candado + lectura de vuelta como patrón.** `AlgoData/locks/<role>.json` y `saveconfig` antes de
   cada `start`. Cubre §2.A y §2.D con 40 líneas y convierte tres trampas documentadas en tres
   errores explícitos.
2. **El piloto reemplaza al SPP** (§3.1) y de paso deja el pipeline en un solo arnés, una sola
   precisión, un solo spread.
3. **El cross-check ya es legible** (§3.4): el estudio multi-mercado del protocolo puede salir
   esta semana de datos que ya existen en `RetestOut`.
4. **Diseño adaptativo** (§2.I): duplica los puntos útiles sin fabricar más.
5. **Una ficha por madre** (`mother.json`: verdict, rho, IC, n_clusters, PBO, coste en segundos y
   GB) que el futuro demonio sirva tal cual. El libro mayor ya tiene casi todo; falta la vista.
6. **Control del mono en el holdout** (§5): reutiliza `nulls/` sin código nuevo.
7. **Un cron para lo mecánico**: `daily_audit.py` no está programado por miedo a un falso "no
   renderiza" durante un save de SQX; un reintento de 5 s sobre `zipfile.BadZipFile` lo resuelve.
   El auditor lleva once días sin correr y el proyecto ha cambiado más en esos once días que en
   los quince anteriores.
8. **Cortafuegos** para 5050–5071 y 8080–8082: la API escucha en `0.0.0.0` sin credenciales. Es un
   `sudo` del dueño, y está en `knowhow/sqx-drive/api-no-auth.md` desde el 21-09.
9. **Rotación de snapshots y limpieza del escritorio** (§3.7): 2 GB de zips que nadie rastrea.
10. **Un test de coherencia de la receta**: para cada fila, que los `needs` de la siguiente estén
    entre los `produces` de alguna anterior, y que ninguna fila con `{day}` sea reanudable sin
    guardar el día. Cinco líneas en `pipeline/verify/selftest.py`.

---

## 7 · Decisiones que solo puede tomar el dueño

Consolidadas, porque hoy están repartidas entre `OPEN.md`, el plan, el pre-registro y `assets/`:

| # | decisión | dónde bloquea | coste de no decidir |
|---|---|---|---|
| 1 | **SPP o piloto** como reconocimiento (§3.1) | toda la corrida de madres | 2 h 40 min por madre |
| 2 | **`spp_oos`**: fuera, opcional o dentro (§3.2) | idem | 80 min por madre |
| 3 | **Firmar el pre-registro** con una sola frontera y el registro de lecturas ya hechas (§2.H) | WFM, WFC sobre 2022+ | el holdout se sigue erosionando sin constancia |
| 4 | **Costes de Infinox** (spread, comisión, y si la comisión % es por pata o por operación, `OPEN.md` 26) | todo resultado en dólares | cada informe lleva la salvedad |
| 5 | **Umbrales**: `rho_floor` 0,30, PBO 0,50, los tres de Monte Carlo (`OPEN.md` 19) | los veredictos | se juzga con números que nadie eligió |
| 6 | **`testPrecision`** única para SPP y retest (§3.6) | comparabilidad entre etapas | canarios incomprobables |
| 7 | **`n_sims`** 100.000 o 20.000 | Monte Carlo | 5× de tiempo |
| 8 | **Retirar las skills globales `sqx-*`** | enrutado de peticiones | plantillas fuera de norma |
| 9 | **Fusionar `perf/montecarlo-tiles`** | memoria de MC | −55 % de pico sin usar |
| 10 | **`git push` y commit** de los ~70 ficheros (§2.K) | todo | riesgo de pérdida |
| 11 | Los 16 activos sin coste (`OPEN.md` 27) y los rangos del MC Retest | cualquier símbolo que no sea XAUUSD | no se puede autorizar nada |

---

## 8 · Orden sugerido para mañana

1. `git push origin data/bar-library` y commit de lo pendiente (10 min).
2. Reescribir `execute.py` para que construya su arnés y lea de vuelta antes de `start`; añadir
   `stop`, timeout, verificación de carga y candado (§2.A, §2.D). Selftest en verde. (medio día)
3. Decidir §7.1 y §7.2. Si piloto: `sppUltra` lee `metrics.parquet`; se borran `spp_is`,
   `spp_oos`, `spp_export` de la receta. Si SPP: arreglar §2.B (databank, orden, carpeta por madre,
   `strategies/`). (un día en cualquiera de los dos casos)
4. IC del WFC por clúster y umbral de operaciones por año (§2.C). Re-emitir el informe de
   `Strategy 17.9.39` y ver qué dice ahora. (medio día)
5. `report_day` en el libro mayor y `mothers()` desde `MADRES.json` (§2.E, §2.F). (una hora)
6. Lanzar las tres madres con `sample: 2000` y un mercado; medir; después dos mercados y lotes.
7. Actualizar `pipeline/README.md`, `docs/manual/17-pipeline.md` y `coste-pipeline` (§2.L).
8. Firmar el pre-registro con el registro de lo ya leído (§2.H).

---

## Apéndice — cómo se verificó cada fallo

Todo de solo lectura, sin instancia de SQX viva por mi parte:

```bash
# §2.A  el arnés actual del custodio
unzip -o -q ~/Desktop/SQX_w2/user/projects/Retester/project.cfx -d <scratch>/w2
grep -oE '<(Setup|OptProfileSysParamPermutation|SequentialOptimization)[^>]*>|<MaxTests>[0-9]+' <scratch>/w2/Retest-Task1.xml
# §2.A  execute.py no escribe arnés ni para antes de arrancar
grep -n "harness\|action=stop\|timeout" sqx/variants/execute.py        # 0, 0, 0
# §2.B  qué exporta la receta y dónde escribe export_spp
grep -n "spp_export" -A2 pipeline/recipe.yaml; grep -n "export_dir\|open(" sqx/export/export_spp.py
# §2.C  dependencia entre variantes y n_clusters, sobre la corrida real
python3 - <<'EOF'
import pandas as pd, numpy as np, json
w='/home/sergioguslw/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39/'
e=pd.read_parquet(w+'equity.parquet').resample('W').sum().iloc[:-1]
c=np.corrcoef(e.to_numpy().T); print(np.nanmedian(c[np.triu_indices_from(c,1)]))
print(json.load(open(w+'cscv.json'))['trials'], json.load(open(w+'wfc.json'))['ci95'])
EOF
# §2.H  ventana del export MC Trades
python3 -c "import json;print(json.load(open('/home/sergioguslw/Desktop/AlgoData/raw/XAUUSD/MC_Trades/2026-09-19/manifest.json'))['source']['window'])"
# §2.L  el cross-check sí deja curva en el .sqx
unzip -l ~/Desktop/SQX_w2/user/projects/Retester/databanks/RetestOut/P00000.sqx | grep dailyEquity
# §2.K
git log origin/master..HEAD --oneline | wc -l; git status --short | wc -l; git branch --no-merged master
```
