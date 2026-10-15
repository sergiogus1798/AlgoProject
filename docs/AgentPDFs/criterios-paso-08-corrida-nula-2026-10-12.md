# Paso 8: la tabla de correcciones y la corrida nula (USATEC H1 ruptura)

Proyecto `Test_USATEC_H1_ruptura_leaseWeb`, cosecha del 2026-10-11 (copia en `_aparte/2026-10-11.090924`), export de la puerta
`reports/.../Results/2026-10-11/gate/` (no se ha tocado). Documenta; no elige ningún corte.

## 1. Corrida nula: cómo se lanzó (resultado en la sección 4)

Se mide qué parte de los monos nulos (estrategias sin ventaja, hechas al azar sobre la huella de las reales) sobrevive a las reglas del paso 8, con la
tasa de paso de las ventajas plantadas (0,05 / 0,10 / 0,15 R). Objetivo: ≤ 1,2 % de nulos supervivientes.

- Dos intentos previos no terminaron: el primero cayó por disco lleno en `/tmp`; el segundo (4 h) se paró al estimar unas 10 h, y el estudio no guarda
  las poblaciones ya calculadas ni tiene opción de reanudar, así que se relanza entera.
- Por precisión de los sorteos (100.000 por escalón) y no por tiempo, el dueño manda seguir. Lanzada el 2026-10-12 18:11 UTC, PID 319701, fin esperado
  hacia las 04:00 UTC del 2026-10-13 (≈ 2 h por población × 5).
- Registro: `AlgoData/tmp_fp/null_run_2026-10-12.log`. Resultado: `AlgoData/reports/Test_USATEC_H1_ruptura_leaseWeb/Results/<día en que acabe>/falsePositives/`
  (`reglas.csv`, `funnel.csv`); la cuota se lee con `tail -n 40 AlgoData/tmp_fp/null_run_2026-10-12.log`, que imprime el embudo y el Pass de cada regla por nivel.

## 2. La tabla «R3 solo · StepM 5 % · StepM 10 % · BH 10 %»

Lote: las 7.822 estrategias con operaciones en el export (las demás cayeron antes del nivel 1a). Panel: 209 semanas (2020-01-02 a 2023-12-29)
× 7.822 estrategias del **exceso neto de oos1** (`excess` de `operaciones.parquet`, descontados costes y deriva, cada operación entera en la semana en
que cierra, `engines/weekly/panel.py`). Remuestreo por bloques estacionario, longitud de bloque 1 (Politis y White), 10.000 réplicas.

| procedimiento | supervivientes | comparten con R3 |
|---|---|---|
| R3 solo (`drift_excess_t` ≥ 1,65) | 173 | 173 |
| StepM, 5 % | 0 | 0 |
| StepM, 10 % | 0 | 0 |
| BH, 10 % (p de remuestreo por estrategia) | 0 | 0 |
| BH, 10 % (p normal de la t de R3), segunda lectura | 0 | 0 |

Qué es cada cosa, en una frase:
- **R3 solo**: la estrategia pasa si la t del exceso por operación, corregida por autocorrelación, es ≥ 1,65. Desde 2026-10-12 R3 ya no juzga (es una
  columna); aquí es exactamente esa columna con el umbral antiguo. La t máxima del lote es 2,54; 3 estrategias pasan de 2,5 y ninguna de 3.
- **SPA**: p de «ninguna estrategia del lote supera a su referencia» pagando por haberlas probado todas. Sale 0,74 (el 0,67 y el 0,74 son sus variantes
  baja y consistente): no hay evidencia de que **alguna** gane.
- **StepM**: va quitando la mejor mientras la prueba siga rechazando; con FWER 5 % o 10 % (probabilidad de nombrar al menos una falsa). No rechaza ni
  en la primera vuelta (SPA 0,74), por eso nombra 0.
- **BH**: controla la proporción esperada de falsas entre las nombradas (FDR). Admite dos lecturas del «p de SPA» y las he calculado las dos:
  el p marginal por estrategia del propio remuestreo de SPA (con +1 para no dar p = 0), y el p normal de la t de R3. Ambas dan 0.

## 3. Lectura y decisión

- 173 estrategias pasan R3 solo (2,2 % del lote) y ninguna llega a t = 3. Las correcciones por búsqueda múltiple no nombran a ninguna: con
  7.822 candidatas, una t de 1,65 a 2,54 es lo que se espera de probar muchas.
- Con 0 de 7.822, el lote **no contiene ventaja detectable por el exceso semanal de oos1** una vez pagada la búsqueda. La puerta actual deja 169
  vivas por el mono con horas (`z_mono`); esta tabla no las contradice ni las confirma: las mide con otro reloj (semanas, no operaciones).
- **Decisión: todavía no se decide el umbral.** Lo que la tabla sí enseña: StepM 5 %, StepM 10 % y BH 10 % dejan 0 de 7.822; el SPA da p = 0,74; el lote
  no muestra ventaja demostrable una vez contada la búsqueda, mientras que la z por celda sola pasa 127 (cifra del coordinador, no recalculada aquí; el
  export antiguo da 67 con `z_mono` ≥ 1,645). Esa distancia (127 frente a 0) es el coste de endurecer, pero sin la corrida nula no se sabe cuántas de las 127 son
  azar ni cuántas buenas se pierden. El umbral se decide cuando la corrida acabe.

## 4. Corrida nula terminada (2026-10-15)

Cosecha entera `_aparte/2026-10-11.090924` (build completo): 100 donantes × 50 = **5.000 monos** por población, 100.000 sorteos de mono por
estrategia, semilla 3439025465. Resultado en `AlgoData/reports/Test_USATEC_H1_ruptura_leaseWeb/Results/2026-10-15/falsePositives/`
(`funnel.csv`, `reglas.csv`, `hechos_monos.parquet` con los hechos de cada mono y de cada real; los cortes de abajo en `cortes_paso8.csv`).
Celda con B = 1: la línea de la z es 1,645. Los monos nulos ganan de media +2,90 R/año en oos1 (72,5 % en positivo): heredan la deriva
alcista del USATEC de las horas de su donante, así que el neto y la ventaja frente al coste **no** los distinguen de una estrategia buena.

### 4.1 Las cifras, con su intervalo

Intervalo de Clopper-Pearson al 95 %. «Sobrevive» = sale del paso 8, en Pasa o en Limbo (el Limbo sigue en la cadena).

| población | Pasa | Limbo | sobrevive | IC 95 % de «sobrevive» | IC 95 % de «Pasa» |
|---|---|---|---|---|---|
| nula (5.000) | 150 | 90 | **240 = 4,80 %** | 4,22-5,43 % | 2,54-3,51 % (3,00 %) |
| planta 0,05 R | 1.555 | 675 | 2.230 = 44,6 % | 43,2-46,0 % | 29,8-32,4 % |
| planta 0,10 R | 2.734 | 1.064 | 3.798 = 76,0 % | 74,8-77,1 % | 53,3-56,1 % |
| planta 0,15 R | 3.270 | 1.176 | 4.446 = 88,9 % | 88,0-89,8 % | 64,1-66,7 % |
| reales (10.000) | 95 | 27 | 122 = 1,22 % | 1,01-1,46 % | — |

- **El 3,0 % es sólo el Pasa. Con el Limbo, que sigue adelante, sobrevive el 4,8 %**: cuatro veces el objetivo de 1,2 %.
- Los 50 monos de un mismo donante comparten horas y no son independientes. Remuestreando donantes (20.000 réplicas) el intervalo de la nula
  sale 4,22-5,40 %: casi el mismo; el agrupamiento no ensancha nada que cambie la lectura.
- La z del mono hace casi todo el trabajo: sola deja pasar el **5,2 %** de la nula (lo que promete α = 5 %); las otras nueve reglas juntas sólo
  bajan eso a 4,8 %. Endurecer otra regla no sustituye a endurecer la z.

### 4.2 Cinco ajustes medidos sobre lo guardado (sin sortear nada)

Se recalcula el paso 8 con `criteria.judged` sobre los hechos de `hechos_monos.parquet`, cambiando una cosa. Para no elegir y medir sobre los
mismos monos, los 100 donantes se parten en dos mitades de 50 (orden de su huella): el corte que se busca (la línea más floja que deja la
mitad A en ≤ 1,2 %) se elige en A y se mide en B. Las líneas fijadas de antemano (1,960, 2,241, 2,326) no se eligen con la nula; ahí A y B
sólo dicen que la cifra es estable. Plantas y reales no se usan para elegir nada.

| ajuste | nula (IC 95 %) | nula, mitad B (IC) | plantas 0,05 / 0,10 / 0,15 | reales |
|---|---|---|---|---|
| hoy (z ≥ 1,645, Limbo sigue) | 4,80 % (4,22-5,43) | 4,60 % (3,81-5,50) | 44,6 / 76,0 / 88,9 % | 95 + 27 |
| z ≥ 1,960 (α 2,5 %) | 2,24 % (1,85-2,69) | 2,24 % (1,70-2,90) | 33,6 / 68,3 / 85,8 % | 19 + 3 |
| **z ≥ 2,241 (α 1,25 %)** | **1,04 % (0,78-1,36)** | 0,96 % (0,62-1,43) | **25,3 / 59,5 / 82,2 %** | 2 + 0 |
| **z ≥ 2,326 (α 1 %)** | **0,78 % (0,56-1,06)** | 0,68 % (0,40-1,09) | **23,0 / 56,8 / 80,5 %** | 0 |
| Limbo fuera (sólo sale el Pasa) | 3,00 % (2,54-3,51) | 2,80 % (2,19-3,52) | 31,1 / 54,7 / 65,4 % | 95 |
| retraso y calidad de datos sin Limbo | 3,86 % (3,34-4,43) | 3,72 % (3,01-4,54) | 41,0 / 72,2 / 87,0 % | 95 + 13 |
| z ≥ 2,11 elegida en A, Limbo fuera | 1,06 % (0,79-1,38) | 0,92 % (0,58-1,38) | 20,8 / 46,9 / 62,1 % | 4 |
| `edge_mean_oos` ≥ 5,75 elegida en A (sin Limbo en esa regla) | 0,88 % (0,64-1,18) | 0,80 % (0,49-1,23) | 16,5 / 48,3 / 79,2 % | 81 + 25 |

`edge_mean_oos` es el bruto medio por operación dividido por el coste medio (1 = sale a la par). La z elegida en A sin el Limbo-fuera sale
2,24: la misma línea que 2,241, que es la que ya da la regla por celda con B = 4 (α/B = 1,25 %).

### 4.3 Lectura

- **La palanca es la z.** A igual nula (~1 %), la z conserva más plantas que cualquier otra cosa: 25 / 60 / 82 % frente a 16 / 48 / 79 % con
  `edge_mean_oos` o 21 / 47 / 62 % quitando el Limbo. Quitar el Limbo se come las plantas fuertes (de 89 % a 65 % en 0,15) y no llega al objetivo.
- **La z de las reales no se parece a la de los monos.** Monos nulos: media -0,03, desviación 1,02 (lo que debe ser). Reales: media +0,48,
  desviación **0,56**, máximo 2,72. Es la nula empírica del 5.3 (δ₀ ≈ 0,55, σ₀ ≈ 0,55). Por eso las reales pasan la z menos que los monos
  (1,2 % frente a 5,2 %) y por eso a 2,241 queda casi ninguna: el lote entero cabe en su propia nula, como dijeron SPA (p = 0,74) y StepM (0).
  La tasa de la nula mide bien la regla contra un mono sin ventaja; no es la tasa de falsas entre las reales.
- **Coste en estrategias:** pasar de 1,645 a 2,241 baja las reales supervivientes de 122 a 2 (a 2,326, a 0); en las plantas se pierden 19 / 17 /
  7 puntos. Ninguna de las 120 que se pierden se distingue del azar con los datos que hay, así que en este lote el coste en ventaja real
  demostrable es cero; en lotes con ventaja de 0,05 R se perdería casi la mitad de lo que hoy sale.
- El objetivo de 1,2 % se cumple en el punto con 2,241 (1,04 %), pero el techo de su intervalo (1,36 %) lo cruza; con 2,326 (α 1 %) el techo
  queda en 1,06 %.

### 4.4 Lo que decide el dueño

| código | qué se decide | A | B | C | recomendación |
|---|---|---|---|---|---|
| P8-Z | la α de la regla «z del mono con horas» (`criteria.yaml` paso 8; el umbral sigue dividiéndose por B de la celda) | 0,05 (hoy): nula 4,8 %, plantas 45/76/89 %, reales 122 | 0,0125: nula 1,04 % (techo 1,36), plantas 25/59/82 %, reales 2 | 0,01: nula 0,78 % (techo 1,06), plantas 23/57/80 %, reales 0 | **C** — cumple el 1,2 % con el intervalo entero por 2 puntos de planta más que B |
| P8-L | el Limbo del paso 8 | sigue adelante (hoy) | sale (sólo el Pasa sigue) | — | **A** — quitarlo cuesta 24 puntos de la planta 0,15 y con la z de P8-Z no hace falta |
| P8-E | endurecer `edge_mean_oos` en vez de la z | no (hoy, ≥ 2 / Limbo ≥ 1,25) | ≥ 5,75: nula 0,88 %, plantas 17/48/79 %, reales 106 | — | **A** — a igual nula pierde más plantas que la z; las 106 reales que deja son las que la nula empírica explica |
