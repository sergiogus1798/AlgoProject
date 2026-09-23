# EL WORKFLOW — los 20 pasos, de la idea a la estrategia superviviente

**Esto lo dictó el dueño el 2026-09-23 y es la espina dorsal del proyecto.** Documento vivo, sin
fecha en el nombre: se actualiza, no se sustituye. Cualquier sesión que vaya a construir algo mira
aquí primero en qué paso está y qué contrato tiene que cumplir.

Qué NO es: `plan-ejecucion-2026-09-21.md` reparte el trabajo entre agentes y
`protocolo-robustez-2026-09-21.md` detalla los contratos internos del tramo de robustez. Esto es la
**secuencia**, y manda sobre el orden que digan los otros dos.

Estados: ✅ construido y medido · 🟡 existe, sin cerrar · ⬜ sin empezar · 🔴 bloqueado por un dato
que sólo el dueño puede dar.

---

## La secuencia

| # | paso | dónde | estado |
|---|---|---|---|
| 1 | **Idea en el chat** | — | — |
| 2 | **Vocabulario** — ¿existe el bloque? si no, se crea e instala | `sqx/inspect/vocabulary.py`, `sqx/blocks/install.py` | ✅ |
| 3 | **Plantilla** — bloque fijo + hueco aleatorio, con registro de lo ya probado | `sqx/templates/`, `/strategy-template` | ✅ |
| 4 | **Preflight** — costes, ventanas y rangos, BLOQUEANTE | `core/assets.py` | ✅ |
| 5 | **Creación del custom project** | `sqx/projects/builder.py` | ✅ |
| 6 | **Configuración del build** | `assets/_build.yaml`, `sqx/projects/doctrine.py` | 🔴 filtros · ⬜ building blocks |
| 7 | **Retest OOS en SQX** | tarea propia, costes de `oos1` | ✅ |
| 8 | **Análisis IS/OOS en Python** | `gate/`, `/oos-gate` → `/curate` | 🟡 umbrales laxos |
| 9 | **Retest crossmarkets en SQX** | `sqx/projects/crossmarket.py` | 🔴 faltan costes |
| 10 | **Análisis crossmarkets en Python** | `strategies/crossmarket/` | 🟡 sin skill |
| 10.5 | **Preparación crossTF** — generación de variantes escaladas | `sqx/variants/scale.py`, `/crosstf` | 🟡 |
| 11 | **Retest crossTimeframes en SQX** | `/crosstf` | 🟡 |
| 12 | **Análisis crossTFs en Python** | `strategies/crossTF/` | 🟡 |
| 13 | **MC Retest en SQX** | tarea del donante; rangos ya en `assets/` | ⬜ |
| 14 | **Análisis MC Retest en Python** | `strategies/retest/` | 🟡 |
| 15 | **SPPs en SQX** | `sqx/variants/spp.py` | ✅ |
| 16 | **Análisis SPPs en Python** | `strategies/sppUltra/` | ✅ |
| 16.5 | **Preparación de variantes para el WFC** | `sqx/variants/make.py` | ✅ |
| 17 | **Walk Forward Correlation** | `strategies/walkForwardCorrelation/report.py` | ✅ |
| 18 | **CSCV** | `strategies/walkForwardCorrelation/pbo.py` | ✅ |
| 19 | **Walk Forward Matrix en SQX** | `strategies/walkForwardMatrix/` | 🟡 |
| 20 | **Análisis conjunto de 17, 18 y 19 — CIEGO hasta tener los tres** | — | ⬜ |

Del 21 en adelante empieza la cartera. **Primero las estrategias individuales.**

## El Monte Carlo de bootstrap está FUERA, a propósito

Decisión del dueño, 2026-09-23, y el razonamiento merece quedar escrito porque es correcto:

> Todos esos tests que hay antes están dedicados a intentar descartar que la estrategia haya tenido
> suerte en el backtest. Mientras que el Monte Carlo sólo resuelve los trades de un backtest
> estático, no dice nada del edge.

Remuestrear los trades realizados mide la dispersión de **una muestra ya seleccionada**. Si la
estrategia llegó ahí por haber sobrevivido a una búsqueda, el bootstrap hereda esa selección entera
y no puede verla: reordenar trades afortunados da secuencias afortunadas.

**El módulo `strategies/monteCarlo/` se mantiene**: en la cartera responde otra pregunta —
dimensionamiento y riesgo de ruina dada una distribución de trades— y ahí sí es la herramienta.

## Qué segmento toca cada paso

Sale de `assets/_policy.yaml` y no se negocia por paso:

- `build` — sólo el paso 6. Es la única muestra que el generador ve.
- `oos1` — del 7 al 16. Retest, crossmarket, crossTF, MC Retest y SPPs.
- `oos2` — **RESERVADO** para 17 y 19 (WFC y WFM). Es una puerta de un solo sentido: cada mirada
  lo gasta. Ningún paso anterior lo toca.

## El contrato que une los pasos pares

Todo paso de Python que juzgue estrategias emite **un CSV con `strategy` y `verdict`**, y `/curate`
lo aplica sobre el databank para que el siguiente paso de SQX sólo vea a los supervivientes. Da
igual qué haya juzgado: el mecanismo no cambia. `identity` es opcional pero recomendada — el nombre
no identifica, SQX renombra en colisión.

⚠️ La identidad es el SHA-256 del `strategy_Portfolio.xml` **normalizado**. Un retest reescribe
`makeExternal` en cada variable: con el hash crudo, el emparejamiento build↔retest casa 0 de 115.

## Decisiones del dueño sobre la secuencia — 2026-09-23

### El paso 20 va ciego, y por eso el orden importa

Los pasos 17, 18 y 19 **no se miran hasta que los tres estén hechos**. La razón no es estética:

> Una vez miramos una ventana de OOS la quemamos, y esas pruebas se hacen con los datos que ya
> habíamos visto **y además la última bala del `oos2`**.

Del 7 al 16 se mira `oos1` una y otra vez, así que para cuando se llega al 17 ese tramo está
gastado. `oos2` es lo único virgen que queda, y sólo se dispara una vez. Si se leen los resultados
de 17 y 18 antes de correr el 19, la decisión de si correrlo —y con qué parámetros— ya está
contaminada por lo que se vio, y la última bala se gasta en un test elegido a posteriori.

**Esto ha de estar forzado por el ledger, no por la buena voluntad de quien lo corra.**

### Un manifiesto global de la cadena — acordado

Un solo registro por estudio que diga, paso a paso, cuántas estrategias entran y cuántas salen. Sin
él, al llegar al 17 nadie sabe si quedan tres supervivientes de diez mil o de cincuenta — y esa
diferencia **es** el resultado, no un detalle de contabilidad.

### 🔭 Antes de correr el workflow entero por primera vez: pasar una población NULA

**Recordatorio para el dueño, pedido por él el 2026-09-23.**

La cadena son seis filtros en serie sobre la misma población, y cada uno ajusta su umbral mirando
lo que mató el anterior. Eso es selección múltiple: el superviviente del paso 20 ha pasado por una
búsqueda tan intensa como la del builder, sólo que esa búsqueda **la hacemos nosotros**.

Habrá métricas y requisitos de rendimiento cuantificables, y eso es necesario. No es suficiente:
un umbral cuantificado sigue sin decir cuántas estrategias sin ningún edge lo cruzarían por azar.

Lo que sí lo dice: **meter por la cadena entera una población de estrategias de entrada aleatoria**
y contar cuántas llegan al paso 20. Si de diez mil monos llegan 4 y de diez mil tuyas llegan 5, ya
sabes lo que vale ese 5. La máquina del mono ya existe (`gate/monkey.py`) y hoy sólo se usa en el
paso 8; llevarla de punta a punta es el control que hace interpretable todo lo demás.

Hacerlo **antes** del primer pase completo, no después: después ya se sabe qué sobrevivió, y el
número de monos se convierte en una cifra que se compara con un resultado conocido.

## Lo que bloquea hoy

| | qué falta, y de quién depende |
|---|---|
| 🔴 | **`assets/_study.yaml`** — los umbrales de aceptación del paso 6 y sobre qué muestra (`sampleType`) se miden. Del dueño |
| 🔴 | **costes de `XAGUSD_DukasM1_Infinox` y `BRENTCMDUSD_ftmo`**, y el `data_from` del Brent. Sin ellos el paso 9 se niega a escribirse. Del dueño |
| ⬜ | **los building blocks** del paso 6: qué indicadores entran en el hueco aleatorio |
| ⬜ | el paso 20, que no existe |
