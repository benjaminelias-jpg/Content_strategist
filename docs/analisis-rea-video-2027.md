# Segunda medición del reel "2027", con rea-video

El reel se volvió a desmontar con `rea-video` sobre el mismo material que usó el análisis
original. Este documento recoge **dónde las dos mediciones coinciden**, dónde la herramienta
se equivoca, y las cuatro cosas que no estaban medidas antes.

No sustituye a `docs/analisis-reel-2027.md` ni al preset: los corrige en tres puntos y
confirma el resto.

## De dónde sale el material

`media/ref/reel-2027.mp4` — 76,343 s, 2288 frames, 29,97 fps, 1440×1080.

Instagram no sirve el vertical sin sesión: las cuatro variantes disponibles son 4:3, un
recorte centrado. **La hoja de contacto del análisis original también es 4:3**, así que las
dos mediciones corren sobre la misma fuente y son comparables. El `1080×1920` del preset es
el lienzo de salida, no el de la referencia. Consecuencia que conviene tener presente: las
medidas verticales (la línea de subtítulos en 0.505, las escalas de caja) están tomadas sobre
un encuadre al que le faltan la parte alta y la baja.

El vídeo está en `.gitignore` y no se versiona.

## Lo que la segunda medición confirma

| parámetro | preset | rea-video | |
|---|---|---|---|
| proporción de cortes secos | 0.90 | 6 transiciones no-corte de 61 → **0.90** | ✅ |
| tarjetas blancas | 17.58 / 25.36 / 60.33 s | 17.58 / 25.36 / 60.33 s | ✅ |
| cortes totales | 53 | 61 planos detectados, 62 tras revisión | ≈ |
| duración media de plano | 1.44 s | 1.231 s | ≈ |
| reparto A-roll / B-roll | 55 / 45 | 68,7 % imagen real (A-roll + b-roll real) | ✅ |
| cortes sobre golpe musical | «sólo el 15 %» | **20 %, cuando el azar da 19 %** | ✅ |
| color de bloom del texto pixelado | `#FFFFB3` | medido `#FCFEB2` | ✅ |
| scanlines del texto pixelado | periodo 2 px | periodo 2 px (ampliación ×6) | ✅ |

La fila que más vale es la de los cortes contra el beat. El `CLAUDE.md` afirma que en esta
pieza manda la voz y no la música. rea-video lo mide por su cuenta: **20 % de los cortes caen
en un golpe, y el azar daría 19 %**. Es decir, no hay relación. La afirmación queda probada,
no asumida.

## Lo que la herramienta dice mal

**rea-video clasifica 16 de los 22 planos de busto parlante como "AI video" al 70 %.** Son el
mismo montaje —mismo sofá, misma camiseta, mismo reloj— que en otros seis planos puntúa como
*live action* al 95–98 %. La única prueba que aporta es la cadencia 24p→30p, que el propio
programa documenta como no concluyente: «AI y cámara real a 24p dan lo mismo».

El veredicto automático sale por tanto muy escorado:

| | rea-video | tras revisión visual |
|---|---|---|
| imagen real | 20 % | **68,7 %** |
| vídeo generado con IA | 44 % | 8,9 % |

El 68,7 % cuadra con el 55 % de A-roll que ya tenía medido el preset más el b-roll que también
es metraje real. **La cifra buena es la de la revisión.** Quedan 23 planos marcados como
`disputed` en `out/ref-2027/video/timeline.md`.

## Las cuatro cosas nuevas

### 1. Hay dos whip blur, no uno

- **31,20–31,30 s** (frames 936-937): tapa el paso del personaje disfrazado al presentador.
- **32,53–32,60 s** (frames 975-976): tapa un jump cut dentro del propio metraje del presentador.

El preset documentaba sólo el segundo; rea-video detecta sólo el primero. Los dos existen y
se ven extrayendo los frames.

### 2. El flash en negativo son dos efectos distintos, y el preset los tenía cruzados

El preset decía «inversión RGB completa» y lo fechaba en 5,74–5,94 s. Midiendo canal a canal
contra un frame limpio del mismo plano:

| tramo | R | G | B | luma | qué es |
|---|---|---|---|---|---|
| 5,07–5,44 s | corr −0.83 pend −0.91 | −0.81 / −1.15 | −0.83 / −0.77 | **invertida** | inversión RGB completa |
| 5,74–5,94 s | corr +0.10 pend **+0.03** | +0.86 / +0.97 | +0.92 / +0.84 | **conservada** | canal rojo anulado |

La descripción del preset («inversión completa») corresponde al evento de 5,07 s. Lo que hay
en 5,74 s —el que el preset fechaba— **conserva la luminancia**, por eso no se lee como un
negativo: el crema vira a cian y el verde a granate.

Receta exacta del segundo, por mínimos cuadrados:

```
R = 0.03 * v + 34      (R² 0.009 — el canal queda aplanado)
G = 0.97 * v - 77      (R² 0.742)
B = 0.84 * v +  8      (R² 0.853)
```

Aplicada a un frame limpio **reproduce el frame real con 0,8–1,4 sobre 255 de diferencia por
canal**. Está implementada en `tools/reelfx.py invert-flash --variante rojo`; la inversión
completa sigue en `--variante rgb`.

### 3. Entre 4,5 y 5,94 s no hay cuatro planos: hay uno

Un detector de cortes ve cuatro. Correlación de luma contra el frame limpio de la hoja (168):

| t | correlación | lectura |
|---|---|---|
| 4,54 s | 0.87 invertida | mismo material, invertido |
| 4,84 s | 0.12 | **material distinto** (control) |
| 5,11 s | 0.82 invertida | mismo material, invertido |
| 5,51 s | 0.95 directa | mismo material, limpio |
| 5,81 s | 0.85 directa | mismo material, canal rojo anulado |

Es **un solo macro de hoja verde** con tratamientos de canal encima. El control de 4,84 s
—una imagen azul con líneas, genuinamente distinta— da 0.12, que es lo que valida el método.

Para quien monte una pieza nueva esto cambia el presupuesto: un tramo así cuesta **un clip**,
no cuatro. El ritmo sale del tratamiento, no de conseguir más material.

### 4. El sonido, medido

- **143,6 BPM**, fa mayor (confianza 0.88), música en el 56 % de la duración (0,5–75,5 s).
- Cambios de sección en **31,5 / 52,5 / 71,5 s**.
- Sonoridad −17,4 dBFS, pico −0,0 dBFS. El fondo corre por encima de los cortes: la cama es
  continua y se pone en post.
- **20 golpes de efecto, 8 sonidos distintos.** El más usado es un *ding* que suena 10 veces,
  siempre sobre un corte: 7,0 / 12,4 / 17,3 / 19,5 / 20,1 / 25,3 / 28,0 / 32,6 / 47,2 / 49,7 s.

Una advertencia: rea-video puntúa la voz como **TTS al 64 %**. Es casi con seguridad falso —se
ve al presentador hablando sincronizado en cámara—. La herramienta lo deduce de que la voz
cruza los cortes, que es sólo señal de que la cama de audio es continua.

## Qué se cambió en el repo

- `presets/estilo-2027.json` → versión `1.0.0+medicion-rea-video`: `flash_negativo` pasa a
  tener dos variantes con su receta y su medición; `whip_blur` recoge las dos apariciones;
  `broll` gana `planos_que_son_el_mismo_material`.
- `tools/reelfx.py` → `invert-flash` acepta `--variante rgb|rojo`.
- `CLAUDE.md` → tercera trampa de ffmpeg documentada (`geq` contra `lutrgb`).

## Lo que sigue sin resolver

- Los planos b-roll **P03–P06 y P12–P13 siguen sin identificar**, igual que en el análisis
  original.
- La fuente tipográfica exacta no se puede medir desde el píxel: el preset propone
  Helvetica Now Display y alternativas libres, y eso sigue siendo una hipótesis.
- El OCR no corrió (falta `rapidocr`), así que la capa de texto se midió por posición, color
  y altura de caja, pero no se transcribió palabra por palabra.
- **El b-roll de la referencia no es reutilizable.** Ver `docs/analisis-reel-2027.md` §11:
  metraje de una película comercial, una foto sin licencia establecida y un objeto generado
  con una marca reconocible deformada.
