# Paso 8 — Propuesta de rediseño de R5, R5b y R5c

**Fecha:** 2026-10-06 · **Alcance:** reglas R5 (frecuencia en oos1), R5b (operaciones en oos1) y R5c (ventaja frente al coste) de `pipeline/autopilot/criteria.yaml`, más un criterio nuevo de degradación temporal.
**Referencia:** `criterios-paso-08-puerta-oos-2026-10-06` (apartados 3.8, 3.9 y 3.10).

---

## 0. Resumen de cambios

| regla | hoy | propuesta |
|---|---|---|
| **R5** | umbral absoluto: PASA ≥ 15/año, LIMBO ≥ 10/año | **test de estabilidad de la frecuencia IS → OOS** (Poisson con sobredispersión, centrado por población, bilateral) |
| **R5b** | ≥ 100 operaciones en oos1, si no LIMBO | **absorbida**: R4a (≥ 35/año en IS) + R5 nueva implican ≥ ~100 con ≥ 3 años de oos1. Se mantiene sólo como red |
| **R5c** | `edge_mean` sobre IS + oos1 juntos, denominador sin slippage | **IS y OOS separados**, denominador con el coste realmente pagado, y **t de R3 con coste estresado** |
| **R5d (nueva)** | — | **degradación temporal**: pendiente del exceso por operación dentro de oos1 |

---

## 1. R5 — La frecuencia no cambia entre el build y oos1

### 1.1 Qué mide

Si la estrategia sigue disparando sus reglas en oos1 al mismo ritmo que en el build. Una **caída** fuerte indica reglas que ya no se activan (ajustadas a algo que dejó de pasar). Una **subida** fuerte indica que la estrategia se comporta distinto de cómo se construyó. Las dos son sospechosas, así que el test es **bilateral**.

### 1.2 Modelo

Las operaciones se tratan como un proceso de Poisson. Con $N_1$ operaciones en $T_1$ años de build y $N_2$ en $T_2$ años de oos1, las tasas son $r_1 = N_1/T_1$ y $r_2 = N_2/T_2$. Si la tasa no ha cambiado:

$$N_2 \mid N_1 + N_2 \;\sim\; \text{Binomial}\!\left(N_1 + N_2,\ \frac{T_2}{T_1 + T_2}\right)$$

En la práctica se usa el log del cociente de tasas, cuyo error estándar bajo Poisson es:

$$\text{se}_{\text{Poisson}}\big(\ln(r_2/r_1)\big) = \sqrt{\frac{1}{N_1} + \frac{1}{N_2}}$$

### 1.3 Dos correcciones necesarias

**a) Sobredispersión.** Las operaciones no llegan como un Poisson puro: se agrupan por régimen de volatilidad, y la varianza real de los recuentos es mayor que la media. Se estima en el build, con los recuentos por año natural $x_1, \dots, x_k$:

$$\hat\varphi = \frac{s^2(x)}{\bar{x}}$$

y se acota:

$$\varphi = \min\big(\max(\hat\varphi,\ 1{,}5),\ 3{,}5\big)$$

- El **suelo de 1,5** evita que una estrategia excepcionalmente regular en el build tenga una banda demasiado estrecha, y deja el PASA algo más ancho que con Poisson puro.
- El **techo de 3,5** evita que una estrategia muy irregular tenga una banda tan ancha que nunca falle.
- Con 8–10 años de build, $\hat\varphi$ se estima con sólo 8–10 puntos: es ruidoso, y el acotado lo estabiliza.

Ejemplo: recuentos anuales 30, 45, 38, 52, 35, 41, 33, 55 (suman 329):

$$\bar{x} = 41{,}1 \qquad s^2 = \frac{562{,}8}{7} = 80{,}4 \qquad \hat\varphi = \frac{80{,}4}{41{,}1} = 1{,}96 \;\Rightarrow\; \varphi = 1{,}96$$

**b) Efecto común de mercado.** Si todo el mercado cambió de régimen (p. ej. la volatilidad de 2020), casi todas las estrategias operan más en oos1, y eso no dice nada de cada una. Se centra con la mediana de la población del mismo activo, timeframe y lado:

$$m_{\text{pop}} = \operatorname{mediana}_{\text{población}}\big(\ln(r_2/r_1)\big)$$

### 1.4 Estadístico

$$\boxed{\;z_{\text{frec}} = \frac{\ln(r_2/r_1) - m_{\text{pop}}}{\sqrt{\varphi\left(\dfrac{1}{N_1} + \dfrac{1}{N_2}\right)}}\;}$$

### 1.5 Criterio propuesto

| estado | condición |
|---|---|
| PASA | $\lvert z_{\text{frec}}\rvert \le 1{,}5$ |
| LIMBO | $1{,}5 < \lvert z_{\text{frec}}\rvert \le 3{,}5$ |
| NO PASA | $\lvert z_{\text{frec}}\rvert > 3{,}5$ |
| sin dato | LIMBO |

Comparado con unos cortes en 2 / 3, la franja de PASA es algo más estrecha y la de LIMBO bastante más ancha: R5 marca antes un cambio de frecuencia, pero sólo descarta cuando el cambio es muy grande ($p$ bilateral ≈ 0,0005 bajo el modelo).

### 1.6 Bandas en operaciones al año

Estrategia de NIKKEI225 con **40 operaciones/año en el build** (8,28 años, $N_1 = 331$), sin centrado ($m_{\text{pop}} = 0$). Entre paréntesis, el total de operaciones en oos1.

**oos1 de 4 años (NIKKEI225)**

| $\varphi$ | NO PASA | LIMBO | **PASA** | LIMBO | NO PASA |
|---|---|---|---|---|---|
| 1,0 | < 28,9 (116) | 28,9–32,5 | **32,5–48,0** (130–192) | 48,0–52,1 | > 52,1 (209) |
| 1,5 | < 26,6 (106) | 26,6–30,9 | **30,9–49,8** (124–199) | 49,8–55,1 | > 55,1 (220) |
| 2,0 | < 24,6 (98) | 24,6–29,5 | **29,5–51,4** (118–206) | 51,4–57,6 | > 57,6 (230) |
| 2,5 | < 22,8 (91) | 22,8–28,4 | **28,4–52,8** (113–211) | 52,8–59,8 | > 59,8 (239) |
| 3,0 | < 21,3 (85) | 21,3–27,3 | **27,3–54,1** (109–217) | 54,1–61,9 | > 61,9 (248) |
| 3,5 | < 19,8 (79) | 19,8–26,3 | **26,3–55,3** (105–221) | 55,3–63,8 | > 63,8 (255) |

**oos1 de 3 años**

| $\varphi$ | NO PASA | LIMBO | **PASA** | LIMBO | NO PASA |
|---|---|---|---|---|---|
| 1,5 | < 25,0 (75) | 25,0–29,9 | **29,9–50,8** (90–153) | 50,8–56,6 | > 56,6 (170) |
| 2,0 | < 22,8 (68) | 22,8–28,4 | **28,4–52,6** (85–158) | 52,6–59,3 | > 59,3 (178) |
| 2,5 | < 20,8 (62) | 20,8–27,0 | **27,0–54,1** (81–162) | 54,1–61,8 | > 61,8 (185) |
| 3,0 | < 19,0 (57) | 19,0–25,8 | **25,8–55,6** (78–167) | 55,6–64,1 | > 64,1 (192) |
| 3,5 | < 17,3 (52) | 17,3–24,7 | **24,7–56,9** (74–171) | 56,9–66,2 | > 66,2 (199) |

**oos1 de 5 años (XAUUSD, forex)**

| $\varphi$ | NO PASA | LIMBO | **PASA** | LIMBO | NO PASA |
|---|---|---|---|---|---|
| 1,5 | < 27,6 (138) | 27,6–31,6 | **31,6–49,2** (158–246) | 49,2–54,1 | > 54,1 (270) |
| 2,0 | < 25,7 (129) | 25,7–30,3 | **30,3–50,7** (152–253) | 50,7–56,4 | > 56,4 (282) |
| 2,5 | < 24,2 (121) | 24,2–29,2 | **29,2–52,0** (146–260) | 52,0–58,5 | > 58,5 (293) |
| 3,0 | < 22,7 (114) | 22,7–28,2 | **28,2–53,2** (141–266) | 53,2–60,5 | > 60,5 (302) |
| 3,5 | < 21,4 (107) | 21,4–27,3 | **27,3–54,3** (137–272) | 54,3–62,3 | > 62,3 (311) |

*(Nota: estas bandas de 5 años usan el build de NIKKEI225, 8,28 años. Con un build de 10 años las bandas son algo más estrechas.)*

**Lecturas:**

- Las bandas son **asimétricas** en número de operaciones porque el test trabaja en escala logarítmica: «la mitad» y «el doble» están a la misma distancia.
- Con menos años de oos1 las bandas se ensanchan: con menos datos se exige menos precisión.
- **El centrado desplaza todo.** Si la mediana de la población operó un 15 % más en oos1, todas las bandas se multiplican por 1,15.

### 1.7 Ejemplos con las estrategias del documento

| | $N_1$ (IS) | $r_1$ | $N_2$ (oos1) | $r_2$ | $\ln(r_2/r_1)$ | $z$ Poisson ($\varphi = 1$) | $z$ con $\varphi = 2$ |
|---|---|---|---|---|---|---|---|
| A | 329 | 39,7 | 196 | 49,0 | 0,21 | 2,33 | 1,65 |
| C | 189 | 22,8 | 98 | 24,5 | 0,07 | 0,57 | 0,41 |

A, que con Poisson puro estaría en LIMBO, pasa con $\varphi = 2$. Con un centrado de +15 % ($m_{\text{pop}} = 0{,}14$) su $z$ baja a ≈ 0,5: casi toda su subida de frecuencia era del mercado.

### 1.8 Pendiente antes de aplicarlo

- Calcular $\hat\varphi$ en la población real para ver su distribución y comprobar que el intervalo [1,5; 3,5] es razonable.
- Calcular $m_{\text{pop}}$ por activo, timeframe y lado.
- Contar cuántas de las 169 vivas cambiarían de estado.

---

## 2. R5b — Al menos 100 operaciones en oos1

### 2.1 Por qué la R5 actual no la implicaba

La línea de PASA de la R5 actual son 15 al año: con 3 años de oos1, **45 operaciones**, no 100. En la población de ejemplo, R5 deja pasar 9.695 estrategias y R5b deja en LIMBO a 2.265.

### 2.2 Por qué con la R5 nueva sí queda implicada

- R4a exige ≥ 35/año en el build para PASA.
- La R5 nueva exige que la frecuencia en oos1 sea compatible con la del build. Con $r_1 = 35$ y $\varphi = 2$, el límite inferior del PASA queda en torno a 25–26/año.
- Con 3 años de oos1, eso son ≈ 75–80 operaciones en el peor caso del PASA, y ≈ 105 si la frecuencia se mantiene.

No es una garantía exacta de 100, pero sí de un orden de magnitud correcto.

### 2.3 Propuesta

- La función principal de R5b (garantizar suficientes operaciones para leer la t) la cubren **R4a + R5 nueva**.
- **Se mantiene R5b como red**, sin descarte: ≥ 100, si no LIMBO. No cuesta nada y cubre estrategias con build corto o casos frontera.
- Opcional (de la discusión de R1b): suelo duro en número absoluto de operaciones en oos1, NO PASA por debajo de 60–80, por la no normalidad de la media con $n$ pequeño y distribuciones sesgadas.

---

## 3. R5c — La ventaja bruta frente al coste

### 3.1 Qué es realmente `edge_mean`

$$\text{edge\_mean} = \frac{\overline{\text{bruto}}}{\overline{\text{coste de hoy}}} = 1{,}70 + \frac{\overline{\text{P/L neto}}}{\overline{\text{coste de hoy}}}$$

(el 1,70 es la razón entre el coste realmente pagado —spread + slippage— y el del denominador —sólo spread— en NIKKEI225).

Es la **media del P/L reescalada por el coste**, sin dividir por la desviación. Por eso:

$$\text{se}(\text{edge\_mean}) \approx \frac{\sigma_{\text{P/L}}}{\sqrt{n}\cdot\overline{\text{coste}}}$$

Para A ($\sigma \approx 950$ USD, coste ≈ 22 USD):

| muestra | $n$ | se de edge_mean |
|---|---|---|
| todo oos1 | 196 | ≈ 3,1 |
| un año de oos1 | ≈ 49 | ≈ 6,2 |

Contiene la misma información que la t, pero con más ruido. Por eso en la población no decide nada.

### 3.2 Cambios propuestos

1. **IS y OOS separados.** El IS está inflado por la selección de SQX; mezclarlo con oos1 mezcla un número optimizado con uno limpio. Se calculan `edge_mean_is` y `edge_mean_oos`, y sólo el de OOS entra en la regla.
2. **Denominador con el coste realmente pagado** (spread + slippage). Así `edge_mean = 1` es el punto de equilibrio y `edge_mean = 2` significa de verdad «sobrevive a un coste doble».
3. **No hacer umbrales por año** (± 6 de error: es ruido). El análisis temporal va en R5d.
4. **El criterio con potencia: la t de R3 con coste estresado.** Se recalcula `drift_excess_t` restando a cada operación $(k-1)\times$ su coste pagado:

$$t_{\text{exceso}}(k) = \frac{\overline{\text{exceso}} - (k-1)\,\overline{\text{coste}}}{\sigma_{\text{exceso}}}\sqrt{n_{\text{ef}}}$$

Esto dice si la estrategia sigue siendo **distinguible del azar** con costes peores, que es lo que importa, y no sólo si la media sigue siendo positiva.

### 3.3 Ejemplo: estrategia A

Exceso medio 172,33 USD, $\sigma = 949{,}76$, $n = 196$, coste pagado medio ≈ 37,12 USD (media IS + oos1; con el de oos1 la cifra cambiaría ligeramente):

| $k$ | $t_{\text{exceso}}(k)$ |
|---|---|
| 1 (coste actual) | 2,54 |
| 1,5 | 2,27 |
| 2 | 1,99 |

### 3.4 Criterio propuesto

| estado | condición |
|---|---|
| PASA | $t_{\text{exceso}}(1{,}5) \ge 1{,}65$ y `edge_mean_oos` ≥ 2 |
| LIMBO | $t_{\text{exceso}}(1{,}5) < 1{,}65$ con $t_{\text{exceso}}(1) \ge 1{,}65$, o `edge_mean_oos` entre 1,25 y 2 |
| NO PASA | `edge_mean_oos` < 1,25 (con el denominador corregido: no aguanta ni un 25 % más de coste) |

$k = 1{,}5$ porque, en NIKKEI225, el spread de SQX está en el percentil 10 del real: un 50 % más de coste es un escenario realista, no extremo.

---

## 4. R5d (nueva) — Degradación temporal dentro de oos1

### 4.1 Qué mide

Si la ventaja por operación cae con el tiempo dentro de oos1.

### 4.2 Modelo

Regresión del exceso por operación (el de R3, ya descontada la deriva) contra el momento de cierre $t_i$, en años:

$$\text{exceso}_i = a + b\,(t_i - \bar{t}) + \varepsilon_i$$

- $b$: cambio del exceso medio por año (USD/año).
- $t_b = b / \text{se}(b)$, con la misma corrección de $n$ efectivo que R3 si hay autocorrelación.
- **Exceso proyectado al final de oos1:** $\hat{e}_{\text{fin}} = a + b\,T/2$.

**Sólo dentro de oos1.** No se incluye el IS: allí el exceso está inflado por la selección, y la caída IS → OOS es esperable aunque la estrategia no se degrade. Mezclarlo fabricaría una pendiente negativa en casi todas.

**Centrado por población.** Si un año fue malo para todos los largos de un activo, la pendiente común no es degradación de una estrategia. Se resta a cada $b$ la mediana poblacional del mismo activo, timeframe y lado, y se trabaja con $b - b_{\text{pop}}$.

### 4.3 Potencia: lo que este test puede y no puede ver

Con operaciones repartidas uniformemente en $T$ años, $\text{sd}(t) = T/\sqrt{12}$:

$$\text{se}(b) = \frac{\sigma}{\sqrt{n}\cdot T/\sqrt{12}}$$

**Estrategia A** ($\sigma = 950$, $n = 196$, $T = 4$):

$$\text{se}(b) = \frac{950}{14 \times 1{,}155} = 58{,}8 \text{ USD/año}$$

- El intervalo al 95 % de $b$ es ± 115 USD/año: **± 67 % del exceso medio (172) por año**.
- Una caída lineal de 344 a 0 USD en los 4 años (la ventaja desaparece por completo) da $b = -86$ y $t_b = -1{,}46$: **no se detecta ni a 1,65**.

**Con oos1 + oos2** (≈ 7 años, $n \approx 340$):

$$\text{se}(b) = \frac{950}{18{,}4 \times 2{,}02} = 25{,}5 \text{ USD/año}$$

La misma caída completa en ese horizonte daría $t_b \approx -1{,}9$. Mejora, pero sigue siendo justo.

**Conclusión:** en el paso 8 este test sólo detecta degradaciones catastróficas. Las graduales quedan dentro del ruido con 3–4 años; sólo las resuelven más años fuera de muestra.

### 4.4 Criterio propuesto

**En el paso 8 (anota, como mucho LIMBO; descarta sólo en el caso extremo):**

| estado | condición |
|---|---|
| PASA | $t_b \ge -1{,}65$ |
| LIMBO | $t_b < -1{,}65$ y $\hat{e}_{\text{fin}} > 0$ |
| NO PASA | $t_b < -1{,}65$ y $\hat{e}_{\text{fin}} \le 0$ (se degrada y al final de oos1 ya no queda ventaja) |
| sin dato | LIMBO |

**En los pasos con muestra nueva (10, 12, 20):** el mismo test sobre oos1 + oos2 juntos, con el doble de potencia, y con descarte a $t_b < -2{,}33$.

---

## 5. Decisiones abiertas

1. **Acotado de $\varphi$ en [1,5; 3,5].** Comprobar con la distribución real de $\hat\varphi$ en la población.
2. **Bandas de R5 en $\lvert z\rvert$ = 2 / 3.** Contar cuántas de las 169 vivas cambian de estado.
3. **R5b:** mantener como red sin descarte, o añadir el suelo duro de 60–80 operaciones.
4. **R5c:** valor de $k$ para el estrés de coste (1,5 propuesto) y si `edge_mean_oos` < 1,25 debe ser NO PASA o sólo LIMBO.
5. **R5d:** confirmar que en el paso 8 sólo descarta con $\hat{e}_{\text{fin}} \le 0$, y que la versión con descarte vive en los pasos de muestra nueva.
6. **Centrado poblacional** (R5 y R5d): por activo + timeframe + lado. Requiere que la población sea suficientemente grande en cada celda.
