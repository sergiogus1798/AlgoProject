# 56 · Lecturas nuevas de una estrategia o de una población — plan por frentes, autocontenido

**Tu oficio:** Python numérico sobre lo que ya está exportado; ningún frente toca SQX en vivo. Estadística
y diseño: **Opus** (25, 40, 26 una vez resuelta su pregunta); **Sonnet** para lo mecánico (mover el
prototipo, tabular, el capítulo del manual) — regla 17.
**Tu encargo:** cinco lecturas que hoy no existen. Cada una termina en **una decisión del dueño** (un filtro
al generar, un cribado, la métrica a optimizar o una lista), **con su coste en estrategias al lado de su
ganancia** y el espacio de búsqueda del que salió; «esto no aporta nada» es una respuesta válida. Los
frentes **no comparten ningún fichero**: cada fila de la tabla se despacha sola, con
«Lee `docs/encargos/56-lecturas-nuevas.md` y ejecuta el frente N».

Lee `CLAUDE.md` (reglas 7, 9, 11, 15, 16, 17) · `CODESTYLE.md` · `studies/CLAUDE.md` (dónde vive un estudio y
su forma) · `.claude/skills/new-study/SKILL.md` (**todo estudio nuevo se construye por `/new-study`**: son siete
sitios y cada uno olvidado es un hallazgo de auditoría) · `core/study/CONTRACT.md`.

## Estado del plan (lo actualiza cada sesión al cerrar)

| # | frente | modelo | depende de | estado |
|---|---|---|---|---|
| 1 | Estacionalidad: ¿el resultado se concentra en meses, días o horas, medido contra el azar? (ex 25) | Opus (estadística) | nada | sin empezar; no existe `studies/readings/seasonality/` |
| 2 | Señal agregada por plantilla: qué plantillas de la librería merece la pena seguir explotando (ex 26) | Opus | **la pregunta del dueño §2.0** (alcance 1, 2 o ambos) y §2.1 (ubicación) | sin empezar; **bloqueado por una pregunta** |
| 3 | Replay de operaciones, tier 2 del retraso: re-ejecutar cada operación desde una entrada desplazada (ex 16) | Opus (diseño) + Sonnet | decisiones §3.3; ver el bloqueo ya levantado | sin empezar; `engines/market/replay/` sólo tiene su README «not built yet» |
| 4 | Cerebro con probabilidades: regresión logística que da a cada estrategia la `p` de pasar el paso siguiente (ex 40) | Opus | decisiones del dueño (objetivo, corte, scikit-learn) | sólo prototipo en `scratch/cerebro/logit.py` (50 líneas, **fuera de git**) |
| 5 | Alfa y beta (ex 13) | — | — | **aparcado por el dueño — no se despacha** |

### Bitácora

- 2026-10-09 — Consolidado desde los encargos 25, 26, 16, 40 y 13 (originales en git en `c923d10`:
  `git show c923d10:docs/encargos/<fichero>`). Estado verificado ese día contra el disco.

---

## 0 · De dónde sale

- **25 y 26** nacen de la comparación con BuildAlpha del 2026-09-27: el dueño pidió el «seasonality
  breakdown» (rendimiento por mes, día de la semana y hora) y, en vez del desglose de señal por
  estrategia suelta, la versión **agregada por plantilla** («por templates estaría bien»).
- **16** sale del *item 4, tier 2* de su PDF `TRADE_LEVEL_TESTS.pdf`, el único de ese documento que no se pudo
  construir el 2026-09-24. El tier 1 (`studies/readings/entryQuality/delay.py`, función `given_up`) supone
  que las salidas no se mueven.
- **40**: conversación del 2026-10-01. El dueño preguntó si Jev (TypeSafe AI) podía juzgar cada paso;
  no: su probabilidad es la confianza del modelo en su lectura del texto, ni está calibrada con nuestros
  datos ni se puede auditar. Le gustó la alternativa: un modelo propio entrenado con nuestras estrategias, con
  probabilidades comprobables, que corre en local y no gasta tokens.
- **13**: decisión del dueño, 2026-09-24 (§5).

**Estándares del dueño para todo lo de aquí:** una lectura termina en decisión (CLAUDE.md, «Un análisis termina en
una decisión»); lo que tiene interfaz es una vista dentro de `ui/` en estilo terminal (`theme.T`, `QFrame`
`term`), nunca un panel aparte; el trader al azar (PSR, benchmark, nulos de entrada aleatoria) **sólo en OOS**
del principal o de los mercados adicionales, **nunca en el IS**, y **`oos2` está reservado**: no se lee sin
que el dueño lo autorice para esa tarea; gráficos grandes, alto contraste, escalas discretas, y cada
estadístico mostrado se explica (memoria `preferencias-de-visualizacion`).

---

## 1 · Estacionalidad (ex 25)

**La pregunta.** BuildAlpha lo llama «seasonality breakdown»: P&L por mes del año, día de la semana y hora.
Hoy nada dice si el resultado de una estrategia se concentra en unos meses, unos días o unas horas, o está
repartido.

**Una tabla de «julio rinde mejor» sin más es la trampa que este proyecto ya conoce** (`studies/CLAUDE.md`
§«Multiple testing es la condición por defecto»): 12 meses + 7 días + 24 horas son decenas de celdas y alguna
destacará por azar. Dos capas, no una:

1. **El desglose:** P&L, nº de operaciones y win rate por celda de calendario.
2. **El contraste contra el azar, obligatorio antes de enseñar la capa 1 como lectura:** ¿la concentración
   observada es mayor que la de repartir las mismas operaciones al azar entre las mismas celdas? Corrige por
   el número de celdas con `engines/inference` (Benjamini-Hochberg), como ya hacen `gate` y `snoopingScreen`.
   El azar es el de **OOS**, no el del IS.

**La decisión que debe salir:** «el resultado depende de una ventana de calendario estrecha (una hora, un
día)» = una **fragilidad a reportar**; o «el reparto es indistinguible del azar» = no aporta nada, dilo.

> **Choque con la regla 15 (posterior al encargo original).** La regla 15 prohíbe al builder dibujar bloques
> de tiempo (BarTime, CurrentTime, día de la semana o del mes) en cualquier estudio o generación. Este frente
> **sólo DESCRIBE una estrategia ya terminada por calendario; jamás devuelve un filtro horario o de calendario
> a una generación**. Ninguna salida suya alimenta el builder. El texto original no proponía actuar sobre el
> calendario; si al ejecutar aparece la tentación («filtrar las horas malas»), **es una pregunta para el
> dueño** (§Decisiones D-1), no un paso.

**Dónde va:** `studies/readings/seasonality/` (familia `readings/`, junto a `monkey`, `entryQuality`, `edgeCost`,
`structure`, `conditionalMap`; tabla en `studies/readings/README.md:5`). No es un paso numerado del WORKFLOW.
Forma (`studies/CLAUDE.md`, `/new-study`): `config.yaml` (granularidad mes/día/hora, umbral de significancia),
`tooltips.py`, `one.py`, `many.py` (probablemente sí: cuántas estrategias de la población muestran
concentración real separa el bloque del ruido), `report.py`, `README.md`.

**Qué reutilizar:**
- El *timestamp* de cada operación: `core/trades.py` / `core/tradestore.py`. No reimplementes el parseo del trade
  export (`knowhow/export/trade-export-columns.md`).
- **Huso horario: ya hay ficha** (el original decía «mídelo si no la hay»): `knowhow/export/feed-clock-timezones.md`
  — SQX sella en el reloj del broker del feed, nunca en UTC; `sqx.inspect.feeds.timezone(feed)` lo lee;
  `EETUS` = Nueva York + 7 h; las horas de cambio de hora se localizan con `ambiguous="NaT"` y se cuentan.
  Sin esto, todo lo horario sale 2-3 h desplazado. Decide y documenta si la hora de calendario es la del feed
  o UTC (D-2).
- El benchmark de `studies/readings/entryQuality/eratio.py:51-59` ya empareja el azar **hora a hora**: mira si se
  puede reutilizar esa maquinaria en vez de duplicarla (`studies/` nunca importa otro estudio: si hace falta,
  súbela a `engines/`).

**Decisiones a cerrar por escrito antes de programar:** hora de apertura, de cierre o ambas por separado
(abrir y cerrar pueden caer en celdas distintas); **mínimo de operaciones por celda** por debajo del cual la
celda se marca «sin datos suficientes», nunca se omite en silencio (ese mínimo lo decide el dueño: D-3).

**Verificación del frente:** `python3 -m pytest tests/test_seasonality.py -q` (caso de respuesta conocida:
operaciones sintéticas concentradas en una hora → la hora sale significativa tras BH; repartidas → ninguna) ·
`python3 tools/depmap.py && python3 tools/checks.py` · capítulo del manual (regla 8, `/manual-chapter`) · fila
en `studies/readings/README.md`.

---

## 2 · Señal agregada por plantilla (ex 26)

**Empieza por una pregunta, y nada es hacible hasta que el dueño la contesta.**

### 2.0 · El alcance (regla 11, léelo antes de tocar código)

«Desglose de la señal por plantilla» admite tres lecturas:
1. **Frecuencia y win rate de la condición fija de la plantilla** (el bloque que `template-run` comprueba que
   todas las estrategias llevan): cuántas veces dispara y qué acierto tiene esa señal, agregado sobre todas las
   estrategias construidas con esa plantilla y en todos los mercados donde se ha probado.
2. **Comparación entre plantillas:** cuáles producen estrategias con mejor relación señal/ruido — un ranking.
3. **Ambas**, con (1) como el dato por plantilla y (2) como la vista comparativa que lee (1). Es la que más
   encaja con la zona **Cobertura** de la ventana (`docs/AgentPDFs/catalogo-para-la-ui-2026-09-25.md:87-89`,
   `ui/README.md`), pero **no se asume**: pregúntala.

### 2.1 · Dónde vive (también se pregunta)
- **`studies/readings/` junto a `structure/`** si la unidad sigue siendo una población de una plantilla en un
  mercado (`structure` ya usa `sqx/structural/` para las ablaciones), con una capa aparte que reúne varias
  fichas para el ranking; o
- **un módulo bajo `sqx/`** si lo central es leer `AlgoData/projects/registry.csv` a través de muchos proyectos
  y mercados, más informe de cobertura que lectura.
Anota la elección y el porqué en el `README.md` que crees.

### 2.2 · Lo que hace falta para que agregar tenga sentido
- **La plantilla debe ser identificable en cada estrategia.** `registry.csv` ya guarda por proyecto la columna
  `template` (ruta en `AlgoData/templates/library/<nombre>/template.sqx`; 61 plantillas hoy) y `/template-run`
  (`.claude/skills/template-run/SKILL.md:140`) ya comprueba que las estrategias llevan el bloque fijo —
  reutiliza esa comprobación, no la repitas a mano. Catálogo: `sqx/templates/registry.py`.
- **Comparar entre plantillas exige mercados y ventanas comparables**, o se mezcla el efecto de la plantilla con
  el del mercado (`studies/CLAUDE.md`: «dos poblaciones estructuralmente distintas pueden compartir un
  databank: sepáralas antes de promediar» — el mismo riesgo, entre plantillas).
- **Corrige por el número de plantillas comparadas** si sale un ranking (`engines/inference`): una plantilla no
  «gana» por haberse probado en más mercados.

### 2.3 · La decisión que debe salir
**Una plantilla concreta a retirar de la rotación** porque su señal no bate el ruido en ningún mercado probado,
o **una a priorizar en la próxima ronda** porque su señal se sostiene entre mercados — **con en cuántos
mercados y estrategias se apoya la conclusión**. Una tabla de frecuencias sola no es el entregable.

> Nota sobre el cuidado: retirar una plantilla de la rotación no toca ningún proyecto del master ni cambia lo que
> una tarea construye (regla 3); sólo se le dice al dueño qué ve.

**Verificación:** respuesta del dueño a §2.0 y §2.1 anotada en la bitácora **antes** del primer fichero ·
test de respuesta conocida (`tests/test_<estudio>.py`) · `depmap` + `checks` · capítulo del manual · fila en el
README de la familia elegida.

---

## 3 · Replay de operaciones, tier 2 (ex 16)

**Qué es y qué no.** No es un motor de backtest: las entradas vienen de SQX y la lógica de entrada no se
reimplementa jamás. El simulador sólo **vuelve a ejecutar cada operación desde una entrada, posiblemente
desplazada `d` barras, caminando el M1 hasta que algo la cierra**. Existe porque el tier 1
(`studies/readings/entryQuality/delay.py`) es correcto para salidas por señal y por nº de barras pero **falso
para un stop o un target**, que se recalculan desde el precio de entrada nuevo.

**Dónde va:** el motor en `engines/market/replay/` (calcula y no juzga; sólo existe su `README.md` «not built
yet»); lo consume `entryQuality` y quien venga. Forma: `studies/CLAUDE.md`, `core/study/CONTRACT.md`.

### 3.1 · El bloqueo original, comprobado hoy (2026-10-09)
El encargo decía: «esta población no tiene ni un SL ni TP» (XAUUSD/MC_Trades: 960.705 operaciones, 236
estrategias, sólo `Exit After X Bars` / `Exit Signal` / `End Of Friday (Time)`) → no hay con qué validar el
recálculo de stops; «si no existe todavía, dilo y párate». **Esa parte del bloqueo ya no es cierta:** existen
poblaciones con stop (NIKKEI225 simpleL, USA500 indicesIBS, USDJPY doubleROC, entre 18 cosechas en
`AlgoData/harvest/`; 30-37 % de sus operaciones salen por `Close type` `AT_PRICE`), y `engines/market/reprice.py`
(commit `90d516d`, `reprice.real` línea 162) ya reproduce el precio de salida de SQX a 0,02 USD
(`knowhow/export/off-grid-stamps-and-stop-exits.md`).
**Pero no basta:** `reprice.real` rellena el stop **al precio que SQX exportó** (`Close price` ± slippage); no
recalcula el **nivel** del stop desde una entrada desplazada. Para eso hace falta la *definición* del stop de la
estrategia (múltiplo de ATR, puntos…), que el trade export no trae. **Primer paso:** mirar de dónde sacarla
(el `.sqx` de la estrategia, vía `sqx/inspect/`) y, si no se puede, párate y díselo al dueño (D-6) en vez de
inventar el recálculo.

### 3.2 · El criterio de aceptación, que es el encargo entero
**Con `d = 0` el simulador reproduce la lista de operaciones de SQX:** mismos instantes de salida, misma razón
de salida, P&L dentro de una tolerancia pequeña. Antes de eso, ningún resultado con retraso vale nada. Reporta la
**tasa de coincidencia** e investiga cada discrepancia (causas por orden de probabilidad: precisión intrabarra,
modelo de spread, redondeo, swap). El precedente: `studies/readings/monkey/calibrate.convention()` halló el
fill `open-open` con correlación 0,999985 (el segundo, 0,9629); la reconciliación licenció todo lo demás.

### 3.3 · Tabla de decisiones abiertas (sólo vivía aquí; cerrarlas por escrito)

| situación | qué decidir |
|---|---|
| SL y TP tocados en la misma barra M1 | el PDF propone SL primero (conservador). **Mide la convención de SQX antes de asumirla** |
| la operación dura menos que el retraso | no existe: se descarta y se reporta la fracción descartada por `d` |
| salida por señal desconocida tras un SL/TP que ya no ocurre | dejarla correr hasta su propio SL/TP o un tope de duración, marcarla, **reportar la fracción marcada**: si es grande, el tier 1 es más fiable que el tier 2 |
| entradas pendientes (stop/limit) | ¿retrasar la colocación de la orden o desplazar el nivel? Documenta la elección |

Las **dos variantes van las dos**: *retraso sólo en la entrada* (prueba la robustez temporal de la señal) y
*latencia completa*, entradas y salidas por señal retrasadas (el caso real en vivo).

### 3.4 · Rendimiento
El PDF propone Numba. **No está en `requirements.txt`; añadir una dependencia compilada es decisión del dueño**
(`sudo` pide contraseña aquí, las ruedas van a `~/.local`). Antes de pedirla: vectoriza **por lotes de
operaciones con numpy** (el truco de `engines/nulls/barrier.py`, que hace el triple barrier sobre miles de
corridas a la vez) y mide. El M1 del oro (7.949.285 barras) carga en 0,4 s con `core.barstore.source`: ni
memory-mapping ni trozos. `core.trades` y `engines.market.calibrate` ya dan `point_value` medido, coste real
`bruto − neto` y `engines.nulls.inputs.on_grid`.

**Ya registrado fuera de este fichero:** columnas del export (`knowhow/export/trade-export-columns.md`), sellos
fuera de rejilla y salidas por stop (`off-grid-stamps-and-stop-exits.md`), tipos de salida y librería M1
(`exits-and-m1-library.md`), fills y precios (`fill-and-pricing.md`).

**Cómo cierra:** la convención intrabarra que midas se **escribe en `knowhow/export/fill-and-pricing.md`**
(es el dato que hoy no tiene nadie) · test de reconciliación `d = 0` · `depmap` + `checks` · capítulo del manual.

---

## 4 · Cerebro con probabilidades (ex 40)

**Tu encargo:** convertir el prototipo en un estudio que dé a cada estrategia de un paso **la probabilidad de
pasar el paso siguiente** (y el oos2 cuando haya datos y el dueño lo autorice), comprobable con nuestros
resultados, y que acabe en una regla de `pipeline/autopilot/criteria.yaml` con lo que cuesta y lo que gana.

### 4.0 · Paso 1, antes de nada: sacar el prototipo de `scratch/`
`scratch/cerebro/logit.py` **sigue ahí (50 líneas) y `scratch/` está en `.gitignore`**: no está en git y se
perdería. Cópialo al estudio como primer paso, antes de reescribir nada.

### 4.1 · El prototipo ya corrido (2026-10-01) — sólo vivía aquí
Datos: los cinco databanks `AlgoData/metrics/XAUUSD/{OOS, OOS-Sharpe, OOS-Rexpect, OOS-Rexpect2,
OOS-Rsquared}/metrics.csv` (existen hoy), **49.124 estrategias** tras quitar las que repiten firma IS.
Objetivo `Profit factor (OOS) > 1` (tasa base 0,276). Entradas: las 21 métricas IS con `sign·log1p|x|`
estandarizadas. Modelo: regresión logística L2 (λ=1), Newton en numpy porque `sklearn` no está instalado
(sigue sin estarlo). Validación: se deja fuera un databank entero, se entrena con los otros cuatro y se rota.

| databank de prueba | AUC modelo | AUC mejor métrica IS sola | PF>1 en el 20 % mejor (base) |
|---|---|---|---|
| OOS | 0,730 | 0,706 | 0,453 (0,255) |
| OOS-Sharpe | 0,685 | 0,632 | 0,469 (0,291) |
| OOS-Rexpect | 0,740 | 0,668 | 0,571 (0,323) |
| OOS-Rexpect2 | 0,692 | 0,639 | 0,437 (0,268) |
| OOS-Rsquared | 0,701 | 0,632 | 0,411 (0,243) |

(AUC 0,69-0,74 el modelo; 0,73 frente a 0,706 de la mejor métrica sola en el databank OOS.)
**Calibración buena:** por deciles, predicho→real va de 0,04→0,02 a 0,53→0,49; el resto, a ±0,04.
**Como filtro:** corte `p ≥ 0,3` deja el 46 % de la población; entre las que se quedan el 41 % tiene PF OOS>1,
entre las descartadas el 17 %; se pierde el 32 % de las ganadoras. Con `p ≥ 0,4` se queda el 26 %, sube al
45 % y se pierde el 59 %. **Pesos:** mandan `DoF Ratio` (−), `# of trades` (+) y `Sharpe` (+); DoF ≈ trades /
parámetros, casi colineales: **no se lee cada peso por separado**.

### 4.2 · Lo que el prototipo NO prueba (hay que resolverlo)
1. **Un solo símbolo y una sola ventana OOS.** Dejar fuera un databank no es dejar fuera un periodo: las cinco
   poblaciones ven el mismo OOS de XAUUSD. Falta validar en otro símbolo (USDJPY tiene cosechas en
   `AlgoData/harvest/`) y en otro tiempo — con **runs completos** (con su `verdict.csv`), que hoy son pocos.
2. **PF OOS>1 es un objetivo flojo.** El útil es «pasa el paso siguiente del autopiloto» y, al final, oos2 o
   MT5. **El objetivo es un parámetro del estudio.**
3. Las cinco poblaciones salieron de **builds con fitness distintos**: no son una muestra al azar de lo que
   genera SQX.

### 4.3 · Qué construir
Un estudio (sitio exacto: `studies/CLAUDE.md`, vía `/new-study`) que hable el contrato de `core/study/`. Entra:
un paso y el objetivo. Sale: la `p` por estrategia **como dato del autopiloto** (`pipeline/autopilot/facts.py`
lista las claves de cada paso), la tabla de calibración y la **tabla de cortes** (qué se queda, % de aciertos
dentro y fuera, ganadoras perdidas). **Entrenar siempre dejando fuera un GRUPO** (un proyecto o un símbolo),
nunca filas sueltas: las estrategias de un mismo build se parecen y la validación saldría inflada. Capítulo de
manual (regla 8) y ficha en `knowhow/` con lo de §4.1 y §4.2.
Nota: los directorios de `metrics/` ya son por proyecto (`Test_…`) además de por símbolo; **reescribir contra el
código actual** la lectura de datos (`core.paths`; el prototipo tiene la ruta absoluta de XAUUSD, que
CODESTYLE.md prohíbe fuera de `core/paths.py`).

**Verificación:** test de respuesta conocida (`tests/test_<estudio>.py`) · `depmap` + `checks` · la tabla de
cortes enseñada al dueño.

---

## 5 · Alfa y beta (ex 13) — **aparcado por el dueño — no se despacha**

> *«El alpha y beta déjalo como un interrogante para hacer en última instancia.»* — dueño, 2026-09-24.
> Nadie lo coge hasta que la secuencia individual esté cerrada. Esta sección conserva lo que no está en otro sitio.

**Por qué está parado.** (1) Los pasos 1-21 deciden si una ventaja es real y qué forma tiene; una
descomposición factorial no cambia ninguna de esas decisiones. (2) El factor que más valdría —los retornos de las
EAs que ya se operan— mide redundancia con lo que ya está en producción, y hoy éstas son las primeras EAs: no hay
cartera contra la que regresar. (3) El intento anterior del dueño salía con una alfa siempre minúscula.

**La causa de la alfa minúscula (sólo vivía aquí).** Contar los días planos como retorno 0: con ocupación del
**7,4 %**, la alfa por día de calendario es **~1/13** de la alfa por día en mercado. No estaba mal calculada;
estaba dicha en una unidad que la hace parecer nada.
**⚠ Y el error contrario:** quitar los ceros **no mejora la significancia** (sube la media, sube la desviación,
baja la n; el t apenas se mueve, y eso es lo correcto). Si algún día se construye, se reportan **las dos alfas y
la ocupación, siempre juntas**.

**Antesala ya construida:** `studies/closing/exposure/` (paso 21; `occupancy.presence`,
`occupancy.py:81`): cuánto del movimiento del mercado ocurrió con posición y cuánto tenía el signo correcto. Si
sale alta, la regresión sobra: es beta con horario.

**Los cinco puntos que faltarían el día que se levante:**
1. equity **marcada a mercado** por día, no el beneficio imputado al día del cierre (hoy el módulo usa lo
   segundo, que es lo que reporta SQX, y lo declara);
2. α con t de **Newey-West** (los retornos diarios de posiciones de varios días están autocorrelacionados);
3. el **appraisal ratio** (α/σ_ε) como métrica de puerta en lugar del Sharpe bruto;
4. betas rodantes (deriva de estilo);
5. R²: **R² alto = la búsqueda redescubrió un efecto conocido con parámetros de más**.

---

## Decisiones del dueño — pregúntalas (regla 11)

| id | pregunta | lecturas |
|---|---|---|
| D-1 (ex 25) | Si la lectura de estacionalidad muestra una hora o un día malo, ¿qué se hace con ello? | (a) sólo se reporta como fragilidad; (b) se propone un filtro horario a la generación — choca con la regla 15, necesita tu OK explícito |
| D-2 (ex 25) | ¿En qué reloj se agrupa el calendario? | hora del feed (broker) · UTC |
| D-3 (ex 25) | Mínimo de operaciones por celda para no marcarla «sin datos suficientes» | lo fijas tú; no se inventa un umbral |
| D-4 (ex 26, §0) | Alcance del desglose por plantilla | 1 frecuencia y win rate por plantilla · 2 ranking · 3 ambos (§2.0) |
| D-5 (ex 26, §1) | Ubicación | `studies/readings/` junto a `structure` · módulo bajo `sqx/` (§2.1) |
| D-6 (ex 16) | Si no se puede obtener la definición del stop de la estrategia, ¿se acepta un tier 2 sólo para salidas por señal y barras, o se espera? | tier 2 parcial · esperar |
| D-7 (ex 16, §3.4) | ¿Se añade Numba a `requirements.txt` si el lote numpy no alcanza? | sí · no (primero se mide) |
| D-8 (ex 40) | Objetivo de la `p` | PF OOS>1 · pasar el paso siguiente del autopiloto · pasar oos2 (**reservado**: requiere tu autorización para esa tarea) · pasar MT5 |
| D-9 (ex 40) | Corte de `p` para `criteria.yaml` | se te enseña la tabla de cortes con coste y ganancia y eliges |
| D-10 (ex 40) | `scikit-learn` o seguir con numpy | `pip install --user scikit-learn` (sudo pide contraseña) · numpy |
| D-11 (ex 40) | ¿Se espera a tener runs completos de otro símbolo para validar, o se publica con la limitación de §4.2? | esperar · publicar con aviso |

---

## Lo que no tocas

- **El master (5050)** y los proyectos que tiene; **ningún frente lanza SQX ni MetaTrader**: todo lee lo ya
  exportado (`metrics/`, `harvest/`, trade export). Si un frente pide una corrida nueva, se pide al dueño por
  `bin/workflow.sh` (regla 19), en proyecto custom y esperando con `/sqx-wait`.
- **`oos2`**, sin autorización explícita del dueño para esa tarea.
- `pipeline/autopilot/criteria.yaml` y `ledger/thresholds.yaml`: los umbrales son del dueño; un valor que él no
  ha fijado no se escribe (frente 4: se le enseña la tabla). Los umbrales nuevos van al final de la sección del
  estudio, leídos como `ledger:<clave>`.
- Los ficheros de los otros frentes de este plan y de los encargos 49-55; `docs/DEPENDENCIES.md` se regenera,
  no se mezcla; `requirements.txt` sólo gana líneas.
- Datos pesados al data root (regla 7), nunca al repo. El dueño hace los commits (regla 12).

## Objetivo — un comando

No hay un único comando para el encargo entero: dos frentes terminan en una **respuesta del dueño** (2 y 4), uno
en una medición contra SQX (3) y uno está aparcado (5). Por eso **no se despacha como bucle**. Cada frente
cierra con su propia **Verificación**:

- **Frente 1:** `python3 -m pytest tests/test_seasonality.py -q && python3 tools/depmap.py && python3 tools/checks.py`
- **Frente 2:** respuestas D-4 y D-5 en la bitácora; después `python3 -m pytest tests/test_<estudio>.py -q && python3 tools/depmap.py && python3 tools/checks.py`
- **Frente 3:** tasa de coincidencia con `d = 0` reportada por escrito, la convención de §3.3 en `knowhow/export/fill-and-pricing.md`, y el mismo `pytest && depmap && checks`
- **Frente 4:** `scratch/cerebro/logit.py` ya copiado al estudio, `pytest` verde, la tabla de cortes en manos del dueño
- **Frente 5:** nada que verificar.

## Cómo cierras

Por frente: **qué hizo** · **qué verificó**, con la salida pegada · **qué dejó sin hacer y por qué** · **qué
descubrió** para `knowhow/` (una ficha por hecho no obvio: el huso horario, la convención SL/TP en la misma
barra, la calibración del cerebro) · la fila de la tabla de estado y la bitácora actualizadas · la lista de
ficheros cambiados. Un frente cumplido se borra de este fichero diciendo dónde fue cada parte. Último renglón:
**¿Quieres hacer el commit?**
