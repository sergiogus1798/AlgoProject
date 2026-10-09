# Pasos 10.5, 11 y 12 — Otras temporalidades (crossTF): cada cálculo, con sus matemáticas y un ejemplo numérico

**Fecha:** 2026-10-06 · **Para:** el dueño, que va a fijar él mismo los criterios · **Alcance:** los pasos 10.5 (fabricar las hermanas escaladas), 11 (retest en SQX) y 12 (análisis en Python). Es de la serie «un documento por paso»; amplía la sección «Pasos 10.5, 11 y 12» de `criterios-pasos-6-a-19-explicados-2026-10-06` y la corrige donde se dice expresamente.

**Qué es:** un documento para aprender y consultar. Primero enseña, desde cero, la estadística que es **nueva** en este paso (lo que ya enseñó el documento del paso 8 sólo se recuerda). Después recorre **todo** lo que el estudio calcula, con el cálculo real sacado del código y un ejemplo rehecho con estrategias reales; luego la regla cargada hoy en `pipeline/autopilot/criteria.yaml`, lo que no cuadra y las decisiones que te quedan.

**Todos los números de los ejemplos están calculados**, no estimados. He vuelto a correr el estudio entero en memoria, con la misma semilla que quedó anotada (3727818526), sobre las operaciones guardadas de la corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04: las 70 celdas salen **idénticas** a las guardadas (diferencia 0 en operaciones, estadístico, p, media y desviación del nulo, `z`, correlación, `z_new` y las combinadas), y los 1.903 hechos del paso coinciden con ellas.

---

## 1. Qué son los pasos 10.5 a 12 y cómo deciden

### 1.1 Qué hacen

Una estrategia que llega aquí ya pasó la puerta OOS (paso 8) y el retest en otros mercados (pasos 9 y 10). Ahora se le cambia **el reloj** y se deja **el mercado**: ¿sigue funcionando la misma idea leída en velas más lentas (o más rápidas)?

- **Paso 10.5** — de cada estrategia, que aquí se llama **madre**, se fabrican **hermanas escaladas**: la misma lógica con los periodos divididos por la razón entre temporalidades. No corre nada en SQX: sólo escribe ficheros.
- **Paso 11** — SQX vuelve a probar madres y hermanas, cada temporalidad en su tarea.
- **Paso 12** — Python mide cada resultado contra el azar de su propia temporalidad, le descuenta lo que la hermana «hereda» de su madre y deja escritos los hechos que lee la regla.

La advertencia que manda sobre todo lo demás, y que el resto del documento desarrolla: **M30, H1 y H4 son la misma serie de precios, troceada distinto.** Una vela de H1 son las mismas dos velas de M30. «También funciona en H1» es una prueba mucho más débil que «también funciona en otro mercado»: no es una muestra nueva, es la misma muestra vista con menos resolución.

### 1.2 Las tareas de SQX que producen la entrada

**Paso 10.5 (`sqx.projects.crosstfload`, con el worker parado).** Coge las supervivientes del databank de otros mercados, fabrica sus hermanas (`sqx/variants/scale.py`) y copia madres y hermanas juntas en el databank `CrossTF_Input`, que se vacía antes. Ninguna tarea de SQX escribe en ese databank: lo rellena este paso. Desde la ventana, los pasos 10.5 y 11 son una sola pulsación.

**Paso 11 (una tarea por temporalidad).** Todas leen `CrossTF_Input` y cada una escribe en su databank:

| tarea | temporalidad | escribe en |
|---|---|---|
| `CrossTF` | la de la madre (aquí M30) | `CrossTF` |
| `CrossTF H1` | H1 | `CrossTF_H1` |
| `CrossTF H4` | H4 | `CrossTF_H4` |

Las tres llevan la misma configuración: sólo el tramo `oos1`, los costes de `oos1`, precisión «temporalidad elegida» y **todas las condiciones de aceptación apagadas** (si estuvieran encendidas, SQX borraría las que fallan y Python no vería a las muertas). Las tareas extra son copias de `CrossTF` a las que sólo se les cambia la temporalidad y el motor. Cada tarea corre **todas** las estrategias del databank de entrada en su temporalidad; por eso de cada estrategia salen varias «celdas» (apartado 2.1).

Qué temporalidades se piden depende de dónde se construyó la madre (`assets/_build.yaml`, bloque `crosstf`):

| madre | temporalidades extra |
|---|---|
| M30 | H1 y H4 |
| H1 | M30, H4 y D1 |

*Código:* `sqx/projects/crosstfload.py`, `sqx/projects/crosstf.py`, `sqx/projects/crosstfsolo.py:19-37`.

### 1.3 Qué datos lee el paso 12

- **Mercado:** el mismo de la madre. En el ejemplo, NIKKEI225.
- **Temporalidades:** M30 (la madre), H1 y H4.
- **Periodo:** sólo `oos1`. Para NIKKEI225 es 2020-01-01 a 2023-12-31: cuatro años, 48 meses. Lo decidiste tú el 2026-10-02: antes la ventana era `build..oos1`, y como la madre se eligió mirando `build`, su p-valor ahí salía 0,0004 por construcción.
- **Costes:** los de `oos1` de la ficha del activo. Hoy, en `assets/symbols/NIKKEI225.yaml`: spread 474,91 puntos, slippage 166,22 puntos, comisión 0. La hermana no recibe otro spread por estar en otra temporalidad: es el mismo instrumento.
- **Población del ejemplo:** 10 madres (las diez que salieron del sorteo de desarrollo del paso 8 aquel día) y sus 20 hermanas. En total 24.925 operaciones de `oos1` y **70 celdas**.

Un aviso sobre los costes que afecta a varias cifras de este documento: el estudio **no** lee el P/L que da SQX; vuelve a valorar cada operación desde las velas, y en esa cuenta **no entran ni el spread ni el slippage** (apartado 3.2 y punto 1 del capítulo 5).

### 1.4 Los tres estados, y cómo se combinan

| estado | qué significa | qué hace el workflow |
|---|---|---|
| **PASA** | cumple la línea exigente de todas las reglas del paso | sigue al paso 13 |
| **LIMBO** | ni prueba ni condena | sigue al paso 13, **marcada** |
| **NO PASA** | alguna regla la da por mala | se **borra** del databank que corta el paso |

El resultado de una estrategia es el de **su peor regla** (`pipeline/autopilot/criteria.py:99-120`). Este paso tiene hoy **una sola regla**, y esa regla lleva `else: limbo`: lo que no llega a la línea de PASA es LIMBO, nunca NO PASA. Y si el dato falta, también LIMBO. **El paso 12, tal como está en disco, no descarta a ninguna madre.**

Dos detalles de cómo se aplica:

- **Se juzga a la madre por sus hermanas.** Los hechos se guardan a nombre de la madre. Si la madre pasa o queda en limbo, sólo ella sigue —en su temporalidad y sin escalar— al databank `CrossTF_Mothers`, que es el que leen las tareas del MC Retest.
- **Las hermanas se quitan siempre.** Son un aparato de medida del paso 11, no candidatas. El juez las marca como descartadas con el motivo «hermana escalada: solo sigue la madre» (`pipeline/autopilot/judge.py:114-120`). No es un fallo de la estrategia.

### 1.5 Cuatro avisos antes de leer números

1. **El día de la corrida de ejemplo este paso no tenía regla.** El resumen de la corrida dice «1903 hechos; ninguno: el paso no tiene criterio». La regla de hoy se cargó después. El resultado combinado que verás en el cierre está calculado hoy, en memoria, con `pipeline.autopilot.criteria` y los hechos guardados.
2. **La lectura del estudio es una propuesta de agente pendiente de tu visto bueno.** Lo dice su propio README («⚠️ an agent's proposal of 2026-10-02, pending the owner») y el código (`studies/transfer/crossTF/verdict.py:7`).
3. **Diez madres no son una población.** Con diez valores no tiene sentido dar los percentiles 5 y 95; donde el documento del paso 8 los daba, aquí doy mínimo, mediana y máximo.
4. **Las cifras de falsos positivos de este paso ya no se pueden rehacer.** Salieron de la calibración del 2026-10-02 (`AlgoData/scratch/calib_step12/`), y esa carpeta ya no está en disco. Lo que queda es lo que copió la ficha `knowhow/research/crosstf-mother-sibling-dependence.md` y el README del estudio.

### 1.6 Las estrategias que nos acompañan

De las tres del documento del paso 8, sólo **C** (`Strategy 14.3.479`) está en esta población: A (`4.9.301`) y B (`16.11.437`) no salieron en el sorteo de diez de aquel día. Así que usamos C y tres nuevas, elegidas para que haya un caso de cada tipo.

| | **P** | **Q** | **R** | **C** |
|---|---|---|---|---|
| nombre | `18.5.355` | `4.13.338` | `16.5.352` | `14.3.479` |
| hermana H1 | sobrevive | heredada | falla | no utilizable |
| hermana H4 | heredada | heredada | falla | no utilizable |
| `combined.z_new` | 1,30 | 0,24 | −2,81 | sin dato |
| con la regla de hoy | LIMBO | LIMBO | LIMBO | LIMBO |

(Todas se llaman `Strategy …`; en la tabla va sólo el número.)

- **P** es el caso «bueno»: una hermana que aporta algo propio.
- **Q** es el caso que justifica todo el paso: su hermana H1 tiene una `z` de 1,77 que parece una confirmación y es casi entera un eco de la madre.
- **R** es el caso malo: sus dos hermanas pierden.
- **C** es el caso «la prueba no se pudo hacer».

Dos invitadas: `Strategy 3.11.426`, la de mejor dato de las diez (1,72), y `Strategy 19.2.363`, que tiene una hermana con un periodo recortado al mínimo.

---

## 2. Fundamentos de este paso

### 2.0 Lo que ya sabes del paso 8, en seis líneas

El documento `criterios-paso-08-puerta-oos-2026-10-06` lo enseña despacio; aquí sólo el recordatorio.

- **Sharpe por operación:** `s = media del P/L / desviación típica del P/L`. Y la **t**: `t = s × √n`, con `n` el número de operaciones.
- **Error estándar:** `desviación / √n`. Con cuatro veces más operaciones, la mitad de incertidumbre.
- **p-valor:** probabilidad de ver un resultado así de bueno si la estrategia no tuviera ventaja. Líneas a una cola: 1,65 ↔ 5 %; 2,33 ↔ 1 %. `Φ(x)` es la probabilidad de que una normal estándar quede por debajo de `x`.
- **Falsos positivos medidos:** el 5 % de la tabla es teoría; lo que vale es cuántas estrategias **sin ventaja** pasan de verdad la línea.
- **Potencia:** probabilidad de que una estrategia **buena** pase la línea. `potencia ≈ Φ(s × √n − línea)`.
- **Máximo de N pruebas y Bayes:** si miras muchas, la mejor es buena por suerte; y «pasó la prueba» no es «es buena»: depende de cuántas buenas hay de partida.

Todo lo que sigue es nuevo.

### 2.1 Lo que fabrica el paso 10.5: las hermanas escaladas

**La idea.** Una media de 40 velas en M30 mira 20 horas. Si la llevas a H1 **tal cual**, mira 40 horas: ya es otra regla. Para que siga mirando 20 horas hay que dividir el periodo entre 2.

**La fórmula.**

```
razón          = minutos de la vela destino / minutos de la vela origen
valor exacto   = valor de la madre / razón
valor escrito  = el mayor de (valor exacto redondeado al entero, 2)
desplazamiento = |valor escrito − valor exacto| / valor exacto
```

- `razón`: de M30 a H1 es 60 / 30 = **2**; de M30 a H4, 240 / 30 = **8**; de H1 a H4, **4**; de H1 a D1, **24**; de H1 a M30, **0,5** (los periodos se doblan).
- El redondeo es al entero más cercano, y los medios suben (2,5 → 3).
- **2 es el suelo**: es el periodo mínimo que acepta el generador de SQX. Si el redondeo da menos de 2, se escribe 2 y la hermana queda marcada como **recortada** (`clamped`).

**Qué se escala y qué no** (tu regla del 2026-09-23: «periodos y salidas por número de velas, nada más»):

| se escala | no se escala |
|---|---|
| lo que SQX tipa como periodo | coeficientes de stop y de objetivo |
| las longitudes de los bloques propios que la tabla `sqx/variants/lengths.yaml` reconoce | niveles y umbrales |
| las salidas «tras N velas» | multiplicadores y desviaciones |

**Ejemplo real: P.** Su madre tiene tres longitudes.

| parámetro | madre M30 | hermana H1 (÷2) | hermana H4 (÷8) |
|---|---|---|---|
| salida tras N velas | 41 | 20,5 → **21** | 5,125 → **5** |
| periodo del ADX | 40 | 20 → **20** | 5 → **5** |
| periodo de las Bollinger | 20 | 10 → **10** | 2,5 → **3** |

En horas: la salida de la madre es a las 41 × 0,5 = 20,5 h; la de la hermana H1 a las 21 h; la de la hermana H4 a las 5 × 4 = 20 h. El peor desplazamiento de la hermana H4 es el de las Bollinger: |3 − 2,5| / 2,5 = **0,20**, un 20 %. Ése es el hecho `rounding_shift` de esa hermana (0,2; coincide).

**Ejemplo de recorte: `Strategy 19.2.363` a H4.** Su salida tras 9 velas, entre 8, da 1,125. Redondeado es 1, menos que el suelo: se escribe **2**. Desplazamiento: |2 − 1,125| / 1,125 = **0,778**. La hermana sale a las 8 horas en vez de a las 4,5: ya no es la misma salida. Su `clamped` vale 1.

**Lo que no se puede escalar.** Si la estrategia lleva un bloque propio con una longitud que la tabla no reconoce, esa longitud se deja como está y la hermana queda marcada (`unverified`). Es lo que le pasa a C: su bloque `CBlc_WAEPosAbvExp_2_2_3` tiene un parámetro `Int1` sin dictaminar. Esa hermana se corre igual, pero su lectura es «no utilizable».

**Lo que la comparación no corrige, y hay que decir siempre.** El coeficiente del stop no se toca, pero el rango que multiplica crece al agregar velas: **si el rango crece con la raíz del tiempo, frente a una madre M30 el stop de la hermana H1 es ≈ 1,4 veces más ancho y el de la H4 ≈ 2,8 veces** (√2 y √8). Una celda de otra temporalidad nunca es «la misma estrategia con el reloj más lento» en limpio.

*Código:* `sqx/variants/scale.py:34-43` (razón), `:46-74` (redondeo, suelo, desplazamiento), `:77-115` (la hermana y su fila de manifiesto).

**Los cuatro papeles de una celda.** Como cada tarea corre todo el databank en su temporalidad, de una madre M30 con hermanas H1 y H4 salen siete celdas:

| papel (`role`) | qué estrategia | en qué velas | cuántas |
|---|---|---|---|
| `baseline` | la madre | las suyas (M30) | 1 |
| `scaled` | cada hermana | las de su destino | 2 |
| `unscaled` | la madre, sin tocar | H1 y H4 | 2 |
| `control` | cada hermana | las de la madre (M30) | 2 |

Con 10 madres: 10 + 20 + 20 + 20 = 70 celdas.

- **`baseline`** es la referencia: lo que hizo la madre en `oos1`.
- **`scaled`** es la pregunta de este paso, la única que se lee.
- **`unscaled`** contesta **otra** pregunta: si el mercado se parece a sí mismo a otra escala. Una media de 40 velas pasa a mirar 160 horas. Fallar aquí no dice nada de la estrategia; no se puntúa.
- **`control`** son los parámetros de la hermana sobre las velas de la madre. Se pensó como comprobación del redondeo, pero dividir todos los periodos por 2 o por 8 sobre las mismas velas es **otra estrategia**. Como lectura falló en 29 de 46 hermanas reales y se invertía con una madre negativa. Desde el 2026-10-02 se enseña y no se lee.

Un detalle de nombres que confunde: en los hechos, `crossTF.cells.control.H1.*` **no** es una celda en velas de H1. Es el control de la hermana H1, corrido en velas de M30 (`pipeline/autopilot/facts.py:184-187`).

### 2.2 Por qué una hermana no es una muestra independiente

Si lanzas una moneda 100 veces y luego otras 100, tienes 200 tiradas. Si lanzas 100 y luego **vuelves a mirar las mismas 100 con otras gafas**, sigues teniendo 100. La hermana es lo segundo: mismo activo, mismos años, velas hechas de las mismas velas.

**Tres cosas se comparten:**

1. **El calendario.** Las dos operan 2020–2023. Si 2020 fue un buen año para comprar caídas, lo fue para las dos.
2. **Las velas.** Una media de 40 velas de M30 y otra de 20 velas de H1 cubren las mismas 20 horas y dan casi el mismo número.
3. **Las operaciones.** Como las señales se parecen, las dos entran casi a la vez y están dentro del mercado a la vez.

**Ejemplo real: Q**, con las operaciones guardadas.

| | madre M30 | hermana H1 |
|---|---|---|
| operaciones en `oos1` | 126 | 117 |
| que coinciden en el tiempo con una de la otra | 118 | **117** |
| entradas a menos de una hora de una entrada de la madre | — | **101** |
| duración media | 20,3 h | 20,5 h |

Las 117 operaciones de la hermana ocurren mientras la madre también está dentro, y 101 de ellas (el 86 %) entran con menos de una hora de diferencia. Son, a efectos prácticos, **las mismas apuestas**.

Qué pasaría si las contaras como independientes: tendrías 126 + 117 = 243 operaciones en vez de 126, y como la t crece con `√n`, la inflarías por `√(243 / 126) = 1,39`. Una t de 1,84 pasaría a parecer 2,56, de ≈ 3 % a ≈ 0,5 % (t 1,84 ↔ p ≈ 3,3 %; 2,56 ↔ p ≈ 0,5 %), sin haber aprendido nada nuevo.

**El contraste: P.** De las 72 operaciones de su hermana H1, sólo 29 coinciden con alguna de la madre y 17 entran a menos de una hora. Aquí el redondeo y la vela más gruesa han hecho que la hermana opere otras ocasiones. Esa diferencia entre Q y P es exactamente lo que mide el número del apartado 2.4.

### 2.3 El azar de cada temporalidad: el nulo de «timing» y la `z` de una celda

**La pregunta.** ¿Ganó la estrategia por **cuándo** entró, o habría ganado igual entrando a cualquier hora?

**El nulo.** Se toman las operaciones reales de la celda y se barajan sólo los **momentos de entrada**:

- cada operación conserva su duración (en velas) y su tamaño (en lotes);
- su vela de entrada se sortea, uniforme, entre todas las de `oos1` en **la temporalidad de esa celda**;
- se valora desde las velas igual que la real;
- se repite **2.500 veces** (2.500 «monos»).

De cada mono se calcula el mismo estadístico que de la real: el **Sharpe por operación**, `s = media / desviación` de sus P/L. Se usa éste y no el neto porque no tiene escala: permite comparar temporalidades con distinto número de operaciones y distinto tamaño.

**Las dos medidas contra ese nulo.**

```
p = (1 + nº de monos con s ≥ s real) / (2.500 + 1)

z = (s real − media de los s de los monos) / desviación típica de los s de los monos
```

- `p` es el p-valor empírico. El «+1» evita que salga 0; el menor posible es 1 / 2.501 = 0,0004.
- `z` dice a cuántas desviaciones del mono medio está la real. A diferencia de `p`, no se satura en 0,0004.

**Ejemplo real: la hermana H1 de P** (72 operaciones), rehecho sorteando otra vez sus 2.500 monos con la semilla guardada.

```
s real                    = 0,2203
media de los monos        = 0,0157
desviación de los monos   = 0,1198
z = (0,2203 − 0,0157) / 0,1198 = 0,2046 / 0,1198 = 1,708
monos con s ≥ 0,2203      = 110
p = (1 + 110) / 2.501     = 0,0444
```

Coincide con los hechos guardados (`z` = 1,7079; `p` = 0,0444). Comprobación cruzada: una normal deja por encima de 1,708 el 4,4 %. Las dos medidas dicen lo mismo.

**Dos cosas que conviene ver en esos números.**

*La desviación del nulo es, casi exactamente, `1 / √n`.* Con 72 operaciones, `1 / √72 = 0,118`; el nulo da 0,1198. Con las 98 de la madre de P, `1 / √98 = 0,101`; el nulo da 0,1026. Así que

```
z ≈ (s real − s del mono medio) × √n
```

es decir, **la `z` de este paso es la t del paso 8, restándole antes lo que gana un mono**.

*El mono medio no gana cero.* Su Sharpe medio es positivo (entre 0,011 y 0,027 en las diez madres) porque el NIKKEI subió en 2020–2023 y todas son largas: un largo puesto al azar también gana algo. Restarlo es la misma idea que la «t descontada la deriva» del paso 8, hecha por otro camino.

**La escala real de la `z`.** El README del estudio dice que, contra una estrategia que ni gana ni pierde, esta `z` se reparte como una normal de desviación **≈ 0,95**, no 1. Si es así, la línea de 1,65 deja pasar `1 − Φ(1,65 / 0,95) = 4,1 %` y no el 5 %: va un poco del lado prudente.

*Código:* `studies/transfer/crossTF/cells.py:71-84` (estadístico, p, media, desviación y `z`); `engines/nulls/model.py:17-48` (el sorteo); `engines/nulls/stats.py:68` (el Sharpe por operación); `engines/nulls/verdict.py:14-31` (el p).

### 2.4 Cuánto se parece una hermana a su madre: ρ

Hace falta un número que diga si la hermana es un eco (Q) o algo distinto (P). El estudio usa la **correlación del beneficio mensual**.

**Cómo se calcula.**

1. Se suma el P/L de la madre mes a mes (por fecha de cierre), y el de la hermana igual.
2. Se ponen los 48 meses de `oos1` en fila. **Un mes sin operaciones cuenta como 0**, no como hueco: que una de las dos no operase es información.
3. Se calcula la correlación de Pearson entre las dos filas:

```
ρ = Σ (mᵢ − m̄)(hᵢ − h̄) / √[ Σ (mᵢ − m̄)² × Σ (hᵢ − h̄)² ]
```

`mᵢ` y `hᵢ` son el P/L del mes `i` de la madre y de la hermana; `m̄` y `h̄`, sus medias. `ρ` (rho) va de −1 a +1: +1 si suben y bajan siempre juntas, 0 si no tienen nada que ver.

**Ejemplo de juguete, a mano.** Cuatro meses.

- Madre: +2, −2, +2, −2. Hermana: +1, −1, +1, −1. Las medias son 0. Numerador: 2 + 2 + 2 + 2 = 8. Denominador: `√(16 × 4) = 8`. **ρ = 1.** La hermana gana la mitad, pero en los mismos meses.
- Madre: +2, −2, +2, −2. Hermana: +1, +1, −1, −1. Numerador: 2 − 2 − 2 + 2 = 0. **ρ = 0.**

**Ejemplo real.** Los ocho primeros meses de 2020, en USD:

| mes | Q madre | Q hermana H1 | P madre | P hermana H1 |
|---|---|---|---|---|
| enero | +180 | +33 | −910 | 0 |
| febrero | +1.269 | +610 | +839 | +90 |
| marzo | +546 | +663 | −725 | +505 |
| abril | −794 | −509 | −1.403 | +457 |
| mayo | +1.099 | +732 | +1.120 | 0 |
| junio | +579 | +457 | −419 | +519 |
| julio | +67 | +29 | −2.345 | 0 |
| agosto | +657 | −8 | +906 | −924 |

Sobre los 48 meses: **ρ = 0,907 en Q** (38 de los 47 meses en que operan las dos tienen el mismo signo) y **ρ = 0,063 en P** (14 de 34). Las dos cifras coinciden con el hecho `corr_vs_baseline`.

**Dos límites de este número.**

- Sale de **48 puntos**. El error estándar de una correlación con 48 datos ronda `1 / √45 = 0,15`. Un ρ de 0,06 y uno de 0,25 no se distinguen bien.
- Es la correlación del **dinero por mes**, usada como sustituto de la correlación entre las dos `z`. Que el sustituto sirva es lo que mide la calibración del apartado 2.6.

Antes de usarlo, el código lo **encierra entre 0 y 0,95**: un ρ negativo se trata como 0, uno por encima de 0,95 como 0,95, y uno que no se puede calcular como 0.

*Código:* `studies/transfer/crossTF/cells.py:87-99` (el P/L mensual), `:202-230` (la correlación), `:168` (el encierro).

### 2.5 `z_new`: lo que la hermana aporta de nuevo

**Primero, lo que NO es.** El nombre invita a pensar que el estudio separa las operaciones «nuevas» de la hermana (las que la madre no hizo) y calcula una `z` sólo con ésas. **No lo hace.** No hay ninguna clasificación de operaciones, ni por hora de entrada ni con ninguna tolerancia. `z_new` es una corrección **sobre la `z` entera** de la hermana, y lo único que mira de la madre es su `z` y el ρ del apartado anterior. (El recuento de operaciones coincidentes del apartado 2.2 lo he hecho yo para ilustrar; el estudio no lo calcula.)

**La idea.** Si no hay ventaja, la `z` de la madre y la de la hermana son dos números al azar, pero **atados**: si a la madre le salió alta por suerte, a la hermana, que hace casi las mismas apuestas, también le saldrá alta. La estadística dice cuánto:

```
si la z de la madre vale z_madre, la de la hermana se espera en  ρ × z_madre
con una dispersión alrededor de ese valor de  √(1 − ρ²)
```

`z_new` es la distancia de la hermana a **lo que se esperaba de ella dado lo que hizo su madre**, medida en esa dispersión:

```
z_new = (z − ρ × z_madre) / √(1 − ρ²)
```

- `z`: la de la hermana contra el nulo de su temporalidad (2.3).
- `z_madre`: la de la celda `baseline` de su madre.
- `ρ`: el parecido (2.4), entre 0 y 0,95.
- `ρ × z_madre`: la **parte heredada**.
- `√(1 − ρ²)`: lo que le queda de «libertad» a la hermana. `1 − ρ²` es la fracción de su `z` que no viene dada por la madre: con ρ = 0,9 es 0,19, un 19 %.

**Por qué quita la parte heredada.** En teoría, si las dos `z` fueran normales con correlación exactamente ρ y no hay ventaja, `z_new` sería una normal estándar **sea cual sea la suerte de la madre**: 5 % por encima de 1,65 tanto si la madre sacó 0 como si sacó 2,5. Pero ρ es un sustituto: se estima con ruido sobre 48 meses y es la correlación del dinero mensual, no de las `z`. Por eso lo medido es 2,7–6,3 % y no 5 %, y 10 % con ρ > 0,9. Eso es justo lo que la `z` sin corregir no cumple. Y resuelve además otro problema: la madre llegó hasta aquí **porque** le fue bien en `oos1` (el paso 8 la eligió por eso). Su `z` alta está garantizada por la selección; `z_new` no premia a la hermana por parecérsele.

**Ejemplo real 1: `z` alta, `z_new` baja (Q, hermana H1).**

```
z        = 1,7721      (por sí sola: p = 0,045, «pasa el 5 %»)
z_madre  = 1,8433
ρ        = 0,9074

heredado     = 0,9074 × 1,8433           = 1,6726
dispersión   = √(1 − 0,9074²) = √0,1766  = 0,4203
z_new        = (1,7721 − 1,6726) / 0,4203 = 0,0995 / 0,4203 = 0,237
```

Con una madre en 1,84 y un parecido de 0,91, de la hermana **ya se esperaba 1,67** sin que supiera nada. Sacó 1,77: una décima más. La «confirmación en H1» de Q es un eco. `z_new` = 0,24 es el percentil 59 del azar.

**Ejemplo real 2: casi no cambia (P, hermana H1).**

```
z = 1,7079   z_madre = 0,5987   ρ = 0,0627

heredado   = 0,0627 × 0,5987 = 0,0375
dispersión = √(1 − 0,0039)   = 0,9980
z_new      = (1,7079 − 0,0375) / 0,9980 = 1,674
```

La hermana apenas se parece a la madre y la madre apenas hizo nada: no hay casi nada que descontar.

**Ejemplo real 3: una hermana mala queda peor (R, hermana H4).** `z` = −1,798, `z_madre` = 0,683, ρ = 0,328: heredado 0,224, dispersión 0,945, `z_new` = (−1,798 − 0,224) / 0,945 = **−2,14**. De ella se esperaba algo ligeramente positivo y perdió.

Los tres coinciden con el hecho guardado al cuarto decimal.

**Tres propiedades que conviene tener presentes.**

1. **Con ρ = 0, `z_new` = `z`.** Con ρ alto, casi todo se descuenta.
2. **Si la madre tiene `z` negativa, `z_new` es mayor que `z`.** El descuento cambia de signo. No ocurre en estas diez (todas las madres tienen `z` positiva).
3. **También descuenta la ventaja de verdad.** Ésta es la contrapartida, y es cuenta mía, no una medición del proyecto. Supón una estrategia con ventaja real, cuya madre y cuya hermana tienen las dos una `z` esperada de 2,5:

| ρ | `z_new` esperada |
|---|---|
| 0,1 | 2,26 |
| 0,2 | 2,04 |
| 0,5 | 1,44 |
| 0,7 | 1,05 |
| 0,9 | 0,57 |

Cuenta: `(2,5 − ρ × 2,5) / √(1 − ρ²)`. Con ρ = 0,9, una estrategia **buena de verdad** se queda en 0,57. No es un defecto: es que una hermana que hace las mismas apuestas no puede enseñar nada que la madre no haya enseñado ya. Pero significa que **este paso sólo puede dar un sí con hermanas que se parezcan poco a la madre**, y que un «heredada» con ρ alto no es una mala noticia: es «no hay prueba nueva».

*Código:* `studies/transfer/crossTF/cells.py:148-170`.

### 2.6 Los falsos positivos medidos, y de dónde sale cada cifra

Hay dos parejas de cifras rodando por los papeles. No se contradicen: son mediciones distintas.

| cifra | qué es | fuente |
|---|---|---|
| `z` sin corregir: **14–40 %** | la cuenta teórica para dos `z` atadas con correlación 0,3 a 0,7 | README del estudio |
| `z` sin corregir: **30 %**; `z_new`: **3,7 %** | una primera medición pequeña (el «smoke null») | README del estudio |
| `z` sin corregir: **17–31 %**; `z_new`: **2,7–6,3 %** | la calibración: estrategias gemelas a coste cero, sin ventaja, por bandas de parecido | ficha de `knowhow`, paquete del Council |

Todas contestan lo mismo: **dado que la madre superó 1,65 por suerte, ¿cuántas veces supera 1,65 una hermana sin ventaja?**

La primera fila se puede rehacer a mano con la normal de dos variables. La he recalculado:

| correlación entre las dos `z` | la hermana supera 1,65 |
|---|---|
| 0 (independientes) | 5,0 % |
| 0,3 | 14,3 % |
| 0,5 | 24,4 % |
| 0,7 | 39,2 % |
| 0,9 | 63,7 % |

Así que «14–40 %» es la teoría para 0,3–0,7. En la calibración, la correlación medida entre las `z` fue de 0,32 a 0,48; la teoría daría 15–23 % y lo medido fue **17–31 %**, algo más. Las cifras que valen son las medidas.

**Lo que dice la calibración** (68 trabajos de nulo, semilla 20261002; las cifras de arriba salen de los 8 primeros):

- La `z` sin corregir no vale como prueba: 17–31 % de falsos positivos donde se espera 5 %.
- `z_new` devuelve la tasa a **2,7–6,3 %** en las bandas con ρ ≤ 0,9.
- **Punto débil:** en las parejas con ρ por encima de 0,9, `z_new` da un **10 %** de falsos positivos con madre afortunada (medido sobre 39 casos). La hermana H1 de Q, con 0,907, está en esa banda.
- Las hermanas redondeadas o recortadas no se detecta inflación de falsos positivos con la muestra de la calibración (4,5–5,7 % frente a 4,0–5,2 %); con ese tamaño no se descarta una diferencia de un punto. Por eso decidiste no descartarlas («Redondea donde puedas, ya está»).

En las diez madres de ejemplo se ve la diferencia a simple vista: de las diez hermanas H1, **seis** tienen una `z` por encima de 1,65; con `z_new`, **dos**. Esto no prueba que las otras cuatro fueran suerte: con ventaja real y ρ = 0,58 (la mediana en H1) una `z` de 2,5 también baja a 1,29. Enseña el tamaño del descuento, no su acierto.

### 2.7 La combinada de una madre: `combined.z_new` y `combined.z_new_max`

Una madre M30 tiene dos hermanas y por tanto dos `z_new`. Hace falta un solo número por madre para la regla.

**La fórmula.**

```
combined.z_new     = (suma de las z_new de las hermanas válidas) / √k
combined.z_new_max = la mayor de esas z_new
combined.n_tested  = k
```

`k` es el número de hermanas **que se pudieron escalar** (no marcadas `unverified`) **y que tienen `z_new`**. Una hermana muda o con menos de 30 operaciones no tiene `z_new` y no cuenta. Si `k` es 0, la combinada no existe y el hecho falta.

El revisor tenía razón en la forma: es una **combinación de Stouffer**, suma dividida por `√k` (`cells.py:172-175`). El matiz es que lo que se suma son las `z_new`, no las `z` sin corregir.

**Por qué se divide por `√k`.** Si sumas `k` normales estándar independientes, la suma tiene desviación `√k`. Dividiendo por `√k` vuelve a tener desviación 1 y se puede leer con las líneas de siempre.

**Ejemplos reales.**

```
P:            (1,6737 + 0,1578) / √2 = 1,8315 / 1,4142 = 1,295     máx = 1,674
Q:            (0,2367 + 0,1015) / √2 = 0,239                       máx = 0,237
R:            (−1,8395 − 2,1397) / √2 = −2,814                     máx = −1,840
3.11.426:     1,7231 / √1 = 1,723    (su hermana H4 no operó: k = 1)
C:            k = 0  →  sin dato
```

**Qué supone, y cómo la correlación lo infla.** La división por `√k` sólo es correcta si los sumandos son independientes. Si se parecen entre sí con correlación `r`, la desviación verdadera de la combinada de dos es

```
desviación = √(1 + r)        (con k sumandos: √(1 + (k − 1) × r))
```

y la línea de 2,33 deja pasar más del 1 %:

| `r` entre los dos sumandos | desviación | pasa 2,33 | pasa 1,65 |
|---|---|---|---|
| 0 | 1,00 | 1,0 % | 5,0 % |
| 0,05 | 1,02 | 1,2 % | 5,4 % |
| 0,3 | 1,14 | 2,1 % | 7,5 % |
| 0,5 | 1,22 | 2,9 % | 9,0 % |
| 0,7 | 1,30 | 3,7 % | 10,4 % |

**Ejemplo trabajado.** Dos hermanas con `z_new` = 1,65 cada una. La combinada da 3,30 / 1,414 = **2,33**: PASA. La cuenta dice «dos resultados del 5 % hacen uno del 1 %». Eso es verdad si son dos pruebas distintas. Si las dos hermanas, H1 y H4, están contando lo mismo con `r` = 0,7, la combinada de 2,33 vale en realidad 2,33 / 1,30 = 1,79: un resultado del 3,7 %, no del 1 %.

**Qué hay medido.**

- La correlación entre las `z_new` de dos hermanas de una misma madre, sin ventaja: **0,03 y 0,07** (el «smoke null»; `cells.py:21-23`). Con eso la inflación sería pequeña: 1,1–1,2 % en vez de 1,0 %. Esa cuenta es mía a partir de su medición.
- La combinada por encima de **1,65**: entre el **3,6 y el 5,7 %** de las madres sin ventaja (ficha de `knowhow`).
- La combinada por encima de **2,33**, que es la línea de la regla: **no medido**. En eso el revisor acierta: la línea de PASA de este paso no tiene tasa de falsos positivos medida. Lo razonable es esperar algo cerca del 1 %, pero nadie lo ha contado, y en la banda de ρ > 0,9 las propias `z_new` fallan el doble.

Para comparar con lo que pasaría sumando las `z` **sin corregir**: madre y dos hermanas con correlación 0,7 entre sí dan una desviación de 1,55, y 2,33 lo pasaría el 6,7 %. En el paso 10 el mismo error está medido: «Stouffer ≥ 1,65» lo pasa entre el 5 y el 24 % de las estrategias sin ventaja, y por eso allí está prohibido como criterio.

**Dos rarezas de la combinada que afectan al veredicto.**

- **Una hermana mediocre diluye; una hermana muda, no.** P tiene una hermana en 1,67 y otra en 0,16: combinada 1,30. `Strategy 3.11.426` tiene una hermana en 1,72 y otra que **no operó**: combinada 1,72. La segunda queda mejor que la primera por tener menos prueba. La regla no mira `n_tested`.
- **Una hermana mala resta.** En R las dos pesan en contra y la combinada es −2,81.

**La variante «máximo» y su precio.** `combined.z_new_max` se queda con la mejor hermana. Parece más amable, pero elegir la mejor de `k` es mirar `k` veces:

```
probabilidad de que la mejor de k supere la línea = 1 − (1 − α)^k
```

con `α` la probabilidad de una sola. Con dos hermanas: `1 − 0,95² = 9,75 %` para 1,65 y `1 − 0,99² = 1,99 %` para 2,33. **El máximo dobla los falsos positivos.** Para que la mejor de dos mantenga el 1 %, la línea tendría que subir a **2,57** (y a 1,95 para mantener el 5 %). Ningún criterio lo usa hoy.

### 2.8 Las seis lecturas de una hermana

Cada hermana escalada recibe una palabra. Las comprobaciones van **en este orden** y se queda con la primera que se cumple:

| orden | lectura | condición exacta |
|---|---|---|
| 1 | `unusable` (no utilizable) | lleva una longitud de bloque propio sin dictaminar |
| 2 | `silent` (muda) | 0 operaciones en `oos1` |
| 3 | `no_data` (sin datos) | no tiene `z_new`: menos de 30 operaciones, ella **o su madre** |
| 4 | `survives` (sobrevive) | `p` < 0,05 **y** `z_new` > 1,645 **y** estadístico > 0 |
| 5 | `inherited` (heredada) | estadístico > 0 |
| 6 | `fails` (falla) | lo demás: estadístico ≤ 0 |

- El «estadístico» es el Sharpe por operación de la celda (2.3).
- **1,645** es `Φ⁻¹(0,95)`: sale del `alpha: 0.05` de `config.yaml`, el mismo para las dos condiciones.
- Las tres primeras significan **«la prueba no se pudo hacer»**. No son un fallo de la estrategia.
- **Sobrevive** pide las dos cosas: ganar a los monos de su temporalidad **y** añadir algo a lo que ya enseñó la madre.
- **Heredada** es «ganó dinero, pero no más de lo que su madre predice».
- **Falla** es «perdió dinero».

**Ejemplos reales.**

| hermana | `p` | `z_new` | lectura | por qué |
|---|---|---|---|---|
| P, H1 | 0,044 | 1,674 | sobrevive | cumple las tres |
| `19.2.363`, H1 | 0,038 | 1,581 | heredada | `z_new` no llega a 1,645 |
| Q, H1 | 0,045 | 0,237 | heredada | eco de la madre |
| R, H1 | 0,908 | −1,840 | falla | estadístico −0,060 |
| `3.11.426`, H4 | — | — | muda | 0 operaciones |
| C, H4 | — | — | no utilizable | (además, 9 operaciones) |

El caso de `19.2.363` enseña lo fino del corte: gana a sus monos con holgura (p = 0,038) y se queda a 0,06 de la línea de `z_new`.

**Los hechos que salen de aquí.** Por cada hermana, seis hechos `crossTF.reading.<TF>.<lectura>`: un 1 en la lectura que le tocó y un 0 en las otras cinco. Y por madre, seis contadores `crossTF.reading.n_<lectura>`, que valen 0, 1 o 2. Los ceros se escriben a propósito: un contador ausente se leería como «dato que falta», y un dato que falta es LIMBO.

En las 20 hermanas del ejemplo: 2 sobreviven, 8 heredadas, 5 fallan, 4 no utilizables, 1 muda, 0 sin datos.

*Código:* `studies/transfer/crossTF/verdict.py:10-17` (las seis), `:56-74` (el orden y las condiciones); `pipeline/autopilot/facts.py:196-202` (los hechos).

### 2.9 El mínimo de operaciones por celda: 30, y lo que vale

Por debajo de **30 operaciones** en `oos1` no se sortea ningún mono: la celda no tiene `p` ni `z`, y la hermana lee «sin datos» (`config.yaml`, `usable.min_trades`).

Treinta es un suelo de **estimabilidad** —«con menos no se puede ni calcular»—, no una garantía de que la prueba vea algo. La potencia lo dice:

```
potencia ≈ Φ(s × √n − línea)
```

Con una ventaja real de `s` = 0,15 por operación (la referencia que usa el proyecto) y la línea de 1,65:

| operaciones `n` | `s × √n` | potencia a 1,65 | potencia a 2,33 |
|---|---|---|---|
| 30 | 0,82 | 20 % | 7 % |
| 51 | 1,07 | 28 % | 11 % |
| 72 | 1,27 | 36 % | 15 % |
| 121 | 1,65 | 50 % | 25 % |
| 200 | 2,12 | 68 % | 42 % |

La cuenta de la primera fila: `0,15 × √30 = 0,15 × 5,48 = 0,82`; `0,82 − 1,65 = −0,83`; `Φ(−0,83) = 0,20`. Con 30 operaciones, **cuatro de cada cinco estrategias buenas no pasan** ni siquiera la línea del 5 %.

La cuenta de las 121: para tener un 50 % hace falta que `s × √n` iguale la línea, `√n = 1,65 / 0,15 = 11`, `n = 121`. Para un 80 % harían falta 276. Y para un 50 % a 2,33, 241.

Ése es el argumento de Feynman en el Council: **con menos de 121 operaciones, LIMBO**. No está en disco.

121 operaciones es la potencia del 50 % sólo si la ventaja es 0,15 por operación; con la ventaja realista (≈ 0,02) esa potencia es del 8 % (Φ(0,02 × √121 − 1,65) = Φ(−1,43)), y para un 50 % harían falta unas 6.800 operaciones. El mínimo de 121 evita el caso peor; no da una prueba capaz de ver una ventaja pequeña.

Dos agravantes. Primero, esa potencia es la de la `z` sin corregir; la de `z_new` es menor (apartado 2.5, propiedad 3). Segundo, 0,15 es una ventaja generosa: la dispersión real de ventaja medida en el proyecto es ≈ 0,02.

En el ejemplo, de las 16 hermanas utilizables sólo **5** llegan a 121 operaciones, y de las 10 madres, 4.

### 2.10 Por qué D1 va aparte

Tu regla: D1 nunca dentro del crosscheck de mercados adicionales; tarea propia, sin crosschecks, con el motor de MetaTrader 4. Hay tres razones, y cada una es un fallo que ya ocurrió.

**1. Un export con varias temporalidades del mismo símbolo no se puede separar.** Al principio las temporalidades eran bloques de una sola tarea de «retest en mercados adicionales». SQX exporta las operaciones de todos los bloques mezcladas por hora, y como el símbolo es el mismo en todos, nada dice de qué bloque es cada una. Se separaban por el ritmo de operaciones, y salió mal: desde H1, las operaciones de M30 se puntuaron como si fueran la madre en H1. Cada celda se valoraba sobre las velas equivocadas, **sin ningún error en pantalla**. Desde el 2026-09-30 cada temporalidad es una tarea con su databank.

**2. En D1, con el motor de MetaTrader 5, la estrategia no opera.** Una estrategia D1 sólo entra a las 00:00, y la sesión de las cuentas de fondeo abre a las 00:05. Con el motor de MT5, que respeta la sesión, no hizo ni una operación: todas las celdas D1 habrían leído «muda». El motor de MT4 no pide sesión. Por eso `assets/_build.yaml` dice `engines: {D1: MetaTrader4}` y `crosstfsolo.py` escribe la tarea `CrossTF D1` con ese motor y con el crosscheck apagado.

**3. Desde H1, la hermana D1 escalada es otra estrategia.** La razón es 24. La cuenta:

| periodo en H1 | ÷ 24 | se escribe | desplazamiento |
|---|---|---|---|
| 20 | 0,83 | 2 (suelo) | 140 % |
| 14 | 0,58 | 2 (suelo) | 243 % |
| 9 | 0,38 | 2 (suelo) | 433 % |
| 7 | 0,29 | 2 (suelo) | 586 % |

Medido: los parámetros se mueven entre un 140 y un 586 % y **todos** los periodos chocan con el suelo. Una hermana así tiene todos sus periodos en 2: no es la madre a escala, es una estrategia nueva. En la corrida de H1 del 2026-09-30, todas las hermanas D1 escaladas salieron no utilizables; sólo se leyó la fila sin escalar.

**Cómo está hoy.** La doctrina sigue listando D1 para una madre H1. La calibración del 2026-10-02 corrió sin él por orden tuya («quítalo»), con `crosstfload --targets M30 H4`, sin tocar la doctrina ni el diseño de la tarea. Una madre **M30**, como las del ejemplo, no tiene D1 en ningún caso.

*Código:* `sqx/projects/crosstfsolo.py:13-15` y `:19-37`; fichas `knowhow/sqx-drive/crosstf-one-task-per-timeframe.md` y `knowhow/export/data-all-blocks.md`.

### 2.11 Los pasos 10 y 12 son una sola prueba, y un PASA aquí no certifica

**Por qué una sola.** El paso 8, el 10 y el 12 leen los mismos años: `oos1`. El 10 cambia el mercado; el 12 cambia el reloj; el calendario es el mismo. El Council contó las muestras **de verdad nuevas** de toda la cadena y le salieron tres: `oos1`; «otros mercados + otras temporalidades», juntos; y `oos2`, la única limpia.

**Qué significa «una sola actualización».** En el lenguaje de Bayes del paso 8, cada prueba multiplica las posibilidades a favor por un número, su razón de verosimilitud (LR):

```
posibilidades nuevas = posibilidades viejas × LR
posibilidades = probabilidad / (1 − probabilidad)
```

El Council fijó, **por convención**, que los pasos 10 y 12 juntos valen como mucho un LR de 3. No 3 cada uno. La cuenta que hicieron, que puedes rehacer:

```
de partida, tras el paso 8:     24 %   →  posibilidades 0,24 / 0,76 = 0,316
tras 10 y 12 juntos (× 3):      0,316 × 3 = 0,947      →  0,947 / 1,947 = 49 %
tras oos2 (× 2,1 a 2,8):        1,99 a 2,65            →  67 % a 73 %
```
El ×3 es sólo para la que PASA; ninguna de las diez pasa, así que todas siguen en el punto de partida. Y con la horquilla de partida 5–49 %, ese 49 % es en realidad 14–74 %.

Si contaras el 10 y el 12 como dos pruebas de LR 3, llegarías a 0,316 × 9 = 2,84, un 74 %, **antes** de mirar `oos2`. Ése es el error que la convención evita. (El 24 % de partida es el centro de una horquilla muy ancha, 5–49 %; y el 3 es una convención, no una medición.)

**Por qué un PASA promueve y no certifica.** Tres razones:

1. La línea de 2,33 de la combinada no tiene tasa de falsos positivos medida (2.7).
2. Es la misma muestra de calendario que ya se usó para elegir a la madre.
3. Munger, en el Council: este paso «resuelve un LIMBO, no certifica». Sirve, por ejemplo, para una H1 que el paso 8 dejó en LIMBO a propósito hasta que una muestra nueva la subiera.

**Por qué nunca descarta (`else: limbo`).** La prueba es frágil y tiene poca potencia: hermanas con periodos recortados, el stop que se ensancha, celdas con 30–70 operaciones, y una corrección que con ρ alto no deja pasar ni a las buenas. Un «no» aquí no distingue «la estrategia es mala» de «la prueba no ve». Con esa incertidumbre, descartar costaría estrategias buenas a cambio de nada medido.

**Lo que hay y lo que no hay en el código.** La regla del paso está cargada. Pero **no hay ningún mecanismo que «promueva»** nada: cada paso que juzga escribe su propio PASA/LIMBO y ahí se queda. Tampoco hay nada que junte los pasos 10 y 12 en una sola cuenta. La promoción y la prueba conjunta son, hoy, una manera de leer los resultados, no algo que el piloto automático haga.

---

## 3. Lo que calcula el estudio, pieza a pieza

### 3.1 Los ficheros

El estudio escribe en `AlgoData/reports/<proyecto>/CrossTF/<día>/crossTF/`:

| fichero | qué lleva |
|---|---|
| `cells.parquet` | una fila por celda (70 en el ejemplo) |
| `verdict.csv` | una fila por hermana escalada (20), con su lectura |
| `crossTF.json`, `.html`, `.md` | la página que pinta la ventana |
| `manifest.json` | el fichero leído, la orden y la semilla de los nulos |

De ahí `pipeline/autopilot/facts.py:161-203` saca los hechos, todos **a nombre de la madre**: 1.903 en el ejemplo, de 115 tipos. Se agrupan en tres familias: `crossTF.cells.*`, `crossTF.combined.*` y `crossTF.reading.*`.

Los nombres de la primera familia tienen esta forma:

```
crossTF.cells.<papel>.<TF>.<medida>
```

con `<papel>` uno de `baseline`, `scaled`, `unscaled`, `control`, y `<TF>` la temporalidad de la celda (en `control`, la de destino de la hermana).

### 3.2 Lo que ganó la celda

Hechos: `…trades`, `…seen`, `…sharpe`, `…net`, `…pf`, `…dd`, `…retdd`, `…sharpe_total`

**Qué miden.** El resultado de la celda en `oos1`.

**Cómo se calculan.** Aquí está la trampa del paso. El estudio **no usa el P/L de SQX**. Vuelve a valorar cada operación desde las velas, con las mismas tres líneas con que valora a los monos, para que la real y sus monos se puedan comparar:

```
P/L revalorado = lotes × valor del punto × (apertura de la vela de salida − apertura de la vela de entrada) − coste
coste          = movimiento entre los precios de entrada y salida que da SQX − P/L que da SQX
```

Ese `coste` recoge comisión y swap. **El spread y el slippage no están en él**, porque SQX los mete dentro del precio de entrada y de salida que anota. Resultado: el P/L revalorado es **mayor** que el de SQX en una cantidad fija por lote.

Lo he medido en las 69 celdas con operaciones: la diferencia es de **0,509 USD por lote y operación**, constante. Entre el valor del punto (0,0631 USD) son 8,07 unidades de índice, es decir, 807 puntos. Y `474,91 + 2 × 166,22 = 807,35`: el spread más el slippage de entrada y de salida de la ficha. Cuadra al punto; que ésa sea la causa es deducción mía por la aritmética, no algo que el código diga.

Sobre ese P/L revalorado:

- `trades`: número de operaciones.
- `sharpe` = `seen`: media / desviación típica (es el mismo número dos veces; `seen` es «el estadístico que se juzga»).
- `net`: suma.
- `pf`: ganancias / pérdidas.
- `dd`: mayor caída de la curva acumulada.
- `retdd`: `net / dd`.

`sharpe_total` es distinto: es **tu** Sharpe anual (P/L de cada día hábil, media / desviación × √252) y **sí** sale del P/L de SQX, con todos los costes. No tiene p-valor: los monos no tienen calendario. Se enseña, no se juzga.

*Código:* `engines/market/calibrate.py:44-73`; `engines/nulls/simulate.py:15-39` y `:101-117`; `engines/nulls/stats.py:62-72`; `core/significance.py:146-164`.

**Ejemplo numérico.** La madre de P, 98 operaciones:

| | con el P/L de SQX | revalorado (el hecho) |
|---|---|---|
| neto (USD) | 5.392 | 8.617 |
| Sharpe por operación | 0,0503 | 0,0803 |

La diferencia de neto es 3.225 USD: 98 operaciones × 32,91 USD (64,6 lotes de media × 0,509). El Sharpe sube 0,030, que es 32,91 / 1.094 (la desviación del P/L).

Y la invitada `Strategy 10.11.484` (madre), para ver `retdd`: neto 18.485,58, caída máxima 3.693,92; `18.485,58 / 3.693,92 = 5,00`. Coincide.

**Cómo leerlo.**

- **El `net`, el `pf` y el `sharpe` de estos hechos son más optimistas que los de SQX.** No los compares con los del paso 8 ni con los del databank. C aparece aquí con un neto de 8.174 USD; en el paso 8 tenía 4.690.
- La `z` casi no se entera: a los monos tampoco se les cobra el spread, así que la ventaja se queda a los dos lados de la resta.
- Lo que sí se entera es **el signo**, y el signo decide entre «heredada» y «falla» (punto 1 del capítulo 5).

Rangos en el ejemplo (mínimo · mediana · máximo):

| hecho | madre M30 | hermana H1 | hermana H4 |
|---|---|---|---|
| `trades` | 58 · 102 · 187 | 51 · 104 · 394 | 0 · 53 · 778 |
| `sharpe` | 0,07 · 0,14 · 0,28 | −0,09 · 0,15 · 0,41 | −0,61 · 0,02 · 0,14 |
| `pf` | 1,20 · 1,45 · 2,14 | 0,80 · 1,52 · 3,02 | 0,10 · 1,05 · 1,44 |
| `sharpe_total` | 0,25 · 0,40 · 1,12 | −0,73 · 0,58 · 1,27 | −1,08 · −0,22 · 0,45 |

Las hermanas H4 son claramente peores que las H1: su Sharpe mediano es casi cero.

### 3.3 Dónde queda la celda frente al azar

Hechos: `…null_mean`, `…null_sd`, `…z`, `…p`, `…p_sharpe`, `…p_net`, `…p_pf`, `…p_dd`, `…p_retdd`

**Qué miden.** La posición de la celda entre sus 2.500 monos.

**Cómo se calculan.** `null_mean` y `null_sd` son la media y la desviación típica del Sharpe de los monos; `z` y `p`, las del apartado 2.3. `p` y `p_sharpe` son el mismo número. Los otros cuatro `p_*` son el mismo p-valor empírico calculado sobre el neto, el profit factor, la caída y el neto / caída de los mismos monos (en `p_dd`, «mejor» es «más pequeña»). Sólo existen si la celda tiene 30 operaciones o más. *Código:* `cells.py:78-84`.

**Ejemplo numérico.** El de 2.3 (hermana H1 de P). Y la madre de P: `s` = 0,0803, media 0,0188, desviación 0,1026; `z` = 0,0615 / 0,1026 = **0,599**; 689 monos la igualan o superan; `p` = 690 / 2.501 = **0,276**.

**Cómo leerlo.**

- `null_sd` ≈ `1 / √n`: es la incertidumbre que da el número de operaciones. Una celda con 30 operaciones tiene 0,18; una con 400, 0,05.
- `null_mean` positivo es la deriva del mercado para un largo.
- `z` por encima de 1,65 «pasa el 5 %» **en una celda sola y sin madre**. En una hermana no vale (2.6).
- Los cuatro `p_*` extra no entran en ninguna lectura.

Rangos (mínimo · mediana · máximo):

| hecho | madre M30 | hermana H1 | hermana H4 |
|---|---|---|---|
| `z` | 0,60 · 1,11 · 2,43 | −1,30 · 1,72 · 2,68 | −1,80 · 0,20 · 1,04 |
| `p` | 0,008 · 0,138 · 0,276 | 0,006 · 0,045 · 0,908 | 0,147 · 0,413 · 0,967 |
| `null_sd` | 0,08 · 0,10 · 0,14 | 0,05 · 0,10 · 0,15 | 0,04 · 0,11 · 0,19 |

Fíjate en la mediana de la `z` de las hermanas H1: 1,72, **más alta que la de las madres** (1,11). Sin corregir, parecería que en H1 funcionan mejor que en casa.

### 3.4 El parecido con la madre

Hecho: `…corr_vs_baseline` (en `scaled`, `unscaled` y `control`)

**Qué mide y cómo se calcula.** La correlación del P/L mensual contra la celda `baseline` (2.4). Aquí el P/L es el de SQX.

**Ejemplo numérico.** Q: 0,907 (H1) y 0,516 (H4). P: 0,063 y 0,138.

**Cómo leerlo.** Alto = la hermana hace las apuestas de la madre; `z_new` le descontará casi todo. Bajo = la hermana es, en la práctica, otra estrategia. Por encima de 0,9 la corrección está en su zona débil.

| | hermana H1 | hermana H4 |
|---|---|---|
| mínimo · mediana · máximo | 0,06 · 0,58 · 0,91 | 0,03 · 0,19 · 0,52 |

A más distancia de temporalidad, menos parecido: coincide con lo que dice el README (0,5–0,95 con la temporalidad contigua, 0,3–0,7 con H4), aunque aquí H4 sale más bajo.

### 3.5 Lo que la hermana aporta de nuevo

Hecho: `crossTF.cells.scaled.<TF>.z_new`

**Qué mide, cómo se calcula, ejemplos:** apartado 2.5.

**Cómo leerlo.** Es una `z` como las demás: 1,65 ↔ 5 %, 2,33 ↔ 1 %, con las salvedades de 2.6. Una rareza: el hecho existe también para las hermanas **no utilizables** (C tiene −0,83 en H1), pero ésas no entran ni en la lectura ni en la combinada.

| | hermana H1 | hermana H4 |
|---|---|---|
| mínimo · mediana · máximo | −2,30 · 0,32 · 1,72 | −2,14 · 0,09 · 0,70 |

La mediana de las hermanas H1 baja de 1,72 (`z`) a 0,32 (`z_new`). Ése es el tamaño de lo heredado.

### 3.6 Lo que la fabricación le hizo a la hermana

Hechos: `…ratio`, `…n_scaled`, `…rounding_shift`, `…clamped`, `…unverified` (en `scaled` y `control`)

**Qué miden.** `ratio`: la razón (2 u 8). `n_scaled`: cuántos parámetros se reescribieron. `rounding_shift`: el mayor desplazamiento por redondeo. `clamped`: 1 si algún periodo se quedó en el suelo. `unverified`: 1 si lleva una longitud sin dictaminar.

**Cómo se calculan y ejemplo:** apartado 2.1.

**Cómo leerlo.** Sólo `unverified` cambia algo: convierte la lectura en «no utilizable» y saca a la hermana de la combinada. `rounding_shift` y `clamped` son números para medir, nunca una puerta.

| | hermana H1 | hermana H4 |
|---|---|---|
| `rounding_shift` (mín · mediana · máx) | 0,01 · 0,02 · 0,11 | 0,09 · 0,20 · 0,78 |
| hermanas recortadas | 0 de 10 | 1 de 10 |
| no utilizables | 2 de 10 | 2 de 10 |

En una población grande el recorte es mucho más frecuente: medido sobre 600 estrategias, el 23 % de las hermanas H1→H4 y el 53 % de las M30→H4.

### 3.7 Las razones contra la madre

Hechos: `…sharpe_vs_original`, `…net_vs_original`, `…pf_vs_original`, `…dd_vs_original`, `…retdd_vs_original`, `…sharpe_total_vs_original`

**Qué miden y cómo se calculan.** El valor de la celda dividido por el de la `baseline`. *Código:* `facts.py:192-195`.

**Ejemplo numérico.** Hermana H1 de P: `0,2203 / 0,0803 = 2,74`. Su Sharpe es 2,7 veces el de la madre.

**Cómo leerlo.** Con cuidado. Si la madre tiene un valor pequeño, la razón se dispara sin significar nada (en el ejemplo hay un `sharpe_vs_original` de 7,3 en una celda `unscaled` de H4 y un `sharpe_total_vs_original` de −13,5 en una `control`; entre las hermanas escaladas van de −4,3 a 2,7). Y el `net` no es comparable entre temporalidades: el tamaño por operación cambia (las madres operan con unos 69 lotes de media; las hermanas H4, con 23). Ninguna regla los lee.

### 3.8 Las filas que se enseñan y no se juzgan

**`unscaled`.** La madre, sin tocar, en H1 y en H4. En H4 casi nunca hay nada que medir: 9 de las 10 madres hacen menos de 30 operaciones (mediana 16,5) y no tienen ni `p` ni `z`. En H1, la `z` mediana es −0,36. No se puntúa (2.1).

**`control`.** Los parámetros de la hermana en las velas de la madre. Suele operar muchísimo más (mediana 189 operaciones para el control de H1, 570 para el de H4, hasta 5.711) y con una `z` mediana cerca de cero (0,18 y 0,01). No se lee (2.1).

### 3.9 La suma de la madre

Hechos: `crossTF.combined.n_tested`, `crossTF.combined.z_new`, `crossTF.combined.z_new_max`

**Qué miden, cómo se calculan, ejemplos:** apartado 2.7.

**Cómo leerlo.** `combined.z_new` es **el hecho que lee la regla**. Las diez madres:

| madre | `n_tested` | `z_new` comb. | `z_new_max` |
|---|---|---|---|
| `3.11.426` | 1 | 1,72 | 1,72 |
| `19.2.363` | 2 | 1,61 | 1,58 |
| `18.5.355` (P) | 2 | 1,30 | 1,67 |
| `4.13.338` (Q) | 2 | 0,24 | 0,24 |
| `3.9.284` | 2 | −0,35 | 1,26 |
| `10.11.484` | 2 | −0,35 | 0,41 |
| `13.3.390` | 2 | −1,54 | 0,12 |
| `16.5.352` (R) | 2 | −2,81 | −1,84 |
| `14.3.479` (C) | 0 | sin dato | sin dato |
| `15.9.352` | 0 | sin dato | sin dato |

Mínimo −2,81, mediana −0,05, máximo 1,72 (sobre las ocho que lo tienen). Con ocho valores la mediana no distingue nada: con ventaja real y ρ alto también sale cero (apartado 2.5). Lo que sí se sale del azar es la cola de abajo: 4 de las 15 `z_new` de hermana están por debajo de −1,65, donde una normal pondría 0,75. Un corte en −1,65 no sería «el 5 % peor». `Strategy 19.2.363` saca 1,61 con dos hermanas que ninguna «sobrevive»: (1,58 + 0,70) / √2. Y una de esas dos es la recortada del apartado 2.1.

### 3.10 Las lecturas

Hechos: `crossTF.reading.<TF>.<lectura>` y `crossTF.reading.n_<lectura>`

**Qué miden, cómo se calculan, ejemplos:** apartado 2.8.

**Cómo leerlo.** `n_survives` es el recuento más natural («¿cuántas hermanas aportan algo propio?»), y **ninguna regla lo lee hoy**. En el ejemplo vale 1 en dos madres (P y `3.11.426`) y 0 en las otras ocho.

---

## 4. El criterio cargado y por qué

### 4.1 La regla, tal como está en disco

`pipeline/autopilot/criteria.yaml`, líneas 125-130:

```
"12":
  cut: CrossTF
  segment: oos1
  rules:
    # Council: z_new>=2.33 PASS; below it LIMBO, never FAIL. Raw z never counts.
    - {fact: crossTF.combined.z_new, pass: ">= 2.33", else: limbo}
```

| hecho | PASA | LIMBO | NO PASA |
|---|---|---|---|
| `crossTF.combined.z_new` | ≥ 2,33 | todo lo demás, y el dato que falta | nunca |

No lleva `by:`: vale igual para cualquier temporalidad y activo. El modo de desarrollo (`dev`) sólo sortea en el paso 8; aquí no actúa.

**De dónde sale cada parte.**

- **Que se lea `z_new` y nunca la `z`:** falsos positivos medidos. 17–31 % con la `z`, 2,7–6,3 % con `z_new`.
- **La línea de 2,33:** convención (el 1 % nominal de una normal). No tiene tasa de falsos positivos medida para la combinada; la de 1,65 sí: 3,6–5,7 % (medido, según la propia calibración, con madres H1 y gemelas a coste cero; para madres M30, el 53 % de cuyas hermanas H4 salen recortadas, no hay medición propia).
- **Que nunca descarte:** poca potencia (20 % con 30 operaciones, 50 % con 121) y fragilidad de la comparación (recortes, stop más ancho). Es del Council. 121 operaciones es la potencia del 50 % sólo si la ventaja es 0,15 por operación; con la ventaja realista (≈ 0,02) esa potencia es del 8 % (Φ(0,02 × √121 − 1,65) = Φ(−1,43)), y para un 50 % harían falta unas 6.800 operaciones. El mínimo de 121 evita el caso peor; no da una prueba capaz de ver una ventaja pequeña.
- **Que el dato que falta sea LIMBO:** tu regla general del 2026-10-01. Aquí encaja: «sin dato» es «la prueba no se pudo hacer».

### 4.2 Cómo sería el resultado ideal

Una madre con todo esto:

- las dos hermanas utilizables (`n_tested` = 2), ninguna recortada;
- **parecido bajo** con la madre: ρ por debajo de 0,2 (con ρ = 0,5 incluso una ventaja real de z = 2,5 sólo rinde `z_new` = 1,44; con ρ = 0,2, 2,04);
- cada hermana con 121 operaciones o más en `oos1`, y la madre también;
- las dos hermanas con `z_new` ≥ 1,65 cada una → combinada ≥ 2,33;
- las dos «sobreviven».

En el ejemplo, 5 de 16 hermanas llegan a 121 operaciones y ninguna madre cumple todo.

El techo honesto:

- En las diez del ejemplo, **ninguna** llega a 2,33. La mejor tiene 1,72, y con una sola hermana.
- Con dos hermanas, la suma de sus `z_new` debe ser ≥ 3,30 (por ejemplo 1,65 + 1,65, o 2,5 + 0,8); con una, 2,33 ella sola.
- Con ρ = 0,9 una estrategia buena de verdad se queda, de media, en 0,57 por hermana (2.5). Para ella este paso **no puede** decir que sí.
- La potencia de la combinada frente a una ventaja real no está medida (el paquete del Council propone hacer curvas de potencia con una ventaja plantada; no están hechas).
- Y un PASA es media prueba compartida con el paso 10 (2.11), no un certificado.

### 4.3 Si mueves este umbral

Calculado sobre las diez madres con `pipeline.autopilot.criteria`. Con la regla de hoy: **0 PASA, 10 LIMBO (8 por debajo de 2,33 y 2 sin dato), 0 NO PASA.**

**Mover la línea de PASA** (sin descartar a nadie):

| regla | PASA | LIMBO | NO PASA |
|---|---|---|---|
| combinada ≥ 2,33 (hoy) | 0 | 10 | 0 |
| combinada ≥ 1,65 | 1 | 9 | 0 |
| `z_new_max` ≥ 2,33 | 0 | 10 | 0 |
| `z_new_max` ≥ 1,65 | 2 | 8 | 0 |
| `n_survives` ≥ 1 | 2 | 8 | 0 |

Lo que cuesta y lo que da: como LIMBO también sigue, **mover la línea de PASA no cambia qué estrategias llegan al paso 13**; sólo cambia la etiqueta. Lo que cambia es cuánto vale esa etiqueta: a 1,65 la combinada tiene falsos positivos medidos del 3,6–5,7 %; con el máximo, el doble (≈ 9,75 % nominal a 1,65; 1 − 0,95² = 9,75 % supone hermanas independientes; con r = 0,03–0,07 casi lo son, pero con r = 0,7 el máximo se parecería a una sola prueba y la cifra bajaría).

**Añadir una línea de NO PASA** (hoy no hay):

| descartar si la combinada es | PASA | LIMBO | NO PASA |
|---|---|---|---|
| nunca (hoy) | 0 | 10 | 0 |
| < −1,65 | 0 | 9 | 1 |
| < 0 | 0 | 6 | 4 |
| < 1,65 (la banda del Council leída como corte) | 0 | 3 | 7 |

La primera opción quita sólo a R. La última quita siete de diez, y entre ellas a P (1,30, con una hermana que sobrevive) y a `19.2.363` (1,61).

Lo que se gana es máquina: en la corrida de ejemplo, el MC Retest del paso 13 tardó 1.010 segundos para diez madres, unos 100 por madre. Descartar siete ahorra unos 700 segundos por corrida. Lo que se arriesga no está medido: nadie ha contado cuántas estrategias buenas tienen una combinada negativa. Con potencias del 20–50 % por celda, serán bastantes.

**Añadir un mínimo de 121 operaciones** (Feynman). No cambia ningún estado hoy (ya son todas LIMBO). De las 16 hermanas utilizables, 5 llegan a 121; sólo una madre (`19.2.363`) tiene sus dos hermanas por encima, y ella misma tiene 66.

---

## 5. Lo que no cuadra o no está medido

**1. El signo que separa «heredada» de «falla» se lee sobre un P/L sin spread ni slippage.** La lectura dice «falla = perdió dinero en `oos1`», pero la condición es «Sharpe revalorado ≤ 0», y el revalorado no cobra 807 puntos por operación (3.2). En el ejemplo, dos hermanas tienen el signo cambiado: la H1 de C (SQX: −723 USD; revalorado: +1.244) y la H4 de `15.9.352` (SQX: −4.433; revalorado: +4.712). Las dos son «no utilizables», así que **ninguna lectura cambia hoy**; en otra población, una hermana que perdió dinero se leería como «heredada». La `z` no tiene este problema. Los hechos `net`, `pf`, `retdd` y `sharpe` del paso son, por lo mismo, más optimistas que los de SQX. La ficha `knowhow/research/crossmarket-returns-miss-entry-offset.md` describe el mismo fallo ya arreglado en el estudio de otros mercados.

**2. La regla y la lectura usan varas distintas.** La lectura es por hermana y a 1,645; la regla es por madre, sobre la combinada, a 2,33. P tiene una hermana que «sobrevive» y es LIMBO. `n_survives` no lo lee nadie.

**3. La combinada premia tener menos prueba.** Una hermana muda, sin datos o no utilizable no entra; una mediocre, diluye. `3.11.426` (una hermana, 1,72) queda por delante de P (dos hermanas, 1,67 y 0,16 → 1,30). La regla no mira `n_tested`.

**4. La línea de 2,33 no tiene falsos positivos medidos.** Hay medida a 1,65 (3,6–5,7 %) y la correlación entre sumandos (0,03–0,07, sobre el «smoke null»). A 2,33, nada.

**5. `z_new` falla el doble con ρ > 0,9.** 10 % de falsos positivos con madre afortunada, sobre 39 casos. Una de las 16 parejas utilizables del ejemplo está ahí (Q, H1). El código corta en 0,95, no en 0,9.

**6. ρ sale de 48 meses** (error ≈ 0,15 con ρ cerca de 0; ≈ 0,03 con ρ = 0,9, porque el error es (1 − ρ²)/√47; Q, con 0,907 ± 0,03, puede caer a cualquier lado del corte de 0,9, decisión 7) y es la correlación del dinero mensual, no la de las `z`. La calibración dice que funciona de media; pareja a pareja es ruidoso.

**7. Con ρ bajo, «sobrevive» es otra lotería.** Si la hermana no se parece a la madre, `z_new` ≈ `z`: lo que se mide es si **esa otra estrategia** gana a sus monos. Eso tiene un 5 % de falsos positivos propio y no está claro que confirme la ventaja de la madre. Con ρ alto no se puede aprobar; con ρ bajo no está claro qué se aprueba. Es razonamiento mío; no está medido.

**8. El comentario del código dice «5 %» donde lo medido es 2,7–6,3 %** (`verdict.py:50-52`), y el README mezcla la cifra teórica (14–40 %) con la de la primera medición (30 % y 3,7 %). Las de la calibración son 17–31 % y 2,7–6,3 %.

**9. La calibración ya no está en disco.** `AlgoData/scratch/calib_step12/` no existe. Las cifras de falsos positivos sólo se pueden citar de la ficha; no las he podido comprobar.

**10. El Council y el disco no dicen exactamente lo mismo.** En la deliberación: «`z_new` PASA ≥ 2,33, LIMBO 1,65–2,33», y Feynman «con menos de 121 operaciones, LIMBO». La ficha de `knowhow` propone «pass ≥ 2,33, limbo ≥ 1,65», que escrito así descartaría por debajo de 1,65. En disco: combinada ≥ 2,33, y todo lo demás LIMBO, sin mínimo de operaciones. El informe anterior ya decía que la banda no hace falta en disco, y es correcto; lo que no está es el mínimo de 121.

**11. No hay promoción ni prueba conjunta en el código.** Ni un PASA del paso 12 sube nada, ni los pasos 10 y 12 se cuentan juntos (2.11). El comentario de la regla del paso 8 para H1 habla de que «una muestra nueva (10, 12, 20) la promueve»: nada lo hace.

**12. La lectura sigue siendo propuesta de agente**, pendiente de ti.

**13. La `z` depende de la semilla.** Con 2.500 monos, la media y la desviación del nulo tienen un error del orden del 2 %, así que una `z` se mueve unas centésimas de una corrida a otra. Si la semilla no se fija, una madre pegada a la línea puede cruzarla. En la corrida de ejemplo quedó anotada y por eso se ha podido rehacer.

**14. Una hermana recortada entra en la combinada como cualquier otra.** La H4 de `19.2.363` sale a las 8 horas en vez de a las 4,5 y aporta 0,70 a un 1,61. Medido: el recorte no infla los falsos positivos. No medido: si cambia la potencia.

**15. El stop no se escala** y, si el rango crece con la raíz del tiempo, frente a una madre M30 el de la hermana H1 es ≈ 1,4 veces más ancho y el de la H4 ≈ 2,8 veces (√2 y √8). Propiedad declarada de la comparación, sin corregir.

**16. Sin medir, además:** la potencia del paso con una ventaja plantada; una población sin ventaja pasada por toda la cadena; H4 como temporalidad de la madre; D1 escalado.

**Dónde mi cuenta difiere del informe anterior** (`criterios-pasos-6-a-19-explicados`, sección 5): en los números, en nada; los he rehecho y coinciden (−2,81 a +1,72, mediana −0,05, diez en LIMBO). Añado tres cosas que allí no estaban: que para la combinada sí hay una medición a 1,65 y una correlación medida entre sumandos (allí se decía sólo que «supone hermanas independientes y no lo son»); que el P/L del estudio no lleva spread ni slippage; y que la combinada trata distinto a una hermana muda y a una mediocre.

---

## 6. Cierre

### 6.1 La regla, en una tabla

| regla | PASA | LIMBO | NO PASA | respaldo |
|---|---|---|---|---|
| `crossTF.combined.z_new` | ≥ 2,33 | lo demás y sin dato | nunca | `z_new`: medido; la línea: convención |

### 6.2 El resultado combinado hoy

Sobre las diez madres de `Trade_NIKKEI225_M30_volatilidadL`, con la regla de hoy:

| estado | madres | cuáles |
|---|---|---|
| PASA | 0 | — |
| LIMBO | 10 | 8 con dato por debajo de 2,33; 2 sin dato |
| NO PASA | 0 | — |

Las diez siguen al paso 13. Las 20 hermanas se retiran, como siempre.

### 6.3 Decisiones abiertas

Cada una con lo que cuesta y lo que da, sobre estas diez madres.

1. **Aprobar o no la lectura** (las seis palabras y la regla de «sobrevive»). Hoy es propuesta de agente. Aprobarla no cambia ningún estado; deja de estar en el aire.

2. **Qué lee la regla: la combinada, el máximo o el número de hermanas que sobreviven.** A 2,33 las tres dan 0 PASA. A 1,65: 1, 2 y 2. La combinada es la única con falsos positivos medidos (3,6–5,7 % a 1,65, medido con madres H1 y gemelas a coste cero; para madres M30 no hay medición propia). El máximo los dobla. `n_survives ≥ 1` es la más fácil de explicar y tiene el mismo problema que el máximo.

3. **Si el paso debe descartar alguna vez.** Hoy no. Con «combinada < −1,65»: pierdes 1 de 10 (R, cuyas dos hermanas pierden dinero) y ahorras unos 100 segundos de MC Retest. Con «< 0»: pierdes 4 y ahorras 400. Con «< 1,65»: pierdes 7, entre ellas P, y ahorras 700. Cuántas buenas se van con cada corte no está medido.

4. **Un mínimo de 121 operaciones para poder PASAR.** Coste hoy: ninguno (nadie pasa). Con él, sólo 5 de 16 hermanas serían «legibles»: el paso quedaría casi siempre en LIMBO, que es lo honrado con esa potencia.

5. **Exigir las dos hermanas (`n_tested` = 2) para PASAR.** Quita la ventaja de la hermana muda. Coste hoy: ninguno. A 1,65 quitaría el único PASA (`3.11.426`).

6. **Arreglar el P/L revalorado** para que cobre spread y slippage, al menos en el signo que separa «heredada» de «falla». Coste: trabajo de código. Hoy cambiaría 0 lecturas de 20; evita que una hermana que perdió se lea como «heredada».

7. **Qué hacer con las parejas de ρ > 0,9.** Tienen el doble de falsos positivos. Opciones: no contarlas en la combinada, o bajar el tope de 0,95 a 0,9. Afecta a 1 de 16 parejas (Q, H1), y no cambia su estado.

8. **D1 para las madres H1:** dentro, como dice la doctrina, o fuera, como en la calibración. Dentro cuesta una tarea más por corrida y, con estrategias de periodos cortos, da hermanas que son otra estrategia. No afecta a las madres M30.

9. **Programar la promoción y la prueba conjunta 10 + 12**, o dejarlas como lectura. Hoy el piloto automático no hace ninguna de las dos.

10. **Medir la línea de 2,33** con una población sin ventaja pasada por los pasos 10.5–12. Es lo único que convertiría el PASA de este paso en algo con cifra. Hasta entonces, lo que dice el encabezado de `criteria.yaml`: provisional, no congelar.
