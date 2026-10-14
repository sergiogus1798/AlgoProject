# Admisión de FundingPips (revisión) — 2026-10-14

Estado: **candidata**, sigue siéndolo. Sustituye a la hoja del 2026-09-29. Aviso de método: su web y su
centro de ayuda siguen bloqueando el acceso automático (403 / 429) y **no se fuerza**. Lo de abajo sale
de los fragmentos que el buscador devuelve de las páginas del propio centro de ayuda (con su URL), no de
una lectura directa: todo queda `unconfirmed` hasta que tú lo leas en su web.

## Las puertas

| puerta | resultado | evidencia |
|---|---|---|
| G1 EAs | 🟡 **abierta, ya no «probablemente en contra»**: los EAs de terceros sólo como gestores de operaciones o riesgo; **pero un EA «desarrollado por ti» puede ir en automático completo con prueba de autoría** (código fuente .mq5 sin compilar, historial de versiones, registros de compilación o explicación de la lógica en una llamada). Concurso mensual: ningún EA. **No dice si un EA generado con StrategyQuant X es «tuyo»**, ni si el código exportado vale como prueba | [Trading Conduct and Security Standards](https://help.fundingpips.com/hc/en-us/articles/34505029138449-Trading-Conduct-and-Security-Standards) |
| G2 MT5 | ✅ probable: planes en MT5, hora de plataforma UTC+3; falta confirmar el nombre del servidor | [2-Step Standard](https://help.fundingpips.com/hc/en-us/articles/34501809112081-2-Step-Standard) |
| G3 España | ✅ probable: no está entre los países vetados (Irán, Vietnam, EAU, listas de sanciones); España figura como compatible para cobro por tarjeta y transferencia. Otros métodos: cripto, Rise (mínimo 500 $) | [Reward Methods](https://help.fundingpips.com/hc/en-us/articles/34504564970385-Reward-Methods) |
| G4 historial | 🟡 abierta, sin juzgar. Fundada en 2022; dicen ~180-200 M$ pagados; Trustpilot 4,5/5 con 32k reseñas (cifras de terceros y de ellos mismos). En contra: hilo de ForexPeaceArmy con un pago de 1.700 $ denegado y cuenta cerrada tras uno de 800 $ pagado; anécdotas de pagos denegados | [fxempire](https://fxempire.com/prop-firms/fundingpips); [payout denials](https://thetrustedprop.com/prop-firms/funding-pips/payout-denials) |
| G5 reglas modelables | 🟡 parcial: objetivos y pérdidas de la ficha manual (de terceros); pérdida diaria = **mayor de balance o equity al inicio del día**, con flotante, reinicio 00:00 UTC+3 | artículos 2-Step Standard y Zero |
| G6 trampas | ver abajo | |

## Trampas para EAs (no se juzgan)

- **Prueba de autoría** del EA (puede exigir una llamada con su equipo): riesgo operativo para código generado.
- Sin EAs en concurso; en 1K Instant se permiten EAs de terceros.
- Cierre automático de posiciones en ventanas 20:45-21:00 UTC (verano) / 21:45-22:00 (invierno): hay que leer si cierra el viernes o a diario.
- Inactividad: una operación abierta no reinicia el contador; plazo no visto.
- Operaciones idénticas, noticias, asignación máxima: no vistos, hay que leer el artículo de conducta.

## El catálogo

**Manual** (`AlgoData/funding/manual/fundingpips.yaml`), todo sin confirmar. Precios de lista en tu
universo ≤ 10k: 2-Step Standard 5k 36 $ y 10k 66 $; 2-Step Pro 29 $ y 55 $; 1-Step 59 $ y 99 $; Zero
69 $ y 99 $. Ya los tecleó la sesión del 2026-09-29 a partir de terceros; **compruébalos en su web**.
La columna `eas_allowed` queda vacía a propósito (no hay respuesta firme).

## Lo que importa para el valor esperado

- Reparto en 2-Step Standard y 1-Step según frecuencia de cobro (60 % semanal a 100 % mensual); reembolso
  tras el 4.º cobro (sin confirmar). Zero 80-95 % según fuente.

## Preguntas para ti o su soporte

| código | qué se decide | A / B | recomendación |
|---|---|---|---|
| FP-1 | ¿un EA generado con SQX cuenta como «desarrollado por ti» y qué prueba de autoría aceptan? | A: preguntar a soporte por escrito; B: asumir que sí | A, antes de comprar nada |
| FP-2 | ¿Aceptas la llamada con su equipo para explicar la lógica si el código no basta? | A: sí; B: no (se descarta la firma) | A |
| FP-3 | comprobar precios y reglas de la ficha manual (8 cifras) | A: tú; B: yo con tu confirmación | A |
| FP-4 | ¿alcanza el historial de pagos (G4)? | A: sí con lo conocido; B: revisarlo más | B si lo piden |

**¿La doy de alta como activa?**
