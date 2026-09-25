# Pre-registro del holdout — XAUUSD

> ## ⚠️ ESTE DOCUMENTO NO ESTÁ EN VIGOR
>
> El andamiaje está escrito; **las cuatro decisiones de la §2 a la §5 son del dueño y están sin
> firmar**. Los valores que aparecen son **PROPUESTAS**, marcadas como tales.
>
> **Hasta que la §6 esté firmada con fecha, ningún módulo del proyecto lee 2022–2026.** Los lotes se
> construyen y se verifican contra la Fase 0 del SPP que ya está en disco
> (`raw/XAUUSD/SPP_IS/2026-09-10/`).

**Qué es esto.** El compromiso, escrito **antes** de mirar, sobre qué ventana de datos se reserva
como prueba final, qué la aprueba y qué pasa si falla.

**Por qué existe.** Es lo único del plan que **no se puede arreglar retroactivamente**. Una ventana
que ya has mirado deja de ser una prueba: cada decisión que tomas sabiendo lo que hay dentro la
contamina un poco más, y no hay forma de deshacerlo. Un resultado sobre una ventana no pre-registrada
no es defendible ante nadie — incluido tú dentro de seis meses.

**Qué NO es.** No es un compromiso con unos umbrales concretos para siempre. Los criterios pueden
cambiar y van a cambiar. Lo que este documento fija es que **cuando cambien, quede escrito cuándo y
por qué** — antes de la siguiente lectura, nunca después. Eso es lo que lo mantiene honesto mientras
el método todavía se está construyendo.

Creado 2026-09-21. Referencia: `docs/AgentPDFs/plan-ejecucion-2026-09-21.md` §8 · `OPEN.md` issue 24.

---

## 1 · Los datos

| | |
|---|---|
| Símbolo | **XAUUSD** |
| Feed | `XAUUSD_DukasM1_Infinox` |
| Timeframe de trabajo | M30 |
| Historia completa disponible | 2008 – 2026 |
| Costes aplicados | `assets/XAUUSD.yaml` ⚠️ **son valores por defecto de SQX, no las cifras acordadas con Infinox.** Todo resultado con coste producido antes de que el dueño los sustituya arrastra esta salvedad (`OPEN.md`) |

---

## 2 · DECISIÓN 1 — el reparto de ventanas  ⬜ SIN FIRMAR

**Propuesta:**

| ventana | rango | para qué | quién la ve |
|---|---|---|---|
| **IS** — in-sample | 2008 – 2017 | construir, optimizar, elegir parámetros | libre |
| **OOS** — out-of-sample de trabajo | 2018 – 2021 | validar, comparar variantes, ajustar el método | libre, tantas veces como haga falta |
| **HOLDOUT** | **2022 – 2026** | **la prueba final, una sola vez por estrategia** | **bajo la §4** |

**Por qué esa frontera.** El estudio de walk forward matrix y el de variantes leen los dos 2022–2026,
así que es la ventana que hay que proteger. El corte en 2022 deja cuatro años de holdout, que a M30
son suficientes operaciones para que el resultado signifique algo.

☐ **Aprobado tal cual**  ☐ **Modificado a:** ______________________  · fecha: __________

---

## 3 · DECISIÓN 2 — qué métrica decide, y con qué umbral  ⬜ SIN FIRMAR

**Propuesta:** el veredicto sobre el holdout **no es un número, son tres condiciones**, porque una
sola métrica se puede ganar por accidente:

| # | condición | umbral propuesto | por qué |
|---|---|---|---|
| 1 | Operaciones en la ventana | **≥ 100** | por debajo, nada de lo que sigue es estable |
| 2 | `RExpectancyScore` | **> 0** | es `RExpectancy × √n`: un estadístico tipo t que penaliza las regiones de pocas operaciones (🔬 `knowhow/sqx-format/metric-formulas.md`) |
| 3 | Degradación contra el OOS de trabajo | **`CalmarRatio?` del holdout ≥ 50 % del OOS** | no se exige que vaya igual de bien, se exige que no se desplome |

⚠️ **Tres avisos que el código debe respetar al calcular esto:**

- **`RExpectancy` lleva centinelas** (`99999.0` y `-1.0`, todas con ~1 operación, el 0,08 % de las
  filas) y **ganan el argmax**. Filtrar `|v| > 100` **antes** de cualquier ranking.
- **`CalmarRatio?` y `AnnualPctReturnDDRatio?` llevan un `?` literal en el nombre.** Pedirlas sin el
  `?` devuelve una columna entera de NaN, sin error.
- **La vista de export tiene que estar cerrada antes** de calcular ningún resultado sobre el
  holdout: el valor de una columna **se congela dentro del `.sqx`**, y una columna añadida después
  sale 0 en toda estrategia anterior, sin aviso (`knowhow/columns/custom-columns-stored.md`, tarea S8 del plan).

☐ **Aprobado tal cual**  ☐ **Modificado a:** ______________________  · fecha: __________

---

## 4 · DECISIÓN 3 — cuántas lecturas, y quién las autoriza  ⬜ SIN FIRMAR

**Propuesta:**

- **Una lectura por estrategia madre.** Se pide, se concede, se ejecuta, se anota en la §7. No se
  repite «a ver si con otro parámetro».
- **Autoriza: el dueño**, explícitamente, por estrategia. Ningún agente lee el holdout por iniciativa
  propia, ni siquiera para «comprobar algo rápido».
- **El método puede iterar todo lo que quiera sobre IS y OOS de trabajo.** El holdout se toca cuando
  el método ya está cerrado para esa madre.
- **Una segunda lectura no está prohibida, está registrada.** Si hace falta, se anota en la §7 con su
  motivo, y el resultado pasa a valer menos — explícitamente, no en silencio.

☐ **Aprobado tal cual**  ☐ **Modificado a:** ______________________  · fecha: __________

---

## 5 · DECISIÓN 4 — qué se hace si falla  ⬜ SIN FIRMAR

**Esto se decide ahora, antes de ver nada.** Es la parte que la gente se salta y es la que hace que
todo lo demás sirva de algo.

**Propuesta:**

| resultado | qué pasa |
|---|---|
| **Pasa las tres condiciones** | la estrategia es candidata a cartera. El resultado del holdout **no se vuelve a usar** para afinarla |
| **Falla por operaciones (< 100)** | **no concluyente.** No cuenta como fallo ni como éxito: la estrategia se archiva sin veredicto |
| **Falla 2 o 3** | la estrategia **se descarta.** No se re-optimiza, no se le busca una variante que sí pase, no se cambia el umbral para que entre |
| **Falla más del 70 % de las madres** | no es un problema de las estrategias, es del **método**. Se para el pipeline, se revisa el protocolo, y **el holdout queda quemado**: la siguiente prueba final necesita datos nuevos o un símbolo nuevo |

La última fila es la importante: es la única que protege contra reescribir el criterio hasta que
pase alguien.

☐ **Aprobado tal cual**  ☐ **Modificado a:** ______________________  · fecha: __________

---

## 6 · Firma

Este pre-registro entra en vigor cuando esta sección está rellena. Antes de eso, las §2–§5 son
propuestas y **ningún módulo lee 2022–2026**.

```
Firmado por: ____________________      Fecha: ____________
Commit del repositorio en esa fecha: ____________
```

---

## 7 · Registro de lecturas del holdout

**Una fila por lectura. Se escribe ANTES de leer, no después.**

| # | fecha | estrategia madre | autorizada por | resultado | ¿repetición? |
|---|---|---|---|---|---|
| | | | | | |

---

## 8 · Registro de cambios de criterio

**Un criterio puede cambiar. Lo que no puede es cambiar después de una lectura y hacer como que
siempre fue así.** Cada cambio se escribe aquí antes de la siguiente lectura.

| fecha | qué cambió | valor anterior | valor nuevo | por qué | lecturas ya hechas con el criterio viejo |
|---|---|---|---|---|---|
| 2026-09-21 | documento creado | — | propuestas §2–§5 | pre-registro inicial, sin firmar | 0 |
