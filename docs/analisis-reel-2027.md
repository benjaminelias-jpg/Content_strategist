# Análisis forense del reel "2027"

Referencia: https://www.instagram.com/reels/DfyVhseRL8Z/
Archivo medido: copia local 960×720, 29.97 fps, 76.34 s, 2288 frames, H.264 + HE-AAC 48 kbps.

> **Sobre las medidas.** Todo lo de aquí sale de medir el archivo, no de mirarlo. Las
> posiciones van normalizadas 0–1 para que sirvan en cualquier lienzo. La copia analizada
> es 4:3; el máster original es vertical, así que las conversiones a píxeles están hechas
> sobre 1080×1920. Los agudos del audio (8–16 kHz) están aplastados por el bitrate de la
> descarga: eso es la compresión, no una decisión de mezcla.

---

## 1. El hallazgo que lo cambia todo

**El zoom no vive en el plano. Vive en la transición.**

Es lo que casi todo el mundo copia mal. Se asume un Ken Burns lento y parejo a lo largo
del plano. No es eso. Midiendo la escala acumulada frame a frame con transformadas de
similitud (ORB + RANSAC), la curva normalizada del plano 19 (14.45–15.92 s) sale así:

| avance del plano | zoom acumulado |
|---|---|
| 0.00 | 0.00 % |
| 0.09 | +3.04 % |
| 0.18 → 0.82 | **+3.84 % clavado, sin moverse** |
| 0.91 | +6.70 % |

Los dos escalones son las rampas de transición de entrada y de salida. El cuerpo del plano
está **quieto**. Los planos 17 y 24 repiten el patrón sin el escalón de entrada: planos a
0 % durante el 85 % de su duración y todo el recorrido (+6 % a +11 %) descargado en los
~5 frames previos al corte, con curva easeInQuart.

Catorce planos del reel están a **0.00 % de zoom**. El A-roll de sofá va clavado. La
energía la dan el corte y el texto, no la cámara.

Corolario práctico: si aplicas la transición `zoomblur-cut` **no** apliques además un
punch al plano. Es el mismo movimiento contado dos veces y se nota.

---

## 2. Ritmo

| dato | valor |
|---|---|
| cortes detectados (umbral 0.25) | 53 |
| cortes detectados (umbral 0.10) | 90 |
| duración media de plano | 1.44 s |
| duración mediana | 1.13 s |
| plano más corto | 0.13 s |
| plano más largo | 9.58 s |

**Los cortes los manda la voz, no el beat.** Sólo el **15 %** de los cortes (8 de 53) cae
a menos de 120 ms de un transitorio musical. Se corta en frontera de palabra o en la
respiración. Quien monte esto al compás se equivoca de sistema.

Cadencia por tramos:

- **0–8 s (apertura):** ráfaga, planos de 0.13–0.5 s.
- **desarrollo:** 0.8–2.0 s.
- **remate:** 2.5–4.0 s, el pulso baja para que aterrice la idea.

---

## 3. Tipografía

**Primaria:** neo-grotesca tipo Helvetica Now Display / Inter Display, pesos 500–700,
tracking ligeramente negativo (≈ −0.015 em). Caja baja casi siempre.

**Acento:** una serif itálica didone, una o dos palabras por pieza como mucho. Marca el
giro conceptual: *repetible*, *ia*, *Loading…*. A veces en naranja.

**Rótulo de fecha:** `NOVIEMBRE 2022.` en mayúsculas, peso 800, tracking cerrado, con
punto final, tumbado a sangre sobre el b-roll.

Alturas de caja medidas, como porcentaje del alto del lienzo:

| escala | % alto | px en 1080×1920 | font-size aprox. |
|---|---|---|---|
| normal | 4.31 % | 83 | 115 |
| énfasis | 10.85 % | 208 | 290 |
| héroe | 18.47 % | 355 | 490 |

Sombra: negra al 35 %, desenfoque ≈18 px, desplazamiento (0, 4). Despega el texto del
b-roll sin leerse como sombra.

---

## 4. La rejilla de subtítulos

Esto es la firma visual de la pieza y es contraintuitivo.

- **Línea base vertical: y = 0.505.** No es un lower-third. Las palabras viven en el
  **centro vertical** del cuadro (banda 0.40–0.60).
- **Dispersión horizontal: p10 = 0.20, mediana = 0.50, p90 = 0.78.** Las palabras **no
  van centradas**: se esparcen a lo ancho sobre esa única línea central.
- Cada palabra nueva aparece en una X distinta. Las anteriores **se quedan** en pantalla.
- Máximo 3–4 palabras simultáneas.
- La frase se borra **de golpe en el corte**, no palabra a palabra.

Medido sobre 680 blobs de texto detectados por umbral de luminancia.

---

## 5. Catálogo de transiciones

### 5.1 Flash en negativo — 6 frames
Inversión RGB **completa del compuesto, texto incluido**, mantenida en duro y cortada en
seco. Sin rampa de entrada ni de salida.

Medido en 5.74–5.94 s: frames 172–177 invertidos, corte limpio en 178. Que el texto
también se invierta demuestra que es una capa de ajuste por encima de todo, no un efecto
sobre el clip. Máximo 1–2 por pieza, para cerrar una idea antes de abrir la contraria.

### 5.2 Whip blur — 2 frames
Dos frames de desenfoque direccional fuerte (≈115°) entre dos tomas del **mismo
encuadre**, para esconder el jump cut. Medido en 32.53–32.60 s.

### 5.3 Corte con zoom + blur
El plano saliente acelera el zoom (+7 %) y se desenfoca; el entrante nace desenfocado y
resuelve a nítido. ~5 frames a cada lado, easeInQuart a la salida y easeOutQuart a la
entrada. Medido en 13.55 s y 14.45 s. **Aquí es donde vive el zoom de la pieza.**

### 5.4 Tarjeta blanca
No es un flash: **se sostiene**. Blanco puro (#FDFDFD), texto negro pequeño en la línea
central, corte en duro a la entrada y a la salida. Duraciones medidas: 0.47 s, 0.67 s y
1.73 s. Aparece a los 17.58 s, 25.36 s y 60.33 s. Es el respiro: baja el pulso antes de
volver a subir.

### 5.5 Corte seco
El 90 % restante. Sin nada.

### 5.6 El orden de capas no es el mismo para todos los efectos
Dos efectos se comportan al revés y conviene no confundirlos:

- El **flash en negativo** va **por encima del texto**: en 5.74–5.94 s los subtítulos se
  invierten con la imagen. Es una capa de ajuste sobre todo el compuesto.
- La **transición de 29.96 s** va **por debajo del texto**: el subtítulo "generadas" se
  mantiene nítido mientras la imagen se degrada.

Si inviertes sólo el clip, o degradas también el texto, ninguno de los dos se parece.

### 5.7 El cambio de personaje (29.96 s) — receta no determinada
A los 29.96 s el presentador se transforma en un **alter ego disfrazado** (peluca blanca
de tazón, gafas de sol, bigote, auriculares) sentado en el mismo sofá. Es rodaje propio
interpretando un personaje, no b-roll.

El corte se escapa al umbral 0.25 y sólo aparece bajando a 0.10, porque la sala y el
encuadre no cambian. La transición ocupa 2 frames.

**No pude determinar la receta exacta**, y conviene decirlo en vez de inventarla. Lo
medido:

- no es mosaico: el error de reconstrucción crece de forma monótona con el tamaño de
  bloque, sin mínimo en ninguno — si hubiera una rejilla de píxeles, habría un mínimo claro
- no es un fundido lineal limpio: el mejor alfa es **0.25 en los dos frames**, cuando un
  fundido debería rampar (0.33 → 0.67), y el error residual sigue siendo de ~10 niveles
- lo "blocoso" que se ve a simple vista es compatible con **macrobloqueo del códec**: la
  copia analizada va a 750 kbps y una transición de 2 frames entre dos imágenes muy
  distintas es justo lo que peor encaja un encoder

Para reproducirlo, lo más cercano del toolkit es `whip` con fuerza baja: mezcla las dos
tomas y las ablanda, que es lo que se observa. Sobre un máster sin comprimir se podría
medir bien; sobre esta copia, no.

---

## 6. Pixelado y tele vieja

### Texto pixelado tras el sujeto
La palabra clave en fuente bitmap gigante, **detrás del sujeto** — su cabeza tapa la letra
central, lo que exige máscara del cuerpo. Bloques de ≈17 px sobre 960 de ancho (1.77 % del
ancho). Color cuerpo chartreuse ≈ `#DFE87F`, núcleo reventado a `#FFFFB3` por el bloom.
Scanlines de periodo 2 px al 45 %. Aparece de 2.17 a 4.34 s.

### Pantalla CRT
Texto incrustado en un monitor antiguo dentro del plano (0–2.17 s). La receta medida:

- aberración cromática: R desplazado +2 px, B desplazado −2 px (sobre 960 de ancho)
- scanlines de periodo 2 px al 35 %
- distorsión de barril k1 ≈ 0.08
- viñeta ≈ 0.45
- bloom ≈ 0.35

En la pantalla conviven `2027` en grotesca pesada con separación RGB visible, la franja
arcoíris de Apple entrando por la izquierda, y `Loading… 13 %` en serif itálica sobre una
barra de progreso de filete fino.

---

## 7. Audio

- **Cama musical continua**, sin un solo hueco hasta 75.68 s. Graves dominantes: la banda
  20–120 Hz supera a la de voz en 9 de los 10 bloques analizados.
- **La música sostiene, no marca.** Nunca compite con la voz, y los cortes la ignoran.
- Voz entre −25.4 y −21.9 dBFS. El máster ronda −22 LUFS integrados.
- Últimos 0.64 s en silencio, bajo la tarjeta final.

---

## 8. Inventario de b-roll

Reparto aproximado: **55 % A-roll, 45 % b-roll.**

| familia | ejemplos en la pieza | para qué sirve |
|---|---|---|
| archivo real | foto de la primera promoción de Y Combinator, entrevista de Sam Altman, tuit del millón de usuarios | ancla la afirmación en un hecho verificable — **o eso aparenta: ver §11** |
| captura de pantalla | UI de ChatGPT en navegador, selección de texto con el cursor a la vista | prueba de primera mano, se graba uno mismo |
| macro / textura | hoja, reloj, ojo con código reflejado | metáfora para conceptos que no tienen imagen |
| humano a escala | figura ante un lago, mujer caminando por un sendero | puerta emocional antes del remate |
| objeto de época | Macintosh clásico con CRT | sitúa la pieza en el tiempo desde el primer frame |
| **el propio autor como personaje** | el alter ego disfrazado de 29.96 s | rompe el A-roll sin salir del set, y no cuesta nada: es él mismo |

**La regla de oro:** cada b-roll entra sobre **una palabra concreta**, no sobre una frase.
Si la palabra no tiene imagen, va tarjeta blanca.

Un detalle revelador: en la captura de pantalla se ve el dock del autor con **Premiere Pro
y After Effects** abiertos. Ese es el toolchain real de la pieza.

### Qué hay que conseguir para reproducirlo

Lo que en la referencia es archivo real **no se puede clonar**: hay que sustituirlo por el
equivalente del tema propio. El resto se consigue así:

- **Archivo real:** material con licencia o de fuente citable. No tomes fotos de prensa sin
  licencia para una pieza comercial.
- **Capturas:** grábalas tú. Es lo más barato y lo más creíble.
- **Macro y textura:** bancos con licencia permisiva (Pexels, Unsplash, Artgrid) o
  generación. Son planos sin cara, fáciles de sustituir.
- **Humano a escala:** banco o rodaje propio.
- **Objeto de época:** generación o banco.

---

## 9. Cierre

Diana concéntrica blanca (#D8D8D8) sobre negro, centrada, ≈14 % del ancho, 2.87 s, en
silencio y casi inmóvil.

---

## 10. Mapa de planos

Texto de subtítulo muestreado a 1 fps, así que faltan palabras intermedias. Los tiempos de
corte sí son exactos.

| t | plano | texto visible |
|---|---|---|
| 0.00 | Macintosh CRT | en 2027 · el criterio · se |
| 2.17 | A-roll + pixel ORO | va a volver en oro · para los creadores |
| 4.34 | macro de hoja | todos sabemos que la inteligencia artificial |
| 5.74 | **flash en negativo** | — |
| 5.94 | ojo con código | está cambiando **todo** |
| 7.21 | carretera cenital | en redes sociales |
| 8.01 | semitono de puntos ámbar | cada día |
| 8.41 | ciudad barrida | — |
| 8.94 | reloj antiguo, marca "FESTA" | estamos viviendo |
| 10.28 | A-roll | sin precedentes |
| 12.48 | foto 1ª promoción de Y Combinator, 2005 (**no** OpenAI) | NOVIEMBRE 2022. |
| 13.55 | **zoom + blur** | — |
| 14.45 | Sam Altman | lanza ChatGPT |
| 15.92 | UI de ChatGPT | una herramienta que puso |
| 17.58 | **tarjeta blanca** | en manos de cualquiera · la capacidad |
| 18.05 | A-roll | crear y producir antes |
| 20.75 | A-roll | habíamos visto |
| 21.89 | jet privado | y en tan solo cinco días |
| 23.52 | tuit | crossed 1 million users! |
| 25.36 | **tarjeta blanca** | hoy en día la *ia* |
| 26.09 | texto desenfocado | escribe guiones |
| 26.76 | diseño sobre papel | diseña |
| 27.36 | A-roll | incluso · personas |
| 28.36 | A-roll | creando contenido · generadas |
| 29.96 | **transición blanda de 2f** → alter ego disfrazado | inteligencia |
| 32.53 | **whip blur** | — |
| 32.60 | A-roll | y ojo · pero esto generó un **nuevo** problema |
| 35.87 | interior acristalado | el hacer cualquier |
| 37.97 | lago al atardecer | hacer deja de ser *difícil* |
| 39.74 | A-roll | se · *repetible* |
| 43.28 | manos en teclado | Elegir · cómo |
| 45.65 | retrato / teclado / cámara | historia · vídeo · cámara |
| 47.81 | A-roll largo | querés · eso · que es más rápido |
| 57.39 | coche y ciudad | Porque · a · te |
| 60.33 | **tarjeta blanca** | no · publique · porque |
| 62.06 | A-roll | su · las |
| 64.00 | sendero en bosque | generación · no · hacer · **más** |
| 67.50 | A-roll | elegir · Entonces |
| 69.30 | A-roll | puede · cualquier · vos |
| 73.47 | **cierre** | ◎ |

---

## Evidencia

Las hojas de contacto y las tiras frame a frame que sostienen todo esto están en
`docs/evidencia/`:

- `sheet_0..3.png` — el reel entero muestreado a 1 fps
- `strip8.png` — el flash en negativo, frame a frame
- `strip17.png` — la transición de zoom + blur
- `strip_invert2.png` — el whip blur de 2 frames
- `broll.png` — las familias de b-roll
- `endcard.png` — el cierre
- `broll_catalogo.png` — los 21 planos de b-roll, etiquetados P00–P20
- `cut30.png` — el cambio de personaje de 29.96 s, frame a frame
- `pixelcut.png` — los 2 frames de esa transición, a resolución completa

---

## 11. Procedencia del b-roll

Investigación posterior sobre los 21 planos de b-roll. Trajo dos correcciones a lo que yo
mismo había afirmado antes en este documento, y un problema de licencia que conviene
mirar antes de imitar nada.

> **Cobertura incompleta, y hay que decirlo.** La investigación corrió como tres etapas
> encadenadas —identificar, refutar, buscar sustituto— y el límite de uso cortó **34 de
> los 54 agentes**. Se completaron 20 de 21 identificaciones; las etapas de **refutación
> adversarial y de sustitución no llegaron a correr**. Por eso el recuento automático dice
> "0 refutados" y "0 no reutilizables": no es un hallazgo, es una etapa que no se ejecutó.
> Lo de abajo son identificaciones **sin contrastar por un segundo agente**, salvo donde
> se indica que lo verifiqué yo.

### 11.1 La foto no es de OpenAI

Lo di por hecho y estaba equivocado. La foto de grupo de 12.48 s es la **primera promoción
de Y Combinator**, el Summer Founders Program de 2005, en Cambridge (Massachusetts). En
ella están Jessica Livingston, un **Sam Altman de 20 años** y Aaron Swartz. El cotejo fue
prenda a prenda y persona a persona contra la copia publicada, no parecido temático.

El rótulo de la pieza dice `NOVIEMBRE 2022.` sobre una foto de **2005**: 17 años de
desfase, y sugiere que son empleados de OpenAI. El único vínculo real con OpenAI es que
Altman sale en la foto.

Autoría y licencia **no establecidas**: circula como repost sin crédito. Hay otra foto
distinta de la misma promoción (todos sentados a la mesa) acreditada a Alex Lewin, pero
esa atribución **no se puede trasladar** a esta toma.

### 11.2 El bloque de 21.9–23.5 s es cine comercial con copyright

Lo que yo había leído como "jet privado + evento" no es un plano: son **cinco microcortes
de ~0.3 s**, y los cinco salen de la misma película — **"Artificial" (2026)**, dirigida por
Luca Guadagnino, sobre la crisis de OpenAI de noviembre de 2023, distribuida por **NEON**.

La identificación fue fotograma contra fotograma: los cinco microplanos coinciden con
cinco stills promocionales distintos (el jet, la cena de equipo, la camiseta con el logo
de OpenAI, la "Q" roja sobre cristal y el corte de cinta).

**Esto no se puede licenciar como stock.** Es metraje de una película comercial. Usarlo en
una pieza propia monetizada es infracción salvo amparo de cita, que es una decisión
jurídica del usuario y no una licencia. Si tu pieza se monetiza, sustitúyelo.

### 11.3 El reel tiene tres días, no es de 2024

**Verificado de forma independiente.** El shortcode de Instagram `DfyVhseRL8Z` decodifica
en base64 al id `4031379290921942809`; desplazado 23 bits y sumada la época de Instagram
da **2026-11-16 02:58 UTC**.

Eso recontextualiza la pieza entera: no es un ensayo atemporal sobre IA, es contenido
montado sobre la **campaña de lanzamiento** de una película que se estrena en diciembre de
2026.

### 11.4 El Macintosh de apertura está generado con IA

Confianza alta, y la prueba está en el logo. El distintivo del frontal es un **disco
circular con bandas en orden espectral** (rojo, naranja, amarillo, verde, azul, violeta).
El logo arcoíris de Apple es una **silueta de manzana** y su orden es deliberadamente **no
espectral** —verde arriba, luego amarillo, naranja, rojo, morado, azul—. Fallan a la vez
la forma y el orden. Ningún Macintosh llevó nunca un roundel circular.

Se suma: proporciones que no corresponden a ningún modelo real, ausencia del mando de
brillo, una fila de pseudo-iconos bajo el "2027" que **cambia entre el frame de 0 s y el
de 1 s**, y texto selectivamente ilegible junto a un filete nítido del mismo tamaño —
firma generativa.

**Riesgo de marca aparte del de copyright:** el plano muestra un arcoíris deformado sobre
un objeto reconocible como Apple. Eso es un problema por sí mismo en una pieza comercial.

### 11.5 El resto

| id | t | naturaleza | confianza |
|---|---|---|---|
| P00 | 0.00–2.17 | generado con IA | alta |
| P01 | 4.34–5.74 | stock — **macro de hoja verde**, no superficie marrón (ver abajo) | baja |
| P02 | 5.94–7.21 | stock, ojo con código | media |
| P03–P06 | 7.21–10.28 | no identificados | ninguna |
| P07 | 12.48–13.55 | archivo real: YC 2005 | alta |
| P08 | 14.45–15.92 | entrevista de Sam Altman, clip concreto no identificado | ninguna |
| P09 | 15.92–17.48 | captura propia de ChatGPT | alta |
| P10 | 21.89–23.52 | película "Artificial" (2026), NEON | alta |
| P11 | 23.52–25.36 | captura del tuit de Altman | alta |
| P12–P13 | 26.09–27.36 | no identificados | ninguna |
| P14 | ~29.9–30.5 | rodaje propio: el autor disfrazado | alta |
| P15–P16 | 35.87–39.74 | stock / no identificado | baja |
| P17–P18 | 43.28–47.81 | rodaje propio | baja / media |
| P20 | 64.00–67.50 | stock genérico | media |

**Corrección sobre P01:** no es una superficie marrón granulada. Es un **macro de hoja
verde** con nervaduras reticuladas y una mancha clorótica. Lo marrón es el propio grade
cálido del reel en la entrada del plano, que vira a verde pleno hacia los 5.0 s antes del
flash en negativo. Son tres aspectos del mismo plano, no tres materiales.

### 11.6 Qué significa esto si quieres imitar la pieza

La familia que yo llamé "archivo real" y presenté como lo que **ancla la afirmación en un
hecho verificable** resulta ser, en esta pieza: una foto de 2005 rotulada con una fecha de
2022, cine de ficción presentado como material de archivo, y un Macintosh generado que
nunca existió.

El recurso retórico funciona —por eso la pieza convence—, pero **funciona porque el
espectador asume documentación donde hay atrezo**. Reprodúcelo con el equivalente real de
tu tema, no copiando el material ajeno: el de la referencia tiene a la vez un problema de
copyright, uno de marca y uno de veracidad.
