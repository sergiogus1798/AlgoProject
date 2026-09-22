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
python3 -m strategies.walkForwardCorrelation.report --work <dir>
```

### Qué produce

Todo en `AlgoData/pipeline/<proyecto>/<estrategia>/`:

| fichero | qué es |
|---|---|
| `plan.csv` | el diseño completo: qué combinaciones y de qué estrato |
| `sqx/P*.sqx` | las estrategias fabricadas. **Es lo único pesado**, y lo que se borra al final |
| `manifest.parquet` | contrato C2: qué es cada fichero, leído **del disco**, no de lo que se pretendía |
| `retest.csv` | el panel tal y como lo escupe SQX |
| `metrics.parquet` | contrato C3: el panel unido al manifiesto. Es la tabla del estudio |
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
   | PROGRESS 100 2000 reteseadas, panel en retest.csv
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

Coste medido: **70 ms por variante** en el retest y **14 KB por fichero**. 2.000 combinaciones son
2 min 16 s de punta a punta y 28 MB; 5.000 son unos seis minutos y 70 MB.

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
