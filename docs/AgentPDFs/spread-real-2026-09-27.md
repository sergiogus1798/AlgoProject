# El spread real de Darwinex — estudio

**27 de septiembre de 2026 · XAUUSD, USDJPY y los cinco índices CFD (DAX40, DJ30, NIKKEI225, USA500, USATEC)**

Código: `studies/data/spread/` · Datos: `AlgoData/spread/<feed de ticks>/` · Manual: capítulo 59,
`docs/manual/03-datos-costes-y-registro.pdf` · Pendientes: `OPEN.md` #76.

---

## 1. Resumen

- **El spread real es mucho mayor que el declarado.** En los ticks de Darwinex, el spread medio
  del oro es de 9 a 63 puntos (2017 → 2026), frente a los 5 y 10 que se declaraban. El de USDJPY
  es de 4,7 a 10,4 puntos frente a 0,1. Los índices no tenían spread declarado.
- **No es constante, ni en puntos ni en % del precio.** Ni siquiera en forex. Con tu criterio
  (cada año a ±20 % de la mediana), falla en los siete activos.
- **En los índices el precio casi no explica el spread.** Va por regímenes: 2020 y 2026 se salen
  de la banda. En el oro sí sigue al precio (exponente 1,18). En USDJPY sube con él, pero ahí el
  precio hace de reloj.
- **Si pagaran el spread real, un 3–7 % de las estrategias que ganaban OOS dejarían de ganar**, y
  las que siguen ganando pierden una mediana del 16–34 % de su neto. El estudio lo calcula
  operación por operación en 2–3 s, en vez de un retest DATATICK.
- **La comisión en % de SQX se cobra una sola vez por operación**, sobre el precio de apertura.
  Verificado operación a operación; el «dos veces» anterior era swap colado en la regresión.
- **Aplicado hoy a los índices**: tramos build (inicio de datos–2019), oos1 (2020–2023) y oos2
  (2024–31/08/2026). Oos1 y oos2 llevan su spread medido × 1,25; el build, el **proporcional al
  precio** (tu opción A) × 1,25. El slippage es la mitad del spread de su tramo, y el rango del MC
  Retest de spread es la dispersión real alrededor de esa media proporcional.

## 2. Objetivos

1. Medir el spread que cobra de verdad el mercado, con los ticks de Darwinex (ask y bid), en
   lugar de suponerlo. Las velas de Dukascopy solo traen el bid.
2. Decidir si el spread se mantiene constante respecto al precio. Si lo hace, basta un % fijo con
   un margen; si no, hay que modelarlo para los años sin ticks.
3. Proponer el coste que declarar en SQX en cada tramo (build, oos1, oos2), con tu factor 1,25.
4. Reajustar las operaciones de una cosecha con el spread real, y ver qué estrategias se
   rompen, sin pagar un retest DATATICK.
5. Modelar el spread medio diario en función del precio, con sus límites del 2,5 % y el
   97,5 %, como base del rango del MC Retest.

## 3. Metodología

### 3.1 Los ticks

- **Formato.** Los `*_TICK.dat` de SQX son un formato binario propio. Las clases de SQX no se
  pueden llamar desde fuera (dependen de código cifrado), así que el formato se leyó del bytecode
  de `SQDataLib.jar`. Es una cabecera y, luego, registros con tiempo, ask, bid y volumen, cada uno
  como diferencia o valor absoluto de 1, 2, 4 u 8 bytes, con una marca cada 1.000 ticks.
- **Lector.** Se reimplementó en `core/tickfile.py`. No guarda los ticks: los pliega minuto a
  minuto sobre la marcha. Tarda 13 s los 368 millones de ticks de USDJPY y 25 s los 647 millones
  del oro.
- **Validación.** El bid de Darwinex contra el cierre de Dukascopy, minuto a minuto: los retornos
  de un minuto correlan 0,99 (oro) y 0,985 (USDJPY), y la diferencia de nivel mediana es 0,09 y
  0,001. El reloj es el mismo, el ingenuo del feed. Un test con un fichero escrito a mano cubre el
  formato (`tests/test_spread.py`).

### 3.2 Qué spread cuenta

- **El del primer tick de cada minuto.** Es lo que paga una orden a mercado en la apertura de la
  vela con precisión DATATICK, y todo lo que construyes entra a mercado.
- **Cuándo lo paga cada operación.** SQX precia sobre el bid y suma el spread del lado del ask.
  Una larga paga el spread que haya al entrar y una corta el que haya al salir.
- **La media, no la mediana.** Un coste acumula su media, y la cola (rollover, noticias) es
  dinero real.
- **El minuto importa.** El primer tick de cada hora en punto cuesta un 13 % más que un minuto
  cualquiera, y a las 00:00 el oro cuesta 2,1 veces la media del día.

### 3.3 Constancia y modelo (XAUUSD, USDJPY)

- **Constancia.** Media anual del spread en % del precio, comparada con la mediana de los años
  completos; es constante si todos los años caen dentro de ±20 % (tu criterio, en el ledger).
- **Si no lo es, se modela.** Hay cuatro modelos del spread relativo diario: constante en %,
  constante en puntos, por volatilidad de Dukascopy, y por volatilidad y precio. La volatilidad
  existe en todos los años, también en los que no hay ticks.
- **Cómo se elige.** Cada modelo se ajusta a un lado de 2022 y se juzga año a año en el otro, en
  los dos sentidos. «Hacia atrás» es la dirección que necesitan los años sin ticks.

### 3.4 La banda del spread (todos)

- **Qué se modela.** Cada día es un punto: su precio mediano y su spread medio en puntos.
- **La curva.** `spread = a · precio^b` (una recta en log-log), ajustada a la media por mínimos
  cuadrados y a los cuantiles 2,5 %, 50 % y 97,5 % por regresión cuantílica. Los cuantiles se
  reordenan para que nunca se crucen.
- **Por qué el spread diario y no el de cada minuto.** El MC Retest de SQX sortea **un** spread
  por simulación, uniforme entre Min y Max en pasos de 0,1 puntos, y lo aplica a todo el backtest
  (`RandomizeSpread.java`).
- **Calibración.** Qué parte de los días de cada año queda fuera de la banda; lo esperado es un
  2,5 % por cada lado.

### 3.5 Reajuste de operaciones

- **Qué hace.** A cada operación de una cosecha se le devuelve el spread plano que cargó su tarea
  (leído del `project.cfx`, también de un proyecto ya retirado) y se le cobra el real: el tick de
  Darwinex a menos de 5 minutos o, si no hay, el del modelo para ese día y esa hora.
- **Qué no cambia.** Solo el spread: con órdenes a mercado no cambia ninguna entrada ni salida, y
  el slippage, la comisión y el swap siguen siendo los de SQX.
- **Qué se guarda.** Tres versiones de cada operación, lado a lado, en `trades.parquet`: la de
  SQX, con el spread real, y con el spread y el slippage reales. SQX cobra su slippage en la
  entrada **y** en la salida (medido en el oro: +0,025 y −0,025 con 2,5 puntos). El slippage
  variable es la mitad del spread real en cada relleno, tu convención.

### 3.7 El build de los índices y el rango del MC Retest

- **Precio y volatilidad de antes de 2018.** Las velas M1 de Dukascopy de los índices no estaban
  en la librería; se leen directamente del `*_M1.dat` de SQX. Es el mismo formato que los ticks, y
  el resultado es idéntico a la exportación de SQX en 8,7 millones de velas de USDJPY.
- **Los cuatro modelos**, ajustados en los años de Darwinex y validados en los dos sentidos, como
  en 3.3.
- **Tu decisión (opción A):** el build lleva el spread **proporcional al precio**, es decir, el
  spread medio en % del precio de los días de Darwinex por el precio de cada día del build. Se
  mide donde hay ticks.
- **Rango del MC Retest en múltiplos.** Se calcula el cociente día medido ÷ media proporcional;
  sus cuantiles 2,5 % y 97,5 %, multiplicados por el spread del build, dan el Min y el Max. No se
  mezclan puntos de años distintos: SQX aplica un solo spread por simulación, y el precio de 2012
  no es el de 2023.

### 3.6 La comisión en %

Sobre la cosecha `XAU_ISOOS_ejemplo` (`PercentageBased 0,001`), operación a operación. En las 45.488
operaciones del mismo día que no cruzan las 23:00, el P/L de SQX cuadra al céntimo con **un** cargo
`(pct/100) × lotes × precio de apertura × valor del punto`, y con dos cargos no cuadra ninguna. Las
1.566 que sí cruzan las 23:00 llevan swap, de 18 a 75 $/lote; eso es lo que dio el falso k = 1,87 del
día anterior.

## 4. Resultados

### 4.1 XAUUSD y USDJPY por año (spread medio del primer tick de cada minuto)

| año | XAUUSD puntos | XAUUSD pb del precio | USDJPY puntos | USDJPY pb |
|---|---|---|---|---|
| 2017 | 9,1 | 0,71 | 4,7 | 0,42 |
| 2018 | 12,2 | 0,97 | 4,7 | 0,43 |
| 2019 | 9,5 | 0,69 | 4,5 | 0,41 |
| 2020 | 32,8 | 1,89 | 4,2 | 0,40 |
| 2021 | 17,6 | 0,98 | 4,0 | 0,36 |
| 2022 | 18,0 | 0,99 | 6,4 | 0,48 |
| 2023 | 17,6 | 0,91 | 8,5 | 0,61 |
| 2024 | 16,1 | 0,67 | 8,6 | 0,57 |
| 2025 | 33,6 | 0,95 | 9,8 | 0,66 |
| 2026 | 63,4 | 1,39 | 10,4 | 0,66 |

Constancia del relativo: el peor año del oro está a 1,96 veces la mediana y el de USDJPY a 1,44.
**No es constante en ninguno de los dos.**

### 4.2 Qué modelo reconstruye mejor los años sin ticks

Error medio |%| de la media anual en años no vistos:

| modelo | XAUUSD hacia atrás | XAUUSD hacia delante | USDJPY hacia atrás | USDJPY hacia delante |
|---|---|---|---|---|
| constante en % | 25 | 27 | 47 | 32 |
| constante en puntos | 119 | 26 | 97 | 49 |
| volatilidad | **19** | 32 | 40 | 29 |
| volatilidad + precio | 19 | 37 | **10** | 10 |

- **2020 en el oro** se queda corto un 46–49 % con cualquier modelo: fue un régimen, no
  volatilidad.
- **USDJPY** gana con el precio porque entre 2017 y 2026 subió a la vez que el tiempo. Aplicado a
  2011–2012 (76–80 yenes) daría los spreads más finos de toda la historia: no me fío de él ahí.

![El informe del oro](../../../AlgoData/manual-fuentes/assets/spread-oro-informe.png)

### 4.3 Propuesta para XAUUSD y USDJPY (× 1,25; no aplicada)

| | tramo | % días medidos | spread medio (pb) | comisión % | puntos equivalentes | declarado hoy |
|---|---|---|---|---|---|---|
| XAUUSD | build | 2 | 1,05 | 0,0131 | 16,4 | 5 |
| | oos1 | 100 | 1,10 | 0,0138 | 23,5 | 10 |
| | oos2 | 100 | 0,94 | 0,0118 | 31,1 | 10 |
| USDJPY | build | 2 | 0,39 | 0,0048 | 0,48 | 0,1 |
| | oos1 | 98 | 0,41 | 0,0052 | 0,57 | 0,1 |
| | oos2 | 98 | 0,62 | 0,0078 | 1,17 | 0,1 |

### 4.4 Los índices por año (spread medio diario en puntos)

| año | DAX40 | DJ30 | NIKKEI225 | USA500 | USATEC |
|---|---|---|---|---|---|
| 2018 | 90 | 236 | 659 | 52 | 71 |
| 2019 | 99 | 296 | 877 | 50 | 157 |
| 2020 | 147 | 204 | 882 | 30 | 80 |
| 2021 | 128 | 305 | 583 | 28 | 76 |
| 2022 | 147 | 367 | 684 | 32 | 72 |
| 2023 | 141 | 333 | 703 | 38 | 76 |
| 2024 | 142 | 214 | 371 | 33 | 76 |
| 2025 | 177 | 222 | 325 | 29 | 87 |
| 2026 | 270 | 338 | 621 | 60 | 105 |

Medianas anuales de los días. DJ30 y NIKKEI225 empiezan en octubre de 2017; el resto, en junio de 2018.

### 4.5 La banda del spread contra el precio

| activo | b de la media | media al último precio | 2,5 % | 97,5 % | peor año fuera de banda, por un lado |
|---|---|---|---|---|---|
| DAX40 | +0,56 | 213 | 164 | 366 | 13 % por debajo (2018) |
| DJ30 | −0,01 | 286 | 179 | 392 | 20 % por debajo (2021) |
| NIKKEI225 | −0,63 | 389 | 172 | 898 | 32 % por debajo (2017, año parcial) |
| USA500 | −0,10 | 38 | 29 | 60 | 16 % por debajo (2021) |
| USATEC | −0,14 | 86 | 82 | 138 | 9 % por encima (2026) |
| XAUUSD | +1,18 | 49 | 18 | 83 | 18 % por encima (2020) |
| USDJPY | +2,26 | 1,0 | 0,7 | 1,5 | 8 % por debajo (2022) |

`b` = 1 es un spread proporcional al precio y `b` = 0 uno fijo en puntos.

- **En los índices, salvo el DAX, `b` sale cero o negativo**: el precio no lleva al spread.
- **En el DAX** el límite de arriba baja con el precio, arrastrado por 2020 (precio bajo y spread
  alto).
- **Calibración:** todos los activos tienen algún año a 8–32 % de sus días fuera de la banda por un
  lado, cuando lo esperado es un 2,5 %. 2020 y 2026 se salen por arriba; los años tranquilos
  (2021 en DJ30 y USA500), por abajo. La banda recoge la dispersión de toda la historia, no la de
  un año concreto.

![La banda del DAX40](../../../AlgoData/manual-fuentes/assets/spread-banda-dax.png)

### 4.6 Reajuste de cosechas (solo spread)

| cosecha | estrategias | ganaban OOS | siguen ganando | cambio mediano del neto de las que ganaban |
|---|---|---|---|---|
| XAU_ISOOS_ejemplo | 115 | 66 | 63 | −16 % (IS −8 %) |
| USDJPY_emaCross_H1 (antes de su criba) | 100 | 40 | 37 | −34 % (IS −6 %) |
| Test_USDJPY_donchianUpperCrossUp_M30 | 200 | 191 | 186 | −19 % (IS −10 %) |

Con el spread **y** el slippage reales: en el oro dejan de ganar en OOS 7 de 115 (neto −31 % de
mediana en las que ganaban); en el donchian de USDJPY, 26 de 200 (−36 %).

Ejemplo: `Strategy 23.14.86` de USDJPY. En OOS gana 1.986 con el spread de SQX (0,1 puntos) y pierde
149 con el real (0,44 puntos de media, todas sus operaciones medidas con ticks).

![Una estrategia que se rompe en OOS](../../../AlgoData/manual-fuentes/assets/spread-una-estrategia.png)

### 4.7 El build de los índices: qué modelo, y qué da

Spread del build × 1,25 (puntos) según el modelo, y error del proporcional en años no vistos:

| | DAX40 | DJ30 | NIKKEI225 | USA500 | USATEC |
|---|---|---|---|---|---|
| A. Proporcional al precio (**elegido**) | 145,3 | 260,3 | 606,7 | 33,6 | 69,7 |
| B. El que mejor valida | 149 | 363 | 1.185 | 54 | 149 |
| C. Media medida en 2018–19 (lo que había) | 143,4 | 363,4 | 933,6 | 68,8 | 176,1 |
| Error del proporcional, hacia atrás / hacia delante | 21 / 26 % | 21 / 47 % | 46 / 153 % | 40 / 85 % | 50 / 169 % |

- **Entre 2018 y 2026 el spread de los índices en Darwinex no fue proporcional al precio.** En
  2018–2019 costaba mucho más en % del precio que desde 2020: USATEC pagaba 1,9 pb a 7.500 y hoy
  0,4 pb a 21.600.
- **Por eso los modelos que mejor validan** («fijo en puntos», «volatilidad + precio») llevan el
  build caro a precios de 2012.
- **Elegiste A** porque ese 2018–2019 caro parece un régimen de Darwinex y no algo del precio. Los
  datos no pueden distinguir entre las dos lecturas.

**Rango del MC Retest de spread (declarado en `assets/`):**

| | DAX40 | DJ30 | NIKKEI225 | USA500 | USATEC |
|---|---|---|---|---|---|
| múltiplos (2,5–97,5 %) | 0,59–2,49 | 0,45–2,18 | 0,27–1,99 | 0,43–2,50 | 0,43–4,04 |
| Min – Max (puntos, sobre el build) | 85,1 – 361,5 | 118,2 – 566,9 | 165,5 – 1.206,6 | 14,4 – 84,1 | 30,1 – 281,3 |

Los múltiplos son anchos porque recogen los dos regímenes: 2018–2019 por encima de la media
proporcional y 2024–2026 por debajo. El Min queda por debajo del spread del backtest: el MC Retest
también prueba spreads más baratos. Si solo quieres probar spreads aumentados, basta con subir el
Min a 1×.

## 5. Conclusiones

1. **Los costes declarados eran demasiado baratos**: de 3 a 8 veces en XAUUSD y USDJPY. Cualquier
   resultado construido con ellos sobrestima el edge, y más cuanto más opera la estrategia.
2. **Un % fijo no recoge bien el spread.** Ni el oro ni el forex lo mantienen dentro de ±20 %.
   Declarar un spread por tramo es lo mínimo; el oro y los índices se mueven lo bastante entre
   oos1 y oos2 como para merecer uno cada uno.
3. **En los índices, el spread es un problema de régimen, no de precio.** Para el MC Retest, la
   banda al precio típico de cada tramo describe lo que pasó, pero no predice un mercado estresado
   como 2020 o 2026.
4. **El reajuste por operación sirve como criba barata** de lo que el retest DATATICK rompería:
   marca un 3–7 % de estrategias que dejan de ganar OOS. Falta contrastarlo con un retest real.
5. **Antes de octubre de 2017 no hay medición.** En XAUUSD y USDJPY el build (2008–2017) es un 97 %
   modelo. En los índices, el build empieza en 2011–2013 y, antes de sus ticks, lleva el spread
   proporcional al precio (opción A). El 1,25 es el único margen contra spreads que fueron más
   anchos antes.

## 6. Decisiones aplicadas el 27/09/2026

- **Tramos de los índices** (DAX40, DJ30, NIKKEI225, USA500, USATEC), en `assets/_policy.yaml`:
  build desde el inicio de los datos hasta el 31/12/2019, oos1 2020–2023, oos2 del 01/01/2024 al
  31/08/2026. SP500ft se retiró: es el mismo índice que USA500 y no tiene datos en SQX.
- **Un spread por tramo**, y el oos2 con el suyo propio (`spread_oos2`, admitido desde hoy por el
  esquema). Cada uno es la media del spread medio diario de Darwinex en su tramo × 1,25,
  redondeada a 0,1 punto. **Slippage = la mitad del spread de su tramo.**

| activo | spread build (A) | oos1 | oos2 | slippage build | oos1 | oos2 | MC Retest spread |
|---|---|---|---|---|---|---|---|
| DAX40 | 145,3 | 205,0 | 251,9 | 72,7 | 102,5 | 126,0 | 85,1 – 361,5 |
| DJ30 | 260,3 | 385,3 | 327,2 | 130,2 | 192,7 | 163,6 | 118,2 – 566,9 |
| NIKKEI225 | 606,7 | 915,5 | 559,1 | 303,4 | 457,8 | 279,6 | 165,5 – 1.206,6 |
| USA500 | 33,6 | 42,8 | 49,7 | 16,8 | 21,4 | 24,9 | 14,4 – 84,1 |
| USATEC | 69,7 | 104,4 | 114,9 | 34,9 | 52,2 | 57,5 | 30,1 – 281,3 |

- **Sin tocar:** la comisión de los índices (sigue sin valor y bloquea la autoría hasta que la
  pongas), el rango del MC Retest de slippage (sigue en 1×–4× el del tramo, la regla general), y
  XAUUSD y USDJPY, cuya propuesta de 4.3 está sin aplicar.

## 7. Lo que queda abierto

- **Contrastar el reajuste** con un retest DATATICK real en `*_DarwTick_*` sobre unas pocas
  estrategias de una cosecha existente. Es un trabajo corto en un worker.
- **Aplicar o no la propuesta** de XAUUSD y USDJPY, y decidir el «poquito de spread» encima del %.
- **La comisión de los índices.**
- **El modelo de USDJPY hacia 2011–2012.**
- **Si el Min del MC Retest debe ser 1×** (solo spreads aumentados) en vez del 2,5 % real.
