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
| 8 | Corrida real en gorilla (celda del dueño) → `bin/remote.sh gorilla collect` → paso 26 en leaseWeb (#123, 72 D) | 95 | gorilla, luego MT5 | pendiente | celda del dueño |
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
| G1 | 8 | celda de la corrida de gorilla | A AUDUSD H1 largos reversión · B EURUSD M30 · C GBPJPY H1 o XAUUSD M15 momentum | A |
| P10 | 5 | dos objetivos de `perf/inputs/construct.py` apuntan a datos borrados | A primer miembro + cosecha USDJPY (no existe) · B cosecha XAUUSD `Test_XAUUSD_H1_ruptura_wtc3` · C retirarlos | B |
| D27 | 5 | ledger único del 66 | el diseño A/B/C está escrito en el 66, sección «D27 · Diseño…» | sin recomendación aquí; fuera de la ruta crítica |
