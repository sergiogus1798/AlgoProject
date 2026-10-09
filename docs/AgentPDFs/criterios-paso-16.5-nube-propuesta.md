# Paso 16.5 — Variantes y nube de parámetros: propuesta de rediseño

**Fecha:** 2026-10-07 · **Alcance:** la fábrica de variantes (`sqx/variants/`) y la nube (`studies/optimisation/cloud/`).
**Referencia:** `criterios-paso-16.5-nube-de-parametros-2026-10-07`. Complementa las propuestas de los pasos 14 (`criterios-paso-14-mc-retest-propuesta.md`), 16 (`criterios-paso-16-spp-propuesta.md`) y 17 (`criterios-paso-17-wfc-propuesta.md`).

---

## 0. La pregunta del paso

El 16.5 deja de juzgar. Tiene dos papeles:

1. **Fábrica:** un lote fijo de variantes de cada madre, retesteado en build, oos1 y oos2, con todas sus operaciones. Es la materia prima del WFC (17), el CSCV (18), las superficies por mercado (18.5) y la WFM (19). Es lo único que empareja la misma combinación de parámetros en varias ventanas: el SPP no puede hacerlo (SQX no lo permite).
2. **Mapa:** qué parámetros mueven el resultado (Sobol), como diagnóstico.

**No tiene regla** (`rules: []`) y no corta nada.

### 0.1 Reparto de la robustez de parámetros

| paso | pregunta | papel |
|---|---|---|
| 14 (T1) | ¿la madre es un pico? (±15 % / ±30 %, alrededor de la madre) | **juzga** |
| 16 (SPP) | ¿cómo rinde la idea con parámetros razonables? ¿dónde está la meseta? | anota, diseña y descarta los casos horrendos |
| **16.5** | **fabricar el lote; mapa de sensibilidad** | **anota** |
| 17 (WFC) | ¿elegir por IS dentro de la familia sirve fuera de muestra? | **juzga** (bloque ciego) |

---

## 1. Lo que se quita

| lectura | qué hacía | en la corrida | decisión | por qué |
|---|---|---|---|---|
| **A1** pico / meseta | rango y compañía de la madre en su vecindad | «Sin dato» en las 10 | **quitar** | lo juzga T1 del paso 14, con vecinas emparejadas alrededor de la madre. La vecindad de la nube (caja de 2 pasos alrededor de la madre) y la del diseño (rombo alrededor del centro de la meseta) no coincidían |
| **A3** rugosidad / pendiente | superficie local alrededor de la madre | «Sin dato» en las 10 | **quitar** | lo mismo; además, con 105–136 coeficientes y pocas vecinas, el R² sube solo |
| **B2** lectura por años | orden, anchura y deriva año a año | calculada y escondida; 5 de 10 sin años legibles | **quitar** | la ρ entre años tiene un margen de ±0,3 a ±0,8 (las variantes valen por 7 a 39 independientes). La estabilidad en el tiempo es la pregunta de la WFM (19) |
| **C1** mezcla | Sharpe de K vecinas frente a la madre | vacía en las 10 (K = 1) | **aparcar** | puede tener sentido para construir cartera; no para juzgar aquí |
| **A2** Sobol y mapas | quién mueve el resultado | lo único con contenido | **mantener**, arreglado (sección 3) | |

---

## 2. La fábrica

### 2.1 La caja: sólo build

La caja donde se fabrican las variantes es la **meseta del SPP IS** (perfil por parámetro, sección 3 de la propuesta del paso 16). Se diseña **sólo con build**:

- si la caja se dibujara mirando oos1, la composición abierta del WFC (build → oos1+oos2) quedaría contaminada por el propio diseño;
- para la composición que decide (build+oos1 → oos2) daría igual: oos2 sigue limpio. Diseñando con build no se pierde nada.

### 2.2 Qué parámetros se mueven

| tipo | tratamiento |
|---|---|
| **vivos** (según el SPP) | se mueven dentro de su tramo de meseta |
| **congelados** (no cambian ninguna operación) | **fijos** en el valor de la madre, en **todas** las variantes. Hoy se mueven en el estrato de cobertura y estropean el Sobol: en F los dos primeros del ranking son congelados; sin ellos, el Σ de primer orden pasa de 0,13 a 0,92 |
| **desplazamientos** (`…Shift…` **y** `…Shf…`) | **fijos**. Hoy la regla sólo reconoce `Shift1`, y `Shf1` se mueve (con índice total de 0,05 a 0,10 en tres madres) |

### 2.3 El diseño: cobertura uniforme

Se sustituyen los estratos actuales (20 % vecindad alrededor del centro de la meseta, 60 % factorial en las esquinas, 20 % cobertura) por **un hipercubo latino** sobre los parámetros vivos, dentro de la caja.

**Por qué:** el WFC pregunta qué pasa si un optimizador elige dentro de la familia. Para eso hace falta una **muestra representativa de lo que se podría elegir**, no esquinas ni un amontonamiento en un punto. Además, el ρ cambia con el reparto de estratos (en C: 0,83 en el factorial, 0,12 en la vecindad, 0,67 junto), y con un diseño uniforme ese efecto desaparece.

Los parámetros enteros toman el entero más cercano al valor del hipercubo.

### 2.4 Cuántas variantes

Con $k$ parámetros vivos, la superficie cuadrática del mapa tiene

$$p = 1 + 2k + \frac{k(k-1)}{2}$$

coeficientes, y conviene tener al menos 8 variantes por coeficiente. El número de variantes por madre es

$$n = \min\!\Big(5000,\; \max\big(1000,\; 8\,p\big)\Big)$$

| vivos $k$ | coeficientes $p$ | $8p$ | variantes $n$ |
|---|---|---|---|
| 5 | 21 | 168 | 1.000 |
| 10 | 66 | 528 | 1.000 |
| 13 | 105 | 840 | 1.000 |
| 15 | 136 | 1.088 | 1.088 |
| 20 | 231 | 1.848 | 1.848 |
| 30 | 496 | 3.968 | 3.968 |
| ≥ 35 | ≥ 666 | ≥ 5.328 | 5.000 (tope) |

Si se llega al tope ($8p > 5000$), el mapa avisa de que tiene menos de 8 variantes por coeficiente.

**Por qué no hacen falta más para la significancia.** La incertidumbre de las pruebas que leen el lote no la pone el número de variantes, sino el único camino de precios que todas recorren juntas. Para la ρ del WFC, aproximadamente:

$$\sigma_\rho^2 \approx \sigma^2_{\text{camino}} + \frac{(1-\rho^2)^2}{n}$$

Con $\sigma_{\text{camino}}$ medido en la corrida de referencia (de 0,09 a 0,41, mediana 0,26) y $\rho \approx 0$:

| variantes $n$ | $\sigma_{\text{camino}} = 0{,}09$ | $0{,}26$ | $0{,}41$ |
|---|---|---|---|
| 500 | 0,100 | 0,264 | 0,412 |
| 1.000 | 0,095 | 0,262 | 0,411 |
| 5.000 | 0,091 | 0,260 | 0,410 |

Pasar de 1.000 a 5.000 mejora el error un 4 % en el mejor caso y nada en la mediana. El documento del WFC lo midió directamente: con la mitad de las variantes de C, la desviación del nulo pasó de 0,41 a 0,43.

**Coste:** cada variante se retestea en tres tramos y en el activo principal más los mercados aleatorios. Bajar de 5.000 a unas 1.000 divide el tiempo de SQX por cinco. Si el 18.5 o el 19 necesitan más, se decide allí.

### 2.5 Controles

Los **canarios** (variantes rotas a propósito) y los **pares inertes** (la madre con un congelado en el extremo) se mantienen: comprueban que la cadena lee bien los parámetros. Pero **no entran en ningún análisis** (hoy entran en el WFC: F lleva 9 copias exactas de la madre).

La **madre** entra en el lote como una variante más (`P00000`).

### 2.6 Piloto, retest y operaciones

- **Piloto:** como hoy (descarta niveles que dejan la estrategia sin operar).
- **Retest:** build, oos1 y oos2, con los costes calibrados MT5–SQX.
- **Se guardan todas las operaciones** de cada variante, en el activo principal y en los mercados aleatorios. Con ellas, cada estudio calcula el **exceso con la deriva por año** (como en el paso 14), que es la medida que usan el WFC y el mapa.

### 2.7 oos2: sellado

Las variantes se corren en oos2, pero **ese tramo queda sellado**: sólo lo abren los estudios del bloque ciego (17, 18, 18.5, 19), después de que sus criterios estén escritos en `criteria.yaml`.

Hoy el corte de oos2 depende de quién lance el estudio (`ALGO_AUTONOMOUS=1`): en la corrida de referencia, la nube leyó oos2 sin dejarlo anotado. **El sellado debe estar en el propio estudio**, no en una variable de entorno.

La nube (el mapa) **no lee oos2 nunca**.

### 2.8 Suelos de operaciones

Los suelos actuales (100 en total en la cosecha; 30 en build en la nube; 50 por lado en el WFC) se sustituyen por los mismos que el WFC (sección 2 de su propuesta):

| lado | suelo |
|---|---|
| dentro de muestra | $15 \times k$ operaciones, con $k$ = parámetros vivos |
| fuera de muestra | 10 por año de la ventana |

La cosecha no descarta variantes: guarda todas y cada estudio aplica el suelo de su ventana. Si la madre no cumple el suelo, se avisa y el suelo no se aplica.

---

## 3. El mapa: Sobol y mapas de calor

### 3.1 Qué se calcula

Sobre la nube (sin controles, sin duplicados exactos y con el suelo de dentro):

- **métrica:** exceso por año en **build** (dentro de muestra). Se anota también en oos1, como lectura secundaria;
- **superficie:** cuadrática sobre los parámetros **vivos** (los congelados ya no varían);
- **índices de Sobol:** de primer orden y total, sobre esa superficie;
- **mapas de calor:** mediana de la métrica por celda, para los pares de los 2 a 4 parámetros con mayor índice total.

### 3.2 Cuándo se puede leer

Los índices se calculan sobre la superficie ajustada: si la superficie explica poco, el ranking describe ese poco. Por eso se publica, al lado de los índices:

- el **R² ajustado** del ajuste global (hoy no se publica; se publica el local, que está vacío);
- su **referencia barajada**: el R² ajustado que sale barajando la métrica entre las variantes (200 tiradas). Con 105 coeficientes y 458 variantes, ruido puro da un R² de alrededor de 0,23.

El ranking **sólo se lee** si el R² ajustado supera el p95 de su referencia barajada. Si no, se publica con el aviso «sin estructura distinguible del ruido».

### 3.3 Para qué sirve

Es un diagnóstico, no un criterio:

- dice qué parámetros importan (en G, un solo umbral lleva el 65 %);
- si los primeros órdenes suman cerca de 1, cada parámetro actúa por su cuenta; si los totales suman mucho más de 1, la estrategia depende de combinaciones finas, lo que es una señal de fragilidad para revisar a mano.

---

## 4. Hechos y criterio

```yaml
"16.5":
  cut: null
  rules: []
```

**Hechos que se escriben** (para el informe): número de variantes por tramo tras los suelos, parámetros vivos, R² ajustado y su p95 barajado, índices de Sobol de primer orden y totales por parámetro, y si el ranking es legible.

**El autopiloto lanza la nube** después de recoger las variantes. Hoy no la lanza.

---

## 5. Decisiones abiertas

1. **Hipercubo latino o secuencia de Sobol** para el diseño: las dos cubren bien; el hipercubo es más simple.
2. **8 variantes por coeficiente**: es una convención razonable para una cuadrática; se puede revisar si el R² ajustado de las primeras corridas sale sistemáticamente cerca de su referencia barajada.
3. **Métrica del mapa:** exceso por año en build (propuesta) o Sharpe del exceso.
4. **Mercados aleatorios:** si el número de variantes por mercado puede ser menor que en el activo principal. Se decide en el 18.5.
