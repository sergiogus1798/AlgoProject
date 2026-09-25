## 39. La nube de parámetros — ¿el punto elegido es un pico de suerte?

### Qué pregunta responde

Cuando la fábrica de variantes (`18-variantes.md`) escribe miles de versiones de una estrategia y el
custodio las retestea, lo que queda en disco no es una lista de candidatas: es **la superficie** de
lo que esa lógica rinde según cómo la ajustes. Este comando la lee y responde cuatro cosas sobre
ella, todas sobre la estrategia original y ninguna sobre las copias:

1. **¿Dónde está la original entre sus vecinas?** Si le gana a casi todas y además casi ninguna se
   le acerca, está encaramada en un pico — y un pico no se puede operar, porque el mercado real no
   te deja aterrizar en el punto exacto. Si tiene compañía, es una meseta.
2. **¿Quién mueve el resultado?** Qué parámetros deciden y cuáles son decorativos.
3. **¿Hay superficie que leer, o es ruido?** Si dos ajustes casi idénticos rinden muy distinto, el
   número de cualquiera de ellos es el sorteo, no el ajuste.
4. **¿Esa forma se sostiene año a año?** Que la familia gane mirando los quince años de golpe no
   dice nada sobre si gana todos los años, ni sobre si el orden entre variantes se mantiene.

Y añade una comparación: **la meseta entera repartida contra el punto único**. Si la original le
saca mucho a la mezcla de sus vecinas, esa distancia es sobreajuste medido.

### Cuándo lo usas, y cuándo no

**Lo usas** después del paso 16.5, cuando ya existen `metrics.parquet` y `equity.parquet` de un lote
de variantes. Es gratis: no toca SQX, no consume CPU del worker, tarda segundos.

**No lo usas para elegir**. Es la regla dura del módulo y no es negociable: fabricar dos mil clones
**es** una búsqueda, más grande que la del builder. Quedarse con el clon que mejor puntúa produce
una estrategia *más* sobreajustada, no más robusta. El comando no devuelve nunca una variante mejor,
y si algún día quieres mover los parámetros al centro de la meseta, eso lo decides tú, se anota, y
se revalida sobre datos que este estudio no ha mirado.

**No sustituye al WFC ni al CSCV** (`19-wfc.md`, `25-cscv.md`). Aquéllos preguntan si optimizar
sirve de algo; éste pregunta qué forma tiene lo que optimizaste.

### Antes de empezar

Tiene que existir el directorio del lote, con estos dos ficheros dentro:

- `metrics.parquet` — lo escribe `python3 -m sqx.variants.collect --work <dir>`
- `equity.parquet` — lo escribe `python3 -m sqx.variants.equity --work <dir>`

SQX puede estar abierto o cerrado: da igual, no se le habla.

### Cómo se ejecuta

```bash
python3 -m studies.optimisation.cloud.report \
    --work ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--work` | sí | el directorio del lote, el mismo que usan `collect` y `equity` |
| `--out` | no | escribe todos los números en un JSON, para el ledger o para comparar dos lotes |
| `--set` | no | cambia un ajuste sin editar el YAML: `--set stability.period=2QE` |

Tarda **1,9 segundos** con 998 variantes y 3.925 días, y ocupa **410 MB** de RAM (medido 2026-09-24). No toca SQX.

### Qué produce

Por pantalla, cuatro bloques. Con `--out`, además un JSON con las lecturas, los índices de
sensibilidad, la tabla por periodo y las medianas. No sobrescribe nada del lote.

### Cómo se lee el resultado

**La cabecera** dice sobre cuántas variantes se lee y qué se ha dejado fuera. Los **canarios** salen
siempre (son controles colocados a propósito en los extremos), y también las variantes que operan
menos de 30 veces, que no son puntos de una superficie sino accidentes.

La línea de **colapsados** es la que más información da por carácter:

```
! colapsados por los filtros, fuera del modelo: DICrossShift1
```

Significa que, una vez fuera las variantes que apenas operan, ese parámetro **sólo tiene un valor
vivo**. No es un fallo: dice que ese parámetro no elige entre bueno y malo, elige entre operar y no
operar. Ningún índice de sensibilidad te habría contado eso.

**A1 — dónde está el punto elegido.**

| número | qué es | qué es bueno |
|---|---|---|
| `q (rango)` | fracción de la nube a la que la original le gana | por sí solo no dice nada |
| `pi (20%)` | fracción que se queda a menos de un 20 % de ella | cuanto más alto, más meseta |
| `M_shrunk` | la mediana del entorno | **éste** es el número a usar hacia adelante, no el de la original |

`q` alto **con** `pi` bajo es el pico de ruido. `q` alto con `pi` alto es una meseta, que es lo que
quieres. Y `M_shrunk` es lo que de verdad cabe esperar en vivo: la original fue seleccionada, sus
vecinas no.

**A2 y A3 — quién manda y si hay superficie.** `S` es cuánto explica cada parámetro por su cuenta y
`S_total` incluye sus interacciones. `S_total` casi cero = parámetro decorativo, se puede congelar.
`S_total` muy por encima de `S` = ese parámetro sólo funciona en combinación con otro, que es la
firma de una lógica ajustada a mano.

Debajo, tres medidas de forma. `r2` es cuánto de la superficie es una función suave de los
parámetros; la **rugosidad residual** es lo que sobra; el **desacuerdo entre vecinos** mide lo mismo
sin suponer ninguna fórmula, y sólo se habla de superficie rugosa cuando las dos coinciden. La
`pendiente` en el origen dice si la estrategia está donde el modelo suave pondría su óptimo.

**B2 — periodo a periodo.** `f_y` es qué fracción de la nube ganó dinero ese año; `q_origen` es
dónde quedó la original ese año; `rho_siguiente` es cuánto del orden entre variantes sobrevive al
año siguiente, y `deriva` cuánto se desplaza la región buena.

`rho` cerca de cero **es el hallazgo importante**: significa que la superficie se rebaraja cada año,
y entonces optimizar los parámetros mirando el histórico es optimizar ruido, por muy bien que se vea
el conjunto.

⚠️ `días_activos` son días con movimiento, **no operaciones**. Un recuento de operaciones por año
exige exportar los trades, que son noventa minutos contra el segundo y medio que cuesta este
fichero. Los periodos por debajo de `min_active_days` no se leen.

**C1 — la meseta contra el punto único.** Se eligen K miembros **repartidos** por la meseta (no los
K mejores: eso volvería a ser elegir), cada uno con 1/K del riesgo, y se compara. Una diferencia de
Sharpe pequeña a favor del punto único es buena señal.

### Un ejemplo completo

Sobre el lote de `Strategy 17.9.39`, que son 2.000 variantes fabricadas y 962 retesteadas:

```
998 variantes sobre Ret/DD Ratio (IS), 1002 descartadas (canarios y pocas operaciones); origen P00000
! colapsados por los filtros, fuera del modelo: DICrossShift1

-- A1 · dónde está el punto elegido
original 2.680
           n  q (rango)  pi (20%)  M_shrunk
near   253.0      0.889     0.269     1.530
cloud  998.0      0.957     0.099     0.075
-> middling: el punto elegido no destaca en su propia nube

-- A2 y A3 · quién mueve el resultado, y si hay superficie que leer
         parámetro     S  S_total
    DICrossPeriod1 0.870    0.888
    ExitAfterBars1 0.073    0.098
    MomentumShift1 0.006    0.020
CBlock_SqzMmnInt21 0.002    0.013
          IsShift1 0.000    0.011
           IsBars1 0.002    0.009
   MomentumPeriod1 0.002    0.004
suavidad r2 0.902 · rugosidad residual 0.098 · desacuerdo entre vecinos 0.151 IQR
curvatura en el origen: pendiente 6.02, autovalores [-5.7 -2.1 -0.5  1.2  2.   3.7 21.9]
-> smooth: la superficie es una función suave de los parámetros
-> off_centre: el óptimo del modelo suave no está donde se sitúa la estrategia

-- B2 · la superficie, periodo a periodo
              f_y  q_origen  días_activos  rho_siguiente  deriva
2008-12-31  0.514     0.797         138.0         -0.048   0.215
2009-12-31  0.000     0.983         138.0          0.216   0.092
2010-12-31  0.746     0.962         148.0          0.245   0.124
2011-12-31  0.719     0.975         147.0          0.225   0.144
2012-12-31  0.537     0.625         142.0          0.542   0.085
2013-12-31  0.421     0.901         130.0          0.098   0.343
2014-12-31  1.000     0.291         122.0         -0.363   0.354
2015-12-31  0.017     0.570         135.0          0.535   0.169
2016-12-31  0.738     0.918         134.0          0.120   0.094
2017-12-31  0.356     0.656         128.0         -0.340   0.347
2018-12-31  0.480     0.436         151.0          0.577   0.060
2019-12-31  0.725     0.690         145.0         -0.528   0.350
2020-12-31  0.897     0.771         155.0         -0.357   0.249
2021-12-31  0.849     0.382         153.0         -0.016   0.264
2022-12-31  0.847     0.532         152.0            NaN     NaN
mediana rho +0.109 · mediana deriva 0.192 · peor periodo f_y 0.000
-> carried: hay periodos que sostienen el resultado y otros en los que la familia entera pierde
-> reshuffled: la superficie se rebaraja cada periodo: optimizarla es optimizar ruido
-> drift_low: la región buena se queda donde estaba de un periodo al siguiente

-- C1 · la meseta entera contra el punto elegido
meseta 68 variantes, 6 con curva, a 1/6 del riesgo
                   net  sharpe   drawdown
punto único  35328.266   0.314 -11310.234
mezcla       31274.974   0.284  -9455.880
diferencia de Sharpe +0.030
```

**Cómo se lee esto de verdad**, que es lo que importa:

- La original **no está en un pico**: le gana al 89 % de su vecindad y un 27 % de ella se queda a
  menos de un 20 %. Pero su Ret/DD de 2.68 no es la expectativa: la mediana del entorno es **1.53**,
  y ése es el número con el que hay que contar.
- **Un solo parámetro manda**: `DICrossPeriod1` explica el 87 % de la varianza. Los otros seis, casi
  nada. Eso son cinco grados de libertad que la estrategia no está usando para nada.
- La superficie **es suave** (r² 0.90), así que la forma se puede leer. Pero la pendiente en el
  origen no es cero: el óptimo del modelo está en otro sitio.
- Y aquí está el hallazgo: **rho mediano +0.11**. El orden entre variantes casi no sobrevive de un
  año al siguiente, y en cuatro años es negativo. En 2009 **ninguna** variante de las 998 ganó
  dinero; en 2014, todas. Esta familia no tiene una configuración buena y otra mala de forma
  estable: tiene años buenos y años malos que se llevan a todo el mundo por delante.
- La mezcla de la meseta rinde casi igual que el punto único (0.284 contra 0.314) **con menos
  drawdown**. Poco sobreajuste en ese eje.

### Qué NO te dice

- **Nada sobre otros mercados.** Las superficies por mercado (A4) y si la región buena coincide
  entre mercados (B3) necesitan un retest de variantes que lleve los cross-checks de
  `assets/_markets.yaml`. Encargo `15-superficies-multimercado.md`.
- **Nada sobre las reglas**, sólo sobre los valores. Quitar una condición o invertir la señal exige
  editar la lógica del `.sqx`: encargo `12-tests-estructurales.md`.
- **No mira el tramo reservado.** `oos2` es la puerta de un solo sentido del `WORKFLOW.md`, así que
  las curvas se cortan donde empieza, y la cabecera dice cuántos días se ha dejado fuera.
- **Los índices de sensibilidad se calculan sobre el modelo suave**, no sobre los backtests. Heredan
  su r²: con un r² bajo describen una forma que los datos sólo sostienen a medias. Por eso el r² se
  imprime al lado.
- **No es una puerta.** Ninguna de sus lecturas descarta ni aprueba nada.

### Si algo falla

- `KeyError: 'equity.parquet'` o fichero no encontrado — falta la cosecha: corre
  `python3 -m sqx.variants.equity --work <dir>` antes.
- **Muchísimas variantes descartadas** (aquí, la mitad) es normal y está en la cabecera: un lote se
  fabrica más grande de lo que vuelve del custodio, y encima la mitad de las combinaciones apenas
  operan.
- Si aparecen **dos o tres parámetros colapsados** en vez de uno, no bajes `min_trades` para
  taparlo: lo que te está diciendo es que tu rejilla de variantes está llena de combinaciones que no
  operan, y eso se arregla en el diseño, no aquí.
