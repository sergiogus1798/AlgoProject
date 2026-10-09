# Paso 17 — Walk Forward Correlation (WFC): qué se calcula, con qué estadística y qué criterio hay cargado

**Fecha:** 2026-10-07 · **Para:** el dueño, que va a fijar los criterios él mismo · **Alcance:** el paso 17 (el análisis en Python del lote de variantes). Del paso 16.5 (la fábrica de variantes) sólo lo necesario para entender qué lee el WFC.

**Qué es:** el documento de consulta del paso 17, con la misma forma que el del paso 16 (`criterios-paso-16-spp-2026-10-07`). Explica desde cero la estadística que este paso usa (correlación de rangos, su intervalo, N efectivo, persistencia del top, el nulo de volteo de signos), repasa **todos** los números que escribe el estudio, cita el criterio tal como está hoy (ninguna regla en `pipeline/autopilot/criteria.yaml`; un veredicto propio del estudio que el paso 20 lee y marca), y cierra con lo que no cuadra y con las decisiones que te quedan.

**Revisión:** revisado por dos miembros del Council (Feynman, Taleb) el 2026-10-07; correcciones aplicadas.

**De dónde salen los números.** Todos los ejemplos son de la corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04 (NIKKEI225, M30, largas), la misma del documento del paso 16: diez madres, un lote de 500 o 501 variantes por madre (`AlgoData/strategyPermutations/Trade_NIKKEI225_M30_volatilidadL/<madre>/`), y el WFC ejecutado ese día a las 22:38 con la composición por defecto, `build+oos1` contra `oos2`.

- La partición **`build` contra `oos1`** está **recalculada por mí** desde `metrics.parquet` y `equity.parquet` de cada lote, y comparada con lo que el estudio dejó escrito: el rho, el Pearson y la pendiente coinciden en las tres cifras que guarda la tabla; el exceso de persistencia, al cuarto decimal; los rangos del nulo, iguales.
- Las particiones que tocan **`oos2`** las **cito** de los ficheros que el estudio ya escribió (`estudios/wfc.json` y `wfc.json` de cada lote) y que el paso 20 de esa corrida ya abrió. No he hecho ninguna cuenta nueva sobre las columnas de `oos2`: sólo he comprobado la aritmética del intervalo a partir del rho y el número de puntos guardados, y he contado operaciones del original.
- Lo que el estudio no publica —el nulo del propio rho, el N efectivo, el rho por estrato, los duplicados— lo he calculado yo, sólo sobre `build` y `oos1`, y lo digo en cada sitio. «Ilustrativo» quiere decir cuenta hecha a mano para enseñar, no medida.

**Aviso sobre `oos2`.** Este documento enseña números de `oos2` de diez madres porque son lo que la corrida escribió. Elegir un umbral mirando esos números es una mirada a `oos2`: si lo haces, apúntala en el ledger (lo pide también la ficha `knowhow/research/wfc-top-persistence-sign-flip-null.md`).

**Ninguna línea de este documento está congelada.** `criteria.yaml` lo dice en la primera línea de `steps`: provisional hasta que una población sin ventaja haya recorrido la cadena; los pasos 17, 18, 19, 21, 23 y 24 «sólo anotan: sin regla a propósito».

---

## 0. En una página

**La pregunta del paso.** Si ordeno las variantes de una madre por lo que ganaron dentro de muestra, ¿ese orden se parece al orden de lo que ganaron fuera? Si se parece, elegir parámetros mirando el pasado sirve de algo en esta familia. Si no, optimizar no compra nada.

**Lo que hay cargado hoy:**

- En `pipeline/autopilot/criteria.yaml`: **nada**. No existe la entrada `"17"` (ni siquiera con `rules: []`).
- En `pipeline/autopilot/offered.yaml`: dos hechos **ofrecidos sin umbral**, `wfc.summary.exceso_persistencia_minimo` y `wfc.summary.exceso_persistencia_oos1`.
- En el propio estudio: **un veredicto con umbral**, `rho_floor: 0.30`. Si el intervalo del rho queda entero por encima de 0,30, «Fiable»; entero por debajo, «No fiable»; si lo cruza, «Indeciso». Ese veredicto lo lee el paso 20. Con `joint.pieces: sin_fallo`, un «No fiable» marca DESCARTAR en el `verdict.csv` del paso 20 (6 de 10 aquí), pero el autopiloto no lo aplica: el 20 no tiene `cut` y todas las supervivientes siguen. Sólo corta si se aplica a mano con `/curate`.

**Lo que sale en la corrida real** (diez madres):

| | Fiable | Indeciso | No fiable |
|---|---|---|---|
| composición pedida, `build+oos1` → `oos2` (escrito por el estudio) | 3 | 1 | 6 |
| `build` → `oos1` (recalculado) | 2 | 3 | 5 |

Sólo una madre (`10.11.484`) es «Fiable» en las dos. El exceso de persistencia del top es positivo en las dos ventanas en 3 de 10.

**Las nueve cosas que conviene saber antes de leer el resto:**

1. **El WFC mide orden, no ganancia.** E (`3.11.426`) tiene el 89 % de sus variantes ganando dentro y fuera, y sale «No fiable» con rho −0,20. G (`4.13.338`) tiene el 98 % ganando en los dos lados y rho 0,01. Al revés: `13.3.390` pierde fuera en la variante mediana (−1.758 USD en `oos1`) y su persistencia del top es de las más altas (+34 puntos). La frase del README y de la nota de la figura —«una nube que llena los cuatro cuadrantes» frente a «una nube sobre la diagonal»— describe otra cosa que lo que el número calcula.
2. **El veredicto cambia con la composición, y la de por defecto gasta `oos2`.** C (`14.3.479`) da rho 0,67 «Fiable» con `build` → `oos1` y rho 0,00 «No fiable» con `build+oos1` → `oos2`. `3.9.284`, al revés: 0,02 y 0,54. Entre las diez, la correlación de rangos entre el rho medido contra `oos1` y el medido contra `oos2` es **−0,60** (intervalo de −0,90 a +0,07, y ese intervalo es optimista: las diez madres comparten plantilla, mercado, ventanas y `build`, así que no son diez casos independientes). El signo no se sostiene; lo que sí se sostiene es que una ventana **no confirma** a la otra.
3. **El intervalo trata 300 variantes como 300 observaciones independientes, y no lo son.** Las variantes de una madre operan los mismos días. Con el nulo que el propio estudio usa para la persistencia (voltear el signo de cada día fuera de muestra), aplicado por mí al rho: una familia **sin ventaja** da un rho con desviación típica de 0,09 a 0,41 (mediana 0,26), no los 0,05–0,07 que supone la fórmula. Traducido a «N efectivo» sale de 8 a 145 (mediana 17) donde el código cuenta de 220 a 477; es un orden de magnitud, y mide sobre todo cuánto se alinea el orden de dentro con la exposición (quién opera más), no «observaciones independientes». Con ese nulo, y dejando fijo el orden de dentro de cada madre, sale «Fiable» sin ventaja el 8 % de las veces en mediana (por madre; máximo 22,5 %, mínimo 0 %). La fórmula supone prácticamente un 0 %. No es la tasa de falsos positivos del paso: ésa no está medida.
4. **«Indeciso = fabrica más puntos» no vale.** Lo dicen el README y el texto del veredicto. Más variantes de la misma madre sí afinan el rho de **este** camino de precios, pero no añaden caminos: el ruido que importa (qué habría salido con otros días) no baja. Medido: con la mitad de las variantes de C, la desviación del nulo pasa de 0,41 a 0,43, es decir, no cambia. (El ejemplo de copias de 2.5 enseña otro mecanismo, el del intervalo que se estrecha solo por contar más puntos.) Y «Indeciso» no es el caso habitual, como dice el código: es el menos frecuente (1 de 10).
5. **Hoy el autopiloto no puede juzgar el paso 17.** El extractor de hechos devuelve **cero filas** para este paso (lo he ejecutado): busca carpetas de resultado y el WFC escribe un fichero (`pipeline/autopilot/facts.py:222`). Y una regla escrita hoy en `"17"` **no se juzgaría nunca**: la cola añade 17, 18 y 18.5 como lecturas a ciegas (`pipeline/autopilot/tail.py:107-110`), sin pasar por el único camino que deja un paso pendiente de juicio (`tail.py:69-73`).
6. **Los dos hechos ofrecidos no se sostienen de una ventana a la otra.** El exceso de persistencia supera su nulo en 4 de 10 madres en `oos1` y en 2 de 10 en `oos2`, y **no son las mismas**: ninguna lo supera en las dos. El hecho «peor ventana» (`_minimo`) no supera el nulo en ninguna. Además `_minimo` incluye `oos2`, y la ficha que lo respalda se calibró sólo con `oos1`.
7. **El ratio de Sharpe OOS/IS divide dos Sharpe que no son el mismo.** El de un tramo suelto es el de SQX; el de una unión (`build+oos1`) lo calcula Python desde la curva diaria. Sobre los mismos días, el de SQX sale entre un 1 % y un 38 % mayor (mediana por variante, según la madre). La ayuda de la tabla dice que los dos son los de SQX. Es un diagnóstico, no un criterio, y así lo declara el estudio.
8. **En la nube hay duplicados y controles.** G tiene 203 puntos distintos de 332; F lleva 9 copias exactas del original (los «pares inertes» y la cobertura de parámetros congelados). El SPP quita los duplicados antes de contar; el WFC no. No cambian el rho (de 0,576 a 0,557 en el peor caso), pero sí el N con que se calcula el intervalo.
9. **Los suelos de operaciones no son los que dicen sus comentarios.** Los comentarios hablan de 50 en total y 30 por lado; los valores son 100 y 50. Con 50 por lado, la madre de `13.3.390` (45 operaciones en `oos2`) queda fuera de su propia nube en la composición por defecto. Y bajar el suelo por lado de 50 a 30 mueve el rho de G de 0,01 a 0,28.

---

## 1. Qué es el paso 17 y cómo decide

### 1.1 Dónde está

Familia «optimización» (`studies/optimisation/`), junto al CSCV (18), las superficies por mercado (18.5) y la WFM (19). Los cuatro forman el **bloque ciego**: se calculan uno detrás de otro y nadie los lee hasta que existen los cuatro; los abre el paso 20 (`studies/closing/blindJoint/`). El WFC y el CSCV leen el mismo lote con el mismo suelo de operaciones y la misma partición (`engines/variants/`): son dos preguntas sobre los mismos puntos.

### 1.2 El paso 16.5, en lo justo

El SPP (pasos 15-16) recorre miles de combinaciones de parámetros, pero cada tarea elige las suyas: no hay «la misma variante» medida en `build` y en `oos1`. Para poder comparar dentro contra fuera hace falta fabricar un lote fijo y pasarlo por las tres ventanas. Eso hace el 16.5:

1. **Diseño.** Con el `design_brief` que dejó el paso 16 (qué parámetros están vivos, en qué niveles), `sqx.variants.make` elige unas 500 combinaciones por madre en tres estratos, más los controles:

   | estrato | qué es | en C (`14.3.479`) |
   |---|---|---|
   | Vecindad | a uno o dos pasos de nivel del original | 99 |
   | Factorial | rejilla completa sobre pocos niveles de cada parámetro | 296 |
   | Cobertura | barrido de todo el espacio, parámetros congelados incluidos | 99 |
   | Original | la madre reconstruida por la fábrica (`P00000`) | 1 |
   | Control (canarios) | permutaciones del SPP de resultado ya conocido y «pares inertes» | 6 (uno no supera el suelo de operaciones) |

2. **Retest.** SQX retestea el lote en tres tareas —`WFC 1 IS` (`build`), `WFC 2 OOS1`, `WFC 3 OOS2`—, cada una con los costes de su tramo (`assets/_build.yaml:370-373`).
3. **Cosecha.** `sqx.variants.collect` escribe `metrics.parquet` (contrato C3): **una fila por variante** con 13 métricas por tramo, y los tramos son seis: los tres sueltos y tres uniones (`build+oos1`, `oos1+oos2`, `ALL`; `collect.py:25-26`). `sqx.variants.equity` escribe `equity.parquet`: la ganancia **día a día** de cada variante.

Dos detalles de la cosecha que importan aquí:

- **Cómo se hace una unión** (`sqx/variants/united.py:91-113`): lo que se puede sumar se suma (beneficio neto, operaciones, ganancias y pérdidas brutas). El drawdown y el Sharpe no se pueden sumar, así que **se recalculan en Python** desde la curva diaria unida (`united.py:129-132`). El Sharpe de un tramo suelto, en cambio, es el que guardó SQX. Vuelve en 2.7 y 5.8.
- **El primer suelo de operaciones, el duro** (`collect.py:100-103`, `assets/_build.yaml:368`): una variante con menos de **100** operaciones sumando los tres tramos no entra en `metrics.parquet`. Se cuenta en `collected.json`.

Lo que quedó en la corrida:

| | C `14.3.479` | E `3.11.426` | F `15.9.352` | G `4.13.338` | las diez |
|---|---|---|---|---|---|
| fabricadas | 501 | 501 | 501 | 500 | 500–501 |
| fuera por menos de 100 operaciones en total | 84 | 72 | 0 | 40 | 0–224 |
| en `metrics.parquet` | 417 | 429 | 501 | 460 | 276–501 |

### 1.3 Qué datos lee el paso 17

| fichero | qué usa de él |
|---|---|
| `metrics.parquet` | por variante: `NetProfit`, `NumberOfTrades` y `SharpeRatio` de cada tramo; el estrato |
| `equity.parquet` | la ganancia diaria de cada variante en los días fuera de muestra, sólo para el nulo |
| `collected.json` | cuántas se quedaron fuera por el suelo duro |
| `segments.parquet` | sólo para saber el activo y el timeframe |

No lee ninguna operación. Un punto de la nube es una variante: en el eje horizontal su **beneficio neto** dentro de muestra, en el vertical su beneficio neto fuera.

### 1.4 Las cuatro composiciones

`build` va siempre dentro de muestra. Las cuatro maneras admitidas de partir (`engines/variants/panel.py:17-18`):

| dentro (IS) | fuera (OOS) | nombre | qué pregunta |
|---|---|---|---|
| `build` | `oos1` | `build__oos1` | ¿lo construido predice el primer tramo que el generador no vio? |
| `build` | `oos2` | `build__oos2` | ¿y el último? |
| `build` | `oos1+oos2` | `build__oos1+oos2` (atajo `oos1_oos2`) | ¿predice todo lo que vino después? |
| `build+oos1` | `oos2` | `build+oos1__oos2` (atajo `oos2_only`) | dando por vistos los dos primeros, ¿sigue apareciendo en el que nadie ha mirado? |

**La de por defecto es la última** (`engines/variants/config.yaml:46`, `split_mode: oos2_only`), y es la que lanza el autopiloto: su línea de comando no elige composición (`ui/daemon/runner/optimisation.py:38-41`). Es decir, el WFC que se guarda como «el» WFC de una madre usa `oos2` como único fuera de muestra.

Eso es coherente con la política: `oos2` está reservado **para** WFC, CSCV, superficies, WFM, el paso 20 y el stop ATR (`assets/_policy.yaml:48`). La puerta del ledger sólo cierra a un agente autónomo; a una sesión con una persona delante la deja pasar y apunta el renglón.

**En cada ejecución se calculan las cuatro** (todas las que la puerta permite) y van al mismo resultado, para que la ventana cambie de una a otra sin recalcular (`report.py:110-122`). En el ledger sólo se apunta la pedida (`report.py:152-157`). Vuelve en 5.5.

Las fechas del activo (`assets/_policy.yaml:102-106`): `build` 2011-09-19 a 2019 (8,3 años), `oos1` 2020 a 2023 (4 años, 1.033 días en la curva), `oos2` 2024 a 2026-09-30 (2,75 años).

### 1.5 Cómo decide hoy

En tres sitios, y conviene tenerlos separados:

1. **El veredicto propio del estudio** (`measure/correlation.py:49-76`): «Fiable», «Indeciso», «No fiable» o «Sin dato», según dónde cae el intervalo del rho respecto a 0,30. En el contrato son los estados `pass`, `watch`, `fail`, `none` (`contract/wfc.py:12`).
2. **El paso 20** lee ese estado tal cual, sin recalcular nada (`studies/closing/blindJoint/pieces.py:46-60`), y lo combina con los de CSCV, superficies y WFM. Con `joint.pieces: sin_fallo` (tu decisión del 2026-10-04, `blindJoint/config.yaml:26`), una madre pasa si **ninguna** pieza está en `fail` (`blindJoint/readings.py:17`); «Indeciso» se tolera. Una madre con una pieza en `fail` sale como DESCARTAR en el `verdict.csv` del paso 20 (`blindJoint/report.py:64`). **El autopiloto no aplica ese veredicto:** el paso 20 no tiene entrada ni `cut` en `criteria.yaml`, el juez devuelve «ninguno» (`judge.py:172-173`) y todas las supervivientes siguen. Sólo corta si alguien lo aplica a mano con `/curate`.
3. **El criterio del autopiloto** (`criteria.yaml`): nada para el paso 17.

Los tres estados de siempre —PASA, LIMBO, NO PASA— y la regla «el resultado de una estrategia es el de su peor regla; un hecho que falta es Limbo» son del autopiloto (`pipeline/autopilot/criteria.py`). Aquí no se aplican todavía, porque no hay regla.

### 1.6 Tres avisos

1. **Las diez son un sorteo.** Las mismas del documento del paso 16: «10.000 → 10» en el paso 8 sin mirar el veredicto, y los pasos 10 a 16 sin reglas aquel día. No son supervivientes de nada. Un indicio en contra, sin explicar: la madre queda por encima de la mediana de `oos1` de su propia nube en 9 de las 10 (por azar, p ≈ 0,01). Vuelve en 2.9.
2. **No hay `hechos.parquet` del paso 17** en ninguna corrida. El paso 20 sí guardó uno, y de este paso sólo lleva una clave: `blindJoint.verdict.17_wfc`, que es el rho de la composición pedida.
3. **En esa corrida el paso 20 descartó a las diez** (`blindJoint.verdict.pass` = 0 y `verdict_csv.drop` = 1 en todas). Seis de ellas llevaban el WFC en «No fiable».

### 1.7 Las estrategias que nos acompañan

Las cuatro del documento del paso 16, con su letra. El punto «Original» de cada nube reproduce el neto de la madre que allí se citaba (por ejemplo G: 53.725 USD en `build`, 22.721 en `oos1`).

| | **C** | **E** | **F** | **G** |
|---|---|---|---|---|
| nombre (`Strategy …`) | `14.3.479` | `3.11.426` | `15.9.352` | `4.13.338` |
| variantes usadas, `build` → `oos1` | 304 | 271 | 477 | 332 |
| rho `build` → `oos1` | 0,668 | −0,203 | 0,317 | 0,009 |
| llamada `build` → `oos1` | Fiable | No fiable | Indeciso | No fiable |
| rho `build+oos1` → `oos2` (pedida) | 0,002 | 0,068 | −0,219 | 0,395 |
| llamada pedida | No fiable | No fiable | No fiable | Fiable |
| variantes que ganan dentro y fuera (`oos1`) | 63 % | 89 % | 20 % | 98 % |

Para lo que este paso enseña: **C es «la que cambia de veredicto con la ventana»**, **E y G son «todo gana y el orden no dice nada»**, y **F es «la familia que pierde»** (la mitad de sus variantes pierde dentro y fuera) con una persistencia alta en `oos1` y la peor de las diez en `oos2`.

---

## 2. Fundamentos de este paso

### 2.0 Lo que ya sabes de los pasos 8, 10 y 16, en seis líneas

```
error estándar = desv / √n
p = probabilidad de que algo sin ventaja llegue ahí por suerte
n efectivo: observaciones que se parecen cuentan como menos observaciones
percentil q: el valor por debajo del cual queda el q % de los casos
mediana = percentil 50          IQR = p75 − p25
un nulo: lo que saldría si no hubiera nada; lo observado se compara con él
```

Lo que sigue es lo **nuevo** de este paso.

### 2.1 La nube dentro/fuera: qué contesta y qué no

Tienes una madre y, digamos, 300 variantes suyas. Cada variante es un punto: lo que ganó en la ventana de dentro (eje horizontal) y lo que ganó en la de fuera (eje vertical).

**Qué contesta.** Si las variantes que más ganaron dentro son también las que más ganaron fuera, la superficie de parámetros «lleva información»: mirar el pasado para elegir parámetros acierta más que elegir al azar. Es la condición para que tenga sentido optimizar (y para creerse la WFM del paso 19, que reoptimiza una y otra vez).

**Qué no contesta.**

- **No dice si la familia gana.** El orden puede mantenerse en una familia que pierde entera, y puede no mantenerse en una que gana entera. Es la primera de las cosas que conviene saber, y los datos reales la enseñan en 3.2.
- **No dice si la madre es buena.** La madre es un punto de los 300.
- **No es una muestra de 300 pruebas.** Todas las variantes viven en el mismo histórico. Es el apartado 2.5.

### 2.2 La correlación de rangos (rho de Spearman), desde cero

**La idea.** Quieres un número entre −1 y +1 que diga cuánto se parecen dos ordenaciones. +1: el mismo orden. −1: el orden exactamente invertido. 0: no tienen nada que ver.

**Por qué rangos y no los dólares.** Con los dólares (la correlación «de Pearson»), una sola variante desbocada decide el resultado. Con los rangos —el puesto de cada variante, 1.º, 2.º, 3.º…— una variante desbocada es sólo «la primera», por mucha distancia que saque.

**Ejemplo a mano.** Seis variantes, beneficio en miles de USD:

| variante | dentro (IS) | fuera (OOS) | puesto IS | puesto OOS | diferencia d | d² |
|---|---|---|---|---|---|---|
| A | 2 | 1 | 1 | 1 | 0 | 0 |
| B | 4 | 3 | 2 | 3 | −1 | 1 |
| C | 5 | 2 | 3 | 2 | 1 | 1 |
| D | 7 | 5 | 4 | 5 | −1 | 1 |
| E | 9 | 4 | 5 | 4 | 1 | 1 |
| F | 30 | 6 | 6 | 6 | 0 | 0 |

(El puesto 1 es el que menos gana; da igual contarlos de arriba abajo o al revés mientras se haga igual en los dos lados.)

```
suma de d² = 4
rho = 1 − 6 × (suma de d²) / (n × (n² − 1))
    = 1 − 6 × 4 / (6 × 35) = 1 − 24 / 210 = 0,886
```

Los dos órdenes casi coinciden: sólo B–C y D–E se cruzan.

**Lo que hace el código** (`measure/correlation.py:18-21`): convierte cada lado en puestos y calcula la correlación de Pearson **de los puestos**. Sin empates da exactamente la fórmula de arriba; con empates (dos variantes con el mismo beneficio) les da a las dos el puesto medio, y sigue funcionando.

**Qué pasa con un punto desbocado.** Cambia sólo el OOS de F: en vez de ganar 6, pierde 20.

```
puestos OOS nuevos: A 2, B 4, C 3, D 6, E 5, F 1
d: −1, −2, 0, −2, 0, 5        suma de d² = 1 + 4 + 0 + 4 + 0 + 25 = 34
rho de Spearman = 1 − 6 × 34 / 210 = 0,03
correlación de Pearson (con los dólares) = −0,93
```

Pearson dice «relación inversa casi perfecta» por un solo punto. Spearman dice «no hay relación», que es lo que se ve: cinco variantes en orden y una que rompe. Por eso el estudio decide con Spearman y enseña Pearson sólo al lado.

**Cómo leer el tamaño.** El cuadrado del rho es, aproximadamente, la parte del orden de fuera que «explica» el orden de dentro. Un rho de 0,30 es un 9 %; uno de 0,67, un 45 %. De ahí sale la frase con que el fichero de umbrales justifica el 0,30 (para el paso 18.5, citando a éste): «por debajo de 0,30 dos rankings comparten menos del 9 % de su varianza».

### 2.3 El intervalo del rho: la transformada z de Fisher

**El problema.** Con seis puntos, un rho de 0,886 puede salir por suerte. Hace falta decir «el rho verdadero está, con un 95 % de confianza, entre tanto y tanto».

**La dificultad.** El rho no puede pasar de 1. Cerca de 1 no puede equivocarse hacia arriba, sólo hacia abajo: su error no es simétrico. El truco de Fisher es estirar la escala para que lo sea:

```
z = ½ × ln( (1 + rho) / (1 − rho) )           (en una calculadora: «atanh»)
```

En la escala z, el error es simétrico y su tamaño sólo depende del número de puntos:

```
error estándar de z = √( 1,06 / (n − 3) )
intervalo de z      = z ± 1,96 × error estándar
```

Luego se deshace el estirado (`tanh`) y se vuelve a la escala del rho.

- El **n − 3** es de la fórmula original de Fisher.
- El **1,06** es una corrección para rangos (Fieller): el rho de Spearman es un poco más ruidoso que el de Pearson, un 6 % más de varianza. El código lo aplica (`correlation.py:43`).
- El **1,96** es el de siempre: el 95 % central de una normal.

**Ejemplo a mano, las seis variantes:**

```
z = ½ × ln(1,886 / 0,114) = ½ × ln(16,5) = ½ × 2,803 = 1,402
error estándar = √(1,06 / 3) = 0,594          × 1,96 = 1,165
intervalo de z: de 1,402 − 1,165 = 0,237  a  1,402 + 1,165 = 2,567
de vuelta:      tanh(0,237) = 0,23         tanh(2,567) = 0,99
```

Con seis puntos, un rho de 0,886 es compatible con cualquier cosa entre 0,23 y 0,99.

### 2.4 La llamada: tres salidas contra un suelo

El estudio compara el intervalo entero con el suelo, 0,30 (`correlation.py:61-76`):

| el intervalo… | llamada | estado |
|---|---|---|
| queda entero por encima de 0,30 | **Fiable**: «el ranking en IS predice el de OOS» | pass |
| queda entero por debajo de 0,30 | **No fiable**: «optimizar en IS no compra nada fuera» | fail |
| cruza 0,30 | **Indeciso**: «demasiado cerca del mínimo para decidir con n puntos: hacen falta más» | watch |
| no se puede calcular (menos de 4 puntos, o todos iguales) | **Sin dato** | none |

En el ejemplo: de 0,23 a 0,99 cruza 0,30 → **Indeciso**.

Fíjate en dos cosas que la tabla no dice:

- **«No fiable» mete en el mismo saco el cero y lo negativo.** Un rho de −0,25 con intervalo de −0,36 a −0,13 (lo que da `19.2.363` contra `oos1`) no es «no hay relación»: es «lo mejor de dentro tiende a ser lo peor de fuera». La llamada es la misma que para un rho de 0,02.
- **Qué rho hace falta, en la práctica.** Con unos 300 puntos el intervalo mide ±0,10. Para «Fiable» hay que sacar más de 0,40; por debajo de 0,19 es «No fiable»; entre 0,19 y 0,40, «Indeciso».

| puntos | error en z (× 1,96) | «No fiable» si rho < | «Fiable» si rho > |
|---|---|---|---|
| 215 | 0,139 | 0,169 | 0,421 |
| 300 | 0,117 | 0,190 | 0,403 |
| 477 | 0,093 | 0,213 | 0,381 |

Los «puntos» de la fórmula son las variantes que **sobreviven** al filtro de operaciones (`correlation.py:43` usa las que quedan), no las fabricadas.

### 2.5 N efectivo: por qué 300 variantes no son 300 observaciones

**Un experimento con el ejemplo.** Coge las seis variantes y copia cada una diez veces. Tienes 60 puntos. El rho no cambia: 0,886 (copiar no desordena nada). Pero el intervalo sí:

```
error estándar = √(1,06 / 57) = 0,136          × 1,96 = 0,267
intervalo: tanh(1,402 − 0,267) = 0,81   a   tanh(1,402 + 0,267) = 0,93      → Fiable
```

De «Indeciso» a «Fiable» sin una sola observación nueva. La fórmula cree que 60 puntos son 60 informaciones; son 6.

**En los datos reales no hay copias exactas (casi), pero pasa lo mismo.** Las variantes de una madre entran en los mismos días con parámetros un poco distintos. Si un día de `oos1` fue malo, fue malo para casi todas a la vez. Sus resultados suben y bajan juntos: cada una aporta una fracción de observación, no una entera. A eso se le llama **N efectivo**: cuántas observaciones independientes harían el mismo ruido que estas 300 dependientes.

**Cómo se mide: el nulo de volteo de signos.** Es la herramienta que el propio estudio usa para la persistencia (`measure/persistence.py:43-61`); la explico aquí porque es la pieza estadística más importante del paso.

La idea: fabricar «la misma familia, pero sin ventaja». Se coge la ganancia diaria de todas las variantes en los días de fuera de muestra, y a cada **día** se le sortea un signo, +1 o −1, **el mismo para todas las variantes**. Con eso:

- cada variante gana, de media, cero (cada día tiene la misma probabilidad de sumar que de restar);
- las variantes siguen pareciéndose entre sí exactamente igual que antes (si dos entraban los mismos días, siguen ganando y perdiendo juntas).

Se repite 1.000 veces y se mira qué sale.

**Ejemplo a mano.** Tres variantes, cuatro días fuera de muestra. X es la que más arriesga, Z la que menos:

| día | X | Y | Z |
|---|---|---|---|
| 1 | +3 | +2 | +1 |
| 2 | −1 | −1 | 0 |
| 3 | +2 | +1 | +1 |
| 4 | −2 | −1 | −1 |
| **neto real** | **+2** | **+1** | **+1** |

Dentro de muestra ganaron X 9, Y 6, Z 3: el orden es X > Y > Z.

Ahora volteo signos. Tres de los 16 sorteos posibles:

```
signos (+, −, +, −):  X = 3 + 1 + 2 + 2 = +8    Y = +5    Z = +3     orden X > Y > Z    rho = +1
signos (−, +, −, +):  X = −3 − 1 − 2 − 2 = −8   Y = −5    Z = −3     orden Z > Y > X    rho = −1
signos (+, −, −, +):  X = 3 + 1 − 2 − 2 = 0     Y = +1    Z = −1     orden Y > X > Z    rho = +0,5
```

Haciendo los 16: el rho sale ±1 en seis, ±0,87 en ocho y ±0,5 en dos. **Nunca cerca de cero.** La familia no tiene ventaja ninguna, y aun así el orden de dentro o se conserva o se invierte, porque el orden lo decide quién arriesga más: cuando el periodo sale bien, el que más arriesga gana más; cuando sale mal, pierde más.

Eso es lo que la fórmula del intervalo no ve.

**Aplicado al rho de las diez madres, `build` → `oos1`** (cálculo mío, 1.000 volteos, la misma semilla que usa el estudio; **no es un hecho** y el estudio no lo hace):

| madre | puntos | error del rho que supone la fórmula | desviación del rho sin ventaja (medida) | N efectivo | sale «Fiable» sin ventaja |
|---|---|---|---|---|---|
| `10.11.484` | 317 | 0,058 | 0,23 | 20 | 4,4 % |
| `13.3.390` | 220 | 0,070 | 0,30 | 13 | 9,7 % |
| C `14.3.479` | 304 | 0,059 | 0,41 | 8 | 22,5 % |
| F `15.9.352` | 477 | 0,047 | 0,25 | 18 | 9,1 % |
| `16.5.352` | 474 | 0,047 | 0,09 | 145 | 0,0 % |
| `18.5.355` | 308 | 0,059 | 0,20 | 28 | 1,8 % |
| `19.2.363` | 259 | 0,064 | 0,26 | 17 | 6,3 % |
| E `3.11.426` | 271 | 0,063 | 0,14 | 52 | 0,0 % |
| `3.9.284` | 324 | 0,058 | 0,30 | 13 | 9,9 % |
| G `4.13.338` | 332 | 0,057 | 0,30 | 14 | 10,2 % |

El N efectivo sale de darle la vuelta a la fórmula: si el error en z es √(1,06/(N − 3)), entonces N = 3 + 1,06 / (varianza de z medida).

Ejemplo, C: la desviación de z medida es de unos 0,46 → N = 3 + 1,06 / 0,46² = 3 + 5,0 = **8**. La fórmula usa 304.

**Lectura.**

- En ocho de las diez, el rho sin ventaja baila como el de **8 a 28** observaciones independientes, no como el de 220–477. La mediana de las diez es 17. El cociente entre la desviación medida y la que supone la fórmula va de 1,8 a 7.
- **Qué es y qué no es ese «N efectivo».** No es una propiedad del lote. Depende de cuánto se alinea el orden de dentro con la exposición: entre las diez, la desviación del nulo y la correlación (en valor absoluto) entre el orden de dentro y el número de operaciones en `oos1` van juntas (≈ 0,88). En C esa correlación es −0,64; en `16.5.352`, −0,02; la excepción es `10.11.484`, con −0,11 y un nulo ancho. Además el nulo no tiene forma de campana (en C sólo el 11 % de los sorteos da un rho entre −0,1 y +0,1: es lo del ejemplo de juguete, o se conserva o se invierte), así que darle la vuelta a la fórmula de Fisher es un ajuste grueso. Léelo como **orden de magnitud**.
- «Fiable» sin ventaja: **mediana 8 %, por madre y con el orden de dentro fijo; máximo 22,5 % (C)**, con ±1,3 puntos de error de simulación. La fórmula, para una familia de rho verdadero 0 y 300 puntos, supone prácticamente un 0 % (el 2,5 % nominal sería para un rho verdadero de justo 0,30). **No es la tasa de falsos positivos del paso**: para eso habría que rehacer también el lado de dentro con una población sin ventaja (decisión 10 de 6.3).
- La misma familia sin ventaja sale «No fiable» entre el 60 % y el 99 % de las veces. Es decir: la prueba sí tiende a llamar ruido al ruido; lo que no se le puede creer es la anchura del intervalo.
- Contra este nulo, el rho real de `build` → `oos1` sólo se distingue de «sin ventaja» al 5 % en **dos** madres: `10.11.484` (p = 0,002) y C (p = 0,018), que son justo las dos «Fiable». Las tres «Indeciso» tienen p de 0,15, 0,14 y 0,09. Son diez contrastes sin corregir: exigiendo 0,005 a cada uno (Bonferroni) sólo queda `10.11.484`.

**Tres límites de esta medida, para no leerle más de lo que da.** (1) El principal: lo que mide es la alineación entre el orden de dentro y la exposición (quién opera más); atribuye a «la familia» cualquier orden que venga de ahí, igual que avisa la ficha de la persistencia. (2) Es la distribución del rho **si no hubiera ventaja**, no el error alrededor del rho real. (3) Sólo voltea el lado de fuera; el de dentro se deja fijo.

### 2.6 La persistencia del top, desde cero

**La pregunta.** Más directa que el rho: de las variantes que estaban entre las mejores dentro, ¿cuántas siguen en la mitad buena fuera?

**La definición** (`measure/persistence.py:22-23`, con `top: 0.20` y `keep: 0.50` de `config.yaml:14-16`):

```
top       = variantes cuyo neto dentro es mayor o igual que el percentil 80 de dentro
persisten = las del top cuyo neto fuera es mayor o igual que la mediana de fuera
persistencia = persisten / top
exceso       = persistencia − 0,50
```

**Por qué se resta 0,50.** Si el orden de dentro no tuviera nada que ver con el de fuera, las del top caerían al azar fuera: la mitad en la mitad buena, la mitad en la mala. Una persistencia del 50 % es **no saber nada**, no «la mitad de bueno». Por eso el hecho es el exceso.

**Ejemplo a mano.** Diez variantes, numeradas por su puesto dentro (10 = la mejor). Sus beneficios fuera, en el mismo orden: 3, 8, 9, 1, 7, 2, 6, 10, 5, 4.

```
percentil 80 de dentro = 8,2     → top: las dos primeras (10 y 9)
sus beneficios fuera: 3 y 8
mediana de fuera = 5,5           → 8 se queda, 3 no
persistencia = 1 / 2 = 50 %      exceso = 0
```

**Cuánto baila por azar: dos respuestas muy distintas.**

- *Si las variantes fueran independientes* (la cuenta «de urna»: saco 61 bolas de 304, la mitad son buenas): la desviación de la persistencia sería √(0,25/61 × (304 − 61)/303) = 0,057, y el 90 % de las veces el exceso quedaría entre −0,09 y +0,09.
- *Con el nulo de volteo de signos* (las variantes tan dependientes como son): para esa misma madre, C, el 90 % queda entre **−0,30 y +0,32**. Tres veces más ancho.

La ficha `knowhow/research/wfc-top-persistence-sign-flip-null.md` lo resume: ±0,27 contra ±0,09, «nunca leas el exceso contra N variantes».

**Qué dice y qué no.** Igual que el rho, es una medida de **orden**. La ficha lo pone con un caso de esta corrida: `13.3.390` da +0,34 de exceso y un ratio de Sharpe mediano de −0,22: «el ranking del build se mantuvo mientras la familia entera perdía».

### 2.7 El ratio de Sharpe fuera/dentro

**La pregunta.** Variante a variante, ¿cuánto del rendimiento de dentro queda fuera?

```
ratio de una variante = Sharpe fuera / Sharpe dentro
hecho = mediana de los ratios, sólo sobre las variantes con Sharpe dentro > 0,1
```

(`measure/persistence.py:39-40`, `sharpe_floor: 0.1` en `config.yaml:10`. Si entran menos de cinco variantes, no hay dato.)

Tres cosas para leerlo:

- **Es una mediana de ratios, no un ratio de medianas.** Se calcula el cociente de cada variante y luego se toma el de en medio. Nunca se promedian: un Sharpe de dentro cercano a cero hace un cociente enorme, y una media se lo tragaría.
- **Por debajo de 1 no significa que decaiga.** Sólo entran las variantes con Sharpe de dentro alto, y una variante que entra por tener un valor alto tiende, por sí sola, a tener un valor más normal la vez siguiente (regresión a la media). Sin decaimiento alguno, la mediana queda algo por debajo de 1. Lo dice el código (`persistence.py:36-37`).
- **Un solo camino de precios.** Si los días de fuera fueron malos, lo fueron para todas las variantes: el ratio de todas baja a la vez. Con el nulo de volteo, una familia sin ventaja da una mediana entre −1,2 y +1,2. Ese rango cubre casi cualquier valor real. Por eso el estudio lo titula «diagnóstico, no criterio» y no lo ofrece.

### 2.8 Pearson y la pendiente: lo que se enseña y no decide

La tabla «Correlaciones por partición» lleva, junto al Spearman:

- **Pearson**: la correlación con los dólares. Sensible a un punto suelto (2.2).
- **Pendiente**: la recta de mínimos cuadrados del neto de fuera sobre el de dentro. «Por cada dólar más que ganó una variante dentro, cuántos más ganó fuera». Depende de la longitud de las ventanas (8 años contra 4): una pendiente de 0,5 con `build` → `oos1` es, por año, 1.

Ninguna entra en el veredicto.

### 2.9 Qué tiene de dato nuevo este paso, y qué no

La idea central del Council (informe del 2026-10-06, que cito; no lo he contrastado con las actas): sólo una prueba que lee datos nuevos puede dar un PASA con contenido, y el WFC está en la lista de las que «releen las mismas operaciones».

Con matices según la composición:

- **`build` → `oos1`.** En una corrida normal, la madre llega aquí porque pasó el paso 8, que la eligió mirando `oos1`. Eso sesga el nivel de la nube y también, **al alza, el rho y la persistencia**: la nube está centrada en la madre; la Vecindad y las copias heredan su `oos1` alto y, por la optimización, un `build` alto, y la Cobertura no. Sale un gradiente en los dos ejes que no es información de la superficie, y el nulo de volteo no lo ve. Es un sesgo mecánico al alza; su magnitud **no está medida**. El indicio de 1.6 (la madre sobre la mediana de `oos1` de su nube en 9 de 10) apunta a que pasa incluso en estas diez.
- **`build+oos1` → `oos2`.** Aquí sí hay un tramo que nadie ha usado para elegir. Pero es **un** tramo de 2,75 años, un solo camino de precios, y todas las variantes lo recorren juntas: la dependencia de 2.5.
- **El trader al azar y el nulo.** El nulo de este paso voltea sólo los días de **fuera** de muestra. No hay ninguna lectura contra el azar sobre el IS. Eso respeta tu doctrina.

---

## 3. Lo que calcula el estudio, pieza a pieza

Para cada pieza: qué mide, la fórmula con su `fichero:línea`, un ejemplo real recalculado y cómo leerlo. Los ejemplos son de `build` → `oos1` salvo que diga otra cosa.

### 3.1 Los puntos utilizables

- *Qué son:* las variantes que entran en la nube.
- *Cómo se eligen* (`engines/variants/panel.py:90-92`): las que tienen neto en los dos lados y **al menos 50 operaciones en el lado de dentro y al menos 50 en el de fuera** (`engines/variants/config.yaml:19`). Es el segundo suelo; el primero (100 en total) ya actuó en la cosecha.
- *No se mira el estrato:* el original, los canarios y los pares inertes entran como un punto más.

| | C | E | F | G | las diez |
|---|---|---|---|---|---|
| en `metrics.parquet` | 417 | 429 | 501 | 460 | 276–501 |
| con menos de 50 operaciones en `build` | 5 | 17 | 0 | 37 | 0–37 |
| con menos de 50 en `oos1` | 113 | 158 | 24 | 128 | 24–158 |
| **usadas** | **304** | **271** | **477** | **332** | 220–477 |

*Cómo leerlo.* El suelo de fuera es el que manda: 4 años a 50 operaciones son 12,5 al año, y aun así se lleva hasta el 37 % del lote (E). Las que se van no son al azar: son las variantes que operan poco, es decir, una región concreta del espacio de parámetros.

*Dos cosas medidas por mí:*

- **Duplicados exactos** (mismo neto dentro y fuera, al céntimo): G tiene 203 puntos distintos de 332; C, 234 de 304; `10.11.484`, 270 de 317. Vienen de mover parámetros que no cambian ninguna operación.
- **Copias del original:** F tiene 9 puntos idénticos al original entre sus 10 canarios (son sus «pares inertes», uno por parámetro congelado); C y E, 4.

### 3.2 El rho

Clave en `wfc.json`: `rho`. En la pestaña: columna «Spearman» de «Correlaciones por partición».

- *Fórmula:* correlación de Pearson de los puestos (`measure/correlation.py:18-21`, llamada en `:38`). Explicada en 2.2.
- *Ejemplo real, C:* 304 puntos. Recalculado: **0,6676**. Guardado en la tabla: 0,668 ✓.

Las diez, recalculadas, con el reparto de la nube en cuadrantes (ganan dentro y fuera / sólo dentro / sólo fuera / ninguno):

| madre | puntos | rho | ++ | +− | −+ | −− |
|---|---|---|---|---|---|---|
| `10.11.484` | 317 | 0,576 | 278 | 8 | 3 | 28 |
| `13.3.390` | 220 | 0,345 | 84 | 134 | 0 | 2 |
| C `14.3.479` | 304 | 0,668 | 191 | 32 | 23 | 58 |
| F `15.9.352` | 477 | 0,317 | 97 | 46 | 95 | 239 |
| `16.5.352` | 474 | 0,099 | 239 | 139 | 35 | 61 |
| `18.5.355` | 308 | 0,290 | 247 | 55 | 3 | 3 |
| `19.2.363` | 259 | −0,246 | 37 | 91 | 72 | 59 |
| E `3.11.426` | 271 | −0,203 | 242 | 19 | 10 | 0 |
| `3.9.284` | 324 | 0,024 | 240 | 39 | 35 | 10 |
| G `4.13.338` | 332 | 0,009 | 324 | 7 | 1 | 0 |

*Cómo leerlo.* Mira las dos columnas a la vez. G: 324 de 332 variantes ganan en los dos lados, y el rho es 0,01. E: 242 de 271, y el rho es negativo. `13.3.390`: 134 de 220 ganan dentro y pierden fuera, y el rho es +0,35. **El rho no sabe en qué cuadrante está la nube; sólo si está inclinada.**

*El rho depende de cómo se fabricó el lote.* Calculado por estrato (mío; no es un hecho):

| | Factorial | Cobertura | Vecindad | todos juntos |
|---|---|---|---|---|
| C | 0,83 | 0,39 | 0,12 | 0,67 |
| `10.11.484` | 0,73 | 0,09 | 0,59 | 0,58 |
| F | 0,06 | 0,37 | −0,22 | 0,32 |

En C, el 0,67 lo hace sobre todo el estrato factorial. El 0,12 de la Vecindad **no es concluyente**: son 91 puntos (±0,22 de intervalo nominal) y su rango de beneficio dentro es 4,7 veces más estrecho que el de la nube entera (desviación de 2.761 USD frente a 12.913), y un rango estrecho rebaja el rho por sí solo; en `10.11.484` la Vecindad da 0,59. Lo que sí se ve: con otro reparto de estratos, otro rho. Cuánto, en general, **no está medido**.

### 3.3 El intervalo

Clave: `ci95` (dos números).

- *Fórmula* (`measure/correlation.py:42-45`): la de 2.3. Si hay menos de 4 puntos o el rho no se puede calcular, no hay intervalo (`:39-41`).
- *Ejemplo real, C, a mano:*

```
z = ½ × ln(1,6676 / 0,3324) = ½ × ln(5,017) = 0,8064
error estándar = √(1,06 / 301) = 0,0593        × 1,96 = 0,1163
intervalo: tanh(0,6901) = 0,598    a    tanh(0,9227) = 0,727
```

- *Comprobación sobre la composición pedida, `10.11.484`:* rho 0,4453, 321 puntos → z = 0,4788, ± 0,1132 → de 0,350 a 0,531. Guardado: 0,3502 y 0,5313 ✓.
- *Cómo leerlo:* como si las variantes fueran independientes. No lo son: en C, la desviación del rho sin ventaja medida en 2.5 es unas siete veces la que supone la fórmula. El intervalo **no es un hecho** en ninguna parte: sólo vive en `wfc.json`.

### 3.4 Pearson y pendiente

- *Fórmulas:* Pearson con los dólares (`correlation.py:46`); pendiente por mínimos cuadrados (`contract/wfc.py:68-69`).
- *Ejemplo real, C:* Pearson 0,718, pendiente 0,252 (por cada 1.000 USD más dentro, 252 más fuera; en 4 años contra 8,3). Guardado: 0,718 y 0,252 ✓.
- *Cómo leerlo:* contexto. `19.2.363` en la composición pedida enseña para qué sirve tener los dos: Spearman 0,20 y Pearson 0,44. Unos pocos puntos extremos tiran del Pearson.

### 3.5 La llamada

Claves: `call`, `why`.

- *Regla* (`correlation.py:61-76`): la tabla de 2.4, con `rho_floor` de `config.yaml:6`.
- *Ejemplos reales:* C, de 0,598 a 0,727 → entero por encima de 0,30 → **Fiable**. F, rho 0,317, 477 puntos → de 0,231 a 0,398 → cruza → **Indeciso**. G, de −0,102 a 0,120 → **No fiable**.

Las diez, en las cuatro particiones (F = Fiable, I = Indeciso, N = No fiable; `build` → `oos1` recalculada, las otras tres deducidas del rho y los puntos que guardó el estudio):

| madre | `build`→`oos1` | `build`→`oos2` | `build`→`oos1+oos2` | `build+oos1`→`oos2` (pedida) |
|---|---|---|---|---|
| `10.11.484` | 0,58 F | 0,25 I | 0,52 F | 0,45 **F** |
| `13.3.390` | 0,35 I | −0,17 N | 0,18 I | −0,16 **N** |
| C `14.3.479` | 0,67 F | −0,05 N | 0,59 F | 0,00 **N** |
| F `15.9.352` | 0,32 I | −0,28 N | 0,19 N | −0,22 **N** |
| `16.5.352` | 0,10 N | −0,04 N | 0,03 N | 0,04 **N** |
| `18.5.355` | 0,29 I | 0,02 N | 0,31 I | 0,11 **N** |
| `19.2.363` | −0,25 N | 0,35 I | 0,16 N | 0,20 **I** |
| E `3.11.426` | −0,20 N | 0,06 N | −0,13 N | 0,07 **N** |
| `3.9.284` | 0,02 N | 0,58 F | 0,50 F | 0,54 **F** |
| G `4.13.338` | 0,01 N | 0,36 I | 0,36 I | 0,40 **F** |
| **F / I / N** | 2 / 3 / 5 | 1 / 3 / 6 | 3 / 3 / 4 | 3 / 1 / 6 |

*Cómo leerlo.* Lee por filas. Sólo `10.11.484` no falla en ninguna. Dos fallan en las cuatro (`16.5.352` y E). Las demás dependen de la columna: C y `3.9.284` son casi imágenes en espejo. Entre las diez, la correlación de rangos entre la primera columna y la segunda es **−0,60**, con intervalo de −0,90 a +0,07. Ese intervalo es optimista (las diez comparten plantilla, mercado, ventanas y `build`): el signo no se puede afirmar; que una columna no confirma a la otra, sí.

### 3.6 La persistencia del top y su exceso

Hechos: `wfc.summary.exceso_persistencia_oos1`, `wfc.summary.exceso_persistencia_oos2`, `wfc.summary.exceso_persistencia_minimo`.

- *Fórmula* (`measure/persistence.py:22-23`): la de 2.6. Siempre con `build` dentro y **una** ventana fuera cada vez (`report.py:124`): `oos1` sola y `oos2` sola. `_minimo` es el menor de los dos (`contract/criteria.py:35-37`).
- *Ejemplo real, C, `oos1`, a mano:*

```
304 variantes. Percentil 80 del neto en build = 14.554 USD   → 61 variantes en el top
mediana del neto en oos1 = 2.897 USD
de las 61, tienen oos1 ≥ 2.897:  54
persistencia = 54 / 61 = 88,5 %        exceso = 0,885 − 0,50 = +0,385
```

Guardado: 0,3852 ✓.

- *Un matiz de la definición:* el top es «mayor o igual que el percentil 80», así que con empates no es exactamente el 20 %. En G entran 81 de 332 (24 %); en F, 101 de 477 (21 %), porque el percentil 80 de F cae justo en el neto del original, que está repetido.

Las diez (el exceso de `oos1`, recalculado; el de `oos2` y el rango de su nulo, escritos por el estudio):

| madre | exceso `oos1` | nulo `oos1` (p5 a p95) | exceso `oos2` | nulo `oos2` (p5 a p95) | `_minimo` |
|---|---|---|---|---|---|
| `10.11.484` | **+0,328** | −0,27 a +0,27 | +0,208 | −0,24 a +0,22 | +0,208 |
| `13.3.390` | **+0,341** | −0,32 a +0,32 | −0,035 | −0,34 a +0,34 | −0,035 |
| C `14.3.479` | **+0,385** | −0,30 a +0,32 | +0,238 | −0,25 a +0,27 | +0,238 |
| F `15.9.352` | **+0,351** | −0,32 a +0,34 | −0,360 | −0,36 a +0,36 | −0,360 |
| `16.5.352` | −0,089 | −0,17 a +0,16 | −0,011 | −0,18 a +0,19 | −0,089 |
| `18.5.355` | +0,065 | −0,23 a +0,23 | −0,160 | −0,22 a +0,22 | −0,160 |
| `19.2.363` | −0,096 | −0,25 a +0,25 | +0,120 | −0,20 a +0,22 | −0,096 |
| E `3.11.426` | −0,161 | −0,18 a +0,18 | +0,161 | −0,18 a +0,20 | −0,161 |
| `3.9.284` | −0,023 | −0,32 a +0,30 | **+0,379** | −0,30 a +0,32 | −0,023 |
| G `4.13.338` | +0,105 | −0,22 a +0,30 | **+0,374** | −0,32 a +0,33 | +0,105 |

En negrita, los que superan el p95 de su propio nulo.

*Cómo leerlo.*

- En `oos1`, 4 de 10 salen del nulo (se esperaría 0,5 por azar). En `oos2`, 2 de 10. **Ninguna en las dos ventanas.** Las cuatro de `oos1` dan en `oos2` +0,21, −0,03, +0,24 y −0,36.
- F es el caso extremo: +0,35 en `oos1` (fuera del nulo por arriba) y −0,36 en `oos2` (en el borde del nulo por abajo: su top del `build` cayó casi entero en la mitad mala).
- `_minimo` es positivo en 3 de 10, y en ninguna supera el p95 del nulo de la ventana que lo fija.
- Entre las diez, la correlación de rangos entre el exceso de `oos1` y el de `oos2` es −0,10.

*Una lectura más directa, que no es un hecho* (calculada por mí, `oos1`): la mediana de lo que ganaron fuera las del top, frente a la de todas.

| | top del `build`: mediana en `oos1` | todas: mediana en `oos1` |
|---|---|---|
| `10.11.484` | 21.184 | 11.724 |
| C | 4.245 | 2.897 |
| F | 5.626 | −3.833 |
| `16.5.352` | 142 | 2.192 |
| E | 7.483 | 9.076 |
| G | 19.572 | 12.219 |

### 3.7 El nulo sin ventaja

En la pestaña: columnas «Exceso sin ventaja» y «Mediana sin ventaja». **No es un hecho**: en la tabla va como texto (5.7).

- *Cómo se fabrica* (`measure/persistence.py:57-61` y `:82-89`): 1.000 sorteos (`DRAWS`), semilla fija 17 (`SEED`). En cada uno, cada día de fuera de muestra recibe un signo al azar, el mismo para todas las variantes. De cada sorteo se saca el neto de cada variante (suma de los días) y su Sharpe (media diaria entre desviación diaria, por √252). Con el neto se recalcula el exceso de persistencia; con el Sharpe, la mediana del ratio. Se guardan los percentiles 5, 25, 50, 75 y 95 de los 1.000.
- *Qué días son «de fuera»* (`report.py:50-57`): los que caen entre el inicio declarado del tramo y el inicio del siguiente. Para `oos1`, del 2020-01-01 al 2023-12-31: 1.033 días de curva.
- *Ejemplo real, C, `oos1`:* percentiles 5 / 25 / 50 / 75 / 95 del exceso sin ventaja: −0,30 / −0,12 / +0,01 / +0,12 / +0,32. El real, +0,385, queda fuera. Con mis 1.000 volteos, sólo el 1,7 % de los sorteos lo iguala.
- *Cómo leerlo:* si el valor real cae dentro del rango, «no se distingue de no tener ventaja». El rango cambia mucho de una madre a otra: de ±0,17 (`16.5.352`) a ±0,34 (F). La ayuda de la ventana da un rango fijo, «entre −0,27 y +0,29», que es la mediana de las diez (5.13).

### 3.8 La mediana del ratio de Sharpe

Hecho: `wfc.summary.mediana_ratio_Sharpe`. **Es el de la composición pedida** (`report.py:138`, `contract/criteria.py:37`), no el de `build` → `oos1`.

- *Fórmula* (`measure/persistence.py:39-40`): la de 2.7.
- *Ejemplo real, C, `build` → `oos1`:* de 304 variantes, 214 tienen Sharpe en `build` mayor que 0,1. La mediana de sus cocientes: **0,49**. Guardado en la tabla: «214 de 304», 0,49 ✓. Nulo: de −1,18 a +1,16.
- *F:* sólo entran 86 de 477. El hecho describe al 18 % de la familia que tenía Sharpe positivo dentro.

| | `build`→`oos1` (variantes, mediana, nulo) | pedida (variantes, mediana, nulo) |
|---|---|---|
| C | 214 de 304 · 0,49 · −1,18 a 1,16 | 220 de 317 · 0,15 · −1,83 a 1,85 |
| E | 250 de 271 · 0,89 · −1,01 a 1,04 | 263 de 273 · **1,92** · −1,62 a 1,53 |
| F | 86 de 477 · 0,80 · −3,09 a 3,05 | 95 de 430 · −2,12 · −4,61 a 4,62 |
| G | 328 de 332 · 0,74 · −0,92 a 1,04 | 416 de 417 · 1,15 · −1,54 a 1,54 |

*Cómo leerlo.* De estas cuatro, sólo E en la composición pedida sale de su nulo. Entre las diez salen dos en la pedida (E y `3.9.284`, con 1,53 frente a un p95 de 1,35) y una contra `oos1` (`10.11.484`, con 1,69 frente a 1,38). En el resto, el valor real está dentro de lo que da una familia sin ventaja. Es lo que dice la ficha: 1 de 10, diagnóstico.

### 3.9 El resumen (`summary`)

Lo que el resultado ofrece como campos planos (`contract/criteria.py:35-37`):

| campo | qué es | de qué ventanas |
|---|---|---|
| `exceso_persistencia_oos1` | 3.6 | `build` → `oos1` |
| `exceso_persistencia_oos2` | 3.6 | `build` → `oos2` |
| `exceso_persistencia_minimo` | el menor de los anteriores | las dos |
| `mediana_ratio_Sharpe` | 3.8 | **la composición pedida** |

Si la puerta del ledger no deja leer `oos2` (un agente autónomo), `exceso_persistencia_oos2` no existe y `_minimo` vale lo mismo que `_oos1`. El mismo nombre significa dos cosas según quién lanza.

### 3.10 La tarjeta del veredicto

- *Qué lleva* (`contract/wfc.py:55-61`): la etiqueta («Fiable»…), el estado, la frase, y como «puntuación» el texto `Spearman 44,53 %`, que es el rho multiplicado por 100.
- *Cómo leerlo:* **no es un porcentaje de nada.** Un rho de 0,45 no quiere decir «acierta el 45 %»; lo que comparten los dos órdenes es rho², un 20 %. Y al ser texto, no llega a los hechos (3.14).

### 3.11 El `wfc.json` de la raíz del lote

El que leía la tubería antigua (`report.py:147-151`). Campos: `n`, `rho`, `ci95`, `pearson`, `call`, `why`, `dropped` (fuera por el suelo de 50 por lado), `dropped_thin` (fuera por el suelo de 100 en total), `composition`, `in_sample`, `out_of_sample`. Ejemplo, `10.11.484`: 321, 0,4453, [0,350; 0,531], 0,389, «fiable», 99, 80, `build+oos1__oos2`.

### 3.12 Lo que hay en la pestaña

Por cada partición (se elige con un selector):

- una línea «N combinaciones medidas · M descartadas por operar poco · K usadas»;
- **la nube**, con los cuadrantes, la recta ajustada y los puntos coloreados por estrato. La «r» de la recta es el Pearson, no el Spearman (`contract/wfc.py:147`);
- el histograma del ratio de Sharpe por variante, con la mediana marcada;
- los Sharpe de dentro y de fuera superpuestos;
- si la llamada es «No fiable», un aviso en rojo.

Y, comunes a todas: las dos tablas «Métricas para criterios — sin umbral todavía» (3.6 y 3.8), la tabla «Correlaciones por partición» y la lista de estratos.

### 3.13 El renglón del ledger

Un renglón por tramo leído de la composición pedida (`report.py:152-157`): paso 17, `criterion: wfc/<composición>`, los umbrales `rho_floor` y `min_trades`, y una nota con la llamada y el rho. No retira a nadie (`n_out` = `n_in`).

### 3.14 Los hechos: lo que saldría, y lo que sale

**Lo que sale hoy: nada.** `python3 -m pipeline.autopilot.facts --project … --step 17` devuelve cero claves. Lo he ejecutado en memoria (`facts.gather`): 0 filas. La razón está en 5.6.

**Lo que saldría si el extractor leyera el resultado** (he pasado `estudios/wfc.json` de `10.11.484` por `facts.flatten`): 44 claves.

| grupo | claves | qué son de verdad |
|---|---|---|
| `wfc.summary.*` | 4 | los de 3.9 |
| `wfc.verdict.pass` | 1 | 1 si «Fiable» |
| `wfc.cloud.ratio_sharpe_oos_is_por_variante.*` | 11 | percentiles del ratio por variante, composición pedida; `.real` vale **siempre 1,0** |
| `wfc.cloud.sharpe_is_y_oos_superpuestos.*` | 10 | percentiles de los Sharpe de dentro y de fuera **mezclados en un montón** |
| `wfc.cloud.metricas_…persistencia_del_top.<ventana>.variantes` | 2 | cuántas variantes; lo demás de la tabla es texto y se pierde |
| `wfc.cloud.correlaciones_por_particion.<partición>.*` | 16 | puntos, Spearman, Pearson y pendiente de las cuatro particiones |

Lo que **no** saldría ni así: el rho con todos sus decimales (la puntuación es texto), el intervalo, los percentiles del nulo y la llamada de las particiones no pedidas. Detalles en 5.7.

---

## 4. El criterio cargado y por qué

### 4.1 Tal como está hoy en disco

**`pipeline/autopilot/criteria.yaml`**: no hay entrada `"17"`. La única mención es el comentario de la línea 59: «Steps 17, 18, 19, 21, 23, 24 annotate only: no rule on purpose». El modo de desarrollo (`dev.on: true`) sólo sortea en el paso 8. No hay línea `frozen`.

| regla | Pasa | Limbo | Falla |
|---|---|---|---|
| (ninguna) | — | — | — |

**`pipeline/autopilot/offered.yaml:8-14`**: dos hechos ofrecidos para un criterio que no has puesto.

| hecho | nombre en la ventana | umbral |
|---|---|---|
| `wfc.summary.exceso_persistencia_minimo` | «WFC · exceso de persistencia del top, peor ventana» | vacío |
| `wfc.summary.exceso_persistencia_oos1` | «WFC · exceso de persistencia del top en OOS1» | vacío |

**Los ajustes del estudio**, que sí llevan umbrales:

| ajuste | valor | dónde | qué hace |
|---|---|---|---|
| `rho_floor` | 0,30 | `studies/optimisation/wfc/config.yaml:6` | el suelo del veredicto propio |
| `min_trades` | 50 | `engines/variants/config.yaml:19` | operaciones mínimas por lado |
| `split_mode` | `oos2_only` | `engines/variants/config.yaml:46` | la composición por defecto |
| `persistence.top` / `keep` | 0,20 / 0,50 | `wfc/config.yaml:14-16` | la definición de la persistencia |
| `sharpe_floor` | 0,1 | `wfc/config.yaml:10` | quién entra en el ratio |
| `wfc.min_trades_total` | 100 | `assets/_build.yaml:368` | el suelo duro de la cosecha |

**El paso 20**: `joint.pieces: sin_fallo` (`studies/closing/blindJoint/config.yaml:26`, tuyo, 2026-10-04). Con `sin_fallo`, un «No fiable» marca DESCARTAR en el `verdict.csv` del paso 20 (6 de 10 aquí; cadena `contract/wfc.py:12` → `blindJoint/readings.py:14` → `blindJoint/report.py:64`), pero el autopiloto no lo aplica: `criteria.yaml` sólo tiene los pasos 8, 10, 11.5, 12, 14 y 16, el juez devuelve «ninguno» (`judge.py:172-173`), el 20 no tiene `cut` y todas las supervivientes siguen. Sólo corta si se aplica a mano con `/curate`.

**La tubería antigua** (`pipeline/config.yaml:51-53`) conserva otra regla distinta: `wfc.rho` mínimo 0,30 sobre el **valor**, no sobre el intervalo. Su receta lanza el estudio sin `--family`, que ahora es obligatorio (`pipeline/recipe.yaml:141`, `report.py:72`), así que tal como está escrita no arranca.

**La razón de que no haya regla** (informe del 2026-10-06, que cito): el Council dejó de 16 a 19 en «sólo anota» porque releen las mismas operaciones, y no hay ninguna tasa de falsos positivos medida. Del suelo de 0,30 dijo que no lo tocaba, pero que es más estricto que cualquier persistencia observada (0,06 medida en la población entre `oos1` y `oos2`; 0,15 en Katz). Dos avisos sobre esas cifras: el 0,06 existe (`knowhow/research/oos1-oos2-persistence.md:6`) pero es otra cosa —Sharpe por operación entre estrategias **distintas**, no el orden de las variantes de una madre—, y el propio informe lo advierte (`criterios-pasos-6-a-19-explicados-2026-10-06.md:518`); el 0,15 de Katz no tiene fuente primaria localizada. Se propuso bajarlo a 0,15 y se retiró: sin una población nula, cualquier línea es una convención.

### 4.2 Qué haría falta para poder escribir una regla

No propongo ninguna. Esto es la lista de lo que falta para que una regla, la que tú elijas, funcione:

| qué falta | estado |
|---|---|
| que los hechos del paso 17 lleguen al juez | **No.** El extractor devuelve cero (5.6) |
| que el paso 17 se juzgue en la cola del autopiloto | **No.** Corre a ciegas con 18 y 18.5 (5.6) |
| un databank que cortar (`cut`) | No está decidido. Una entrada con reglas y sin `cut` para la corrida (`judge.py`) |
| elegir la composición que se juzga | Hoy es la que toca `oos2` |
| el rho y su intervalo como hechos | No. Sólo el rho redondeado, dentro de una tabla |
| el rango del nulo como hecho | No. Es texto en una tabla |
| una tasa de falsos positivos | No medida para el veredicto. Para la persistencia, la ficha da los cuantiles del nulo |
| que apuntar el umbral conste como mirada | La ficha lo pide: «el día que se ponga un umbral sobre el exceso, apúntalo en el ledger como una mirada del paso 17» |

### 4.3 Cuántas fallaría cada regla posible, sobre la población real

Ninguna está cargada. Las cuentas son mías, sobre las diez. Las que usan `oos2` salen de lo que el estudio escribió.

**Con el veredicto propio**

| regla candidata | fallan | quiénes |
|---|---|---|
| «No fiable» es Falla, composición pedida (lo que hoy marca el `verdict.csv` del paso 20, sin cortar) | 6 | `13.3.390`, C, F, `16.5.352`, `18.5.355`, E |
| lo mismo con `build` → `oos1` | 5 | `16.5.352`, `19.2.363`, E, `3.9.284`, G |
| «No fiable» en las dos | 2 | `16.5.352`, E |
| «No fiable» en alguna de las dos | 9 | todas menos `10.11.484` |
| sólo «Fiable» pasa, composición pedida | 7 | todas menos `10.11.484`, `3.9.284`, G |
| sólo «Fiable» pasa, `build` → `oos1` | 8 | todas menos `10.11.484`, C |
| rho ≥ 0,30 sin intervalo (la regla antigua), pedida | 7 | todas menos `10.11.484`, `3.9.284`, G |
| rho ≥ 0,30 sin intervalo, `build` → `oos1` | 6 | pasan `10.11.484`, `13.3.390`, C, F (`18.5.355` se queda en 0,290) |

**Con la persistencia**

| regla candidata | fallan | quiénes pasan |
|---|---|---|
| `exceso_persistencia_minimo` ≥ 0 | 7 | `10.11.484`, C, G |
| `exceso_persistencia_oos1` ≥ 0 | 4 | `10.11.484`, `13.3.390`, C, F, `18.5.355`, G |
| `exceso_persistencia_oos1` ≥ 0,27 (el p95 «de ficha») | 6 | `10.11.484`, `13.3.390`, C, F |
| `exceso_persistencia_oos1` por encima del p95 de **su** nulo | 6 | las mismas cuatro (no expresable hoy: el p95 no es un hecho) |
| `exceso_persistencia_minimo` ≥ 0,27 | 10 | ninguna |
| `mediana_ratio_Sharpe` ≥ 0,5 (pedida) | 5 | `10.11.484`, `13.3.390`, E, `3.9.284`, G |

Lo que se ve:

- **Elegir ventana es elegir a quién se descarta.** Los seis que fallan con la composición pedida y los cinco que fallan con `build` → `oos1` sólo tienen dos en común.
- **Las cuatro que pasan la persistencia en `oos1` con margen** incluyen a F, la peor familia de las diez por nivel (239 de 477 variantes pierden en los dos lados), y a `13.3.390`, que pierde fuera en la mediana.
- **La regla «peor ventana» con el umbral del nulo no la pasa nadie.**

### 4.4 Cómo sería el resultado ideal

- **No existe un resultado ideal certificable en este paso.** Como referencia, no como umbral:
- **El mismo signo y la misma llamada en las cuatro particiones.** En las diez sólo lo roza `10.11.484` (F, I, F, F).
- **Un rho que se distinga de «sin ventaja» con un nulo que respete la dependencia**, no con el intervalo de la fórmula. Contra `oos1` lo cumplen dos de diez.
- **Exceso de persistencia fuera de su nulo en las dos ventanas.** Ninguna de las diez. `10.11.484` es la más cercana: +0,328 (fuera del nulo) y +0,208 (dentro, con el p95 en +0,22).
- **La nube en el cuadrante bueno.** Esto no lo mide ningún número del estudio; se ve en la figura, y en la tabla de 3.2.

**El techo honrado.** Ni el mejor WFC posible prueba ventaja. Dice «en esta familia, en este tramo, lo que iba mejor dentro siguió yendo mejor fuera». `10.11.484` es la que mejor sale aquí y el paso 20 la descartó igualmente.

### 4.5 Si mueves un umbral

**El suelo del rho** (`rho_floor`). Reparto Fiable / Indeciso / No fiable entre las diez:

| suelo | composición pedida | `build` → `oos1` |
|---|---|---|
| 0,30 (hoy) | 3 / 1 / 6 | 2 / 3 / 5 |
| 0,15 | 3 / 3 / 4 | 5 / 1 / 4 |
| 0 | 4 / 4 / 2 | 6 / 2 / 2 |

Bajar el suelo a 0,15 no añade ningún «Fiable» en la composición pedida: saca de «No fiable» a dos (`18.5.355` y E pasan a «Indeciso»). Con `sin_fallo` en el paso 20, eso es **6 marcadas DESCARTAR → 4** (marcadas, no cortadas).

**El suelo de operaciones por lado** (`min_trades`). Con 30 en vez de 50, `build` → `oos1`:

- entran más puntos (en G, de 332 a 424);
- nueve llamadas no cambian;
- G pasa de rho 0,009 «No fiable» a 0,283 «Indeciso», con 424 puntos en vez de 332. `3.9.284` pasa de 0,02 a 0,14.

Un suelo que mueve el rho de 0,01 a 0,28 en una madre no es un detalle de limpieza: decide el resultado.

**Quitar duplicados y controles.** El rho casi no se mueve (lo máximo, `10.11.484`: de 0,576 a 0,557). Lo que cambia es el N del intervalo: G pasaría de 332 a 203. Ninguna llamada cambia en `build` → `oos1`.

**Más estricto** (suelo más alto, exigir «Fiable») descarta más familias cuyo orden no se mantiene, y también más familias que ganan enteras sin que el orden importe (E, G contra `oos1`). **Más laxo** deja pasar casi todo. Lo que ninguna opción da es una probabilidad: la única tasa medida aquí es la mía de 2.5, con un nulo y una ventana.

---

## 5. Lo que no cuadra o no está medido

### 5.1 El README y la nota de la figura describen cuadrantes; el número mide inclinación

`studies/optimisation/wfc/README.md:6-9` y la nota de la nube (`contract/wfc.py:148-150`): «una nube que llena los cuatro cuadrantes: optimizar dentro no compra nada fuera; una nube sobre la diagonal ascendente…». El rho de Spearman no sabe de cuadrantes. G está entera en el cuadrante bueno (324 de 332) con rho 0,01; `13.3.390` tiene 134 de 220 en «gana dentro, pierde fuera» con rho +0,35.

### 5.2 «Con una docena de tuplas» e «Indeciso es el caso habitual»

`README.md:42-44` y `measure/correlation.py:33-35` y `:57-59` hablan de «una docena de puntos» y de que la salida intermedia «es la común». El estudio corre hoy con 215 a 477 puntos, el intervalo mide ±0,10, e «Indeciso» sale en 1 de 10. El remedio que da el texto del veredicto —«hacen falta más»— afina el rho de este camino de precios pero no añade caminos: con la mitad de las variantes de C la desviación del nulo no cambia (0,41 → 0,43).

### 5.3 El intervalo supone independencia

Apartado 2.5. El comentario del código lo llama «la lectura honrada» (`correlation.py:34-35`). Medido por mí contra `oos1`: la desviación del rho sin ventaja es de 1,8 a 7 veces la que supone la fórmula; como «N efectivo», de 8 a 145 (mediana 17) donde la fórmula usa 220 a 477. Es un orden de magnitud y mide la alineación entre el orden de dentro y la exposición, no «observaciones independientes». «Fiable» sin ventaja: mediana 8 %, por madre y con el orden de dentro fijo; máximo 22,5 %. La fórmula supone prácticamente 0 %. No es la tasa de falsos positivos del paso.

### 5.4 Los controles y los duplicados están dentro de la nube

`engines/variants/panel.py:90-92` no filtra por estrato. El glosario dice de los canarios que «detectan una cadena rota, no leen la superficie» (`contract/wfc.py:42-43`), pero cuentan como puntos. Los pares inertes son, por definición, copias del original. El SPP quita duplicados exactos antes de contar (`core/surface/dedupe.py`); el WFC no.

### 5.5 La composición por defecto gasta `oos2`, y se calculan cuatro miradas apuntando una

- El WFC «oficial» de cada madre es `build+oos1` → `oos2` (`engines/variants/config.yaml:46`).
- Cada ejecución calcula y enseña las cuatro particiones, tres de las cuales tocan `oos2`, y apunta en el ledger sólo la pedida (`report.py:107-122` y `:152-157`; el comentario lo dice).
- `exceso_persistencia_minimo` incluye `oos2` (`contract/criteria.py:35-36`). La ficha que justifica ofrecerlo dice que se calibró «build → oos1 ONLY (oos2 is reserved and was not used to decide anything)». El hecho ofrecido y la medida que lo respalda no son sobre las mismas ventanas.

### 5.6 Los hechos del paso 17 no llegan al juez

Tres cosas, la primera comprobada ejecutando y las otras dos leídas en el código:

1. `facts.gather` se queda sólo con los resultados que son **carpeta** (`pipeline/autopilot/facts.py:222`). Los estudios de lote escriben un **fichero**, `estudios/wfc.json` (`ui/daemon/workflow/sources.py:82-87`). Resultado: 0 filas. Lo mismo valdría para 18 y 18.5.
2. La cola del autopiloto añade 17, 18 y 18.5 como acciones «a ciegas» con `add(n, "blind")` (`pipeline/autopilot/tail.py:107-110`), sin pasar por `visit`, que es lo único que deja un paso pendiente de juicio; y sólo un paso pendiente genera la acción de juzgar (`tail.py:69-73`). **Una regla `"17"` en `criteria.yaml` no se juzgaría nunca.**
3. El resultado se firma con el nombre de la carpeta, `Strategy_10.11.484`, con guion bajo (`report.py:136`); en el databank la estrategia se llama `Strategy 10.11.484`. El juez casa por identidad o por nombre exacto, sin normalizar (`judge.py:68-86`; la carpeta lleva guion bajo por `core/datapaths.py:97`). No casarían por nombre; el WFC tendría que firmar con el nombre del databank o con su identidad. Es un riesgo real, hoy latente. (No comprobado qué identidad escribe el sobre del resultado.)

Con tu doctrina —un hecho que falta es Limbo—, una regla sobre un hecho `wfc.*` dejaría a todas en Limbo el día que se juzgara; hoy ni eso, porque no se juzga (punto 2).

### 5.7 Hechos que engañarían si se extrajeran

- **`.real` = 1,0 siempre.** El histograma del ratio recibe 1,0 en el hueco del «valor real» para pintar la línea de paridad (`contract/wfc.py:93-94`). Saldría como `wfc.cloud.ratio_sharpe_oos_is_por_variante.real`.
- **Dos particiones con la misma clave.** `build__oos1+oos2` y `build+oos1__oos2` se convierten las dos en `build_oos1_oos2` al limpiar el nombre (`facts.py:29-32`). El extractor las separaría con `#2` según el orden (`facts.py:228-229`): una clave sin sufijo para «`build` contra todo lo de después» y la misma con `#2` para la composición estricta.
- **Los Sharpe «superpuestos» son una mezcla.** El bloque junta los de dentro y los de fuera en un solo montón para sacar percentiles (`contract/wfc.py:102-105`). Es el mismo defecto que el panel 2 del SPP.
- **El rho no es un hecho limpio.** La puntuación del veredicto es texto (`Spearman 44,53 %`) y se descarta. Queda el de la tabla, a tres cifras significativas (`contract/wfc.py:169`).
- **De la tabla de persistencia sólo sobrevive «Variantes».** El resto de celdas es texto a propósito (`contract/criteria.py:43-44`).

### 5.8 Dos Sharpe distintos en un mismo cociente

- Tramo suelto (`build`, `oos1`, `oos2`): el que guardó SQX. Unión (`build+oos1`, `oos1+oos2`): calculado en Python desde la curva diaria, media entre desviación por √252 (`sqx/variants/united.py:129-132`).
- Medido por mí sobre los mismos días y variantes: el de SQX sale, en mediana por variante, entre un 1 % y un 32 % mayor en `oos1` y entre un 5 % y un 38 % mayor en `build`, según la madre (correlación entre los dos, de 0,97 a 0,998). Por qué difieren, **no medido**.
- Consecuencias: en la composición por defecto, el ratio es «Sharpe de SQX en `oos2`» entre «Sharpe de Python en `build+oos1`». Y el nulo del ratio pone siempre un Sharpe de Python arriba (`persistence.py:59-61`) y el de dentro, que puede ser de SQX, abajo. Un matiz más: el Sharpe del nulo divide por la desviación «de población» (ddof = 0, `persistence.py:59`) y el de una unión por la «de muestra» (ddof = 1, `united.py:129-132`); con mil días la diferencia es de un 0,05 %, pero son tres definiciones, no dos.
- La ayuda de la columna dice: «Los dos Sharpe son los anualizados de SQX (√252)» (`contract/criteria.py:84-85`).

### 5.9 Los suelos de operaciones: comentarios y valores

- `engines/variants/config.yaml:5-18` dice que el suelo duro es «50 operaciones en TOTAL» y que el segundo es «30, el suelo que usa el propio SQX». Los valores son 100 (`assets/_build.yaml:368`, cuyo propio comentario de la línea 353 también dice 50) y 50 (`engines/variants/config.yaml:19`).
- La madre de `13.3.390` hizo 45 operaciones en `oos2`: no entra en su propia nube en ninguna composición cuyo lado de fuera sea `oos2` solo.
- El suelo por lado decide el resultado en algún caso (4.5: G, de 0,01 a 0,28).

### 5.10 El suelo 0,30 no está en el registro de umbrales

`ledger/thresholds.yaml` no tiene ninguna clave del WFC. El `rho_floor` es un número suelto en `studies/optimisation/wfc/config.yaml:6`, sin quién, cuándo ni por qué. Y sin embargo el registro lo cita: el suelo del paso 18.5 está justificado como «el mismo suelo que el WFC» (`ledger/thresholds.yaml:78-85`).

### 5.11 «Spearman 44,53 %»

Apartado 3.10 (`contract/wfc.py:57-60`). Un coeficiente de correlación presentado como porcentaje.

### 5.12 El top del «20 %» no es siempre el 20 %

Apartado 3.6 (`persistence.py:22`, «mayor o igual»): del 20 % al 24 % en las diez.

### 5.13 El rango del nulo en la ayuda de la ventana es fijo

`ui/text/columnhelp_criteria.py:29-32`: «Una familia sin ventaja da entre −0,27 y +0,29». Es la mediana de diez madres con `oos1`. Madre a madre va de ±0,17 a ±0,34, y la tabla del estudio ya enseña el de cada una.

### 5.14 El neto del nulo no es exactamente el neto real

La suma de la curva diaria en los días de `oos1` no coincide siempre con el `NetProfit (oos1)` de SQX: en tres madres coincide al dólar; en las otras se separa hasta 1.470 USD en alguna variante (mediana de 0 a 322). Viene de las operaciones abiertas en los bordes del tramo. No cambia ninguna conclusión de aquí, pero el nulo y el real no miden exactamente lo mismo.

### 5.15 La documentación del estudio habla del CSCV

`README.md:46-72` («Three traps measured here» y «What it does not tell you») y todo `POSSIBLE_IMPROVEMENTS.md` tratan del PBO, de los bloques, del Sharpe desinflado: son del CSCV, que se separó el 2026-09-25. `contract/README.md:3` nombra una carpeta `verdict/` que no existe. El WFC no tiene escrito por qué usa beneficio neto y no una tasa (el propio `POSSIBLE_IMPROVEMENTS.md`, sección 2, argumenta que una medida que crece con el tiempo no se compara entre ventanas de distinta duración; para el rho de rangos da igual, para la pendiente no), ni de dónde sale el 20/50 de la persistencia.

### 5.16 Lo que no está medido

- La tasa de falsos positivos del veredicto con una población sin ventaja pasada por 16.5 y 17. Lo de 2.5 es un nulo por madre, una ventana, con el lado de dentro fijo, hecho por mí: no es esa tasa.
- Si el WFC de una ventana predice el de la siguiente. Aquí, con diez: −0,60 (de −0,90 a +0,07, intervalo optimista) para el rho y −0,10 para el exceso: no confirma; el signo no se sostiene.
- Cuánto cambia el rho con el reparto de estratos del diseño, o con el ancho de la rejilla (3.2).
- Cuánto contamina el rho de `build` → `oos1` que la madre se eligiera mirando `oos1` (2.9): sesgo mecánico al alza, magnitud no medida.
- Un intervalo del rho que respete la dependencia (por bloques de días, por ejemplo).
- Este paso sobre estrategias que sí pasan el 8. Ninguna corrida lo tiene.

### 5.17 Dónde este documento corrige al informe anterior

Sobre `criterios-pasos-6-a-19-explicados-2026-10-06`, apartado 8:

- **«`indeciso` (lo cruza; es el caso habitual)».** En la corrida es el menos frecuente: 1 de 10 en la composición pedida, 3 de 10 contra `oos1`.
- **«Con pocas variantes distintas el error es enorme».** El estudio trabaja con cientos de variantes y su fórmula da un error pequeño (±0,10). El error real es grande por otra razón: las variantes no son independientes.
- **«Sólo anota».** Para el autopiloto, sí. Y más de lo que yo escribí en el primer borrador: el veredicto propio se lee en el paso 20 y con `sin_fallo` un «No fiable» marca DESCARTAR en su `verdict.csv` (6 de 10 aquí), pero el autopiloto no lo aplica; sólo corta si se aplica a mano con `/curate`.
- **«El mismo signo en las dos composiciones» como resultado ideal.** Sigue siendo razonable; en las diez entre `build` → `oos1` y la pedida lo cumplen seis por signo (`10.11.484`, C, `16.5.352`, `18.5.355`, `3.9.284` y G, varias con uno de los dos rho casi nulo), tres por llamada (`10.11.484`, `16.5.352`, E) y sólo una con «Fiable» en las dos.
- «No hay hechos de este paso en las corridas consultadas»: sigue siendo cierto, y ahora se sabe por qué (5.6).

---

## 6. Cierre

### 6.1 Las reglas, en una tabla

| regla | hecho | Pasa | Limbo | Falla |
|---|---|---|---|---|
| — | — | — | — | — |

No hay entrada del paso 17 en `criteria.yaml`.

### 6.2 El resultado sobre la población real

No hay nada que calcular con `pipeline.autopilot.criteria`: sin regla y sin hechos. Lo que dijo el veredicto propio del estudio, y las lecturas de este documento, una al lado de otra:

| madre | pedida: rho [intervalo] | llamada | `build`→`oos1`: rho [intervalo] | llamada | p contra el nulo (mío) | exceso `oos1` / `oos2` |
|---|---|---|---|---|---|---|
| `10.11.484` | 0,445 [0,350; 0,531] | Fiable | 0,576 [0,494; 0,647] | Fiable | 0,002 | +0,33 / +0,21 |
| `13.3.390` | −0,159 [−0,290; −0,022] | No fiable | 0,345 [0,219; 0,459] | Indeciso | 0,15 | +0,34 / −0,03 |
| C `14.3.479` | 0,002 [−0,111; 0,116] | No fiable | 0,668 [0,598; 0,727] | Fiable | 0,018 | +0,39 / +0,24 |
| F `15.9.352` | −0,219 [−0,310; −0,124] | No fiable | 0,317 [0,231; 0,398] | Indeciso | 0,14 | +0,35 / −0,36 |
| `16.5.352` | 0,038 [−0,059; 0,134] | No fiable | 0,099 [0,006; 0,190] | No fiable | 0,13 | −0,09 / −0,01 |
| `18.5.355` | 0,105 [−0,019; 0,227] | No fiable | 0,290 [0,181; 0,392] | Indeciso | 0,09 | +0,06 / −0,16 |
| `19.2.363` | 0,202 [0,096; 0,303] | Indeciso | −0,246 [−0,361; −0,125] | No fiable | 0,80 | −0,10 / +0,12 |
| E `3.11.426` | 0,068 [−0,055; 0,188] | No fiable | −0,203 [−0,317; −0,082] | No fiable | 0,92 | −0,16 / +0,16 |
| `3.9.284` | 0,542 [0,458; 0,616] | Fiable | 0,024 [−0,089; 0,136] | No fiable | 0,46 | −0,02 / +0,38 |
| G `4.13.338` | 0,395 [0,308; 0,475] | Fiable | 0,009 [−0,102; 0,120] | No fiable | 0,49 | +0,10 / +0,37 |

| | Fiable | Indeciso | No fiable |
|---|---|---|---|
| composición pedida | **3** | 1 | 6 |
| `build` → `oos1` | 2 | 3 | 5 |

### 6.3 Las decisiones que te quedan

Cada una con su coste en estrategias (sobre las diez) junto a lo que gana.

1. **¿Dejar el paso sin regla en el autopiloto?** Coste: 0. Ganancia: 0. Es lo que hay. Y hoy una regla no serviría: no se juzgaría (5.6).

2. **¿Qué composición es «el» WFC?** Hoy, `build+oos1` → `oos2`. Coste de cada opción con «No fiable = fallo»: **6 de 10** con la pedida, **5 de 10** con `build` → `oos1`, y sólo dos madres en común. A favor de la pedida: usa el tramo que nadie ha mirado. En contra: lo gasta en una medida cuyo error real es varias veces el que declara, sobre 2,75 años. A favor de `build` → `oos1`: no toca `oos2`. En contra: en una corrida normal `oos1` ya se usó para elegir a la madre.

3. **¿Sigue contando «No fiable» como fallo en el paso 20?** (`joint.pieces: sin_fallo`). Coste hoy: **6 de 10 marcadas DESCARTAR** en el `verdict.csv` del paso 20, **0 cortadas** por el autopiloto (el 20 no tiene `cut`); serían 6 si aplicas ese veredicto a mano con `/curate`. Lo que sabes ahora: con el orden de dentro fijo, una familia sin ventaja sale «No fiable» entre el 60 % y el 99 % de las veces (bien), pero familias que ganan enteras también (E y G contra `oos1`), porque la prueba mide orden. Alternativa sin coste: `ninguna` (las piezas son contexto), que ya existe como opción en ese fichero.

4. **¿El suelo de 0,30?** A 0,15: «No fiable» baja de **6 a 4** en la composición pedida y no aparece ningún «Fiable» nuevo. A 0: de 6 a 2. Lo que no sabes: qué tasa de falsos positivos tiene cada línea. Y, sea cual sea, conviene que conste en `ledger/thresholds.yaml` con fecha y motivo: hoy no está.

5. **¿Un intervalo que respete la dependencia?** Es trabajo de código, no una decisión estadística tuya, pero cambia el veredicto: contra el nulo de volteo, sólo **2 de 10** (`10.11.484` y C) tienen un rho contra `oos1` distinguible de «sin ventaja» al 5 %, y son diez contrastes sin corregir: con Bonferroni (0,005) queda **1 de 10** (`10.11.484`, p = 0,002; C, con 0,018, no). El intervalo de fórmula excluye el cero por arriba en 6. Sin esto, «Fiable» y «No fiable» se apoyan en un error entre 1,8 y 7 veces menor que el medido.

6. **¿Poner umbral a la persistencia?** Los dos hechos ofrecidos: `_oos1` ≥ 0 cuesta **4 de 10**; `_oos1` por encima de su nulo, **6 de 10**; `_minimo` ≥ 0, **7 de 10**; `_minimo` por encima del nulo, **10 de 10**. Lo que sabes: en `oos1` separa (4 de 10 fuera del nulo), pero ninguna de esas cuatro repite en `oos2`, y dos de ellas (F y `13.3.390`) son familias que pierden. Si pones umbral, es una mirada: apúntala en el ledger.

7. **¿Exponer los hechos?** Que el extractor lea los resultados de lote; el rho, los dos extremos del intervalo y el p95 del nulo como números; cada partición con su clave. Coste en estrategias: 0. Sin esto, ninguna regla del paso 17 (ni del 18, ni del 18.5) puede existir.

8. **¿Sacar de la nube los controles y los duplicados?** Coste: 0 llamadas cambian contra `oos1`; el rho se mueve como mucho 0,02. Ganancia: el N deja de contar copias (G: 332 → 203).

9. **¿Qué suelo de operaciones por lado?** De 50 a 30: **1 de 10** cambia de llamada (G, de «No fiable» a «Indeciso»). Y decidir qué número es el bueno: los comentarios dicen 50 y 30, los valores son 100 y 50.

10. **¿Correr la prueba de vacuidad?** Fabricar el lote de variantes de unas cuantas estrategias sin ventaja («monos seleccionados») y pasarlas por el WFC. Coste: un paso 16.5 por cada una. Ganancia: la única cifra que convierte el suelo, o el umbral de persistencia, en algo más que una convención. Mi nulo de 2.5 es un sustituto barato, no lo mismo.

### 6.4 El límite que no cambia

El WFC contesta una pregunta estrecha y útil: **dentro de esta familia, ¿sirve de algo mirar el pasado para elegir parámetros?** No contesta si la familia gana, ni si la madre es buena. La contesta sobre un solo camino de precios que todas las variantes recorren juntas, así que su error es mucho mayor de lo que su intervalo dice, y lo que da en una ventana no se ha visto repetirse en la siguiente. Su sitio natural es el que le dio el Council: **anotar**. Lo que hoy no encaja con eso es que su veredicto, con un suelo que nadie ha calibrado y un intervalo que cuenta de más, ya escribe DESCARTAR en el `verdict.csv` del paso 20. El autopiloto no lo aplica; quien lo aplique a mano, sí.
