# 74 — Listo el domingo: la cadena entera, de la idea a la cartera, en las dos máquinas

## Estado (cada sesión actualiza su fila)

| # | frente | sesión | recurso | estado | espera |
|---|---|---|---|---|---|
| 1 | V del 50: corrida entera con el paso 8 vigente (`Test_USATEC_H1_breakoutL_v8_leaseWeb`) | 18 | custodio leaseWeb | en curso desde jue 19:23 UTC | — |
| 2 | Z1 del 50 y resto del 49 (ledger, autopilot, umbrales al ledger, higiene de `criteria.yaml`) | 18 | Python | pendiente | 1 |
| 3 | #93: C2-C11 del 72 en `criteria.yaml` y `assets/_study.yaml` | 07 | Python | pendiente | 2 commiteado, y el dueño confirma a 07 |
| 4 | Resto del F3 del 56 (`entryQuality` lee el replay tier 2 con stop) | 07 | Python | **hecho** (ya estaba: bitácora del 56, 2026-10-14; `tests/test_replay.py` + `test_entry_delay_replay.py` 10/10, 2026-10-15) | — |
| 5 | 66 frentes 1, 2, 4, 5, 9, 10 (sin SQX; sin medir mientras corra SQX) | 95 | Python | hecho jue noche: casi todo ya estaba construido; quedan las mediciones con la máquina libre (bitácora del 66) | P10, D27 |
| 6 | #96 (L4): silueta en el CSCV · #104 (F8a/b) | 95 | Python | hecho jue noche: #96 cerrada (fila en la lectura del CSCV), #104 F8a/b (F8c tras la corrida limpia), #119 cerrada | — |
| 7 | 66 frentes 6-7 (SQX vivo) · #112 (núcleos) · mediciones aplazadas del 66 | 95 | conductor y custodio | pendiente | 1 terminado |
| 8 | Corrida real en gorilla (celda del dueño) → `bin/remote.sh gorilla collect` → paso 26 en leaseWeb (#123, 72 D) | 95 | gorilla, luego MT5 | build 10.000 hecho; **paso 8 falló: EURUSD sin `price_rounding`** (sólo 6 activos medidos). Medida `engines.market.rounding` en curso → ficha → `run` | medida |
| 9 | Si V falla: arreglo con su test y V otra vez desde cero (regla de la corrida limpia) | 18 | custodio | — | 1 |
| 10 | Paso 26 con una superviviente real (55 C) → su fila en el pool | 95 | conductor, MT5 | pendiente | supervivientes de 1 u 8 |
| 11 | Motor de carteras con un pool real (#87; M0 ya filtra por costes actuales) | 07 | Python | pendiente | 10 |
| 12 | Ensayo general: dos celdas a la vez (leaseWeb y gorilla), del director a la cartera, sin manos | 95 + 18 | todo | sábado | 2, 3, 10 |
| 13 | Campaña desatendida toda la noche del sábado en las dos máquinas | 95 | todo | sábado noche | 12 |
| 14 | Hoja final para el dueño: qué está listo, qué no, cómo lanza un agente | 95 | — | domingo 8:00 | 13 |

## Bitácora

- 2026-10-15 (jueves noche) — escrito por algoproject-95 a petición del dueño: «el domingo por la
  mañana quiero el proyecto terminado para empezar a usar agentes para lanzar workflows,
  desarrollar estrategias y testearlas». Dueño: D1 = la cadena entera probada una vez en las dos
  máquinas, más la campaña corriendo sola; D2 = lo aparcado sigue aparcado (53, 57, 58, 60, 67,
  56 F2/F4/F5, 69); D4 = «lo que sea, pero termina a tiempo»; D5 = sin Council. Reparto acordado
  con 18 y 07 por mensajes. N3: commit y push por frente con pathspec y `checks.py` verde. N4: una
  ambigüedad para ese frente; la pregunta va a «Preguntas para la mañana» y se sigue con otro.
- 2026-10-15 20:40 — dueño: «cuanto más rápido mejor», «elige, pero dale». Reparto: 18 = V, criteria.yaml y 49, ensayo en leaseWeb; 95 = gorilla, D27, 66 frentes 6-7, collect, paso 26, celdas del viernes, campaña; 07 = ya sin esperar: F3 del 56, prueba en seco de la campaña, preparar #87 con un pool archivado; luego #93 y #87 real. Celdas del viernes (elegidas por 95): leaseWeb `Trade_GBPJPY_H1_momentumL_leaseWeb` (simple, largo, `momentum_base_v3`), gorilla `Trade_AUDUSD_H1_reversionL_gorilla` (simple, largo, `reversion_base_v3`), 10.000 estrategias y 30 min cada una. Hecho esta noche: #96, #104, #119, P10, D27 fase 1, dos fallos de gorilla (`remote.sh`, `live._log`).
- 2026-10-15 21:05 — gorilla `Trade_EURUSD_M30_reversionL_gorilla`: build 0 → 10.000 en 35 min; paso 8 falla: la ficha de EURUSD no tiene `price_rounding` (#120: 22 fichas sin medir). Bloquea también GBPJPY y AUDUSD (celdas del viernes) y la campaña fuera de XAUUSD, USA500, DAX40, NIKKEI225, USATEC y USDJPY. 95: medida reutilizable sobre las operaciones del propio build, y EURUSD medido con el build de gorilla. Pregunta R1 abajo.
- 2026-10-15 21:45 — 95: la celda de gorilla del viernes pasa de AUDUSD H1 a **`Trade_XAUUSD_M15_momentumL_gorilla`** (simple, largo, `momentum_base_v3`): `core.assets AUDUSD` avisa de que su feed sólo es estable desde 2025 (construcción 2008 = calidad B), y XAUUSD ya tiene `price_rounding`. Gorilla no tiene el proyecto de herramientas ni el snippet `AlgoBank` compilado (`sqx.snippets.install --check`): cada volcado cae a la ruta lenta; se instala al acabar EURUSD, antes de la celda siguiente.

## Reglas de la noche

- Nada pesado de CPU junto a una corrida de SQX (regla 19). El custodio tiene un solo dueño a la vez.
- Cada sesión orquesta y reparte cada frente a un subagente Sonnet. Commit sólo de sus ficheros
  (`git commit -- <ficheros>`; con un fichero compartido, índice temporal).
- Ficheros de 18 esta noche: `ledger/`, `pipeline/autopilot/` (con `criteria.yaml`),
  `verdict/gates.py`, `ledger/thresholds.yaml`, encargos 49/50/53. Nadie más los toca.
- `criteria.yaml` no se edita mientras una corrida lo lee.

## Preguntas para la mañana

| código | frente | qué se decide | lecturas | recomendación |
|---|---|---|---|---|
| G1 | 8 | celda de la corrida de gorilla | **contestada: B** (EURUSD M30 largos reversión, `Trade_EURUSD_M30_reversionL_gorilla`) | — |
| P10 ✅ B | 5 | dos objetivos de `perf/inputs/construct.py` apuntan a datos borrados | A primer miembro + cosecha USDJPY (no existe) · B cosecha XAUUSD `Test_XAUUSD_H1_ruptura_wtc3` · C retirarlos | B |
| D27 ✅ A | 5 | ledger único del 66 | el diseño A/B/C está escrito en el 66, sección «D27 · Diseño…» | sin recomendación aquí; fuera de la ruta crítica |
| K1 | 11 | cómo se dimensiona en cartera una estrategia sin stop (OPEN #113 (1); el M3 para con «sin stop del paso 24») | A pérdida diaria flotante de la firma + tope de exposición conjunta · B stop ATR sintético sólo para el tamaño · C 1 lote fijo (rompe límites en 50-77 % de cuentas) | A |
| K2 | 11 | `oos2` se gasta una vez por pool: ¿quién lo lee? | A sólo la cartera de fondeo · B dos pools · C la real primero | A |
| K3 | 11 | de qué proyecto salen las supervivientes del pool del viernes | nombre del proyecto, o «las de la corrida V del 50» | — |
| W1 ✅ fuera | 7 | la celda interrumpida `squeezeBBLong XAUUSD H1` es un test de 15 min y `following()` la corre la primera | A dejar que termine · B marcarla hecha/fallida en el ledger | B |
| W2 | 7 | `claude -p` con límite de uso: el bucle ahora para (`7f6a293`) | A parar · B dormir 30 min y reintentar, con tope | B si va desatendido |
| W3 ✅ B | 7 | la campaña no retira sus `Trade_` (1,1 GB el de NIKKEI) y SQX los carga al arrancar | A dejarlos · B retirarlos tras `keep` | A un fin de semana, B si dura semanas |
| W4 ✅ fuera (`dropped_templates`) | 7 | `squeezeBBLong` falla en 16.5 (`not variables of this strategy: ['SqueezeBB']`, la causa sigue) | A dejarla en la cola · B al final | B |
| W5 ✅ No | 7 | antes de lanzar: existe `AlgoData/campaign/STOP` (desde 07-10), la cola está vacía y nada relanza el bucle si muere | `run --go` quita el STOP; `plan --queue N` encola; ¿supervisor (cron) sí/no? | encolar y lanzar a mano; supervisor no hasta ver una noche limpia |
| R1 | 8, 12, 13 | un activo sin `price_rounding` en su primera corrida | A el paso 8 lo mide solo sobre las operaciones del build y escribe la ficha (con `why`), y sigue · B se para, se mide a mano y `run` · C la campaña sólo elige activos ya medidos | A: sin ella la campaña del sábado se para en cada activo nuevo |

## Informe de las 5:40 (viernes 2026-10-16, hora del servidor, UTC)

Orden del dueño (jue 21:30): toda la noche buscando soluciones, testeando, arreglando y commiteando,
las tres instancias; a las 5:40 cada una dice qué ha hecho y sus siguientes pasos del día. Cada
sesión rellena sólo su sección antes de las 5:35; 95 las junta para el dueño.

### Informe de las 5:40 — algoproject-95

(pendiente)

### Informe de las 5:40 — algoproject-18

(pendiente)

### Informe de las 5:40 — algoproject-07

(pendiente)
