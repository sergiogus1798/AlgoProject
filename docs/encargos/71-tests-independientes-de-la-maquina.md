# 71 · Tests independientes de la máquina

**Estado:** sin empezar. Dueño, 2026-10-14 (D26 = A): cada test construye sus datos en una raíz
temporal, en vez de mirar en `AlgoData` los datos que hay en esta máquina. **Se lanza cuando el
workflow haya dado una pasada limpia** (regla 19: nada pesado a su lado).

**Tu oficio:** tests (Sonnet escribe; regla 17). Es mecánico. Lo único que se decide son las
preguntas de abajo.
**Tu encargo:** que `python3 tools/audit_tests.py` pase igual aquí (leaseWeb) y en gorilla, cuyo
`AlgoData` sólo lleva los datos de mercado (`bin/mirror-data.sh`). Devuelves al dueño la lista de
tests que pasaron a raíz temporal y la de los que siguen leyendo datos reales, cada uno con su
motivo.

## §0 De dónde sale

Cierre del encargo 68, 2026-10-14. La tanda completa en gorilla dio 345 tests corridos, 302 bien y
40 ficheros que fallan. La clasificación dio:

| causa | ficheros |
|---|---|
| leen datos que sólo existen aquí | 36 |
| arreglos sin comitear de otra sesión (`test_autopilot_closing`, `test_perf66_review_data`) | 2 |
| entorno: sin terminal MT5 en gorilla, y pyright no encontrado por el trinquete | 2 |

Ninguno es un bug de código.

## Partes

1. **La base de fondeo plantada.** Ficheros: `test_funded_bank`, `test_funded_bank_run`,
   `test_funded_decide`, `test_funded_price`, `test_funded_rules`, `test_fleet_risk_rules`,
   `test_portfolio_stagea`, `test_portfolio_stageb` y `test_ui_portfolios`.
   - Leen `funding/firms.yaml` y `funding/funding.sqlite` a través de
     `portfolio/funded/rules/catalog.py:44-47` y `firms.load`.
   - Arreglo: un ayudante en `tests/` que planta una raíz temporal con una firma y un plan
     mínimos. El patrón es el de `tests/portfolio_planted.py` y `ALGO_DATA_ROOT`.
2. **Un `.sqx` de muestra en `tests/fixtures/`.** Ficheros: `test_advance`, `test_advance_edges`,
   `test_chain`, `test_launch` y `test_archive`.
   - Ya construyen un árbol temporal (`tree(root)`), pero copian la semilla de
     `AlgoData/raw/Test_USDJPY_donchianUpperCrossUp_M30/SPP_IS/…`.
   - Arreglo: una estrategia pequeña dentro del repo. Hay que comprobar su tamaño; el repo no
     guarda datos pesados (regla 7).
3. **Las cosechas e informes de un proyecto.** Ficheros: `test_identity`, `test_ui_screen`,
   `test_ui_tearmarket`, `test_ui_tearsheet`, `test_ui_cmdpalette`, `test_ui_runner`,
   `test_ui_workflow`, `test_ui_batch`, `test_ui_studypage`, `test_ui_strategy`,
   `test_ui_research` y `test_ui_shell`.
   - Leen `harvest/`, `raw/`, `reports/` y `strategyPermutations/` de
     `Test_USDJPY_donchianUpperCrossUp_M30`, `Trade_NIKKEI225_M30_volatilidadL` y
     `Test_XAUUSD_H1_ruptura_mcptR`, más el perfil de mercado.
   - Arreglo: una cosecha mínima plantada (`metrics.parquet`, `trades.parquet` e informes `.json`)
     con las columnas que lee cada ruta.
4. **El archivo de versiones.** Ficheros: `test_portfolio_build`, `test_portfolio_pool`,
   `test_portfolio_search`, `test_portfolio_universe` y `test_portfolio_testroot`.
   - Piden versiones concretas de `AlgoData/archive`.
5. **Los sueltos:**
   - `test_mt5_pool`: un `run.json` de `mt5/verify`.
   - `test_mt5_autopilot`: `structural/`, y además falla al recoger el test.
   - `test_sqx_problems`: un proyecto del master.
   - `test_newsfilter`: `newsfilter-reference`.
   - `test_feedquality`: `feedQuality/calibration.json`.
6. **El entorno de gorilla.**
   - `pyright` debe estar en el `PATH` que ve `tools/ratchet.py`. Se instala con `bin/remote.sh
     gorilla python3 -m pip install --user -r requirements.txt`, y se comprueba que el
     trinquete lo encuentra.
   - `test_mt5_start_check` necesita el terminal bajo Wine: se marca como test de esta máquina
     sólo si el dueño lo dice (D3).

## Decisiones del dueño — pregúntalas (regla 11)

- **D1.** Algunos tests leen datos reales **a propósito**: comprueban la cosecha o el archivo
  vivos, no sólo el código. Para cada uno que lo parezca hay dos lecturas: (a) pasa a raíz
  temporal; (b) se queda como test de esta máquina y se aparta en gorilla con su motivo. Se
  pregunta con la lista delante.
- **D2.** El `.sqx` de muestra de la parte 2: ¿una estrategia real recortada, o una sintética
  generada para el test?
- **D3.** `test_mt5_start_check` en gorilla: ¿instalar allí el terminal, o apartar ese test en
  gorilla?

**Contestadas por el dueño (2026-10-14):**
- **D1 → (a)**, salvo los tests que existen para validar los datos vivos de esta máquina: esos (b),
  apartados en gorilla con su motivo. La lista se le enseña igualmente al cerrar la parte 3.
- **D2 → sintética**: determinista y sin datos del dueño en git (regla 7).
- **D3 → apartar el test en gorilla.** Condición del dueño: las estrategias que salgan de gorilla se
  verifican (paso 26) en el MT5 de leaseWeb. Comprueba que el camino existe —que una superviviente
  de gorilla llega al MT5 Bridge de esta máquina— y, si no existe, apúntalo en `OPEN.md` y en el
  encargo 57.

## Lo que no tocas

- Los ficheros de otra sesión: `portfolio/testroot/harvest.py`,
  `tests/test_autopilot_closing.py` y `tests/test_perf66_review_data.py`, mientras sigan sin
  comitear.
- El código de producción, salvo para darle una raíz de datos a un test que hoy no la acepta.
  Eso se dice en el cierre, con su fichero y línea.
- `AlgoData` real: ningún test escribe en él.
- gorilla, salvo con `bin/remote.sh` (regla 12).

## Objetivo — un comando

```bash
python3 tools/depmap.py && python3 tools/checks.py && python3 tools/audit_tests.py \
  && bin/remote.sh gorilla python3 tools/audit_tests.py
```

Sale 0 sólo cuando pasan los dos: aquí y en gorilla, después de comitear y empujar.

## Cómo cierras

Qué hizo, qué verificó (con la salida de los dos `audit_tests` pegada), qué dejó sin hacer y por
qué, y qué descubrió para `knowhow/eng/tests-are-scripts-run-via-audit-tests.md`. Después, los
ficheros cambiados y **¿Quieres hacer el commit?**

/loop Lee docs/encargos/71-tests-independientes-de-la-maquina.md y ejecútalo entero. Tras cada iteración corre el Objetivo; si sale 0, para el bucle; si no, arregla lo que falló y vuelve a correrlo.
