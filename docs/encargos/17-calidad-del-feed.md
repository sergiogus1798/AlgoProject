# 17 · Calidad del feed y atribución de ticks malos — encargo autocontenido

**Tu oficio:** Python sobre la librería de barras. No toca SQX. Sale del **item 5** del PDF del
dueño `TRADE_LEVEL_TESTS.pdf`.

Lee `CODESTYLE.md` · `core/README.md` §`barstore.py` · `docs/manual/13-barras.md`.

---

## 0 · Por qué importa aquí más que en otro proyecto

Sólo hay **un proveedor de datos** —Dukascopy, salvo el Brent— así que no existe la comprobación
cruzada entre proveedores que resolvería esto de un plumazo. Si una parte del beneficio de una
estrategia sale de velas erróneas, no hay nada fuera del propio fichero que lo delate.

## 1 · Lo ya medido — el punto de partida, no el resultado

🔬 2026-09-24, `XAUUSD_DukasM1_Infinox`, con `core.barstore.source`:

| | |
|---|---|
| barras M1 | **7.949.285**, de 2003-05-05 a 2026-09-22, cargadas en **0,4 s** |
| inconsistencias OHLC (`H < max(O,C)`, `L > min(O,C)`, `H < L`) | **0** |
| barras planas (`High == Low`) | **40.097**, el **0,50 %** |

Las dos primeras filas son buenas noticias y acotan el trabajo: **la detección de inconsistencias
OHLC no va a encontrar nada**, así que el valor está en las otras tres familias del PDF —picos,
precios estancados y huecos— y sobre todo en la **atribución**.

Las 40.097 barras planas son el primer hilo del que tirar: una barra plana en el M1 del oro a las
14:30 de un martes no es lo mismo que a las 23:58 de un viernes, y ese reparto por hora es la
primera tabla del informe.

## 2 · Lo que construyes

Módulo nuevo, y **no cuelga de `strategies/`**: esto describe un feed, no una estrategia. Ponlo como
carpeta propia de primer nivel, igual que `nulls/` lo es por tener varios consumidores.

Dos mitades, y la segunda es la que justifica la primera:

**Detección**, por símbolo: picos (`|r_t|` sobre `K · MAD_local × 1.4826`, y sobre todo
**pico-y-vuelta** dentro de `m` barras, que es la firma del tick malo), rachas de OHLC idénticos de
`L` barras o más en horario activo, minutos ausentes fuera de fin de semana y festivos conocidos.
Salida: un informe de calidad por símbolo, **con recuento por tipo y por año**.

**Atribución**, por estrategia: marcar las operaciones cuya entrada, salida o fill de SL/TP cae a
`±w` barras de una anomalía; comparar **su cuota del beneficio contra su cuota del número de
operaciones**; y recalcular las métricas sin ellas. Esa comparación es el resultado del encargo: un
2 % de las operaciones que aporta el 40 % del beneficio es un hallazgo; un 2 % que aporta el 2 % no
lo es.

## 3 · Los umbrales son del dueño

`K`, `m`, `L` y `w` deciden el resultado entero, y fijarlos después de ver los números no vale. Los
propones con un argumento, **se los enseñas, y no los mueves después**. `ledger/thresholds.yaml`
(encargo 8) es donde viven cuando exista.

## 4 · Un aviso sobre el uso

Marcar operaciones y recalcular sin ellas **no es una limpieza de datos**: es un diagnóstico. Quitar
del backtest las operaciones que tocaron una anomalía y quedarse con el resultado mejorado es
sobreajuste con otro nombre. Lo que el informe dice es *cuánto de lo que ves podría no ser real*, no
*cuánto ganarías con datos buenos*.

## 5 · Cómo cierras

`python3 tools/depmap.py && python3 tools/checks.py` → 0 problemas · página de manual en español con
salida real · y **una fila por símbolo en `~/Desktop/AlgoData/INDEX.md`** con su recuento de
anomalías, que es donde alguien lo va a buscar.
