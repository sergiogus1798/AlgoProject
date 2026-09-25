# 30. Retest en otros mercados — ¿el edge sobrevive fuera de su activo?

### Qué pregunta responde

Una estrategia que gana dinero en el oro puede estar capturando algo real del mercado, o puede
haberse ajustado a las casualidades de esos años concretos de oro. La forma más directa de
distinguirlo es llevarla a otro mercado al que nunca se ajustó y ver si sigue viva.

Esta página cubre la parte mecánica: **qué mercados, desde cuándo y con qué costes** se configuran
en el crosscheck *Retest on additional markets* de SQX.

### Cuándo lo usas, y cuándo no

Después de que la población haya pasado la puerta OOS (`29-puerta.md`). Antes no: este test es
caro y la puerta es lo que lo hace asequible.

No lo uses para *buscar* en qué mercados funciona una estrategia. Los mercados están fijados de
antemano en `assets/_markets.yaml`, y elegirlos después de ver los resultados convierte la prueba
en una selección.

### Qué mercados hay declarados

```bash
python3 -m sqx.projects.crossmarket XAUUSD
```

```
XAGUSD_DukasM1_Infinox   family   2008.01.01 a 2022.12.31   costes: ⚠️ NINGÚN fichero de assets/symbols/ declara este feed
BRENTCMDUSD_ftmo         family   2008.01.01 a 2022.12.31   costes: ⚠️ ...  ⚠️ data_from sin averiguar
```

Dos categorías, y la diferencia importa:

- **`family`** — mismo motor económico que el activo principal. Es la prueba fácil: pasarla no
  demuestra mucho, fallarla sí dice algo.
- **`structural`** — misma *forma* de mercado (volatilidad, horario, ruido) sin motor compartido.
  Es la prueba dura.

### La ventana de cada mercado

La declara `assets/_build.yaml` de una vez para todos los activos, en `crossmarket.segment`:
**`build..oos1`** (decisión del dueño, 2026-09-24), con la misma notación de dos puntos que la MC
Retest. O sea, desde el **inicio del IS del activo principal** —o desde la primera barra de ese
mercado, la que sea más tardía— hasta el final de `oos1`. Para el XAUUSD: la plata va de 2008 a 2022, y un mercado
cuyos datos empiezan en 2013 va de 2013 a 2022.

Se usa todo el histórico a propósito. Recortarlo a la ventana del activo principal tira justo los
años que responderían a la pregunta.

### Los costes

Cada mercado extra lleva su propio `<Setup>` dentro del crosscheck, con **su** spread, **su**
slippage, **su** comisión y **su** swap, leídos de **su** `assets/symbols/<SIM>.yaml`.

⚠️ **El comando se niega a escribir nada si un mercado declarado no tiene fichero de costes.** No
es un fallo: SQX lo correría tan tranquilo con el spread por defecto de su registro, y un resultado
cross-market con un coste inventado es peor que no tener resultado.

Un `<Setup>` lleva un solo spread y la ventana cruza los dos tramos, así que se cobran los del
**OOS**. Al mercado que tiene que sorprendernos no se le da nunca el precio barato.

`<MainTestValues>` dice qué se hereda del test principal en vez de tomarse de este Setup: el
timeframe, la precisión y la distancia mínima se comparten; las fechas, el spread, el slippage, las
comisiones y el swap son propios. La sesión se hereda, porque `assets/` no declara sesión para un
mercado de crosscheck.

### Cómo se configura

```bash
python3 -m sqx.projects.crossmarket XAUUSD \
    --cfx ~/Desktop/SQX_w2/user/projects/<P>/project.cfx \
    --task Retest-Task3.xml --timeframe M30
```

`Retest-Task3.xml` es la tarea de mercados adicionales del donante; lee y escribe el databank
`Retest Markets - Family`. Ejecutarla es igual que cualquier otra tarea del custodio: ver
`28-builder.md` y la skill `/template-run`.

### Aquí no se filtra nada

`crossmarket.conditions: []` en `assets/_build.yaml`, decisión del dueño del 2026-09-24. El comando
lo hace cumplir: apaga **todas** las condiciones de aceptación del crosscheck, fuerza
`DeleteFailedStrategies` a false y dice cuántas apagó.

```
  XAGUSD_DukasM1_Infinox         family      2008.01.01 a 2022.12.31
  BRENTCMDUSD_ftmo               family      2013.01.01 a 2022.12.31
1 condiciones de aceptacion apagadas — esto es evidencia, no un filtro
```

El donante traía una viva, `ReturnDDRatio > 1` sobre el primer mercado. Con una condición viva SQX
**no escribe en el databank de salida** la estrategia que no la cumple, y entonces el análisis de
Python se queda sin las muertas — que son la mitad de la evidencia: sin ellas no se puede decir qué
mercado mató a qué estrategia. SQX corre los backtests; el veredicto se toma en Python y se aplica
con `/curate`.

🤔 Con cero condiciones vivas, `<MinConditions>` y `<MinMarkets>` quedan inertes y se dejan como
estaban. En la primera corrida real, comprueba que el databank de salida tiene tantas estrategias
como el de entrada y apunta lo que veas en `knowhow/conditions/crossmarket-crosstf-no-conditions.md`.

### Cómo se lee el resultado

Y di a qué categoría pertenecía cada mercado. Pasar el test de `family` puede significar sólo que
los dos mercados son el mismo trade.

### Qué NO demuestra

Que una estrategia pase aquí no la valida: la valida el protocolo entero. Que falle no la rompe
necesariamente —puede que ese mercado tenga una microestructura distinta— pero sí obliga a
explicar por qué se conserva.
