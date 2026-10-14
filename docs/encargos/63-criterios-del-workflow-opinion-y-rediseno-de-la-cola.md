# 63 · Los criterios del workflow: la opinión brutal y el rediseño de la cola (pasos 14 a 20)

> **Plan vivo, abierto el 2026-10-12.** Sale de la lectura del dossier
> `docs/AgentPDFs/criterios-implementados-2026-10-12.md` (los 26 pasos tal como están en el código y
> tal como corrieron sobre datos reales). Cada sesión actualiza la tabla y la bitácora. Donde otro
> encargo ya cubre una pieza se cita y no se repite: el 58 (MCPT de la fábrica: poblaciones nula y
> plantada), el 59 (política de costes), el 51 (pasos 10 y 12), el 60 (el build), el 62 (N del ledger).

| frente | qué | modelo | depende de | estado |
|---|---|---|---|---|
| 0 | la segunda opinión: otro agente lee el mismo dossier sin ver ésta y entrega la suya (§1) | Opus | nada | pendiente |
| 1 | el repricing reproduce a SQX: `descuadre_sqx` < 1 % en 17 y 18.5 antes de tocar ningún umbral | Opus (diagnóstico) · Sonnet (el arreglo si es mecánico) | nada | pendiente |
| 2 | `dev.on` apagado y una población entera 8 → 20 con su nula y su plantada por la misma cola | Sonnet (la corrida) · Opus (leerla) | frente 1; el 58 para las poblaciones; custodio libre | pendiente |
| 3 | `falsePositives` una vez por activo × TF, cacheado | Sonnet | nada | pendiente |
| 4 | el paso 14 cambia de pregunta: percentil de la madre entre sus 500 vecinas en oos1 | Opus | D-3 | pendiente |
| 5 | la cola 17-18-18.5-19-20 se sustituye por UNA prueba prerregistrada en oos2 | Opus | D-1, D-2; frente 2 | pendiente |
| 6 | las reglas inertes y las de sólo Limbo del paso 8 pasan a columnas (R4a, R5, R5b, R8, R9b) | Sonnet | D-5 | pendiente |
| 7 | el perfil del paso 1: término de deriva y lista de pruebas congelada por trimestre, o apagado | Opus | D-4 | pendiente |

## Bitácora

- 2026-10-12 · Abierto. La opinión de §0 es la del agente que leyó el dossier ese día; nada ejecutado aún.

**Tu oficio:** estadístico del pipeline (`pipeline/autopilot/`, `studies/`, `ledger/`). Diseño y
estadística en **Opus**; corridas, cachés, columnas y textos en **Sonnet** (regla 17).

**Tu encargo:** que el workflow deje de ser «26 pasos de los que uno solo corta». Devuelves al dueño,
por frente, una decisión: un umbral con su coste en estrategias y su ganancia al lado, un paso que se
borra con la razón escrita, o una prueba nueva con su potencia medida. «Apenas ayuda» se dice.

**Lee, en este orden:** `CLAUDE.md` · `CODESTYLE.md` · `docs/AgentPDFs/WORKFLOW.md` (manda sobre
este encargo donde no coincidan) · `docs/AgentPDFs/criterios-implementados-2026-10-12.md` **por
secciones y en subagente** (regla 16: es largo) · `pipeline/autopilot/criteria.yaml` ·
`ledger/thresholds.yaml` · `studies/CLAUDE.md` y el `README.md` de cada estudio que toques.

## §0 De dónde sale — la opinión del 2026-10-12

Dueño, 2026-10-12: «Quiero tu opinión brutal sobre estos criterios y este workflow. Quiero que me
digas si son muy estrictos, si debería relajarlos, si por el contrario debería incrementarlos, si
debería añadir nuevos, si tendría que hacer algo diferente». Y después: «anota eso en un encargo».

**Veredicto.** La pregunta «¿estrictos o laxos?» es la equivocada: los criterios no están calibrados y
casi ninguno discrimina. El workflow que corre hoy de verdad es: build → top-10.000 por Ret/DD IS →
R3 (t del exceso ≥ 1,65 en oos1) → sorteo de 3 (`dev.on`). Los pasos 9 a 21 son decoración cara.

**Lo roto antes de cualquier umbral** (todo medido en el dossier):

1. El repricing en Python no reproduce a SQX: `descuadre_sqx` 0,925-1,0 en 18.5 y hasta 0,87 en 17.
   Invalida 14, 16.5, 17, 18, 18.5 y 20: comparan curvas que no son las de SQX. → frente 1.
2. La extrapolación de costes: spread en % de 2025-26 aplicado a 2008 (NIKKEI paga 0,41× lo medido en
   build y 1,74× en oos2), swap de hoy a toda la historia. → encargo 59; aquí sólo se exige que esté
   cerrado antes del frente 2.
3. `dev.on: true, sample: 3`: no hay evidencia a escala de población de ningún paso ≥ 9. → frente 2.
4. `falsePositives` cuesta 4.170 s, el 95 % del paso 8, y se recalcula por corrida. → frente 3.

**Paso a paso.**

- **Paso 1.** 16.188 pruebas, BH, 2 celdas pasan (probables artefactos de deriva); el tablero lo
  decide el prior en 357 de 359; 5.288 s diarios. No guía. O lleva el término de deriva `d` del paso 8
  y una lista de pruebas congelada por trimestre, o se apaga. → frente 7, D-4.
- **Pasos 6-7.** Bien. Los filtros de PF y NetProfit son redundantes con Ret/DD; el top-N por Ret/DD
  sigue sin decidirse (encargo 60); las corridas Simple Strategy no dejan fila del paso 6 en el ledger
  (encargo 62).
- **Paso 8.** El único que corta. La nula pasa 0,98 % y lo real 1,69 %: enriquecimiento ≈ 1,7×, ≈ 58 %
  de supervivientes son ruido. **No subir t a 2,33**: mata la potencia; lo que falta es una confirmación
  independiente después. R3 hace el 98-99 % del corte; R4a, R5, R5b inertes; R8 sólo Limbo (89 %), R9b
  53 %. → frente 6, D-5.
- **Pasos 10 y 12.** P3 falla con z < 0 (cara o cruz bajo la nula), incluye V1 (años del build), V0 sin
  leer, en bruto. El z combinado ≥ 2,33 del paso 12 es inalcanzable: no puede eliminar una madre. El
  otro mercado es la mayor fuente de muestra nueva y se desperdicia. → encargo 51; aquí, D-2.
- **Paso 14.** Estricto donde no debe: T1 mata por exceso del build ≤ 0 (47/50 en mc2, 29/50 con exceso
  del build ≤ 0), y eso no es fragilidad. Sustituir la ratio de retención por el **percentil de la
  madre entre sus 500 vecinas en oos1** (top 5 % = pico, centro = meseta; nula de rango uniforme).
  → frente 4, D-3.
- **Pasos 16.5-19.** 25-40 min de SQX por madre para pruebas que nunca deciden: WFC PASA 0/12, CSCV
  10/10 PASA, 18.5 13/13 neutro, WFM 0 NO PASA, T3 = 1,000 en 58/58. Con una sola senda de precios de
  143 semanas no hay potencia: la sd nula de ρ llega a 0,45. La calibración del WFC se midió con volteo
  por día y el código voltea por semana.
- **Paso 20.** La lectura `peor` une cuatro pruebas de baja potencia: suma errores de tipo I sin sumar
  potencia. SPA/StepM contra el trader al azar es lo único que vale de la cola.
- **Paso 26.** Las filas 3b y 4 no pueden fallar a 0,1 lotes; el spread es el «actual» del día; pool
  0/10 validadas.

**El límite físico.** ~35 operaciones/año → ~100 operaciones en oos2 → potencia 25-40 % con s = 0,10
por operación. Ningún umbral lo arregla. Las salidas: agrupar (una cesta de supervivientes de la misma
familia probada en oos2, n × 50) o validar familias y no estrategias sueltas, con el sizing como
decisión de cartera. → D-6.

**La frase que resume:** un workflow de 26 pasos en el que uno solo corta es un workflow de un paso con
mucha latencia. No relajar ni endurecer todavía: calibrar las tres cosas que deciden y borrar el resto.

## 1 · Frente 0 — la segunda opinión

Otro agente, **sin leer este encargo ni §0**, lee el mismo dossier y entrega su análisis en
`docs/AgentPDFs/criterios-segunda-opinion-<fecha>.md` (y su PDF con `/dossier-pdf`). El prompt está en
`docs/encargos/63-prompt-segunda-opinion.md`. Después, una sesión aparte pone las dos opiniones frente a
frente: donde coinciden, el frente se ejecuta; donde discrepan, pregunta al dueño (regla 11).

## 2 · Frente 1 — el repricing reproduce a SQX

Ficheros: el motor de repricing (`engines/` — localízalo con `graphify query "descuadre_sqx"`), los
estudios 17 (`studies/`… WFC) y 18.5 (superficies). Medida: `descuadre_sqx` por estrategia en las
mismas 13 madres del dossier; objetivo < 1 % en todas. Hasta que no se cumpla, **ningún umbral de 14,
16.5, 17, 18, 18.5 ni 20 se toca** — serían umbrales sobre curvas falsas. Lo que descubra sobre por qué
no cuadra (comisión, swap, rollover, redondeo de lotes) va a `knowhow/costs/`.

## 3 · Frente 2 — una población entera por la cola

`dev.on: false` en `criteria.yaml`, una cosecha real del paso 8 entera (no 3) y, por la misma cola 9 →
20, la población nula y la plantada del encargo 58. Devuelve **una tabla por paso**: cuántas entran,
cuántas pasan en real, en nula y en plantada. Un paso cuyo paso en real no supera al de la nula se
propone para borrar; uno que deja pasar la nula igual que la plantada no tiene potencia y se dice.

## 4 · Frente 3 — `falsePositives` cacheado

Una corrida de monos por activo × TF × tramo, guardada en `AlgoData/` bajo `core.paths` con la fecha
de los datos; el paso 8 la lee si existe y la recalcula sólo si los datos del tramo cambiaron.
Un test en `tests/` que falle si dos corridas del paso 8 en la misma celda recalculan los monos.

## 5 · Frente 4 — el paso 14 pregunta otra cosa

Con el repricing cuadrado (frente 1): para cada madre, su exceso neto en oos1 contra el de sus 500
vecinas de parámetros; la métrica es el **percentil** de la madre. La nula es el rango uniforme: una
madre en el top 5 % de sus vecinas es un pico (ajuste fino); una en el centro, una meseta. El umbral
se calibra con las poblaciones del frente 2. T1 por exceso del build ≤ 0 desaparece.

## 6 · Frente 5 — la cola en una prueba prerregistrada

Los pasos 17, 18, 18.5, 19 y la lectura `peor` del 20 se sustituyen por **una** prueba: t del exceso
neto de la madre en oos2 contra su mono de la misma huella (mismo número de operaciones, misma
duración, misma dirección), **una sola mirada**, StepM sobre las K madres que llegan. Variantes,
nube de parámetros y CSCV quedan como diagnóstico opcional sobre build + oos1, sin veredicto. Su
potencia se mide con la plantada del frente 2 y se escribe en el ledger al lado del umbral. **oos2 sólo
con la autorización del dueño (D-1).**

## 7 · Frente 6 — las reglas del paso 8 que no cortan

R4a, R5, R5b (inertes), R8 y R9b (sólo Limbo) salen de las reglas y entran como columnas del informe
del paso 8. El corte queda en R3 más lo que el frente 2 demuestre que corta en real y no en nula.

## 8 · Frente 7 — el perfil del paso 1

Dos lecturas, el dueño elige (D-4): (a) el perfil lleva el término de deriva `d` del paso 8 y la lista
de pruebas se congela por trimestre, con BH sobre esa lista; (b) el perfil se apaga y el tablero se
rige sólo por el prior, que ya lo decide en 357 de 359.

## 9 · Decisiones del dueño — pregúntalas (regla 11)

- **D-1 · oos2.** La prueba única del frente 5 gasta oos2, que está reservado. ¿Se autoriza oos2 para
  esta prueba, una mirada por madre, o la prueba se hace sobre un tramo distinto?
- **D-2 · el otro mercado como confirmación.** ¿El paso 10 pasa a ser la segunda prueba independiente
  (z conjunto del exceso neto en V0 + V2, falla si no bate a la nula), o sigue descriptivo y la
  confirmación es sólo oos2? Toca al encargo 51.
- **D-3 · el paso 14.** ¿Percentil entre vecinas en oos1 (frente 4), o se borra el paso y el ajuste
  fino se lee en la nube de parámetros del 16.5?
- **D-4 · el paso 1.** Lectura (a) o (b) del §8.
- **D-5 · el paso 8.** ¿Las reglas inertes y de sólo Limbo pasan a columnas (frente 6), o se dejan
  hasta que el frente 2 las mida sobre la población entera?
- **D-6 · el límite físico.** ¿Se valida por familias/cestas (n × 50 operaciones en oos2) o se sigue
  validando estrategia a estrategia sabiendo que la potencia es 25-40 %?
- **D-7 · orden.** ¿Frente 1 antes que todo, como se propone, o el frente 2 arranca ya con el repricing
  descuadrado aceptando que la tabla de 14-20 no vale?

## 10 · Lo que no tocas

El master. `oos2` sin D-1. `assets/_policy.yaml` y la política de costes (encargo 59). El build y su
fitness (encargo 60). El generador sintético y el veredicto MCPT (encargo 58). `ledger/thresholds.yaml`
sólo gana filas al final de su sección.

## Objetivo — un comando

No lo tiene: es un rediseño con decisiones del dueño en cada frente. Los frentes 3 y 6 sí lo tendrán
cuando se despachen (`python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest
tests/test_falsepositives_cache.py -q`). **Verificación:** por frente, la tabla real / nula / plantada
pegada en la bitácora, y la decisión del dueño escrita con fecha.

## Cómo cierras

Qué hizo · qué verificó, con las tablas pegadas · qué dejó sin hacer y por qué · qué descubrió para
`knowhow/` (el porqué del descuadre a `knowhow/costs/`, la potencia medida de la prueba única a
`knowhow/research/`). La lista de ficheros cambiados y, como última línea, «¿Quieres hacer el commit?».
