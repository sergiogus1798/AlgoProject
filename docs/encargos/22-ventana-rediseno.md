# 22 · Rediseño de la ventana (`ui/`) — encargo autocontenido

**Tu oficio:** PySide6 + FastAPI (`ui/desktop/`, `ui/daemon/`). Las piezas de motor del §12 las
puede hacer en paralelo otra instancia con oficio Python. Sale de una sesión de dictado del dueño
(2026-09-27) mirando la ventana en vivo, revisada después con él punto por punto. Donde dice
«primera versión, se itera», así es: el dueño quiere **verlo construido** y corregir en una segunda
pasada.

Lee `ui/README.md` · `ui/desktop/README.md` · `core/study/CONTRACT.md` · `docs/AgentPDFs/WORKFLOW.md`
· `docs/AgentPDFs/paneles-flask-inventario-2026-09-25.md` · `studies/CLAUDE.md` ·
`ui/desktop/ops/ledger.py` (qué es el Ledger — ver §9).

---

## 0 · Decisiones del dueño que cambian reglas escritas

Todas del 2026-09-27. Cada una **se escribe en el documento que contradice, en la misma tarea**
(`ui/README.md` y, si aplica, `CLAUDE.md`):

| decisión | contradice |
|---|---|
| La ventana **puede lanzar la siguiente tarea de SQX** con «Continuar workflow» (§7), siempre tras una pantalla de confirmación | `ui/README.md` §«What it does not do»: hoy la ventana solo toca SQX para cargar un databank |
| PROYECTO pasa de seis zonas a **tres** (§2) | la tabla de zonas de `ui/README.md` |
| En Windows la ventana funciona **solo en modo lectura** (§11) | nada: hoy ofrece botones que aquí solo pueden fallar |
| **Cada filtro que aplique el dueño se apunta en el Ledger** como una búsqueda (§7) | nada: extiende el Ledger a búsquedas hechas a mano |
| El WFC admite **cualquier composición** IS/OOS; la disciplina es del dueño, y cada composición leída queda apuntada (§12.1) | los dos modos fijos de `engines/variants/panel.py` |
| OOS2 aparece en el panel fijo **solo cuando ya está disponible**: tras correr los pasos 17, 18 y 19 (§5) | nada: concreta `ledger/gate.py` en la ventana |

## 1 · Fases — en este orden

El encargo es demasiado grande para una sola pasada, y el dueño necesita ver algo pronto.

| fase | qué | por qué en este orden |
|---|---|---|
| **0** | Pulido global (§10) + modo lectura en Windows (§11) | un día de trabajo; el dueño ve el cambio enseguida |
| **1** | **Maqueta con datos falsos** del nuevo espacio de trabajo (§3-§5): la disposición, sin conectar nada al backend | el dueño dijo que ya no se imagina cómo quedará: la maqueta se itera barata. Se puede enseñar en su PC Windows, que es donde tiene los dos monitores |
| **2** | Proyectos (§3) + Proyecto (§4), conectados de verdad | |
| **3** | Estrategia, la ficha (§5) + visualizaciones (§6) | |
| **4** | Filtros + «Continuar workflow» (§7) | es lo más delicado: borra en SQX |
| **5** | BIBLIOTECA: Activos, Configuración SQX, Datos (§8) | |
| **6** | OPERACIÓN (§9) + PORTFOLIOS (§2) | Portfolios depende del encargo 23 |
| en paralelo | motor: §12.1, §12.2, §12.3 | condición para acabar las fases 3 y 6 |

Entre la fase 1 y la 2, **parar y enseñarle la maqueta al dueño**.

## 2 · La nueva barra lateral

La barra lateral le gusta mucho al dueño: se mantiene como está. Cambia lo que cuelga de ella.

| grupo | zonas |
|---|---|
| BIBLIOTECA | Cobertura, Plantillas, Nueva plantilla, Paletas, Activos, **Configuración SQX** (nueva, §8.2), **Datos** (construida de verdad, §8.3) |
| PROYECTO | **Proyectos** (§3) → **Proyecto** (§4) → **Estrategia** (§5) |
| OPERACIÓN | **En marcha** (Custodio + Generación fusionados, §9) · **Registro de búsquedas** (el Ledger, renombrado, §9) |
| **PORTFOLIOS** | lo que hoy es CARTERAS, renombrado. Importa estrategias archivadas (encargo 23) |

**Se retiran como zonas** Workflow, Población, Estudio de población, Estrategias y Puerta IS/OOS: su
contenido entra en «Proyecto». Lo que cada una muestra hoy y no puede perderse:

- **Estrategias** (`desktop/studies.py`): el selector proyecto/activo/databank, la lista de
  resultados a la derecha, el botón de informe HTML, la curva de equity emparejada.
- **Puerta IS/OOS** (`desktop/gate.py`): el embudo y la tarjeta de puntuación del paso 8.
- **Población** (`desktop/matrix/`): la matriz estrategias × estudios.
- **Workflow** (`desktop/workflow/`): el raíl de pasos con su estado.

La barra de contexto (`Proyecto › Población › Estrategia`) se adapta a las tres zonas nuevas.

## 3 · Proyectos — la galería

Sustituye al desplegable de `desktop/matrix/view.py` (líneas 59-61 y 120-165). Una tarjeta por
proyecto con:
- símbolo y timeframe,
- número total de estrategias entre todos sus databanks,
- plantilla usada,
- estado: corriendo / terminado / etc.

Al hacer clic en una tarjeta se carga el proyecto entero (todos los databanks, todas las
estrategias) y se abre «Proyecto».

**Fuentes, que hoy están separadas y hay que fusionar:**
- `/api/projects` (`daemon/results/api.py:129-142`): barato, pero solo ve proyectos con `reports/`.
  Un proyecto recién construido no aparece.
- `daemon/progress.py` (`projects()` 29-38, `tasks()` 41-59): lee el `project.cfx` real.
- El número de estrategias sale de un roster por databank (`find.roster`, que ya usa
  `daemon/results/matrix.py:92`).
- **El estado del custodio se lee solo con `-project action=status`** (regla dura 3 de `CLAUDE.md`).
  Nunca `count`: sincroniza desde los ficheros y borra lo que solo está en memoria.

## 4 · Proyecto — el espacio de trabajo

Tres franjas, de arriba abajo:

### 4.1 · Arriba: el raíl del workflow, que es a la vez mapa y panel de automatización

El raíl de pasos que ya existe (`desktop/workflow/`) hace tres trabajos que el dueño pidió por
separado:
- **Mapa**: cada paso dice qué test es y en qué panel de databank vive su resultado. Al hacer clic se
  va a ese panel. Se genera de `WORKFLOW.md` y del catálogo de estudios (`daemon/workflow/steps.py`,
  `daemon/results/catalogue.py`), **nunca a mano**, para que no se desincronice.
- **Automatización**: cada paso y cada test tienen una casilla y la configuración a la vista. Hay un
  botón por test, uno por panel (corre los marcados de ese panel) y uno global «correr todo», como
  el play de SQX. Los resultados aparecen en su databank conforme terminan. Base: `daemon/runner/`
  ya sabe encontrar el input de cada estudio.
- **Estado**: hecho / en marcha / pendiente / bloqueado.

**Paralelismo** (el dueño: «en paralelo, no me hagas el error de antes»): un trabajo por carril, y
**paralelo por dentro** entre estrategias, con los núcleos físicos (`psutil`) y dentro del
presupuesto de RAM de Python (20 GB, `knowhow/perf/ram-budget.md`). Nunca estrategia a estrategia en
serie.

**Regla dura** (`ledger/gate.py`, `WORKFLOW.md` 165-178): el paso 20 no se puede leer ni pintar
hasta que los pasos 17, 18 y 19 estén los tres terminados. Su botón y su panel quedan bloqueados, con
el motivo escrito.

### 4.2 · En medio: el embudo de la población

Cuántas estrategias entran, cuántas pasan cada criba, y por qué se caen las que se caen. Base:
`desktop/funnel.py` (el embudo de la Puerta). Primera versión; se itera.

### 4.3 · Abajo: el panel de databanks, al estilo SQX

- Plegable y redimensionable en altura, como en SQX.
- **Dos niveles de pestañas.** Arriba, una por databank o test: Puerta IS/OOS (build+oos1 juntos),
  Cross Market, Cross Timeframe, MC Retest, SPP, WFM, WFC, CSCV, Market Surfaces, Cierre. La lista
  es de partida: se afina viendo la maqueta. Al hacer clic en una se abre debajo una segunda fila con
  sus subpaneles (dentro de Cross Market, cada mercado; dentro de Walk Forward, WFM / WFC / CSCV...).
- Las columnas se ordenan con un clic en la cabecera. Los valores negativos van en rojo (al dueño le
  gusta cómo está hoy el Net Profit).
- Con doble clic en una estrategia se abre «Estrategia».
- También a nivel de databank, no solo por estrategia: curva de equity agregada con sus
  estadísticas, la de SQX y la corregida con spread y slippage reales.
- **El Monte Carlo de operaciones sale de aquí.** Decisión del dueño del 2026-09-23: vive en
  portfolio, fuera de la secuencia.
- Botón «Recargar databank»: vuelve a leer de SQX qué estrategias hay ahora.

## 5 · Estrategia — la ficha

**Panel básico fijo arriba** (plegable), igual en todos los databanks:
- Curva de equity: la original de SQX **y** la recalculada con spread y slippage reales, con su
  evolución en el tiempo. Cada una se enciende y se apaga por separado.
- Estadísticas básicas del backtest: distribución de trades, curtosis, etc., con selector IS / OOS1 /
  OOS2. **OOS2 aparece bloqueado** («reservado: se abre tras los pasos 17, 18 y 19») hasta que esos
  tres pasos se hayan corrido. Después se añade como uno más.
- Base: `daemon/tearsheet/` y `daemon/tearmarket/` ya calculan casi todo esto. Es enganchar, no
  reconstruir.

**Debajo**, lo propio del databank desde el que se abrió la ficha. Las pestañas actuales (Ficha,
Cribado, Transferencia, Rotura, Optimización, Cierre, Lecturas) se mantienen, con el indicador de
pestaña activa cambiado a un **recuadro de bordes redondeados** en lugar de la raya inferior.

**Panel nuevo de metadatos**: indicadores y señal, long/short, spread y slippage del backtest, activo,
money management, cierre de los viernes. Depende del §12.2.

Cada métrica sin calcular dice **«no calculado»** y tiene un botón para calcularla para esta
estrategia o para todo el databank, en paralelo.

Cada panel lleva una descripción corta y precisa (las actuales están bien, no tocarlas) y, bajando
con el scroll, una más larga si hace falta.

## 6 · Visualizaciones

### 6.1 · Histogramas IS/OOS superpuestos

- En el mismo gráfico, cada serie con su interruptor para mostrarla u ocultarla.
- **Normalizados como densidad**, no como conteos: IS y OOS tienen longitudes distintas.
- **Solo para métricas por operación**: retorno por trade, duración, MAE/MFE, múltiplo R. Nunca
  Net Profit ni drawdown, que dependen de la longitud.
- Al lado, el desplazamiento de la mediana y el p-valor de una prueba KS, para que la degradación sea
  un número y no una impresión.
- Necesita el §12.3.

### 6.2 · Superficies (SPP, Market Surfaces)

- Un desplegable para elegir activo, y **2 o 3 superficies a la vez, una al lado de otra**. No hace
  falta superponerlas en 3D.
- **Misma escala de color** en todas, y θ₀ (los parámetros de la madre) marcado en cada una.
- Además, un **mapa de consenso**: en cuántos de los mercados cada celda es meseta. Resume nueve
  superficies en una imagen. `marketSurfaces` ya calcula ρ y Jaccard.
- El bloque `grid` del contrato ya sirve para esto.

### 6.3 · Los tests grandes (monkey, cross-market, MC Retest)

Al dueño le gusta mucho ver distribuciones, histogramas y gráficos en detalle. Referencia de diseño:
`docs/AgentPDFs/paneles-flask-inventario-2026-09-25.md`, y su lista de cierre (líneas 139-156) es de
obligado cumplimiento aquí:

1. selector de estrategia compartido entre estudios;
2. cajón de configuración completo, con una frase de ayuda por parámetro y desplegables cuando los
   valores son fijos;
3. los selectores no recalculan;
4. la distribución con el valor real marcado, más la tabla de percentiles, como dibujo base;
5. el cono de equity reutilizado donde haga falta;
6. «Re-correr este subtest» muestra el resultado nuevo **al lado**, sin pisar el guardado;
7. se puede correr un mercado suelto y fusionarlo con lo ya calculado;
8. los avisos colorean pero nunca eliminan, y hay una pestaña de glosario;
9. un trabajo por carril, con progreso visible, y paralelo por dentro (§4.1);
10. el botón de informe reproduce exactamente lo que hay en pantalla.

## 7 · Filtros y «Continuar workflow» — lo más delicado

### 7.1 · El constructor de filtros

- Filas de `métrica` + `operador` (>, <, ≥, ≤, =, entre) + `valor`, combinadas con AND.
- Las métricas disponibles salen de las columnas que el databank cargado tiene de verdad, incluidas
  las de estudios ya corridos. No hay lista fija.
- Para las distribuciones, un modo «la mediana cae dentro o fuera del intervalo de confianza X %».
  Usa `band` y `percentiles`, que el bloque `distribution` ya trae.
- **No se puede filtrar por métricas de OOS2.**
- **Cada filtro aplicado se apunta en el Ledger** (`ledger/`), con qué redujo, de cuántas a cuántas y
  sobre qué tramo. Es una búsqueda y cuenta como tal. Lo mismo para los borrados a mano.
- Los filtros se pueden guardar con nombre para reutilizarlos.

### 7.2 · El ciclo — confirmado por el dueño tras corregirse a sí mismo en la sesión

1. Filtrar o borrar a mano **no toca SQX**. Es una vista en Python: de 10.000 estrategias a 3.000, se
   sigue probando, se borran más a mano, quedan 2.000. El databank de SQX sigue intacto con 10.000.
2. **La lista de descartes se guarda en disco** (en `AlgoData`, por proyecto y databank), nunca solo
   en memoria: un reinicio del demonio no puede perderla.
3. **«Continuar workflow»** abre una **pantalla de confirmación**: «Se van a borrar 8.000 estrategias
   de `<databank>` en `<proyecto>` sobre `<install>`, y después se lanzará `<tarea>`». Solo al
   confirmar se aplica el `curate` y arranca la tarea.

**Reglas duras que este botón tiene que respetar:**
- El borrado pasa **solo** por `/curate` (`sqx/`), nunca por un camino nuevo. Una sincronización de
  SQX borra en disco lo que no está en memoria (regla 1).
- **Solo sobre los workers**, nunca sobre el maestro (regla 3).
- Antes de arrancar, comprueba que nadie más está usando ese install (regla 3: `ListAgents`, los
  proyectos recientes, el log del día). Todavía no hay bloqueo (`OPEN.md` #32) y un `stop` mata la
  ejecución de cualquiera. Si el install está ocupado, se niega y dice por qué.
- Arranca y para **solo** con `bin/sqx-worker.sh` o `sqx.variants.execute.awake()`.

## 8 · BIBLIOTECA

### 8.1 · Activos — lavado de cara

- Etiquetas legibles: «Slippage (Short)», nunca `slippage_short`; lo mismo con swap y los demás.
- Tramos con nombre: «Build», «OOS 1», «OOS 2»...
- MC Retest: bien como está (mín/máx), solo los nombres. **«Min Distance» vale `0`**, no `null`.
- **«Universo de retest» pasa a llamarse «Check de Cross Market»** y se construye por filas: botón
  «Añadir» → desplegable de categoría (Family / Structural) → desplegable con los activos disponibles,
  con nombre legible. Las filas se agrupan por categoría («Family: 6», «Structural: 4»), cada grupo
  con su color de fondo, y cada fila se puede quitar.
- **«Política y tramos» desaparece tal como está** (el dueño: «no hay Dios quien entienda nada»). En
  su lugar, dentro de cada activo, las fechas con datos disponibles (desde / hasta) y un selector
  para elegir las fechas de cada tramo.
- **«Retirados» se quita.** Ni se muestra.
- Lo «compartido / decidido para todos» sale de Activos y pasa al §8.2.
- Dos activos por fila en lugar de uno a pantalla completa, si cabe.

### 8.2 · Configuración SQX — zona nueva

Todos los parámetros de entrada de SQX, **por test y cada uno en su sección**: WFM (número de runs,
porcentajes), CrossTF, precisión de simulación, MC Retest, SPP... Todo lo que hoy vive en la
doctrina de construcción (`sqx/projects/doctrine.py`, `tasksettings.py`). **Desplegable en todo lo
que tenga valores fijos.** El ejemplo del dueño: los timeframes de CrossTF (M30, H1, H4, H12...) hoy
se escriben a mano.

### 8.3 · Datos — construirla de verdad

- Catálogo de `AlgoData`: qué exports hay, de qué fecha, cuánto ocupan.
- Series de velas de cada activo (diario, H1...).
- Estudios de volatilidad y evolución del spread (`studies/data/spread`, `feedQuality`), con
  gráficos.

Si esto vive aquí o al hacer clic en un activo de Activos, lo decide quien lo construya.

## 9 · OPERACIÓN

**Corrección de un malentendido de la sesión:** el Ledger **no** es un monitor de ejecuciones. Según
`desktop/ops/ledger.py`, es *«una línea por búsqueda que miró datos y redujo una población… tres
supervivientes de 10.000 no valen lo que tres de 50»*: el registro de comparaciones múltiples. Lo que
se solapa es Custodio con Generación.

- **«En marcha»** = Custodio (`ops/pulse.py`, el pulso de la ejecución larga en SQX_w2) + Generación
  (`generation.py`, las tareas del proyecto una a una), **del mismo proyecto y en la misma pantalla**.
- **«Registro de búsquedas»** = el Ledger renombrado, con una explicación a la vista de qué es y por
  qué importa. Ahí aparecen también los filtros del §7.1.
- El botón **«Recargar»** del pie de la barra lateral (`nav.py:75`): tooltip o texto que diga qué
  recarga.
- La franja de trabajos («0 en marcha, 0 en cola») gana una **barra de progreso de 0 a 100 %** por
  trabajo.

## 10 · Pulido global (fase 0)

- Fuente un poco más grande.
- **Etiquetas legibles desde un único sitio**: un glosario de etiquetas visibles del que beben todos
  los widgets, no arreglos pantalla a pantalla. Si no, el próximo estudio volverá a traer `null.draws`
  o `null.chunk3_traits`. Mayúscula inicial siempre («Configuración», «Historial», «Comparar»).
- **Nunca notación científica.** Número completo, o con «K» o «M».
- **Nunca mostrar el `identity`** (el hash SHA-256). Por debajo se sigue usando.
- Desplegables en lugar de texto libre cuando los valores son fijos.
- Algo más de separación entre secciones (bordes o recuadros sutiles), sin cambiar la estructura.
- **Un toque de color más alegre**, dentro de `theme.T`: sigue siendo un único tema, no un segundo.
- Las descripciones y la distribución general están bien: no se tocan.

## 11 · Modo lectura en Windows (fase 0)

Lo que en la sesión parecía un bug («`Test_USD2` y crossTF no están en ninguna instalación») es en
realidad esto: en el PC Windows del dueño, `config/machine.yaml` apunta a `~/Desktop/SQX…`, que no
existe, y todo lo que mueve SQX pasa por `bin/sqx-worker.sh`, que solo funciona en Linux. El fallo
real es que la ventana ofrece botones que ahí solo pueden fallar.

Decisión del dueño: la ventana **solo ejecuta en el servidor Linux**. Si no hay ningún install
alcanzable, entra en modo lectura: los botones de correr aparecen desactivados y un aviso visible
dice «Esta máquina no tiene SQX: modo lectura».

## 12 · Motor — lo que la ventana necesita y no es ventana

### 12.1 · WFC con composición libre

Hoy, `engines/variants/panel.py:15`:
`MODES = {"oos1_oos2": ("build", "oos1+oos2"), "oos2_only": ("build+oos1", "oos2")}`.

- Hay que pasar a una composición libre de cada lado a partir de {build, oos1, oos2}, incluida la
  opción de apagar oos1. `metrics.parquet` ya tiene las columnas: no hace falta volver a hacer
  backtests.
- **Cada composición leída se apunta en el Ledger.** No bloquea nada: deja rastro.
- Las composiciones que usan OOS2 solo se ofrecen cuando OOS2 ya está disponible (§0).
- Hay que dejar escrito en la ventana que **el PBO del CSCV no cambia con la composición** (parte el
  historial en 924 trozos por su cuenta, `panel.py` 36-40). Solo cambian cuatro números
  cronológicos. El WFC, en cambio, depende entero de la composición.

### 12.2 · Metadatos de estrategia

Hoy no existe: ningún código extrae señal, dirección, costes usados, money management o cierre de
viernes como campos. Fuentes:
- **La skill `/translate` ya convierte un `.sqx` en pseudocódigo legible.** Es la base para
  «indicadores y señal»; no hay que reescribirla.
- El XML de la estrategia (`strategy_Portfolio.xml`, cuyo SHA-256 normalizado es el `identity`) para
  la dirección, el money management y el cierre de los viernes.
- La ficha de costes del activo con la que se hizo el backtest, para el spread y el slippage.

### 12.3 · El bloque `distribution` con dos series

Para el §6.1: una extensión de `core/study/CONTRACT.md` que permite dos series (IS, OOS), más los
estudios que la emiten.

## 13 · Qué es firme y qué decide quien lo construye

**Firme:** todo el §0, las reglas duras del §7.2, qué se oculta (OOS2 antes de tiempo, el `identity`),
el orden de fases y la parada tras la maqueta.

**A criterio, se anota al cerrar y se revisa en la iteración:** la lista final de pestañas de
databank, la paleta concreta, si «Datos» vive en su zona o dentro de Activos, si el filtro admite
OR, y la disposición exacta del raíl.

## 14 · Cómo cierra

Como todos: **qué hizo · qué verificó, con la salida pegada · qué dejó sin hacer y por qué · qué
descubrió que merezca ir a `knowhow/`.** Además:
- `python3 tools/depmap.py && python3 tools/checks.py` limpio;
- los capítulos del manual de la ventana (`AlgoData/manual-fuentes/`, familia `02-la-ventana`)
  reescritos para las zonas nuevas, y `python3 tools/manual.py` (regla 8);
- `ui/README.md` con la nueva tabla de zonas y las decisiones del §0.
