# 78 — Higiene del código: lo repetido, lo muerto y lo que hace lento cambiarlo

## Estado (cada sesión actualiza su fila)

| parte | qué | estado |
|---|---|---|
| A | Borrar lo muerto y lo que solo llaman los tests | pendiente |
| B | Un escritor atómico, `core/fsio.atomic_write` | pendiente |
| C | Un `core/proc.run` con timeout; un solo cliente de worker SQX | pendiente |
| D | `bin/lib-agent-alert.sh` recoge lo repetido de los scripts | pendiente |
| E | Tests: marcas, `conftest.py`, `checks.py --fast`, hook del mapa | pendiente |
| F | Contrato de estudios: `verdict.csv` y `config_hash` donde faltan | pendiente |
| G | Rutas muertas en la documentación; Flask; `translate` | pendiente |

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
  `slow`; `pytest -m "not ui and not sqx and not slow"` es el subconjunto rápido.
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

## Decisiones del dueño — pregúntalas (regla 11)

- A: código que solo llaman los tests pero que una ficha da por herramienta viva.
- F: `board`, ¿estudio o panel?

## Lo que no tocas

El master; `portfolio/` (congelada); lo que el 75, 76 y 77 tengan abierto; ficheros con cambios sin
commitear de otra sesión; `ui/daemon/` hasta que el 77 haya movido lo suyo.

## Objetivo — un comando

```bash
python3 -m pytest -m "not ui and not sqx and not slow" -q && \
! test -e studies/data/spread/fundedswap.py && ! test -e pipeline/ledger/progress.py && \
python3 tools/depmap.py && python3 tools/checks.py
```

## Cómo cierras

Qué hizo · qué verificó, con la salida pegada · qué dejó y por qué · qué descubrió para `knowhow/`.
`graphify update . && python3 tools/projectmap.py`. La lista de ficheros cambiados y **¿Quieres hacer
el commit?**

/loop Lee docs/encargos/78-higiene-del-codigo.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
