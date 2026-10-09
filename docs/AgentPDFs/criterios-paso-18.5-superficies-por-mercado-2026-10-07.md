# Paso 18.5 — Superficies por mercado: qué calcula, qué criterio hay cargado y qué no cuadra

**Fecha:** 2026-10-07 · **Para:** el dueño · **Alcance:** el módulo `studies/optimisation/marketSurfaces/`
(`report.py` y todo lo que importa, incluido `core/surface/`), el sitio donde su veredicto se usa
(`studies/closing/blindJoint/`, paso 20) y lo que el piloto automático hace con él
(`pipeline/autopilot/`).

**Qué es este documento.** La referencia para que fijes tú el criterio del paso 18.5. Cuenta qué
calcula el módulo exactamente, con qué matemática, qué números escribe, qué criterio hay cargado hoy y
qué no cuadra entre el código y lo que dicen sus textos. Cada estadístico se explica desde cero, con
un ejemplo pequeño hecho a mano, antes de usarlo. No propone reglas nuevas: describe lo que hay y, en
la sección 5, lo que falta para poder escribir una.

**De dónde salen los números.** De la corrida `Trade_NIKKEI225_M30_volatilidadL` del 2026-10-04
(NIKKEI225, M30, largas): diez madres, cada una con su lote de variantes del paso 16.5 retestado en el
principal y en once mercados más. Los tramos `build` y `oos1` los he **recalculado yo** con el código
del propio estudio (`one.measure`) y coinciden con el `pairs.csv` que el paso dejó escrito hasta el
decimal 16, en las diez madres. El tramo `oos2` **no lo he recalculado**: sus cifras están copiadas de
lo que el paso ya escribió ese día (`pairs.csv` y el resumen de `marketSurfaces.json`), sin abrirlo de
nuevo. Lo que lleva la marca «calculado por mí; no es un hecho» es una medición mía que el módulo no
hace. «No medido» quiere decir que nadie lo ha medido. «Ilustrativo» es un ejemplo inventado para
explicar.

**Ninguna línea de este documento está congelada.** Los tres umbrales del estudio los puso un agente,
no tú (`ledger/thresholds.yaml:78-103`), y uno de ellos está marcado «PROVISIONAL hasta que el dueño lo
fije».

**Revisión.** Revisado por dos miembros del Council (Feynman, Taleb) el 2026-10-07; correcciones
aplicadas. Lo que lleva la marca «medición del revisor» lo midieron ellos sobre los mismos ficheros,
no yo.

---

## 0. En una página

### La pregunta del paso

Una madre ha llegado hasta aquí con una **zona de parámetros** que funciona en el NIKKEI225. El paso
18.5 pregunta: **las variantes que son buenas en el mercado principal, ¿son también las buenas en
otros mercados?** No pregunta si la madre gana en otros mercados (eso es el paso 10). Pregunta si el
**orden** de las variantes —cuál es mejor que cuál— se repite fuera.

La idea de fondo: si el orden de las variantes en el NIKKEI es puro ajuste al ruido del NIKKEI, en el
DAX ese orden saldrá barajado. Si el orden se repite, lo que distingue una variante buena de una mala
es algo del mercado y no del histórico concreto.

### Lo que hay cargado hoy

| Dónde | Qué | Valor | Quién lo puso |
|---|---|---|---|
| `pipeline/autopilot/criteria.yaml` | regla del paso `"18.5"` | **no existe** | — |
| `ledger/thresholds.yaml:78-85` | `rho_floor`: suelo del Spearman | 0,30 | agente, 2026-09-26 |
| `ledger/thresholds.yaml:87-94` | `j_quantile`: banda del azar del Jaccard | 0,975 | agente |
| `ledger/thresholds.yaml:96-103` | `min_share`: parte de los mercados que debe pasar | 0,5 | agente, «PROVISIONAL» |
| `engines/variants/config.yaml` | `min_trades`: operaciones mínimas por celda | 50 | — |
| `studies/closing/blindJoint/config.yaml` | `joint.pieces: sin_fallo` (paso 20) | ninguna pieza en «fail» | tú, 2026-10-04 |

El paso 18.5 **no tiene regla en el piloto**. Lo único que decide algo es el veredicto que el propio
estudio se pone (con esos tres umbrales) y que el paso 20 lee como una de sus cuatro piezas.

### Lo que sale en la corrida real

- **Las diez madres salen «La región no viaja»** (estado `fail`), en los tres tramos.
- Hacen falta **6 de 11** mercados aprobados en un tramo (11 × 0,5 = 5,5). El máximo que alcanza
  cualquier madre en cualquier tramo es **2 de 11**.
- Por parejas principal-mercado: en `build`, 6 aprueban, 44 quedan en duda y 60 suspenden (de 110); en
  `oos1`, 3, 22 y 84 (de 109).
- En el paso 20 la pieza «superficies» es `fail` en las diez. Con la lectura `sin_fallo` eso basta
  para «DESCARTAR». En nueve de las diez hay además otra pieza en `fail`; **sólo en una (`10.11.484`)
  superficies es la única pieza que falla**.
- **Nadie fue cortado.** Ese «DESCARTAR» se escribe en el `verdict.csv` del paso 20, pero el
  autopiloto no lo aplica: `criteria.yaml` sólo tiene reglas de los pasos 8, 10, 11.5, 12, 14 y 16, y
  `pipeline/autopilot/judge.py:172-173` responde «ninguno: el paso no tiene criterio». Todas siguen;
  sólo se corta si alguien lo aplica a mano con `/curate`. Los pasos 21 y 22 corrieron sobre las diez.

### Las ocho cosas que conviene saber

1. **El paso decide con un número que no es el que enseña.** La decisión usa el Spearman «sin
   exposición» (`verdict/call.py:25,27`). Las barras de la pestaña y las partes del veredicto enseñan
   el Spearman **bruto** con la línea del suelo y el color del estado (`contract/tabs.py:77-82`,
   `one.py:184`). El manual (cap. 52, líneas 123-128) dice que la llamada usa el bruto. Resultado: una
   barra entera por encima del suelo puede estar en rojo (madre G, HK50, `build`).
2. **No hay regla del paso 18.5 y, si la escribieras hoy, no funcionaría.** El piloto ejecuta el 18.5
   «a ciegas» (calcula y no lee) y `facts.py` no recoge ningún hecho de este estudio: su filtro
   descarta los resultados que son ficheros y no carpetas. Una regla sobre el 18.5 dejaría a todas en
   Limbo.
3. **El criterio que de verdad actúa son tres umbrales que no has fijado tú**, más tu decisión
   `sin_fallo` del paso 20.
4. **El intervalo del Spearman es unas 3,6 veces más estrecho de lo que debería** (calculado por mí;
   no es un hecho). Trata las variantes como si fueran independientes y no lo son: son vecinas unas de
   otras. El propio código lo admite («optimista»).
5. **La banda del azar del Jaccard es más o menos la mitad de ancha que la que mide el propio
   módulo** con su segundo contraste (el volteo de signos de `measure/lift.py`). De 25 parejas que superan la banda, sólo 2 superan también la del segundo contraste (orden de
   magnitud, no prueba).
6. **Lo más grave: el «fail» de la madre no informa.** Sin ventaja ninguna, ninguna madre llegó a 6
   de 11 en 1.000 sorteos por madre y tramo (calculado por mí). Pero tampoco llega lo que debería
   llegar seguro (medición del revisor): el NIKKEI contra **sí mismo** (`build` frente a `oos1`, las
   mismas variantes) pasa la regla de pareja en 1 de 10 madres, y los tres índices de EE. UU., que son
   casi el mismo mercado, aprueban entre sí 3 de 60 parejas. Con estos lotes, 6 de 11 en tres tramos
   es inalcanzable: sale «no viaja» haya algo o no lo haya.
7. **Los textos hablan de «9 mercados», «misma familia» y «costes provisionales» y ninguna de las tres
   cosas es verdad en esta corrida:** son 11 mercados, 3 de ellos estructurales (oro, euro, cobre), y
   la marca de costes provisionales está apagada en los 12 símbolos. Son frases fijas en el código
   (`one.py:163-166`, `one.py:188`, `contract/tabs.py:8-11,85`).
8. **«La región» del titular no es lo que se mide.** Se mide si el orden de **todas** las variantes
   coincide y si el 10 % mejor se comparte. La meseta alrededor de la madre, que es lo que uno
   entiende por «región», tiene aquí entre 1 y 4 variantes y sólo se enseña, no decide.

---

## 1. Qué es el paso y cómo decide

### 1.1 Dónde está en la secuencia

```
16    SPP                  -> ¿aguanta la madre al mover sus parámetros?
16.5  lote de variantes    -> ~500 variantes de cada madre, retestadas en 12 mercados
17    WFC      \
18    CSCV      |  cuatro lecturas del MISMO lote, calculadas sin mirarlas
18.5  superficies|
19    WFM      /
20    lectura conjunta     -> lee las cuatro a la vez y propone MANTENER o DESCARTAR
```

Los pasos 17, 18, 18.5 y 19 trabajan sobre el mismo material y el piloto los calcula sin leer el
resultado. Sólo el paso 20 los junta. La razón es no gastar miradas: cada vez que se mira un resultado
y se decide algo, cuenta como un intento más.

### 1.2 Lo que deja el paso 16.5 (lo justo para entender éste)

Para cada madre, el 16.5 diseña unas 500 **variantes**: la misma estrategia con los parámetros
movidos. Vienen de tres diseños —vecindario de la madre (99), factorial (296) y cobertura (99)— más
unos controles. La madre es la variante `P00000`.

Cada variante se retesta en el mercado principal y en todos los mercados que la ficha
`assets/_markets.yaml` declara para el activo. Para el NIKKEI225 son **once**:

| Grupo | Mercados |
|---|---|
| Familia (8) | USA500, USATEC, DJ30, DAX40, UK100, HK50, USDJPY, AUS200 |
| Estructurales (3) | XAUUSD, EURUSD, XCUUSD |

Todos en M30, igual que el principal. **No hay D1 en este paso**, así que tu regla de «D1 nunca en el
cruce de mercados adicionales» se cumple.

De cada variante, mercado y tramo, el 16.5 guarda el beneficio neto, las operaciones y la exposición
(el tiempo que la estrategia pasa dentro del mercado). Los tramos de esta corrida:

| Tramo | Desde | Hasta |
|---|---|---|
| `build` | 2011-09-19 | 2020-01-01 |
| `oos1` | 2020-01-01 | 2024-01-01 |
| `oos2` | 2024-01-01 | 2026-10-01 |

No todas las variantes diseñadas llegan. El 16.5 tira las que no alcanzan 100 operaciones en total
(`assets/_build.yaml:368`, `min_trades_total: 100`). Lo que queda en cada madre:

| Madre | Diseñadas | Quedan | Tiradas por pocas operaciones |
|---|---:|---:|---:|
| `10.11.484` | 500 | 420 | 80 |
| `13.3.390` | 500 | 276 | 224 |
| C `14.3.479` | 501 | 417 | 84 |
| F `15.9.352` | 501 | 501 | 0 |
| `16.5.352` | 500 | 499 | 1 |
| `18.5.355` | 500 | 376 | 124 |
| `19.2.363` | 500 | 402 | 98 |
| E `3.11.426` | 501 | 429 | 72 |
| `3.9.284` | 500 | 416 | 84 |
| G `4.13.338` | 500 | 460 | 40 |

(Las letras C, E, F y G son las mismas cuatro estrategias que seguimos en el dossier del paso 16.)

### 1.3 Qué lee el estudio

Tres ficheros de la carpeta de cada madre, en
`AlgoData/strategyPermutations/<proyecto>/Strategy_<x>/`:

| Fichero | Qué trae | Quién lo lee |
|---|---|---|
| `metrics.parquet` | la lista de variantes que quedaron | `inputs/surfaces.py:62-73` |
| `segments.parquet` | beneficio, operaciones y exposición por variante, mercado y tramo | `inputs/surfaces.py:91-120` |
| `equity_markets.parquet` | el resultado de cada día de cada variante en cada mercado | `inputs/surfaces.py:144-158` |

No habla con SQX. Es todo aritmética sobre esos ficheros.

### 1.4 Cómo decide: dos escalones

**Escalón 1: cada pareja principal-mercado, en cada tramo, recibe un estado.**

```
aprueba (pass)   si  el límite INFERIOR del Spearman sin exposición  > 0,30
                 Y   el Jaccard del 10 % mejor  >  la banda alta del azar
suspende (fail)  si  el límite SUPERIOR del Spearman sin exposición  < 0,30
en duda (watch)  en cualquier otro caso
```

(`verdict/call.py:6-29`.) El Jaccard no puede suspender a nadie: sólo puede impedir el aprobado.

**Escalón 2: la madre recibe una llamada.**

```
en cada tramo:  ¿aprueban al menos la mitad de los mercados DECLARADOS?
                (11 declarados × 0,5 = 5,5  ->  hacen falta 6)

los tres tramos llegan      -> «La región viaja»           (pass)
ninguno llega               -> «La región no viaja»        (fail)
unos sí y otros no          -> «La región viaja a medias»  (watch)
```

(`verdict/call.py:48-75`.) El divisor son siempre los mercados declarados: un mercado que falta cuenta
como que no aprueba.

Fíjate en la asimetría: para que una madre «suspenda» no hace falta que ninguna pareja suspenda. Basta
con que **en ningún tramo lleguen a aprobar seis**. Una madre con las once parejas «en duda» en los
tres tramos sale «La región no viaja».

### 1.5 Cómo entra en el paso 20

El paso 20 (`studies/closing/blindJoint/`) lee el estado que cada una de las cuatro piezas se ha
puesto a sí misma (`pieces.py:12`, `pieces.py:45-60`). Con la lectura cargada, `sin_fallo`
(`readings.py:16-18`), la madre pasa si **ninguna** pieza está en `fail`. Así que hoy:

```
superficies = «La región no viaja»  ->  pieza en fail  ->  paso 20 dice «No pasa»  ->  DESCARTAR
superficies = «viaja a medias»      ->  pieza en watch ->  no estorba
```

El paso 20 no usa ningún número del 18.5. Sólo la etiqueta.

Y lo que el paso 20 hace con ella es **marcar**: escribe «DESCARTAR» en su `verdict.csv`. El
autopiloto no lo aplica y todas siguen; sólo corta si se aplica a mano con `/curate`.

### 1.6 Los avisos que escribe

| Aviso | Cuándo sale | Dónde |
|---|---|---|
| `costs_provisional` | si algún coste de la ficha tiene un «por qué» que empieza por «PROVISIONAL» | `one.py:141-143` |
| `family_only` | **siempre**, con el texto fijo «Los 9 mercados son de la misma familia…» | `one.py:163-166` |

El segundo sale también cuando no es cierto. Ver sección 5.

---

## 2. Fundamentos: los estadísticos, desde cero

### 2.1 Qué es una «superficie» de parámetros

Imagina una estrategia con dos parámetros: el periodo de una media y el tamaño del stop. Pruebas
varias combinaciones y apuntas el beneficio de cada una. Ilustrativo:

```
                 stop 1,5   stop 2,0   stop 2,5
periodo 10         3.000      5.000      4.000
periodo 20         6.000      9.000      7.000
periodo 30         2.000      4.000      1.000
```

Eso es una superficie: un beneficio por cada combinación. Si la dibujas con el beneficio como altura,
sale un relieve con una cima (aquí, periodo 20 y stop 2,0).

En el paso 18.5 la «superficie» de un mercado y un tramo es simplemente **la lista del beneficio neto
de cada variante** en ese mercado y ese tramo. Con 417 variantes, 417 números. Hay una superficie por
mercado y por tramo: 12 mercados × 3 tramos = 36 por madre.

La pregunta del paso es si el relieve del NIKKEI se parece al del DAX: si las cimas y los valles caen
en los mismos sitios.

### 2.2 Rangos: quedarse con el orden y tirar los dólares

No se pueden comparar los dólares de un mercado con los de otro: el cobre mueve cifras distintas que
el Nikkei. Lo que sí se puede comparar es el **orden**.

El **rango** de una variante es su puesto cuando las ordenas de peor a mejor: la peor tiene rango 1,
la siguiente 2, y así. Seis variantes, ilustrativo:

```
variante    beneficio en A    rango en A    beneficio en B    rango en B
   V1            9.000            6              4.000            5
   V2            7.000            5              6.000            6
   V3            5.000            4              1.000            3
   V4            3.000            3              2.000            4
   V5            1.000            2             -1.000            2
   V6           -2.000            1             -3.000            1
```

### 2.3 El Spearman (rho): cuánto se parecen dos órdenes

El **Spearman**, que se escribe rho, mide cuánto se parecen dos órdenes. Va de −1 a +1:

| rho | Qué quiere decir |
|---|---|
| +1 | el orden es idéntico en los dos mercados |
| 0 | no tienen nada que ver: saber el puesto en A no dice nada del puesto en B |
| −1 | el orden está invertido: lo mejor en A es lo peor en B |

Con la tabla de arriba, a mano. Para cada variante se resta un rango del otro (d), se eleva al
cuadrado y se suma:

```
variante   rango A   rango B    d     d²
   V1         6         5       1     1
   V2         5         6      -1     1
   V3         4         3       1     1
   V4         3         4      -1     1
   V5         2         2       0     0
   V6         1         1       0     0
                              suma = 4

rho = 1 − 6 × suma / (n × (n² − 1))
    = 1 − 6 × 4 / (6 × 35)
    = 1 − 24 / 210
    = 0,886
```

Los dos órdenes se parecen mucho: sólo se cruzan V1 con V2 y V3 con V4.

El código lo calcula de otra forma que da lo mismo: saca los rangos (si hay empates, el rango medio) y
calcula la correlación normal entre las dos columnas de rangos (`measure/pairs.py:14-26`). Si una de
las dos superficies es constante, devuelve «sin dato».

**Cuánto vale por azar.** Si los dos órdenes no tienen nada que ver, rho sale alrededor de 0, pero
nunca exactamente 0: baila. Cuánto baila depende de cuántas variantes haya. Eso es lo siguiente.

### 2.4 El intervalo: cuánto fiarse de un rho

Un rho de 0,886 con seis variantes vale poco: con tan pocas, el azar da valores altos con facilidad.
Con 400 variantes, un rho de 0,886 sería casi una certeza. El **intervalo de confianza del 95 %** es
el rango de valores entre los que estaría el rho «de verdad» 95 de cada 100 veces.

El código usa el método de Fisher (`measure/pairs.py:122,131`), en tres pasos:

```
1. se estira el rho:      z = atanh(rho)
2. se le suma y resta:    medio = 1,96 / raíz(n − 3)
3. se vuelve a encoger:   límites = tanh(z − medio)  y  tanh(z + medio)
```

Con el ejemplo de seis variantes:

```
z      = atanh(0,886)        = 1,402
medio  = 1,96 / raíz(6 − 3)  = 1,96 / 1,732 = 1,132
límite inferior = tanh(1,402 − 1,132) = tanh(0,270) = 0,264
límite superior = tanh(1,402 + 1,132) = tanh(2,533) = 0,988

intervalo: de 0,264 a 0,988
```

El rho es 0,886, pero con seis variantes el intervalo baja hasta 0,264. Como el límite inferior queda
por debajo de 0,30, esta pareja **no aprobaría**.

Cuantas más variantes, más estrecho el intervalo. El rho que hace falta para que el límite inferior
supere 0,30, y el rho por debajo del cual la pareja suspende:

| Variantes distintas (n efectivo) | rho mínimo para aprobar | rho por debajo del cual suspende |
|---:|---:|---:|
| 150 | 0,439 | 0,147 |
| 220 | 0,416 | 0,175 |
| 300 | 0,400 | 0,193 |
| 420 | 0,385 | 0,210 |
| 500 | 0,378 | 0,218 |

Este método da por hecho que cada variante es una observación **independiente** de las demás. Aquí no
lo son: una variante y su vecina (un parámetro movido un paso) hacen casi las mismas operaciones. Eso
hace que el intervalo sea demasiado estrecho. Cuánto, en la sección 4.4.

### 2.5 El n efectivo: quitar las variantes repetidas

A veces dos variantes distintas dan **exactamente** el mismo beneficio en los dos mercados: el
parámetro que las diferencia no llega a cambiar ninguna operación. Contarlas como dos sería contar dos
veces lo mismo.

El código deja una sola fila por cada par de beneficios distinto (`measure/pairs.py:115`, con
`core/surface/dedupe.py:38-52`). A lo que queda lo llama **n efectivo** (`n_eff`), y es el n que usa
en todo: en el rho, en el intervalo y en el Jaccard.

```
madre C, NIKKEI contra USDJPY, build:
  variantes con dato en los dos mercados:   383
  pares de beneficios distintos:            320   <- n efectivo
```

Ojo con el nombre: «efectivo» sugiere que ya descuenta el parecido entre vecinas. No lo hace. Sólo
quita las repeticiones **exactas**. Dos variantes que difieren en un dólar cuentan como dos.

### 2.6 La exposición y el Spearman «sin exposición»

**El problema.** La exposición es el tiempo que una estrategia pasa dentro del mercado. En un mercado
que sube durante años, una variante larga que está más tiempo dentro gana más, sea cual sea su lógica.
Si en el Nikkei y en el DAX las variantes más expuestas son las mismas y los dos índices suben, los dos
órdenes coincidirán… sólo porque estar más tiempo dentro paga en los dos. Eso no es que la región
viaje.

**La solución del código** (`measure/pairs.py:29-53`): quitar de cada superficie la parte que explica
la exposición **de su propio mercado**, y comparar lo que queda.

```
1. en cada mercado, rango del beneficio y rango de la exposición de cada variante
2. se ajusta una recta: rango del beneficio = pendiente × rango de la exposición + corte
3. el RESIDUO de cada variante es lo que le sobra o le falta respecto a esa recta:
   «para lo expuesta que está, ¿ha ganado más o menos de lo que tocaba?»
4. se correlacionan los residuos de un mercado con los del otro
```

Ejemplo ilustrativo con las mismas seis variantes de antes:

```
            MERCADO A                         MERCADO B
variante  rango benef.  rango expos.     rango benef.  rango expos.
   V1          6             6                5             6
   V2          5             4                6             5
   V3          4             5                3             4
   V4          3             2                4             3
   V5          2             3                2             1
   V6          1             1                1             2

recta en A:  rango benef. = 0,886 × rango expos. + 0,4
recta en B:  rango benef. = 0,829 × rango expos. + 0,6

residuo de V1 en A:  6 − (0,886 × 6 + 0,4) = 6 − 5,714 =  0,286
residuo de V1 en B:  5 − (0,829 × 6 + 0,6) = 5 − 5,571 = −0,571

variante   residuo A   residuo B
   V1        0,286      −0,571
   V2        1,057       1,257
   V3       −0,829      −0,914
   V4        0,829       0,914
   V5       −1,057       0,571
   V6       −0,286      −1,257

Spearman bruto            = 0,886
Spearman sin exposición   = 0,536   (correlación entre las dos columnas de residuos)
```

En el ejemplo, buena parte del 0,886 se debía a que en los dos mercados las variantes más expuestas
ganaban más. Quitado eso, el acuerdo baja a 0,536.

En el código este número se llama `rho_neutral`. Tres cosas:

- **Es el número con el que se decide.** El bruto sólo se enseña.
- Su intervalo se calcula igual que el del bruto, con el mismo «medio» (`pairs.py:132-133`).
- Puede ser mayor o menor que el bruto. Cuando la exposición empuja en sentidos contrarios en los dos
  mercados, quitarla **sube** el acuerdo.

### 2.7 El decil superior y el Jaccard

El Spearman mira el orden de **todas** las variantes. Pero lo que te importa de verdad es la cima: si
las mejores aquí son las mejores allí. Dos órdenes pueden parecerse mucho en el montón de en medio y
nada en la punta.

**El decil superior** es el 10 % mejor. El código coge
`k = el 10 % de las variantes, redondeado hacia arriba` (`measure/pairs.py:56-70`). Con 320 variantes,
k = 32. Los empates se resuelven por el nombre de la variante.

**El Jaccard (J)** mide cuánto se solapan dos grupos:

```
J = las que están en los dos grupos / las que están en al menos uno
```

Como los dos grupos tienen el mismo tamaño k, si comparten x variantes:

```
J = x / (2k − x)
```

Va de 0 (no comparten ninguna) a 1 (son el mismo grupo). Ejemplo ilustrativo con 20 variantes y k = 2:

```
las 2 mejores en A:  V7 y V12
las 2 mejores en B:  V7 y V3
comparten:           1 (V7)

J = 1 / (2 × 2 − 1) = 1 / 3 = 0,333
```

Atención a la escala: el Jaccard castiga mucho. Compartir la mitad del decil (x = k/2) da J = 0,333,
no 0,5.

### 2.8 Cuánto vale el Jaccard por azar

Si los dos decilos se eligieran a ciegas, algo compartirían por pura casualidad. ¿Cuánto?

Es la cuenta de una urna. Hay n bolas; k están marcadas (las mejores en A). Sacas k bolas al azar (las
mejores en B). ¿Cuántas marcadas te salen? El número esperado es:

```
solape medio por azar = k × k / n
```

Con las 20 variantes y k = 2 del ejemplo: 2 × 2 / 20 = 0,2 variantes. Y las probabilidades exactas:

```
compartir 0:   153 / 190 = 0,805
compartir 1:    36 / 190 = 0,189
compartir 2:     1 / 190 = 0,005
```

El código saca dos números de aquí (`measure/pairs.py:73-88`):

**«Jaccard por azar» (`j0`)** es el Jaccard que corresponde al solape medio:

```
j0 = 0,2 / (2 × 2 − 0,2) = 0,2 / 3,8 = 0,053
```

Cuando k es justo el 10 % de n, esta cuenta da siempre 1/19 = 0,053. Es el «en torno a 0,05» que dice
el glosario.

**«Banda alta del azar» (`j_hi`)** es el Jaccard del solape que el azar no supera el 97,5 % de las
veces. Se suman las probabilidades desde abajo hasta llegar a 0,975:

```
hasta 0 compartidas:   0,805            (no llega a 0,975)
hasta 1 compartida:    0,805 + 0,189 = 0,995   (ya pasa de 0,975)  ->  solape de corte = 1

j_hi = 1 / (2 × 2 − 1) = 0,333
```

Para aprobar, el Jaccard tiene que ser **estrictamente mayor** que la banda. En el ejemplo, compartir
1 da J = 0,333, que es igual a la banda y no mayor: no aprueba. Hay que compartir las 2.

Como el solape sólo puede ser un número entero, «superar la banda» es en la práctica más exigente que
el 2,5 % que sugiere el nombre:

| n | k | solape de corte | para aprobar hay que compartir | probabilidad por azar de lograrlo |
|---:|---:|---:|---:|---:|
| 100 | 10 | 3 | 4 o más | 0,8 % |
| 300 | 30 | 6 | 7 o más | 1,9 % |
| 320 | 32 | 7 | 8 o más | 0,8 % |
| 500 | 50 | 9 | 10 o más | 1,8 % |

Esta cuenta da por hecho que los dos decilos se eligen **a ciegas y de forma independiente**. Con
variantes vecinas, que suben y bajan juntas, el azar real da solapes más grandes. El propio fichero de
umbrales lo dice: «Optimista: el diseño agrupa las variantes, así que el azar real es más ancho».

El código guarda también `p_overlap`: la probabilidad de que el azar dé un solape igual o mayor que el
observado (`pairs.py:135`). Se escribe en `pairs.csv` y no decide nada.

### 2.9 El segundo contraste: voltear el signo de los días

El módulo lleva dentro una segunda forma de preguntar «¿cuánto daría el azar?», más honrada que la
urna (`measure/lift.py`). No alimenta la decisión: alimenta dos números del resumen.

**La idea.** Se coge el resultado de cada día de cada variante. Se tira una moneda **por día**: si
sale cruz, ese día se cambia de signo (lo ganado pasa a perdido y al revés) **en todas las variantes a
la vez**. Se recalcula el beneficio de cada variante y su decil superior.

¿Qué se consigue? Se destruye cualquier ventaja (un día ganador es tan probable como uno perdedor),
pero se conserva el parecido entre variantes: dos vecinas que operan los mismos días siguen moviéndose
juntas. Es un azar que respeta la estructura del lote.

Ejemplo ilustrativo con dos variantes y tres días:

```
              día 1    día 2    día 3    total
V1 real       +100      −50      +30      +80
V2 real        +90      −40      −10      +40      -> V1 es la mejor

monedas (+, −, +):
V1            +100      +50      +30     +180
V2             +90      +40      −10     +120      -> V1 sigue siendo la mejor

monedas (+, +, −):
V1            +100      −50      −30      +20
V2             +90      −40      +10      +60      -> ahora la mejor es V2
```

El código repite el sorteo 1.000 veces, con las mismas monedas para todos los mercados
(`lift.py:19-32`; semilla fija, 17). En cada sorteo calcula el Jaccard entre el decil **real** del
principal y el decil del mercado volteado. La media de esos 1.000 es el «azar» de este segundo
contraste. De ahí salen:

```
lift = Jaccard real / Jaccard medio de los 1.000 sorteos
```

- **lift = 1:** el solape es el que da el azar.
- **lift = 2:** el doble que el azar.
- **lift por debajo de 1:** menos solape que la **media** del azar. Ojo: lo normal sin ventaja ya es
  quedar por debajo de 1 (sección 3.9).

Y otro número sobre la madre:

```
exceso de la madre = parte de los mercados donde la madre está en el decil superior
                     − la misma parte en los sorteos
```

Si la madre está en el 10 % mejor en 2 de 11 mercados (0,18) y en los sorteos sale 0,07, el exceso es
+0,11.

### 2.10 Cómo se juntan las parejas

Sólo lo que el código hace de verdad:

- **Dentro de un tramo:** se cuentan las parejas principal-mercado que aprueban. No se promedian los
  rho. No se pondera por mercado. Once mercados, once votos iguales.
- **Entre tramos:** cada tramo tiene que llegar por separado a la mitad. No se suman aprobados de un
  tramo con los de otro.
- **Las parejas entre dos mercados que no son el principal** (DAX contra oro, por ejemplo) se calculan
  y se guardan (78 filas por tramo, contando cada mercado consigo mismo), pero sólo sirven para
  pintar. No votan (`verdict/call.py:32-45`).
- **Los lifts:** el número del resumen es la **mediana** de los lifts de los mercados
  (`lift.py:65-93`).
- **No hay corrección por hacer muchas pruebas.** Cada madre pasa por 11 mercados × 3 tramos = 33
  contrastes. El requisito de «la mitad» hace de freno, pero no es una corrección calculada.

---

## 3. Lo que calcula el estudio, pieza a pieza

Los ejemplos de esta sección son de la madre **C `14.3.479`**, tramo `build`, salvo que se diga otra
cosa.

### 3.1 La celda y cuándo es utilizable

Una **celda** es una variante en un mercado y un tramo. Trae tres cosas: beneficio neto, operaciones y
exposición (`inputs/surfaces.py:91-120`).

Una celda es **utilizable** si tiene al menos 50 operaciones y su beneficio es un número
(`inputs/surfaces.py:119`). Si no lo es, esa variante queda en blanco en ese mercado y ese tramo, y no
entra en ninguna cuenta de esa pareja.

```
madre E, HK50, oos1:  la madre hace 44 operaciones  ->  44 < 50  ->  celda no utilizable
                      -> en esa pareja la madre no cuenta y su «Madre (%)» sale en blanco
```

Hay, por tanto, dos suelos distintos:

| Suelo | Valor | Sobre qué | Dónde |
|---|---:|---|---|
| para que la variante exista en el lote | 100 | operaciones en total | `assets/_build.yaml:368` |
| para que una celda cuente | 50 | operaciones en ese mercado y ese tramo | `engines/variants/config.yaml:19` |

### 3.2 n y n efectivo

- **n:** variantes con celda utilizable en **los dos** mercados de la pareja.
- **n efectivo:** de ésas, las que tienen un par de beneficios distinto (sección 2.5).

En C, el principal tiene 417 variantes utilizables. Los demás mercados, menos:

```
mercado     n (comunes)   n efectivo
USDJPY          383          320
EURUSD          383          318
DAX40           383          301
HK50            308          241
AUS200          305          235
```

Por qué los otros mercados traen 383 y no 417 no lo he trazado. Lo más probable es el suelo de 50 por
celda (el 16.5 apunta 2.166 celdas «finas» en esta madre), pero no lo he comprobado variante a
variante.

Sobre las diez madres: la mediana de n es 360 en `build` y 301 en `oos1`; la de n efectivo, 319 y 263.

### 3.3 El Spearman bruto y su intervalo

`measure/pairs.py:122,131`. NIKKEI contra USDJPY, recalculado a mano:

```
rho      = 0,6234
z        = atanh(0,6234)           = 0,7305
medio    = 1,96 / raíz(320 − 3)    = 1,96 / 17,80 = 0,1101
inferior = tanh(0,7305 − 0,1101)   = tanh(0,6204) = 0,5515
superior = tanh(0,7305 + 0,1101)   = tanh(0,8406) = 0,6861
```

Coincide con lo que el paso escribió (0,5515 y 0,6862). Este número se enseña en la tabla y en las
barras. **No decide.**

### 3.4 El Spearman sin exposición y su intervalo

`measure/pairs.py:29-53` y `132-133`. Es el que decide. En USDJPY apenas cambia: 0,6204, con intervalo
de 0,5481 a 0,6836. En otras parejas cambia mucho. El caso más claro de la corrida es la madre G
contra HK50, en `build`:

```
Spearman bruto:           0,364   intervalo de  0,241 a 0,477
Spearman sin exposición: −0,046   intervalo de −0,180 a 0,091
```

Qué ha pasado (cifras de la corrida, calculadas por mí sobre las 209 variantes distintas de esa
pareja). En los dos mercados las variantes más expuestas ganan menos: el Spearman entre beneficio y
exposición es −0,32 en el NIKKEI y −0,72 en HK50. Y las más expuestas en uno son las más expuestas en
el otro (0,85). Lo que mejor lo explica son los cruces: el beneficio en HK50 contra la exposición en
el NIKKEI da −0,73, y el beneficio en el NIKKEI contra la exposición en HK50, −0,50. Es decir: saber
cuánto tiempo pasa una variante dentro del mercado ya dice cómo queda en los dos. Quitada la
exposición, del parecido no queda nada.

Sobre las 219 parejas de `build` y `oos1` (cifras de la corrida, calculadas por mí), el bruto y el
neutral se parecen pero no son lo mismo: su correlación es 0,74 y difieren de media en 0,116. Ocho
parejas superan el suelo con el bruto y no con el neutral; seis, al revés.

### 3.5 El decil, el solape, el Jaccard y sus dos referencias

`measure/pairs.py:134-135`. NIKKEI contra USDJPY:

```
n efectivo = 320
k          = 10 % de 320 = 32
solape     = 11 variantes están en los dos decilos

J     = 11 / (2 × 32 − 11) = 11 / 53 = 0,2075

solape medio por azar = 32 × 32 / 320 = 3,2
j0    = 3,2 / (64 − 3,2) = 3,2 / 60,8 = 0,0526

probabilidad por azar de compartir exactamente x:
  x:     0      1      2      3      4      5      6      7      8      9
  p:   0,029  0,114  0,212  0,245  0,198  0,119  0,055  0,020  0,006  0,001
  sumando desde 0, se pasa de 0,975 al llegar a x = 7  ->  solape de corte = 7
j_hi  = 7 / (64 − 7) = 7 / 57 = 0,1228

p_overlap = probabilidad de compartir 11 o más por azar = 0,0001
```

J = 0,2075 es mayor que 0,1228: la pata del Jaccard se cumple.

Y el caso contrario, NIKKEI contra EURUSD, misma madre y tramo:

```
k = 32, solape = 7
J    = 7 / 57 = 0,1228
j_hi = 7 / 57 = 0,1228
¿J > j_hi?  No: son iguales.  ->  la pata del Jaccard NO se cumple
```

EURUSD tiene un Spearman sin exposición de 0,584 con intervalo de 0,507 a 0,652, entero por encima de
0,30. Se queda «en duda» por una sola variante compartida de menos. Lo mismo le pasa a la madre G con
DJ30 (J = 0,1154 = banda).

### 3.6 El estado de cada pareja

`verdict/call.py:6-29`. La tabla completa de C en `build`:

| Mercado | n ef. | rho bruto | rho sin exp. | inferior | superior | k | solape | J | banda | Estado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| USA500 | 302 | 0,017 | −0,046 | −0,158 | 0,067 | 31 | 2 | 0,033 | 0,127 | suspende |
| USATEC | 280 | −0,167 | −0,011 | −0,128 | 0,106 | 28 | 0 | 0 | 0,120 | suspende |
| DJ30 | 292 | −0,204 | −0,136 | −0,247 | −0,021 | 30 | 1 | 0,017 | 0,111 | suspende |
| DAX40 | 301 | 0,598 | 0,602 | 0,524 | 0,669 | 31 | 5 | 0,088 | 0,127 | en duda |
| UK100 | 295 | 0,281 | 0,343 | 0,238 | 0,440 | 30 | 0 | 0 | 0,111 | en duda |
| HK50 | 241 | 0,554 | 0,225 | 0,101 | 0,342 | 25 | 4 | 0,087 | 0,136 | en duda |
| USDJPY | 320 | 0,623 | 0,620 | 0,548 | 0,684 | 32 | 11 | 0,208 | 0,123 | **aprueba** |
| AUS200 | 235 | 0,631 | 0,504 | 0,402 | 0,594 | 24 | 0 | 0 | 0,116 | en duda |
| XAUUSD | 311 | 0,154 | −0,268 | −0,368 | −0,162 | 32 | 0 | 0 | 0,123 | suspende |
| EURUSD | 318 | 0,591 | 0,584 | 0,507 | 0,652 | 32 | 7 | 0,123 | 0,123 | en duda |
| XCUUSD | 316 | 0,271 | 0,227 | 0,120 | 0,329 | 32 | 0 | 0 | 0,123 | en duda |

Cómo leerla:

- **USDJPY aprueba:** inferior 0,548 > 0,30 y J 0,208 > 0,123.
- **DAX40, AUS200 y EURUSD** tienen el intervalo entero por encima de 0,30 pero no comparten bastante
  decil. AUS200 tiene un rho de 0,50 y **ni una** variante compartida en el 10 % mejor: el orden
  general se parece y la cima no.
- **UK100, HK50 y XCUUSD** tienen el 0,30 dentro del intervalo: ni sí ni no.
- **USA500, USATEC, DJ30 y XAUUSD** tienen el intervalo entero por debajo de 0,30.
- **XAUUSD** es el caso inverso a G-HK50: bruto +0,154, sin exposición −0,268.

Total de C en `build`: 1 aprueba, 6 en duda, 4 suspenden.

Casos límite que el código resuelve sin avisar:

| Caso | Qué hace | Ejemplo real |
|---|---|---|
| n = 3 | rho = 1,0; J = 1,0; banda = 1,0 → «en duda» | `19.2.363`, USDJPY y EURUSD, `build` |
| n = 1 | rho sin dato → «en duda» | `19.2.363`, USDJPY, `oos1` |
| n = 0 | la fila **desaparece** de la tabla de lectura | `19.2.363`, EURUSD, `oos1` |

Un «sin dato» nunca es mayor ni menor que nada, así que cae siempre en «en duda». El caso de n = 0 se
debe a cómo se junta la tabla con la columna «Madre (%)» (`one.py:118-119`): el mercado sin ninguna
celda utilizable se cae. Por eso `oos1` tiene 109 parejas y no 110. El aviso `market_absent` (`one.py:144-148`) no lo
cubre: sólo avisa de los mercados ausentes del lote entero. El veredicto no se sesga, porque el
divisor de la llamada sigue siendo el de los declarados; lo que pasa es que la tabla oculta el caso.

### 3.7 «Madre (%)»: dónde cae la madre entre sus variantes

`one.py:26-41`. En cada mercado y tramo:

```
Madre (%) = 100 × parte de las variantes utilizables con beneficio MENOR que el de la madre
```

Un 76 quiere decir que la madre gana más que el 76 % de sus variantes en ese mercado. Se calcula sobre
todas las utilizables, sin quitar repetidas. No decide nada.

La madre en el **principal**:

| Madre | `build` | `oos1` |
|---|---:|---:|
| `10.11.484` | 78,3 | 61,2 |
| `13.3.390` | 22,1 | 80,0 |
| C `14.3.479` | 69,2 | 81,6 |
| F `15.9.352` | 79,8 | 74,4 |
| `16.5.352` | 39,3 | 75,7 |
| `18.5.355` | 74,5 | 32,5 |
| `19.2.363` | 52,7 | 70,7 |
| E `3.11.426` | 58,0 | 86,3 |
| `3.9.284` | 78,4 | 69,4 |
| G `4.13.338` | 96,7 | 74,4 |

Sólo G está en el decil superior de su propio lote en `build`. En los demás mercados, la mediana de
«Madre (%)» es 58,6 en `build` y 56,0 en `oos1`: la madre queda un poco por encima de la mitad.

Para hacerse una idea del tamaño de lo que hay detrás, el beneficio neto de la madre C en `build`, en
dólares: NIKKEI 13.239 · DJ30 12.079 · USATEC 8.325 · EURUSD 6.642 · XAUUSD 4.516 · HK50 3.719 · DAX40
1.869 · USDJPY 1.542 · USA500 −1.501 · AUS200 −8.205 · UK100 −18.877 · XCUUSD −49.825. Estas cifras no
entran en ninguna decisión del paso: aquí sólo cuenta el orden.

### 3.8 La llamada de la madre

`verdict/call.py:48-75`. Con C:

```
build:  aprueban 1 de 11  ->  1 / 11 = 0,09  ->  ¿llega a 0,5?  No
oos1:   aprueban 1 de 11  ->  0,09           ->  No   (DAX40)
oos2:   aprueban 0 de 11  ->  0              ->  No

ningún tramo llega  ->  «La región no viaja»  ->  estado fail
```

Fíjate en que el mercado que aprueba en `build` (USDJPY) no es el que aprueba en `oos1` (DAX40). En
`oos1`, USDJPY tiene un rho bruto de −0,305.

### 3.9 Los lifts y los dos hechos del resumen

`one.py:44-80`, `measure/lift.py`, `contract/criteria.py:77-83`. La pestaña se titula «Métricas para
criterios — sin umbral todavía». Escribe dos números por tramo en el resumen:

- `lift_Jaccard_mediano_<tramo>`: la mediana, entre mercados, del lift (sección 2.9).
- `exceso_madre_en_top_<tramo>`: el exceso de la madre (sección 2.9).

Un mercado con menos de 10 variantes distintas en común queda fuera (`lift.py`, `MIN_VARIANTS = 10`).

Para C en `build`, mercado a mercado: USDJPY tiene J = 0,2075 contra un azar de 0,0596, lift 3,48. Pero
en los 1.000 sorteos sin ventaja, el lift de USDJPY va de 0 a 3,87 (percentiles 5 y 95). Es decir: un
lift de 3,48 **cabe dentro de lo que da el azar** cuando el azar respeta el parecido entre variantes.
EURUSD tiene lift 2,05 y DAX40 1,46.

Las diez madres (lift mediano y exceso de la madre):

| Madre | lift `build` | exceso `build` | lift `oos1` | exceso `oos1` | lift `oos2` | exceso `oos2` |
|---|---:|---:|---:|---:|---:|---:|
| `10.11.484` | 0,57 | +0,11 | 0,43 | +0,01 | 0,39 | +0,10 |
| `13.3.390` | 0,00 | +0,03 | 0,29 | +0,04 | sin dato | sin dato |
| C `14.3.479` | 0,22 | −0,08 | 0,46 | −0,01 | 0,34 | +0,09 |
| F `15.9.352` | 0,31 | −0,07 | 0,35 | −0,07 | 1,41 | +0,20 |
| `16.5.352` | 0,82 | −0,11 | 0,85 | 0,00 | 1,02 | +0,10 |
| `18.5.355` | 0,58 | 0,00 | 0,79 | +0,20 | 0,69 | +0,04 |
| `19.2.363` | 0,83 | −0,04 | 0,00 | +0,08 | 0,85 | −0,06 |
| E `3.11.426` | 1,08 | −0,09 | 0,88 | +0,14 | 0,86 | +0,20 |
| `3.9.284` | 0,62 | +0,36 | 0,46 | +0,09 | 0,00 | −0,09 |
| G `4.13.338` | 0,56 | +0,08 | 0,33 | +0,28 | 0,60 | +0,08 |

(`oos2` copiado de lo que el paso escribió; no recalculado.)

Lectura: el lift mediano está por debajo de 1 en 26 de las 29 casillas con dato, **pero eso no quiere
decir «menos que el azar»**. El lift divide por la **media** de un azar muy asimétrico
(`lift.py:57-60`): la mayoría de los sorteos dan poco o nada y unos pocos dan mucho, así que la media
queda por encima de lo que sale normalmente. Sin ventaja ninguna, la mediana entre mercados vale de
0,32 a 0,76 y queda por debajo de 1 en el 78-98 % de los sorteos (medición del revisor). Lo observado
es **compatible con el azar; no indica menos**. El
manual ya lo había anotado para el Nikkei («la mediana del lift real queda en 0,4–0,6»). El exceso de
la madre supera con holgura el percentil 95 de los sorteos en dos de las veinte casillas de `build`
y `oos1` (`3.9.284` en `build`: +0,36 contra 0,18; G en `oos1`: +0,28 contra 0,19) y queda justo en ese
percentil en otras dos (`18.5.355` y E, las dos en `oos1`). Con veinte casillas, una por azar es lo
esperable.

### 3.10 Las comprobaciones

`measure/verify.py`. Tres controles que se escriben en `checks.csv`:

| Control | Qué comprueba | Listón |
|---|---|---|
| curva = beneficio | la suma de los días de cada variante ordena igual que su beneficio neto | Spearman ≥ 0,99 (`verify.py:15`) |
| C3 = superficie | la superficie del principal es la misma que usan WFC y CSCV | exacto |
| diagonal | cada mercado contra sí mismo da rho = 1 y J = 1 | exacto |

El primero es lo que da validez al segundo contraste (el de voltear días): comprueba que los días
sumados reproducen el beneficio. En C todos pasan; en DAX40 el 88 % de las variantes cuadra al dólar y
el orden coincide en 0,9999998.

### 3.11 Lo que se pinta y no decide

| Pieza | Qué es | Dónde |
|---|---|---|
| Rejillas | para cada par de parámetros, la mediana del beneficio en cada casilla, por mercado | `contract/grids.py:23-26` |
| Consenso | en cuántos mercados una casilla está en el 10 % mejor de ese mercado | `contract/grids.py:96-121` |
| Meseta / región | las variantes a 2 pasos o menos de la madre en **todos** los parámetros a la vez y con beneficio en `build` no más de un 20 % por debajo del suyo | `measure/region.py:32-64` |
| Dentro / fuera | cómo les va en cada mercado a las de la meseta frente al resto | `measure/region.py:87-115` |
| Parejas entre mercados | las 55 parejas que no tocan el principal | `measure/pairs.py:138-155` |

La meseta merece una nota. Su tamaño en esta corrida, en variantes, madre incluida:

```
10.11.484: 1    13.3.390: 1    C: 2    F: 4    16.5.352: 1
18.5.355:  1    19.2.363: 1    E: 2    3.9.284:  1    G: 1
```

Con entre 6 y 17 parámetros por estrategia, pedir «a 2 pasos en todos a la vez» deja a la madre casi
sola. La pestaña «región» compara, pues, de 1 a 4 variantes contra varios cientos.

### 3.12 Qué escribe

En `…/Strategy_<x>/estudios/`:

| Fichero | Contenido |
|---|---|
| `marketSurfaces.json` | el resultado entero, con todas las pestañas (de 14 a 299 MB por madre) |
| `marketSurfaces.html`, `.md` | lo mismo para leer |
| `pairs.csv` | una fila por pareja y tramo, con todo lo de la sección 3.3 a 3.6 |
| `checks.csv` | las comprobaciones |
| `verdict.csv` | la llamada de la madre, en una línea |

Y una fila por tramo en el registro global de búsquedas (`report.py:20-53`), con el texto
«marketSurfaces: 12 mercados (principal + 11 de 11 declarados) × N variantes, NetProfit; k pasan» y
con entradas iguales a salidas: el paso no quita a nadie.

Antes de leer cada tramo pregunta al portero (`report.py:72-73`, `gate.allow`). `oos2` está permitido para
este estudio por la política (`assets/_policy.yaml:48`).

### 3.13 Qué números serían «hechos» si llegaran al piloto

Hoy no llega ninguno (sección 5.2). Pero he pasado un resultado real por la función que los
convertiría (`facts.flatten`), y esto es lo que saldría, con los valores de C:

| Clave | Valor en C | Qué es |
|---|---:|---|
| `marketSurfaces.verdict.pass` | 0 | 1 sólo si «La región viaja» |
| `marketSurfaces.summary.declared` | 11 | mercados declarados |
| `marketSurfaces.summary.markets` | 12 | principal + presentes |
| `marketSurfaces.summary.variants` | 417 | variantes del lote |
| `marketSurfaces.summary.costs_provisional` | 0 | marca de costes provisionales |
| `marketSurfaces.summary.lift_jaccard_mediano_build` | 0,2206 | sección 3.9 |
| `marketSurfaces.summary.exceso_madre_en_top_build` | −0,0815 | sección 3.9 |
| `marketSurfaces.verdict.usdjpy_build` | 0,6234 | Spearman **bruto** de esa pareja |
| `…lectura.principal_contra_cada_mercado_build.usa500.spearman_sin_exposicion` | −0,0460 | el que decide |

Tres huecos, aunque se arreglara la recogida:

- **El número de mercados que aprueban por tramo no saldría.** Está en el resumen como una lista
  (`passed`), y la función sólo recoge números sueltos.
- **La tabla de lectura sólo saldría para `build`**, que es la vista por defecto. Los Spearman sin
  exposición de `oos1` y `oos2` no serían hechos.
- **El estado de cada pareja no saldría:** es texto.

---

## 4. El criterio cargado y por qué

### 4.1 Lo que hay

```
criteria.yaml, paso "18.5":   nada
                              (el comentario de la línea 58 enumera los pasos que «sólo anotan»:
                               17, 18, 19, 21, 23, 24.  El 18.5 ni se nombra.)

el estudio, por dentro:       pareja aprueba  si  inferior(rho sin exposición) > 0,30
                                              y   J > banda del 97,5 %
                              pareja suspende si  superior(rho sin exposición) < 0,30
                              madre: la mitad de los declarados, en cada tramo, en los tres tramos

paso 20:                      sin_fallo  ->  superficies en fail = «No pasa»
```

### 4.2 De dónde sale cada umbral

| Umbral | Razón escrita en `ledger/thresholds.yaml` | Comentario |
|---|---|---|
| suelo 0,30 | «el mismo suelo que el WFC y por la misma razón: por debajo de 0,30 dos rankings comparten menos del 9 % de su varianza. Fijado antes de mirar ningún lote» | 0,30 × 0,30 = 0,09. Es una convención, no una medición sobre tus datos. |
| banda 97,5 % | «percentil del Jaccard de dos órdenes independientes… Optimista: el diseño agrupa variantes y el nulo real es más ancho» | El propio texto dice que se queda corto. |
| mitad de los mercados | «PROVISIONAL hasta que el dueño lo fije» | Sin razón estadística escrita. |

Los tres los firma «agente». El 0,30 se fijó antes de ver ningún lote, lo cual es bueno: no está
ajustado a los resultados.

### 4.3 Qué cambia al mover cada pieza

Calculado por mí sobre las diez madres, **sólo con `build` y `oos1`** (no he reabierto `oos2`). Las
columnas de madres están, por tanto, del lado optimista: la regla real exige además `oos2`, donde C y
F tienen 0 aprobados. No son hechos; son la regla del código con un número cambiado.

| Variante de la regla | Parejas que aprueban (`build` / `oos1`) | Madres «viaja» | Madres «no viaja» |
|---|---:|---:|---:|
| **La cargada hoy** | 6 / 3 | 0 | 10 |
| Decidir con el rho bruto | 5 / 2 | 0 | 10 |
| Sin la pata del Jaccard | 22 / 6 | 0 | 10 |
| Suelo 0,20 | 8 / 4 | 0 | 10 |
| Suelo 0,10 | — | 0 | 10 |
| Suelo 0 | 10 / 9 | 0 | 10 |
| Suelo 0 y sin Jaccard | 68 / 30 | 2 | 2 |
| Mitad → una cuarta parte (3 de 11) | 6 / 3 | 0 | 10 |
| Mitad → 2 de 11 | 6 / 3 | 0 | 9 |
| Mitad → 1 de 11 | 6 / 3 | 2 (C y F); 0 contando `oos2` | 4 |
| Suelo 0, sin Jaccard y una cuarta parte | 68 / 30 | 4 | 0 |

Lo que dice la tabla:

- **Ningún umbral por sí solo cambia el resultado.** Bajar el suelo hasta cero, quitar el Jaccard o
  cambiar de rho deja las diez igual. El máximo de aprobados en un tramo sin la pata del Jaccard es 5
  en `build` y 2 en `oos1`; hacen falta 6.
- Para que salga alguna madre hay que aflojar dos o tres piezas a la vez, o bajar el requisito a «un
  mercado de once».
- **«Un mercado de once» es ruido, no una opción.** C y F tienen 0 aprobados en `oos2` (sección 6.2),
  así que con los tres tramos no «viaja» ninguna. Y sin ventaja ninguna, C alcanza 1 o más en `build`
  el 61 % de las veces (sección 4.4).
- El resultado de esta corrida no es cosa del afinado de los umbrales. Es que en `oos1` el acuerdo es
  prácticamente nulo (siguiente apartado).

Cuántas parejas cumplen cada pata:

| | `build` (110) | `oos1` (109) |
|---|---:|---:|
| las dos patas (aprueba) | 6 | 3 |
| sólo la del rho | 16 | 3 |
| sólo la del Jaccard | 8 | 8 |
| ninguna | 80 | 95 |

### 4.4 Qué saca la regla cuando no hay nada (calculado por mí; no es un hecho)

El módulo no mide esto. Lo he medido aplicando su propio segundo contraste (voltear días, misma
semilla, 1.000 sorteos) a la regla entera: dejo la superficie del principal como está, volteo los días
del otro mercado —con lo que ese mercado se queda sin ventaja ninguna, pero sus variantes siguen
pareciéndose entre sí— y paso la pareja por la regla.

**Lo que baila el rho cuando no hay nada:**

```
lo que supone el intervalo de Fisher:   desviación de 0,056 (build) y 0,062 (oos1)
lo que sale en los sorteos:             desviación de 0,22
cociente:                               3,6 veces de mediana (entre 1,5 y 8,1 según la pareja)

rho sin exposición con ventaja cero:    entre −0,39 y +0,40 el 95 % de las veces
```

Es decir: un Spearman de 0,35 entre dos mercados, con estos lotes, es algo que el puro azar da con
frecuencia. El intervalo que usa la regla es 3,6 veces demasiado estrecho.

El revisor rehízo esta cuenta en 4 de las 10 madres y la confirma. Añade un apoyo: la dispersión
**observada** del rho sin exposición entre parejas es 0,23 en los dos tramos, la misma que da el azar.
Y un aviso: esta anchura está medida con ventaja cero (rho = 0); trasladarla a un rho de 0,30 es una
aproximación.


**Qué estados salen por pareja cuando no hay nada, frente a lo observado:**

| | aprueba | en duda | suspende |
|---|---:|---:|---:|
| `build`, sin ventaja | 2,3 % | 16,6 % | 81,1 % |
| `build`, observado | 5,5 % | 40,0 % | 54,5 % |
| `oos1`, sin ventaja | 1,4 % | 18,6 % | 80,1 % |
| `oos1`, observado | 2,8 % | 20,2 % | 77,1 % |

- **En `oos1` lo observado es casi idéntico a lo que da el azar.** Las tres parejas que aprueban son
  compatibles con las 1,5 que se esperan por azar entre las diez madres.
- **En `build` hay algo más:** el doble de «en duda» y menos «suspende». El rho sin exposición medio
  por madre es +0,17 y es positivo en las diez. Pero `build` es el tramo en el que se construyó la
  madre.
- En `oos1` el rho sin exposición medio por madre es +0,012, positivo en 6 de 10. Nada.

Las tasas «sin ventaja» de la tabla son **medias** sobre parejas. Por pareja van del 0 % (las de
`13.3.390`) a entre el 5 y el 11 % (las de C en `build`).

Cada pata por separado, sin ventaja: la del rho se cumple el 4,8 % de las veces en `build` (2,9 % en
`oos1`) y la del Jaccard el **16,1 %** (13,4 %), cuando su nombre promete un 2,5 %.

**Y a nivel de madre:**

```
aprobados esperados por azar entre 11 mercados:   menos de 0,5 en todas salvo C en build
  (C en build: 0,95; probabilidad de 1 o más: 61 %; de 2 o más: 24 %; de 3 o más: 7 %)

veces que el azar llegó a 6 de 11:   0 de 1.000 sorteos por madre y tramo (menos del 0,3 %)
                                     el máximo fue 5 (C en build)
```

No son 20.000 sorteos independientes: la semilla es la misma y las fechas coinciden entre madres
(2.185 días en `build`, 1.088 en `oos1`). Son 1.000 sorteos por tramo aplicados a las diez madres.

**Resumen de este apartado, en claro:**

1. A nivel de pareja la regla es **floja**: aprueba por azar más de lo que promete, y un «aprueba»
   suelto (como USDJPY en C) no demuestra nada. Lo observado en C, 1 de 11, es justo lo esperado sin
   ventaja.
2. A nivel de pareja el «suspende» también está **inflado**: con un intervalo honrado, a 300 variantes
   haría falta un rho por debajo de −0,10 para afirmar que está por debajo de 0,30, y no por debajo de
   +0,19 como ahora. Muchas de las parejas «suspende» son en realidad «no se sabe».
3. A nivel de madre la regla es **durísima**: el azar no la pasó en ninguno de los 1.000 sorteos. Eso
   está bien para no dejar pasar basura.
4. **Y tampoco la pasa lo que debería pasarla seguro** (medición del revisor, no mía). Hay dos
   controles positivos dentro de los propios datos, y los dos suspenden:
   - **El NIKKEI contra sí mismo** (`build` frente a `oos1`, las mismas variantes): pasa la regla de
     pareja en 1 de 10 madres; rho sin exposición mediano, 0,13.
   - **USA500, USATEC y DJ30 entre sí**, tres índices casi iguales: aprueban 3 de 60 parejas; rho
     sin exposición mediano, 0,12 y 0,08.

   Si ni el principal contra sí mismo ni tres índices casi iguales pasan la regla de pareja, 6 de 11
   en tres tramos es inalcanzable con estos lotes. **El «fail» no informa:** sale lo mismo haya región
   que viaje o no la haya. Lo que sigue sin medir es la potencia en regla: qué rho cabe esperar entre
   el Nikkei y el cobre cuando la región viaja de verdad.

Límites de esta medición mía: el azar que uso deja el principal como está y supone ventaja cero en el
otro mercado; es una extensión del contraste del módulo al rho, no algo que el código haga; y las diez
madres y los once mercados no son independientes entre sí, así que la comparación «observado contra
esperado» no lleva un valor p formal.

### 4.5 Los dos contrastes del Jaccard no dicen lo mismo

Medido sobre 216 parejas de `build` y `oos1`:

| | Jaccard medio por azar | percentil 97,5 del azar |
|---|---:|---:|
| La urna (la que decide) | 0,053 | 0,119 |
| Voltear días (la del propio módulo) | 0,066 | 0,233 |

La banda con la que se decide es la mitad de alta que la del contraste que respeta el parecido entre
variantes. De las 25 parejas que superan la banda de la urna, **sólo 2** superan la otra.

Tómalo como orden de magnitud, no como prueba: por construcción el azar ya daría unas 5 de 216 por
encima de esa segunda banda, su percentil 97,5 se apoya en los 25 sorteos más altos de 1.000 y el
Jaccard va a saltos.

---

## 5. Lo que no cuadra o no está medido

### 5.1 Se decide con un rho y se enseña otro

- **Código:** `verdict/call.py:25,27` decide con `rho_neutral_lo` y `rho_neutral_hi`.
- **Lo que se enseña:** las barras de la pestaña de lectura pintan el rho **bruto**, su intervalo
  bruto, la línea del suelo y el color del estado (`contract/tabs.py:77-82`). Las partes del veredicto
  llevan el rho bruto como valor (`one.py:184`).
- **Lo que dicen los textos:** el manual, cap. 52, líneas 123-128: «La llamada usa el rho bruto (la
  métrica del WFC, como pediste)». `POSSIBLE_IMPROVEMENTS.md`: «the call stays on raw». El `README.md`
  del módulo (línea 71) sí dice que es el neutral. El comentario de `rho_floor` en `config.yaml` no
  dice cuál.
- **Efecto visible:** G contra HK50 en `build` tiene la barra entera por encima del suelo (0,241 a
  0,477) y está en rojo.
- Si en algún momento pediste que se decidiera con el bruto, hoy no se hace.

### 5.2 Ningún hecho del 18.5 llega al piloto

- `pipeline/autopilot/tail.py:8` y `107-110`: el 18.5 se planifica como acción «a ciegas». Se calcula
  y no se juzga.
- `pipeline/autopilot/facts.py:221-222` (función `gather`): sólo acepta resultados que sean
  **carpetas**. Los del 18.5 son ficheros: `ui/daemon/workflow/steps.py:59-60` lista
  `["marketSurfaces"]` para el paso y `ui/daemon/workflow/sources.py:84-85` devuelve
  `…/estudios/marketSurfaces.json`. Recoge cero hechos. La ayuda de `--step` dice «paso que juzga: 8,
  10, 12, 14 o 16» (`facts.py:237`).
- `criteria.yaml` sólo tiene entradas para los pasos 8, 10, 11.5, 12, 14 y 16. Para cualquier otro,
  `pipeline/autopilot/judge.py:172-173` devuelve «ninguno: el paso no tiene criterio». El paso 20 no
  tiene `cut` y `blindJoint` no aplica su veredicto: el «DESCARTAR» se queda en el `verdict.csv`.
- El `hechos.parquet` del paso 20 de esta corrida tiene 10 claves `blindJoint.*` por madre y ninguna
  del 18 ni del 18.5.
- **Consecuencia:** una regla `"18.5"` escrita hoy en `criteria.yaml` no se juzgaría; y si se juzgara,
  le faltarían los hechos y, por tu doctrina, un hecho que falta es Limbo: las diez al Limbo.

### 5.3 «9 mercados de la misma familia», escrito a fuego

- `one.py:163-166`: el aviso `family_only` sale **siempre**, con el texto «Los 9 mercados son de la
  misma familia macro que el principal (`_markets.yaml`, sin structural)».
- `contract/tabs.py:8-11` (es el texto de costes, no el aviso de familia): «los 9 pares y el
  principal».
- `docs/AgentPDFs/WORKFLOW.md:48` y el manual (cap. 52, líneas 14, 111-116 y 255): «los 9 mercados»,
  «Nada estructural».
- **Realidad en esta corrida:** 11 declarados, 3 estructurales. El texto viene de cuando el principal
  era USDJPY.

### 5.4 «Costes provisionales», también a fuego

- Sólo el aviso `costs_provisional` es condicional (`one.py:141-143`). El texto de costes
  (`contract/tabs.py:8-11`) se pega siempre:
- `one.py:188` añade la frase de costes provisionales al significado del veredicto **siempre**;
  `contract/tabs.py:85` la añade a la descripción de la pestaña **siempre**.
- La marca real (`costs_provisional`) es `false` en las diez madres: ningún coste de los 12 símbolos
  tiene hoy un «por qué» que empiece por «PROVISIONAL».
- `WORKFLOW.md:48` sigue avisando de «comisión CERO».
- **No verificado:** con qué costes se retestaron de verdad las variantes en los once mercados. Eso
  está dentro de SQX y no lo he abierto. Sólo he leído la marca de la ficha.

### 5.5 El `README.md` dice que `oos2` no se abre

- `README.md:52-55`: «`oos2` is never opened… default `build` and `oos1`».
- `config.yaml:9`: `segments: [build, oos1, oos2]`. `report.py:72-73` pide paso al portero
  (`gate.allow`) para cada uno de los tres. La llamada exige los tres.
- La política lo permite (`assets/_policy.yaml:48`) y el manual lo dice bien. El `README.md` está
  viejo.
- **Para que lo tengas presente:** esta corrida ya leyó `oos2` para las diez madres en este paso.

### 5.6 El intervalo y la banda son optimistas, y el código lo sabe

- Intervalo de Fisher sobre n efectivo (`pairs.py:122`): unas 3,6 veces demasiado estrecho (sección
  4.4, calculado por mí).
- `n_eff` sólo quita repeticiones exactas (`core/surface/dedupe.py:52`); el texto de su función habla
  de «autocorrelación», que no trata.
- Banda del Jaccard por urna (`pairs.py:86-88`): la mitad de la del contraste propio del módulo
  (sección 4.5).
- `config.yaml`, `thresholds.yaml` y `POSSIBLE_IMPROVEMENTS.md` («The null is too narrow») lo admiten.
- El contraste bueno ya existe en el módulo (`measure/lift.py`), pero no está enchufado a la decisión.

### 5.7 Filas que desaparecen y parejas con tres variantes

- `one.py:118-119`: un mercado sin ninguna celda utilizable se cae de la tabla sin aviso.
- Parejas con n = 1 o n = 3 salen «en duda» con rho = 1,0 (sección 3.6). No hay un mínimo de variantes
  para leer una pareja en la decisión; sí lo hay (10) para los lifts.

### 5.8 El «mayor que» estricto de la banda

- `verdict/call.py:25`: `j > j_hi`. Como el solape es entero, el nivel real es del 0,8 % al 1,9 %, no
  del 2,5 % (sección 2.8).
- Dos parejas de la corrida se quedan «en duda» por estar exactamente en la banda (C-EURUSD y
  G-DJ30).

### 5.9 Los suelos de operaciones, en los comentarios

- `engines/variants/config.yaml:6`: «50 operaciones en TOTAL». El valor real es 100
  (`assets/_build.yaml:368`; el 16.5 escribe `"floor": 100`).
- El mismo fichero dice que «30 es el suelo que usa el propio SQX»; el valor es 50.

### 5.10 El coste del paso

- `README.md:46-48`: «9-11 s… 5.000 variantes × 10 mercados».
- Real: unas 500 variantes × 12 mercados; 245 segundos en la madre C; el JSON llega a 299 MB.
  `pipeline/autopilot/blind.py` habla de «~13 MB de entrada» y de 570 segundos para el paso.
- El paso 20 carga ese JSON entero sólo para leer una palabra (`blindJoint/pieces.py:45-60`).

### 5.11 «La región» no es lo que se mide

- El titular dice «La región viaja». La decisión mira el orden de todas las variantes y el 10 % mejor
  (sección 2.10).
- La meseta alrededor de la madre tiene de 1 a 4 variantes (sección 3.11) y no decide.
- No está medido si las variantes del 10 % mejor están cerca unas de otras en el espacio de
  parámetros (una «región») o desperdigadas.

### 5.12 Mercados que son casi el mismo cuentan como tres

- El encabezado de `assets/_markets.yaml` dice que los mercados casi idénticos cuentan como uno («13
  pares son unos 5-6 mercados independientes»).
- La llamada cuenta USA500, USATEC y DJ30 como tres votos de once.
- **Cuánto pesa, medido por el revisor:** sin ventaja, el rho de un mercado y el de otro apenas van
  juntos (correlación 0,02 de mediana; entre los tres índices de EE. UU., de 0,15 a 0,43). Salen unos
  10 mercados efectivos de 11 y los aprobados se reparten como si fueran independientes. **Sin
  ventaja, unos 10 independientes; con ventaja real, no medido.**
- Curiosidad medida: en esta corrida las superficies del trío entre sí se parecen poco (rho mediano
  0,08 en `build` y 0,11 en `oos1`), menos que la mediana de todas las parejas entre mercados (0,25 y
  0,13).

### 5.13 El contraste de voltear días se calcula también en `build`

- Tu doctrina: el trader al azar y sus contrastes, sólo en OOS, nunca en el IS.
- `one.py:44-80` calcula los lifts para todos los tramos de la configuración, `build` incluido, y
  escribe `lift_Jaccard_mediano_build` y `exceso_madre_en_top_build` en el resumen.
- No es exactamente un trader al azar (no sortea entradas: voltea días), pero es un contraste de azar
  sobre el tramo de construcción. Te toca decir si entra en tu regla.

### 5.14 Pequeñas

- `measure/pairs.py:29-53` cita un ejemplo «−0,70 bruto y −0,39»; el `README.md` cita «−0,87 bruto»
  para lo mismo.
- `criteria.yaml:58` no nombra el 18.5 entre los pasos que sólo anotan.
- El glosario dice que el Jaccard por azar «sale en torno a 0,05»; es 0,053 con la urna y 0,066 con el
  contraste propio.

### 5.15 No medido

- **La potencia de la regla, en regla:** con qué frecuencia una madre cuya región viaja de verdad
  llegaría a 6 de 11 en los tres tramos. Lo que sí hay son dos controles positivos, y los dos
  suspenden (medición del revisor; sección 4.4, punto 4): el NIKKEI contra sí mismo pasa en 1 de 10
  madres y los tres índices de EE. UU. entre sí en 3 de 60 parejas. Con eso, «no medido» se queda
  corto: lo razonable es dar la potencia por cercana a cero.
- **Qué rho cabe esperar entre el Nikkei y cada mercado cuando la región viaja.** Sin eso, 0,30 es una
  convención.
- **Si el paso predice algo:** si las madres con mejor acuerdo entre mercados aguantan mejor después.
  Con diez madres, todas en «fail», no se puede medir aquí.
- **`oos2` no lo he recalculado.**
- **El orden exacto en que corrió el paso 20 respecto a estos ficheros.** `pairs.csv` es de las 22:28
  y `marketSurfaces.json` se reescribió entre las 23:09 y las 23:25 del mismo día. No he comprobado
  que el JSON que leyó el paso 20 tuviera los mismos estados; los `pairs.csv` y el JSON actual sí
  coinciden entre sí.

---

## 6. Cierre

### 6.1 La tabla de reglas

| Nivel | Regla hoy | Umbral | Quién lo puso | Lo usa |
|---|---|---|---|---|
| celda | cuenta si tiene operaciones suficientes | ≥ 50 | configuración del lote | el estudio |
| pareja | aprueba si inferior(rho sin exposición) > suelo **y** J > banda | 0,30 · 97,5 % | agente | el estudio |
| pareja | suspende si superior(rho sin exposición) < suelo | 0,30 | agente | el estudio |
| madre | cada tramo: aprobados / declarados ≥ parte mínima | 0,5 (6 de 11) | agente, provisional | el estudio |
| madre | «viaja» si llegan los tres tramos; «no viaja» si ninguno | — | código | el estudio |
| paso 20 | ninguna pieza en «fail» | `sin_fallo` | tú, 2026-10-04 | lectura conjunta: marca DESCARTAR; el autopiloto no lo aplica |
| piloto | regla del paso 18.5 | **no hay** | — | nadie |

### 6.2 El resultado sobre la población real

Aprobados de 11, por tramo:

| Madre | `build` | `oos1` | `oos2` | Llamada |
|---|---:|---:|---:|---|
| `10.11.484` | 0 | 1 | 1 | no viaja |
| `13.3.390` | 0 | 0 | 0 | no viaja |
| C `14.3.479` | 1 | 1 | 0 | no viaja |
| F `15.9.352` | 1 | 1 | 0 | no viaja |
| `16.5.352` | 0 | 0 | 0 | no viaja |
| `18.5.355` | 1 | 0 | 0 | no viaja |
| `19.2.363` | 0 | 0 | 0 | no viaja |
| E `3.11.426` | 0 | 0 | 0 | no viaja |
| `3.9.284` | 1 | 0 | 0 | no viaja |
| G `4.13.338` | 2 | 0 | 0 | no viaja |

Y las cuatro piezas en el paso 20 de esa corrida
(`AlgoData/reports/Trade_NIKKEI225_M30_volatilidadL/WFM/2026-10-04/blindJoint/verdict.csv`):

| Madre | WFC | CSCV | Superficies | WFM | Paso 20 |
|---|---|---|---|---|---|
| `10.11.484` | pasa | pasa | **falla** | en duda | DESCARTAR |
| `13.3.390` | falla | falla | falla | falla | DESCARTAR |
| C `14.3.479` | falla | pasa | falla | en duda | DESCARTAR |
| F `15.9.352` | falla | pasa | falla | pasa | DESCARTAR |
| `16.5.352` | falla | pasa | falla | en duda | DESCARTAR |
| `18.5.355` | falla | pasa | falla | falla | DESCARTAR |
| `19.2.363` | en duda | pasa | falla | falla | DESCARTAR |
| E `3.11.426` | falla | falla | falla | en duda | DESCARTAR |
| `3.9.284` | pasa | pasa | falla | falla | DESCARTAR |
| G `4.13.338` | pasa | pasa | falla | falla | DESCARTAR |

Superficies falla en 10 de 10. Es la **única** pieza que falla en 1 de 10 (`10.11.484`). Ninguna fue
cortada: el paso 20 marca «DESCARTAR» en su `verdict.csv`, pero el autopiloto no lo aplica y todas
siguen; sólo corta si se aplica a mano con `/curate`.

### 6.3 Las decisiones que te quedan

Cada una con lo que cuesta en estrategias **sobre estas diez madres**. Los costes en madres de las
decisiones 2 a 5 salen de la tabla de la sección 4.3 (`build` y `oos1`; calculado por mí).

| # | Decisión | Opciones | Coste en esta corrida |
|---|---|---|---|
| 1 | **¿Decide algo el 18.5, o sólo anota?** | (a) como hoy: su «fail» marca DESCARTAR en el paso 20 (que el autopiloto no aplica; corta sólo con `/curate`) · (b) sólo anota | (a) marca 10 de 10; es el único motivo en 1. (b) marca 0; `10.11.484` quedaría sin pieza en «fail». |
| 2 | **¿Con qué rho se decide?** | bruto (lo que dice el manual) · sin exposición (lo que hace el código) | 0 madres cambian. En parejas: 5 / 2 aprobados con el bruto contra 6 / 3. |
| 3 | **El suelo** | 0,30 · 0,20 · 0,10 · 0 | 0 madres cambian con ninguno. |
| 4 | **¿El Jaccard es requisito?** | sí · no | 0 madres cambian. Parejas: de 6 / 3 a 22 / 6. |
| 5 | **Cuántos mercados deben aprobar** | 6 de 11 · 3 · 2 · 1 | con 3: 0 cambian. Con 2: 1 madre sale de «no viaja». Con 1: 6 salen de «no viaja» en `build` y `oos1`, pero contando `oos2` no «viaja» ninguna, y ese umbral es ruido: C llega a 1 por azar el 61 % de las veces. |
| 6 | **Qué tramos cuentan** | los tres · sólo los OOS · sólo `oos1` | No medido para las madres. `build` es donde se construyó la madre; `oos2` es el tramo reservado y aquí se lee. |
| 7 | **Qué intervalo y qué banda** | Fisher y urna (hoy) · los del contraste de voltear días | No medido para las madres. Por parejas: de las 25 que superan la banda de hoy, 2 superarían la otra; y casi ninguna pareja «suspende» podría afirmarse. El otro lado: aprobar exigiría un rho observado de unos 0,63 (el z de 0,30 más 1,96 × 0,22), además de J > 0,233. La opción honrada **endurece aún más** la regla. |
| 8 | **Qué cuenta como un mercado** | 11 votos iguales · agrupar los casi iguales | Sin ventaja, los 11 valen por unos 10 independientes (medición del revisor); con ventaja real, no medido. |
| 9 | **Mínimo de variantes para leer una pareja** | ninguno (hoy) · un número | Afecta a 4 parejas de `19.2.363`; 0 madres cambian. |

Y dos arreglos que no son decisiones estadísticas pero condicionan todo lo demás:

- **Si quieres una regla del 18.5 en `criteria.yaml`**, antes hay que hacer que sus hechos lleguen
  (sección 5.2) y que el número de aprobados por tramo sea un hecho (sección 3.13).
- **Los tres textos fijos** («9 mercados», «misma familia», «costes provisionales») y las barras con
  el rho que no decide hacen que hoy la pantalla cuente una cosa distinta de la que el código hace.

Lo que la tabla dice en una frase: **en esta corrida ninguna decisión de umbral cambia nada, salvo la
número 1.** Lo que de verdad está en tu mano hoy es si un paso cuyo «fail» no informa —no lo pasa ni el
principal contra sí mismo— debe poder marcar a las diez para descarte.

### 6.4 El límite que no cambia

- **El paso compara órdenes, no dinero.** Que el orden de las variantes se repita en el DAX no dice
  que la estrategia gane en el DAX, ni que vaya a ganar en el Nikkei mañana.
- **Las variantes no son independientes.** Son la misma estrategia con los parámetros movidos.
  Cuatrocientos puntos valen por bastantes menos (por cuántos, no medido). Cualquier
  intervalo que las cuente una a una será optimista; el contraste de voltear días lo corrige en parte,
  no del todo.
- **Los mercados, casi.** Sin ventaja, los once votos valen por unos diez independientes (medición
  del revisor). Con ventaja real, cuando un mismo motivo empujaría a varios a la vez, no está medido.
- **Diez madres no calibran un umbral.** Cualquier número que se elija mirando estas diez queda
  ajustado a estas diez, y su `oos2` ya está leído en este paso.
- **Falta la otra mitad de la cuenta.** Se sabe lo que la regla hace cuando no hay nada: no pasó en
  ninguno de 1.000 sorteos. Y hay indicios fuertes de lo que hace cuando sí lo hay: tampoco pasa (el
  NIKKEI contra sí mismo, 1 de 10; tres índices casi iguales, 3 de 60 parejas; medición del revisor).
  Mientras sea así, «La región no viaja» quiere decir «no ha llegado a 6 de 11», y no «se ha
  demostrado que no viaja».
