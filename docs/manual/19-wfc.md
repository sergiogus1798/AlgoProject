# 19. Walk forward correlation — ¿sirve de algo optimizar los parámetros?

### Qué pregunta responde

**Si eliges los parámetros de una estrategia por lo bien que van dentro de muestra, ¿siguen yendo
bien fuera?**

Esa es toda la pregunta, y es la que decide si la optimización es trabajo o es autoengaño. El
estudio coge una estrategia madre, fabrica muchas versiones de ella con parámetros distintos,
las retestea todas con la misma partición IS/OOS, y dibuja un punto por combinación: lo que ganó
dentro contra lo que ganó fuera.

- Si la nube sube en diagonal, el ranking dentro de muestra **predice** el de fuera. Optimizar
  compra algo.
- Si la nube llena los cuatro cuadrantes, no predice nada. Lo que ganas optimizando dentro te lo
  quitan fuera, y el "mejor" juego de parámetros del backtest es ruido con buena pinta.

### Cuándo lo usas, y cuándo no

**Lo usas** cuando ya tienes una estrategia que te interesa y quieres saber si sus parámetros
significan algo, antes de gastar días en afinarlos. También cuando quieras comparar dos estrategias
por su *robustez* en vez de por su beneficio.

**No lo usas** para elegir los parámetros. Este estudio no te dice cuáles poner: te dice si merece
la pena elegirlos. Si sale que no, la respuesta es cambiar de estrategia o de enfoque, no buscar
mejor dentro del mismo grid.

**Tampoco lo usas con cuatro puntos.** Con una docena de combinaciones el margen de error de una
correlación es enorme, y el estudio te lo dirá a la cara (`indeciso`) en vez de fingir una
conclusión. `indeciso` significa **fabrica más puntos**, no "baja el umbral".

### Antes de empezar

Tres cosas, y las tres son bloqueantes:

1. **Los costes del símbolo tienen que estar acordados.**

   ```bash
   python3 -m core.assets XAUUSD
   ```

   Si sale con código distinto de cero, párate. Hoy XAUUSD sale en 0 pero con los tres valores
   marcados **PROVISIONAL**: son los defaults de SQX, no cifras pactadas con Infinox. Todo número
   con coste que produzcas arrastra esa salvedad, y el `state.json` del pipeline la marca con
   `costs_provisional: true`.

2. **Tiene que existir el export SPP de la estrategia**, en
   `AlgoData/raw/<proyecto>/<databank>/<fecha>/`. Es lo que lee `strategies/sppUltra` para decidir
   qué parámetros mueven el resultado y con qué niveles.

3. **El custodio tiene que poder arrancar.** Es el install `~/Desktop/SQX_w2`, puerto 5070, y es
   quien ejecuta los retests. El maestro no se toca en ningún momento.

### Cómo se ejecuta

**La forma corta, y la que vas a usar.** Una línea hace las siete etapas:

```bash
python3 -m pipeline.run --project XAUUSD --databank SPP_IS --strategy "Strategy 17.9.39"
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | proyecto tal y como aparece en SQX |
| `--databank` | no | carpeta del export, con guiones bajos. Por defecto `SPP_IS` |
| `--strategy` | no | repetible. Por defecto, **todas** las del export |
| `--day` | no | fecha del export. Por defecto la más reciente |

**Cuántas combinaciones se fabrican** lo decide `sample` en `pipeline/config.yaml`. El valor por
defecto es **2.000**, y no es un número redondo elegido a ojo: es donde la respuesta deja de ser
"no se puede saber". Medido sobre esta misma estrategia el mismo día:

| puntos pedidos | utilizables | rho | intervalo 95 % | veredicto |
|---|---|---|---|---|
| 11 | 9 | 0,18 | [−0,55, 0,75] | `indeciso` |
| 150 | 74 | 0,23 | [−0,00, 0,43] | `indeciso` |
| 600 | 297 | 0,22 | [0,10, 0,32] | `indeciso` |
| **2.000** | **1.001** | **0,19** | **[0,13, 0,25]** | **`no_fiable`** |

Fíjate en que **rho apenas se mueve** (0,18 → 0,19): lo que cambia es la anchura del intervalo. Con
once puntos el número ya era el correcto y no servía para nada. Con `sample: 0` fabrica el diseño
entero del brief. Están **repartidas** por todo el diseño, no cogidas por arriba — eso importa, y el
apartado *Qué NO te dice* explica por qué.

La corrida entera de 2.000, arrancando con el custodio apagado: **2 min 16 s y 28 MB**.

**Las etapas por separado**, si quieres repetir solo una:

```bash
python3 -m sqx.variants.make    --brief <design_brief.json> --project XAUUSD --sample 11
python3 -m sqx.variants.execute --work <dir>     # carga en el custodio, retestea, exporta
python3 -m sqx.variants.collect --work <dir>     # une el panel al manifiesto → metrics.parquet
python3 -m sqx.variants.equity  --work <dir>     # las curvas diarias de los 3 tramos, unidas
python3 -m strategies.walkForwardCorrelation.report --work <dir> [--split oos2_only]
```

### El suelo de operaciones: 50, y es duro

**Ningún backtest con menos de 50 operaciones en todo el periodo (`build`+`oos1`+`oos2`) entra en
ninguna estadística.** Decisión del dueño, 2026-09-24. Está en `wfc.min_trades_total` de
`assets/_build.yaml` y lo aplica `collect.py`: lo que no llega **no se escribe** en
`metrics.parquet`, así que ningún estudio de aguas abajo puede volver a meterlo por descuido.

Se cuenta por **variante × mercado**, porque un backtest es una estrategia corriendo en un mercado.
Una variante que opera 400 veces en oro y 9 en plata tiene un resultado y un no-resultado:

```
P00003  Main      300 operaciones   usable=True
P00003  XAGUSD      9 operaciones   usable=False
```

No desaparece sin decirlo. `collect.py` avisa:

```
⚠️  1 variantes y 12 celdas (variante x mercado) operan menos de 50 veces en
    build+oos1+oos2 y quedan FUERA de toda estadistica. Siguen en segments.parquet
    con usable=False, por si hace falta mirarlas.
```

y el recuento queda en `collected.json` (`thin`, `thin_cells`, `floor`) y en la nota del `wfc.html`.

⚠️ **Hay un segundo suelo, y es otra cosa.** `min_trades: 30` en el `config.yaml` del WFC mira cada
**lado** de la partición por separado: una variante puede sumar 200 operaciones y llevar sólo 4 en
el tramo que hace de fuera de muestra. Actúa sobre lo que ya pasó el duro, y el informe dice cuántos
puntos cayó cada uno:

```
PROGRESS 100 rho 0.19 — no_fiable (1001 puntos; 37 fuera por pocas operaciones en total,
                                   962 por pocas en un lado)
```

Con `split_mode: oos2_only` ese segundo suelo aprieta más, porque el lado fuera de muestra son 3,7
años en vez de 10. Si se come el lote, se baja **ése**, no el duro.

### Los tres tramos, y las dos maneras de leerlos

El lote se retestea **una vez** en tres tareas de SQX —`build`, `oos1` y `oos2`, cada una a sus
propios costes: `docs/manual/37-wfc-retest.md`— y de ahí salen tres paneles. La cosecha los une:

- **suma lo que es sumable** (neto, número de operaciones, beneficio y pérdida brutos), así que el
  profit factor de una unión es `Σ bruto ganado / Σ bruto perdido` y no el promedio de tres profit
  factors, que pesaría un tramo de cinco años igual que uno de diez;
- **recalcula lo que no lo es** (drawdown y Sharpe) sobre la curva diaria ya unida, porque una unión
  puede cruzar un valle más profundo que cualquiera de sus partes.

Y con eso, el mismo lote responde a **dos preguntas distintas** (decisión del dueño, 2026-09-24):

| modo | dentro de muestra | fuera de muestra | qué pregunta |
|---|---|---|---|
| `oos1_oos2` | `build` | `oos1` + `oos2` | la normal: ¿lo que se construyó predice todo lo que vino después? |
| `oos2_only` | `build` + `oos1` | `oos2` | **la estricta**: dando por vistos los dos primeros tramos, ¿sigue apareciendo en el que no ha mirado nadie? |

El default está en `strategies/walkForwardCorrelation/config.yaml` (`split_mode`), hoy `oos2_only`.
`--split` lo pisa para una ejecución suelta. **Cambiar de modo no re-corre ningún backtest**: las
columnas de los dos ya están en `metrics.parquet`.

### El reconocimiento SPP, dentro del proceso

El SPP es la etapa que dice **qué parámetros mueven el resultado y con qué recorrido**. Sin él no
hay rejilla. Corre en el custodio, sobre una sola madre:

```bash
python3 -m sqx.variants.spp --work <dir> --mother "<ruta al .sqx>" --kind spp_is   --chart "XAUUSD_DukasM1_Infinox M30 5"
```

`--kind` es `spp_is` (2008–2017) o `spp_oos` (2018–2022); las ventanas salen de la tarea del
donante. Los mandos están en `sqx/variants/config.yaml`, bloque `spp`: `steps`, `spread_pct` y
`keep_pct`.

⚠️ **`keep_pct` (el `PctToPass` de SQX) va a 0**, y no es un descuido. El donante lo tiene a 80
porque está **filtrando una población**; aquí se está **mapeando una superficie**, y hacen falta los
perfiles de todas las madres, también de las que fallan. Con 80, una madre con el 70 % de
permutaciones rentables es rechazada y **su perfil no se escribe en ningún sitio**.

**Cuánto tarda, y por qué parece colgado.** Un SPP sobre una madre real de 22 parámetros a precisión
de 1 minuto escribe sus 22 líneas de log **en tres segundos** y luego no dice nada durante **más de
media hora**. `action=status` marca `Total tested 0` todo ese rato: no existe progreso por
permutación en SQX. La señal de que está vivo es **la memoria del JVM**, que sube sin parar mientras
acumula resultados — se midieron 23,6 → 36,9 GB sobre un heap de 48 GB.

| | señal | qué significa |
|---|---|---|
| RSS del JVM subiendo, sin log | está trabajando | espera |
| RSS plano, sin log | **colgado** | párralo |

⚠️ **La memoria es el límite, no el tiempo.** El perfil acaba pesando ~20 MB en disco pero decenas
de gigas mientras se construye. **No lances dos SPP a la vez en el mismo install.**

### Cambiar cómo se retestea: el arnés

El retest lo ejecuta un **arnés** en el custodio: el proyecto `Retester` de `~/Desktop/SQX_w2`, con
**una sola tarea Retest** — sin tarea Build y sin `GoToTask`, que es lo que lo hace seguro de
arrancar. Se reconstruye con:

```bash
# retest normal, solo XAUUSD
python3 -m sqx.variants.harness --kind retest --project Retester --output RetestOut   --chart "XAUUSD_DukasM1_Infinox M30 5"

# añadiendo un cross-check en otro mercado (la plata, mismo bróker y feed)
python3 -m sqx.variants.harness --kind retest --project Retester --output RetestOut   --chart "XAUUSD_DukasM1_Infinox M30 5" --chart "XAGUSD_DukasM1_Infinox M30 5" --markets
```

| flag | qué hace |
|---|---|
| `--kind` | `retest`, `spp_is` o `spp_oos`. De qué tarea del donante se copia |
| `--chart` | repetible, **el principal primero**: `'SÍMBOLO TIMEFRAME SPREAD'` |
| `--markets` | activa el cross-check en mercados adicionales |
| `--spp-steps`, `--spp-spread` | activan el SPP con esa resolución y ese ±% |

⚠️ **El custodio tiene que estar parado**: SQX reescribe el `project.cfx` al salir, así que un
cambio hecho mientras está levantado se pierde en silencio. El comando se niega a escribir si
detecta el puerto abierto.

⚠️ **Todos los `<Chart>` se reapuntan, incluidos los de cross-checks desactivados.** SQX resuelve
todos los símbolos de la tarea al cargar el proyecto, y uno que no existe mata la tarea sin
hacerla fallar: `Total tested 0`, sin error, para siempre.

⚠️ **El arnés se construye copiando una tarea del donante que sí ha corrido**, nunca a mano. Una
tarea a la que le falta `<Databanks retestSelected="false">` retestea "la selección", la selección
está vacía, y reporta cero sin quejarse. Eso costó dos días.

### Qué produce

Todo en `AlgoData/pipeline/<proyecto>/<estrategia>/`:

| fichero | qué es |
|---|---|
| `plan.csv` | el diseño completo: qué combinaciones y de qué estrato |
| `sqx/P*.sqx` | las estrategias fabricadas. **Es lo único pesado**, y lo que se borra al final |
| `manifest.parquet` | contrato C2: qué es cada fichero, leído **del disco**, no de lo que se pretendía |
| `retest_build.csv`, `retest_oos1.csv`, `retest_oos2.csv` | el panel de cada tramo, tal y como lo escupe SQX |
| `equity.parquet` | la P&L diaria del activo principal, **los tres tramos unidos** en una sola serie continua |
| `equity_markets.parquet` | lo mismo para cada mercado adicional, en formato largo (fecha, variante, mercado, tramo) |
| `segments.parquet` | las 82 métricas que SQX guarda, por variante **× tramo × mercado**, más las uniones y el `usable` de cada celda. **Aquí sí están los descartados** |
| `metrics.parquet` | contrato C3: las métricas de cabecera por tramo y por unión, unidas al manifiesto, **sin los backtests que no llegan a 50 operaciones**. Es la tabla del estudio |
| `wfc.html` | **el gráfico**. Ábrelo en el navegador |
| `wfc.json` | rho, su intervalo, el veredicto y cuántos puntos se descartaron |
| `state.json` | el libro mayor. Sobrevive al borrado de las variantes |

### Cómo se lee el resultado

Por pantalla ves esto:

```
  ran        python3 -m sqx.variants.execute --work .../Strategy_17-9-39
   | PROGRESS 2 despertando el custodian
   | PROGRESS 95 2000 de 2000 reteseadas
   | custodian stopped
   | PROGRESS 100 2000 variantes x 3 tramos, build: 2000 en disco, oos1: 2000 en disco, oos2: 2000 en disco
  collected  python3 -m sqx.variants.collect --work .../Strategy_17-9-39
   | PROGRESS 100 4 resultados distintos entre 5 controles
  wfc        python3 -m strategies.walkForwardCorrelation.report --work .../Strategy_17-9-39
   | PROGRESS 55 1001 puntos utiles de 2000
   | PROGRESS 100 rho 0.19 — no_fiable
   |
   | rho 0.19, intervalo [0.13, 0.25] entero por debajo de 0.3: optimizar en IS no compra
   | nada fuera
```

El custodio lo arranca y lo para **el propio comando**. Si ya estaba levantado, lo deja levantado:
alguien lo estará usando.

**Línea por línea, porque cada número decide algo:**

- **`4 resultados distintos entre 5 controles`.** Es la comprobación más importante de todo el
  estudio y conviene entenderla. Una variante recién fabricada lleva dentro los resultados **del
  padre** — SQX los guarda en `settings.xml` y la fábrica solo reescribe los parámetros. Si el
  retest no llegó a ejecutarse, las variantes no salen vacías: salen **con los números del padre**,
  todas iguales, y el estudio entero parecería correcto. Por eso se cuenta. Si salieran los cinco
  iguales, la etapa aborta y te dice que no uses el lote.

  *(Cuatro de cinco, no cinco de cinco, es lo correcto: uno de los controles es un "par inerte", una
  copia que solo cambia en un parámetro **congelado**. Que dé idéntico es la prueba de que
  congelarlo estaba justificado.)*

- **`1001 puntos utiles de 2000`.** Se descartan las combinaciones que operan menos de 30 veces en
  alguna de las dos muestras. No es limpieza: una combinación que apenas opera da un beneficio que
  mide una o dos operaciones, y son la mitad del lote: dejarlas dentro convierte la
  correlación en un artefacto de los rincones degenerados del grid.

- **`rho 0.19`.** La correlación de **rangos** (Spearman) entre el beneficio dentro y fuera. Se usan
  rangos y no valores para que una combinación desbocada no decida ella sola el resultado.

- **`intervalo [0.13, 0.25]`.** Y esto es lo que de verdad hay que leer. Es el margen de error al
  95 % sobre ese 0,19. Aquí está **entero por debajo** del umbral de 0,30, así que la conclusión sí
  se sostiene: hay una relación positiva y real —el intervalo no toca el cero— pero **demasiado
  débil para ordenar nada**. Elegir parámetros por su beneficio dentro de muestra, en esta
  estrategia, no compra prácticamente nada fuera.

Los tres veredictos posibles:

| veredicto | qué significa | qué haces |
|---|---|---|
| `fiable` | el intervalo entero por encima del umbral | optimizar en IS sirve; sigue adelante |
| `no_fiable` | el intervalo entero por debajo | optimizar no compra nada; cambia de estrategia |
| `indeciso` | el intervalo cruza el umbral | **fabrica más puntos**. No bajes el umbral |

El umbral (`rho_floor`, por defecto 0,30) es tuyo y está en
`strategies/walkForwardCorrelation/config.yaml`. Cambiarlo **no obliga a repetir nada**: el estudio
guarda los números, no los juicios, y solo se recalcula el veredicto.

### Un ejemplo completo

```bash
# 1. ¿Qué costes se aplican? Bloqueante.
python3 -m core.assets XAUUSD

# 2. Once combinaciones, de punta a punta: diseño, fabricación, retest, panel y gráfico
python3 -m pipeline.run --project XAUUSD --databank SPP_IS --strategy "Strategy 17.9.39"

# 3. Mira el gráfico
xdg-open ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39/wfc.html

# 4. Si sale `indeciso`, sube los puntos y repite
sed -i 's/^  sample: 2000/  sample: 5000/' pipeline/config.yaml
rm -rf ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39
python3 -m pipeline.run --project XAUUSD --databank SPP_IS --strategy "Strategy 17.9.39"

# 5. Cuando ya tengas la respuesta, tira las variantes y quédate el registro
python3 -m pipeline.cleanup --project XAUUSD --strategy "Strategy 17.9.39" --apply
```

**Coste medido el 2026-09-25**, tres madres de USDJPY H1 × 5.000 variantes × 3 tramos × 10 mercados
(USDJPY y los nueve de su familia) en el custodio, en el proyecto propio `USDJPY_variantes`:

| fase | por madre | memoria | disco |
|---|---|---|---|
| `make` (fabricar 5.000 `.sqx`) | 3 s | — | 67 MB en local |
| `execute` (cargar, retestear, exportar, volcar) | **63–71 min** | JVM **84–87 GB**: toca su techo de 80 GB y el recolector aguanta | **7,5–14,7 GB** en el custodio |
| `equity` | 83–88 s | 3,7–4,4 GB | — |
| `collect` | 17 s | 2,1 GB | — |
| `execute --clear` (vaciar los cuatro databanks) | **3–4 s** | — | el custodio a 0 |
| WFC (paso 17) | 0,7 s | 0,3 GB | — |
| CSCV (paso 18) | **90–170 s** | 1,6 GB | — |
| **se guarda por madre** | | | **~520–870 MB** de parquet (el 80 % son las curvas de los 9 mercados) |

**50 madres**: ~55–60 h de custodio, ~3 h de Python (casi todo CSCV) y ~25–45 GB de parquet. El
custodio **tiene** que vaciarse entre una madre y la siguiente: sin eso serían 50 × ~10 GB en su
disco. `execute --clear` lo hace con SQX parado, **después** de `equity` y `collect`, que leen esos
ficheros.

### Qué NO te dice

- **No te dice qué parámetros poner.** Dice si elegirlos sirve de algo.
- **No es un walk forward de verdad.** Hay **una** partición IS/OOS, no una ventana que rueda. Mide
  si la superficie de parámetros se mantiene entre dos trozos de historia, no si se mantiene a lo
  largo del tiempo. Para eso está `strategies/walkForwardMatrix`.
- **No te dice nada sobre el futuro.** El OOS de este estudio es historia que la estrategia no vio
  al optimizarse, pero que tú sí has visto ya muchas veces. La única ventana que no está contaminada
  es la del holdout pre-registrado (`docs/preregistro/`), y hasta que esté firmada ningún módulo la
  lee.
- **Un `rho` alto no es una estrategia buena.** Puede correlacionar perfectamente y perder dinero en
  las dos muestras. Mira la nube: si está entera en el cuadrante de abajo a la izquierda, correlaciona
  las pérdidas.
- **Los costes son provisionales.** Hasta que los sustituyas, todos estos beneficios son
  aproximados. El orden entre combinaciones aguanta mejor que las cifras.

### Si algo falla

| síntoma | qué pasa | qué haces |
|---|---|---|
| `los controles devuelven el MISMO resultado` | el retest no llegó a ejecutarse y las variantes traen las métricas del padre | mira el log del custodio: `tail ~/Desktop/SQX_w2/user/log/StrategyQuant/log_*.log` |
| la etapa `ran` no avanza nunca | SQX arrancó el proyecto y no testea nada | el arnés `Retester` de W2 necesita `retestSelected="false"`; y hay que lanzarlo con `action=start`, **nunca** con `action=startOnlyTask`, que miente |
| `AlgoData N GB de 90 GB` | el presupuesto de disco frenó la corrida | libera espacio o sube el presupuesto en `perf/config.yaml` |
| `Symbol '...' doesn't exist` | una tarea nombra un símbolo que el install no tiene | pasa aunque el cross-check esté apagado: todos los `<Chart>` de la tarea se resuelven igual |
| `no manual page` en `checks.py` | hay un comando nuevo sin documentar | es esta misma regla: copia `_PLANTILLA.md` |
