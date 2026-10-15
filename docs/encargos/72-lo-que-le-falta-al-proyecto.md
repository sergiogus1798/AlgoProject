# 72 — Lo que le falta al proyecto: decisiones, guardián, conciliador, collect y janitor

## Estado (cada sesión lo actualiza)

| parte | qué | modelo | estado | espera a |
|---|---|---|---|---|
| A1 | cola única de decisiones del dueño, dossier PDF | Opus redacta, Sonnet recoge | hecho 2026-10-15 (`docs/AgentPDFs/decisiones-pendientes-2026-10-15.pdf`, 8 págs.) | — |
| A2 | aplicar las respuestas del dueño: F4-F7, V2-V4, L1, L2, L4 (C2-C11, F8 y L3 son de la otra instancia) | Sonnet | hecho 2026-10-15 salvo L4 (F4 Bonferroni en `walkforward.compare`, F5, F6 en `candidates.in_pool`, F7b en `stagea.room`, V1b-V4, L1, L2) | L4: el recuento al que iba la silueta ya no existe |
| B | guardián de suelos con la ventana cerrada | Sonnet | hecho 2026-10-15 (`mt5/fleet/guard.py`) | — |
| C | conciliador semanal + SPRT en cron | Sonnet; Haiku instala la línea | a medias: cabecera, registro desde `magics.csv` y manual hechos; ni encadenado ni cron | FundingPips falta en `mt5_accounts`; `live.run` va por estrategia (`--asset --deposit --sqx`) |
| D | «collect» gorilla → leaseWeb (OPEN #123) | Sonnet | hecho 2026-10-15 salvo la verificación real (`bin/remote.sh gorilla collect`) | una superviviente en gorilla |
| E | el janitor no retira un workflow aparcado (OPEN #116) | Sonnet | hecho 2026-10-15, #116 cerrada (`python3 -m ui.daemon.projects.janitor`) | — |
| F | mapa, dependencias, revisión y cierre | Haiku + `reviewer` | hecho 2026-10-15 (revisión: 8 arreglos aplicados) | — |

**Bitácora**

- 2026-10-15 — escrito. Dueño: Q1 B (sólo frentes nuevos), Q2 A (el 53 sigue parado hasta cerrar A),
  Q3 A (el guardián sólo avisa), Q4 A (56 F2/F4/F5 y 62 partes 2-4 congelados), Q5 A (empieza ya, en
  paralelo), Q6 A (la cola es un dossier PDF).
- 2026-10-15 — A1 hecho: 3 recolectores Sonnet, dossier escrito en Opus, PDF de 8 páginas. La otra sesión (c8) confirma que no hay solape; tiene el custodio, `assets/`, el repreciador, `ledger/thresholds.yaml` y, después, `mt5/verify/` y `portfolio/funded/`: A2 coordina con ella antes de tocar `thresholds.yaml`. B, D y E esperan B-1, D-1 y E-1.
- 2026-10-15 — dueño: B-1 A, D-1 A, E-1 A. B, D y E lanzados a la vez en Sonnet. Reloj de Hantec: UTC+3 hoy (beacon), se distingue EETUS/EET entre el 25-10 y el 1-11. La cuenta Hantec 8063673 es fondeada (guarda `mt5/guard.py`, commit 37d197a).
- 2026-10-15 — B, D y E hechos; revisión independiente con 8 arreglos (rsync a temporal, guardián aislado por cuenta y del log del collector, `guard.json` atómico, tupla de excepciones del janitor). Objetivo: 11 tests verdes; `checks.py` sólo con 3 fallos previos ajenos (`tools/manual.py`, `xauusd-corpus`). Quedan C y A2 (respuestas del dueño) y la verificación real de D.
- 2026-10-15 — **dueño: «toma todas tus recomendaciones»** sobre `docs/AgentPDFs/decisiones-pendientes-2026-10-15.md`. Contestadas con la recomendación del dossier: C1 C (α 0,01) · C2 A · C3 A · C4 A (v0 provisional) · C5 A · C6 A · C7 A · C8 A (manda el 65; se borra `sin_fallo`) · C9 A · C10 A (`oos2` sólo para los monos de 17-18, anotado en el ledger) · C11 A · F1 `close_to_open_blocks` · F3 A · F4 B · F5 `pnl` / `[build, oos1, oos2]` / `[5, 100]` · F6 A · F7a, c, d, e confirmar · F7b cambiar (el tope cuenta el trailing) · F7f dejar · F8a, b arreglar · F8c archivar tras la corrida limpia · V2 A (1 barra) · V3 A (registro desde `magics.csv`) · V4 A · L1 2014-01-01 · L2 no construir sobre Brent · L3 (a) ya, (b) después · L4 mostrar. **Sin respuesta, porque el dossier no recomendaba nada:** F2 (`tax_rate`) y V1 (qué es la cuenta FTMO 541350656; Hantec 8063673 es fondeada, FundingPips 11308943 es SIM). S1-S6 son preguntas del dueño a soporte. - 2026-10-15 — dueño: **V1** — FTMO 541350656 es cuenta fondeada real (ya cobró un payout y le devolvieron el challenge; contesta también S3 para esta cuenta), FundingPips 11308943 está en fase 2 de 2, Hantec 8063673 en fase 1 de 2. **F2** — impuestos en ningún sitio: encargo 73, hecho y borrado el mismo día (`owner.tax_rate: null` = apagado; código en `portfolio/funded/`, ficha `knowhow/costs/funded-stage-catalogue-gaps.md`, capítulos 79 y 88). La otra sesión avisa: **C1 y F1 ya estaban aplicadas** (commits 9aef247 y 6e53802), no repetir; `thresholds.yaml`, `criteria.yaml` y `assets/` libres. **F3 en conflicto:** 6e53802 fijó `p_payout_denied` 5 % POR COBRO («dueño 2026-10-15») y el dossier recomendaba 5 % al año; Dueño: **F3 A** — se queda el 5 % POR COBRO ya escrito (A2 no lo toca). **V1b A** — el conciliador concilia las tres cuentas: `live.accounts` = FTMO 541350656, FundingPips 11308943 y Hantec 8063673. La parte C ya no espera nada del dueño (V2 1 barra, V3 registro desde `magics.csv`, V4 sin listón).
- 2026-10-15 — **reparto con la instancia que sigue el «Orden de ejecución»** (dueño): C2-C11, F8 (= #104) y L3 (= #118) pasan a esa instancia, que los aplica al reescribir 49/50/53 y antes de la corrida de la fila 6. **A2 aquí se queda con F4, F5, F6, F7, V2-V4, L1, L2 y L4.** El dueño confirma que el conciliador sólo LEE las operaciones de las tres cuentas y que eso cabe en «backtests y leer», así que C sigue adelante.
**A2 coordina antes con la sesión que tiene `ledger/thresholds.yaml`, `pipeline/autopilot/criteria.yaml` y `assets/`.**
- 2026-10-15 — sesión algoproject-95: A2 y C en tres Sonnet. **Hecho:** F4 B (`wf.confidence` 0,95 conjunto, Bonferroni en `walkforward.compare`), F5, F6 A (`candidates.in_pool`: fuera `Test_Calib_*` y lo creado antes del 2026-10-01), F7a/c/d/e confirmadas en PLAN §12, F7b (`stagea.room` = min(daily_loss, max_loss) en planes trailing), F7f anotada; V1b `live.accounts: [ftmo, fundingpips, hantec]`, V2 1 barra, V3 (`reconcile.register.read()` sale de `magics`; se borran `magics --register` y la clave `register:`), V4; L1 (NIKKEI225 `build.from` 2014-01-01, #117 cerrada), L2 (nota en `assets/RULES.md`); notas desfasadas. **No hecho:** L4 — `core.surface.trials.independent` no tiene llamador y el CSCV ya no guarda `trials`: no hay recuento junto al que ponerla (anotado en #96). C paso 2 — `portfolio.funded.live.run` pide `--asset --strategy --firm --deposit --sqx` (backtest de toda la vida) y el registro no los lleva; C paso 4 (cron) esperando, porque una corrida real hoy se para en «fundingpips: no está en mt5_accounts» y en la ausencia de `magics.csv`.

## Tu oficio

Eres el **orquestador, en Opus**. Escribes tú la cola de decisiones (A1), porque es diseño y
estadística. Todo lo demás lo reparte a subagentes (regla 17):
- B, C, D y E van a un `general-purpose` con `model: "sonnet"` cada uno, lanzados a la vez, porque no
  comparten fichero.
- Lo puramente mecánico va a `model: "haiku"`: la línea del crontab, `graphify update .`,
  `tools/projectmap.py`, `tools/depmap.py` y la fila del README.

Cada subagente recibe su parte de este fichero copiada en el brief, no el fichero entero. Te devuelve
qué hizo, lo verificado con la salida pegada, lo que dejó y por qué.

## Tu encargo

Cerrar los cinco huecos de la revisión del 2026-10-15 que no son errores de ejecución del workflow:
1. Las decisiones que dejan provisionales los umbrales de toda la cadena.
2. Un aviso cuando una cuenta en vivo se acerca a un suelo de la firma con el MetaTracker cerrado.
3. El conciliador semanal y el SPRT ejecutándose solos.
4. El camino para que las supervivientes de gorilla lleguen al paso 26 de leaseWeb.
5. Que el janitor de los lunes deje de borrar workflows aparcados.

El dueño recibe:
- un PDF con cada decisión, sus opciones y una recomendación con su coste en estrategias;
- notificaciones de escritorio de los suelos;
- un cron más;
- un comando nuevo con su capítulo del manual;
- un janitor que no destruye datos.

## §0 De dónde sale

- **La revisión del 2026-10-15** (sesión del dueño): «qué le falta a este proyecto», sin contar sacar
  estrategias. Fijó el orden 2 → 1 → 3 de los siete puntos y lo contestado arriba.
- **Los monos por la cadena** (punto 1) siguen en el **53**, parado (README «Orden de ejecución», fila
  10). La corrida nula del paso 8 sigue en el **65 B** y el repreciador (#120, #121) en el **70**. Este
  encargo no los toca.
- **Diferidos sin trabajo aquí:** `portfolio/real/`, el asignador de cartera
  (`55-mt5-paso-26-y-flota.md:243`) y el exportador 55-H. Esperan a una superviviente real.

## Parte A1 — La cola de decisiones (Opus)

**Fichero:**
- `docs/AgentPDFs/decisiones-pendientes-<fecha>.md`;
- su PDF, con `/dossier-pdf`;
- su fila en `docs/AgentPDFs/README.md`.

**Cómo:**
1. Lanza 3 `Explore` con `model: "sonnet"`, en paralelo, uno por grupo de fuentes. Cada uno devuelve,
   por decisión: de dónde sale (`file:line`), qué se decide, las lecturas posibles y qué se ha medido
   ya.
   - **Cadena:** `docs/AgentPDFs/WORKFLOW.md:236-244`; OPEN #93, #50, #19, #96, #117, #118; el §3 y
     las filas 1.2 y 1.9 del 49; los P1-P9 del 51; el T3 del paso 14, que no discrimina (WORKFLOW
     fila 14); la sesión de Brent (WORKFLOW:244).
   - **Cartera y fondeo:** OPEN #87, #85, #104; las entradas `tax_rate`, `p_payout_denied` y `t1_gap`
     del 54 (`54:30-36`); 61-1 y 61-4; `incubation.*`, `wf.confidence`, `verdict.pass_percentile` y
     la fracción de riesgo abierto.
   - **Vivo:** las claves vacías de `mt5/reconcile/config.yaml` y `portfolio/funded/live/config.yaml`,
     que bloquean la parte C; la autorización única de `oos2` (README de encargos, «Una sola
     autorización»).
2. Con lo que devuelvan, escribe tú el dossier. Una tabla por decisión, como pide el dueño: código,
   qué se decide, opciones A/B/C, recomendación con su coste en estrategias junto a su ganancia, y la
   fuente. Agrúpalas por qué desbloquean, con lo que desbloquea el 53 primero (regla «una análisis
   acaba en decisión»).
3. Escribe una recomendación concreta para cada decisión. Si una sólo se puede recomendar tras medir,
   dilo y estima el coste de medirla. No la midas.

No decides nada. No tocas `ledger/thresholds.yaml`, ningún `criteria.yaml` ni ninguna configuración.

## Parte A2 — Aplicar las respuestas (Sonnet, sólo cuando el dueño conteste)

- Cada respuesta va a su sitio. Un umbral se cambia en `ledger/thresholds.yaml` con su fila en
  `criteria-history.jsonl`; mover un umbral es del dueño, y su respuesta es la autorización.
- Una issue que la respuesta cierra va a `/open-close`. Lo que cambia una regla del workflow va a
  `WORKFLOW.md`.
- Al acabar, actualiza la fila 10 del «Orden de ejecución». El 53 se despacha cuando estén firmados
  los umbrales de los pasos 10-20.

## Parte B — Guardián de suelos con la ventana cerrada (Sonnet)

**Ficheros:**
- nuevo `mt5/fleet/guard.py`;
- `mt5/fleet/collect.py`, que lo llama al final de cada pasada;
- `mt5/fleet/README.md`;
- `mt5/fleet/app/README.md`, en su «Por ahora» (líneas 96-100);
- `mt5/fleet/CONTRACT.md:5`;
- nuevo `tests/test_fleet_guard.py`.

**Qué hace:**
- El cálculo de cada suelo ya existe: `mt5/fleet/app/floors.py:29` `reading()` da `daily_left` y
  `max_left`; `mt5/fleet/app/state.py:39` lo compara con `red_margin_left` de
  `mt5/fleet/app/config.yaml:8`.
- El guardián reutiliza esas funciones, sin copiarlas. Si `tools/layering.py` impide importarlas
  desde `collect`, súbelas a `mt5/fleet/` y que la app las importe de ahí.
- Por cada cuenta de `AlgoData/fleet/live/`, avisa cuando cruza a rojo: un suelo bajo
  `red_margin_left`, o la cuenta callada más de 300 s (CONTRACT:11). Avisa sólo en el cruce, no en
  cada minuto: guarda el último color en `AlgoData/fleet/guard.json`.
- El aviso es una notificación crítica de escritorio, con el mismo mecanismo que
  `portfolio/funded/deals/notify.py`. Recuerda que cron no tiene el bus de sesión
  (`bin/lib-agent-alert.sh:18`).
- **Sólo lee.** Nunca envía, modifica ni cierra una orden (dueño 2026-10-03, CONTRACT:3-6; reafirmado
  Q3 A el 2026-10-15).

**Prueba:** un latido plantado que cruza a rojo notifica una vez; el siguiente minuto en rojo no
notifica; la vuelta a verde rearma el aviso. La notificación se inyecta, nunca se llama a
`notify-send` real.

**Documentación:** borra del «Por ahora» las alertas con la ventana cerrada; las del móvil siguen
diferidas. No es un comando nuevo: no lleva `__main__`.

## Parte C — Conciliador y SPRT solos (Sonnet; Haiku instala)

**Ficheros:**
- `bin/weekly-reconcile.sh`;
- `mt5/reconcile/README.md`;
- el crontab;
- el capítulo del manual que nombra al conciliador (`grep -l reconcile ~/Desktop/AlgoData/manual-fuentes/*.md`).

**Pasos:**
1. **Bloqueo:** sólo cuando A2 haya rellenado las claves del dueño de `mt5/reconcile/config.yaml` y
   `portfolio/funded/live/config.yaml`. Antes, la parte está en «espera» y no instalas nada.
2. En `bin/weekly-reconcile.sh`, tras `mt5.reconcile.run`, encadena `python3 -m
   portfolio.funded.live.run`. Si alguna estrategia sale `retire`, envía una notificación crítica que
   la nombre. El comando sigue sin enviar órdenes (`portfolio/funded/live/README.md`).
3. Quita el «WRITTEN, NOT INSTALLED» de la cabecera y deja la línea propuesta: **sábado 02:10**
   (`10 2 * * 6`). Ese minuto está libre en el crontab de hoy, después de `weekly-data-update.sh`
   (sábado 02:00), cuyo lock espera.
4. Un subagente Haiku añade la línea al crontab. Primero hace `crontab -l > scratch/crontab-<fecha>.bak`.
   Luego comprueba con `crontab -l | grep -c weekly-reconcile`, que debe dar 1.
5. Haz un `--dry-run` del script y pega su salida.

## Parte D — «Collect» gorilla → leaseWeb (Sonnet)

**Ficheros:**
- `bin/remote.sh`, con un verbo nuevo `collect`;
- un módulo receptor si hace falta, en el paquete que ya maneje el almacén (mira el `README.md` de
  `/store-save`);
- nuevo `tests/test_gorilla_collect.py`;
- el capítulo del manual (regla 8, `/manual-chapter`).

**Qué hace:**
- Lee entero OPEN #123 (`OPEN.md:877`): dice qué no vuelve hoy (supervivientes, `.sqx`, tienda de
  estrategias, ledger…).
- `bin/remote.sh gorilla collect` trae a leaseWeb lo que el paso 26 necesita de una corrida de
  gorilla, con el sufijo `_gorilla` en cada nombre. Lo trae por la vía de `remote.sh`, que hace pull
  primero y no corre bajo un SQX vivo (regla 12). En gorilla sólo se lee.
- Una superviviente traída entra en el pool del paso 26 de leaseWeb igual que una propia.

**Prueba:** con una tienda plantada en un directorio temporal como «gorilla», el collect la deja en
leaseWeb sin pisar una superviviente local del mismo nombre. La verificación real queda como fila
pendiente hasta la primera superviviente de gorilla.

**Cierre:** cierra #123 con `/open-close`, o anótala si queda la verificación real.

## Parte E — El janitor no retira un workflow aparcado (Sonnet)

**Ficheros:** `sqx/projects/sweep.py:45` (`candidates`), su llamador
(`bin/weekly-project-cleanup.sh` o el agente `projectJanitor`) y nuevo `tests/test_sweep_parked.py`.

**Qué hace:** primero pregunta E-1. Con la opción (a), `candidates` recibe `finished(project) ->
bool`, inyectado desde fuera de `sqx/` como ya se hace con `describe`. Un `Test_` cuyo carril no ha
terminado no es candidato.

**Prueba:** un `Test_` aparcado en el paso 13, intacto 48 h, no sale en `candidates`; uno terminado
sí.

**Cierre:** cierra #116 con `/open-close`.

## Parte F — Cierre común (Haiku + `reviewer`)

1. Haiku ejecuta `graphify update . && python3 tools/projectmap.py && python3 tools/depmap.py`
   (regla 22) y confirma las filas del mapa de `mt5/fleet`, `sqx/projects` y `bin`.
2. Los ficheros de todo el encargo pasan por el agente `reviewer` (CONTRIBUTING.md §5). Lo que
   encuentre se arregla antes de la pregunta del commit.
3. Knowhow: lo no obvio va a una ficha en el mismo trabajo. Por ejemplo, cómo llega el bus de sesión
   a cron, o qué no vuelve de gorilla.

## Decisiones del dueño — pregúntalas (regla 11)

| código | qué | lecturas | recomendación |
|---|---|---|---|
| E-1 | Cómo sabe el janitor que un workflow está aparcado (OPEN #116) | (a) inyectar `finished()` desde fuera de `sqx/`; (b) bajar la derivación del carril por debajo de `ui/`. El Council ya rechazó una gracia de 7 días | (a): un parámetro, sin mover capas |
| D-1 | Qué trae el collect | (a) sólo lo que pide el paso 26 (`.sqx` de las supervivientes, su carpeta de la tienda, la fila del ledger); (b) la tienda entera de gorilla | (a): menos disco y sin choques; la tienda entera queda allí |
| B-1 | Avisar también de las noticias y del cierre del viernes en rojo (CONTRACT:8-10), o sólo suelos y silencio | (a) sólo suelos y silencio; (b) los cuatro rojos | (a): es lo que pierde la cuenta; los otros se ven con la ventana abierta |

Las preguntas de A1 no van aquí: son el contenido del dossier.

## Lo que no tocas

- El master, los proyectos del custodio y `oos2`.
- Los encargos 53, 65, 66 y 70, y lo congelado: 56 F2/F4/F5, 62 partes 2-4, 57, 58, 60 y 67.
- Ninguna orden en ninguna cuenta: el guardián y el SPRT sólo leen.
- En gorilla, nada que no pase por `bin/remote.sh`.

## Objetivo — un comando

```
python3 tools/depmap.py && python3 tools/checks.py && python3 -m pytest -q tests/test_fleet_guard.py tests/test_sweep_parked.py tests/test_gorilla_collect.py && ls docs/AgentPDFs/decisiones-pendientes-*.pdf
```

Cubre A1, B, D, E y F. C y A2 esperan al dueño y se marcan en la tabla de estado. Si el Objetivo
falla sólo por una fila que espera al dueño (E-1, D-1 o B-1 sin contestar), para el bucle y
pregúntale.

## Cómo cierras

- Qué hizo cada parte.
- Qué se verificó, con la salida pegada: el Objetivo, el `--dry-run` de C y el `grep -c` del crontab.
- Qué quedó sin hacer y por qué: C hasta las claves, A2 hasta las respuestas, la verificación real
  de D.
- Qué fue a `knowhow/`.
- La tabla de estado y la bitácora, al día.
- La lista de ficheros cambiados, `PROJECT_MAP.md` incluido, y como última línea **¿Quieres hacer el
  commit?**

```
/loop Lee docs/encargos/72-lo-que-le-falta-al-proyecto.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
```
