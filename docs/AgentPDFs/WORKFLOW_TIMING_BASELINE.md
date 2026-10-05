# Referencia de tiempos del workflow (pasos 6 a 25), antes de optimizar

Medida la noche del 2026-10-04 al 2026-10-05 sobre el proyecto `Test_NIKKEI225_M30_simpleL_ref`: Simple Strategy, largo, NIKKEI225 M30, 1.000 estrategias construidas con tope de 20 minutos, recortadas a 10 por el sorteo de desarrollo del paso 8 (semilla 20261004). Instalación «custodian», ruta de reinicio (SQX se arranca y se para alrededor de cada paso de SQX), autopiloto con `--smoke`.

Este documento solo describe lo medido. No propone cambios.

## 1. En una frase

La referencia entera tardó **13.814 s = 230,2 min (3 h 50 min)**. SQX calculando fueron **aprox. 7.689 s = 128,2 min (56 %)** y todo lo demás **aprox. 6.125 s = 102,1 min (44 %)**.

Cómo sale: son cuatro lanzamientos del autopiloto (no uno), 1.632 + 1.088 + 10.483 + 611 = 13.814 s. SQX calculando: 1.218 + 817 + 1.940 (columna `sqx` de los tres primeros lanzamientos) + 3.374 (paso 16.5) + 76 (paso 23) + aprox. 264 (paso 24) = aprox. 7.689 s. El resto es la resta: 13.814 - 7.689 = aprox. 6.125 s.

## 2. Tabla por paso

Segundos de reloj. «SQX» es SQX calculando (de la orden de arrancar hasta «Project finished»). «Resto» es el Python del paso (estudios, juez). Los pasos 16.5, 23 y 24 llevan el reparto recuperado del log de SQX (ver sección 7); en 24 las cifras son aproximadas.

| paso | total | SQX | arranque | parada | export | copias | resto | qué hizo |
|---|---|---|---|---|---|---|---|---|
| 6+7 | 1336 | 1218 | 23 | 18 | 77 | 0 | 1 | construcción 0 → 1000 y OOS 0 → 1000 |
| 8 | 299 | 0 | 0 | 0 | 0 | 0 | 299 | estudios (295) y juez (2+2); OOS 1000 → 10 por sorteo |
| 9 | 94 | 10 | 26 | 9 | 47 | 0 | 2 | Retest Markets: 0 → 10 |
| 10 | 8 | 0 | 0 | 0 | 0 | 0 | 8 | crossmarket (Python) |
| 11 | 113 | 10 | 27 | 10 | 65 | 1 | 1 | CrossTF: 0 → 30 |
| 12 | 6 | 0 | 0 | 0 | 0 | 0 | 6 | crossTF (Python) |
| 13 | 866 | 797 | 27 | 13 | 28 | 0 | 1 | MC Retest, 7 tareas con resultado: 0 → 10 cada una (la de distancia mínima 0 → 0) |
| 14 | 5 | 0 | 0 | 0 | 0 | 0 | 5 | mcRetest (Python), tras la ingesta a mano (incidencia 2) |
| 15 | 880 | 776 | 29 | 24 | 49 | 0 | 1 | SPP en muestra y fuera de muestra: 0 → 10 cada una |
| 16 | 19 | 0 | 0 | 0 | 0 | 0 | 19 | spp (Python) |
| 16.5 | 7324 | 3374 | 248 | 1321 | 1249 | 0 | 361 (+771 de carga) | variantes de 10 madres; reparto en la sección 7 |
| 17 | 17 | 0 | 0 | 0 | 0 | 0 | 17 | wfc, 10 madres leídas a ciegas |
| 18 | 50 | 0 | 0 | 0 | 0 | 0 | 50 | cscv, 10 madres |
| 18.5 | 546 | 0 | 0 | 0 | 0 | 0 | 546 | marketSurfaces, 10 madres |
| 19 | 1348 | 1164 | 38 | 29 | 99 | 1 | 18 | WFM: 0 → 10 (resto: lectura 16 + 2) |
| 20 | 15 | 0 | 0 | 0 | 0 | 0 | 15 | blindJoint sobre el estudio (juez: sin criterio) |
| 21 | 6 | 0 | 0 | 0 | 0 | 0 | 6 | exposure, 10 madres |
| 22 | 14 | 0 | 0 | 0 | 0 | 0 | 14 | conditionalMap, 10 madres |
| 23 | 260 | 76 | 13 | 44 | 64 | 0 | 29 (+34 de carga) | estructural, 10 madres |
| 24 | 603 | aprox. 264 | aprox. 26 | aprox. 80 | 129 | 0 | aprox. 104 | stop loss, dos pasadas, 10 madres |
| 25 | 8 | 0 | 0 | 0 | 0 | 0 | 8 | edgeCost de 10 versiones; 10 finalistas |

Notas de la tabla:
- El paso 8 junta el primer lanzamiento (295 + 2) y el segundo (2).
- En 16.5, 23 y 24 la carga de bases desde archivo, el vaciado y las esperas fijas antes de lanzar (771, 34 y aprox. 70 s) se separan de «resto» porque los temporizadores no las distinguían.
- Paso 24, cuenta aproximada: por pasada, arranque 13, carga 35, SQX aprox. 74 (pasada 1) y aprox. 180-200 (pasada 2, 660 variantes), parada aprox. 40, export aprox. 64. Cifras medidas: total 603 s y export 129 s; el resto es aprox.
- Los totales por paso suman 13.817 s; la diferencia de 3 s con los 13.814 s medidos es redondeo.

## 3. Dónde se abre y se cierra SQX

En toda la referencia SQX se arrancó y se paró **29 veces cada uno**:
- 1 por cada paso de SQX con ruta de reinicio: 6+7, 9, 11, 13, 15 y 19 = 6.
- 20 en el paso 16.5 (dos por madre: un piloto de 300 variantes en `make` y la tanda de 500 en `execute`).
- 1 en el paso 23.
- 2 en el paso 24.

Además, cada exportación de operaciones lanza un proceso Java de vida corta en la otra instalación («conductor»).

Lo que cuesta cada arranque: SQX tarda unos 12 s en estar listo, pero el autopiloto le pregunta cada 10 s, así que espera 24-38 s (medido). Lo que cuesta cada parada: 9-30 s en los pasos normales (SQX guarda sus bases en disco al cerrar) y hasta 80 s en variantes.

## 4. Qué se copia y cuánto pesa

Antes de cada paso de SQX se copia la carpeta del proyecto aparte, como copia de seguridad (con 1.000 estrategias pesa 68 MB). La copia tardó unos 0,2-1 s. Después se compara y se borra. No hay otras copias.

**Aquí no se va el tiempo.** La columna «copias» suma 2 s en toda la referencia.

## 5. Exports e imports

Después de cada parada, Python exporta tres cosas: métricas (0,5-2,5 s por base), operaciones (14-21 s por base; cada una arranca un Java en el conductor) y «harvest» (14-28 s).

Bases exportadas que aparecen entre las fases más largas de cada paso:
- 6+7: Results y OOS (métricas, operaciones, harvest de Results 28 s).
- 9: Results (harvest 14 s) y OOS.
- 11: CrossTF_Input, CrossTF, CrossTF_H1 y CrossTF_H4 (14-15 s cada una).
- 13: CrossTF_Mothers (14 s).
- 15, 19: bases SPP IS y SPP OOS, más lo propio de cada paso (49 s y 99 s de export en total).
- 24: SPP IS y SPP OOS otra vez (15-16 s cada una por pasada), más la ingesta del MC Retest (1 s).

Dos hallazgos:

**(a) Las dos bases SPP se reexportaron en CADA parada después del paso 15, aunque no habían cambiado.** Unos 40 s por parada, en más de 20 paradas. Motivo: SQX vuelve a guardar un binario dentro de cada archivo de estrategia con otro orden de bytes, y la comprobación de «¿ha cambiado?» creyó que sí.

**(b) En 16.5, 23 y 24 cada parada ejecutó el export completo (aprox. 63 s)**, aunque esas ejecuciones solo escriben bases desechables que nadie lee desde el export. Suma medida: 1.249 + 64 + 129 = 1.442 s.

## 6. Esperas fijas y sondeos

- Esperar a que SQX esté listo: se pregunta cada 10 s (medido 24-38 s donde el arranque real tarda 12).
- Vigilar la ejecución: se pregunta cada 10 s.
- En cada sesión de variantes: 3-4 vaciados con una espera fija de 2 s cada uno, más 8 s fijos de asentamiento, más sondeos cada 5 s. Unos 16-20 s por sesión, unos 320 s en las 20 sesiones.
- Regla de «silencio» de 15 minutos: se niega a lanzar si alguien escribió hace poco en el log de SQX. Costó una espera de relanzamiento de unos 9 min al principio de todo, fuera del total medido.

## 7. SQX calculando frente a todo lo demás

Reparto del paso 16.5 (7.324 s, 10 madres, 20 sesiones de SQX; por madre unos 730 s, de ellos unos 337 calculando):

| concepto | s |
|---|---|
| SQX calculando | 3374 (46 %) |
| arranque hasta estar listo | 248 |
| carga de bases desde archivo, vaciado y esperas fijas antes de lanzar | 771 |
| de «Project finished» a la salida de SQX (parada y guardado) | 1321 |
| exports de Python tras cada parada (20 × aprox. 62) | 1249 |
| otro Python (equity aprox. 118, collect aprox. 42, mothertrades aprox. 15, resto de lanzamiento) | aprox. 361 |

Paso 23 (260 s): SQX 76, arranque 13, carga 34, parada 44, export 64, otro Python aprox. 29.

Por bloques:

| bloque | total s | SQX s | todo lo demás s | de qué se compone lo demás |
|---|---|---|---|---|
| construcción + OOS (6-7) | 1336 | 1218 | 118 | arranque 23, parada 18, export 77 |
| estudios en Python (8, 10, 12, 14, 16, 17, 18, 18.5, 20, 21, 22, 25) | 993 | 0 | 993 | cálculo puro de estudios; destacan 18.5 (546) y 8 (299) |
| retests cortos (9, 11) | 207 | 20 | 187 | arranque 53, parada 19, export 112, otros 3 |
| tareas largas de SQX (13, 15, 19) | 3094 | 2737 | 357 | arranque 94, parada 66, export 176, otros 21 |
| variantes (16.5) | 7324 | 3374 | 3950 | arranque, carga, parada, export y Python (tabla anterior) |
| cierre (23, 24) | 863 | aprox. 340 | aprox. 523 | arranque, carga, parada y export de cada pasada |

Los totales de los bloques suman 13.817 s (3 s de redondeo sobre 13.814).

Los tres sitios donde se concentra el tiempo que no es SQX calculando, en orden:
1. Variantes (16.5): 3.950 s (parada y guardado 1.321, export 1.249, arranque y carga 1.019, Python aprox. 361).
2. Estudios de Python: 993 s (sobre todo 18.5, 546 s, y el paso 8, 299 s).
3. Abrir, cerrar y exportar SQX en el resto de pasos de SQX (6+7, 9, 11, 13, 15, 19, 23 y 24): aprox. 1.185 s (118 + 187 + 357 + 523).

## 8. Incidencias de la referencia

1. **Paso 8, primer lanzamiento.** Con las reglas reales las 1.000 estrategias fallaron (0 supervivientes) y la ejecución terminó. La base OOS se había vaciado con el recorte, así que se repitió el paso 7 (131 s) y se añadió un modo de prueba `--smoke` (solo juzgan las reglas de «legibilidad», solo en proyectos `Test_`; commit 5a6321d). Por eso la referencia es la suma de cuatro lanzamientos, no de uno.
2. **Paso 14.** La ingesta del Monte Carlo se negó a escribir: 5 de 70 reconstrucciones de RecoveryFactor superaron su tolerancia del 0,2 % (por 1,01× a 1,22×). Su regla llama «sistemática» a una falla desde max(2, 5 % de las ejecuciones), calibrada para poblaciones grandes; con 10 estrategias salta. Es una guarda de cálculo y no se cambió: se corrió la ingesta a mano con la opción de la propia guarda (`--set recon.systematic_share=0.2`), que excluye y anota esas 5 celdas. Decisión pendiente para el dueño.
3. **Paso 24, pasada 2.** SQX abortó solo («Error while running project», una NullPointerException en su librería fastutil) con 219 de 660 variantes reprobadas. Es un fallo transitorio conocido de SQX (ficha `knowhow/sqx-drive/mcr-nullpointer-fastutil-transient.md`); el remedio es repetir el paso. El autopiloto no reintenta solo.
4. **Después de ese aborto.** El plan dio el paso 24 por hecho (existía el resultado de la pasada 1) y el paso 25 se rompió por falta del archivo de la pasada 2. La tanda a medias se movió a la carpeta de la ejecución (`paso-24-abortado`) y el 24 se repitió limpio (603 s).

Además: se hizo una repetición extra del paso 7 (`fases-oos-rerun.csv`), que no entra en el total de la referencia; es la de la incidencia 1.

## 9. Lo que NO se ha medido

- El paso 26 (MT5): fuera por decisión del dueño.
- La espera de 9 minutos del primer lanzamiento por la regla de silencio.
- El tiempo perdido en los tres relanzamientos entre incidencias: no está en los totales.
