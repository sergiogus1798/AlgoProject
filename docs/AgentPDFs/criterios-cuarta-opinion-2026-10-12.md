# Cuarta opinión sobre los criterios del workflow: la decisión de desplegar, no la inferencia

**Fecha:** 2026-10-12 · **Autor:** gestor de riesgo (Opus, sesión única) · **Material:** `docs/AgentPDFs/criterios-implementados-2026-10-12.md` (leído por secciones en subagentes), `pipeline/autopilot/criteria.yaml`, `ledger/thresholds.yaml`, `AlgoData/funding/rules/{ftmo,hantec}.yaml`, `AlgoData/funding/funding.sqlite` (tabla `stages`), `mt5/verify/README.md`, `perf/README.md`, y las 3.261.933 operaciones de `AlgoData/reports/Test_USATEC_H1_ruptura_leaseWeb/Results/2026-10-11/gate/operaciones.parquet`. Opción elegida: **(b)**, las tres opiniones anteriores se leyeron después de entregar la tabla; el apartado «Dónde discrepo» va al final.

Todo el cómputo nuevo de este dossier está en dos guiones del scratchpad de la sesión (`fondeo_sim.py`, `sprt.py`); reproducen cada cifra desde las 169 supervivientes del gate de USATEC H1 (1R = 1.000 USD, `assets/_build.yaml`, Amount 1000). Nada se ejecutó en SQX.

---

## 0. Las cinco cifras que gobiernan todo lo demás

| cifra | valor | de dónde |
|---|---|---|
| ventaja por operación de las 169 supervivientes en oos1 (2020-2023) | **0,095 R** (sd 0,706 R, Sharpe por operación 0,135, 65,8 op./año, 6,26 R/año) | `operaciones.parquet`, 169 identidades `MANTENER` de `verdict.csv` |
| probabilidad de que una superviviente del paso 8 tenga ventaja real | **≈ 0,42** | nula 0,98 % · real 1,69 % · plantada 0,10 → 50,2 % (dossier §8.7, control `falsePositives`): tasa base π = (1,69 − 0,98)/(50,2 − 0,98) = 1,4 %; posterior = 0,014·0,502/0,0169 = 0,42. Con ventaja 0,05 en vez de 0,10 sale 0,44 |
| coste esperado de un falso positivo (una nula en una cuenta FTMO 2-step 100k, tamaño 2 % en evaluación y 1 % fondeada) | **≈ 0 € (−220 … +490 €)** | tasa 540 €; una nula pasa la evaluación el 25,7 % de las veces y cobra 2.950 USD/año fondeada (simulación §2) |
| ganancia esperada de un verdadero positivo (0,10 R real, misma cuenta) | **≈ +4.000 €/año** | 0,749·6.064 − 540 (simulación §2) |
| operaciones en vivo para pasar de p = 0,42 a p = 0,8 | **179 si la ventaja es 0,10 R (2,7 años); 714 si es 0,05 R (10,9 años)** | KL por operación = μ²/2σ² = 0,0100 / 0,0025 nats; hacen falta 1,79 nats (`sprt.py`) |

De aquí sale todo: **el umbral de evidencia que hace rentable desplegar es p* ≈ 0,05-0,10, la cadena ya está en 0,42 tras el paso 8, y el vivo no puede subir esa p en un plazo útil.** Lo que sigue son las consecuencias.

---

## 1. Lo roto antes de decidir

Nada de lo de abajo es una decisión estadística; es lo que invalida cualquier decisión mientras siga así.

1. **El repreciador de Python no reproduce a SQX.** `descuadre_sqx` en los lotes del WFC llega a 0,853-0,868 (USDJPY 10k) y 0,590 (XAUUSD) (dossier §17, `one.py:139-150`); `costes.descuadre` vale 0,925-1,0 en las 13 corridas del 18.5 con el aviso `cost_gap` que no cambia el estado (dossier §18.5). El repreciador está «UNVERIFIED against SQX» para cortos, comisión ≠ 0 y swap en puntos (dossier §8 L715, OPEN #26). Todo paso de Python desde el 14 lee un P/L que no es el del simulador. Decisión: ningún corte en Python sobre P/L repreciado hasta que el descuadre sea < 1 % en el lote (umbral que ya existe: `wfc.sqx_gap_relative = 0,01`, `thresholds.yaml:1291`).
2. **Los costes de las fichas son provisionales y, donde se han medido, cortos.** NIKKEI225 build: 304 en la ficha, 607 en la propuesta de septiembre, 747 medido en Darwinex (dossier §4.12 d358); cociente ficha/medido 0,41 build, 0,65 oos1, 1,74 oos2 (d354). La hora 0 del servidor pesa el 29 % de la media de USDJPY/FTMO con un spread 9× (d357). El swap de hoy se aplica a 2018-2023 (d654). La comisión `SizeBased` no está verificada operación a operación: USDJPY pasaría de 10,49 a 15,49 USD por ida y vuelta (d373). Con R5c exigiendo ventaja ≥ 2 costes (`criteria.yaml:91-94`), un coste a la mitad duplica la tasa de paso: 59 % en USATEC, 2 % en XAUUSD con el mismo umbral (dossier §25).
3. **La reconciliación con MT5 falla en lo que se ha probado.** NIKKEI225: 0 de 5 validadas en FTMO y en Hantec; fila 1 (emparejamiento) 0,46-0,87 frente al 0,95 exigido; fila 2 (diferencia de P/L por pareja) 0,23-1,03 R frente a 0,05 (dossier §26). Solo USDJPY H1 valida, y solo en FTMO. La fila 5 compara drawdown de balance, no flotante, y para fondeo manda el flotante (dossier §26 ⚠). Ninguna superviviente real ha llegado al 26 por el flujo completo.
4. **Reglas de las firmas con lectura pendiente.** FTMO 2-step: devolución de la tasa «unconfirmed», modelada como no (`rules/ftmo.yaml`, `fee_refund`, 2026-10-11); si se devuelve con el primer pago, el coste del falso positivo baja otros 540 €. Hantec: ciclo de pago no está en `rules/hantec.yaml` (aquí se asume 14 días como FTMO, `payout_cycle` confirmado solo en FTMO); «no identical EA across accounts/users» (`ea_policy`) afecta a operar la misma estrategia en dos cuentas Hantec; `profit_target_addon_phases` sin confirmar. La pérdida diaria de FTMO incluye flotante (`daily_loss_basis`); la simulación de §2 es a cierre de día con un estrés de MAE (media −0,60 R, peor −3,39 R en las 825 operaciones OOS de la cosecha), no un flotante real.
5. **El corte real del paso 8 hoy no es un criterio.** `dev.on: true, sample: 3` (`criteria.yaml:53-57`): 10.000 → 3 al azar entre las 169 (`judge.py:197-203`). Las tres de USATEC eran Limbo. Ninguna corrida de los pasos 9-20 ha visto una población elegida por criterio.
6. **Los ensayos no se cuentan.** `trials.accumulated` falla con `TypeError` (`trials.py:40`, dossier §3 d272); `criteria-history.jsonl` tiene 16 ediciones y no hay `frozen` (dossier §8 L884); 61 de 61 plantillas siguen `draft`; oos1 cribado 4 veces en la misma celda (19.000 estrategias) y 94 filas sobre oos2 (dossier §3 d273). Ver §8.
7. **Datos.** 15 activos construyen antes de su año estable (dossier §4.9); el IS de NIKKEI parece empezar tarde (cociente 9,0 vs 1,06, d650); el build de forex es modelo en el 97,6 % de sus días (d355).
8. **La población plantada no puede atravesar SQX.** Plantar 0,05/0,10/0,15 R por operación es una transformación del parquet de operaciones; los pasos 13, 15 y 19 re-ejecutan en SQX y no ven esa ventaja. La corrida de contraste tendrá «no sé» en esos pasos por construcción, salvo que la ventaja se plante en el precio.

---

## 2. El umbral de decisión y su derivación

### 2.1 Las reglas que se simulan

Tabla `stages` de `funding.sqlite`, planes de 100.000 (precio en EUR para FTMO, USD para Hantec, convertido ×0,92):

| plan | fase 1 | fase 2 | pérdida diaria | pérdida máxima | mínimo | tasa |
|---|---|---|---|---|---|---|
| FTMO 2-step | +10 % | +5 % | 5 % (balance a medianoche, flotante incluido) | 10 % estática | 4 días operados por fase | 540 € |
| FTMO 1-step | +10 % | — | 3 % | 10 % trailing a cierre, se ancla en el inicial | mejor día ≤ 50 % de los días positivos | 499 € |
| Hantec Enhanced | +10 % | +5 % | 5 % (máx(balance, equity) a las 00:00) | 10 % estática | 3 días rentables ≥ 0,5 % por fase | 599 USD |
| Hantec Express | +10 % | — | 5 % | 6 % trailing, se ancla en el inicial al +6 % | ninguno | 529 USD |

Fondeada: mismos límites, reparto 80 %, pago cada 14 días (10 días operados) con el balance de vuelta al inicial (FTMO `payout_cycle` 14; Hantec asumido igual, pregunta Q4).

### 2.2 La simulación

Bootstrap por bloques de 20 días dentro de una estrategia, sobre el P/L diario cerrado de las 169 supervivientes en oos1 (1.043 días), 2.000 caminos por celda, escenarios recentrados por operación: real (0,095 R, sesgada al alza por la selección del propio oos1), nula (0), plantada 0,05 / 0,10 / 0,15. **k** es cuánto vale 1R en % de la cuenta. Horizonte de evaluación 3 años; fondeada 12 meses.

| firma | k | escenario | P(fase 1) | P(evaluación) | P(evaluación ≤ 12 m) | días op. mediana | P(vive 12 m fondeada) | pago 12 m (USD) | EV cuenta (€) |
|---|---|---|---|---|---|---|---|---|---|
| FTMO 2-step | 1 % | real | 0,856 | 0,840 | 0,036 | 535 | 0,986 | 5.865 | +4.381 |
| FTMO 2-step | 1 % | nula | 0,280 | 0,220 | 0,002 | 807 | 0,875 | 2.950 | +158 |
| FTMO 2-step | 1 % | 0,05 | 0,608 | 0,562 | 0,013 | 672 | 0,952 | 4.421 | +1.966 |
| FTMO 2-step | 1 % | 0,10 | 0,896 | 0,886 | 0,052 | 507 | 0,987 | 6.064 | +4.815 |
| FTMO 2-step | 1 % | 0,15 | 0,987 | 0,982 | 0,148 | 379 | 0,998 | 8.211 | +7.519 |
| FTMO 2-step | 2 % | real | 0,848 | 0,752 | 0,432 | 226 | 0,684 | 11.380 | +8.102 |
| FTMO 2-step | 2 % | nula | 0,420 | 0,257 | 0,116 | 276 | 0,382 | 5.579 | +904 |
| FTMO 2-step | 2 % | 0,05 | 0,662 | 0,528 | 0,244 | 268 | 0,548 | 8.355 | +3.959 |
| FTMO 2-step | 0,5 % | real | 0,488 | 0,488 | 0,000 | 885 | 1,000 | 2.951 | +961 |
| FTMO 2-step | 0,5 % | nula | 0,037 | 0,035 | 0,000 | 1.023 | 0,999 | 1.527 | −489 |
| FTMO 1-step | 1 % | real | 0,850 | 0,850 | 0,278 | 322 | 0,970 | 6.117 | +4.674 |
| FTMO 1-step | 1 % | nula | 0,268 | 0,268 | 0,058 | 386 | 0,848 | 3.037 | +342 |
| Hantec Enhanced | 1 % | real | 0,866 | 0,850 | 0,038 | 536 | 0,988 | 5.906 | +4.446 |
| Hantec Enhanced | 1 % | nula | 0,264 | 0,218 | 0,002 | 785 | 0,872 | 2.963 | +1 |
| Hantec Express | 1 % | real | 0,760 | 0,760 | 0,297 | 296 | 0,860 | 5.734 | +3.846 |
| Hantec Express | 1 % | nula | 0,221 | 0,221 | 0,054 | 367 | 0,520 | 2.888 | +160 |

Con el estrés flotante (MAE 0,6 R por día con operación) FTMO 2-step a k = 1 % apenas se mueve (real 0,842 / 0,978 / +4.485; nula 0,218 / 0,856 / +80); FTMO 1-step sí cae por su 3 % diario (real 0,679 / 0,820 / +3.394).

Drawdown a 12 meses en R (real): p50 3,7 · p90 6,8 · p99 10,0; peor día p99 3,14 R. Nula: p50 5,7 · p90 11,2 · p99 16,5. **A k = 1 % el p99 del drawdown real coincide con el 10 % de pérdida máxima**: es el tamaño que la regla de la firma permite a esta población, y no otro.

### 2.3 La derivación

Sea p la probabilidad de que la candidata tenga ventaja ≥ 0,10 R. Desplegar paga si p·G − (1−p)·L > 0, es decir **p* = L/(L+G)**.

- **L** (falso positivo) = tasa − P(nula pasa)·pago(nula) + coste del tiempo. En euros: 540 − 0,257·2.950·0,92 ≈ −160 € con k = 2 % en evaluación; +490 € con k = 0,5 %. **El falso positivo cuesta ≈ 0 € en dinero**: la tasa de la firma está puesta al precio de la opción que una nula disciplinada tiene sobre sus pagos quincenales. Lo que cuesta es **tiempo**: una nula ocupa la cuenta una mediana de 276 días operados en evaluación y 12 meses más fondeada antes de que el 10 % la mate (62 % de las nulas a k = 2 %, 12,5 % a k = 1 %).
- **G** (verdadero positivo, 0,10 R) = 0,749·6.064·0,92 − 540 ≈ **+3.640 €/año** por cuenta de 100k; con 0,05 R, +1.650 €; con 0,15 R, +6.500 €.
- **p*** = 0 … 490/(490 + 3.640) = **0,00 … 0,12**. Con el tiempo como coste (una cuenta-año vale G si la ocupa una buena y ≈ 0 si la ocupa una nula): p* = (coste de la cuenta-año perdida)/(G + …) ≈ 0,10-0,15 si se dispone de más candidatas que cuentas, y ≈ 0 si sobran cuentas.

**Comparación con la cadena.** Tras el paso 8, p ≈ 0,42: ya es 3-4× el umbral. Cada superviviente del 8 que la cola 9-20 descarta cuesta en esperanza 0,42 × 3.640 ≈ **1.500 €/año**; cada nula que deja pasar cuesta ≈ 0 € y una cuenta-año. La cola está construida como si L ≫ G; la cuenta dice G ≫ L. En los pasos 17-20 el falso NO PASA con ventaja real es del 22 % (WFC, `wfc_calibration.json`), 15-29 % (CSCV, README) y ≈ 100 % en la lectura `peor` del 20 (16 de 16 madres completas serían DESCARTAR, dossier §20): la cola destruye entre 0,42·0,22·3.640 ≈ 340 €/año (solo el 17) y 1.500 €/año (el 20) por superviviente, y no evita ninguna pérdida mensurable.

### 2.4 Decisión ejecutable

- **Umbral de evidencia para enviar a evaluación: p ≥ 0,15, que hoy equivale a «supera el paso 8 por criterio (no por sorteo) y el 26 valida la fidelidad».** Coste: las candidatas nulas que entran (58 % de las supervivientes) consumen ≈ 0 € y una cuenta-año cada una. Ganancia: no se pierde ninguna de las 0,42·N verdaderas, ≈ 1.500 €/año por superviviente recuperada.
- **Tamaño: k = 2 % en evaluación (mediana 226 días operados, 43 % pasa antes de 12 meses, 75 % pasa) y k = 1 % fondeada (vive 12 meses el 98,6 %, p99 del drawdown = 10 R).** Con k = 1 % en evaluación la mediana es 535 días: 2,1 años para cobrar el primer euro.
- **Capital inicial: una cuenta por apuesta independiente de la celda (2-4, §5) = 1.080-2.160 € en FTMO 2-step 100k, o 356 € en cuatro cuentas de 10k (89 € cada una) como laboratorio en vivo** (mismos porcentajes, pagos ÷10: EV real +440 €/año por cuenta, nula ≈ 0). La firma ya cobra la opción; no hay capital propio en riesgo más allá de la tasa.
- **Firma:** FTMO 2-step y Hantec Enhanced son equivalentes en esta población (0,840 / 0,850 de paso; 0,986 / 0,988 de supervivencia). FTMO 1-step pasa antes (mediana 322 días) pero su 3 % diario con flotante baja la supervivencia a 0,82. Hantec Express (6 % trailing) mata al 48 % de las nulas y al 14 % de las reales en 12 meses: es la mejor **prueba** de una estrategia y la peor **cuenta**.

---

## 3. La tabla de predicciones y la tabla de fondeo

### 3.1 Tasa de paso esperada por paso (se contrastará con la corrida real, la nula y las plantadas)

«Tasa de paso» = fracción que sigue viva tras el paso (Pasa o Limbo), sobre las que entran en él. Las entradas del 9 en adelante son supervivientes del 8, lo que condiciona la nula: una nula que sobrevivió al 8 es una nula afortunada en oos1.

| paso | real | nula | plantada 0,05 / 0,10 / 0,15 | razón en una línea |
|---|---|---|---|---|
| 8 | 1,0-2,5 % (1,69 % observado) | 0,8-1,2 % (0,98 %) | 18-22 / 48-55 / 73-78 % (19,2 / 50,2 / 75,3 % observado) | R3 (t ≥ 1,65, una cola) corta el 97,8 % de lo que le llega; el resto es casi Limbo (165 de 169), `criteria.yaml:60-100` |
| 9 | 100 % | 100 % | 100 % | medición, no corta (dossier §9) |
| 10 | 55-70 % (2 de 3 observado) | 60-70 % | **no sé**: si la ventaja se planta solo en el principal, ≈ nula (60-70 %); si en todos los mercados, 85-95 % | P3 incluye V1 y V2 donde la principal ya se seleccionó (dossier §10 L78); z_conj sd 1,08 centrada en 0 → la mitad de una nula falla P3, pero la nula que llega está seleccionada en V2 |
| 10.5-11.7 | 100 % | 100 % | 100 % | fabricación y retest, `rules: []` |
| 12 | 100 % | 100 % | 100 % | `pass ≥ 2,33 else limbo`: nunca elimina madres (dossier §12, dueño 2026-10-01) |
| 13 | 100 % | 100 % | 100 % | genera vecinas y MCR, no corta |
| 14 | 50-65 % (7 de 10 en las 4 corridas juzgadas; 0 de 9 y 3 de 50 en smoke) | 30-45 % | **no sé** en SQX (T2, T3 re-ejecutan en SQX y no ven la plantación); T1 build con vecinas en Python: 55 / 75 / 90 % | T1 mata por `f_pos < 0,7` y por exceso build ≤ 0 (29 de 50 en NIKKEI H1), que es sesgo de la madre, no fragilidad (dossier §14 ⚠) |
| 15-16 | 100 % | 100 % | 100 % | `rules: []` (`criteria.yaml:225-229`) |
| 16.5 | 100 % | 100 % | 100 % | `cut: null` |
| 17 | 75 % no cortadas (0 PASA, 9 LIMBO, 3 NO PASA de 12) | 50-55 % (calibración sintética: PASA 0,02, LIMBO 0,50, NO PASA 0,48) | 75-80 / 90-95 / 95-98 % (Sharpe anual ≈ 0,57 / 1,1 / 1,7 ↔ filas «0,5 sin orden» 78 % y «1,0 sin orden» 93 % de `wfc_calibration.json`) | NO PASA = `nivel_top ≤ 0`; la banda del nulo (±0,20 a ±0,74) casi nunca rechaza el orden |
| 18 | 95-100 % (10 de 10) | 50-60 % | 70-85 / 90-95 / 95-100 % | NO PASA si `p_perdida ≥ 0,5`; falso NO PASA 14,7-29,3 % en paneles sintéticos con Sharpe semanal 0,03 (README CSCV) |
| 18.5 | 90-100 % (11 PASA + 2 LIMBO de 13) | 90-95 % | 90-100 % | solo «perverso» (p− ≤ 0,05) es NO PASA; las 13 salen neutro; `cost_gap` en todas |
| 19 | 90-100 % (7 PASA + 3 LIMBO de 10) | 85-90 % | 95-100 % | NO PASA si p− ≤ 0,05 sobre 143-195 semanas; el p− mínimo observado es 0,066; con asimetría el nulo rechaza 13 % al 5 % |
| 20 (`peor`, corte en `SPP OOS`) | 70-75 % no DESCARTAR, **0 % MANTENER** | 20-25 % | 55-60 / 78-82 / 85-90 % | DESCARTAR = algún `fail` en 17/18/18.5/19; MANTENER exige cuatro PASA, que ningún lote ha dado |
| 8 → 20 acumulado | ≈ 0,4-0,8 % de 10.000 | ≈ 0,05-0,1 % | ≈ 5-7 / 20-30 / 45-60 % | producto de las filas; la cola después del 8 quita ≈ 2/3 de lo real y ≈ 9/10 de lo nulo: razón de verosimilitud ≈ 3-4, frente a 51 del paso 8 solo |

### 3.2 Tabla de fondeo para una superviviente (del §2.2, k = 2 % en evaluación y 1 % fondeada)

| escenario | FTMO 2-step: P(fase 1) · P(evaluación) · P(≤ 12 m) | Hantec Enhanced: P(fase 1) · P(evaluación) · P(≤ 12 m) | P(sobrevive 12 m fondeada), FTMO / Hantec | cálculo |
|---|---|---|---|---|
| superviviente tal cual (0,095 R, sesgada) | 0,848 · 0,752 · 0,432 | 0,834 · 0,740 · 0,423 | 0,986 / 0,988 | bootstrap de sus propios días; P(eval) = fase 1 × fase 2 a k = 2 %; supervivencia a k = 1 % |
| superviviente deflactada a 0,05 R (lo que vale si la mitad de la t es selección) | 0,662 · 0,528 · 0,244 | 0,662 · 0,507 · 0,239 | 0,952 / 0,954 | ídem recentrada |
| nula | 0,420 · 0,257 · 0,116 | 0,428 · 0,269 · 0,116 | 0,875 / 0,872 | ídem recentrada a 0 |
| **mezcla p = 0,42 (lo que la cadena entrega hoy)** | **≈ 0,60 · 0,47 · 0,25** | ≈ 0,60 · 0,47 · 0,25 | ≈ 0,92 | 0,42·real + 0,58·nula |

Lectura: de cada 100 supervivientes enviadas a evaluación, 47 llegan a fondeadas (25 dentro del primer año), y de esas 47, ≈ 43 siguen vivas al año; 21 de ellas son nulas que cobran la opción. El 10 % de pérdida máxima a k = 1 % no distingue una buena de una nula en 12 meses (0,986 frente a 0,875): **la cuenta fondeada no es un filtro, es un instrumento de pago.**

---

## 4. El protocolo en vivo

### 4.1 Lo que el vivo no puede hacer

Con sd 0,706 R y 65,8 operaciones/año, la información por operación es μ²/2σ² = 0,0100 nats (0,10 R) o 0,0025 (0,05 R). SPRT H0: μ = 0 contra H1: μ = 0,10, α = 0,05, β = 0,10 (`sprt.py`, trades remuestreados de las 169):

| μ real | P(acepta H1) | operaciones, mediana · p90 | el 10 % de la firma la mata antes que el SPRT decida | muerta por la firma en 12 meses |
|---|---|---|---|---|
| 0,00 | 0,047 | 160 · 416 | 36,7 % | 11,6 % |
| 0,05 | 0,439 | 265 · 744 | 33,7 % | 5,2 % |
| 0,10 | 0,907 | 208 · 479 | 9,5 % | 1,7 % |
| 0,15 | 0,990 | 127 · 250 | 1,6 % | 0,6 % |

Para H1: μ = 0,05 la mediana son 808 operaciones (12 años). Agrupar la celda no rescata: con ρ semanal 0,73 entre estrategias de la misma lógica (38 de 41, dossier §3 d272), 2-4 estrategias dan un factor de información 1,16-1,25.

**Conclusión: el vivo no sube p de 0,42 a 0,8 en un plazo operable (179 operaciones = 2,7 años en el mejor caso).** El backtest en oos1 (263 operaciones por estrategia, 4 años) sigue siendo la mayor parte de la evidencia que habrá nunca. El papel del vivo es otro: **matar rápido y comprobar fidelidad**.

### 4.2 El protocolo, en tres etapas

**Etapa A, fidelidad (demo o cuenta de 10k, 30 operaciones, ≈ 5 meses a 65,8/año).** Las filas 1, 2, 3a y 5 del paso 26 (`thresholds.yaml:1041-1097`) aplicadas a las operaciones reales frente a la re-ejecución SQX del mismo tramo: emparejadas ≥ 0,95, diferencia media ≤ 0,05 R, correlación diaria ≥ 0,95, drawdown relativo ≤ 0,10. Tasa de error: con 30 operaciones y sd de la diferencia ≈ 0,1 R, el error típico de la media es 0,018 R → t ≈ 2,7 contra 0,05 R: α ≈ 0,01, β ≈ 0,2 para un sesgo real de 0,10 R. La fila 1 con 30 operaciones no separa 93 % de 95 % (dossier §26): se lee como aviso. Parada: cualquier fila falla → fuera, y la causa (reloj, símbolo, comisión) va a la ficha del activo, no a la estrategia. Gasta: 0 tramo, 30 operaciones de calendario, 89 € si es cuenta real de 10k.

**Etapa B, evaluación (k = 2 %).** La prueba la pone la firma: +10 % y +5 % con 10 % de pérdida máxima = 5 R de drawdown. β de la firma ≈ 0,25 con ventaja 0,10 R (P(evaluación) 0,75); α ≈ 0,74 (pasa el 25,7 % de nulas). No se añade ninguna regla propia: cualquier regla más estricta que la de la firma solo añade falsos negativos sobre una p que ya es 0,42.

**Etapa C, fondeada (k = 1 %): SPRT por operación, explícito.** Con S_n = suma de R netos de deriva (la misma `excess` del paso 8, `gate/config.yaml:57-64`):
- continuar mientras −11,2 R < S_n − 0,05·n < +14,4 R (fronteras de Wald para μ1 = 0,10, σ = 0,706, ln A = 2,89, ln B = −2,25);
- **frontera superior**: la única decisión de «más»: k sube a 1,5 % (p99 del drawdown real 10 R → 15 %, pregunta Q2);
- **frontera inferior**: retirar la estrategia y, si la celda tiene otra medoide, sustituir;
- la regla de la firma (10 % = 10 R a k = 1 %) coincide con la frontera inferior de Wald (−11,2 R bajo la línea de deriva): **la pérdida máxima de la firma ya es un SPRT con β ≈ 0,10 para μ1 = 0,10**. Se formaliza, no se inventa.
- Tasas: α = 0,05 y β = 0,10 nominales; la α realizada es menor porque la firma mata al 36,7 % de las nulas antes. Esperanza de parada: 208 operaciones con ventaja, 160 sin ella.
- Actualización bayesiana equivalente, por operación: ln O_n = ln O_0 + Σ (0,10/0,498)·(x_i − 0,05); con O_0 = 0,42/0,58 se declara «confirmada» en ln O ≥ ln 4 (p = 0,8) y «retirada» en ln O ≤ ln(1/9) (p = 0,1). Son las mismas fronteras con otra escala.

### 4.3 Qué le queda a cada paso del backtest con este protocolo

| paso | papel que le queda | papel que pierde |
|---|---|---|
| 6-7 | generar y medir oos1 | — |
| 8 | **la única criba estadística**: fija p ≈ 0,42 y el orden de entrada a las cuentas | el sorteo dev |
| 9-12 | ficha de transferencia: ordena candidatas y nombra los mercados donde **no** debe funcionar (§6) | cortar |
| 13-14 | **tamaño**: la dispersión de vecinas y OHLC da el k (p99 del drawdown) | cortar por `f_pos` |
| 15-16.5 | caja de parámetros para la cuenta: qué variante opera y cuánto ancho tiene la meseta | — |
| 17-19 | ficha de orden y de nivel en oos2 para **ordenar** las medoides de la celda | cortar (falso NO PASA 15-29 %) |
| 20 | REVISAR como etiqueta; StepM contra el trader al azar como cifra de la celda | DESCARTAR (`peor`) |
| 26 | **obligatorio** antes de cualquier cuenta: la Etapa A es el 26 en vivo | — |

---

## 5. La unidad que se opera

Hechos: 38 de 41 guardadas de una misma lógica tienen ρ semanal mediana 0,73 (≈ 2 independientes, dossier §3 d272); las 10.000 de un lote equivalen a 10-180 resultados independientes con correlación media +0,22 (d590); una sola isla del genético aporta 19 de 56 y 23 de 72 supervivientes (d590); 273 de 1.004 variantes de USATEC 1.11.277 tienen las mismas operaciones (dossier §16.5); en el 20, dos madres USDJPY comparten el 98,8 % de los días de oos2 (dossier §20).

Las tres opciones, con lo que cambia:

| unidad | qué se valida | qué se opera | cambio en la cadena | veredicto |
|---|---|---|---|---|
| una estrategia | t de una curva seleccionada entre ≈ 2-4 independientes: el máximo de 3 nulas da t ≈ 0,85 de sesgo; la t observada 1,65-2,54 (`drift_excess_t` de las 169) lleva ese sesgo | una curva, un slot | ninguno | hoy; p = 0,42 ya lo descuenta a nivel de población, no de estrategia |
| **el promedio de la celda** | la media de la celda en oos1 con n_eff por ρ (t de la serie media, no de la mejor): sin sesgo de máximo | la **medoide** de cada grupo de huella (la estrategia cuyas operaciones están más cerca de la media del grupo) | paso 8: agrupar por huella de operaciones (la `redundancia` ya agrupa por XML, solo anota) → veredicto por grupo; el sorteo dev → medoides; 13-19 solo sobre medoides; la nube del 16.5 **ya es** el promedio de la celda a nivel de parámetros | **recomendado**: cuesta 0 CPU y quita el sorteo |
| cartera de celdas | cada celda como arriba | 1 medoide por celda, k/celda | el módulo `portfolio/` dimensiona por celda; el 26 y la cuenta reciben una celda, no una estrategia | el paso siguiente cuando haya > 1 celda con p ≥ 0,15; hoy hay 1 (`campaign/ledger.jsonl`: 3 celdas, todas `Test_`) |

Diversificar dentro de la celda no paga (factor 1,16-1,25 con ρ 0,73): **una cuenta por celda, con la medoide del grupo mayor; una segunda cuenta solo si hay un segundo grupo con t de grupo ≥ 1,65.** Con 169 supervivientes de USATEC eso son 2-4 cuentas, no 169 candidatas.

---

## 6. El mecanismo

Dos plantillas de la biblioteca (`AlgoData/templates/registry.csv`, 61 plantillas, todas `draft`):

### 6.1 `squeezeBBLong` (volatility, largo, índices): bloque fijo `BBWidthRatio` + 1 hueco libre

Mecanismo: compresión de volatilidad seguida de expansión; la entrada compra la ruptura del estrechamiento. Lo que obliga a cumplir:

| predicción | dónde se mide | paso que la contrasta hoy |
|---|---|---|
| P1. La ganancia está en las 2 primeras horas de la sesión de contado (15:30-17:30 Madrid en USATEC/USA500, 09:00-11:00 en DAX40) y en días con ATR(1)/ATR(20) > 1,3; fuera de ahí, ≤ coste | `operaciones.parquet` por hora de `open_time` y régimen de ATR, tramo build | **ninguno**: el 22 (mapa condicional) se eliminó el 2026-10-11; la regla 15 prohíbe bloques de reloj, no pruebas de reloj |
| P2. Asimetría positiva: ganancia media / pérdida media > 1,5 con acierto < 50 %; MFE/MAE de las ganadoras > 1,5 | columnas `Profit/Loss`, `MAE ($)`, `MFE ($)` de la cosecha | ninguno juzga; R9b mira solo el p95 del MAE |
| P3. **No** debe funcionar en EURUSD/USDJPY en sesión asiática (reversión), ni en XAUUSD en ventanas de rango | paso 9-10, mercados «structural» de `_markets.yaml` | el 10 lo mide y **lo penaliza**: P8 falla con > 2 mercados «en contra» (`criteria.yaml:165-168`) y P3 exige z_conj ≥ 0 sobre el conjunto |
| P4. Con `ExitAfterBars1 → ∞` converge a la deriva del índice (Sobol 0,700 en `ExitAfterBars1`, USATEC 1.11.277) | exceso neto de deriva (variante `d`) frente al P/L bruto | R3 del 8 ya resta la deriva: el único paso que contrasta algo del mecanismo |
| P5. 2017 y el 2.º semestre de 2019 (baja volatilidad) deben ser planos o negativos | P/L por año en build | ninguno; R7 (homogeneidad por trimestres) castiga justo lo contrario, la heterogeneidad que el mecanismo predice |

### 6.2 `hurstMeanRevShort` (meanReversion, corto, forex): bloque fijo `HurstExponent` + 1 hueco libre

Mecanismo: H < 0,5 = antipersistencia; se vende la extensión esperando la vuelta.

| predicción | dónde se mide | paso que la contrasta hoy |
|---|---|---|
| P1. Gana en sesión asiática y mediodía de Londres; pierde los días de dato macro de alto impacto (NFP, CPI, FOMC): la pérdida media esos días debe ser peor que el resto | hora y calendario de noticias sobre `operaciones.parquet`, build | ninguno (`ea-news` filtra en el EA, no mide) |
| P2. Asimetría negativa: acierto > 55 %, ganancia media < pérdida media; MAE profundo | cosecha | R9b (`mae_p95_r ≤ 1,5`, Limbo ≤ 2,5) la **castiga** sin preguntar si es el mecanismo |
| P3. **No** debe funcionar en índices (corto contra la deriva) ni en XAUUSD 2019-2020 (tendencia); 2022 (tendencia del USD) debe ser negativo | 9-10 y P/L por año | el 10 lo penaliza (P8, P3); R7 castiga el año malo |
| P4. Debe pagar el swap negativo del corto: ventaja ≥ 2 costes con el swap de la ficha | R5c `edge_mean_oos ≥ 2` | **el 8 la contrasta** (R5c incluye swap), con la salvedad de que el swap aplicado es el de hoy (d654) |

### 6.3 La prueba que falta y lo que gasta

**Mapa condicional pre-registrado por familia, en el tramo build**: para cada plantilla, 6 celdas fijadas en su `brief.md` antes del build (3 bandas horarias × 2 regímenes de ATR, o día de noticia / no), con la predicción escrita (gana / pierde / plano) y un umbral de Bonferroni 0,05/6 sobre el exceso neto de deriva por celda. Se juzga sobre **build**, que ya está visto y no gasta tramo; coste ≈ 14 s por 10 madres (lo que costaba el 22) y 0 SQX. Se añade al 10 un vector de signo esperado por mercado: los mercados «structural» de una familia de ruptura entran como controles negativos (pasa si z ≤ 0) y P8 se invierte para ellos. Una plantilla que no cumple sus propias predicciones se queda en `draft` aunque pase el 8: ese sí es un corte barato, porque no gasta oos.

---

## 7. Valor de la información por paso

Marco: p0 = 0,42 tras el 8; G = 3.640 €/año; L ≈ 0 (−160 … +490 €). Valor de un paso que corta = −p0·FN·G + (1−p0)·(1−FPR)·L − coste; con L ≈ 0, **ningún corte posterior al 8 tiene valor positivo salvo con FN = 0**. El valor que queda es informativo: ordenar candidatas y fijar k. Coste en CPU: la corrida USATEC entera son 10.034 s = 167 min de custodio (`tiempos.md`, 2026-10-11); a cualquier coste plausible del servidor (≤ 300 €/mes ≈ 0,007 €/min) una corrida cuesta ≈ 1 €: **el CPU no es un coste**. Los costes reales son el tramo (oos2 es el único no visto: 94 filas ya consumidas en una celda), el custodio en serie (un trabajo a la vez: 8 corridas/día) y los tokens (el autopiloto lee una línea de estado; `perf/README.md` no cataloga tokens por paso: «sin cita»).

| paso | coste (custodio · tramo · tokens) | FN con ventaja 0,10 | Δp o información que aporta | valor/€ | veredicto |
|---|---|---|---|---|---|
| 8 | 4.390 s Python (`falsePositives` 4.170 s = 95 %) · oos1 · 0 | 50 % (pasa el 50,2 % de plantadas 0,10) | p: 0,014 → 0,42; LR = 51 | ≫ todo | **se queda**; el control nulo es lo más valioso de la cadena: calibra p |
| 9-10 | 34 + 21 s · oos1 de 11 mercados · 0 | ≈ 35 % (1 de 3 por P3) | LR ≈ 1 (nula seleccionada pasa 60-70 %) | ≈ 0 | pasa a ficha; P8 se invierte en controles negativos (§6) |
| 10.5-12 | 88 + 39 + 42 + 44 s · oos1 y build · 0 | 0 % | ninguna decisión (nunca corta) | 0 | ficha de hermanas; se quita del juez |
| 13-14 | 88-179 + 39 + 33 s · build y oos1 · 0 | ≥ 33 % observado (1 de 3 en 3 corridas; 9 de 9 en mc1b) | **k**: dispersión de vecinas → p99 del drawdown | alto como ficha, negativo como corte | se queda como medida; `f_pos` deja de cortar |
| 15-16 | 275 s · build y oos1 · 0 | 0 % | meseta y caja de parámetros | medio | se queda |
| 16.5 | 627 s (2 madres) · build y oos1 · 0 | 0 % | la nube = promedio de la celda a nivel de parámetros | alto | se queda; es la unidad (§5) |
| 17 | 6 s · **oos2** · 0 | 22 % (irreversible) | orden IS→OOS: ρ nunca significativa (12 de 12 neutro; banda ±0,74) | negativo como corte | marca; no corta |
| 18 | 9-32 s · todo · 0 | 15-29 % | `p_perdida` como ficha de la celda | negativo como corte, útil para ordenar | marca |
| 18.5 | 17-209 s · build y oos1 (+ oos2 ciego) · 0 | ≈ 5 % | nada mientras `cost_gap` = 0,925-1,0 | 0 hasta arreglar el repreciador | marca |
| 19 | 983-1.511 s (SQX + reapertura 575-627 s) · **oos2** · 0 | ≈ 5-13 % | L1 en oos2: 3 de 10 negativas, ninguna significativa | bajo; el más caro de la cola | marca; se corre solo para las medoides que van a cuenta |
| 20 | 15 s · oos2 · 0 | ≈ 100 % (`peor`: 16 de 16 DESCARTAR) | StepM contra el trader al azar: 0 nombradas en 10 corridas (p ≥ 0,40) | **muy negativo** | `peor` se retira; REVISAR etiqueta; el StepM se queda como cifra de la celda |
| 26 | 2-5 min · ventana propia · 0 | ≈ 10 % (fila 1 con 105 op. y 97 % de fidelidad real) | fidelidad SQX↔MT5: lo único que un backtest no puede saber de sí mismo | **el más alto después del 8** | obligatorio; filas 3b y 4 no pueden fallar a 0,1 lote (se quitan) |

Orden por valor/€: **8 ≫ 26 > 14 (como k) ≈ 16.5 > 15-16 > 18 > 17 ≈ 19 > 10 > 12 = 0 > 20 (negativo)**. No pagan su coste como cortes: 10, 12, 14, 17, 18, 19 y 20. Pagan como fichas: 14, 16.5, 18, 19. Lo que se borra: el corte `peor` del 20 y el corte del 12.

---

## 8. Equipo rojo

### 8.1 Cómo engañaría a la cadena con acceso al build y a la autoría de plantillas

1. **Elegir la plantilla después de mirar oos1.** `studies/research/memory/` guarda los resultados por celda, oos1 incluido; `researchDirector` y `ideaExpert` los leen. Una plantilla cuya condición fija es el filtro de régimen que mejor salió en oos1 de la corrida anterior llega al 8 con el oos1 ya visto. Coste para mí: 0; la cadena no lo ve porque el 8 cuenta las estrategias de un lote, no los lotes de la celda.
2. **Repetir lotes en la misma celda hasta que R3 pase.** USDJPY M30: 5 lotes, 4.880.561 generadas, 324.271 aceptadas, 41 guardadas; oos1 cribado 4 veces (19.000 → 5, 3, 3, 56). El máximo esperado de ruido en t sube de 3,86 (10.000) a 4,83 (832.299) a 5,17 (4,88 M) (dossier §5-6 d620, d271). R3 sigue en 1,65.
3. **Reutilizar el sorteo dev.** `dev.on: true, sample: 3` con `seed: null`: se relanza hasta que las tres sean las que quiero.
4. **Editar `criteria.yaml`.** 16 ediciones registradas, ningún `frozen`; el `gate.seal` solo sella el 17 (`ledger/gate.py:86-123`). Bajar R3 de 1,65 a 1,5 duplica las supervivientes y nadie lo contrasta con la nula.
5. **Explotar P3 del 10.** `z_conj` incluye V1 (el build del principal, donde la estrategia se seleccionó) y se lee en bruto (`judge_on: gross`); `net_t_pooled` en neto salió −1,7 a −4,1 en las diez de referencia y ninguna regla lo lee (dossier §10 L78, L138).
6. **Bajar el coste de la ficha.** R5c exige ventaja ≥ 2 costes; con la ficha de NIKKEI al 0,41 del spread medido, la mitad de las que pasan no pasarían al coste real.
7. **Elegir la paleta mirando qué bloques sobrevivieron en otras celdas** (103 de 575 condiciones encendidas en B5): la paleta no cuenta como ensayo.

### 8.2 La regla más fácil de sobreajustar

**R3 (`drift_excess_t ≥ 1,65`, una cola, sin corrección, `criteria.yaml:66`)**: es el 97,8 % del corte, se aplica a 3.458-7.822 estrategias por lote y a 2-5 lotes por celda, y su tasa efectiva depende del activo (1,0 % en USATEC, 15,7 % en NIKKEI H1 `aroonL_cal6`, causa no verificada, dossier §8 L891). Con el nulo del lote se calibra dentro del lote; entre lotes y entre plantillas de la misma celda no hay nada.

### 8.3 Ensayos no contados en idea → plantilla → proyecto

| eslabón | ensayos que no cuenta nadie | cifra |
|---|---|---|
| idea | pruebas del perfil de mercado y variantes por celda | 202 + 702 = 904 para DJ30 H1 largo, «aparte, sin sumar» (d115); 16.188 pruebas en el mapa |
| plantilla | plantillas probadas en la celda; huecos y grupos (2-13 bloques por hueco) | 61 plantillas; 54 líneas del ledger de campaña; 0 contadas |
| paleta | bloques encendidos por lote | 103 de 575; 0 contadas |
| build | generadas → aceptadas → guardadas | 832.299 → 47.976 → 10.000 por lote; el ledger escribe «0 → 10000» (`report.py:43,53`) |
| oos1 | lotes cribados en la misma celda | 4-5 por celda; `trials.accumulated` roto |
| criterios | ediciones de `criteria.yaml` | 16, sin `frozen` |
| oos2 | miradas | 94 filas en una celda; `gate.allow` solo frena a agentes con `ALGO_AUTONOMOUS=1` |

### 8.4 El contador y la corrección

- **Contador:** una fila por celda (activo × TF × dirección × familia) en `ledger/trials.py`, arreglado (`trials.py:40`), con seis enteros: plantillas probadas, lotes construidos, generadas acumuladas, estrategias cribadas en oos1, ediciones de `criteria.yaml` desde el último sello, miradas a oos2. Lo escribe `builder.py` al crear el proyecto y `judge.py` al juzgar. Un lote `Test_` cuenta igual que un `Trade_`.
- **Corrección, barata y ejecutable:** R3 por celda = Φ⁻¹(1 − 0,05/B) con B = lotes cribados en oos1 en esa celda: 1,65 con B = 1; 1,96 con B = 2; 2,24 con B = 4. No corrige dentro del lote (eso ya lo mide la nula del lote); corrige lo que la nula no ve. Coste: en USATEC (B = 1) nada; en USDJPY (B = 5) R3 = 2,33 y las 56 supervivientes del 5.º lote bajarían a ≈ 8.
- **Sello:** `gate.seal` extendido al 8 (hash de `criteria.yaml` por corrida en el ledger); una corrida con hash distinto del sellado no cuenta para la celda.
- **oos2 quemado:** una celda con > 3 miradas a oos2 pasa a «solo vivo»: las medoides van a la Etapa A sin más backtest. Es la única corrección que la cadena no puede deshacer editando un YAML.

---

## 9. Consenso: las preguntas de las cuatro opiniones, respondidas

El dueño pidió (2026-10-12, en la sesión) que las preguntas abiertas de las cuatro opiniones (encargo 63 §9 D-1..D-7, encargo 64 §6 D-1..D-5, tercera opinión §6 Q1..Q10 y las Q1..Q8 de este dossier) se respondieran con un consenso en vez de devolverse. Lo que sigue es ese consenso: la respuesta, la razón en una línea y quién disentía. Es la respuesta de este dossier integrando las tres anteriores; la del dueño sigue siendo la última, pero ya no hay que esperar a ella para empezar.

| tema (preguntas que cierra) | respuesta | razón | disenso |
|---|---|---|---|
| **Qué es «ventaja real» y con qué p se despliega** (D3-1, 4ª-Q7, D64-D-2) | ventaja real = **neta ≥ 2 × coste** (≈ 0,05 R/op. en USATEC; es R5c). Se dimensiona con 0,05 R (P(eval) 0,53, EV +1.650 €/año) y se despliega con **p ≥ 0,15**. El paso 8 emite una **p por estrategia** (fdr local: mezcla con F₀ = los 5.000 monos) y corta en p ≥ 0,15, ordenando por p | por debajo de 0,05 R no es desplegable (0,02 R = 1,3 R/año); StepM al 5 % nombra 0 en 10 corridas (FN ≈ 1); la tabla «R3 · StepM 5 · StepM 10 · BH 10» de D64 se corre **una vez** como documentación, no para elegir | D3 daba 0,30 para «neto > 0»; con esta definición y p ≥ 0,15 la acción es la misma |
| **R3: ≥ 0 o 1,65** (D3-4) | **1,65 en el lote, corregido por celda**: Φ⁻¹(1 − 0,05/B), B = lotes cribados en oos1 en la celda | para ≥ 0,05 R la LR es ≈ 20 (19,2 % frente a 0,98 %); con ≥ 0 la LR cae a ≈ 1,25 y toda la carga pasa a oos2 con 100 op. (potencia 25-40 %). Lo que sí se adopta de D3: **el orden por t dentro de oos1 no se usa para nada** (ρ entre mitades < 0 en 26 de 27 poblaciones): el orden lo dan la celda y la lectura de oos2 | D3 (≥ 0) |
| **Unidad** (D3-2, D64-D-3, D63-D-6, 4ª-Q5) | **la celda**; se opera la **medoide del grupo mayor** de huella de operaciones, no la mejor t | sin sesgo de máximo; la mejor t es la más frágil a vecinas (`ret_med` 1,28 en 1 de 11); ρ 0,73 hace que para la cuenta dé igual | ninguno |
| **N efectivo** (D64-D-5) | el del panel semanal que D3 ya midió (mediana 3,0; USATEC 2,1; GBPUSD 9,5); la curva de Jaccard es diagnóstico, no decisión | está medido en 27 poblaciones; el «~20» de D64 era hipótesis | ninguno |
| **`dev.on`** (D3-10, 4ª §1.5) | **se apaga ya**; `sample` pasa a ser **una medoide por grupo** de `redundancia` (que ya agrupa por XML), ≤ 4 por lote; no se espera a 5.1-5.6 | 10.000 → 3 al azar no es un criterio; la agrupación existe y solo anota | ninguno |
| **Paso 1** (D63-D-4) | **apagado**; las celdas las dan el ledger de campaña y el mecanismo (§6); el mapa se regenera a mano cuando se abre una celda nueva | 5.288 s diarios para 2 de 359 celdas, artefactos de deriva | D63 ofrecía «deriva + lista congelada» como alternativa |
| **Paso 10** (D63-D-2, D64 §1, D3-8, 4ª-Q6) | **segunda confirmación sobre V0 + V2**, z ≥ 1,65 una cola; V1 fuera de P3 (era réplica del sesgo de selección). El signo esperado por mercado va en **`_markets.yaml` por familia** (7 filas), no por plantilla; los «structural» de la familia son **controles negativos** (pasan si z ≤ 0) y P8 se invierte para ellos | V0 es la única ventana no vista; una tabla de 7 familias no obliga a autoría por plantilla | ninguno |
| **Paso 14** (D63-D-3, D64 §1, D3 §5, 4ª §7) | **no corta**. Entrega dos cifras: el **percentil de la madre entre sus 500 vecinas en oos1** (D63) y la **dispersión que fija k** (p99 del drawdown, 4ª); se informa dentro del 16.5 (D64). T2 y T3 fuera (T3 = 1,000 en 58 de 58) | el exceso build ≤ 0 (29 de 50) es sesgo de la madre, no fragilidad | ninguno |
| **La cola 17-20 y oos2** (D63-D-1, D3-7, 4ª-Q3) | **17 y 19 se funden en UNA lectura pre-registrada de oos2**: suma semanal del exceso neto de la madre contra su mono con horas, 5.000 volteos centrados, una cola, α 0,05; **una mirada por celda**, anotada en el ledger de ensayos; oos2 queda autorizado para eso y nada más. **Corta solo por signo** (z ≤ 0): FN ≈ 8 % con 0,10 R y ≈ 24 % con 0,05 R sobre 100 op.; el nivel **ordena** las medoides. **18** → columna sin veredicto. **18.5** → apagado hasta descuadre < 1 %. **`peor` del 20** → fuera; StepM del 20 → diagnóstico con semilla por madre. Celda con > 3 miradas a oos2 (USDJPY M30: 94 filas) → «solo vivo» | las tres anteriores pedían una prueba en oos2; esta dice que con L ≈ 0 ningún corte paga; el corte por signo es el más débil posible (α 0,5 sobre la nula) y lo que compra es una cuenta-año | 4ª (incluso el signo es opcional); D3 borraba 18 y 18.5 del todo |
| **Frente 1 (repreciador) o frente 2 (estadística del 8) primero** (D63-D-7, D64-D-1) | **los dos a la vez**: el 8 lee el P/L **exportado por SQX**, no repreciado, así que la mezcla, el fdr local y la tabla de StepM arrancan ya en Python; el repreciador < 1 % es condición para que **cuente** cualquier lectura de vecinas, nube u oos2 repreciado (14, 16.5, 18, 18.5) | no comparten dependencia ni CPU | D63 (frente 1 antes que todo) |
| **Reglas inertes a columnas** (D63-D-5, D3 §5.1) | **ya**: R4a, R5, R5b, R8 → columnas; **R3, R5c-t, R8 y z_mono son el mismo número** (ρ 0,89-1,00) → una sola z sobre el mono con horas; R9b queda como columna porque depende del mecanismo (§6.2) | coste 0 | ninguno |
| **Mono con horas; la planta** (D3-6, D3-3, 4ª-Q8) | el mono **con las horas de la estrategia sustituye** al uniforme (hora 0 con spread 9×). La planta va **en las operaciones**, en los tres tramos, variantes y hermanas; se añade **0,02 R neto** («lo que el generador produce») a 0,05/0,10/0,15 («lo desplegable»); no se escribe inyector en precio: los pasos que re-ejecutan en SQX quedan «no sé» y son diagnóstico | lo que cruza SQX ya no corta | ninguno |
| **Build sintético por celda** (D3-5) | **sí, una vez por celda** (no antes de cada paso 8), ≈ 40 min de custodio con K = 5, cuando no corre un workflow (regla 19) | es la única medida del sesgo de selección de la fábrica; ningún mono ha pasado por el Builder | ninguno |
| **Spread de la ficha** (D3-9, 4ª §1.2) | **el medido** (NIKKEI: 747 en Darwinex), intervalo 607-747; la ficha se corrige por la ventana (`core.assetwrite`) y un lote construido a 304 se reprecia antes de que su veredicto cuente | con R5c a 2 costes, la mitad del coste duplica la tasa de paso | ninguno |
| **¿El paso 6 lee oos1 en filtro o fitness?** (D64-D-4) | según el dossier §5-6 los filtros del build (35 op./año, PF ≥ 1, NetProfit > 0, Ret/DD ≥ 2,90 al guardar) leen el tramo **build**; oos1 solo lo lee el retest del 7. Se confirma con `sqx/inspect/dump_project.py` en la próxima corrida; si leyera oos1, el 8 pasa a oos2 | 📓 del dossier, no verificado en el `project.cfx` | — |
| **Qué cuenta y qué tamaño** (4ª-Q1, Q2) | **laboratorio de 10k primero** (4 × 89 €, Etapa A en ellas); **FTMO 2-step 100k** cuando la primera 10k valide la fidelidad; **k = 2 % en evaluación, 1 % fondeada**; subir a 1,5 % solo en la frontera superior del SPRT (+14,4 R) | la 10k tiene las mismas reglas y una décima del coste; a 1 % siempre son 2,1 años hasta el primer pago | ninguna opinión anterior trataba el fondeo |
| **Ciclo de pago de Hantec** (4ª-Q4) | 14 días (como FTMO) hasta que `fundingWatcher` lo confirme | ± 1.000 USD/año en el EV de la nula; no cambia ningún veredicto | — |

Resumen de lo que cambia mañana con este consenso, en orden de ejecución: (1) `dev.on` fuera y medoides por grupo; (2) paso 1 apagado; (3) `peor` fuera, 18.5 apagado, 18 a columna; (4) P3 sobre V0 + V2 y `_markets.yaml` con signo por familia; (5) mezcla + fdr local en el 8 con B por celda; (6) la lectura única de oos2 (17 + 19) con el mono con horas; (7) ficha de NIKKEI a 747; (8) repreciador < 1 %; (9) build sintético por celda; (10) cuatro cuentas de 10k y el SPRT de §4.2.

---

## 10. Tabla final: paso, coste, valor, veredicto

| paso | coste (custodio · tramo) | valor para la decisión de desplegar | veredicto |
|---|---|---|---|
| 1 | 5.288 s diarios · build | 2 de 359 celdas, artefactos de deriva | **apagado** (§9); las celdas las dan el ledger de campaña y el mecanismo |
| 2-5 | 0 SQX | fija plantilla y proyecto; 904 + 61 ensayos sin contar | se quedan; se cuentan (§8.4) |
| 6-7 | 2.445 s · build, oos1 | produce las 10.000 y su oos1 | se queda; el ledger escribe generadas reales, no «0 → 10000» |
| 8 | 4.390 s · oos1 | p: 0,014 → 0,42; LR 51 | **se queda**; p por estrategia (mezcla con F₀, fdr local) y corte p ≥ 0,15; R3 por celda con B; una z sobre el mono con horas; medoide por grupo; fuera el sorteo dev |
| 9-10 | 55 s · oos1 × 11 | LR ≈ 1; ordena | ficha; P8 invertido en controles negativos |
| 10.5-12 | 213 s · oos1, build | 0 (nunca corta) | ficha; fuera del juez |
| 13-14 | 160-250 s · build, oos1 | k (p99 del drawdown) | se queda como medida; `f_pos` no corta |
| 15-16 | 275 s · build, oos1 | caja de parámetros | se queda |
| 16.5 | 627 s · build, oos1 | la unidad (promedio de la celda) | se queda |
| 17 + 19 | ≈ 1.000-1.500 s (SQX) · oos2, **una mirada por celda** | la única lectura nueva: exceso neto semanal contra el mono con horas, 5.000 volteos, una cola | **fundidos** (§9); corta solo por signo (FN 8 % a 0,10 R, 24 % a 0,05); el nivel ordena las medoides |
| 18 | 9-32 s · todo | FN 15-29 %; `p_perdida` ordena | columna sin veredicto |
| 18.5 | 17-209 s · build, oos1 | 0 mientras `cost_gap` ≈ 1 | apagado hasta descuadre < 1 % |
| 20 | 15 s · oos2 | `peor`: FN ≈ 100 %; StepM 0 de 10 corridas | **`peor` fuera**; REVISAR etiqueta; StepM diagnóstico con semilla por madre |
| 21 | 6 s · oos1 | describe | se queda como ficha |
| 25 | < 1 s · oos1 | gemelo de R5c | fuera (ya lo está) |
| 26 | 2-5 min · propia | fidelidad: lo que ningún backtest sabe | **obligatorio** antes de cuenta; filas 3b y 4 fuera; Etapa A en vivo |
| nuevo: mapa pre-registrado por plantilla | 14 s · build | contrasta el mecanismo sin gastar oos | se añade; una plantilla que incumple sus predicciones no sale de `draft` |
| nuevo: SPRT fondeada | 0 · vivo | la única decisión de «más» o «fuera» con tasa de error explícita (α 0,05, β 0,10) | se añade a `portfolio/` |

---

## 11. Dónde discrepo (leídas después de la tabla: encargos 63 y 64 y la tercera opinión)

Coincido con las tres en lo central y §9 ya lo integra: el 8 es el único corte; la cola 17-20 suma errores de tipo I; una sola lectura de oos2; la unidad es la celda; paso 1 apagado; P3 sobre V0 + V2; `dev.on` fuera; `peor` fuera; mono con horas. Discrepo en:

1. **Ninguna de las tres pone dinero al falso positivo.** Las tres diseñan como si L ≫ G: StepM al 5 %, Bonferroni sobre 27 celdas, «todavía no se ha demostrado en ninguna celda» (tercera, L420-422). La tasa de la firma hace L ≈ 0 (§2.3): un falso positivo cuesta 540 € y recupera 0,257 × 2.950 USD. Con eso p* = 0,05-0,15 y la cadena ya lo supera 3-4× tras el 8. La inferencia de la tercera es correcta; su acción (seguir probando) es la cara: la prueba de la firma cuesta menos que un paso más de backtest.
2. **Tercera: 0,30 (0,15 para ≥ 2× coste) frente a mi 0,42.** Es la misma cuenta (prior × LR) con dos definiciones de ventaja y un descuento por costes y tramos que la tercera no cuantifica. Con ventaja ≥ 0,05 R la mezcla da 0,44; el descuento por «la t no persiste entre mitades» ya está dentro, porque la LR sale del control nulo, no de la t. No cambia la acción: p ≥ 0,15 en ambas.
3. **Tercera: R3 a ≥ 0.** No: LR 1,25 y toda la carga a oos2 con 100 operaciones (§9). Sí a lo que la motiva: no ordenar por t.
4. **63, 64 y tercera: StepM sobre las K madres en oos2 como la prueba.** StepM al 5 % nombra 0 en 10 corridas, y FWER sobre 2-4 apuestas independientes es Bonferroni de 4: FN ≈ 1 con 0,05 R. La lectura única de oos2 sirve para ordenar y para el signo, no para FWER.
5. **63: frente 1 antes que todo.** El 8 lee el P/L exportado por SQX; el repreciador no lo bloquea (§9).
6. **64: «~20 efectivos».** La tercera lo midió: 2,1 en USATEC. Se usa la medida.
7. **Las tres se detienen en el backtest.** Solo la tercera menciona el 26 en demo, como «la única prueba fuera de muestra que le queda» a USDJPY M30 (L361-363). Esta opinión lo extiende: el vivo no sube p (179-714 operaciones), así que el protocolo en vivo es fidelidad + la prueba de la firma + SPRT fondeada (§4), y el 26 pasa a obligatorio.
8. **Tercera: build sintético antes de cada paso 8.** Una vez por celda basta: mide la fábrica, no el lote.
9. **Tercera: borrar 18 y 18.5.** 18 queda como columna (`p_perdida` ordena las medoides a 9-32 s); 18.5 apagado, no borrado, porque será la única lectura ciega de oos2 cuando el repreciador cuadre.
10. **63 y 64 devuelven 12 preguntas; la tercera, 10.** El dueño pidió consenso: §9 las cierra todas con una respuesta y su disenso, y le deja solo el veto.
