# 70 · El redondeo al tick del repreciador, por activo

**Estado:** sin empezar. Dueño, 2026-10-13 (R18d = A): por activo, con un campo en la ficha de costes,
medido activo a activo, en un encargo propio.

**Tu oficio:** medición y precios (Opus decide, Sonnet escribe; regla 17). Ningún SQX nuevo: se mide
sobre lotes de variantes que ya existen en `AlgoData/strategyPermutations/`.
**Tu encargo:** que el repreciador (`engines/market/reprice.py`) redondee al tick sólo en los activos
en que SQX lo hace, para que reproduzca a SQX y el paso 18.5 deje de saltarse madres por descuadre.
Devuelves al dueño **una tabla por activo**: redondea o no, el descuadre antes y después en build y en
oos1, y cuántas madres leería el 18.5 con el cambio.

Lee primero el asunto de `OPEN.md` «Step 18.5 skips every XAUUSD mother…» (todos los números del
2026-10-13) y la sección de precios de `engines/README.md`.

## Lo que ya se sabe (2026-10-13)

| activo | tramo | variantes que no cuadran, con redondeo | sin redondeo | lectura |
|---|---|---|---|---|
| XAUUSD H1 | oos1 | 48,5 % | 12,75 % | SQX no redondea |
| USA500 H1 | oos1 | 15,4 % | 0,6 % | SQX no redondea |
| DAX40 M30 | oos1 / build | 7,0 % / 0,85 % | 1,4 % / 1,28 % | mixto: hay que entenderlo |
| NIKKEI225 M30 | oos1 | 0,0 % | 0,1 % y 1,0 % | SQX redondea |
| USDJPY | — | con `tick_step`: 77,73 → 0,01 | — | se queda como está |

## Partes

1. **Entender el DAX40** antes de diseñar nada: por qué build y oos1 van en sentidos opuestos. Si la
   regla de SQX no es «por activo» sino otra (por tamaño de tick, por dígitos, por tramo de costes),
   el campo de la ficha es la solución equivocada: se para y se pregunta.
2. **El campo en la ficha** (`assets/symbols/<S>.yaml`; `core.assetwrite` es el único escritor): nombre,
   valor por defecto y quién lo lee. Pregunta al dueño en tabla antes de escribirlo.
3. **Medir cada activo de `assets/`** que tenga un lote de variantes en disco; los que no lo tengan
   quedan sin valor y el repreciador se niega a repreciarlos sin él (o conserva lo de hoy: pregunta).
4. **El resto del oro**: 0,043 USD por operación en oos1 sin causa (coste de precio de ida y vuelta de
   SQX 0,2873 frente a 0,2879 declarado).
5. **La puerta del 18.5** (`pipeline/autopilot/blind.py:47-48`) reutiliza `wfc.sqx_gap_relative`, que
   en `engines/weekly/panel.py:121` es fracción del neto, como fracción de variantes: su propia clave
   en el ledger, con el valor que diga el dueño.

**Contestado por el dueño (2026-10-14):**
- **Parte 1 primero**: averiguar la regla de SQX en el DAX40 antes de diseñar el campo. Si no va por
  activo, se para y se pregunta.
- **Parte 2**: `price_rounding: tick | none` en la ficha, **sin valor por defecto**.
- **Parte 3**: un activo sin lote medido queda sin valor y el repreciador **se niega** a repreciarlo
  (falla claro).
- **Parte 5**: clave propia en el ledger, arrancando con el valor de hoy; se recalibra después.

## Lo que no se toca sin prueba

`tests/test_reprice.py::test_cost_off_the_tick_rounds_the_fill` y el caso auditado
`tests/fixtures/reprice_audited.csv` (Nikkei) dependen del redondeo: un test que cambia de valor se
enseña con su cifra vieja y nueva, no se actualiza a ciegas.

## Hecho cuando

Cada activo medido tiene su valor en la ficha con su fecha y su fuente; el descuadre de build y oos1
queda por debajo del umbral en los activos medidos, o se dice cuál no y por qué; `bin/workflow-test.sh`
dice PASA; `python3 tools/checks.py` da 0 problemas.
