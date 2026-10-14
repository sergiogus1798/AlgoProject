# Admisión de FundedNext (revisión) — 2026-10-14

Estado: **candidata**, sigue siéndolo. Sustituye a la hoja del 2026-09-29. Alcance que pediste: sólo
cuentas **por debajo de 25k**. Hoy en el catálogo: Stellar 2-Step 6k (59,99 $) y 15k (119,99 $);
1-Step 6k (65,99 $) y 15k (129,99 $); Lite 5k (32,99 $) y 10k (59,99 $); Instant 2k, 5k, 10k y 20k
(59,99 / 149,99 / 299,99 / 599,99 $). Las de 25k (2-Step 199,99 $, 1-Step 219,99 $, Lite 139,99 $)
quedan fuera por ser «25k no es menos de 25k»: ver pregunta 3.

## Las puertas

| puerta | resultado | evidencia |
|---|---|---|
| G1 EAs | 🟡 **abierta**: EAs permitidos por debajo de 50k en MT4/MT5, con «tarifa de uso de EA» **de importe no publicado** (releído hoy: sigue sin cifra) | [artículo de EAs](https://help.fundednext.com/en/articles/8020763-is-ea-allowed-in-fundednext), actualizado 2026-09-08 |
| G2 MT5 | ✅ | mismo artículo; servidores `FundedNext-Server` y `-Server 2` ([login MT5](https://help.fundednext.com/en/articles/10725745-how-do-i-log-in-to-the-mt5-platform-pc)) |
| G3 España | 🟡 **medio cerrada**: España **no** está en la lista de países restringidos de CFD ([lista oficial](https://help.fundednext.com/en/articles/8020080-are-any-countries-restricted-on-fundednext-cfds)). Falta confirmar que el cobro llega a España (cripto, transferencia bancaria; Wise no aparece) | [métodos de retirada](https://help.fundednext.com/en/articles/11641804-how-can-i-withdraw-my-performance-reward) |
| G4 historial | 🟡 abierta, sin juzgar. A favor: fundada en 2022; la web declara 306,9 M$+ pagados y «99,99 % en 24 h» (cifra de la propia web, no verificada). En contra (terceros, anecdóticos): quejas de pagos recortados por «HFT», una por «15 tick scalp», una por «gambling», y un reembolso en cripto aprobado y rechazado después | [portada](https://fundednext.com/); [payout denials](https://thetrustedprop.com/prop-firms/funded-next/payout-denials) |
| G5 reglas modelables | ✅ salvo un punto: la **referencia de la pérdida diaria** (balance o equity) no la dice el artículo; reinicio a las 00:00 del servidor | [reinicio](https://help.fundednext.com/en/articles/8394309-when-does-the-daily-loss-limit-reset-with-fundednext-cfd) |
| G6 trampas | listadas abajo | |

## Trampas para EAs (no se juzgan)

- **Operaciones idénticas entre cuentas prohibidas**: una cartera por cuenta.
- EAs «personalizados»; sin EAs de superar retos (Prop Pilot, PropEA...); herramientas que sólo tocan SL/TP/lote cuentan como EA.
- Tope agregado de **300.000 $** por trader; sin límite de número de cuentas. No afecta a < 25k.
- **HFT y tick scalping prohibidos** (el scalping normal, no). Sin umbral numérico publicado: riesgo para estrategias M15 de muchas operaciones.
- Riesgo abierto máximo 3 % en fondeada; noticias ±5 min: sólo cuenta el 40 % del beneficio.
- Fin de semana y noche permitidos. Inactividad: 30 días naturales.

## El catálogo

Automático (datos inline de la portada, `portfolio/funded/catalog/fundednext.py`), refrescado hoy sin
cambios de precio. Fiable mientras la portada conserve el objeto Next.js. Ofertas: precio rebajado
en el propio catálogo.

## Lo que importa para el valor esperado

- Paga **15 % del beneficio del challenge** (2-Step y 1-Step) antes de estar fondeado.
- Reembolso: 2-Step al 1.er cobro; 1-Step y Lite al 3.º; Instant sin reembolso.
- Reparto: 80 % (1-Step, compras desde 2026-01-12), 70 % Instant (tramos 1-2).
- La tarifa de EA es un coste por cuenta aún sin cifra.
- MT5 para el paso 26: comisión 5 $ por lote y lado en forex, 0,0016 % en metales; servidor GMT+2/+3;
  existe cuenta de prueba gratis en `FundedNext-Server 3` (su feed puede diferir; sin confirmar).

## Preguntas para ti o su soporte

| código | qué se decide | A / B | recomendación |
|---|---|---|---|
| FN-1 | importe y periodicidad de la tarifa de EA | A: preguntar a soporte; B: verlo en la página de compra con una cuenta | A, por escrito |
| FN-2 | ¿«EA hecho con SQX» es el EA «personalizado» que piden? | A: preguntar a soporte; B: asumirlo | A |
| FN-3 | «menos de 25k»: ¿incluye 25k? | A: no (como arriba); B: sí | A |
| FN-4 | una cartera por cuenta | A: aceptar; B: descartar la firma | A |
| FN-5 | el cobro a España | A: confirmar con soporte; B: aceptar cripto | A |

**¿La doy de alta como activa?**
