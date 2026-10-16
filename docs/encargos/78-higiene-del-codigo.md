# 78 — Higiene del código: lo repetido, lo muerto y lo que hace lento cambiarlo

## Estado (cada sesión actualiza su fila)

| parte | qué | estado |
|---|---|---|
| A | Borrar lo muerto y lo que solo llaman los tests | hecho 2026-10-16 salvo: `sqx/variants/build/stoploss.py` (la ficha `knowhow/sqx-format/grafting-a-stop-loss.md` y OPEN.md #-risk la dan por viva, y lo importan `tests/test_stoploss.py`/`test_strategymeta.py`: decisión A del dueño), `core/significance.py min_track_record` (fichas `mintrl-explosion-is-correct` y `psr-dsr-two-conventions-jsharpe` + `test_inference_vs_jsharpe`: decisión A), `core/commission.py broker_pct` (`assets/RULES.md:318` lo declara el accesor del paso 26: decisión A), `core/worker.py wait_ready` (`knowhow/sqx-drive/driving-a-role.md` lo da por herramienta y `core/worker.py` lo carga la campaña viva: decisión A); `portfolio/` congelada |
| B | Un escritor atómico, `core/fsio.atomic_write` | en parte 2026-10-16: `core/fsio.py` + test, 15 llamadores convertidos, trinquete `os_replace` = 12 en `tools/ratchet.json`. Esperan a que acabe la celda de 07 (el autopiloto vivo los importa): `core/store/*` (y borrar `write.atomic`, que aún usan `ledger/cells.py`, `sqx/projects/patch.py`, `taskcap.py`), `pipeline/autopilot/{finalists,judge,kept}.py`; tras el 77, `ui/daemon/`. No se convierten (no son escribir un fichero entero): `core/uitoken.py` (modo 0600), `core/barstore.py` (parquet en streaming), `sqx/projects/sessiondb.py` (copia), `sqx/curate/aftercut.py` (varios a la vez), `mt5/fleet/collect.py:62` (mueve), `core/store/collect.py:155` (directorio) |
| C | Un `core/proc.run` con timeout; un solo cliente de worker SQX | pendiente |
| D | `bin/lib-agent-alert.sh` recoge lo repetido de los scripts | hecho 2026-10-16: `resolve_data`, `resolve_claude`, `dry_run`, `take_lock` en la lib; la usan 10 scripts (nightly-docs, nightly-commit-proposal, daily-funding-deals, daily-literature-scout, weekly-docs-health, weekly-funding-refresh, weekly-knowhow-review, weekly-project-cleanup, weekly-reconcile, weekly-refactor-scout). Aplazado: `nightly-audit.sh` y `nightly-fix.sh` (cambios sin commitear de otra sesión); `weekly-data-update.sh`, `monthly-oos2-roll.sh`, `weekly-claude-cleanup.sh` y `sqx-log-prune.sh` (resuelven DATA/lock con otra forma, no es copiar tal cual); `workflow.sh`, `remote.sh`, `sqx-worker.sh`, `mirror-data.sh` (pueden estar en uso) |
| E | Tests: marcas, `conftest.py`, `checks.py --fast`, hook del mapa | hecho 2026-10-16 salvo: helpers duplicados de `conftest.py` (ninguno es mover tal cual: los cuerpos difieren), marca `slow` sin tests marcados, `pytest` en un solo proceso no corre (los `*_planted` exigen un proceso por fichero: usar `tools/audit_tests.py`), y lo de las barras (docstrings, `sync_bars`, README de `core`, ratchet `pyright.perf`) que es de otra sesión |
| F | Contrato de estudios: `verdict.csv` y `config_hash` donde faltan | hecho 2026-10-16 salvo lo diferido (abajo) |
| G | Rutas muertas en la documentación; Flask; `translate` | hecho 2026-10-16 salvo `mt5/README.md`, `ui/daemon/README.md` (`studyapi.py`, `saved.yaml`) y `bin/README.md` (`mt5linux.sh`, es un script externo de MetaQuotes), fuera de alcance de esta sesión |

## Tu oficio

**Sonnet** (regla 17: es ejecutar lo ya decidido). Las partes no comparten fichero: lánzalas como subagentes
`general-purpose` con `model: "sonnet"` a la vez, salvo B y C, que van **después del 77** en todo lo
que esté bajo `ui/daemon/` (el 77 lo mueve; hacerlo antes es tocarlo dos veces).

## Tu encargo

Quitar la fricción que la revisión del 2026-10-16 midió: código que ya nadie llama, 25 escrituras
atómicas hechas a mano (14 con carrera), 57 llamadas a procesos sin timeout, 4 clientes de SQX, una
batería de tests que solo se puede correr entera o fichero a fichero, y `checks.py` en rojo. Devuelves
al dueño los recuentos antes y después.

## §0 De dónde sale

`AlgoData/audit/refactorScout/2026-10-16.md`, hallazgos `dead-*`, `conv-atomic-writes`,
`conv-shared-direct-writes`, `rob-subprocess-timeouts`, `dup-sqx-clients`, `dup-sqx-runner-clones`,
`dup-bin-boilerplate`, `dx-*`, `conv-study-contract`, `conv-ruff-b023`. El dueño dijo sí a todo el
2026-10-16.

## Parte A — Lo muerto (regla 21)

Borra, con sus citas (README, ficha de knowhow, `assets/RULES.md:242`, whitelist de vulture):
`studies/data/spread/fundedswap.py`, `pipeline/ledger/progress.py`,
`core/assetwrite/__init__.py:164 rename_cost`, `core/paths.py:135 view_file`,
`core/assetwrite/markets.py:102 set_expected_sign`. Los que solo llaman los tests
(`core/surface/shift.py`, `sqx/variants/build/stoploss.py`, `core/surface/plateau.py:122,137`,
`core/significance.py:163 min_track_record`, `core/commission.py:43 broker_pct`,
`core/worker.py:140 wait_ready`, `portfolio/…` excluidos por la congelación) se borran con sus tests,
**salvo** que una ficha de knowhow los dé por herramienta viva: entonces pregunta. Las claves de
config sin lector (`portfolio/common/construct/config.yaml` `equity.reconcile_max_trades` queda por la
congelación; `assets/_classes.yaml:42,77`) se borran.

## Parte B — Un escritor atómico

`core/fsio.py`: `atomic_write(path, data)` con temporal único (PID + hilo) en el mismo directorio y
`os.replace`, `encoding="utf-8"`. Sustituye a `core/store/write.py:94 atomic` y a las ~25 copias
(lista en el informe; empieza por las 14 de `.tmp` fijo). También a las escrituras directas de
ficheros que otro proceso lee: `ledger/cells.py:151`, `pipeline/autopilot/finalists.py:45`,
`pipeline/autopilot/judge.py:199`, `core/store/extra.py:118`. Un check en `tools/checks.py` cuenta
`os.replace` fuera de `core/fsio.py`, con trinquete.

## Parte C — Procesos y SQX

- `core/proc.py`: `run(cmd, timeout, …)` con timeout obligatorio y `check=True` por defecto. Primero
  los `rsync`, `ssh` y `sqcli`; luego el resto de los 57. Trinquete en `checks.py` para
  `subprocess.run` sin `timeout=`.
- Un solo cliente de worker: `core/worker.py`. `sqx/projects/liveapi.py`, `sqx/projects/live.py:64,101`,
  `sqx/data/update.py:70` pasan por él; los timeouts (120 s, 600 s) salen de un sitio.
- Clones: `sqx/projects/mcretest.py:22,52` contra `crosschecks.py:13,36`, y `sqx/variants/harness.py:188`
  contra `crosschecks.py:95` → una sola.
- Ruff B023 (16 cierres sobre la variable del bucle): revísalos uno a uno y arregla los que sean bug.

## Parte D — Los scripts de `bin/`

`bin/lib-agent-alert.sh` gana `resolve_data`, `resolve_claude`, `take_lock` y `dry_run`; los scripts
que copian esos bloques (unos 20) los llaman. No toques `bin/nightly-audit.sh` ni `bin/nightly-fix.sh`
mientras tengan cambios sin commitear de otra sesión.

## Parte E — Tests y checks

- `pyproject.toml`: `testpaths`, y las marcas `ui` (PySide6), `sqx` (necesita una instalación) y
  `slow`; `pytest -m "not ui and not sqx and not slow"` filtra dentro de un fichero; la batería entera va por `tools/audit_tests.py` (los `*_planted` piden un proceso por fichero, 2026-10-16).
- `tests/conftest.py` con los helpers que hoy se copian (`_sqx`, `_days`, `_trades`, `_stage`, `_rows`).
- `tools/checks.py --fast` sin pyright ni ruff sobre todo el árbol; hoy tarda 68 s.
- `.claude/hooks/stop_checks.py` falla si se añadieron o borraron `.py` y `PROJECT_MAP.md` no se
  regeneró (regla 22, hoy solo prosa).
- Deja `checks.py` en verde: `DEPENDENCIES.md`, la cabecera de
  `knowhow/research/price-rounding-per-asset.md` y el PLR0913 231→232 (empaqueta los parámetros de
  la función nueva que lo subió).

## Parte F — Contrato de estudios

`wfc`, `cscv`, `marketSurfaces`, `isOos` y `monkey` no escriben `verdict.csv` (`/curate` no puede
aplicarlos); `board`, `monkey`, `wfm`, `edgeCost`, `entryQuality`, `decay` y `gate` no emiten
`config_hash` (la ventana no puede marcarlos obsoletos). Añádelos con `core.study`
(`core/study/CONTRACT.md`). Si un estudio no tiene veredicto por estrategia (`board` puede ser un
panel, no un estudio), **pregunta** antes de inventarlo.

## Parte G — Documentación y dependencias

Las 18 rutas citadas que no existen (`ui/desktop/README.md` ×8, `ui/daemon/README.md` `studyapi.py`,
`mt5linux.sh` en `knowhow/mt5/mt5-under-wine.md`, `bin/README.md`, `mt5/README.md`, …). Flask fuera
del entorno (no está en `requirements.txt`; se desinstala). La fila de `translate` en
`docs/SKILLS.md:26` (se regenera con `tools/skillmap.py`).

### Parte F — qué se hizo y qué se difiere

- Hecho: `wfc` y `cscv` escriben `verdict.csv` (una fila por lote de variantes, `verdict` = su `estado`, igual que `marketSurfaces` y `wfm`; no corta nada).
- `config_hash` ya estaba: medido sobre los JSON de `AlgoData/reports`, todos los resultados de `gate`, `wfm`, `edgeCost`, `entryQuality`, `decay`, `isOos` y `monkey` lo llevan (lo firma `core.study.result.envelope`). Solo `board` no lo emite.
- Diferido, decisión del dueño: `isOos` y `monkey` no tienen veredicto por estrategia (su código dice que no juzgan: `isOos` marca blando por Benjamini-Hochberg, el veredicto de `monkey` es de `monkeyExcess`); `board` es un panel de celdas, no de estrategias (ya en la lista de abajo).

## Decisiones del dueño — pregúntalas (regla 11)

- A: código que solo llaman los tests pero que una ficha da por herramienta viva.
- F: `board`, ¿estudio o panel?
- F: `isOos` y `monkey`, ¿qué es pasar o fallar por estrategia (¿IS/OOS por Benjamini-Hochberg? ¿p del mono < alfa?) para que `/curate` pueda aplicarlos?

## Lo que no tocas

El master; `portfolio/` (congelada); lo que el 75, 76 y 77 tengan abierto; ficheros con cambios sin
commitear de otra sesión; `ui/daemon/` hasta que el 77 haya movido lo suyo.

## Objetivo — un comando

```bash
python3 tools/audit_tests.py --changed && \
! test -e studies/data/spread/fundedswap.py && ! test -e pipeline/ledger/progress.py && \
python3 tools/depmap.py && python3 tools/checks.py
```

## Cómo cierras

Qué hizo · qué verificó, con la salida pegada · qué dejó y por qué · qué descubrió para `knowhow/`.
`graphify update . && python3 tools/projectmap.py`. La lista de ficheros cambiados y **¿Quieres hacer
el commit?**

/loop Lee docs/encargos/78-higiene-del-codigo.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
