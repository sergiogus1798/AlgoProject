# Paso 8 — Propuesta de rediseño de R9a, R9b y R9c

**Fecha:** 2026-10-06 · **Alcance:** reglas R9a (peor día), R9b (peor MAE) y R9c (drawdown frente a neto anual) de `pipeline/autopilot/criteria.yaml`.
**Referencia:** `criterios-paso-08-puerta-oos-2026-10-06` (apartados 3.14, 3.15 y 3.16). Complementa `criterios-paso-08-R5-R5b-R5c-propuesta.md` y `criterios-paso-08-R6-R7-R8-propuesta.md`.

---

## 0. Decisión principal

> **R9a y R9c salen de la puerta IS/OOS (paso 8) y pasan a un módulo especializado de fondeo.**
> **Sólo R9b se queda en la puerta.**

Motivo: R9a y R9c no dicen si la estrategia tiene ventaja real, sino **cuánto riesgo se le puede poner** dentro de los límites de una cuenta de fondeo. Eso es dimensionado, no validación. Separándolo:

- la **puerta IS/OOS** responde a una sola pregunta: *¿hay ventaja real y estable?*
- el **módulo de fondeo** responde a otra: *¿cómo la opero dentro de los límites?* (y lo hace por cartera, que es lo que de verdad cuenta para el límite diario).

| regla | decisión |
|---|---|
| **R9a** peor día | **sale de la puerta → módulo de fondeo.** El paso 8 sólo calcula y guarda el dato, sin juzgar |
| **R9b** MAE | **se queda en la puerta**, reformulada con el percentil 95 |
| **R9c** DD / neto anual | **sale de la puerta → módulo de fondeo.** El paso 8 guarda el DD$_{95}$ simulado de R6, sin juzgar |

---

## 1. Problema común de las tres reglas actuales

Las tres usan el **valor extremo observado** (peor día, peor operación, peor drawdown). Ese extremo:

1. **Depende de $n$.** Con más operaciones o más días, el mínimo sale peor sólo por haber tenido más oportunidades. Una estrategia que está menos tiempo en el mercado parece más segura sin serlo.
2. **No acota el futuro** (argumento de Taleb en el Council). Con ≈ 1.000 días de oos1, el peor día observado es aproximadamente el cuantil 1/1.000; el día que rompe una cuenta de fondeo puede ser el de 1/5.000, todavía no visto.

---

## 2. R9b — La MAE típica mala (SE QUEDA EN LA PUERTA)

### 2.1 Qué mide

Si el riesgo que la estrategia toma es el que se cree tomar. La doctrina no lleva stop fijo, así que 1R es nominal; la MAE (máxima excursión adversa) mide cuánto se aparta el riesgo real del nominal.

### 2.2 Por qué cambiar el mínimo por un percentil

- El **mínimo** de la MAE se apoya en una sola operación, depende de $n$, y su efecto sobre la cuenta ya lo recoge el peor día (en C, la peor operación fue también su peor día).
- Lo que interesa en la puerta es la parte **sistemática**: si la operación mala *típica* va mucho más allá de 1R. Eso se mide con un cuantil estable.

### 2.3 Cálculo

$$\text{MAE}_{95} = \text{percentil 95 de } \frac{\lvert\text{MAE}_i\rvert}{1\text{R}} \quad \text{sobre las operaciones de oos1}$$

Con 196 operaciones, el p95 se apoya en ≈ 10 operaciones, frente a 1 del mínimo.

### 2.4 Criterio propuesto

| estado | condición |
|---|---|
| PASA | $\text{MAE}_{95} \le 1{,}5$R |
| LIMBO | $1{,}5\text{R} < \text{MAE}_{95} \le 2{,}5$R |
| NO PASA | $\text{MAE}_{95} > 2{,}5$R (el riesgo real es sistemáticamente más del doble del nominal) |
| sin dato | LIMBO |

Umbrales orientativos: calibrar con la distribución de $\text{MAE}_{95}$ en la población. Referencia actual: la mediana de la peor MAE en la población es −3,72R, así que conviene ver dónde cae el p95.

---

## 3. R9a — Peor día (SALE DE LA PUERTA → MÓDULO DE FONDEO)

### 3.1 Qué hace el paso 8

**No juzga.** Sólo calcula y guarda, para todas las estrategias que pasan R3:

- la **curva diaria de flotante de oos1** (hoy sólo se conserva para las estrategias del sorteo),
- el **peor día observado** en R (`gate.scorecard.oos_worst_day_r`, como hoy).

### 3.2 Coste de quitar el descarte de la puerta

Según el documento de referencia (decisión abierta 7, propuesta de Taleb), que el peor día y la peor MAE anoten en vez de descartar mete **18 estrategias más en LIMBO** de 10.000. Con R9b aceptada, el caso grave (pérdidas sistemáticamente mucho mayores de 1R) sigue cortándose en la puerta.

### 3.3 Idea para el módulo de fondeo (a desarrollar allí)

El peor día visto no es el peor que va a llegar. El módulo estimará la pérdida diaria que se supera con una probabilidad pequeña, extrapolando con un modelo de cola:

- ajuste de una **Pareto generalizada** a los peores días (*peaks over threshold*),
- cuantil $q_{\text{día}}$ tal que $P(\text{día} < -q_{\text{día}}) \approx 0{,}05/252$ (5 % de probabilidad de un día así en un año),
- riesgo máximo por R por el límite diario $L_d$:

$$\text{riesgo}_d = \frac{L_d}{q_{\text{día}}}$$

Se hará **por cartera**, no por estrategia: el límite diario real se juega con varias estrategias abiertas a la vez. Queda pendiente explicarlo con ejemplos al diseñar el módulo.

---

## 4. R9c — Drawdown frente a neto anual (SALE DE LA PUERTA → MÓDULO DE FONDEO)

### 4.1 Qué hace el paso 8

**No juzga.** Sólo guarda:

- el **p95 del drawdown simulado** que sale del bootstrap por bloques de R6 (`gate.scorecard.dd_esperado_p95_r`), que es el drawdown que cabe esperar en el próximo tramo de igual duración;
- el **neto anual en R** de oos1.

### 4.2 Idea para el módulo de fondeo (a desarrollar allí)

Riesgo máximo por R por el límite total $L_{\text{tot}}$:

$$\text{riesgo}_{\text{tot}} = \frac{L_{\text{tot}}}{\text{DD}_{95}}$$

El cociente actual (drawdown / neto anual) pasa a ser un dato derivado: el **tiempo de recuperación**, $\text{DD}_{95}/\text{neto anual}$.

---

## 5. Esbozo del módulo de fondeo (fuera del paso 8)

Combina R9a y R9c en un solo número:

$$\text{riesgo}_{\max} = \min\!\left(\frac{L_d}{q_{\text{día}}},\ \frac{L_{\text{tot}}}{\text{DD}_{95}}\right)$$

y, como dato anotado:

$$\text{rend}_{\text{anual}} = \text{riesgo}_{\max} \times \text{neto anual en R}$$

**Cuenta aproximada** con A y C. Límites de 5 % diario y 10 % total. Se usan el peor día observado en vez de $q_{\text{día}}$ y DD$_{95}$ ≈ 2 × DD observado; las dos aproximaciones son optimistas.

| | A | C |
|---|---|---|
| peor día observado | 2,21R | 1,74R |
| DD observado → DD$_{95}$ ≈ ×2 | 6,8 → 13,6R | 5,1 → 10,1R |
| riesgo$_d$ = 5 % / peor día | 2,26 % | 2,87 % |
| riesgo$_{\text{tot}}$ = 10 % / DD$_{95}$ | 0,74 % | 0,99 % |
| **riesgo$_{\max}$** | **0,74 %** | **0,99 %** |
| neto anual en oos1 | 9,6R | 1,2R |
| **rendimiento anual a ese riesgo** | **≈ 7 %** | **≈ 1,2 %** |

En los dos casos manda el límite total. C admite más riesgo pero gana tan poco que no sirve para fondeo.

Puntos para el diseño del módulo:

- Posible criterio sobre el riesgo: viable si $\text{riesgo}_{\max} \ge 0{,}75\,\%$, dudosa entre 0,4 % y 0,75 %, inviable por debajo de 0,4 % (orientativo).
- El rendimiento anual, **anotado, no como regla**: lleva dentro la media de oos1, que ya juzga R3 en la puerta.
- La Pareto generalizada es ruidosa con ≈ 100 excedencias: usar el extremo conservador de su intervalo de confianza.
- Todo **por cartera**, con las estrategias que vayan a operarse juntas.

---

## 6. Decisiones abiertas

1. **R9b:** calibrar los umbrales 1,5R / 2,5R con la distribución de $\text{MAE}_{95}$ en la población.
2. **Paso 8:** guardar la curva diaria de flotante de oos1 de todas las estrategias que pasan R3 (hoy sólo de las del sorteo).
3. **Paso 8:** añadir el hecho `dd_esperado_p95_r` (sale del bootstrap de R6).
4. **Módulo de fondeo:** diseño completo (cola del peor día, límites de la cuenta, nivel por cartera, criterio de viabilidad). Pendiente.
