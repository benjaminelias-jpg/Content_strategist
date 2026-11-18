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
| archivo real | foto del equipo de OpenAI, entrevista de Sam Altman, tuit del millón de usuarios | ancla la afirmación en un hecho verificable |
| captura de pantalla | UI de ChatGPT en navegador, selección de texto con el cursor a la vista | prueba de primera mano, se graba uno mismo |
| macro / textura | hoja, reloj, ojo con código reflejado | metáfora para conceptos que no tienen imagen |
| humano a escala | figura ante un lago, mujer caminando por un sendero | puerta emocional antes del remate |
| objeto de época | Macintosh clásico con CRT | sitúa la pieza en el tiempo desde el primer frame |

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
| 8.01 | ciudad barrida | cada día |
| 8.41 | reloj | estamos viviendo |
| 10.28 | A-roll | sin precedentes |
| 12.48 | foto equipo OpenAI | NOVIEMBRE 2022. |
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
| 28.36 | A-roll | creando contenido |
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
