# Paso 8 — Estudios 4.5, 4.6 y 4.7: decisión y propuesta

**Fecha:** 2026-10-06 · **Alcance:** estudios `feedQuality` (4.5), `spread` (4.6) y las columnas restantes de `edgeCost` (4.7) del paso 8, más la regla R2b.
**Referencia:** `criterios-paso-08-puerta-oos-2026-10-06` (apartados 3.4, 4.5, 4.6 y 4.7). Complementa las demás propuestas del paso 8.

---

## 0. Resumen

| estudio / regla | decisión |
|---|---|
| **4.5** calidad de los datos (`feedQuality`) | **SE MANTIENE**, reformulado como retención de la ventaja sin las operaciones afectadas; puede descartar |
| **4.6** spread (`spread`) | **SE ELIMINA** |
| **R2b** neto al spread real | **SE ELIMINA** (depende del estudio del spread) |
| **4.7** `edge_median` y `n` de `edgeCost` | **SE ELIMINAN** |

---

## 1. 4.5 — Calidad de los datos: SE MANTIENE

### 1.1 Por qué

Es la misma preocupación que el retraso de una barra (4.4): **una ventaja que vive de un defecto del histórico no existe en real**. Si el beneficio sale de operaciones que tocan huecos, picos o velas imposibles, ese beneficio no se va a repetir con el feed de la fondeadora.

### 1.2 Problema del test actual

Hoy se comparan las operaciones que tocan una anomalía con el resto mediante una prueba de permutación. Tiene muy poca potencia: si sólo 5 operaciones tocan una anomalía, la prueba nunca saldrá significativa, **aunque esas 5 sean todo el beneficio**.

### 1.3 Método propuesto

La misma lógica que R8 ($t_{-3}$) y el retraso de una barra: **quitar las operaciones afectadas y ver cuánta ventaja queda**.

1. Marcar las operaciones de oos1 que tocan una anomalía del histórico (entre la barra de entrada y la de salida, ambas incluidas). Conjunto $A$, con $n_A$ operaciones.
2. Con el exceso por operación de R3, $e_i$:

**Retención de la ventaja sin las operaciones afectadas:**

$$\text{ret}_{\text{datos}} = \frac{\bar{e}_{\text{limpio}}}{\bar{e}}$$

**¿Las operaciones afectadas ganan más que el resto?** Diferencia de medias:

$$t_{A} = \frac{\bar{e}_A - \bar{e}_{\text{limpio}}}{\sqrt{s_A^2/n_A + s_{\text{limpio}}^2/n_{\text{limpio}}}}$$

**Anotado:** la t de R3 sin las operaciones afectadas, $t_{\text{limpio}}$, y la fracción del exceso total que viene de $A$.

Mismo repreciado común que R3, el mono y el retraso: costes de SQX calibrados con el estudio de emparejamiento MT5–SQX.

### 1.4 Criterio propuesto

Se aplica a estrategias que pasan R3.

| estado | condición |
|---|---|
| PASA | $\text{ret}_{\text{datos}} \ge 0{,}60$, o ninguna operación toca anomalías |
| LIMBO | $0{,}25 \le \text{ret}_{\text{datos}} < 0{,}60$, o $\text{ret}_{\text{datos}} < 0{,}25$ con $t_A \le 1{,}65$ |
| **NO PASA** | $\text{ret}_{\text{datos}} < 0{,}25$ **y** $t_A > 1{,}65$: la ventaja estaba en los datos malos |
| sin dato | LIMBO |

### 1.5 La solución de fondo

Si un activo tiene muchas anomalías, se arregla **una vez en los datos** (limpiar el histórico antes de construir), no estrategia a estrategia. Este test es la red para lo que se escape.

---

## 2. 4.6 — Spread: SE ELIMINA

El spread de los ticks de Darwinex no es realista en algunos activos (no se opera con tanto). El coste ya está calibrado con el **estudio de emparejamiento de operaciones MT5–SQX**.

Arrastra:

- **R2b se elimina:** usaba el repreciado con el spread de Darwinex. No es la única regla que descarta a ninguna estrategia; quitarla no cambia el resultado actual.
- **R5b** leía el número de operaciones de oos1 de este estudio; pasa a leer `gate.scorecard.sanidad_value`, que es el mismo dato.
- **El repreciado común** (R3, mono, retraso de una barra, calidad de datos) usa los **costes de SQX calibrados con el emparejamiento MT5–SQX**. Corregido en `criterios-paso-08-mono-propuesta.md` y `criterios-paso-08-estudios-4.2-4.3-4.4-propuesta.md`.
- El hallazgo de que el spread de SQX estaba en el percentil 10 del real se midió contra Darwinex, así que también decae.

---

## 3. 4.7 — `edge_median` y `n`: SE ELIMINAN

`edge_median` castiga a los sistemas de tendencia sin medir la ventaja, y la dependencia de unas pocas operaciones grandes ya la juzga la $t_{-3}$ de R8. El `n` acompañante desaparece con R5c reformulada (IS y OOS separados).

---

## 4. Decisiones abiertas

1. **4.5:** umbrales de retención (0,60 / 0,25), los mismos que el retraso de una barra; calibrar con la población.
2. **4.5:** qué cuenta como anomalía (definición actual de `feedQuality`) y comprobar por qué no dejó datos en la corrida de ejemplo.
3. **4.5:** inventario de anomalías por activo, para decidir dónde merece la pena limpiar el histórico.
4. **R5c:** confirmar que su coste (denominador de `edge_mean`) sale también de los costes calibrados MT5–SQX.
