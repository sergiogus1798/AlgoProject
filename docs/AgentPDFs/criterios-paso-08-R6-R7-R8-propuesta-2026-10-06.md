# Paso 8 — Propuesta de rediseño de R6, R7 y R8

**Fecha:** 2026-10-06 · **Alcance:** reglas R6 (drawdown), R7 (años positivos) y R8 (concentración) de `pipeline/autopilot/criteria.yaml`.
**Referencia:** `criterios-paso-08-puerta-oos-2026-10-06` (apartados 3.11, 3.12 y 3.13). Complementa `criterios-paso-08-R5-R5b-R5c-propuesta.md`.

---

## 0. Resumen de cambios

| regla | hoy | propuesta |
|---|---|---|
| **R6** | DD máx oos1 / DD máx build ≤ 1,25, si no LIMBO | **percentil del DD de oos1** en un bootstrap por bloques del build, con la media desplazada a la de oos1 |
| **R7** | ≥ 3 años positivos en oos1, si no LIMBO | **homogeneidad del exceso por trimestres**: estadístico Q con nula por permutación |
| **R8** | mejor trimestre ≤ 50 % del beneficio, si no LIMBO | **t de R3 sin el mejor trimestre** ($t_{-Q^*}$) y **sin las 3 mejores operaciones** ($t_{-3}$) |

Problema común de las tres reglas actuales: son cocientes o recuentos sin un modelo de qué valor cabe esperar, así que su escala depende de la duración de los tramos y del tamaño del beneficio total. Además, por la cascada de la puerta, a muchas estrategias les falta el dato (R6: 6.021 de 10.000; R7: 4.054; R8: 4.060). Las tres propuestas se calculan para **todas** las estrategias.

---

## 1. R6 — El drawdown de oos1 es el esperable

### 1.1 Problemas de la regla actual

- **Compara tramos de distinta duración** (NIKKEI225: 8,3 años de build frente a 4 de oos1). El drawdown esperado crece con el número de operaciones, así que un cociente < 1 sale casi siempre por construcción.
- **Mezcla la caída de la ventaja con el cambio de riesgo.** La media del build está inflada por la selección; con menos media en oos1, el drawdown crece aunque el riesgo sea el mismo. Esa caída ya la juzgan R3 y R5d.
- **Sin dato en el 60 % de la población**, por la cascada.

### 1.2 De qué depende el drawdown

El drawdown máximo depende de tres cosas:

1. **la media** por operación (más media, recuperación más rápida),
2. **la dispersión** (más dispersión, caídas más hondas),
3. **el orden de las operaciones**: si las pérdidas se agrupan, el drawdown es mucho mayor con la misma media y la misma dispersión.

Para un paseo aleatorio con deriva, sin agrupamiento, hay una aproximación (Magdon-Ismail et al., 2004). Con media $\mu$ y desviación $\sigma$ por operación y $n$ operaciones:

$$E[\text{MDD}] \approx \frac{2\sigma^2}{\mu}\left(\tfrac14 \ln x + 0{,}49\right), \qquad x = \frac{\mu^2 n}{2\sigma^2}$$

Estrategia A en oos1 ($\mu = 196$ USD, $\sigma = 951$ USD, $n = 196$): $x = 4{,}17$, $E[\text{MDD}] \approx 7.800$ USD $= 7{,}8$R. El observado fue 6,8R.

La fórmula sirve de referencia, pero no incluye el punto 3 (el agrupamiento), que es justo lo que hace que un drawdown «se dispare». Por eso la propuesta usa un bootstrap por bloques.

> **Descartado:** un test sobre el cambio de varianza IS → OOS. Sólo mira el punto 2; no ve el agrupamiento de pérdidas, que es lo que dispara el drawdown (ver ejemplo 2 en 1.6).

### 1.3 Método

Pregunta: *con la ventaja que de verdad tuvo en oos1, ¿es normal un drawdown como el de oos1 para la forma de riesgo que la estrategia enseñó en el build?*

**Paso 1 — Desplazar la media del build a la de oos1.**

$$y_i = x_i - \bar{x}_{\text{IS}} + \bar{x}_{\text{OOS}}$$

$x_i$ son las operaciones del build en R. El desplazamiento cambia la media y deja intactos la dispersión, las colas y el orden.

Ejemplo de juguete (build con media 100 USD, oos1 con media 20 USD, se resta 80):

| build original | +300 | −100 | +200 | −200 | +400 | −150 | +250 | −50 | +350 | 0 |
|---|---|---|---|---|---|---|---|---|---|---|
| desplazada (−80) | +220 | −180 | +120 | −280 | +320 | −230 | +170 | −130 | +270 | −80 |

- Curva original: 300, 200, 400, 200, 600, 450, 700, 650, 1.000, 1.000 → MDD = 200
- Curva desplazada: 220, 40, 160, −120, 200, −30, 140, 10, 280, 200 → MDD = 340

Con las mismas operaciones y menos ventaja, el drawdown es un 70 % mayor.

**Por qué se desplaza:**

- Un drawdown mayor en oos1 puede venir de (1) **menos ventaja** o (2) **un riesgo distinto** (pérdidas más grandes o más agrupadas). La causa 1 ya la juzgan R3 y R5d. Desplazar la media neutraliza la causa 1 para que R6 juzgue sólo la 2. Es comparar a igualdad de ventaja, igual que la distancia de frenado de dos coches se compara a igual velocidad.
- La media del build casi siempre baja en oos1, aunque la estrategia sea buena: SQX eligió las mejores entre decenas de miles, y esa media incluye la suerte de haber sido elegida. Sin desplazar, R6 castigaría a casi todas por haber sido seleccionadas.

**Por qué no simular con las operaciones de oos1:** compararías el drawdown de oos1 consigo mismo, y el test no podría detectar ningún cambio.

**Paso 2 — Bootstrap por bloques.** Se construyen $B$ secuencias (p. ej. 5.000) de $n_{\text{oos}}$ operaciones, encadenando bloques de $L$ operaciones consecutivas de $y$ con inicio aleatorio. Los bloques conservan las rachas del build; un remuestreo operación a operación las rompería y subestimaría el drawdown. Longitud de bloque: $L \approx 5$–10, o $L \approx \sqrt{n_{\text{IS}}}$.

**Paso 3 — Percentil del drawdown observado.**

$$P_{\text{DD}} = \frac{\#\{\text{secuencias con MDD} \ge \text{MDD}_{\text{oos1}}\} + 1}{B + 1}$$

Todo en R (1R = 1.000 USD), sobre P/L de operaciones cerradas. Opcional: repetirlo con la curva de flotante si se quiere el drawdown que ve una cuenta de fondeo.

### 1.4 Criterio propuesto

| estado | condición |
|---|---|
| PASA | $P_{\text{DD}} > 0{,}10$ |
| LIMBO | $0{,}01 < P_{\text{DD}} \le 0{,}10$ |
| NO PASA | $P_{\text{DD}} \le 0{,}01$ |
| sin dato | LIMBO |

### 1.5 Subproducto para fondeo

El **percentil 95 del MDD simulado** es el drawdown que cabe esperar en el próximo tramo de igual duración. Es más honesto que el drawdown observado (el documento ya señala que el Monte Carlo da cerca del doble). Se propone guardarlo como hecho (`gate.scorecard.dd_esperado_p95_r`) y usarlo en R9c en lugar del drawdown observado.

### 1.6 Ejemplos (datos sintéticos)

**Build común:** 330 operaciones, media 0,30R, desviación 0,81R, colas gordas (t de Student, 4 grados de libertad).

**oos1:** 196 operaciones, media 0,19R, desviación 0,95R, $t = 2{,}77$, beneficio final +37R. **Las dos versiones tienen exactamente las mismas operaciones; sólo cambia el orden.**

**Simulación:** build desplazado a media 0,19R, 5.000 secuencias de 196 operaciones, bloques de 8.

| | Ejemplo 1 — se mantiene | Ejemplo 2 — falla |
|---|---|---|
| orden de las operaciones | normal | las 14 peores pérdidas dentro de una ventana de 28 operaciones |
| media / desviación / t | 0,19R / 0,95R / 2,77 | 0,19R / 0,95R / 2,77 |
| racha perdedora más larga | 5 | 7 |
| **MDD observado** | **5,6R** | **20,0R** |
| MDD simulado: mediana / p90 / p95 / p99 | 5,8 / 9,8 / 11,2 / 15,1 R | 5,8 / 9,8 / 11,3 / 15,2 R |
| $P_{\text{DD}}$ | 0,53 | 0,0012 |
| **resultado** | **PASA** | **NO PASA** |

Lecturas:

- **R3 no distingue los dos casos**: media, desviación, t y beneficio final son idénticos. La t mira el conjunto de operaciones; el drawdown, su orden. R6 aporta algo que no mide ninguna otra regla.
- **La racha perdedora más larga apenas cambia** (5 frente a 7). Lo que dispara el drawdown es la *densidad* de pérdidas en una ventana, no una racha seguida.
- **Efecto de no desplazar la media.** Simulando con la media del build (0,30R), en el ejemplo 1 la mediana simulada baja de 5,8R a 4,3R y el p99 de 15,1R a 11,9R. El 5,6R observado parecería un 30 % peor de lo esperado, pero esa diferencia es entera por la caída de la ventaja, no por el riesgo. Un caso intermedio (≈ 12R) pasaría a NO PASA sin motivo de riesgo.
- **Fondeo:** el p95 del ejemplo 1 (11,2R) es el doble del drawdown observado (5,6R).

---

## 2. R7 — El resultado es homogéneo en el tiempo

### 2.1 Problemas de la regla actual

- **No discrimina:** con 4 años, una moneda al aire saca 3 años positivos de 4 el 31 % de las veces; con 5 años, 3 de 5 el 50 %.
- **No pesa el tamaño:** un año «positivo» de +0,2R (C en 2021) cuenta igual que uno de +16R.
- **Es la t con menos potencia.** Con una t total $t$ repartida en $K$ años, la probabilidad de que un año sea positivo es ≈ $\Phi(t/\sqrt{K})$: contar años positivos es una versión degradada de R3.
- **El «3» significa cosas distintas** con 4 y con 5 años de oos1.

Lo que la regla quiere de verdad es **homogeneidad**: que el resultado no dependa de un régimen concreto.

### 2.2 Método: estadístico Q por trimestres

Se agrupa el **exceso por operación** de R3 (ya descontada la deriva) por trimestre natural de oos1: $K = 16$ en NIKKEI225, $K = 20$ en XAUUSD y forex. Con $n_k$ operaciones y exceso medio $\bar{e}_k$ en el trimestre $k$, exceso medio total $\bar{e}$ y desviación dentro de trimestres $\hat\sigma$:

$$Q = \sum_{k=1}^{K} \frac{n_k\,(\bar{e}_k - \bar{e})^2}{\hat\sigma^2}$$

Si el exceso es homogéneo, $Q \sim \chi^2_{K-1}$ aproximadamente. Un $Q$ grande dice que algunos trimestres son muy distintos de los demás.

**Nula por permutación.** Con colas gordas, la $\chi^2$ da demasiados positivos. Se saca la distribución nula barajando las operaciones entre trimestres (manteniendo $n_k$) unas 2.000 veces:

$$p_Q = \frac{\#\{Q_{\text{perm}} \ge Q_{\text{obs}}\} + 1}{2.000 + 1}$$

Trimestres con muy pocas operaciones (< 5): se agrupan con el siguiente.

**Ventajas:** usa la magnitud de cada trimestre (no sólo su signo), tiene más grados de libertad que contar 4 años, y significa lo mismo con 4 o con 5 años de oos1.

### 2.3 Criterio propuesto

| estado | condición |
|---|---|
| PASA | $p_Q > 0{,}05$ |
| LIMBO | $p_Q \le 0{,}05$ |
| NO PASA | — (no descarta) |
| sin dato | LIMBO |

Sin descarte porque algo de heterogeneidad entre regímenes es normal en trading, y con 3–5 años la potencia es baja.

---

## 3. R8 — La ventaja no depende de un trimestre ni de unas pocas operaciones

### 3.1 Problema de la regla actual

El denominador es el beneficio total. Cuando la t es pequeña, ese total está cerca de cero y el cociente explota (C da 0,64; hay un caso de 59.693 en la población). La regla mide sobre todo lo pequeño que es el beneficio total, que ya mide R3.

### 3.2 Método: la t de R3 quitando lo mejor

Se recalcula `drift_excess_t` (R3) en dos versiones:

$$t_{-Q^*} = t_{\text{exceso}}\big(\text{oos1} \setminus \text{mejor trimestre}\big)$$

$$t_{-3} = t_{\text{exceso}}\big(\text{oos1} \setminus \text{3 mejores operaciones}\big)$$

- $t_{-Q^*}$: ¿sigue habiendo ventaja sin el mejor trimestre? Mejor trimestre = el de mayor exceso total.
- $t_{-3}$: ¿sigue habiendo ventaja sin las tres mejores operaciones? Es la bandera roja de Chande (la mayor ganancia por encima del 40–50 % del beneficio) sin el problema del cociente.

Misma escala que R3, sin unidades nuevas, sin dividir por totales pequeños.

**Ejemplo aproximado, estrategia C:** sin su mejor trimestre (3.021 USD de un total de 4.690), le quedan ≈ 1.670 USD en ≈ 90 operaciones. Descontando la deriva, el exceso medio queda en ≈ 11 USD con desviación ≈ 576, y $t_{-Q^*} \approx 0{,}2$. *(Cuenta aproximada; requiere recalcularse con sus operaciones.)*

### 3.3 Criterio propuesto

Se aplica a estrategias que ya pasan R3 (para las demás no aporta):

| estado | condición |
|---|---|
| PASA | $t_{-Q^*} \ge 1{,}65$ y $t_{-3} \ge 1{,}65$ |
| LIMBO | alguna de las dos entre 0 y 1,65 |
| NO PASA | alguna de las dos ≤ 0 (todo el exceso viene de un trimestre o de tres operaciones) |
| sin dato | LIMBO |

---

## 4. Decisiones abiertas

1. **R6 — longitud de bloque** ($L$ = 5–10 o $\sqrt{n_{\text{IS}}}$) y número de secuencias ($B$ = 5.000). Comprobar la sensibilidad del percentil a $L$.
2. **R6 — curva de cerradas o de flotante.** La de cerradas es la propuesta; la de flotante es más relevante para fondeo pero exige guardar la curva diaria de todas las estrategias.
3. **R6 — sustituir el drawdown observado en R9c** por el p95 simulado.
4. **R7 — trimestres o meses.** Con meses, $K$ = 36–60, pero pocas operaciones por mes (3–4).
5. **R8 — número de operaciones a quitar** en $t_{-3}$ (3 propuesto; podría ser proporcional, p. ej. el 2 % de $n$).
6. **Coste de cálculo:** R6 (5.000 secuencias) y R7 (2.000 permutaciones) por estrategia. Con 10.000 estrategias es comparable al estudio del mono; se puede calcular sólo para las que pasan R3 (≈ 3 % de la población).
7. **Recuento:** antes de fijar umbrales, contar cuántas de las 169 vivas cambian de estado con cada regla.
