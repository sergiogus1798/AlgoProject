# Medición del stop lejano (2026-10-11)

## 0. Conclusión

El criterio escrito **antes de mirar** dice **NO PASA**: el stop a 2·X toca el **11,55 %** de las operaciones (intervalo de Wilson 95 %: 11,09 %–12,03 %) y el límite era 1 %. Por el texto del propio criterio, **no hay stop por operación**: el riesgo se controla en la cuenta (`portfolio/`). El p90 sale en todos los casos.

## 1. El criterio, tal cual, y que se escribió antes

Está en `portfolio/DECISIONS.md` (entrada del 2026-10-11), escrito antes de que `breach.py` leyera un solo MAE:

> El p90 sale en todos los casos. Con k = 2 fijado antes de mirar: si el stop 2·X toca menos del 1 % de las operaciones —todas las madres y `build`+`oos1` juntos, cota superior del intervalo de Wilson al 95 %— se injerta antes del 16.5 con X fijo; si no, ningún stop por operación y el riesgo se controla en la cuenta (`portfolio/`). `oos2` no se lee. k = 1,5 y las tasas de ruptura se informan, no deciden.

## 2. Qué se midió

- 7 proyectos, 56 madres, tramos `build` + `oos1`: **17.718 operaciones**. `oos2` no se abrió.
- X es el percentil 90 del MAE/ATR(20) de las ganadoras de `build` de cada madre (lo que ya lee el paso 24). Una operación «toca» a k cuando su MAE llega a k·X·ATR.
- El stop lejano **se deriva del MAE de cada operación**; no se reteste en SQX.

## 3. La tabla que decide

Un **intervalo de Wilson** es el margen de error de una proporción: dice entre qué dos valores cae, con un 95 % de confianza, la tasa real de toques dado cuántas operaciones se miraron. Se decide con su cota superior, no con la tasa suelta.

| k | tocadas | tasa | Wilson 95 % | papel |
|---|---|---|---|---|
| 1 | 5.840 de 17.718 | 32,96 % | 32,27 %–33,66 % | informa |
| 1,5 | 3.323 de 17.718 | 18,75 % | 18,19 %–19,34 % | informa |
| **2** | **2.046 de 17.718** | **11,55 %** | **11,09 %–12,03 %** | **decide (límite 1 %)** |

Por tramo, a k = 2: `build` 9,27 % (1.026 de 11.066) y `oos1` 15,33 % (1.020 de 6.652): fuera de la muestra toca más. Por proyecto, a k = 2: 9,7 % (USA500 H1) a 12,2 % (NIKKEI225 M30 `auto` y `fin`). Por madre (build+oos1 sumados): de **6,2 % a 16,7 %**; **ninguna madre baja de 6,2 %**. Con salidas por número de barras no existe un múltiplo «de catástrofe» del p90 que casi nunca se active.

## 4. Calibración: ¿se puede fiar de la derivación?

A k = 1 la derivación se compara con el p90 que SQX retestea de verdad: porcentaje de operaciones paradas **33,0 % derivado frente a 32,7 % real** (todos los proyectos juntos). Para **tasas de toque es fiable**. Para **dinero no**: el neto derivado es 2.183.070 frente a 2.058.370 real, porque la derivación no ve las entradas que SQX toma tras un cierre adelantado, ni los rellenos más allá del nivel (huecos, deslizamiento), ni los costes de la operación parada. Las cifras de dinero derivadas son un suelo del daño, no una estimación.

## 5. La cuenta (informa, no decide)

Cada proyecto como una sola cuenta, al tamaño exportado, 100.000 arranques simulados. «Ruptura» = el arranque toca un límite de la prueba (diario o total) sobre el flotante antes de llegar al objetivo.

| proyecto | sin stop | p90 real (SQX) | derivado 2·X |
|---|---|---|---|
| NIKKEI225 M30 simpleL `auto` | 70,2 % | 67,5 % | 70,3 % |
| NIKKEI225 M30 simpleL `fin` | 69,1 % | 66,9 % | 69,2 % |
| NIKKEI225 M30 simpleL `live` | 70,7 % | 70,7 % | 70,8 % |
| NIKKEI225 M30 simpleL `ref` | 69,7 % | 67,7 % | 69,7 % |
| USA500 H1 indicesIBS | 76,5 % | 52,9 % | 68,0 % |
| USDJPY M30 doubleROCLong | 49,8 % | 38,1 % | 31,2 % |
| NIKKEI225 M30 volatilidadL | 55,2 % | 30,3 % | 45,0 % |

Lectura honesta: al tamaño exportado **entre la mitad y las tres cuartas partes de las cuentas rompen un límite con o sin stop** (sin stop: 49,8 %–76,5 %). Eso mide el **tamaño de la posición**, no el stop. Es lo siguiente que hay que trabajar: el riesgo a nivel de cuenta en `portfolio/`.

## 6. Salvedades

- Las madres hermanas comparten operaciones, así que el intervalo verdadero es **más ancho** que el de Wilson (que supone operaciones independientes).
- Un 11,5 % no se rescata contra un 1 %: ni ensanchando el intervalo se acerca.
- No se probó nada en cortos.
- El día se corta en la medianoche del feed.
- La comisión no se flota.

## 7. Qué decide y qué queda pendiente

**Decide:** no hay stop por operación; el p90 sale; el riesgo se controla en la cuenta.

**Ganancia:** lo que opera es lo que validó la cadena. Según el dossier anterior (`criterios-implementados-2026-10-12`), el p90 injertado al final se activa en 23–41 % de las operaciones y cuesta ~32 % del neto de `oos1`; quitarlo devuelve ese ~+32 %.

**Coste:** sin stop en el broker, si el EA o el VPS caen con una posición abierta, nada la protege. Es el único argumento a favor de un stop que esta medición no puede responder.

**Pendiente:** ejecutar la retirada del paso 24 (OPEN.md #113 c) espera la palabra del dueño.
