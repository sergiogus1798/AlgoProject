# 64 · La estadística se hace una vez, sobre toda la población: modelo global, StepM en el paso 8 y deduplicación — y los cambios al 63

> **Plan vivo, abierto el 2026-10-12.** Es la segunda lectura del dossier
> `docs/AgentPDFs/criterios-implementados-2026-10-12.md`, hecha con el encargo 63 delante y con un
> supuesto del dueño: **el cómputo en Python es ilimitado**. No sustituye al 63: lo corrige donde
> discrepa (§1) y añade lo que el 63 no tiene (frentes A-C). Donde otro encargo cubre una pieza se cita:
> el 58 (MCPT de la fábrica), el 59 (costes), el 51 (pasos 10 y 12), el 60 (el build), el 62 (N del ledger).

| frente | qué | modelo | depende de | estado |
|---|---|---|---|---|
| A | deduplicación por solape de operaciones: N efectivo de cualquier lista (§2) | Opus (la medida) · Sonnet (la columna) | nada: el export del paso 7 ya existe | pendiente |
| B | StepM/SPA sobre las 10.000 del paso 8, no sobre las 10 del paso 20 (§3) | Opus | A | pendiente |
| C | modelo de mezcla empírico-bayesiano sobre la población: P(μ > 0) y E[μ] por estrategia, FDR local por lista (§4) | Opus | A; los monos de `falsePositives` | pendiente |
| D | los cambios al 63: frente 1 al final, frente 5 con el P&L de SQX sin reprecio, 13-14 fusionados en 16.5 como diagnóstico, paso 1 apagado (§1) | el dueño decide; Sonnet aplica | D-1..D-4 | pendiente |
| E | la tercera opinión: otro agente, sin ver el 63 ni éste, con el prompt de `64-prompt-tercera-opinion.md`; después, las tres opiniones frente a frente como **predicciones** que el frente 2 del 63 adjudica (§5) | Opus | nada | pendiente |

## Bitácora

- 2026-10-12 · Abierto. Nada ejecutado. La opinión de §0 es la de la sesión de ese día.

**Tu oficio:** estadístico del pipeline (`studies/screening/`, `engines/inference/`, `ledger/`). Diseño
y estadística en **Opus**; columnas, cachés y textos en **Sonnet** (regla 17). Nada de SQX: todo lo de
este encargo se calcula sobre lo que el paso 7 ya exportó.

**Tu encargo:** que la pregunta «si apostase dinero a que esta superviviente tiene ventaja, ¿qué
probabilidad le daría?» tenga un número por estrategia, calculado una vez sobre toda la población y
con la multiplicidad contada donde está (10.000 hipótesis, no 10). Devuelves al dueño, por frente, una
decisión: la lista de supervivientes con su FDR y su N efectivo, el paso que se borra con la razón, o
«esto apenas ayuda» dicho sin rodeos.

**Lee, en este orden:** `CLAUDE.md` · `CODESTYLE.md` · `docs/AgentPDFs/WORKFLOW.md` (manda) · el 63
entero (es el plan que corriges) · `docs/AgentPDFs/criterios-implementados-2026-10-12.md` **por secciones
y en subagente Sonnet** (regla 16; quédate con cifras y `file:line`) · `pipeline/autopilot/criteria.yaml`
· `engines/inference/snooping/superior.py` · `studies/screening/falsePositives/README.md` ·
`studies/screening/gate/README.md` · `engines/README.md`.

## §0 De dónde sale — la opinión del 2026-10-12, segunda lectura

Dueño, 2026-10-12: «Busca una nueva perspectiva y dame tu opinión. Considera "ilimitadas" las
capacidades computacionales en Python para ello». Y después: «apunta todos esos cambios en el
encargo 64 y dame el prompt para el 3er agente que opine».

**Veredicto.** El 63 diagnostica bien (26 pasos de los que corta uno) y remedia en local: calibrar
paso a paso. Con Python sin límite la estadística se hace **una vez, sobre toda la población**, y la
cola deja de emitir veredictos. Tres hechos del dossier lo sostienen:

1. **La multiplicidad vive en el paso 8, no en el 20.** R3 (t del exceso ≥ 1,65 en oos1) se aplica a
   10.000 estrategias sin corrección (`criteria.yaml:69-145`); SPA/StepM existe en
   `engines/inference/snooping/superior.py` y sólo lo ven las ~10 madres del paso 20, donde nunca ha
   corrido en real. El export del paso 7 (10.000 listas de operaciones en oos1, ~440 s) es todo lo que
   hace falta para correrlo donde toca.
2. **Nadie calcula P(ventaja | sobrevive).** El dossier mide enriquecimiento (nula 0,98 % frente a real
   1,69 % en USATEC: ≈ 58 % de ruido entre supervivientes) a nivel de población. Un modelo de mezcla
   sobre las 10.000 da ese número **por estrategia**, encogido hacia la población, y el FDR local de
   cualquier lista. Los 5.000 monos de `falsePositives` son la componente nula ya calculada.
3. **Nadie cuenta el N efectivo.** Diez mil estrategias de una plantilla en un activo comparten la
   mayoría de sus entradas. Los 169 supervivientes de USATEC pueden ser ~20 efectivos; explica que CSCV
   pase 10/10 y que el 1,7× esté mal contado. Una matriz de Jaccard de barras de entrada es barata.

**Lo que no cambia con cómputo ilimitado:** ~100 operaciones en oos2 por estrategia dan 25-40 % de
potencia. La salida es agregar (celda activo × TF × familia, n × 100 operaciones, supervivientes
deduplicados) y desplegar cestas — D-6 del 63, aquí se afirma: sí.

**La frase:** una cola de pruebas de robustez sobre la misma muestra no suma evidencia de ventaja, suma
errores de tipo I. Evidencia de ventaja sólo la dan datos nuevos (oos2, otros mercados); la robustez
ordena, no corta.

## 1 · Frente D — los cambios al 63

Cada línea es un cambio al 63 que el dueño acepta o no (D-1..D-4). Hasta que decida, el 63 sigue
como está.

| frente del 63 | cambio | razón (cifra del dossier) |
|---|---|---|
| 1 (repricing < 1 %) | **pasa al final**; sólo lo necesitan los diagnósticos que cambien costes | la prueba única (frente 5) lee el P&L neto de SQX en oos2 tal cual; D-7 desaparece y el frente 2 arranca ya |
| 2 (población entera por la cola) | **se hace primero y en Python**, sobre el export del paso 7, sin SQX | lo que corta es el 8; la tabla por paso de 9-20 se obtiene después, cuando 9-20 ya no decidan |
| 4 (paso 14 por percentil entre 500 vecinas) | **13 y 14 se fusionan en 16.5** y pasan a diagnóstico sin veredicto; el percentil de la madre se lee en la nube de 1.000 variantes LHS | dos retests de SQX para una pregunta; T3 = 1,000 en 58/58; 25-40 min de SQX por madre |
| 5 (una prueba prerregistrada en oos2) | **sí**, con el P&L de SQX, StepM sobre las K que llegan **deduplicadas** (frente A), y la potencia escrita en el ledger | sin N efectivo el StepM sobre K está mal contado |
| 7 (perfil del paso 1) | **lectura (b): apagar** | 16.188 pruebas sobre una senda de precios por celda; el prior decide 357 de 359; 5.288 s diarios |
| D-2 (otro mercado) | **sí como segunda confirmación**: z conjunto del exceso neto en V0 + V2, falla si no bate a la nula | es la mayor muestra nueva que hay y se desperdicia (encargo 51, frente 1) |
| D-6 (familias/cestas) | **sí** | potencia 25-40 % por estrategia; n × 100 por celda |
| 3 y 6 | sin cambio, Sonnet | — |

## 2 · Frente A — N efectivo por solape de operaciones

Ficheros: nuevo `studies/screening/dedup/` (contrato de `studies/CLAUDE.md`), lee el export del paso 7
(`AlgoData/harvest/<P>/Results/<fecha>/`, trades por estrategia) y escribe por estrategia su clúster y
por lista su N efectivo. Medida: Jaccard de **barras de entrada** (misma barra, misma dirección) entre
todas las parejas; clúster por umbral de solape (D-5: 0,5 o el que el dueño diga; el estudio reporta la
curva N_eff(umbral) y no elige). El N efectivo de una lista es el número de clústeres que toca. Sale
como columna del informe del paso 8 y como entrada de B y C.

Verificación: en USATEC (10.000 en oos1) la tabla «umbral → clústeres → N_eff de los 169»; y la misma
sobre la población nula de `falsePositives` (los monos no comparten entradas: N_eff ≈ N, que es el control).

## 3 · Frente B — StepM sobre las 10.000 del paso 8

Ficheros: `engines/inference/snooping/superior.py` (ya existe; no se reescribe, se llama), la puerta
(`studies/screening/gate/`), `criteria.yaml` paso 8. Entrada: la matriz semanas × estrategias del exceso
neto en oos1 (`engines/weekly/`), con la dependencia estimada por remuestreo de bloques de semanas.
Salida: el conjunto StepM a FWER 5 % y a 10 %, y el conjunto por FDR (BH sobre los p de SPA), cada uno
con su coste en estrategias frente a R3 solo. Cómputo: 10.000 × reps; con cómputo ilimitado, reps ≥ 10.000.

Lo que el dueño recibe: una tabla «R3 solo · StepM 5 % · StepM 10 % · BH 10 %» con supervivientes,
N_eff (frente A) y, cuando C esté, FDR local medio. **R3 no se toca hasta que la tabla esté.**

## 4 · Frente C — el modelo de mezcla sobre la población

Ficheros: nuevo `studies/screening/posterior/`. Por estrategia i, su exceso neto medio por operación en
oos1 (x̄_i) y su error típico (s_i / √n_i, con n_i operaciones). Modelo: μ_i ~ π₀ · F₀ + (1 − π₀) · G,
donde F₀ sale de los 5.000 monos de `falsePositives` (misma huella, costes cargados) y G se estima de
las 10.000 (empírico-Bayes: deconvolución, o una mezcla de normales ajustada por EM; con cómputo
ilimitado, la deconvolución no paramétrica). Salida por estrategia: P(μ_i > 0), E[μ_i | datos], fdr
local; por lista: FDR esperado. Calibración: las poblaciones nula y plantada del encargo 58 (δ = 0,05 /
0,10 / 0,15 por operación): P(μ > 0) debe estar ≈ 0 en la nula y crecer con δ en la plantada.

Lo que el dueño recibe: la lista del paso 8 ordenada por P(μ > 0), con el corte a FDR 10 % y 20 % y su
coste en estrategias frente a R3; y «apenas ayuda» si el modelo no separa más que R3.

## 5 · Frente E — la tercera opinión y la adjudicación

El prompt está en `docs/encargos/64-prompt-tercera-opinion.md`: pregunta abierta sin menú de
respuestas y **con predicciones prerregistradas** (tasa de paso esperada por paso en real, nula y
plantada). Lo mismo se pide a posteriori a las opiniones del 63 (§0) y de éste (§0): cada una rellena
la misma tabla de predicciones. El frente 2 del 63 (corrido según §1: primero en Python) adjudica con
datos; **al dueño sólo llegan las discrepancias que los datos no resuelvan** (regla 11). Entregable: un
dossier `docs/AgentPDFs/criterios-tres-opiniones-<fecha>.md` con las tres columnas y la cuarta, los datos.

## 6 · Decisiones del dueño — pregúntalas (regla 11)

- **D-1 · el orden del 63.** ¿Se aceptan los cambios de §1 (frente 2 primero y en Python, frente 1 al
  final, 13-14 a diagnóstico, paso 1 apagado), o el 63 corre como está y éste sólo añade A-C?
- **D-2 · dónde corta el paso 8.** Cuando B y C estén: ¿corta StepM (FWER), BH (FDR) o el modelo de
  mezcla (fdr local), y a qué nivel (5, 10, 20 %)? Se pregunta con la tabla de §3 delante, no antes.
- **D-3 · la unidad que se valida.** ¿Celda (activo × TF × familia) con sus supervivientes deduplicados
  agregados en oos2, o estrategia a estrategia como hasta ahora? (Es la D-6 del 63; aquí se recomienda
  la celda.)
- **D-4 · oos1 en el build.** ¿El paso 6 de SQX usa oos1 en algún filtro o fitness (la tarea «build+OOS»
  del dossier)? Si lo usa, oos1 no es una mirada limpia para B y C y hay que decirlo antes de contar nada.
- **D-5 · el umbral de solape** para el clúster del frente A: ¿0,5 de Jaccard, otro, o la curva entera y
  el dueño elige viéndola?

## 7 · Lo que no tocas

El master. `oos2` (sólo el frente 5 del 63, con su D-1). R3 y cualquier umbral de `criteria.yaml` hasta
que la tabla de §3 esté. `assets/_policy.yaml` y los costes (59). El build (60). El generador sintético
y el veredicto MCPT (58). `ledger/thresholds.yaml` sólo gana filas al final de su sección.

## Objetivo — un comando

Los frentes A, B y C sí lo tendrán, cada uno con su test de respuesta conocida (una población sintética
de clústeres sabidos para A; la nula de monos para B y C: ≤ 5 % de supervivientes a FWER 5 %, P(μ > 0)
≈ 0): `python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest
tests/test_dedup.py tests/test_posterior.py -q`. Los frentes D y E no lo tienen: son decisiones y un
dossier. **Verificación:** por frente, la tabla pegada en la bitácora y la decisión del dueño con fecha.

## Cómo cierras

Qué hizo · qué verificó, con las tablas pegadas · qué dejó sin hacer y por qué · qué descubrió para
`knowhow/` (el N efectivo medido a `knowhow/research/`; lo que el modelo de mezcla separe o no, también).
La lista de ficheros cambiados y, como última línea, «¿Quieres hacer el commit?».
