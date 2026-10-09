# Criterios del paso 16.5 — la nube de parámetros

**Fecha:** 2026-10-07 · **Para:** el dueño · **Alcance:** el estudio `studies/optimisation/cloud/` (la
«nube de parámetros») y, del paso 16.5 que la alimenta (`sqx/variants/`), lo necesario para entender qué
variantes le llegan y cuáles no.

**Qué es este documento.** Un documento de consulta para que fijes tú los criterios. Dice qué calcula
exactamente el estudio, con qué matemática, qué números escribe, qué criterio hay cargado hoy y qué no
cuadra entre el código y lo que dicen sus textos. No propone un rediseño: describe lo que hay.

**De dónde salen los números.** Cada fórmula está leída en el código (se cita `fichero:línea`), no en el
README ni en el glosario. Los ejemplos reales son de la corrida `Trade_NIKKEI225_M30_volatilidadL`
(variantes fabricadas y nube escrita el 2026-10-04; diez madres), **recalculados por mí** con el propio
código del estudio sobre los ficheros de
`AlgoData/strategyPermutations/Trade_NIKKEI225_M30_volatilidadL/Strategy_<x>/`. Donde lo recalculado
coincide con lo guardado en `estudios/cloud.json` lo digo; donde un número no lo escribe el estudio y lo he
calculado aparte, lleva la marca «calculado por mí». Los ejemplos de juguete llevan la marca «Ilustrativo».
Las cuatro madres que el dossier del paso 16 llama C, E, F y G son aquí las mismas:
C = `14.3.479`, E = `3.11.426`, F = `15.9.352`, G = `4.13.338`.

**Ninguna línea de este documento está congelada.** No hay criterio escrito para este paso; lo que aquí
aparece como «umbral» es un umbral de diagnóstico que puso un agente el 2026-09-24 y que nadie ha
calibrado.

**Revisión.** Revisado por dos miembros del Council (Feynman, Taleb) el 2026-10-07; correcciones
aplicadas. Lo que comprobó el revisor y no yo lleva la marca «comprobado en la revisión».

---

## 0. En una página

### La pregunta del paso

El paso 16 (SPP) responde «¿la madre es un punto raro dentro de su rejilla de parámetros?» con una rejilla
que mueve los parámetros **en bloque** dentro de un rango. El 16.5 fabrica unas 500 **variantes** de cada
madre —la misma estrategia con otros valores de parámetros, elegidos con un diseño— y las vuelve a pasar
por SQX en los tres tramos (build, oos1, oos2). La nube lee esas variantes y pregunta cuatro cosas:

| lectura | pregunta | en una palabra |
|---|---|---|
| **A1** | ¿La madre está sola en lo alto (pico) o rodeada de vecinas parecidas (meseta)? | Pico / Meseta / Sin destacar |
| **A2** | ¿Qué parámetros mueven el resultado, solos o combinados? | (ranking, sin palabra) |
| **A3** | ¿La superficie alrededor de la madre es lisa o rugosa, y la madre está en lo alto o en la ladera? | Suave / Rugosa / Óptimo descentrado |
| **B2** | ¿La forma aguanta año a año: ganan casi todas las variantes, las mejores siguen siendo las mismas, la zona buena se queda quieta? | tres palabras |
| **C1** | ¿Operar una mezcla de K vecinas buenas rinde parecido a operar sólo la madre? | (una diferencia de Sharpe) |

### Lo que hay cargado hoy

**Nada que decida.**

- `pipeline/autopilot/criteria.yaml` tiene reglas para los pasos 8, 10, 11.5, 12, 14 y 16. **No hay entrada
  para el 16.5.**
- La nube **no escribe hechos**: de los 164 `hechos.parquet` que hay en disco, ninguno tiene una clave de
  la nube. `pipeline/autopilot/facts.py` sólo aplana los pasos 8, 10, 12, 14 y 16.
- **El autopiloto no la lanza.** El paso 16.5 del autopiloto fabrica y recoge las variantes
  (`pipeline/autopilot/variants.py:52-96`) y ahí termina; en `pipeline/` no hay ninguna llamada a la nube.
  Se lanza a mano desde la ventana o por línea de comandos.
- El veredicto del sobre que entrega es `None`. Las palabras («Pico», «Rugosa»…) son etiquetas de
  diagnóstico: `config.yaml` las llama «DIAGNOSTIC thresholds, not gates».
- **El paso 20** (la lectura conjunta) lee WFC, CSCV, superficies por mercado y WFM. **No lee la nube.**

Los únicos números con aspecto de criterio son ocho umbrales de diagnóstico (§4), tres de ellos en
`ledger/thresholds.yaml` con `set_by: agente`.

### Lo que sale en la corrida real

Diez madres, 500 variantes fabricadas por cada una.

| lectura | resultado en las diez madres |
|---|---|
| A1 (pico o meseta) | **«Sin dato» en las diez.** Ninguna variante cae dentro de la vecindad de la madre. |
| A3 (superficie) | **«Sin dato» en las diez**, por lo mismo. |
| C1 (mezcla) | **Vacía en las diez**: la «mezcla» es la madre sola, diferencia 0,000. |
| B2 (por años) | Se calcula y se guarda, **no se pinta**. En cinco madres hay como mucho un año legible. |
| A2 (quién manda) y mapas de calor | Lo único con contenido. En una madre (F) el ranking lo encabezan parámetros que el SPP dio por muertos. |

Lo único que la pestaña A1 enseña con dato es la fila «Nube entera», que **no** entra en la palabra.

### Las diez cosas que conviene saber

1. **El paso no decide nada hoy y no deja rastro en los hechos.** Una madre pasa por el 16.5 y sale igual
   que entró. Si quieres que cuente, hay que escribir la regla y además cablear el hecho.
2. **A1, A3 y C1 están vacías porque la vecindad se mide alrededor de la madre y el diseño pone las
   variantes densas alrededor de otro punto.** La nube llama vecinas a las variantes a 2 pasos o menos de
   la **madre** (`model/neighbourhood.py:22`). El diseño del 16.5 pone su estrato denso a 2 pasos del
   **centro de la meseta que encontró el SPP** (`sqx/variants/design/levels.py:109-122`,
   `design/strata.py:42-72`). En las cinco madres en que lo he medido (C, E, F, G y
   16.5.352) ese estrato queda a entre 9 y 45 pasos de la madre. **El problema es el centro, no la forma**:
   con el mismo centro, todo lo que está a 2 pasos sumados está también a 2 pasos en cada eje, y serían
   todas vecinas. Resultado: **0 variantes a 2 pasos o menos, en las diez madres**.
3. **«Un paso» no significa lo mismo en cada parámetro.** El README y `config.yaml:18-19` dicen que un paso
   es comparable entre parámetros. Ya no: un parámetro entero toma **todos** los enteros de su tramo
   (`levels.py:16-45`), así que un paso es «1 barra» en un periodo de 100 (un 1 %) y un 8 % en un
   multiplicador decimal con diez niveles.
4. **La lectura por años (B2) se calcula, se resume en tres palabras y no se enseña.** La pestaña se quitó
   el 2026-10-02; el cálculo y las palabras siguen en el JSON y en las columnas de la ventana. Y **las
   palabras se publican aunque no haya datos**: sin ningún año legible sale «Sostenida por periodos / Orden
   que se rebaraja / Deriva baja» (`verdict/call.py:82-85`). Es el caso de la madre C.
5. **«Superficie rugosa» se dispara con una de dos medidas, no con las dos.** Los textos dicen «sólo cuando
   las dos coinciden»; el código usa `or` (`call.py:58-59`). Hoy no se nota: con una
   vecindad de 1 punto la palabra es «Sin dato» antes de llegar ahí. Saldrían rugosas 5 de 10 con `or` y
   2 de 10 con `and` **si la regla se evaluara sobre el R² de la nube entera, que no es lo que el código
   hace** (calculado por mí; una de ellas entra por milésimas).
6. **El ranking de «quién manda» mezcla parámetros vivos con parámetros que el SPP congeló, y los
   congelados lo estropean.** Sólo se mueven en un estrato del diseño; la superficie no puede identificar
   bien sus términos cruzados y el Sobol los extrapola a todo el espacio. En F los dos primeros del
   ranking son congelados cuyos controles demuestran que no cambian nada en la madre. **Quitando las
   columnas congeladas, F da un ranking limpio** (comprobado en la revisión): el artefacto es del cálculo,
   no de la estrategia.
7. **La «compañía» (π) cuenta también a las variantes que superan a la madre.** El glosario dice «a menos
   de δ del punto elegido»; el código cuenta todo lo que esté por encima del suelo
   (`core/surface/plateau.py:128`). En C, de 148 «compañeras», 132 son mejores que la madre.
8. **El «valor encogido» es la mediana de la vecindad**, sin mezcla con el valor de la madre
   (`plateau.py:141`). No alimenta ninguna decisión; sólo se enseña en la pestaña A1
   (`contract.py:70`, `:110`).
9. **La nube miró `oos2` en esta corrida.** `WORKFLOW.md` dice que «corta las curvas donde empieza oos2».
   El código sólo corta si `ALGO_AUTONOMOUS=1` (`inputs/cloud.py:79-80`). La pone el autopiloto
   (`pipeline/autopilot/run.py:235`, desde el 2026-10-04), pero no una ejecución a mano ni desde la
   ventana, y el autopiloto no lanza la nube. Estas diez no cortaron; el motivo probable es ése. C1 enseña
   neto, Sharpe y caída de la madre con oos2 dentro, y B2 lee 2024-2026. No hay fila en el registro de
   miradas.
10. **Todo se mide sobre el Ret/DD del tramo de construcción.** A1, A2, A3 y los mapas leen
    `ReturnDDRatio (build)`: es una lectura **dentro de muestra**. Con la misma cuenta en oos1 el rango de
    varias madres cambia mucho (13.3.390: 0,36 en build, 0,93 en oos1; calculado por mí).

---

## 1. Qué es el paso y cómo decide

### 1.1 Dónde está en el workflow

```
16  SPP (rejilla en bloque, meseta)  →  16.5  variantes + nube  →  17 WFC · 18 CSCV · 18.5 · 19 WFM  →  20 lectura conjunta
```

El 16.5 tiene dos mitades que conviene no confundir:

| mitad | carpeta | qué hace | toca SQX | lo lanza el autopiloto |
|---|---|---|---|---|
| fabricar y medir variantes | `sqx/variants/` | diseña 500 combinaciones, fabrica los `.sqx`, los pasa por los tres tramos, recoge métricas y curvas | sí | sí |
| **la nube** | `studies/optimisation/cloud/` | lee esas métricas y curvas y calcula las lecturas A1-C1 | no (1,3 s por madre) | **no** |

Las variantes existen porque los pasos 17 (WFC), 18 (CSCV) y 19 (WFM) también las necesitan. La nube es
un lector más de ese mismo lote.

### 1.2 Cómo se fabrican las variantes (lo que le llega a la nube)

Paso a paso, con la madre C (`14.3.479`) como ejemplo. Los números son de su `design.json`, `pilot.json` y
`collected.json`.

**a) Qué parámetros se mueven.** El SPP del paso 16 deja un «brief» por madre: de cada parámetro dice si
está **vivo** (moverlo cambia las operaciones) o **congelado** (moverlo no cambia nada, o es un `shift`).
C tiene 17 parámetros: 12 vivos, 3 congelados con niveles y 2 que no se mueven nunca (un `Shift1` y
un decimal que queda fijo).

**b) Qué valores puede tomar cada uno** (`design/levels.py`).

- Vivo y entero: **todos los enteros** del tramo que el SPP dio por bueno. `ADXRisingPeriod1` de C: los 27
  enteros de 28 a 54.
- Vivo y decimal: una rejilla de niveles. `WAE…Dbl11` de C: 10 niveles.
- Congelado: 5 niveles en ±30 % del valor de la madre (`sqx/variants/config.yaml`), que sólo se usan en un
  estrato (ver c).
- Un parámetro **congelado** cuyo nombre acaba en `Shift1` se queda en su valor (`levels.py:5`,
  `:63-69`; el bucle recorre sólo los congelados).

**c) Cómo se reparten las 500** (`design/strata.py`, `studies/breakage/spp/config.yaml:18-22`).

| estrato | parte | qué es | alrededor de |
|---|---|---|---|
| controles | 7 en C | la madre, 3 canarios, 3 «pares inertes» | — |
| vecindad | 20 % (99) | todas las combinaciones a distancia ≤ 2 pasos | **el centro de la meseta del SPP** |
| factorial | 60 % (296) | combinaciones de niveles extremos de los vivos | todo el tramo |
| cobertura | 20 % (99) | relleno uniforme de todo el espacio, **congelados incluidos** | todo el espacio |

Dos detalles que pesan después:

- La «distancia ≤ 2» del estrato de vecindad es **de Manhattan**: se **suman** los pasos de todos los
  parámetros (§2.2). Y su centro es el centro de la meseta, no la madre (`levels.py:109-122`).
- Los parámetros **congelados sólo se mueven en el estrato de cobertura** (y en los pares inertes).
  Comprobado en los datos de C, E y F: en vecindad y factorial todos los congelados valen lo que en la
  madre (calculado por mí).

**d) Controles.** Un **canario** es una variante rota a propósito (debe salir distinta: prueba que el
retest lee los parámetros). Un **par inerte** es la madre con un congelado llevado al extremo (debe salir
idéntica: prueba que el congelado está bien congelado). En C los 3 pares inertes salen iguales a la madre
en neto y en operaciones; en F, 8 de 8; en E, 3 de 3.

**e) Piloto.** Antes de fabricar las 500 se prueban 300 combinaciones para descartar niveles que dejan la
estrategia sin operar. En C: 300 probadas, 0 niveles descartados.

**f) Retest y recogida.** Las variantes se pasan por build, oos1 y oos2. `collect` descarta las que suman
menos de **100 operaciones en total** (`sqx/variants/collect.py:100`, valor de `assets/_build.yaml:368`;
el comentario de `:353` de ese fichero dice «menos de 50»: está desfasado).

**g) El filtro de la nube** (`inputs/cloud.py:29-31`). Se queda con las variantes que **no** son canario
**y** tienen al menos 30 operaciones en build (`config.yaml:14-15`); la madre entra siempre.

### 1.3 Cuántas variantes llegan, madre por madre

Recalculado; «en la nube» y «quitadas» coinciden con lo guardado.

| madre | fabricadas | tras `collect` (caen por < 100 ops) | en la nube (quitadas) | parámetros / vivos para la nube | ops de la madre en build |
|---|---|---|---|---|---|
| 10.11.484 | 500 | 420 (80) | 418 (2) | 9 / 8 | 154 |
| 13.3.390 | 500 | 276 (224) | 274 (2) | 10 / 10 | 143 |
| C 14.3.479 | 501 | 417 (84) | 412 (5) | 17 / 15 | 189 |
| F 15.9.352 | 501 | 501 (0) | 490 (11) | 15 / 13 | 224 |
| 16.5.352 | 500 | 499 (1) | 497 (2) | 6 / 5 | 304 |
| 18.5.355 | 500 | 376 (124) | 374 (2) | 7 / 5 | 161 |
| 19.2.363 | 500 | 402 (98) | 400 (2) | 6 / 6 | 161 |
| E 3.11.426 | 501 | 429 (72) | 424 (5) | 10 / 9 | 135 |
| 3.9.284 | 500 | 416 (84) | 414 (2) | 10 / 9 | 222 |
| G 4.13.338 | 500 | 460 (40) | 458 (2) | 13 / 13 | 198 |

**Cómo leerlo.**

- Todas las que quita la nube son canarios. Ninguna cae por el suelo de 30 operaciones en build: el suelo
  de 100 totales de `collect` ya había pasado antes.
- «Vivos para la nube» son los parámetros que toman más de un valor en lo que queda
  (`model/space.py:55`). **No es lo mismo que «vivos para el SPP»**: en C la nube cuenta 15 y sólo 12 se mueven de verdad en todo el diseño,
  porque los congelados que se movieron en el estrato de cobertura cuentan como vivos.
- **En 13.3.390 se pierde casi la mitad** (224 de 500). Y se pierde entero el estrato de vecindad: sus 99
  variantes tenían una mediana de 30 operaciones en build y cayeron todas. El centro de la meseta del SPP
  es, en esa madre, una zona donde la estrategia casi no opera.

### 1.4 Quién lanza la nube y qué escribe

- **Ventana:** aparece catalogada en el paso «16.5» (`ui/daemon/results/catalogue.py:27`) y se lanza con
  `report --work <lote> --set run.symbol=<activo>` (`ui/daemon/runner/optimisation.py:7-14`).
- **Escribe:** `<lote>/estudios/cloud.json`, `cloud.html` y `cloud.md` (`report.py`).
- **Enseña tres pestañas** (`contract.py:99`, `:106`, `:120`): C1, A1, y «A2 y A3» con los mapas de calor.
  La descripción del propio estudio sigue diciendo «Cuatro preguntas».
- **Columnas en la ventana** (`ui/text/columnhelp_fields.py:17-48`): `point`, `surface`, `temporal`,
  `variants`, `dropped`, `r2`, `roughness`, `gap`, `rho_median`, `drift_median`.

### 1.5 Los estados

Las palabras de la nube tienen un color (`contract.py:10`), no un estado de los tres del workflow
(pasa / limbo / fuera):

| palabra | color | palabra | color |
|---|---|---|---|
| Meseta | verde | Pico | aviso |
| Superficie suave | verde | Superficie rugosa · Óptimo descentrado | aviso |
| Orden persistente · Gana en casi todos · Deriva baja | verde | Orden que se rebaraja · Sostenida por periodos · Deriva alta | aviso |
| Sin dato · Sin destacar | neutro | | |

**Ninguna de estas palabras mueve a una madre de sitio.**

---

## 2. Fundamentos: la estadística desde cero

Todo lo de esta sección es **Ilustrativo**: ejemplos pequeños hechos a mano para que cada pieza de la §3
se pueda leer.

### 2.1 La nube, la madre y la métrica

Una estrategia con dos parámetros, periodo y multiplicador, es un punto en un plano. Si se prueban nueve
combinaciones, hay nueve puntos; cada uno tiene un resultado. Eso es una **nube**. Con 15 parámetros es lo
mismo en 15 dimensiones: no se puede dibujar, pero se puede medir.

- **La madre** (θ₀ en el código, `P00000`) es el punto que eligió el genético.
- **La métrica** de cada punto es el **Ret/DD del tramo de construcción**: beneficio neto dividido entre la
  máxima caída. Ret/DD 3 quiere decir «ganó tres veces su peor caída».

### 2.2 Dos maneras de medir «cerca»: la caja y el rombo

La distancia se mide en **pasos de nivel**: si el periodo puede valer 28, 29, 30…, de 30 a 32 hay 2 pasos.

Con varios parámetros hay que decidir cómo se juntan los pasos de cada uno.

```
Variante X: se aleja 2 pasos en el periodo, 2 en el multiplicador, 2 en la salida.

Distancia «caja» (Chebyshev): el MAYOR de los tres   = max(2, 2, 2) = 2
Distancia «rombo» (Manhattan): la SUMA de los tres   = 2 + 2 + 2    = 6

Variante Y: 2 pasos en el periodo, 0 en lo demás.
Caja = 2 · Rombo = 2
```

- La **nube** usa la caja: vecina es la que no se aleja más de 2 pasos **en ningún** parámetro.
- El **diseño** usa el rombo: fabrica las que **suman** 2 pasos o menos.

Cuántos puntos caben en cada figura de radio 2:

| parámetros (k) | caja: 5^k | rombo: 1 + 2k + 2k² |
|---|---|---|
| 5 | 3.125 | 61 |
| 8 | 390.625 | 145 |
| 13 | 1.220.703.125 | 365 |
| 15 | 30.517.578.125 | 481 |

**Cómo leerlo.** El rombo cabe entero dentro de la caja: quien suma 2 pasos o menos no se aleja más de 2
en ningún eje. Si las dos figuras tuvieran el mismo centro, las ~100 variantes del estrato de vecindad
serían todas vecinas para la nube. No lo son porque **los centros son distintos** (§3.2). Las cifras de la
tabla son el máximo: no descuentan los recortes cuando el centro está cerca del borde de un tramo.

### 2.3 Rango (q): en qué puesto queda la madre

Se ordenan los resultados y se cuenta qué parte es **menor o igual** que el de la madre.

```
Nueve puntos: 5 6 6 7 7 7 8 8 9      la madre es el 9
Menores o iguales que 9: los nueve   →  q = 9/9 = 1,00
```

q = 1 quiere decir «la madre es la mejor»; q = 0,5, «está en la mitad». La cuenta **incluye a la propia
madre**, así que q nunca vale 0: con 2 puntos, lo mínimo es 0,5.

### 2.4 Compañía (π): cuántas la acompañan

Se fija un **suelo** un 20 % por debajo de la madre y se cuenta qué parte de los puntos queda **por encima
del suelo**.

```
Rejilla A:  5  6  6  7  7  7  8  8  9        madre = 9
suelo = 9 − 0,20 × 9 = 7,2
por encima de 7,2: 8, 8, 9  →  π = 3/9 = 0,33        mediana = 7

Rejilla B: −4 −3 −3 −2 −2 −2 −1 −1  9        madre = 9
suelo = 7,2
por encima de 7,2: sólo el 9 →  π = 1/9 = 0,11       mediana = −2
```

Las dos tienen q = 1 (la madre es la mejor). En A está acompañada: **meseta**. En B está sola en lo alto y
alrededor se pierde: **pico**.

Dos propiedades de esta cuenta que conviene tener presentes:

- **«Por encima del suelo» incluye a las que superan a la madre.** Si la madre es mediocre y la mitad de
  la nube es mejor, π sale alto. π alto no quiere decir «muchas parecidas»; quiere decir «pocas mucho
  peores».
- **El ancho de la banda depende del valor de la madre.** Con madre 9 la banda mide 1,8; con madre 0,3
  mide 0,06. Una madre casi en cero tiene una banda casi nula.

### 2.5 Valor «encogido»

Es la **mediana** de los vecinos (7 en A, −2 en B). La idea es: si mañana el mercado mueve un poco el
parámetro óptimo, lo razonable es esperar el resultado típico de la zona, no el del punto elegido.

### 2.6 Ajustar una superficie y el R²

Para saber si la zona es lisa se le ajusta una **superficie cuadrática**: la forma más simple que puede
tener una loma (sube, llega arriba, baja). Con un parámetro es una parábola.

**R²** mide qué parte de las diferencias entre puntos explica la superficie. 1 = todos los puntos caen
sobre ella; 0 = la superficie no explica nada.

```
Cinco valores del parámetro: 0 · 0,25 · 0,5 · 0,75 · 1

Caso liso:    resultados  2  4  5  4  2
parábola ajustada:        1,97  4,11  4,83  4,11  1,97
R² = 0,992       →  rugosidad = 1 − R² = 0,008

Caso rugoso:  resultados  4  2  5  1  4
R² = 0,069       →  rugosidad = 0,931
```

**La trampa del R²: con muchos coeficientes y pocos puntos, sube solo.** La cuadrática con k parámetros
tiene 1 + 2k + k(k−1)/2 coeficientes:

| k | 5 | 8 | 10 | 13 | 15 |
|---|---|---|---|---|---|
| coeficientes | 21 | 45 | 66 | 105 | 136 |

Ajustada a **puro ruido**, una superficie con p coeficientes y n puntos da un R² de alrededor de
(p − 1)/(n − 1). Con 136 coeficientes y 412 puntos: 135/411 = **0,33 sin que haya nada que explicar**. Con
tantos puntos como coeficientes más uno, el R² es prácticamente 1 siempre. Por eso existe el **R²
ajustado**, que descuenta ese efecto; el estudio lo calcula y no lo usa (§3.6).

### 2.7 Rugosidad local, sin modelo

Otra manera de medir lo mismo sin suponer una forma: para cada punto se miran sus 8 vecinos más próximos,
se toma la mediana de sus resultados y se mide cuánto se separa el punto de esa mediana. Se resume con la
mediana de esas separaciones, dividida por el ancho de la mitad central de los resultados (el rango
intercuartílico, IQR).

```
Siete puntos en fila, resultados 1 2 3 4 5 6 7, comparando cada uno con sus 2 vecinos:
punto 4: vecinos 3 y 5 → mediana 4 → separación 0
(igual en todos los interiores)                    →  rugosidad local ≈ 0

Los mismos siete resultados barajados: 5 1 7 2 6 3 4
punto «1»: vecinos 5 y 7 → mediana 6 → separación 5
                                                   →  rugosidad local alta
```

**Referencia útil:** con resultados que son puro ruido la rugosidad local **depende de la madre**: de
0,35 (entre 0,31 y 0,41) en C a 0,53 en 13.3.390 (barajando las nubes reales; 20 tiradas mías, 200 en la
revisión). **En C el umbral de 0,35 ES el ruido.** Un umbral fijo no sirve igual para todas: cada madre
hay que compararla con su propio barajado.

### 2.8 Pendiente: ¿la madre está arriba o en la ladera?

Sobre la superficie ajustada se calcula la **pendiente** en el punto de la madre. En lo alto de una loma la
pendiente es 0; en una ladera no. Pendiente grande = «moviendo un poco los parámetros se mejora» = la madre
no está en el óptimo de su zona (**óptimo descentrado**).

### 2.9 Índices de Sobol: quién mueve el resultado

**Varianza** es cuánto se dispersan los resultados. Los índices de Sobol reparten esa dispersión entre los
parámetros.

- **Primer orden:** qué parte de la dispersión produce un parámetro **él solo**.
- **Total:** qué parte pasa por él, **solo o combinado con otros**.

```
Resultado = 3 × x₁ + x₂          (x₁ y x₂ entre 0 y 1; cada uno actúa por su cuenta)
x₁ aporta 9 partes de dispersión, x₂ aporta 1
primer orden: x₁ = 0,90 · x₂ = 0,10        total: lo mismo        suma = 1

Resultado = (x₁ − ½) × (x₂ − ½)  (ninguno hace nada solo; sólo importa la combinación)
primer orden: x₁ = 0 · x₂ = 0
total:        x₁ = 1 · x₂ = 1                                    suma de totales = 2
```

**Cómo leerlo.**

- Si los primeros órdenes suman cerca de 1, los parámetros actúan cada uno por su lado: superficie simple.
- Si suman poco y los totales suman mucho más de 1, todo son combinaciones. El glosario de la ventana lo
  llama «lógica afinada». **También es lo que sale cuando se ajusta ruido, o cuando entran columnas que la superficie no
  puede identificar** (§3.4, §3.5).
- Los índices se calculan **sobre la superficie ajustada**, no sobre los datos. Si la superficie explica el
  17 % (R² = 0,17), el ranking describe ese 17 %.

### 2.10 Correlación de rangos (ρ de Spearman)

Mide si dos clasificaciones coinciden. +1 = el mismo orden; 0 = sin relación; −1 = orden inverso.

```
Cinco variantes, puesto en 2020: 1 2 3 4 5
                 puesto en 2021: 2 1 4 3 5
diferencias: −1 +1 −1 +1 0   → al cuadrado y sumadas: 4
ρ = 1 − 6 × 4 / (5 × 24) = 1 − 0,2 = 0,80
```

**El margen de ρ aquí es ancho.** Con 400 variantes independientes y sin relación real, ρ saldría entre
−0,10 y +0,10. **Las variantes de una madre no son independientes**: comparten casi todas las operaciones
y el ruido les llega por familias. Medido en la revisión: entre pares de años, ρ se dispersa de 0,16 a
0,40 según la madre, y del 56 % al 89 % de los pares cae fuera de ±0,10; las 274-497 variantes valen por
7 a 39 independientes. **El margen real es de ±0,3 a ±0,8.**

### 2.11 Centroide y deriva

Cada parámetro se pone en una escala de 0 a 1 (0 = su valor más bajo en la nube, 1 = el más alto). El
**centroide** del 10 % mejor de un año es el punto medio de esas variantes. La **deriva** es cuánto se
mueve ese punto de un año al siguiente, dividido por √k para que no crezca sólo por tener más parámetros.

```
Dos parámetros. Centroide de las mejores en 2020: (0,2 ; 0,6)
                Centroide de las mejores en 2021: (0,5 ; 0,2)
distancia = √(0,3² + 0,4²) = 0,5        deriva = 0,5 / √2 = 0,354
```

0 = la zona buena no se mueve; 0,35 = se ha ido a un tercio del espacio de distancia.

### 2.12 Sharpe anualizado de una curva diaria

Media de la ganancia diaria dividida por su dispersión, multiplicada por √252.

```
Madre C, todo el histórico: media diaria 5,67 · dispersión diaria 240,07 · 3.768 días
Sharpe = 5,67 / 240,07 × √252 = 0,0236 × 15,87 = 0,375
```

**El Sharpe de un solo año es muy ruidoso**: su error típico es de alrededor de 1. Una estrategia con
Sharpe verdadero 0,5 pierde un año de cada tres (31 %) sólo por azar.

```
Probabilidad de NO tener ningún año perdedor:
  Sharpe verdadero 0,5, en 15 años:  0,69^15 =  0,4 %
  Sharpe verdadero 1,0, en 15 años:  0,84^15 =  7,3 %
  Sharpe verdadero 0,5, en  5 años:  0,69^5  = 15,6 %
```

Esto importa en B2: «gana en casi todos los años» es casi imposible con 15 años y fácil con 5, **a igual
calidad de estrategia**.

### 2.13 Por qué mezclar puede subir el Sharpe

Si se opera la media de K curvas, la ganancia media no cambia pero la dispersión baja si las curvas no van
a la par.

```
Dos curvas con el mismo Sharpe:
  correlación 0    →  la mezcla tiene Sharpe × 1,41
  correlación 0,9  →  la mezcla tiene Sharpe × 1,03
```

Variantes de una misma madre son casi la misma estrategia: correlación alta, mejora pequeña. C1 mide eso.

---

## 3. Lo que calcula el estudio, pieza a pieza

### 3.1 Cabecera: variantes, quitadas, parámetros colapsados

**Qué es.** `variants` = filas que entran; `dropped` = filas quitadas por el filtro; «colapsados» =
parámetros que toman un solo valor en lo que queda y por tanto salen del análisis.

**Dónde.** `inputs/cloud.py:29-31` (filtro), `model/space.py:55` (vivos).

**En la corrida.** Tabla de §1.3. Colapsados: `DIPlusShift1` (10.11.484), `ADXRisingShift1` y `WAE…Dbl21`
(C), `ADXChangesUpShift1` y `WAE…Dbl21` (F), `ADXCrossDownShift1` (16.5.352), `ADXHigherShift1` y
`BBBarOpensShift1` (18.5.355), `ZScrStrDbl33` (E), `ChoppinessIndRsnShf1` (3.9.284).

**Cómo leerlo.** Los `…Shift1` colapsados son la regla «un shift no se mueve» funcionando. Pero **la regla
sólo reconoce el nombre acabado en `Shift1`** (`levels.py:5`, `:69`; `studies/breakage/spp/run.py:108`).
Los bloques propios abrevian `Shf1` y **sí se varían**: `KCBarOpnAftOpnShf1` de E está vivo con 6 niveles
(1 a 6); `ChoppinessIndRsnShf1` de 16.5.352, con 4. Y pesan: índice de Sobol total 0,05 a 0,10 en tres
madres.

### 3.2 La vecindad: quién es vecina de la madre

**Qué es.** Las variantes a **2 pasos o menos en todos los parámetros** de la madre.

**Fórmula** (`model/neighbourhood.py:22`, radio en `config.yaml:20`):

```
pasos(variante, parámetro) = puesto del valor entre los valores presentes en la nube   (space.py:34-35)
vecina  ⇔  |pasos(variante) − pasos(madre)| ≤ 2  en TODOS los parámetros vivos
```

**En la corrida** (recalculado):

| madre | variante más cercana a la madre (pasos, caja) | a ≤ 2 pasos | a ≤ 5 | a ≤ 10 | estrato «vecindad» que llega a la nube |
|---|---|---|---|---|---|
| 10.11.484 | 4 | **0** | 2 | 21 | 99 |
| 13.3.390 | 4 | **0** | 1 | 19 | 0 |
| C 14.3.479 | 11 | **0** | 0 | 0 | 99 |
| F 15.9.352 | 7 | **0** | 0 | 9 | 61 |
| 16.5.352 | 3 | **0** | 5 | 36 | 60 |
| 18.5.355 | 3 | **0** | 19 | 137 | 60 |
| 19.2.363 | 3 | **0** | 9 | 33 | 17 |
| E 3.11.426 | 4 | **0** | 10 | 101 | 81 |
| 3.9.284 | 6 | **0** | 0 | 2 | 99 |
| G 4.13.338 | 12 | **0** | 0 | 0 | 99 |

**Por qué sale cero.** El estrato de vecindad existe (hasta 99 variantes por madre), pero está en otro
sitio:

```
Madre C, parámetro ADXRisingPeriod1
  valor de la madre: 40 · centro de la meseta del SPP: 47 · niveles: los 27 enteros de 28 a 54
  → el centro del estrato denso está a 7 pasos de la madre en este parámetro

Madre C, parámetro WAE…Prd11
  valor de la madre: 100 · centro de la meseta: 83   → 14 pasos (con los valores presentes en la nube)

Madre E, parámetro ZScrStrInt21:  madre 170 · centro 159 · 88 valores  → 10 pasos
Madre 16.5.352, ChoppinessIndRsnPrd1: madre 80 · centro 100           → 19 pasos
```

El estrato de vecindad queda, medido en la caja de la nube, a **39-42 pasos de la madre en C, 9-12 en E,
41-45 en F, 43-45 en G y 17-21 en 16.5.352**.

**Cómo leerlo.**

- Con radio 2 y el diseño actual, **esta lectura no puede dar dato** salvo que la madre coincida con el
  centro de su meseta. No es mala suerte de esta corrida.
- Hay dos cosas distintas mezcladas: **el centro** (madre frente a centro de meseta) y **la unidad** (un
  paso = un entero). En un periodo que va de 28 a 54, «2 pasos» es ±2 barras; el SPP había dado por bueno
  el tramo entero.
- El número de pasos se cuenta entre los valores **presentes** en la nube, no entre los niveles del
  diseño. Si un nivel no tiene ninguna variante superviviente, deja de contar como paso.
- El tamaño del estrato cuadra con el rombo de §2.2: con 5 parámetros vivos caben 61 puntos, y 16.5.352 y
  18.5.355 tienen 60 (calculado por mí).

### 3.3 A1 — rango, compañía y valor encogido

**Fórmulas** (`core/surface/plateau.py`, llamadas desde `model/neighbourhood.py:41-46`):

```
q        = parte de los valores ≤ el de la madre                         plateau.py:112
π        = parte de los valores ≥ madre − 0,20 × |madre|                 plateau.py:128   (δ: config.yaml:21)
encogido = mediana de los valores                                        plateau.py:141
```

Se calculan dos veces: sobre **la vecindad** y sobre **la nube entera**. Sólo la primera entra en la
palabra.

**La palabra** (`verdict/call.py:34-39`):

```
vecindad con menos de 2 puntos        →  Sin dato
q de la vecindad < 0,95               →  Sin destacar
q ≥ 0,95 y π ≤ 0,15                   →  Pico
q ≥ 0,95 y π > 0,15                   →  Meseta
```

**En la corrida.** Vecindad: 1 punto (la madre), q = 1, π = 1 → **«Sin dato» en las diez**. La fila «Nube
entera», recalculada (coincide con lo guardado):

| madre | Ret/DD madre | n | ≤ madre → q | suelo | ≥ suelo → π | de ellas, mejores que la madre | mediana («encogido») |
|---|---|---|---|---|---|---|---|
| 10.11.484 | 3,07 | 418 | 285 → 0,682 | 2,456 | 179 → 0,428 | 133 | 2,18 |
| 13.3.390 | 1,45 | 274 | 99 → 0,361 | 1,160 | 199 → 0,726 | 175 | 1,76 |
| C | 2,47 | 412 | 280 → 0,680 | 1,976 | 148 → 0,359 | 132 | 0,85 |
| F | 0,30 | 490 | 416 → 0,849 | 0,240 | 89 → 0,182 | 74 | −0,31 |
| 16.5.352 | 0,84 | 497 | 232 → 0,467 | 0,672 | 294 → 0,592 | 265 | 0,96 |
| 18.5.355 | 3,31 | 374 | 248 → 0,663 | 2,648 | 165 → 0,441 | 126 | 2,41 |
| 19.2.363 | 0,42 | 400 | 210 → 0,525 | 0,336 | 195 → 0,487 | 190 | 0,31 |
| E | 3,43 | 424 | 230 → 0,542 | 2,744 | 229 → 0,540 | 194 | 3,02 |
| 3.9.284 | 5,62 | 414 | 289 → 0,698 | 4,496 | 147 → 0,355 | 125 | 2,30 |
| G | 8,65 | 458 | 445 → 0,972 | 6,920 | 28 → 0,061 | 13 | 2,59 |

Ejemplo a mano, madre C:

```
Ret/DD de la madre = 2,47 · 412 variantes en la nube
≤ 2,47: 280          →  q = 280/412 = 0,680
suelo = 2,47 − 0,20 × 2,47 = 1,976
≥ 1,976: 148         →  π = 148/412 = 0,359
   de esas 148: 132 son MEJORES que la madre; 16 (madre incluida) están entre 1,976 y 2,47
mediana de las 412 = 0,85
```

**Cómo leerlo.**

- **G sería «Pico» si la palabra leyera la nube entera** (q 0,972 ≥ 0,95 y π 0,061 ≤ 0,15): es la mejor de
  su nube y sólo 15 de 458 quedan en su banda. Pero la palabra sólo lee la vecindad, y dice «Sin dato».
- **«Meseta» exige que la madre sea casi la mejor** (q ≥ 0,95). Una madre en mitad de una zona buena y
  llana (E: q 0,54, π 0,54, mediana 3,02 frente a 3,43) sale «Sin destacar», que es neutro. La palabra
  «Meseta» significa aquí «la mejor, pero acompañada», no «zona llana».
- **«Sin destacar» no distingue una madre mediocre en zona buena de una madre en un hoyo.** 13.3.390 tiene
  q 0,36: dos tercios de su nube la superan.
- **π alto con madre baja engaña.** 16.5.352: π 0,59, pero 265 de las 294 son mejores que ella.
- **La banda de F mide 0,06** (0,30 × 0,20). Cualquier criterio sobre π castiga a las madres con Ret/DD
  cercano a cero por construcción.
- La nube entera **no es una muestra uniforme** del espacio: el 60 % son esquinas (factorial) y el 20 %
  está amontonado en el centro de la meseta. q y π de la nube entera describen ese diseño, no «la zona».
- El rango del SPP en IS (dossier del paso 16) para C, E, F, G era 44, 64, 79, 94; el q de la nube es 68,
  54, 85, 97. Son muestras distintas del mismo espacio; con cuatro madres y un par invertido no se puede decir
  que coincidan ni que no.

### 3.4 A2 — índices de Sobol

**Qué es.** El reparto de la dispersión del Ret/DD entre parámetros, calculado sobre una superficie
cuadrática ajustada a **toda la nube**.

**Fórmulas.**

```
superficie: y ≈ c₀ + Σ aᵢxᵢ + Σ bᵢxᵢ² + Σ cᵢⱼxᵢxⱼ          model/surrogate.py:21-22, 38-45
   (x en escala 0-1: space.py:69-71)
se evalúa en 2¹² = 4.096 puntos al azar bien repartidos    model/sensitivity.py:32-46
primer orden (Saltelli) = media( y_B × (y_AB − y_A) ) / varianza
total (Jansen)          = media( (y_A − y_AB)² ) / (2 × varianza)
```

En `one.py`: ajuste global en `:44`, Sobol en `:46`.

**En la corrida.** Los índices totales coinciden con lo guardado. El R² del ajuste global **no se publica
en ningún sitio**; calculado por mí:

| madre | k | coeficientes | n | R² (ajustado) | R² del ruido ≈ (p−1)/(n−1) | Σ primer orden | Σ total |
|---|---|---|---|---|---|---|---|
| 10.11.484 | 8 | 45 | 418 | 0,674 (0,635) | 0,11 | 0,94 | 1,05 |
| 13.3.390 | 10 | 66 | 274 | 0,704 (0,611) | 0,24 | 0,93 | 1,07 |
| C | 15 | 136 | 412 | 0,868 (0,803) | 0,33 | 0,65 | 1,32 |
| F | 13 | 105 | 490 | 0,642 (0,546) | 0,21 | **0,13** | **1,84** |
| 16.5.352 | 5 | 21 | 497 | **0,174** (0,139) | 0,04 | 0,85 | 1,15 |
| 18.5.355 | 5 | 21 | 374 | 0,556 (0,531) | 0,05 | 0,87 | 1,13 |
| 19.2.363 | 6 | 28 | 400 | 0,544 (0,511) | 0,07 | 0,92 | 1,08 |
| E | 9 | 55 | 424 | 0,671 (0,623) | 0,13 | 0,86 | 1,15 |
| 3.9.284 | 9 | 55 | 414 | 0,842 (0,818) | 0,13 | 0,89 | 1,10 |
| G | 13 | 105 | 458 | 0,789 (0,727) | 0,23 | 0,95 | 1,06 |

Los primeros del ranking (total / primer orden; **(cong.)** = congelado por el SPP):

| madre | 1.º | 2.º | 3.º | 4.º |
|---|---|---|---|---|
| C | `ZScrStrDbl31` 0,332 / 0,313 | `ZScrStrInt21` 0,223 / 0,195 | `WAE…Prd31` 0,158 / 0,003 **(cong.)** | `WAE…Prd61` 0,146 / 0,017 **(cong.)** |
| E | `ZScrStrDbl31` 0,350 / 0,316 | `ExitAfterBars1` 0,223 / 0,194 | `ZScrStrInt22` 0,119 / 0,088 **(cong.)** | `ZScrStrInt23` 0,112 / 0,071 **(cong.)** |
| F | `WAE…Prd11` 0,237 / 0,019 **(cong.)** | `WAE…Prd41` 0,193 / −0,001 **(cong.)** | `ExitAfterBars1` 0,188 / −0,014 | `ADXChangesUpPeriod1` 0,163 / 0,034 |
| G | `ZScrStrDbl31` 0,647 / 0,608 | `ExitAfterBars1` 0,226 / 0,200 | — | — |

**Cómo leerlo.**

- **G, E y C dicen algo claro y creíble:** un umbral (`ZScrStrDbl31`) y la salida por barras
  (`ExitAfterBars1`) explican la mayor parte, cada uno por su cuenta. En G un solo parámetro lleva el 65 %.
- **El ranking de F, tal como sale, no vale; el de sus parámetros vivos sí.** Primer orden 0,13, total
  1,84, los dos primeros congelados. Barajando al azar el Ret/DD entre las variantes de F sale el mismo
  dibujo: R² 0,216, Σ primer orden 0,16, **Σ total 1,84** (20 tiradas mías; reproducido con 200 en la
  revisión). Los ocho congelados de F suman 1,16 de índice total; sus ocho pares inertes reproducen a la
  madre exactamente. **Pero sin las columnas congeladas F da R² 0,47, Σ primer orden 0,92, Σ total 1,06 y
  tres parámetros vivos a ≈ 0,28 cada uno** (comprobado en la revisión). F sí tiene estructura; la tapan
  los congelados.
- **Por qué los congelados puntúan: es un artefacto del cálculo.** Sólo se mueven en el estrato de
  cobertura (§1.2 c): unas 100 filas de 400-500. Con tan pocas filas la superficie no puede identificar
  sus términos cruzados, y el Sobol evalúa esa superficie en **todo** el cubo, también donde no hay datos.
  Comprobado en la revisión: permutando los valores congelados dentro de cobertura su Sobol queda igual
  (F: 1,14, entre 1,02 y 1,29, frente a 1,17), y barajando todo el Ret/DD siguen puntuando (F 1,26;
  C 0,73; E 0,82). **No es que hagan de etiqueta del estrato**: cobertura y factorial tienen en F la misma
  mediana de Ret/DD (−0,41 y −0,35). En C los congelados suman 0,38 de índice total y, quitándolos, el Σ
  de primer orden de C pasa de 0,65 a 0,97; en E suman 0,28.
- **El R² que justificaría fiarse del ranking no está a la vista.** El README (`:65-68`) dice que el R² va
  al lado de los Sobol. El `r2` que se publica es el del ajuste **local** (`one.py:105`), que aquí es nulo.
  En 16.5.352 el ajuste global explica el 17 %: su ranking describe una sexta parte de lo que pasa.
- **Los mapas de calor** (`heatmaps.py`: 6 × 6 celdas, mediana del Ret/DD por celda, pares de los 4
  parámetros de mayor Sobol total) heredan el problema: en F cruzan dos parámetros congelados.

### 3.5 Referencia: qué sale cuando no hay nada (calculado por mí)

Barajando el Ret/DD entre las variantes de cada madre (20 veces, mediana):

| madre | R² real | R² barajado | Σ1 / ΣT real | Σ1 / ΣT barajado | rugosidad local real | barajada |
|---|---|---|---|---|---|---|
| C | 0,868 | 0,331 | 0,65 / 1,32 | 0,31 / 1,67 | 0,072 | 0,356 |
| F | 0,642 | 0,216 | 0,13 / 1,84 | 0,16 / 1,84 | 0,351 | 0,512 |
| 16.5.352 | 0,174 | 0,043 | 0,85 / 1,15 | 0,81 / 1,20 | 0,439 | 0,500 |
| G | 0,789 | 0,230 | 0,95 / 1,06 | 0,72 / 1,27 | 0,177 | 0,434 |

**Cómo leerlo.** Son medianas de 20 tiradas, sin intervalo; la revisión las reproduce con 200. C y G
tienen estructura real (R² y rugosidad muy lejos del ruido). **16.5.352 tiene estructura débil, no nula**:
su R² de 0,174 queda muy fuera del barajado (entre 0,02 y 0,06), pero su rugosidad y su reparto de Sobol
no se distinguen del azar. F tiene R² real por encima del ruido y un reparto entre parámetros estropeado
por los congelados (§3.4). La rugosidad barajada cambia de madre a madre (0,36 en C, 0,51 en F): el
umbral fijo de 0,35 no significa lo mismo en cada una.

### 3.6 A3 — rugosidad, rugosidad local y pendiente

**Qué calcula y sobre qué puntos.** Aquí está el detalle que más confunde:

| número | sobre qué puntos | línea |
|---|---|---|
| `r2` y rugosidad 1 − R² | **sólo la vecindad** (ajuste local) | `one.py:45`, `surrogate.py:38-45` |
| rugosidad local sin modelo (`roughness` en el resumen) | **toda la nube** | `one.py:64`, `surrogate.py:102-104` |
| pendiente | el ajuste **local**, en el punto de la madre | `one.py:65`, `surrogate.py:77-85` |

**Fórmulas.**

```
R² = 1 − varianza(residuos) / varianza(y)          rugosidad = 1 − R²
R² ajustado: se calcula (surrogate.py:43) y no se usa en ningún sitio
rugosidad local = mediana( |y − mediana de sus 8 vecinas más próximas| ) / IQR(y)     (vecinas: config.yaml:24)
pendiente = longitud del vector (coeficiente lineal + curvatura × posición de la madre)
```

**La palabra** (`verdict/call.py:56-62`):

```
vecindad con n ≤ nº de coeficientes                       →  Sin dato
rugosidad (1 − R² local) ≥ 0,35  O  rugosidad local ≥ 0,35 →  Superficie rugosa
si no, y pendiente ≥ 1,0                                   →  Óptimo descentrado
si no                                                      →  Superficie suave
```

**En la corrida.** Vecindad de 1 punto frente a 21-136 coeficientes: **«Sin dato» en las diez**. La tabla
«¿Hay superficie que leer?» ni se pinta (`contract.py:88`). `r2` sale nulo. La rugosidad local de toda la
nube sí se escribe (coincide con lo guardado):

| 10.11.484 | 13.3.390 | C | F | 16.5.352 | 18.5.355 | 19.2.363 | E | 3.9.284 | G |
|---|---|---|---|---|---|---|---|---|---|
| 0,119 | **0,407** | 0,072 | **0,351** | **0,439** | 0,230 | 0,282 | 0,237 | 0,090 | 0,177 |

**Cómo leerlo.**

- **La columna `roughness` de la ventana tiene dato aunque `surface` diga «Sin dato».** Tres madres
  superan 0,35 y no reciben la palabra «rugosa» porque la palabra exige primero que haya vecindad. Y el
  0,35 no significa lo mismo en cada madre: el ruido puro da de 0,35 a 0,53 según cuál (§2.7).
- **Para que A3 tenga dato hacen falta más vecinas que coeficientes**: 22 con 5 parámetros, 137 con 15.
  Y con justo una más que coeficientes el R² es casi 1 (§2.6): la lectura diría «suave» por construcción.
  No hay un mínimo de puntos por coeficiente.
- **`or`, no `and`.** `model/README.md:19-20`, el docstring de `call.surface` y el manual dicen «sólo se
  habla de superficie rugosa cuando las dos coinciden». El código (`call.py:58-59`) marca rugosa con una
  sola.
- La palabra **mezcla dos escalas**: 1 − R² de la vecindad con rugosidad local de toda la nube.
- La pendiente está en «unidades de Ret/DD por recorrer el tramo entero de un parámetro». Un umbral fijo de
  1,0 es exigente para una madre con Ret/DD 0,3 y laxo para una con 8,6. Las pendientes que salen del
  ajuste sobre un solo punto no significan nada y no las cito.

### 3.7 B2 — la lectura por años (calculada, no pintada)

**Qué calcula.** Parte la curva diaria de cada variante por años naturales y, por año:

```
Sharpe del año de cada variante = media diaria / dispersión diaria × √252      measure/stability.py:27-30
días activos = días con ganancia ≠ 0
año legible  ⇔  la mediana de días activos entre variantes ≥ 60                stability.py:43, config.yaml:30

f_y       = parte de las variantes con ganancia > 0 ese año                    stability.py:57
q_origen  = puesto de la madre entre las variantes ese año                     stability.py:117-118
ρ         = Spearman entre los Sharpes de un año legible y el siguiente legible   stability.py:73-77
centroide = punto medio del 10 % mejor del año (config.yaml:31)                stability.py:95-102
deriva    = distancia entre centroides consecutivos / √k
```

**Las tres palabras** (`verdict/call.py:82-85`):

```
mínimo de f_y entre años ≥ 0,50      →  Gana en casi todos      · si no →  Sostenida por periodos
mediana de ρ ≥ 0,20                  →  Orden persistente       · si no →  Orden que se rebaraja
mediana de la deriva ≥ 0,20          →  Deriva alta             · si no →  Deriva baja
```

**En la corrida** (recalculado; las palabras coinciden con lo guardado):

| madre | mediana de días activos/año | años legibles | mín f_y | mediana ρ | mediana deriva | palabras guardadas |
|---|---|---|---|---|---|---|
| 10.11.484 | 39 | 1 (2024) | — | — | — | Gana en casi todos · Rebaraja · Deriva baja |
| 13.3.390 | 97 | 15 | 0,07 | −0,045 | 0,281 | Sostenida · Rebaraja · Deriva alta |
| C | 30 | **0** | — | — | — | Sostenida · Rebaraja · Deriva baja |
| F | 76 | 11 | 0,09 | −0,056 | 0,188 | Sostenida · Rebaraja · Deriva baja |
| 16.5.352 | 96 | 15 | 0,04 | −0,051 | 0,216 | Sostenida · Rebaraja · Deriva alta |
| 18.5.355 | 61 | 9 | 0,23 | +0,148 | 0,160 | Sostenida · Rebaraja · Deriva baja |
| 19.2.363 | 21 | 1 (2026) | — | — | — | Gana en casi todos · Rebaraja · Deriva baja |
| E | 37 | 1 (2024) | — | — | — | Gana en casi todos · Rebaraja · Deriva baja |
| 3.9.284 | 54 | 5 | 0,57 | +0,063 | 0,284 | Gana en casi todos · Rebaraja · Deriva alta |
| G | 40 | 1 (2024) | — | — | — | Gana en casi todos · Rebaraja · Deriva baja |

Un ejemplo completo, madre 13.3.390 (274 variantes):

| año | f_y | q de la madre | días activos | ρ con el siguiente | deriva al siguiente |
|---|---|---|---|---|---|
| 2012 | 0,905 | 0,982 | 122 | +0,062 | 0,168 |
| 2013 | 0,923 | 0,058 | 81 | −0,263 | 0,428 |
| 2014 | 0,796 | 0,474 | 108 | +0,046 | 0,411 |
| 2015 | 0,686 | 0,467 | 108 | −0,064 | 0,280 |
| 2016 | 0,193 | 0,245 | 93,5 | −0,340 | 0,296 |
| 2017 | 0,730 | 0,212 | 90,5 | −0,419 | 0,447 |
| 2018 | 0,474 | 0,865 | 86 | +0,374 | 0,232 |
| 2019 | 0,653 | 0,383 | 91 | −0,279 | 0,267 |
| 2020 | 0,639 | 0,883 | 99 | −0,120 | 0,281 |
| 2021 | 0,774 | 0,263 | 110,5 | +0,019 | 0,167 |
| 2022 | 0,073 | 0,493 | 95,5 | −0,259 | 0,221 |
| 2023 | 0,354 | 0,971 | 109 | −0,026 | 0,349 |
| 2024 | 0,288 | 0,401 | 107,5 | +0,097 | 0,450 |
| 2025 | 0,949 | 0,409 | 103 | +0,167 | 0,223 |
| 2026 | 0,909 | 0,912 | 77 | — | — |

**Cómo leerlo.**

- **Las palabras salen aunque no haya datos.** Con cero años legibles las tres cuentas dan «sin número», y
  una comparación con «sin número» es siempre falsa: salen las tres palabras del «si no». En C eso da
  «Sostenida por periodos · Orden que se rebaraja · Deriva baja» **sin haber mirado nada**. Con un solo
  año no hay ρ ni deriva, y pasa lo mismo con dos de las tres.
- **El suelo de 60 días activos deja fuera a media corrida.** Estas estrategias hacen 135-300 operaciones
  en ocho años de build. Cinco de diez madres se quedan con 0 o 1 año.
- **El único año legible de cuatro madres es 2024 o 2026: años de `oos2`.**
- **«Gana en casi todos» depende de cuántos años se miran, no de la estrategia** (§2.12). Las cuatro que
  la reciben con dato real tienen 1 año (tres) o 5 (3.9.284). Las que tienen 9-15 años son todas
  «Sostenida por periodos». Con el suelo en 20 días (calculado por mí) todas tienen 8-15 años legibles y
  **las diez** salen «Sostenida» y «Rebaraja».
- **El orden entre variantes no persiste en ninguna madre.** Mediana de ρ entre −0,06 y +0,15; el umbral es
  0,20. En 13.3.390 la madre es la 2.ª mejor de su nube en 2012 y de las peores en 2013.
  **Lo que se sostiene: la mediana de ρ es prácticamente cero en todas.** Lo que no se sostiene es leer
  un valor suelto: con un margen real de ±0,3 a ±0,8 (§2.10), **un 0,15 no se distingue del umbral
  0,20**. La explicación no es «cada variante tiene su ruido de ±1»: el ruido es común por familias de
  variantes que comparten operaciones (comprobado en la revisión; n efectivo de 7 a 39). Elegir «la mejor
  variante del año pasado» no sirve.
- **«Año siguiente» es el siguiente legible**, no el siguiente del calendario. En F cae 2015, así que una
  ρ compara 2014 con 2016.
- **La deriva no tiene referencia válida.** Si el 10 % mejor de cada año fuera un grupo al azar de
  variantes independientes, la deriva sería de 0,05 a 0,11 (calculado por mí, 500 tiradas), y lo observado
  es 0,16-0,28. **Esa comparación no vale**: con variantes que valen por 7-39 independientes, el mejor
  decil sale agrupado aunque no haya ninguna «esquina buena» (inferencia de la revisión, no recalculada).
  La deriva, tal como está, **no distingue una zona buena que se mueve de ruido compartido**. El umbral
  0,20 no sale de ninguna cuenta.
- 2011 y 2026 son años parciales (la curva va del 2011-09-19 al 2026-09-29) y entran como un año más si
  pasan el suelo.
- Los «días activos» no son operaciones: 13.3.390 tiene unos 100 días activos al año con 143 operaciones en
  ocho años. Lo más probable es que la curva diaria marque a mercado las posiciones abiertas. **No
  verificado.**

### 3.8 C1 — la mezcla frente al punto único

**Qué calcula.**

```
candidatas = vecinas de la madre con Ret/DD ≥ madre − 0,20 × |madre|        measure/ensemble.py:25-27
se eligen K = 8 lo más separadas posible entre sí                           ensemble.py:44-49, config.yaml:34
mezcla = media de las ganancias diarias de las K                            ensemble.py:86-89
se da neto, Sharpe anualizado (√252) y máxima caída del punto único y de la mezcla   ensemble.py:63-66
gap = Sharpe del punto único − Sharpe de la mezcla                          one.py:39
```

**En la corrida.** Vecindad vacía → la única candidata es la madre → K = 1 → la mezcla **es** la madre →
gap 0,000 en las diez (coincide con lo guardado). Lo que la pestaña enseña es, por tanto, sólo la fila del
punto único, **sobre todo el histórico, `oos2` incluido**:

| madre | neto | Sharpe | máx. caída |
|---|---|---|---|
| 10.11.484 | 48.920 | 0,610 | −7.587 |
| 13.3.390 | 28.090 | 0,309 | −11.835 |
| C | 21.367 | 0,375 | −5.817 |
| F | 14.345 | 0,146 | −14.641 |
| 16.5.352 | 23.644 | 0,171 | −17.932 |
| 18.5.355 | 43.104 | 0,417 | −13.449 |
| 19.2.363 | 2.863 | 0,062 | −11.577 |
| E | 44.502 | 0,567 | −7.054 |
| 3.9.284 | 45.967 | 0,491 | −9.013 |
| G | 96.748 | 0,874 | −8.736 |

```
Madre C: neto 21.367 = build 13.239 + oos1 4.690 + oos2 3.438
```

**Cómo leerlo.**

- **Un gap de 0,000 con K = 1 no es «la mezcla rinde igual»**; es «no hay mezcla». La ventana enseña el
  cero en la columna `gap` sin esa advertencia.
- Cuando haya vecinas, el signo importa: gap **positivo** = el punto único es mejor que su zona (señal de
  pico); gap **negativo o cero** = operar la zona rinde igual o mejor (señal de meseta). No hay umbral.
- Las candidatas se eligen por su Ret/DD de **build** y la mezcla se mide sobre **todo** el histórico: la
  parte de build de esa comparación está contaminada por la selección; la de oos1 y oos2 no.
- **Esta tabla es una mirada a `oos2`.** Se ve el neto total de cada madre con el tramo reservado dentro
  (en 18.5.355 el oos2 de la madre es −3.902; en 19.2.363, −1.136).
- El Sharpe es de la curva diaria con todos los días (también los que no opera), sin costes de financiación
  añadidos y sin tipo libre de riesgo.

### 3.9 Lo que la ventana enseña, en resumen

| columna | de dónde sale | en esta corrida |
|---|---|---|
| `point` | A1 sobre la vecindad | «Sin dato» × 10 |
| `surface` | A3 | «Sin dato» × 10 |
| `temporal` | B2, tres palabras | con dato real sólo en 5; en C, sin ninguno |
| `variants`, `dropped` | filtro | §1.3 |
| `r2` | ajuste **local** | vacío × 10 |
| `roughness` | rugosidad local de **toda la nube** | 0,07 a 0,44 |
| `gap` | C1 | 0,000 × 10 |
| `rho_median`, `drift_median` | B2 | sólo en 5 |

---

## 4. El criterio cargado y por qué

### 4.1 Criterio que decide: ninguno

| dónde tendría que estar | qué hay |
|---|---|
| `pipeline/autopilot/criteria.yaml` | entradas "8", "10", "11.5", "12", "14", "16". Para el 16.5, un comentario (`:18`) y nada más |
| `pipeline/autopilot/facts.py` | `--step` admite 8, 10, 12, 14 y 16 |
| hechos en disco | 0 de 164 `hechos.parquet` con claves de la nube |
| veredicto del sobre | `None` |
| paso 20 (`blindJoint`) | lee `wfc`, `cscv`, `marketSurfaces`, `wfm` |

**Consecuencia para la doctrina «un hecho que falta es Limbo»:** hoy no aplica, porque ninguna regla pide
un hecho de la nube. El día que una regla lo pida, **las diez madres de esta corrida irían a Limbo** por
A1 y A3 «Sin dato».

### 4.2 Los umbrales de diagnóstico

Son los que eligen la palabra. `config.yaml` dice de ellos que deben fijarse «antes de leer la nube»; los
tres del registro llevan `set_by: agente`, fecha 2026-09-24, sin calibración.

| umbral | valor | dónde | para qué palabra |
|---|---|---|---|
| `rank_high` | 0,95 | `ledger/thresholds.yaml:47-66` | q mínimo para hablar de pico o meseta |
| `plateau_low` | 0,15 | registro | π por debajo = pico |
| `rho_low` | 0,20 | registro | ρ mediana por encima = orden persistente |
| `roughness_high` | 0,35 | `config.yaml:40` | 1 − R² local |
| `local_roughness_high` | 0,35 | `config.yaml:41` | rugosidad sin modelo |
| `slope_high` | 1,0 | `config.yaml:42` | óptimo descentrado |
| `drift_high` | 0,20 | `config.yaml:44` | deriva alta |
| `fraction_low` | 0,50 | `config.yaml:45` | mínimo de f_y para «gana en casi todos» |

Y los parámetros que no son umbrales pero deciden igual o más:

| parámetro | valor | dónde | efecto en la corrida |
|---|---|---|---|
| radio de la vecindad | 2 pasos | `config.yaml:20` | 0 vecinas en las diez |
| δ de la banda | 0,20 | `config.yaml:21` | banda de 0,06 (F) a 1,73 (G) |
| mínimo de operaciones en build | 30 | `config.yaml:14` | no quita ninguna (ya pasó el suelo de 100) |
| días activos mínimos por año | 60 | `config.yaml:30` | 5 madres con ≤ 1 año |
| parte superior para el centroide | 10 % | `config.yaml:31` | 27 a 49 variantes por año |
| K de la mezcla | 8 | `config.yaml:34` | K = 1 en las diez |
| vecinas para la rugosidad local | 8 | `config.yaml:24` | — |
| métrica | `ReturnDDRatio (build)` | `config.yaml:13` | todo es dentro de muestra |

### 4.3 Qué dirían esos umbrales sobre las diez madres

Como la vecindad está vacía, la única manera de ver los umbrales trabajar es aplicarlos **a la nube
entera**. **Esto no es lo que hace el estudio**; es una cuenta mía para que veas el tamaño de cada umbral.

| lectura | umbral | madres que marcaría (de 10) | cuáles |
|---|---|---|---|
| Pico | q ≥ 0,95 y π ≤ 0,15 | 1 | G |
| Meseta | q ≥ 0,95 y π > 0,15 | 0 | — |
| Sin destacar | q < 0,95 | 9 | el resto |
| Rugosa, con `or` (el código) | 1 − R² **global** ≥ 0,35 o local ≥ 0,35 | 5 (7 con el R² ajustado) | 13.3.390, F, 16.5.352, 18.5.355, 19.2.363 |
| Rugosa, con `and` (los textos) | las dos | 2 (3 con el R² ajustado) | F, 16.5.352 |
| Orden persistente | ρ mediana ≥ 0,20 | 0 de las 5 con dato | — |
| Gana en casi todos | mín f_y ≥ 0,50 | 1 de las 5 con dato | 3.9.284 (5 años) |
| Deriva alta | deriva mediana ≥ 0,20 | 3 de las 5 con dato | 13.3.390, 16.5.352, 3.9.284 |

**Cómo leerlo.** Las filas de «Rugosa» usan el R² de la nube entera, que la palabra no leería, y son
frágiles: F entra por 0,351 y 0,358 frente a 0,35. Con estos umbrales, la lectura de punto casi nunca dice «Meseta» (hay que ser la mejor),
la de orden nunca dice «persistente» y la de anchura sólo dice «gana en casi todos» cuando hay pocos años.
**Son umbrales que casi sólo pueden dar avisos.** Ninguno se ha contrastado con qué madres aguantaron
después.

### 4.4 Qué haría falta para que una regla fuera posible

No es una propuesta; es la lista de lo que hoy impide escribirla.

1. Que A1 y A3 **tengan dato**: hoy no lo tienen en ninguna madre.
2. Que la nube **escriba hechos** y `facts.py` los aplane.
3. Que el autopiloto **la lance** tras recoger las variantes.
4. Que las palabras de B2 **distingan «sin dato» de «aviso»**.
5. Decidir si la nube puede mirar `oos2`.

---

## 5. Lo que no cuadra o no está medido

Ordenado de más a menos peso para una decisión.

### 5.1 La vecindad de la nube y la del diseño no son la misma

- La nube: caja de 2 pasos alrededor de **la madre** (`model/neighbourhood.py:22`).
- El diseño: rombo de 2 pasos alrededor del **centro de la meseta** (`sqx/variants/design/strata.py:42-72`,
  `levels.py:109-122`).
- **Efecto:** A1, A3 y C1 vacías en las diez madres. Mientras siga así, el estudio no puede dar dato salvo
  coincidencia.

### 5.2 «Un paso significa lo mismo en cada parámetro» ya no es verdad

- Lo dicen `studies/optimisation/cloud/README.md:55-57` y `config.yaml:18-19`.
- `levels.py:16-45` da a un entero todos los enteros del tramo.
- **Efecto:** el radio 2 es ±2 barras en un periodo con 88 valores posibles y ±16 % en un multiplicador
  con diez niveles. Aunque se arreglara el centro, la vecindad sería muy estrecha en unos ejes y ancha en
  otros.

### 5.3 B2: calculada, etiquetada y escondida

- `contract.py` pinta tres pestañas; el README (`:27`), la descripción del estudio y el manual
  (`39-nube-de-parametros.md`) hablan de cuatro bloques. La pestaña se retiró el 2026-10-02.
- `summary` sigue llevando `temporal`, `periods`, `rho_median`, `drift_median` (`one.py:103-111`) y la
  ventana los enseña como columnas.
- Sin años legibles, las palabras son las del «si no» (`call.py:82-85`). **No hay «Sin dato» en B2.**
- El suelo de 60 días activos no está calibrado para estrategias de 20-40 operaciones al año.

### 5.4 «Rugosa»: `or` en el código, «las dos» en los textos

- `verdict/call.py:58-59` frente a `model/README.md:19-20`, el docstring de la función y el manual.
- Hoy no cambia nada: la palabra es «Sin dato» antes. Sobre el R² de la nube entera —que no es lo que el
  código lee— serían 5 de 10 frente a 2 de 10, con una madre en el filo (§4.3).
- Además mezcla el R² de la vecindad con la rugosidad de toda la nube (`one.py:64`), y el R² ajustado
  (`surrogate.py:43`) no se usa.

### 5.5 El R² que acompaña a los Sobol no se publica

- Sobol sale del ajuste global (`one.py:44`, `:46`); `r2` publicado es el local (`one.py:105`).
- El README (`:65-68`) dice que el R² va junto a los índices para saber cuánto fiarse.
- **Efecto:** no se ve que el ranking de 16.5.352 describe un 17 % de la dispersión.

### 5.6 Los congelados entran en el ranking y en los mapas

- La nube llama vivo a todo lo que varía (`space.py:55`); los congelados varían en el estrato de cobertura.
- Sólo varían ahí: sus términos cruzados quedan mal identificados y el Sobol los extrapola a todo el
  cubo (§3.4; mecanismo comprobado en la revisión).
- **Efecto:** F tiene sus dos primeros puestos ocupados por parámetros inertes; C y E, el 3.º y el 4.º.
  Sin ellos, F da un ranking limpio (Σ primer orden 0,92) y C pasa de 0,65 a 0,97.
- El glosario (`contract.py:18-19`) lee «total muy por encima del primer orden» como «lógica afinada». En F
  es ese artefacto.

### 5.7 π y el «valor encogido» no hacen lo que dice el glosario

- π: `contract.py:15` «queda a menos de δ del punto elegido»; `plateau.py:128` cuenta todo lo que supera
  el suelo, mejores incluidas.
- Encogido: `contract.py:17` «encogido hacia su vecindad: el número que se lleva aguas abajo»;
  `plateau.py:141` es la mediana, y no alimenta ninguna decisión: sólo se enseña en A1
  (`contract.py:70`, `:110`).
- q usa «menor o igual» e incluye a la madre (`plateau.py:112`): con pocas vecinas está inflado.

### 5.8 `oos2`

- `docs/AgentPDFs/WORKFLOW.md:66-70`: la nube «corta las curvas donde empieza `oos2`».
- `inputs/cloud.py:79-80`: sólo corta si `core.assetdata.enforced()`, que exige `ALGO_AUTONOMOUS=1`.
- La pone el autopiloto (`pipeline/autopilot/run.py:235`, decisión D4 del 2026-10-04;
  `pipeline/autopilot/README.md:141`). **No la pone una ejecución a mano ni desde la ventana**, y el
  autopiloto no lanza la nube. El docstring de `core/assetdata.py:21-27` («Nothing sets it today») está
  desfasado.
- El manual dice lo contrario que `WORKFLOW.md`: «mira todo el histórico, oos2 incluido (dueño,
  2026-09-28)».
- **Efecto:** en estas diez, C1 y B2 leyeron 2023-11-28 → 2026-09-29: no cortaron, y el motivo probable
  es que se lanzaron fuera del autopiloto (no sé quién las lanzó). No queda anotado como mirada. **El
  corte depende de quién lance el estudio**, no de una decisión escrita en él.

### 5.9 Los `Shf1` se varían

- La regla «un shift nunca se mueve» sólo reconoce `…Shift1` (`levels.py:5`, `:69`;
  `studies/breakage/spp/run.py:108`, `:117`).
- Vivos y con peso: `ATRPercentCrsUPShf1` 0,051 (13.3.390), `ChoppinessIndRsnShf1` 0,069 (16.5.352),
  `ATRPercentRnkRsnShf1` 0,100 (3.9.284), `KCBarOpnAftOpnShf1` (E, 6 niveles).
- Esto nace en el paso 16 y llega aquí; afecta también a WFC, CSCV y WFM, que usan las mismas variantes.

### 5.10 Menores

| qué | dónde |
|---|---|
| Comentario «menos de 50 operaciones en total» frente a `min_trades_total: 100` | `assets/_build.yaml:353` y `:368` |
| Fila 16.5: «corre en el `Retester` de serie» — `ran.json` muestra los bancos `WFC_Build`, `WFC_OOS1`, `WFC_OOS2` del propio proyecto | `docs/AgentPDFs/WORKFLOW.md:45` |
| El docstring de `contract.py` dice «C1 first, then A1, then A2 and A3»; la descripción, «Cuatro preguntas» | `contract.py:1` |
| ρ entre años legibles consecutivos, no años consecutivos | `measure/stability.py:73-77` |
| El manual enseña el bloque B2, la ruta antigua `AlgoData/pipeline/XAUUSD/…` y un ejemplo con vecindad de 253 variantes que el diseño actual no produce | `AlgoData/manual-fuentes/39-nube-de-parametros.md` |
| Si la vecindad tiene menos de 2 puntos, el dibujo pinta la nube entera sin avisarlo en el título | `contract.py:80` |

### 5.11 No medido

- **El ruido del Ret/DD de una variante.** Cada variante tiene 135-300 operaciones en build; cuánto baila
  su Ret/DD por azar no está medido. Dos variantes vecinas comparten casi todas las operaciones, así que
  su diferencia puede bailar mucho menos que cada una por separado. Sin eso no se sabe si δ = 0,20 es una
  banda ancha o estrecha.
- **Si alguna lectura de la nube predice algo.** Ningún umbral se ha comparado con qué madres aguantaron
  en oos1.
- **A1 y A2 en oos1.** El estudio sólo lee build. Calculado por mí, con la misma cuenta de q sobre la nube
  entera:

  | madre | q en build | q en oos1 | π en build | π en oos1 |
  |---|---|---|---|---|
  | 13.3.390 | 0,361 | 0,931 | 0,726 | 0,099 |
  | 18.5.355 | 0,663 | 0,350 | 0,441 | 0,682 |
  | E | 0,542 | 0,884 | 0,540 | 0,182 |
  | G | 0,972 | 0,928 | 0,061 | 0,323 |
  | C | 0,680 | 0,721 | 0,359 | 0,386 |
  | F | 0,849 | 0,845 | 0,182 | 0,184 |

  La posición de la madre en su nube cambia de un tramo al otro en la mitad de los casos. **Sin banda de
  ruido no se puede decir cuánto de ese cambio es real**: la madre hace entre 58 y 187 operaciones en oos1
  (dato de la revisión) y nadie ha medido cuánto baila q con tan pocas.
- **Si los congelados son inertes en toda la nube** o sólo en la madre: los pares inertes lo prueban en el
  punto de la madre.
- **Qué es exactamente un «día activo»** en `dailyEquity` (§3.7).
- **Quién lanzó la nube el 2026-10-04 a las 22:37.** En `pipeline/` no hay ninguna llamada a la nube, así
  que lo probable es una ejecución a mano o desde la ventana; no lo he podido confirmar.
- **Por qué se retiró la pestaña B2.** Sólo he visto el cambio, no el motivo.

---

## 6. Cierre

### 6.1 Las reglas, en una tabla

| lectura | regla que decide | palabra de diagnóstico | umbral | fijado por |
|---|---|---|---|---|
| A1 punto | **ninguna** | Pico / Meseta / Sin destacar / Sin dato | q ≥ 0,95 · π ≤ 0,15 | agente, 2026-09-24 |
| A2 Sobol | **ninguna** | (ninguna) | — | — |
| A3 superficie | **ninguna** | Suave / Rugosa / Descentrado / Sin dato | 0,35 · 0,35 · 1,0 | `config.yaml`, sin firma |
| B2 años | **ninguna** | tres palabras, sin «Sin dato» | 0,50 · 0,20 · 0,20 | agente (ρ) y `config.yaml` |
| C1 mezcla | **ninguna** | (ninguna) | — | — |

### 6.2 El resultado sobre la población real

Diez madres de `Trade_NIKKEI225_M30_volatilidadL`:

| | nº de madres |
|---|---|
| con A1 legible | 0 |
| con A3 legible | 0 |
| con C1 que mezcle algo | 0 |
| con B2 de al menos 5 años | 5 |
| movidas de estado por este paso | 0 |

**El paso 16.5, tal como está, no cuesta ninguna estrategia y no informa de ninguna.** La parte cara —500
retests por madre en tres tramos— no se pierde: la usan los pasos 17, 18 y 19.

Lo que sí se puede sacar de esta corrida, aunque el estudio no lo diga:

- **G es la mejor de su nube y está casi sola** (q 0,97, π 0,06 en build), con un único parámetro
  (`ZScrStrDbl31`) llevando el 65 % del resultado. En oos1 su compañía sube a 0,32.
- **13.3.390 y 16.5.352 están por debajo de la mediana de su propia nube** (q 0,36 y 0,47): el genético no
  eligió un máximo, y la mayoría de sus variantes las supera en build.
- **F tiene una nube que pierde**: mediana −0,31, sólo el 27 % de las variantes con Ret/DD positivo en
  build. La madre (0,30) es de las mejores de un vecindario malo.
- **La mediana de ρ entre años es prácticamente cero en las cinco madres con dato**: no hay señal de que
  el orden de las variantes persista (un valor suelto no se puede leer; §2.10).

### 6.3 Las decisiones que quedan

Cada una con lo que cuesta o cambia en madres, sobre estas diez.

| # | decisión | opciones | efecto en las 10 madres |
|---|---|---|---|
| 1 | **¿Cuenta el 16.5 para el veredicto?** | (a) sigue siendo sólo consulta · (b) escribe hechos y entra en el paso 20 | (a) 0 madres afectadas. (b) hoy, las 10 a Limbo por «Sin dato» |
| 2 | **¿Alrededor de qué punto se mide la vecindad?** | (a) la madre, como ahora · (b) el centro de la meseta, donde están las variantes · (c) fabricar el estrato denso alrededor de la madre | (a) 0 de 10 con dato. (b) A1 tendría puntos en 9 de 10 (cajas de 17 a 99; 13.3.390 perdió el estrato entero), pero la madre no cae en ninguna caja: q y π exigen cambiar código, y la pregunta pasa a ser «¿la madre se parece al centro?». A3 sólo tendría dato en 5 (10.11.484, 16.5.352, 18.5.355, E, 3.9.284) y casi saturado: en E, 79 puntos para 55 coeficientes dan «suave» con puro ruido (comprobado en la revisión). (c) obliga a repetir el 16.5: 500 retests por madre |
| 3 | **¿Qué radio?** (si se queda en la madre) | 2 · 5 · 10 pasos | con 2: 0 de 10. Con 5: 6 de 10 con alguna vecina, de 1 a 19. Con 10: 8 de 10 para A1; **A3 sólo en 4** (16.5.352, 18.5.355, 19.2.363, E), porque exige más vecinas que coeficientes |
| 4 | **¿Qué es «un paso»?** | (a) un entero · (b) una fracción del tramo | no medido; cambia qué entra en la vecindad en todos los ejes enteros |
| 5 | **«Rugosa»: ¿una medida o las dos?** | `or` (código) · `and` (textos) | hoy ninguno («Sin dato» antes). Sobre el R² de la nube entera, que el código no lee: 5 frente a 2 de 10 (7 y 3 con el R² ajustado; F en el filo) |
| 6 | **¿Qué exige «Meseta»?** | (a) ser casi la mejor (q ≥ 0,95) · (b) estar acompañada, sea cual sea el puesto | con (a), 0 mesetas y 9 «Sin destacar». Con (b) y π > 0,15: 9 de 10 |
| 7 | **π: ¿cuentan las que superan a la madre?** | (a) sí, como ahora · (b) sólo la banda de ±δ | C pasa de 0,36 a 0,04; 16.5.352 de 0,59 a 0,06; G de 0,06 a 0,03 |
| 8 | **B2: ¿se recupera, se arregla o se borra?** | (a) borrar cálculo y columnas · (b) volver a pintarla con «Sin dato» · (c) bajar el suelo de días | (a) nada cambia de estado. (c) con 20 días: las 10 con 8-15 años, las 10 «Sostenida» y «Rebaraja» |
| 9 | **¿La nube mira `oos2`?** | (a) sí (tu decisión del 2026-09-28) y se corrige `WORKFLOW.md` · (b) no, y se corta siempre | con (b), cuatro madres pierden su único año legible de B2 |
| 10 | **¿Entran los congelados en el Sobol?** | (a) sí · (b) sólo los vivos del brief | con (b) cambia el ranking entero de F (Σ primer orden de 0,13 a 0,92, tres vivos a ≈ 0,28); en C el Σ de primer orden pasa de 0,65 a 0,97; E pierde el 3.º y 4.º |
| 11 | **¿Los `Shf1` se mueven?** | (a) sí · (b) se tratan como `Shift1` | afecta a 4 madres y a los pasos 16 a 19; obliga a repetir |
| 12 | **¿Sobre qué tramo se lee la superficie?** | build · oos1 · los dos | la posición de la madre cambia mucho en 3 de las 6 madres comparadas (§5.11) |

Si sólo vas a tomar tres: la **1** (si no cuenta, el resto puede esperar), la **2** (sin ella no hay dato)
y la **9** (es una regla dura tuya la que está en juego).

### 6.4 El límite que no cambia

Decidas lo que decidas arriba:

- **400-500 puntos en un espacio de 5 a 15 dimensiones son muy pocos.** La caja de radio 2 con 15
  parámetros tiene 30.000 millones de puntos. Ninguna vecindad razonable estará nunca «llena»; la lectura
  de la zona siempre será de unas decenas de variantes.
- **Cada punto es ruidoso, y no se sabe cuánto.** El Ret/DD de una variante sale de 135-300 operaciones.
  El tamaño de ese ruido no está medido (§5.11), ni cuánto se compensa entre vecinas que comparten
  operaciones.
- **La superficie es de dentro de muestra.** Todo lo que no sea B2 y C1 se mide en el tramo donde se
  construyó la madre. Una meseta en build no promete una meseta fuera; la tabla de §5.11 apunta ahí, sin banda de ruido.
- **El orden fino entre variantes no se puede aprender con años sueltos.** Las variantes de una madre valen por 7 a 39
  independientes y el margen de ρ entre años es de ±0,3 a ±0,8; con eso, «cuál es la mejor variante» no es una pregunta que estos datos contesten. Lo que la nube sí puede
  contestar, cuando tenga vecinas, es la pregunta gruesa: **si alrededor de la madre se gana o se pierde.**
