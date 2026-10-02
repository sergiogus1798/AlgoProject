# Repos externos: qué hay en abierto que cubra o complemente nuestra investigación

**Fecha:** 2026-10-02. **Pedido por el dueño:** una búsqueda exhaustiva de repositorios que cubran
nuestras necesidades de investigación o las complementen.

**Cómo se hizo.** Cinco buscadores en paralelo, uno por área, unos 170 repos. De cada uno se
comprobó contra GitHub, el mismo día, que existe, su licencia, sus estrellas y su último push. Lo
que hace cada uno sale de su README o de su descripción: **no se ha ejecutado ninguno**. La API de
búsqueda de GitHub limitó a tres de los buscadores, así que puede faltar algún repo pequeño de 2026.

**Conclusión.** Ninguno sustituye nada de lo nuestro. Lo aprovechable son piezas sueltas: unas
pocas se pueden adoptar ya, y el resto son patrones de diseño para el bucle de investigación o
material para fases posteriores. En varias piezas (nulos de entrada aleatoria, embudo IS→OOS,
herramientas de SQX) no hay nada publicado comparable a lo que ya tenemos.

Coste: S = una sesión corta · M = una o dos sesiones largas.

---

## 0. Lo que ya teníamos y la búsqueda recomendó igualmente

Dos recomendaciones de la búsqueda resultaron estar ya hechas. Se dejan escritas para que nadie
las repita.

| lo recomendado | por qué no hace falta |
|---|---|
| Longitud de bloque automática (Politis-White) con `arch` para la nula del perfil de mercado | Medido el 2026-10-01 con `marketProfile/blocklen.py`: un bloque de 1 barra es la única nula con el tamaño correcto; un bloque más largo solo pierde potencia. La cifra de Politis-White (240-750 barras) mide la memoria de la volatilidad, no la de la dirección. Tarjeta: `knowhow/research/market-profile-block-length.md`. |
| `arch` como referencia para validar nuestro SPA y StepM | `engines/inference/snooping/` ya está escrito sobre el `SPA` de `arch`, con test de respuesta conocida (`tests/test_snooping.py`). |
| Permutación de barras de Masters ([neurotrader888/mcpt](https://github.com/neurotrader888/mcpt)) como nulo nuevo | Con bloque de 1 barra nuestro remuestreo ya rompe el orden temporal conservando la forma de las barras. La diferencia es remuestrear con o sin reposición: aporta poco. |

El origen del error: el §11 del dossier `director-de-investigacion-2026-10-01` seguía diciendo que
la longitud de bloque «no está elegida». Queda anotado allí.

---

## 1. Adoptar: tapa un hueco real

| repo | qué nos da | coste | aviso |
|---|---|---|---|
| [sushiix-trader/mql5-news-filter](https://github.com/sushiix-trader/mql5-news-filter) (Apache-2.0) | Filtro de noticias que funciona **dentro del tester de MT5** reproduciendo un CSV. Hoy el skill `ea-news` reconoce que el calendario no existe en el tester, así que el EA con filtro no se puede verificar en backtest. | S-M | 3 estrellas: auditar el código y el huso del CSV contra el reloj EET |
| [janickfarrell/newfac](https://github.com/janickfarrell/newfac) (MIT) y [ehsanrs2/forexfactory-scraper](https://github.com/ehsanrs2/forexfactory-scraper) (GPL) | Calendario de ForexFactory desde 2007 con impacto: el histórico de noticias de alto impacto para las reglas de las firmas. Dos fuentes para cruzar. | S | 0 estrellas el primero; no se comprobó que el CSV publicado exista |
| [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) (Apache-2.0), [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) (MIT), [J535D165/pyalex](https://github.com/J535D165/pyalex) (MIT) | Búsqueda de papers para el `ideaExpert` y para ampliar el fichero de 62 edges. Sustituye a portar el buscador de Vibe-Trading. | S | Solo arXiv el primero; la cobertura de SSRN del segundo no está comprobada |
| [tschm/jsharpe](https://github.com/tschm/jsharpe) (MIT) | Versión empaquetada y testeada del marco PSR / DSR / número de ensayos de López de Prado, para contrastar `core/significance.py` y `core/surface/`. Añade FDR y FWER sobre Sharpe. | S | Pequeño y joven. El código de los autores ([zoonek/2025-sharpe-ratio](https://github.com/zoonek/2025-sharpe-ratio)) no tiene licencia: solo leer |
| [eguidotti/bidask](https://github.com/eguidotti/bidask) (MIT) | Estimador publicado (JFE 2024) del spread a partir de OHLC. Sería un quinto modelo candidato en `studies/data/spread/model.py`, que ya elige por error fuera de muestra. | S | Ruidoso en ventanas intradía cortas; puede que no gane a los cuatro que hay |

---

## 2. Para el bucle de investigación: se copian patrones, no código

| repo | la pieza | lo que ya tenemos |
|---|---|---|
| [hch-wang/Negative_Knowledge](https://github.com/hch-wang/Negative_Knowledge) (MIT) | Esquema tipado del fracaso: qué capa falló, alcance, qué probar en su lugar. Y la obligación de que quien propone adopte o rechace cada registro previo antes de proponer. | `studies/research/memory/` guarda dónde murió una corrida (`died@<etapa>`), no por qué ni qué descarta |
| [Kaimen-Inc/Co-Scientist](https://github.com/Kaimen-Inc/Co-Scientist) (Apache-2.0) | Prompts ya escritos de revisor (novedad, corrección, testabilidad) y de deduplicado por proximidad. Es un crítico adversario para las tres ideas, antes de gastar CPU. | No hay un agente distinto del que genera que revise la idea |
| [Kryhr/26-quant-trading-skills](https://github.com/Kryhr/26-quant-trading-skills) (MIT) | Que la frecuencia de operaciones predicha por la idea se compare con la que el build produce de verdad, y que un desajuste cuente como señal de fallo. | El `ideaExpert` ya escribe mecanismo y frecuencia esperada; no se comprobó que nadie la contraste después |
| [SakanaAI/ShinkaEvolve](https://github.com/SakanaAI/ShinkaEvolve) (Apache-2.0) | Rechazo por novedad contra todo lo ya probado, y un resumen periódico de qué tipo de ideas sobreviven que vuelve al prompt del que propone. | El `ideaExpert` lee lo probado a mano; no hay medida de parecido |
| [ALAGENT-HKU/x2strategy](https://github.com/ALAGENT-HKU/x2strategy) | Esquema «paper → especificación de estrategia». | El fichero de edges se hizo a mano. Licencia dudosa: solo leer |
| [vincent212/llm-assisted-trading-strategy-search](https://github.com/vincent212/llm-assisted-trading-strategy-search) | Una regla de diseño: el LLM nunca ve precios ni elige un número. Nuestro `ideaExpert` sí mira el tramo `build`. | Es una decisión de diseño que conviene tomar a conciencia, no un fallo |

Ninguna de estas piezas está demostrada: no hay prueba de que suban la tasa de supervivientes.
Cada una añade tokens por propuesta (hoy 10-30 $), sin medir cuántos.

---

## 3. Canteras de ideas

| repo | qué contiene | cómo se usa | aviso |
|---|---|---|---|
| [rolling-panda-san/notebooks](https://github.com/rolling-panda-san/notebooks) (MIT) | Unos 28 papers replicados, uno por notebook: tendencia, ruptura, reversión de Connors, momentum de materias primas | Lo más parecido a nuestro fichero «edge → regla medible» | Futuros diarios; los de carry y curva no valen para CFD, los intradía usan reloj |
| [pst-group/pysystemtrade](https://github.com/pst-group/pysystemtrade) (GPL-3) | Las reglas de Carver: EWMAC, breakout, aceleración, reversión | Definiciones limpias de un solo instrumento | Previsiones continuas, no entradas binarias; leer, no copiar |
| [StockSharp/AlgoTrading](https://github.com/StockSharp/AlgoTrading) | 3.811 estrategias cortas clasificadas por familia (rupturas 319, reversión 299, tendencia 264, momentum 206…) | La mayor mina de condiciones de entrada | Licencia propia y calidad mixta: solo como ideas |
| [octopus444/technical-trading-rules-based-strategies-btc](https://github.com/octopus444/technical-trading-rules-based-strategies-btc) | La única rejilla pública al estilo Sullivan-Timmermann-White: 3.669 reglas | Transcribir la rejilla como barrido del perfil | 0 estrellas, sin licencia; su propio resultado es que nada sobrevive |
| [TA-Lib/ta-lib](https://github.com/TA-Lib/ta-lib) (BSD) y [xgboosted/pandas-ta-classic](https://github.com/xgboosted/pandas-ta-classic) (MIT) | Dos fuentes independientes de fórmulas de indicadores y velas | Contrastar bloques de SQX | — |

---

## 4. Útiles, pero para fases posteriores

| área | repo | para qué |
|---|---|---|
| Umbrales (encargo 41, puntos 1.6-1.9) | [OliverHennhoefer/online-fdr](https://github.com/OliverHennhoefer/online-fdr) (BSD) | FDR secuencial entre corridas a lo largo del tiempo, que el Benjamini-Hochberg por lote no controla |
| | [braverock/quantstrat](https://github.com/braverock/quantstrat) | El haircut y el listón de beneficio de Harvey-Liu; está en R, habría que portarlo |
| | [chenandrewy/high-throughput-ap](https://github.com/chenandrewy/high-throughput-ap) (CC0), [stephens999/ashr](https://github.com/stephens999/ashr) | Contracción bayesiana de una población entera para predecir el OOS: da un orden, no un pasa/no pasa |
| Carteras (`portfolio/PLAN.md`) | [skfolio/skfolio](https://github.com/skfolio/skfolio), [dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) (BSD ambos) | HRP, HERC y medidas de riesgo por drawdown, que es lo que castigan las firmas |
| Fondeo | [LuxAlgo/prop-firm-sim](https://github.com/LuxAlgo/prop-firm-sim) (MIT) | Reglas por firma y probabilidad de pasar, para contrastar nuestro Monte Carlo. No se comprobó si acepta listas de operaciones reales |
| Regímenes | [Yizhan-Oliver-Shu/jump-models](https://github.com/Yizhan-Oliver-Shu/jump-models) (Apache-2.0) | Regímenes con penalización de persistencia, más estables que un HMM |
| Gemelos de nuestro stack | [DAVIDAROCA27/sqx-mcp](https://github.com/DAVIDAROCA27/sqx-mcp), [masdevid/mt5-quant](https://github.com/masdevid/mt5-quant) (MIT ambos) | Comparar sus parsers de `.sqx`/`.cfx` y de informes del tester con los nuestros |
| Datos | [Leo4815162342/dukascopy-node](https://github.com/Leo4815162342/dukascopy-node) (MIT) | Segunda fuente de ticks para auditar barras; sus spreads no son los de las firmas |

---

## 5. Descartado

- **Motores de backtest en Python** (vectorbt, NautilusTrader, backtesting.py, backtrader…):
  ninguno modela a la vez swap, spread por tramo y resolución intrabarra compatible con SQX.
  Seguimos con el nuestro.
- **Agentes «el LLM opera»** (TradingAgents, ai-hedge-fund, FinRobot, FinMem…): el LLM decide cada
  operación y no produce una regla.
- **Minería de alphas** (RD-Agent, Qlib, AlphaGen, QuantaAlpha): factores cross-sectional de renta
  variable diaria, no expresables como bloques de SQX.
- **Capas de memoria genéricas** (mem0, letta, graphiti) y **generadores GAN o de difusión** de
  series: demasiado para lo que necesitamos.
- **mlfinlab:** ya es propietario.
- **Bases académicas de anomalías** (Open Source Asset Pricing, JKP): cross-sectional.

## 6. Lo que no existe en abierto

- Herramientas serias para StrategyQuant: el repo oficial solo contiene un fichero de licencia.
- Librerías de entrada aleatoria («monos») con el perfil de salida de la estrategia.
- Análisis de supervivencia del embudo de una población IS→OOS.
- Analítica de MAE/MFE por operación.
- El universo exacto de 7.846 reglas de Sullivan-Timmermann-White, ni los de Qi-Wu o Hsu-Kuan.
- Un equivalente de Open Source Asset Pricing para reglas de un solo activo.
- Modelo de spread desde ticks, histórico de swaps, verificador de alineación EET/DST.

## 7. Avisos

- **Licencias.** `pypbo`, `fathon`, `pycatch22`, `backtesting.py` y `pysystemtrade` son GPL o
  AGPL: valen como oráculo para comparar salidas, no para copiar código. Los repos sin licencia
  son solo para leer.
- **Cebo.** `PropGuard-Trailing-Equity-Armor`, `PropFirm-Tracker-Elite` y `mt5-quiet-automata`
  muestran unas 120 estrellas, push del día y descripciones de anuncio: parecen granjas de
  estrellas. No descargar.
- **Repos de 0-3 estrellas.** Varios de los recomendados lo son (noticias, Negative_Knowledge,
  Kryhr). Se recomiendan por la idea o por el hueco que tapan, y se auditan antes de usarlos.

## 8. Orden propuesto

1. El filtro de noticias en el tester y el histórico del calendario: tapan un hueco que el propio
   skill `ea-news` reconoce, y tocan el fondeo, que es la prioridad.
2. El MCP de arXiv para el `ideaExpert`.
3. `jsharpe` como test de respuesta conocida del DSR y del número de ensayos.
4. El bloque 2 entero, después de la fase 1 del encargo 41 y de una en una, midiendo si cambia
   algo.
