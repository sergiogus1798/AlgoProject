# Paso 8 — Propuesta de rediseño del test del mono

**Fecha:** 2026-10-06 · **Alcance:** estudio `monkey` y criba `mono` de la cascada de la puerta (`studies/screening/gate/monkey.py`), y su uso en mercados adicionales.
**Referencia:** `criterios-paso-08-puerta-oos-2026-10-06` (apartados 4.1 y 4.2). Complementa las propuestas de R5, R6–R8 y R9.

---

## ⚠️ 0. ANTES DE NADA: REVISAR A FONDO EL REPRECIADO DEL MONO

> **El mono reprecia las operaciones con su propio motor y obtiene un neto de 45.464 USD para la estrategia A, frente a los 38.465 USD de SQX: un 18 % más. Nadie ha investigado esta diferencia.**
>
> **Hay que revisarlo muy a fondo antes de darle al mono ningún papel en la puerta.**

Por qué importa:

- Si el motor del mono calcula con los mismos costes la estrategia y los monos, su p (o su z) es coherente consigo mismo. Pero ese motor está cobrando **menos coste** que SQX, o calculando **otra cosa** (otros precios de relleno, otro valor del punto, otra conversión de lotes, otro tratamiento del slippage o de la comisión).
- R3, el estudio del spread y el mono tienen que hablar del **mismo P/L**. Si no, se están contrastando hipótesis distintas y las discrepancias entre ellos no significan nada.
- Un 18 % de diferencia en el neto es del orden de la deriva entera de A (4.689 USD, el 12 % de su neto): suficiente para cambiar conclusiones.

Qué revisar, operación a operación, al menos para A, B y C:

1. Precio de entrada y de salida que usa el mono frente al de SQX.
2. Lotes y valor del punto (NIKKEI225: 0,063137 USD por punto y lote).
3. Spread, slippage y comisión que cobra el mono frente a SQX y frente al repreciado del estudio del spread (`studies/data/spread/reprice.py`).
4. Si el mono reprecia con el spread plano de SQX, con el real de Darwinex o sin coste.
5. La suma: el P/L de cada operación debe cuadrar con SQX (o con el repreciado del spread) al céntimo, o la diferencia debe estar explicada.

**Objetivo:** un único repreciado compartido por la estrategia, los monos, R3 y el estudio del spread.

---

## 1. Diagnóstico: el mono y R3 son casi la misma prueba

### 1.1 Lo medido

- De las 325 estrategias con t ≥ 1,65, **318 ya ganan al mono** con p ≤ 0,05 (las otras 7 no tienen dato).
- **821 ganan al mono** con p ≤ 0,05 y **no llegan** a t 1,65.
- Lift de «ganar al mono con p ≤ 0,05»: **+5 por cada 1.000** (301 contra 296). Nada.
- En la cascada, la criba mono deja pasar con p ≤ 0,50: no filtra.

### 1.2 La razón

El peldaño *timing* sortea entradas con el mismo lado, la misma duración y el mismo tamaño que las reales. El P/L esperado de una de esas entradas al azar es:

$$E[\text{P/L}_{\text{mono}}] = \text{lado}\times\mu\times\text{barras}\times\text{lotes}\times vp - \text{costes}$$

Es la **deriva de R3** menos los costes. El mono contrasta la misma hipótesis nula que R3 («la entrada no vale más que una al azar»), pero sin suponer normalidad: saca la distribución nula del mercado real.

**Conclusión:** el mono no debe ser una regla aparte, sino **la versión no paramétrica de R3**, que sirve para comprobar que los supuestos de R3 se sostienen.

---

## 2. Sólo en el tramo OOS

El mono se calcula **sólo sobre oos1** (en el paso 8) y, en general, sólo sobre tramos que el generador no vio. En el build no significa nada: SQX eligió la estrategia precisamente por ganar ahí, así que ganarle al mono en el build es una consecuencia de la selección, no una prueba.

Esto ya es tu regla actual («trader al azar sólo fuera de muestra»); se mantiene.

---

## 3. Los tres cambios

### 3.1 El tamaño sigue la regla de la doctrina, no se copia

**Hoy:** cada entrada al azar recibe los mismos lotes que la operación real.

**Problema:** la doctrina pone más lotes cuando el mercado está tranquilo. Si a la calma le siguen movimientos distintos de la media, una estrategia sin habilidad gana o pierde por eso (el sesgo del término de deriva, apartado 3.5 del documento de referencia: ±0,02 a ±0,27 en la t). Un mono que copia los lotes rompe esa relación y **hereda el mismo sesgo** que R3.

**Propuesta:** el mono **dimensiona su entrada sorteada con la regla de la doctrina** (inverso de la volatilidad en el momento de *su* entrada, con el mismo 1R). Así reproduce exactamente lo que ganaría una estrategia sin habilidad con tu forma de dimensionar, y el sesgo desaparece de raíz. La corrección de «la operación ciega» propuesta para R3 sólo quita el 60 %.

### 3.2 Sorteo estratificado en el tiempo

**Hoy:** el momento de entrada se sortea en cualquier punto de oos1.

**Propuesta:** cada entrada al azar se sortea **dentro del mismo año (o trimestre) que la operación real**. El mono mide entonces si la entrada es buena *dentro de su régimen*, y no si la estrategia estuvo más tiempo dentro en los años buenos.

Es la versión limpia de la idea de calcular la deriva de R3 por ventanas, sin suponer que cada barra es una barra media. Mismas consideraciones que allí: ventanas de un año como mucho; ventanas más cortas empiezan a llamar «mercado» a la habilidad de elegir régimen.

### 3.3 Un z continuo en lugar de un p

**Hoy:** con 2.000–2.500 sorteos, el p mínimo es 1/2.501 = 0,0004. Consecuencias:

- A tiene p = 0,0004: está en el **suelo**, y el mono no puede ordenar a las buenas.
- La criba familia (Benjamini–Hochberg con 3.979 candidatas) necesitaría p ≤ 0,0000126, o sea **unos 80.000 sorteos** por estrategia: no puede nombrar a nadie.

**Propuesta:**

$$z_{\text{mono}} = \frac{\bar{x}_{\text{real}} - \bar{x}_{\text{monos}}}{\text{sd}(\bar{x}_{\text{monos}})}$$

$\bar{x}$ es la media de P/L por operación; $\bar{x}_{\text{monos}}$ y $\text{sd}(\bar{x}_{\text{monos}})$ son la media y la desviación de esa media entre los sorteos.

- Con 2.000 sorteos, la media y la desviación de los monos están muy bien estimadas: el $z$ no tiene suelo.
- Está en la **misma escala que la t de R3**: se pueden comparar directamente.
- Sirve para la criba familia sin multiplicar los sorteos (pasando $z$ a p con la normal, o usando $z$ como t).
- Se guarda también el p empírico como dato secundario, para ver si la cola de los monos se aparta de la normal.

---

## 4. Papel en la puerta

| | hoy | propuesta |
|---|---|---|
| tramo | oos1 | oos1 (sólo OOS) |
| tamaño | lotes copiados de la operación real | lotes por la regla de la doctrina en la entrada sorteada |
| momento | cualquier punto de oos1 | dentro del mismo año / trimestre |
| salida | p (suelo en 0,0004) | $z_{\text{mono}}$ continuo (+ p empírico anotado) |
| papel | criba laxa (p ≤ 0,50), no filtra | **control de R3** |

### 4.1 Criterio propuesto

No es una regla independiente: es una condición que acompaña a R3.

| estado | condición |
|---|---|
| PASA | R3 en PASA **y** $z_{\text{mono}} \ge 1{,}65$ |
| LIMBO | R3 y el mono discrepan: una por encima de su línea y la otra por debajo |
| NO PASA | lo decide R3 (el mono no descarta por sí solo) |
| sin dato | LIMBO |

Una discrepancia indica que algo falla en los supuestos de una de las dos pruebas: colas, sesgo del tamaño o deriva por régimen. Merece una mirada antes de seguir.

### 4.2 Peldaños como diagnóstico (anotan)

Se calculan los cuatro peldaños (*timing*, *timing + duración*, *timing + tamaño*, *free*), todos con $z$, sólo para anotar:

- $z$ parecido en *timing* y en *free*: la ventaja está en **cuándo entra**.
- $z$ alto sólo en *free*: la ventaja está en la **duración** o el **tamaño**, no en la entrada.

---

## 5. El mono en mercados adicionales (fuera del documento)

La misma lógica se aplica, y encaja aún mejor: en un mercado en el que la estrategia no se construyó, **todo el histórico es fuera de muestra**, así que se puede usar el periodo completo.

### 5.1 Lo que hay que adaptar a cada mercado

1. **Tamaño por la doctrina con la volatilidad y el valor del punto de ese mercado** (no los lotes del mercado original).
2. **Costes de ese mercado**: su spread real y su slippage, con el mismo repreciado común (sección 0).
3. **Estratificación por año** en ese mercado.
4. **La deriva propia de ese mercado**: el mono la recoge sola; no hace falta calcularla aparte. Un mercado bajista castigará automáticamente a un largo que no aporte nada.

### 5.2 Cómo combinar varios mercados

Con varios mercados hay varias pruebas. Contar en cuántos «gana» desperdicia información y es sensible al azar. Con $z$ continuos se combinan con **Stouffer**:

$$Z = \frac{\sum_{j=1}^{k} z_j}{\sqrt{k}} \quad \text{(mercados independientes)}$$

Si los mercados están correlacionados (p. ej. varios índices, o EURUSD y GBPUSD), se corrige con la correlación $\rho_{ij}$ entre sus $z$ (o, en su defecto, entre sus rentabilidades):

$$Z = \frac{\sum_j z_j}{\sqrt{k + 2\sum_{i<j}\rho_{ij}}}$$

Con mercados muy correlacionados, $k$ mercados valen mucho menos que $k$ pruebas independientes.

Variante con peso por número de operaciones: $Z = \sum w_j z_j / \sqrt{\sum w_j^2}$ con $w_j = \sqrt{n_j}$.

### 5.3 Dos trampas a evitar

- **Contar todos los mercados probados, no sólo los buenos.** Si se prueban 8 mercados y se informan los 3 que salen bien, el $Z$ combinado está sesgado. La lista de mercados debe fijarse **antes** de mirar resultados.
- **No reajustar la estrategia a cada mercado.** Si se reoptimizan parámetros por mercado, ese mercado deja de ser fuera de muestra.

---

## 6. Decisiones abiertas

1. **⚠️ Repreciado del mono (sección 0): revisión a fondo, prioritaria.** Nada de lo demás tiene sentido hasta que la estrategia, los monos, R3 y el spread usen el mismo P/L.
2. **Ventana de estratificación:** año o trimestre.
3. **Regla de tamaño en el mono:** implementar la de la doctrina (inverso de la volatilidad) en la entrada sorteada.
4. **Línea de $z_{\text{mono}}$:** 1,65 propuesto como control; comprobar en la población cuántas de las 169 vivas discrepan con R3.
5. **Criba familia:** recalcular con $z$ en lugar de p empíricos y ver si nombra a alguna.
6. **Mercados adicionales:** fijar la lista de mercados antes de probar, y decidir si se exige un $Z$ combinado mínimo (p. ej. ≥ 1,65) o sólo se anota.
