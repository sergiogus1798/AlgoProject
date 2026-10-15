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
| 1 | Estacionalidad: ¿el resultado se concentra en meses, días o horas, medido contra el azar? (ex 25) | Opus (estadística) | nada | **hecho 2026-10-14** → `studies/readings/seasonality/` (§1 borrado: ver bitácora) |
| 2 | Señal agregada por plantilla: qué plantillas de la librería merece la pena seguir explotando (ex 26) | Opus | **la pregunta del dueño §2.0** (alcance 1, 2 o ambos) y §2.1 (ubicación) | sin empezar; **bloqueado por una pregunta** |
| 3 | Replay de operaciones, tier 2 del retraso: re-ejecutar cada operación desde una entrada desplazada (ex 16) | Opus (diseño) + Sonnet | decisiones §3.3; ver el bloqueo ya levantado | **hecho 2026-10-14** (motor `engines/market/replay/`; `entryQuality` lo consume en las estrategias con stop) |
| 4 | Cerebro con probabilidades: regresión logística que da a cada estrategia la `p` de pasar el paso siguiente (ex 40) | Opus | decisiones del dueño (objetivo, corte, scikit-learn) | sólo prototipo en `scratch/cerebro/logit.py` (50 líneas, **fuera de git**) |
| 5 | Alfa y beta (ex 13) | — | — | **aparcado por el dueño — no se despacha** |

### Bitácora

- 2026-10-09 — Consolidado desde los encargos 25, 26, 16, 40 y 13 (originales en git en `c923d10`:
  `git show c923d10:docs/encargos/<fichero>`). Estado verificado ese día contra el disco.
- 2026-10-14 — **Frente 1 hecho y borrado de aquí.** El estudio es `studies/readings/seasonality/`
  (README: el nulo, las palabras, los límites), su test `tests/test_seasonality.py`, umbrales
  `seasonality.min_trades` (30, D-3) y `seasonality.fdr_q` (0,05, **pendiente de que el dueño lo
  confirme**) en `ledger/thresholds.yaml`, ficha `knowhow/research/seasonality-indistinguishable-from-chance.md`,
  capítulo del manual en `06-lecturas`. Decisiones aplicadas: D-1 sólo informa, D-2 UTC, D-3 30;
  apertura y cierre se leen las dos por separado. Lectura: XAUUSD donchian2 H1 1/300 y USDCAD
  reversion M30 0/64 con celda descubierta, bajo el techo del azar (15 y 3,2) → el calendario no
  explica el resultado; no aporta filtro (y la regla 15 no lo permitiría).
- 2026-10-14 — **Frente 3 entero: `entryQuality` consume el replay** (`delay.replayed`, `inputs.stopped`): una cosecha `Stop_p90` da dos tablas (sólo entrada tarde / latencia completa) con `descartadas` y `desconocidas`; sin tabla de minutos; un export con SL que no sea cosecha se rechaza; el tier 1 queda sólo para estrategias sin stop (`tests/test_entry_delay_replay.py`). USDJPY doubleROC, 1 barra: entregado 2,0 $ (tier 1) → 9,6 $ (tier 2).
- 2026-10-14 — **Frente 3: motor y reconciliación hechos.** `engines/market/replay/` (walk, reconcile,
  inputs; README con la tabla por cosecha), `tests/test_replay.py`. La definición del stop SÍ existe
  (D-6 se cumple sin esperar): las cosechas `harvest/<P>/Stop_p90/` nombran su lote de variantes y su
  `x` (SL = x · ATR(20) Wilder de la barra anterior). Con `d = 0` reproduce el 99,4-99,9 % de 18.520
  operaciones de siete cosechas (barra y razón de salida), 98,8-100 % de los stops a ≤ 2 ticks. Convenciones
  nuevas en `knowhow/export/fill-and-pricing.md` (nivel redondeado al tick; hueco → se llena a la
  apertura). SL+TP en la misma barra ya estaba medido (`sl-pt-same-bar-convention.md`). Sin Numba (D-7):
  0,01 s por cosecha. Lectura (`knowhow/research/delay-tier1-overstates-stop-strategies.md`): el tier 1
  sobrestima el P&L con retraso de las estrategias con stop (NIKKEI simpleL, 1 barra: 42,0 frente a 27,0 $
  por operación) → para estrategias con stop sólo vale el tier 2.

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

## 3 · Replay de operaciones, tier 2 (ex 16) — HECHO 2026-10-14

El motor está hecho y reconciliado (bitácora 2026-10-14; `engines/market/replay/README.md`). Queda
**que `studies/readings/entryQuality/` lo consuma** para las estrategias con stop: hoy su `delay.py`
(tier 1) mantiene las salidas fijas, que sobrestima el P&L con retraso de una estrategia con stop.
No se hizo el 2026-10-14 porque `entryQuality/one.py` lo tenía otra sesión. Al hacerlo: las dos
variantes (sólo entrada y latencia completa), reportar las fracciones `dropped` y `unknown`, la lectura en la
ventana, y el capítulo del manual de `entryQuality` actualizado. La entrada al motor es
`engines.market.replay.inputs.ready(harvest/<P>/Stop_p90/<día>)`: una cosecha sin stop injertado no
tiene `x` y se niega.

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

**Contestadas por el dueño (2026-10-14)** — lo que sigue manda sobre la lista de abajo:
- D-1 → **sólo se informa** (regla 15). D-2 → **UTC**. D-4 → **ambos** (frecuencia y win rate, y ranking). D-5 → **`studies/readings/`**.
- D-6 → **esperar** a la definición del stop. D-7 → **medir antes** de añadir Numba. D-8 → **la p predice pasar el paso siguiente**.
- D-10 → **numpy**. D-11 → **esperar** a corridas de otro símbolo.
- Siguen abiertas: D-3 (mínimo de operaciones por celda) y D-9 (corte de p, con la tabla delante).
- D-3 → **30 operaciones** por celda. Sigue abierta D-9.


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

- **Frente 2:** respuestas D-4 y D-5 en la bitácora; después `python3 -m pytest tests/test_<estudio>.py -q && python3 tools/depmap.py && python3 tools/checks.py`
- **Frente 4:** `scratch/cerebro/logit.py` ya copiado al estudio, `pytest` verde, la tabla de cortes en manos del dueño
- **Frente 5:** nada que verificar.

## Cómo cierras

Por frente: **qué hizo** · **qué verificó**, con la salida pegada · **qué dejó sin hacer y por qué** · **qué
descubrió** para `knowhow/` (una ficha por hecho no obvio: el huso horario, la convención SL/TP en la misma
barra, la calibración del cerebro) · la fila de la tabla de estado y la bitácora actualizadas · la lista de
ficheros cambiados. Un frente cumplido se borra de este fichero diciendo dónde fue cada parte. Último renglón:
**¿Quieres hacer el commit?**

## Contestadas por el dueño (2026-10-15)

- `seasonality.fdr_q` = 0,05, confirmado.
