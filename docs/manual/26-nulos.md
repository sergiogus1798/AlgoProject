# 26. Nulos — ¿esto lo habría conseguido un mono entrando al azar?

### Qué pregunta responde

Coge las operaciones reales de una estrategia y fabrica miles de versiones imaginarias de ella
sobre **las mismas velas**: el mismo número de operaciones, la misma duración, el mismo dinero
en riesgo y el mismo coste de bróker — cambiando solo **cuándo entra**. Luego te dice en qué
percentil de esas miles quedó la real.

Si el resultado de tu estrategia lo consigue una de cada tres tiradas al azar, no hace falta
discutir más. Si no lo consigue ninguna de 2.500, has medido algo.

Y hace una segunda cosa más interesante: como puedes elegir **qué le dejas fijo al mono**, la
diferencia entre dos configuraciones te dice de dónde sale el edge — del momento de entrar, de
cuánto aguanta la posición, o de cómo calcula el tamaño.

### Cuándo lo usas, y cuándo no

**Lo usas** después de exportar las operaciones de una databank, sobre el tramo `oos1`, para
decidir qué estrategias merecen que el pipeline gaste días de máquina en ellas.

**No lo usas** para decidir nada sobre el tramo `oos2`: está reservado a WFC y WFM, y cada
mirada lo gasta (`assets/_policy.yaml`).

**No sirve** para comparar dos mercados distintos, ni para decirte si funcionará el año que
viene. Lo que mide es: *dada esta historia concreta, ¿hubo habilidad en el momento de entrar?*
Si lo que quieres saber es qué pasaría en **otra** historia, eso es el MC Retest (página 11).

### Antes de empezar

1. Tienen que existir las operaciones exportadas en `raw/<proyecto>/<databank>/<fecha>/trades.parquet`
   (página 06 para exportarlas).
2. Tienen que existir las velas del feed en `bars/` (página 13).
3. **No hace falta cerrar SQX.** Este módulo no toca la instalación: lee ficheros ya exportados.

### Cómo se ejecuta

**Una sola estrategia**, que es el uso normal:

```bash
python3 -m nulls.one --project XAUUSD --databank MC_Trades \
    --feed XAUUSD_DukasM1_Infinox --strategy "Strategy 1.10.80"
```

**Primero la verificación, siempre.** Sobre una estrategia cualquiera:

```bash
python3 -m nulls.verify --project XAUUSD --databank MC_Trades \
    --feed XAUUSD_DukasM1_Infinox --strategy "Strategy 1.10.80"
```

Y luego la corrida completa:

```bash
python3 -m nulls.report --project XAUUSD --databank MC_Trades \
    --feed XAUUSD_DukasM1_Infinox --timeframe M30 --sample OOS1
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--project` | sí | nombre del proyecto tal y como aparece en SQX |
| `--databank` | sí | databank cuyo export de operaciones se lee; coge el más reciente |
| `--feed` | sí | nombre del feed en SQX, p.ej. `XAUUSD_DukasM1_Infinox`. Sin él no sabe qué velas usar |
| `--timeframe` | no | `M30` por defecto. Tiene que ser el de la estrategia o las duraciones no cuadran |
| `--sample` | no | `OOS1` por defecto. `IST` es dentro de muestra — úsalo para atribuir, nunca para decidir |
| `--limit` | no | solo las N primeras estrategias, para una prueba rápida |
| `--set` | no | cambia un ajuste sin editar el fichero: `--set nulls.draws=500` |
| `--workers` | no | estrategias a la vez, una por proceso. Por defecto todos los núcleos |

**Cuánto tarda:** 757 estrategias × 4 peldaños × 2.500 tiradas en **11 segundos** con 96 procesos
(medido el 2026-09-25; en un solo núcleo, 569 s). No toca SQX, así que puedes lanzarlo con la GUI
abierta.

**Los monos son reproducibles.** Cada estrategia sortea de su propia semilla, que sale de
`nulls.seed`, de su nombre, del peldaño y del bloque. Repetir la corrida da exactamente los mismos
p, uses 1 proceso o 96, y aunque cambien las demás estrategias del lote. Subir `nulls.draws` añade
monos y no cambia los primeros. Lo que sí los cambia es `nulls.chunk_trades`: no lo toques.
No toca SQX, así que puedes lanzarlo con la GUI abierta.

**Lo que imprime `nulls.one`**, salida real:

```
Strategy 1.10.80   399 operaciones   muestra OOS1   2,500 monos por peldano
reconciliacion 0.999985  (relleno open-open, segunda convencion 0.9629)

           tu estrategia    mono medio     mono p95  percentil        p
-----------------------------------------------------------------------
     net       21,387.13     -5,567.68    19,567.73      96.2%   0.0380  <--
  sharpe            0.09         -0.02         0.07      98.6%   0.0148  <--
      pf            1.31          0.95         1.25      97.3%   0.0276  <--
   retdd            3.18          0.02         1.97      98.2%   0.0184  <--
     dd         6,724.18     20,180.50    37,685.82       1.4%   0.0144  <--

de donde sale la ventaja, medida en 'net':
  ventaja total sobre el mono suelto ....      26,960.91
  de cuanto aguanta la posicion .........         156.05
  del tamano por volatilidad ............         103.83
  resto, que es el momento de entrar ....      26,701.03
```

Se lee así: **el mono medio pierde 5.568 $ y tu estrategia gana 21.387**; solo el 3,8 % de las
2.500 tiradas al azar igualó eso. En drawdown está en el percentil 1,4 — sufrió mucho menos que
el azar, que es lo contrario de lo que pasa con el beneficio y por eso su columna se lee al revés.

Y la atribución dice de dónde sale: de los 26.961 $ de ventaja, **26.701 son el momento de
entrar**. La duración aporta 156 y el tamaño 104. En esta estrategia el edge es timing y poco más.

⚠️ El «resto» no se mide aparte: es lo que queda tras quitar los canales que **sí** se pueden
sortear. Si un día se añade un peldaño nuevo, ese resto se encoge.

Debajo va el histograma de las 2.500 tiradas con tu estrategia marcada, que es el dibujo del que
va todo esto, y luego los avisos de `distrust`.

### Qué produce

```
reports/<proyecto>/<databank>/<fecha>/nulls/
├── nulls.csv       una fila por estrategia
├── rungs.json      qué aleatoriza cada peldaño, para que el CSV se entienda solo
└── manifest.json   qué lo produjo, con qué export y cuántas tiradas
```

Los informes **se acumulan**: una corrida nueva de otro día no borra la de hoy.

### Cómo se lee el resultado

**La verificación primero.** Salida real:

```
Strategy 1.10.80  (399 trades, muestra OOS1)

RECONCILIACION  fill=open-open  corr=0.999985  gap mediano=6.39 $  (segunda mejor convencion: 0.9629)
BARRERAS        399 trades, 339 tocan una barrera sintetica, discrepancias vectorizado vs bucle: 0
UNIFORMIDAD     400 runs nulos juzgados contra el resto: KS=0.0633 p=0.078 media=0.487 (debe ser ~0.5)
```

Las tres tienen que pasar:

- **RECONCILIACION** por encima de 0.99. Es la que lo sostiene todo: si el P/L que reconstruimos
  desde las velas no es el que SQX reportó, tampoco lo será el de las tiradas imaginarias. Aquí
  0.999985. La "segunda mejor convención" en 0.9629 dice que el relleno está identificado sin
  ambigüedad: SQX rellena **a la apertura de la vela**, en la entrada y en la salida.
- **BARRERAS** tiene que dar **0 discrepancias**. Tus estrategias de hoy no llevan stop ni
  objetivo, así que el código que los calcula no lo ejercita ninguna operación real: se le ponen
  barreras inventadas a propósito y se compara el cálculo rápido contra un bucle lento.
- **UNIFORMIDAD** con media ~0.5. Se coge una tirada al azar, se hace pasar por la estrategia real
  y se mide su percentil contra las demás. Si el mecanismo es correcto, esos percentiles salen
  repartidos de 0 a 1. Si salieran torcidos, habría un fallo en el sorteo — y se ve **antes** de
  mirar ninguna estrategia de verdad.

**Y luego el CSV.** Las columnas:

| columna | qué es |
|---|---|
| `n` | operaciones en la muestra |
| `reconcile` | la correlación de arriba, por estrategia |
| `real_net`, `real_sharpe`, … | lo que hizo la estrategia de verdad |
| `p_timing_net`, `p_timing_sharpe`, … | **el percentil**: qué parte de las 2.500 tiradas la igualó o la superó |
| `p_free_net`, … | lo mismo con el mono más suelto |
| `edge_total` | cuánto le sacó al mono, en dólares |
| `edge_sizing`, `edge_holding_time` | cuánto de eso venía del tamaño y de la duración |
| `distrust` | por qué no fiarte, en cristiano |

**Un `p` por debajo de 0.05 quiere decir que menos de 1 de cada 20 tiradas al azar lo igualó.**

### Un ejemplo completo

Corrida real sobre las 757 estrategias, peldaño `timing` (solo se aleatoriza *cuándo* entra):

```
estrategias: 757   reconcile mediana: 0.999983   minimo: 0.99945

pasan a p<0.05, por estadistico:
  dd       640 de 757 =  84.5%    p mediano 0.013
  sharpe   586 de 757 =  77.4%    p mediano 0.027
  retdd    582 de 757 =  76.9%    p mediano 0.028
  pf       418 de 757 =  55.2%    p mediano 0.046
  net      299 de 757 =  39.5%    p mediano 0.059

la media del mono es NEGATIVA en el 100% de las estrategias (mediana -4.698 $)
```

**Esto es lo más importante de toda la página**, y hay que leerlo despacio:

Es la **misma** simulación. Lo único que cambia es qué número se compara. Y pasa del 84.5 % al
39.5 %. **La elección del estadístico decide el veredicto mucho más que la elección del mono.**

Por qué: el Sharpe divide el beneficio entre la volatilidad, así que borra justo lo que separa
a tus operaciones de las aleatorias — las tuyas son un **36 % menos volátiles** (491 $ contra
661 $ de desviación por operación). Ser más tranquilo que el azar **es** un edge, y el Sharpe te
lo paga mientras que el beneficio neto no.

Por eso el informe imprime los cinco y **no elige ninguno**. Elegir es tuyo.

Y la segunda lectura: la media del mono es negativa en las 757. Un mono que entra al azar en el
oro **pierde dinero**, porque con posiciones de 6 horas captura ~2.867 $ de la subida del oro y
paga ~7.756 $ de coste. Batir a ese mono es, por tanto, un listón **más bajo** que ganar dinero.

### El tercer comando: ¿y la población entera?

```bash
python3 -m tasks.reports.nulls --project XAUUSD --databank MC_Trades
```

Los dos comandos de arriba miran estrategias. Éste mira **el lote**, y contesta otra pregunta:
*elegir también puede salir con suerte.* Si coges 757 estrategias sin ningún edge y te quedas con
las que sacan `p<0.05`, te llevas 38 igualmente — porque `p<0.05` significa "esto le pasa a 1 de
cada 20 por azar", y 757/20 = 38.

Salida real:

```
| estadistico | pasan | si NINGUNA tuviera edge | exceso | de las pasadas, suerte | nombrables |
|---|---|---|---|---|---|
| `net`    | 299 | 38 | **+261** | 13% |   0 |
| `sharpe` | 586 | 38 | **+548** |  6% | 152 |
| `pf`     | 418 | 38 | **+380** |  9% |   0 |
| `retdd`  | 582 | 38 | **+544** |  7% | 243 |
| `dd`     | 640 | 38 | **+602** |  6% | 614 |
```

Dos lecturas, y son independientes:

- **exceso** — cuántas hay de verdad. 299 pasan y el azar daría 38: sobran 261. **Hay señal.**
  Éste es el número que juzga a tu generador, y es comparable entre tiradas: si cambias el
  template y el exceso baja, lo has empeorado.
- **nombrables** — a cuántas puedes señalar con el dedo. En `net`, **ninguna**. No es que no haya
  señal, es que ninguna destaca lo bastante entre 757 candidatas.

Esa discrepancia no es un fallo: *"aquí dentro hay unas 261 buenas y no te puedo decir cuáles"* es
una conclusión legítima y frecuente.

⚠️ **El aviso de muestra preseleccionada.** Si más del 95 % de las estrategias gana dinero en la
muestra que se está juzgando, el informe lo canta arriba del todo: esa databank fue filtrada **por**
esa muestra, y entonces el exceso mide el filtro y no el generador. En `MC Trades` salta, porque
desciende de una tarea con condiciones de aceptación sobre OOS. Para juzgar al generador hace falta
una databank sin esas condiciones.

### Qué NO te dice

- **No te dice que la estrategia vaya a funcionar.** Dice que su momento de entrar, en esta
  historia concreta, fue mejor que entrar al azar en esa misma historia.
- **No te dice que el edge sea significativo.** Batir al mono es más fácil que batir a cero,
  porque el mono pierde por costes. Para "¿puede su media ser cero?" está MinTRL en
  `core/significance.py` — y son tests **distintos**: con el beneficio neto, 48 estrategias pasan
  MinTRL y fallan el mono, y 145 al revés.
- **No corrige por haber buscado.** Estas estrategias salieron de generar miles y quedarse con
  las buenas. Si vas a quedarte con las mejores de una lista de 200, el `p` de cada una hay que
  corregirlo (Benjamini-Hochberg), y el `p` más pequeño que se puede leer con 2.500 tiradas es
  `1/2501 = 4.0e-4`. Si te salen `p` topados ahí, el `distrust` te lo dice y hay que subir
  `nulls.draws`.
- **No vale para el tramo `oos2`.**
- **Los costes de XAUUSD son provisionales** (los que trae SQX de fábrica, no pactados con
  Infinox). Como la posición del mono la fija sobre todo el coste, estos `p` se mueven con ellos.
  El `distrust` lo repite en cada fila a propósito.

### Si algo falla

- **`un trade dura N barras y barrier.max_hold es 400`** — hay una operación más larga que el
  techo del escaneo. Sube `barrier.max_hold`; el módulo se niega en vez de recortar la operación,
  porque recortarla sería valorar otra operación distinta de la que SQX corrió.
- **`RECONCILIACION` por debajo de 0.99 en el `distrust`** — el `--timeframe` no es el de la
  estrategia, o el `--feed` no es el mercado en el que corrió. Es el error más común.
- **CSV vacío** — ninguna estrategia llega a `verdict.min_trades` (30) en esa muestra. Revisa
  que `--sample` sea el correcto: en este corpus es `OOS1`, no `OOS`.
