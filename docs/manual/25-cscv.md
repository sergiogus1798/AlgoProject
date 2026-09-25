# 25. CSCV — ¿te fías de tu forma de elegir parámetros?

### Qué pregunta responde

El estudio de la página 19 te dice si **esta** superficie de parámetros aguantó fuera de muestra.
Éste responde a la pregunta de debajo, que es más útil y más incómoda: **tu manera de elegir los
parámetros, ¿escoge sistemáticamente los que van a decepcionar?**

La diferencia importa. Una correlación se mide sobre una sola partición: entrenas con 2008–2017,
compruebas con 2018–2022, y sale un número. Pero esa frontera la elegiste tú, y si la hubieras
puesto en otro sitio habría salido otra cosa. El CSCV parte la historia en doce trozos y prueba
**las 924 formas** de usar seis para elegir y seis para juzgar. En cada una elige los parámetros
como los elegirías tú, y anota en qué puesto quedaron. La proporción de veces que quedaron por
debajo de la mediana es el **PBO**, la probabilidad de sobreajuste del backtest.

Y como lo que se juzga es la *forma de elegir*, se corre tres veces cambiando solo eso. La
conclusión deja de ser «esta estrategia decae» y pasa a ser algo accionable:

> Con esta estrategia, elegir el máximo dentro de muestra falla el 30 % de las veces. Elegir el
> centro de la meseta falla el 4 %. **Cambiar de regla vale más que cambiar de estrategia.**

### Cuándo lo usas, y cuándo no

**Lo usas** después de fabricar y retestear las variantes de una estrategia madre. El pipeline lo
corre solo; a mano tiene sentido cuando quieres reexaminar un lote ya recogido, o probar qué pasa
con otra regla de selección.

**No lo usas para saber si la estrategia va a ganar dinero el año que viene.** El CSCV rompe la
cronología a propósito: mezcla trozos de 2009 con trozos de 2021 y juzga el procedimiento, no el
futuro. Lo que mira hacia delante es el holdout y el walk forward matrix de la página 14.

**No lo usas con pocas variantes.** Por debajo de unos cientos de puntos utilizables, el puesto de
lo elegido entre sus compañeros es demasiado grueso para significar nada.

**Y no lo uses para separar un 45 % de un 55 %.** Está medido: sobre paneles de puro ruido, el PBO
de un panel concreto tiene una desviación típica de **0,21**, y doce paneles idénticos en todo menos
la semilla dieron desde 0,25 hasta 0,92. El PBO distingue bien un 4 % de un 30 %; no distingue un
45 % de un 55 %.

### Antes de empezar

Tres cosas, y las tres son bloqueantes:

1. **Los costes del símbolo tienen que estar acordados.**

   ```bash
   python3 -m core.assets XAUUSD
   ```

   Si sale con código distinto de cero, para.

2. **El lote tiene que estar recogido**, es decir, la carpeta de trabajo tiene que llevar
   `metrics.parquet` y `equity.parquet`. El segundo lo escribe la etapa `equity`, que lee los
   `.sqx` reteseados del custodio. Si solo tienes `metrics.parquet`, te falta esa etapa.

3. **El custodio tiene que haber volcado su databank a disco.** Lo hace `sqx.variants.execute` al
   terminar, antes de apagar la instalación. Si lanzaste el retest a mano sin ese volcado, en disco
   habrá menos ficheros que variantes reteseadas y la matriz saldrá coja. Se ve en `equity.json`:
   `n` tiene que coincidir con `n_returned` de `ran.json`.

No toca SQX, no arranca nada y no gasta la GPU ni los 95 núcleos: es una lectura de ficheros y unos
segundos de Python. Lo puedes correr con la GUI abierta.

### Cómo se ejecuta

Dos comandos, en este orden. El primero solo hace falta una vez por lote:

```bash
python3 -m sqx.variants.equity --work ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39
python3 -m strategies.walkForwardCorrelation.pbo --work ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39
```

| flag | obligatorio | qué hace |
|---|---|---|
| `--work` | sí | la carpeta del lote. Es de donde lee y donde escribe; no hay opción de salida |
| `--blocks` | no | en cuántos trozos partir la historia, por encima de lo que diga el `config.yaml`. 12 da 924 particiones, 10 da 252 y cuesta la mitad, 16 da 12.870 |

Cuánto tarda, medido el 2026-09-23 sobre 962 variantes y 786 semanas:

| | |
|---|---|
| `equity` (leer 962 `.sqx`) | **1,5 s**, y deja 5,9 MB |
| `pbo` con 12 bloques (3 reglas × 924 particiones + agrupamiento + bootstrap) | **14 s**, 380 MB de RAM |
| `pbo --blocks 10` (las 252 particiones de antes) | **6 s** |

Los mandos están todos en `strategies/walkForwardCorrelation/config.yaml`, bloque `cscv`: el
periodo de agregación, con qué métrica se ordena (`score`), cuántos bloques, qué reglas comparar y
cuántos remuestreos. **`score` admite `sharpe` o `sortino`**, y no admite Ret/DD a propósito: el
Ret/DD crece con la longitud de la ventana (el retorno crece con el tiempo y el drawdown solo con
su raíz), así que no sirve para comparar ventanas de distinta longitud. El Deflated Sharpe sigue
siendo un Sharpe aunque ordenes por Sortino, porque está definido contra un máximo de Sharpes.

**La frontera dentro/fuera de muestra no está ahí**: sale de los tramos que `equity.json` midió
sobre las propias curvas, para que no haya dos ficheros diciendo dos fechas. Cuál de las dos se usa
lo dice `split_mode` del mismo `config.yaml` — `oos2_only` pone la frontera al empezar `oos2`,
`oos1_oos2` al empezar `oos1` (ver `19-wfc.md`).

⚠️ **El PBO NO cambia entre los dos modos, y está comprobado sobre el código**: `cscv.run` parte la
historia de sus 924 maneras y no mira nunca la frontera declarada. Lo que sí se mueve son los cuatro
números cronológicos que van al lado en el mismo informe: el **coste** de cada regla de selección,
el **Sharpe desinflado**, el **número de pruebas independientes** y el **drift**. Los cuatro se
calculan sobre `inside`/`outside`, que son justo las dos mitades que la frontera define.

### Qué produce

| ruta | qué es |
|---|---|
| `<work>/equity.parquet` | el P&L de cada variante, día a día. Una columna por variante |
| `<work>/equity.json` | cuántas curvas, cuántos días, la frontera usada y cuántas curvas no cuadran |
| `<work>/cscv.json` | todos los números, planos, para que el veredicto los lea por nombre |
| `<work>/cscv.html` | **el informe. Es esto lo que se mira** |

Los cuatro se sobrescriben al volver a correr.

### Cómo se lee el resultado

Así queda la salida real de `Strategy 17.9.39`:

```
PROGRESS 100 PBO 30% con argmax, DSR 0.66
  argmax               PBO  30.4%  percentil OOS   0.2 [0, 49]  pierde 24%
  plateau_centre       PBO   3.6%  percentil OOS  63.3 [31, 82]  pierde 3%
  random_profitable    PBO  38.6%  percentil OOS  68.3 [6, 98]  pierde 29%

479 variantes que valen 21 pruebas independientes; el orden se conserva con pendiente +0.49
```

Léelo fila a fila:

- **PBO.** Por debajo del 50 % la regla sirve; por encima, elegir así es peor que no elegir.
  `argmax` (quedarse con el mejor) falla el 30 % de las veces. `plateau_centre` (quedarse con el
  mejor después de promediar con sus vecinos) falla el 4 %. **Ésa es la conclusión del estudio.**
- **Percentil OOS.** Sobre la partición cronológica de verdad, en qué puesto quedó lo que la regla
  habría elegido. 50 es lo que da elegir a ciegas. El máximo dentro de muestra quedó en el
  **percentil 0,2**: de 479 variantes, casi la peor. El corchete es el intervalo del 95 %, y cuando
  es ancho es que el número no soporta una conclusión fina.
- **Pierde.** En qué fracción de las 924 particiones lo elegido acabó la mitad reservada en
  pérdidas. El PBO habla de puestos; esto habla de dinero.
- **Pruebas independientes.** Las 479 variantes no son 479 intentos: comparten árbol de reglas y
  casi todas sus operaciones. Agrupadas por lo parecido de sus rendimientos valen **21**. Ese
  número es el que usa el Deflated Sharpe, y de él sale el `DSR 0.66`: la probabilidad de que el
  Sharpe del mejor sea real teniendo en cuenta cuántas cosas se probaron para encontrarlo.
- **Pendiente.** Cuánto del orden dentro de muestra se conserva fuera, ajustado sobre **todas** las
  variantes. 1 sería conservarlo entero, 0 que el número de dentro no decía nada. Aquí +0,49: hay
  información, pero la mitad justa.

En la página HTML, la figura de arriba es la que se lee sin saber estadística: tres bandas, una por
regla, y cada barra cuenta particiones. **Lo rojo, a la izquierda de la raya, son las veces que la
regla eligió mal.** La banda de `plateau_centre` está casi entera a la derecha; la de `argmax`, a
caballo.

### Un ejemplo completo

```
$ python3 -m sqx.variants.equity --work ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39
PROGRESS 5 leyendo 962 .sqx de RetestOut
PROGRESS 84 900 de 962 curvas leidas
PROGRESS 92 comprobando cada curva contra lo que SQX guardo
PROGRESS 100 962 curvas x 3925 dias, 5.9 MB en 1 s, 172 con posicion abierta al final
```

Las «172 con posición abierta al final» no son un error y no bloquean nada. SQX valora a mercado una
posición que sigue abierta en la última barra, y el beneficio neto solo cuenta lo cerrado, así que
las dos cifras discrepan justo en esas variantes. El estudio descarta el último periodo por eso.

Lo que **sí** bloquea es que `mismatch` no sea 0: eso significa que las curvas no cuadran con lo que
SQX guardó en la frontera, y entonces se está leyendo el resultado equivocado del fichero.

```
$ python3 -m strategies.walkForwardCorrelation.pbo --work ~/Desktop/AlgoData/pipeline/XAUUSD/Strategy_17-9-39
PROGRESS 30 argmax: 924 particiones sobre 479 variantes
...
  argmax               PBO  30.4%  percentil OOS   0.2 [0, 49]  pierde 24%
  plateau_centre       PBO   3.6%  percentil OOS  63.3 [31, 82]  pierde 3%
-> .../cscv.html
```

Y la lectura en una frase: **en esta estrategia, la meseta es la regla y el máximo es una trampa.**

### Qué NO te dice

- **No dice si la estrategia funcionará hacia delante.** Es lo primero y lo más importante. Baraja
  la historia a propósito.
- **No dice que la estrategia sea buena.** Un PBO bajo sobre una superficie donde todo pierde
  significa que eliges de forma fiable dentro de un conjunto malo. Por eso está la columna
  «pierde»: el PBO es un puesto, no un euro.
- **No dice que `plateau_centre` sea la regla correcta siempre.** Lo dice de esta madre. El estudio
  existe precisamente para medirlo en cada una en vez de suponerlo.
- **No distingue un PBO del 45 % de uno del 55 %.** Ver «cuándo no lo usas». Por el mismo motivo,
  tampoco esperes el mismo número al cambiar de bloques: con esta misma estrategia, pasar de 10 a
  12 bloques movió el PBO de `argmax` del 41 % al 30 %, y las dos cifras dicen lo mismo.
- **El recuento de pruebas independientes es una regla, no una medición.** Está explicado en
  `strategies/walkForwardCorrelation/POSSIBLE_IMPROVEMENTS.md`, sección 6, con la alternativa.

### Si algo falla

- **`alguna curva diaria no cuadra con el beneficio que SQX guardo`** — el lector está cogiendo la
  curva equivocada del `.sqx`, o el databank del custodio ya no es el de este lote porque corrió
  otra madre por encima. Comprueba `ran.json: databank_dir`.
- **`KeyError: 'databank_dir'`** — el `ran.json` es de antes de que existiera esta etapa. Vuelve a
  correr `sqx.variants.execute`, o añade a mano la ruta del databank y el número de ficheros.
- **Salen muchas menos variantes de las que reteseaste** — el custodio no volcó a disco. Está en
  «Antes de empezar», punto 3.
