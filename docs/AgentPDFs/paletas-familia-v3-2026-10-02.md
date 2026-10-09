# Paletas de familia v3 — 2026-10-02

Tu orden: «¿Cómo que solo 6-13 bloques? … yo esperaba al menos 90/100 hasta 150. Rehazlas con los nuevos conocimientos». Hechas: cinco paletas nuevas en `sqx/blocks/palettes/`, de 110 a 125 bloques cada una. Las antiguas (`*_base`, `*_v2`) no se han tocado y **ninguna v3 está aplicada a ningún proyecto**.

## Resumen

| paleta | bloques encendidos | condiciones | valores y comparadores | peso 3 | peso 2 | peso 1 |
|---|---|---|---|---|---|---|
| `ruptura_base_v3` | 112 | 99 | 13 | 27 | 48 | 37 |
| `reversion_base_v3` | 123 | 113 | 10 | 64 | 25 | 34 |
| `tendencia_base_v3` | 125 | 111 | 14 | 62 | 23 | 40 |
| `momentum_base_v3` | 110 | 102 | 8 | 64 | 18 | 28 |
| `volatilidad_base_v3` | 120 | 113 | 7 | 30 | 44 | 46 |

**Cómo leer los pesos.** Peso 3: las señales propias de la familia, todas las razonables (no una por clase). Peso 2: su contexto o régimen. Peso 1: lo ortogonal — lo que tiene sentido como segunda condición y como salida — siguiendo las dos reglas del director (ortogonalidad; tendencia con contratendencia; nunca el mismo dato dos veces).

**Lo que garantiza el test** (`tests/test_palettes_families.py`): cada v3 tiene entre 90 y 150 bloques contados sobre lo que el builder recibe de verdad; ningún bloque de reloj o calendario; ningún precio de sesión, del día, de la semana ni VWAP anclado; ningún nivel stop/limit; y **ningún bloque es peso 3 en dos familias** (la etiqueta de familia significa algo).

**Tres cosas que debes saber antes de usarlas:**

1. **«Pullback» tiene paleta propia, `pullback_base_v3`: 135 bloques (127 condiciones), dentro de banda.** La unión cruda de tendencia v3 + reversión v3 daba 199. Su peso 3 son dos conjuntos disjuntos: 40 bloques de contexto de tendencia (solo estados, sin cruces) y 56 de disparo de reversión; una estrategia cuenta como pullback si su entrada lleva uno de cada.
2. **No existe en el catálogo un bloque de contexto D1 sin reloj.** CloseD/HighD/LowD y compañía dependen del corte del día y se han quedado fuera, como pediste para los niveles de sesión. El filtro D1 que el perfil dio por útil hay que ponerlo con un segundo gráfico en el build, no desde la paleta.
3. **Los valores de doble papel** (Close, Highest, Keltner, medias… en ruptura y tendencia) encienden también su gemelo stop/limit hasta que entre el arreglo de `buildingblocks.rewrite` que está haciendo otro agente. Reversión, momentum y volatilidad no llevan ninguno.

## Ruptura — `ruptura_base_v3`

| clase de información | bloques | peso |
|---|---|---|
| Ruptura del rango de N barras (Donchian, Highest/Lowest, nube de Ichimoku) | CBlock_BreakoutDonchianLong, CBlock_BreakoutDonchianLong_2, BarOpensAboveHighestAfterOpenBelow, BarOpensBelowLowestAfterOpenAbove, IchimokuKumoBreakoutBullish, IchimokuKumoBreakoutBearish | 3 |
| Ruptura de la envolvente de Bollinger (cruce, apertura y cierre fuera de banda) | CBlock_BBBreakoutUp, CBlock_BBBreakoutDown, BBBarOpensAboveUpAfterOpenBelow, BBBarOpensBelowDownAfterOpenAbove, BBBarClosesAboveUp, BBBarClosesBelowDown, BBBarOpensAboveUp, BBBarOpensBelowDown | 3 |
| Ruptura del canal de Keltner (canal de ATR) | KCBarOpensAboveUpperAfterOpenBelow, KCBarOpensBelowLowerAfterOpenAbove, KCBarClosesAboveUpper, KCBarClosesBelowLower, KCBarOpensAboveUpper, KCBarOpensBelowLower | 3 |
| Vela de expansión (cuerpo > k·ATR; cuerpo > 80 % del rango, solo alcista) | CBlock_CandleBreakoutLong, CBlock_CandleBreakoutLong_2, CBlock_StrongCandle | 3 |
| Salida de una compresión con dirección (TTM Squeeze con momentum) | TTMSqueezeMomentumCrossLevelUP, TTMSqueezeMomentumCrossLevelDown, TTMSqueezeMomentumIsRising, TTMSqueezeMomentumIsFalling | 3 |
| Contexto: compresión previa y liberación | CBlock_SqueezeOn, CBlock_SqueezeOff, CBlock_BBWRPercent | 2 |
| Contexto: nivel de volatilidad contra su propia historia | CBlock_ATRRankHighVol, CBlock_ATRRankLowVol, ATRPercentRankAboveLevel, ATRPercentRankBelowLevel, ATRPercentRankCrossUP, ATRPercentRankCrossDown, ATRPercentAboveLevel, ATRPercentBelowLevel, ATRPercentCrossUP, ATRPercentCrossDown | 2 |
| Contexto: la volatilidad sube o baja | ATRRising, ATRFalling, ATRChangesUp, ATRChangesDown, ATRPercentRankRising, ATRPercentRankFalling, StdDevRising, StdDevFalling, StdDevChangesUp, StdDevChangesDown, CBlock_ATRCrossMAATR | 2 |
| Contexto: las bandas se abren o se cierran | BBUpperRising, BBUpperFalling, BBLowerRising, BBLowerFalling, KCUpperRising, KCUpperFalling, KCLowerRising, KCLowerFalling | 2 |
| Contexto: cambio de distribución y calma previa | CBlock_KSBreakOn, CBlock_KSBreakOff, CBlock_WassersteinShiftHigh, CBlock_WassersteinShiftLow, CBlock_WAEPosAboveExplosion_2_2_3, CBlock_WAEPosAboveExplosion_2_2_3_2 | 2 |
| Contexto: empieza a haber tendencia (ADX, eficiencia) | ADXRising, ADXCrossUp, ADXHigher, KERaboveLevel | 2 |
| Segunda condición contraria y salida por agotamiento (reversión) | RSILower, RSIHigher, StochSlowDLower, StochSlowDHigher, CCILower, CCIHigher, WPRLower, WPRHigher, CBlock_ZScoreStretchedDown, CBlock_ZScoreStretchedUp, CBlock_IBSCloseLarger, CBlock_IBSCloseLarger_2 | 1 |
| Salida: la ruptura falla (reentrada en la banda o en el canal) | BBBarOpensAboveDownAfterOpenBelow, BBBarOpensBelowUpAfterOpenAbove, KCBarOpensAboveLowerAfterOpenBelow, KCBarOpensBelowUpperAfterOpenAbove, BarOpensAboveLowestAfterOpenBelow, BarOpensBelowHighestAfterOpenAbove | 1 |
| Salida: pierde la media o el trailing | MABarClosesAbove, MABarClosesBelow, BarClosesAboveSuperTrend, BarClosesBelowSuperTrend, CBlock_PMaxFlipUp, CBlock_PMaxFlipDown, PSARBarHigher, PSARBarLower | 1 |
| Velas (un puñado) | BullishEngulfing, BearishEngulfing, CBlock_CandleSmallUpperWick, CBlock_CandleSmallUpperWick_2 | 1 |
| Valores: canales y bandas para comparar con el precio | Highest, Lowest, DonchianChannels, KeltnerChannel, BollingerBands, HullMovingAverageATRBands | 2 |
| Valores: precio | Close, High, Low | 1 |
| Comparadores | IsGreater, IsLower, CrossesAbove, CrossesBelow | 1 |

## Reversión a la media — `reversion_base_v3`

| clase de información | bloques | peso |
|---|---|---|
| Oscilador acotado en extremo (RSI, Estocástico, CCI, %R, DeMarker, DVO, Laguerre, QQE, WaveTrend, Schaff, Ergodic) | RSILower, RSIHigher, RSICrossUp, RSICrossDown, StochSlowDLower, StochSlowDHigher, StochSlowDCrossUp, StochSlowDCrossDown, StochFastKCrossUp, StochFastKCrossDown, CCILower, CCIHigher, CCICrossUp, CCICrossDown, WPRLower, WPRHigher, WPRCrossUp, WPRCrossDown, DEMLower, DEMHigher, DEMCrossUp, DEMCrossDown, DVOBelowLevel, DVOAboveLevel, DVOCrossAboveLevel, DVOCrossBelowLevel, LaguerreRSICrossUP, LaguerreRSICrossDown, QQEValue1Lower, QQEValue1Higher, QQEValue1CrossAbove, QQEValue1CrossBelow, WaveTrendMainLower, WaveTrendMainHigher, WaveTrendMainCrossAbove, WaveTrendMainCrossBelow, SchaffTrendCycleBelowLevel, SchaffTrendCycleAboveLevel, BHErgodicBelowLevel, BHErgodicAboveLevel | 3 |
| Estiramiento respecto de la media (ZScore, CMMA, Disparity) | CBlock_ZScoreStretchedDown, CBlock_ZScoreStretchedUp, CBlock_CMMAIsAboveLevel, CBlock_CMMAIsAboveLevel_2, CBlock_CMMAIsAboveLevel_3, CBlock_CMMAIsAboveLevel_3_2, DisparityIndexBelowLevel, DisparityIndexAboveLevel, DisparityIndexCrossesAboveLevel, DisparityIndexCrossesBelowLevel | 3 |
| Posición del cierre y de la apertura dentro de la barra (IBS) | CBlock_IBSCloseLarger, CBlock_IBSCloseLarger_2, CBlock_IBSCloseLarger_3, CBlock_IBSCloseLarger_4 | 3 |
| Reentrada en la banda o en el canal: la ruptura falló | BBBarOpensAboveDownAfterOpenBelow, BBBarOpensBelowUpAfterOpenAbove, KCBarOpensAboveLowerAfterOpenBelow, KCBarOpensBelowUpperAfterOpenAbove, BarOpensAboveLowestAfterOpenBelow, BarOpensBelowHighestAfterOpenAbove | 3 |
| Giro desde el extremo (cruce de la señal estando en zona) | CBlock_StochWeightsUp, CBlock_StochWeightsDown, CBlock_SmoothedRSIRising_3_3, CBlock_SmoothedRSIRising_3_3_2 | 3 |
| Contexto: régimen sin tendencia (ADX bajo, choppiness, Hurst < 0,5, entropía, CSSA alto, SuperTrend plano) | ADXLower, ADXFalling, ADXCrossDown, ADXChangesDown, CBlock_ChoppinessChoppy, ChoppinessIndexAboveLevel, ChoppinessIndexCrossesAboveLevel, ChoppinessIndexRising, CBlock_HursExponentIsAboveLevel_3_2, CBlock_HursExponentIsAboveLevel_2, KERbelowLevel, CBlock_EntropyHigh, EntropyMathAboveLevel, EntropyMathCrossAboveLevel, CSSAMarketRegimeAboveLevel, CBlock_CSSARegimeAbove50, SuperTrendInRange | 2 |
| Contexto: volatilidad alta (la reversión paga con volatilidad alta) y baja | CBlock_ATRRankHighVol, ATRPercentRankAboveLevel, CBlock_ATRRankLowVol, ATRPercentRankBelowLevel | 2 |
| Segunda condición: filtro de tendencia (pullback = contratendencia a favor de la tendencia) | MARising, MAFalling, MABarClosesAbove, MABarClosesBelow, SuperTrendUPTrend, SuperTrendDownTrend, DIPlusHigher, DIPlusLower, LinRegRising, LinRegFalling, MACDMainHigherZero, MACDMainLowerZero | 1 |
| Salida: el precio volvió a la media | CBlock_DisparityAbove0, CBlock_DisparityBelow0, CBlock_DPOAbove0, CBlock_DPOBelow0 | 1 |
| Segunda condición y salida: momentum girado | ROCAboveLevel, ROCBelowLevel, MACDMainHigherSignal, MACDMainLowerSignal | 1 |
| Segunda condición: la volatilidad sube, baja o está comprimida | ATRRising, ATRFalling, CBlock_SqueezeOn, CBlock_SqueezeOff | 1 |
| Velas de giro (un puñado) | BullishEngulfing, BearishEngulfing, Hammer, ShootingStar | 1 |
| Valores: estiramiento sin bloque de condición propio (%B, ZScore, Ultimate, Fisher) | BollingerBandsPercentB, ZScore, UltimateOscillator, AdaptiveFisherTransform | 2 |
| Comparadores (con percentil: el extremo relativo a su propia historia) | IsGreater, IsLower, CrossesAbove, CrossesBelow, IsGreaterPercentil, IsLowerPercentil | 1 |

## Tendencia — `tendencia_base_v3`

| clase de información | bloques | peso |
|---|---|---|
| Pendiente de la media (MA, LinReg, HMA, KAMA, DEMA, MAMA) | MARising, MAFalling, LinRegRising, LinRegFalling, HMARising, HMAFalling, KAMARising, KAMAFalling, DEMARising, DEMAFalling, CBlock_EMAMAIsRising_2_2, CBlock_EMAMAIsRising_2_3 | 3 |
| Precio respecto de la media | MABarClosesAbove, MABarClosesBelow, MABarOpensAbove, MABarOpensBelow, LinRegBarClosesAbove, LinRegBarClosesBelow | 3 |
| Media rápida sobre lenta, como estado (HMA, KAMA, DEMA, Didi, MACD > 0) | FasterHMAIsAboveSlowerHMA, FasterHMAIsBelowSlowerHMA, FastKAMAAboveSlowKAMA, FastKAMABelowSlowKAMA, DoubleDEMARising, DoubleDEMAFalling, DidiIndexUp, DidiIndexDown, MACDMainHigherZero, MACDMainLowerZero | 3 |
| Cruce de medias, como evento (SMA, EMA, HMA, MAMA/FAMA, Tenkan/Kijun, Didi, MACD por cero) | CBlock_CrossAboveMA, CBlock_CrossAboveMA_4, CBlock_CrossAboveMA_2, CBlock_CrossAboveMA_6, CBlock_CrossAboveMA_3, CBlock_CrossAboveMA_7, CBlock_EMAMAIsRising_2_2_2, CBlock_EMAMAIsRising_2_2_2_2, IchimokuTenkanKijunCrossBullish, IchimokuTenkanKijunCrossBearish, DidiIndexCrossUP, DidiIndexCrossDown, MACDMainCrossAboveZero, MACDMainCrossBelowZero | 3 |
| Movimiento direccional (DI+/DI−, Vortex, Aroon, IsUptrend) | DIPlusHigher, DIPlusLower, DICrossUp, DICrossDown, VortexUptrend, VortexDowntrend, AroonCrossesAbove, AroonCrossesBelow, IsUptrend, IsDowntrend | 3 |
| Trailing por volatilidad (SuperTrend, PSAR, Gann HiLo, PMax) | SuperTrendUPTrend, SuperTrendDownTrend, BarClosesAboveSuperTrend, BarClosesBelowSuperTrend, PSARBarHigher, PSARBarLower, GannHiLoUPTrend, GannHiLoDownTrend, CBlock_PMaxFlipUp, CBlock_PMaxFlipDown | 3 |
| Contexto: hay tendencia (ADX alto, choppiness bajo, Hurst > 0,5, eficiencia, entropía baja, CSSA bajo) | ADXHigher, ADXRising, ADXCrossUp, ADXChangesUp, CBlock_ChoppinessTrending, ChoppinessIndexBelowLevel, ChoppinessIndexCrossesBelowLevel, ChoppinessIndexFalling, CBlock_HursExponentIsAboveLevel_3, CBlock_HursExponentIsAboveLevel, KERaboveLevel, CBlock_EntropyLow, EntropyMathBelowLevel, EntropyMathCrossBelowLevel, CSSAMarketRegimeBelowLevel, CBlock_CSSARegimeBelow50 | 2 |
| Segunda condición contraria: retroceso dentro de la tendencia (reversión) | RSILower, RSIHigher, RSICrossUp, RSICrossDown, StochSlowDLower, StochSlowDHigher, CCILower, CCIHigher, WPRLower, WPRHigher, CBlock_ZScoreStretchedDown, CBlock_ZScoreStretchedUp, CBlock_IBSCloseLarger, CBlock_IBSCloseLarger_2, CBlock_CMMAIsAboveLevel, CBlock_CMMAIsAboveLevel_2, BBBarOpensAboveDownAfterOpenBelow, BBBarOpensBelowUpAfterOpenAbove | 1 |
| Segunda condición ortogonal: volatilidad | CBlock_ATRRankHighVol, CBlock_ATRRankLowVol, ATRRising, ATRFalling, ATRPercentRankAboveLevel, ATRPercentRankBelowLevel, CBlock_SqueezeOn, CBlock_SqueezeOff | 1 |
| Salida: la tendencia se apaga | ADXLower, ADXFalling, CBlock_ChoppinessChoppy | 1 |
| Velas (un puñado) | BullishEngulfing, BearishEngulfing, Hammer, ShootingStar | 1 |
| Valores: medias y trailings sin bloque de condición propio | KalmanFilter, VIDYA, TEMA, HalfTrend, SSL, SlopeDirectionLine, ATRTrailingStops | 2 |
| Valores: precio | Close | 1 |
| Comparadores | IsGreater, IsLower, CrossesAbove, CrossesBelow, IsRising, IsFalling | 1 |

## Momentum — `momentum_base_v3`

| clase de información | bloques | peso |
|---|---|---|
| Velocidad del precio en N barras (ROC, Momentum) | ROCAboveLevel, ROCBelowLevel, ROCCrossesAboveLevel, ROCCrossesBelowLevel, ROCRising, ROCFalling, MomHigher, MomLower, MomCrossUp, MomCrossDown, MomRising, MomFalling | 3 |
| Aceleración (MACD contra su señal, OSMA, Awesome) | MACDMainHigherSignal, MACDMainLowerSignal, MACDMainCrossAboveSignal, MACDMainCrossBelowSignal, MACDMainRising, MACDMainFalling, OSMAHigherZero, OSMALowerZero, OSMACrossZeroUp, OSMACrossZeroDown, OSMARising, OSMAFalling, AWOHigher, AWOLower, AWOCrossUp, AWOCrossDown, AWORising, AWOFalling | 3 |
| Impulso que supera a la volatilidad y vigor (Waddah Attar, momentum del squeeze, RVI) | CBlock_WAEPosAboveExplosion, CBlock_WAEPosAboveExplosion_2, CBlock_WAEPosAboveExplosion_2_2_2, CBlock_WAEPosAboveExplosion_2_2, CBlock_SqueezeMomentumPos, CBlock_SqueezeMomentumNeg, RVIAboveLevel, RVIBelowLevel, RVIRising, RVIFalling | 3 |
| Oscilador contra su propia señal (QQE, Estocástico K/D, WaveTrend, DSS, Ergodic, RSI contra su media, TDI) | QQEValue1HigherValue2, QQEValue1LowerValue2, QQEValue1CrossAboveValue2, QQEValue1CrossBelowValue2, CBlock_QQEModBuy, CBlock_QQEModSell, StochFastKUp, StochFastKDown, WaveTrendMainHigherSignal, WaveTrendMainLowerSignal, WaveTrendMainCrossAboveSignal, WaveTrendMainCrossBelowSignal, DSSBressertRising, DSSBressertFalling, DSSBressertCrossUP, DSSBressertCrossDown, BHErgodicUP, BHErgodicDown, BHErgodicCrossUP, BHErgodicCrossDown, CBlock_TRSICrossUp, CBlock_TRSICrossDown, CBlock_RMICrossUp, CBlock_RMICrossDown | 3 |
| Contexto: el movimiento es limpio (ADX, eficiencia, Hurst, choppiness bajo) | ADXHigher, ADXRising, KERaboveLevel, CBlock_HursExponentIsAboveLevel_3, CBlock_ChoppinessTrending, ChoppinessIndexBelowLevel | 2 |
| Contexto: volatilidad en expansión o recién comprimida | CBlock_ATRRankHighVol, CBlock_ATRRankLowVol, ATRRising, ATRFalling, CBlock_ATRCrossMAATR, CBlock_SqueezeOn, CBlock_SqueezeOff, CBlock_BBWRPercent, ATRPercentRankAboveLevel, ATRPercentRankBelowLevel | 2 |
| Segunda condición contraria y salida por agotamiento (reversión) | RSILower, RSIHigher, StochSlowDLower, StochSlowDHigher, CCILower, CCIHigher, WPRLower, WPRHigher, CBlock_ZScoreStretchedDown, CBlock_ZScoreStretchedUp, CBlock_IBSCloseLarger, CBlock_IBSCloseLarger_2 | 1 |
| Salida: pierde la media o el trailing, o el movimiento se apaga | MABarClosesAbove, MABarClosesBelow, BarClosesAboveSuperTrend, BarClosesBelowSuperTrend, ADXFalling, ADXLower | 1 |
| Velas (un puñado) | BullishEngulfing, BearishEngulfing, Hammer, ShootingStar | 1 |
| Valores: momentum sin bloque de condición propio (Accelerator, sesgo de volatilidad VST) | Accelerator, VST | 2 |
| Comparadores | IsGreater, IsLower, CrossesAbove, CrossesBelow, IsRising, IsFalling | 1 |

## Volatilidad — `volatilidad_base_v3`

| clase de información | bloques | peso |
|---|---|---|
| Nivel de volatilidad contra su propia historia (rango percentil del ATR, ATR en % del precio) | CBlock_ATRRankHighVol, CBlock_ATRRankLowVol, ATRPercentRankAboveLevel, ATRPercentRankBelowLevel, ATRPercentRankCrossUP, ATRPercentRankCrossDown, ATRPercentAboveLevel, ATRPercentBelowLevel, ATRPercentCrossUP, ATRPercentCrossDown | 3 |
| La volatilidad sube o baja (ATR, desviación típica, ATR contra su media) | ATRRising, ATRFalling, ATRChangesUp, ATRChangesDown, ATRPercentRankRising, ATRPercentRankFalling, StdDevRising, StdDevFalling, StdDevChangesUp, StdDevChangesDown, CBlock_ATRCrossMAATR | 3 |
| Compresión y liberación (Squeeze, anchura de Bollinger en percentil bajo) | CBlock_SqueezeOn, CBlock_SqueezeOff, CBlock_BBWRPercent | 3 |
| Cambio de distribución y calma (KS, Wasserstein, Waddah bajo la línea de explosión) | CBlock_KSBreakOn, CBlock_KSBreakOff, CBlock_WassersteinShiftHigh, CBlock_WassersteinShiftLow, CBlock_WAEPosAboveExplosion_2_2_3, CBlock_WAEPosAboveExplosion_2_2_3_2 | 3 |
| Las bandas se abren o se cierran (Bollinger, Keltner) | BBUpperRising, BBUpperFalling, BBLowerRising, BBLowerFalling, KCUpperRising, KCUpperFalling, KCLowerRising, KCLowerFalling | 2 |
| Régimen: hay tendencia | ADXHigher, ADXRising, ADXCrossUp, ADXChangesUp, CBlock_ChoppinessTrending, ChoppinessIndexBelowLevel, ChoppinessIndexCrossesBelowLevel, ChoppinessIndexFalling, CBlock_HursExponentIsAboveLevel_3, CBlock_HursExponentIsAboveLevel, KERaboveLevel, CBlock_EntropyLow, EntropyMathBelowLevel, EntropyMathCrossBelowLevel, CSSAMarketRegimeBelowLevel, CBlock_CSSARegimeBelow50 | 2 |
| Régimen: no hay tendencia | ADXLower, ADXFalling, ADXCrossDown, ADXChangesDown, CBlock_ChoppinessChoppy, ChoppinessIndexAboveLevel, ChoppinessIndexCrossesAboveLevel, ChoppinessIndexRising, CBlock_HursExponentIsAboveLevel_3_2, CBlock_HursExponentIsAboveLevel_2, KERbelowLevel, CBlock_EntropyHigh, EntropyMathAboveLevel, EntropyMathCrossAboveLevel, CSSAMarketRegimeAboveLevel, CBlock_CSSARegimeAbove50, SuperTrendInRange | 2 |
| Dirección — ruptura | CBlock_BreakoutDonchianLong, CBlock_BreakoutDonchianLong_2, CBlock_BBBreakoutUp, CBlock_BBBreakoutDown, CBlock_CandleBreakoutLong, CBlock_CandleBreakoutLong_2, BarOpensAboveHighestAfterOpenBelow, BarOpensBelowLowestAfterOpenAbove, KCBarOpensAboveUpperAfterOpenBelow, KCBarOpensBelowLowerAfterOpenAbove, TTMSqueezeMomentumCrossLevelUP, TTMSqueezeMomentumCrossLevelDown | 1 |
| Dirección — momentum | ROCAboveLevel, ROCBelowLevel, MACDMainHigherSignal, MACDMainLowerSignal, CBlock_WAEPosAboveExplosion, CBlock_WAEPosAboveExplosion_2, OSMAHigherZero, OSMALowerZero | 1 |
| Dirección — tendencia | MARising, MAFalling, MABarClosesAbove, MABarClosesBelow, SuperTrendUPTrend, SuperTrendDownTrend, DIPlusHigher, DIPlusLower | 1 |
| Dirección — reversión | RSILower, RSIHigher, CBlock_ZScoreStretchedDown, CBlock_ZScoreStretchedUp, CBlock_IBSCloseLarger, CBlock_IBSCloseLarger_2, BBBarOpensAboveDownAfterOpenBelow, BBBarOpensBelowUpAfterOpenAbove, StochSlowDLower, StochSlowDHigher | 1 |
| Velas (un puñado) | BullishEngulfing, BearishEngulfing, Hammer, ShootingStar | 1 |
| Valores: volatilidad para comparar con su propia historia | LogATR, StdDev, ATRPercent | 2 |
| Comparadores (percentil y sube/baja) | IsGreaterPercentil, IsLowerPercentil, IsRising, IsFalling | 1 |

## Pullback — `pullback_base_v3`

| clase de información | bloques | peso |
|---|---|---|
| Contexto de tendencia — pendiente de la media | MARising, MAFalling, LinRegRising, LinRegFalling, HMARising, HMAFalling, KAMARising, KAMAFalling, DEMARising, DEMAFalling, CBlock_EMAMAIsRising_2_2, CBlock_EMAMAIsRising_2_3 | 3 |
| Contexto de tendencia — precio respecto de la media | MABarClosesAbove, MABarClosesBelow, MABarOpensAbove, MABarOpensBelow, LinRegBarClosesAbove, LinRegBarClosesBelow | 3 |
| Contexto de tendencia — media rápida sobre lenta (estado) | FasterHMAIsAboveSlowerHMA, FasterHMAIsBelowSlowerHMA, FastKAMAAboveSlowKAMA, FastKAMABelowSlowKAMA, DoubleDEMARising, DoubleDEMAFalling, DidiIndexUp, DidiIndexDown, MACDMainHigherZero, MACDMainLowerZero | 3 |
| Contexto de tendencia — movimiento direccional (estado) | DIPlusHigher, DIPlusLower, VortexUptrend, VortexDowntrend, IsUptrend, IsDowntrend | 3 |
| Contexto de tendencia — trailing por volatilidad (estado) | SuperTrendUPTrend, SuperTrendDownTrend, PSARBarHigher, PSARBarLower, GannHiLoUPTrend, GannHiLoDownTrend | 3 |
| Disparo de reversión — oscilador acotado en extremo | RSILower, RSIHigher, RSICrossUp, RSICrossDown, StochSlowDLower, StochSlowDHigher, StochSlowDCrossUp, StochSlowDCrossDown, StochFastKCrossUp, StochFastKCrossDown, CCILower, CCIHigher, CCICrossUp, CCICrossDown, WPRLower, WPRHigher, WPRCrossUp, WPRCrossDown, DEMLower, DEMHigher, DEMCrossUp, DEMCrossDown, DVOBelowLevel, DVOAboveLevel, DVOCrossAboveLevel, DVOCrossBelowLevel, LaguerreRSICrossUP, LaguerreRSICrossDown, WaveTrendMainLower, WaveTrendMainHigher, WaveTrendMainCrossAbove, WaveTrendMainCrossBelow | 3 |
| Disparo de reversión — estiramiento respecto de la media | CBlock_ZScoreStretchedDown, CBlock_ZScoreStretchedUp, CBlock_CMMAIsAboveLevel, CBlock_CMMAIsAboveLevel_2, CBlock_CMMAIsAboveLevel_3, CBlock_CMMAIsAboveLevel_3_2, DisparityIndexBelowLevel, DisparityIndexAboveLevel, DisparityIndexCrossesAboveLevel, DisparityIndexCrossesBelowLevel | 3 |
| Disparo de reversión — IBS | CBlock_IBSCloseLarger, CBlock_IBSCloseLarger_2, CBlock_IBSCloseLarger_3, CBlock_IBSCloseLarger_4 | 3 |
| Disparo de reversión — reentrada en la banda o el canal | BBBarOpensAboveDownAfterOpenBelow, BBBarOpensBelowUpAfterOpenAbove, KCBarOpensAboveLowerAfterOpenBelow, KCBarOpensBelowUpperAfterOpenAbove, BarOpensAboveLowestAfterOpenBelow, BarOpensBelowHighestAfterOpenAbove | 3 |
| Disparo de reversión — giro desde el extremo | CBlock_StochWeightsUp, CBlock_StochWeightsDown, CBlock_SmoothedRSIRising_3_3, CBlock_SmoothedRSIRising_3_3_2 | 3 |
| Contexto: la tendencia es limpia | ADXHigher, ADXRising, CBlock_ChoppinessTrending, CBlock_HursExponentIsAboveLevel_3, KERaboveLevel, CBlock_CSSARegimeBelow50 | 2 |
| Contexto: nivel de volatilidad | CBlock_ATRRankHighVol, CBlock_ATRRankLowVol, ATRPercentRankAboveLevel, ATRPercentRankBelowLevel | 2 |
| Salida: el precio volvió a la media | CBlock_DisparityAbove0, CBlock_DisparityBelow0, CBlock_DPOAbove0, CBlock_DPOBelow0 | 1 |
| Salida: la tendencia se apaga o se pierde el trailing | ADXLower, ADXFalling, CBlock_ChoppinessChoppy, BarClosesAboveSuperTrend, BarClosesBelowSuperTrend, CBlock_PMaxFlipUp, CBlock_PMaxFlipDown | 1 |
| Salida y segunda condición: volatilidad y momentum girado | ATRRising, ATRFalling, CBlock_SqueezeOn, CBlock_SqueezeOff, MACDMainHigherSignal, MACDMainLowerSignal | 1 |
| Velas de giro (un puñado) | BullishEngulfing, BearishEngulfing, Hammer, ShootingStar | 1 |
| Valores: estiramiento sin bloque propio (%B, ZScore) | BollingerBandsPercentB, ZScore | 2 |
| Comparadores (con percentil) | IsGreater, IsLower, CrossesAbove, CrossesBelow, IsGreaterPercentil, IsLowerPercentil | 1 |

## Lo que se ha dejado fuera, y por qué

| qué | por qué |
|---|---|
| Todo `Bar And Time` (hora, día, mes, primer/último día del mes) y `TimeBreakout` | regla 15: nada que lea el reloj o el calendario |
| SessionHigh/Low/Open/Close, OpenD/HighD/LowD/CloseD y sus versiones semanales y mensuales, HighestInRange/LowestInRange, VWAP anclado, perfil de volumen, TPO, Pivots | dependen de una franja horaria; no has decidido sobre ellos |
| Bloques que solo son nivel stop/limit (BarRange, BBRange, FixedPips, niveles de Ehlers…) | todo va a mercado |
| Volumen: Avg Volume, Money Flow Index, VWAP | es volumen de ticks, cambia con el feed; nadie lo ha medido en los 16 activos |
| `CBlock_BarsLargerRSI` y `_2` | taxonomía a cero, como pediste |
| `CBlock_BullishMarubozu` y `_2` | leída su definición: compara el cuerpo en unidades de precio con un número y Close/High > 0,9, que es casi siempre cierto. No es lo que dice su nombre |
| El resto de las 60 velas «La City» | patrón: como mucho un puñado, y se han usado las 4 nativas (envolventes, martillo, estrella fugaz) |
| ATR y StdDev contra un nivel fijo en puntos, DPO contra nivel | no viaja entre activos ni entre años |
| Woodies CCI, SR Percent Rank, Ulcer Index, Reflex, CUSUM, DTW, Fibo, Aroon «rise/fall from top/bottom» | no he podido verificar qué calculan exactamente |
| Bulls/Bears Power | distancia a la media: ni momentum ni extremo acotado |
| Los duplicados: 2 de los 8 cruces de medias (SSMA), los cruces custom de Didi y Aroon (ya están los nativos), 2 WAE repetidos | mismo dato dos veces |

## Bloques cuya lectura es «por el nombre», sin código leído

`IsUptrend`/`IsDowntrend` (el método de tendencia es un parámetro interno), los seis bloques de Ehlers MAMA/FAMA usados (leídos dos de ellos, los demás por nombre), `SchaffTrendCycle` y `DVO` (acotados 0-100 según su ficha), `VST` y `Accelerator` como valores (rango tomado de la ayuda de SQX), y `CBlock_StrongCandle`, que solo existe en alcista (no tiene gemelo bajista).

Comprobado en el código: `CBlock_SqueezeOn` = Bollinger dentro de Keltner (comprimido), `SqueezeOff` lo contrario; los cuatro `TTMSqueezeMomentum…` nativos solo disparan con el squeeze ON (por eso están en ruptura); `CSSA` alto = rango, bajo = tendencia; `Momentum` de SQX es un cociente ×100 (viaja entre activos); `RVI` es el Relative Vigor Index (−1..1), no un oscilador 0-100.
