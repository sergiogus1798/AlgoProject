# Paso 8: la tabla de correcciones y la corrida nula (USATEC H1 ruptura)

Proyecto `Test_USATEC_H1_ruptura_leaseWeb`, cosecha del 2026-10-11 (copia en `_aparte/2026-10-11.090924`), export de la puerta
`reports/.../Results/2026-10-11/gate/` (no se ha tocado). Documenta; no elige ningún corte.

## 1. Corrida nula: en marcha (sin resultado todavía)

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
