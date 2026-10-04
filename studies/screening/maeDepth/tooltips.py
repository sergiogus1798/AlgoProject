"""One sentence per config.yaml knob, for the window's configuration drawer."""

TIPS = {
    "depth.k": "Distancias en ATR a las que se cuenta una operación como profunda: las que "
               "en algún momento estuvieron a k ATR o más en contra. Se leen todas.",
    "depth.slippage": "Deslizamiento, en ATR, con el que se cierra la operación profunda en el "
                      "contrafactual: sale a -(k + deslizamiento) ATR. Tres lecturas; es una "
                      "cota, no un backtest de stop.",
    "depth.atr_period": "Periodo del ATR de SQX (Wilder) de la barra cerrada antes de la "
                        "entrada; el mismo que usa el paso 24.",
    "anomaly.sigma": "Una operación es anómala si su MAE es profundo Y su duración, en barras, "
                     "llega a media + sigma desviaciones de su estrategia y tramo.",
    "verdict.min_cuota_rec": "Cuota del beneficio neto que dan las anómalas recuperadas a partir "
                             "de la cual se marca la estrategia. Sin fijar: decisión del dueño.",
    "verdict.action": "'mark' sólo marca la estrategia; 'drop' hace que verdict.csv pida "
                      "DESCARTAR a las marcadas. Decisión del dueño."}
