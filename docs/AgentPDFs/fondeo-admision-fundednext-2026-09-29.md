# Admisión de FundedNext — 2026-09-29

Estado: **candidata**. Se sigue (catálogo semanal, ofertas diarias), pero no entra en el universo de
compra, ni en los avisos, ni en los estudios hasta que digas que sí. Protocolo: `/firm-onboard`.

## Las puertas

| puerta | resultado | evidencia |
|---|---|---|
| G1 EAs | 🟡 **abierta**: se permiten por debajo de 50k en MT4/MT5, **con una tarifa de uso de EA cuyo importe no publican**. De 50k en adelante, sólo manual | [help.fundednext.com — Is EA allowed](https://help.fundednext.com/en/articles/8020763-is-ea-allowed-in-fundednext), actualizado 2026-09-08 |
| G2 MT5 | ✅ | el mismo artículo |
| G3 España | 🟡 abierta: el catálogo lista restricciones por país (Vietnam, Pakistán en tamaños grandes); España no aparece, pero no está confirmado ni el método de cobro | catálogo de la web |
| G4 historial | 🟡 abierta: no revisado aún (años operando, pagos verificables, episodios de pagos denegados) | — |
| G5 reglas modelables | ✅ objetivos, pérdidas diaria y máxima, tipo de drawdown, días mínimos, reparto, ciclo de cobro y reembolso vienen en el propio catálogo | `fundednext.com`, datos de la página |
| G6 trampas para EAs | ⚠️ **prohibidas las operaciones idénticas entre cuentas** (no se puede poner la misma cartera en dos cuentas de FundedNext); cada EA debe ser «personalizado»; máximo 300.000 $ por estrategia de EA; **riesgo abierto máximo 3 % en todo momento** en fondeada; el beneficio de operaciones en noticias cuenta sólo hasta el 40 % | artículo de EAs y catálogo |

## El catálogo

**Automático**: la portada lleva el catálogo entero en los datos de la página (Next.js), con precio,
precio rebajado, código promocional y reglas por plan (`portfolio/funded/catalog/fundednext.py`).
Sólo el bloque CFD (MT5): Stellar 2-Step, 1-Step, Lite, Instant y FNL 001. El bloque de futuros
(Flex, Legacy, Rapid) no es MT5 y queda fuera.

En tu universo (≤ 10k USD, EAs): Stellar 2-Step 6k (59,99 $), 1-Step 6k (65,99 $), Lite 5k y 10k
(32,99 y 59,99 $), Instant 2k, 5k y 10k (59,99, 149,99 y 299,99 $). Hoy hay ofertas en la web:
2-Step y 1-Step de 6k con START6K (−50 % y −39 %), Instant −30 %.

## Lo que importa para el valor esperado

- **Paga durante el challenge**: un 15 % del beneficio del propio challenge (2-Step y 1-Step). Es
  dinero antes de estar fondeado; el encargo 33 tiene que modelarlo.
- Reembolso: 2-Step con el primer cobro; 1-Step y Lite al tercer cobro; Instant sin reembolso.
- Cobros: 2-Step y Lite, el primero a los 21 días y luego cada 14; 1-Step cada 5 días hábiles.
- La tarifa de EA es un coste más por cuenta, de importe desconocido.

## Preguntas para ti (o para su soporte)

1. **¿Cuánto cuesta la tarifa de uso de EA** y se paga una vez o por cuenta?
2. La regla de operaciones idénticas: ¿aceptas que en FundedNext sólo haya **una cuenta por
   cartera**?
3. ¿Revisamos G3 y G4 (España, historial de pagos) antes de decidir, o te basta con lo conocido?

**¿La doy de alta como activa?**
