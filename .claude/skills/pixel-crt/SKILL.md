---
name: pixel-crt
description: Reproduce el pixelado y la estética de tele vieja del estilo "2027" — texto bitmap gigante detrás del sujeto, scanlines, aberración cromática, barril y bloom. Úsala cuando pidan el efecto pixelado, de CRT, de televisión antigua, de VHS o de pantalla retro en un reel de este estilo.
---

# Pixelado y tele vieja

Dos efectos distintos que la gente confunde. El primero es tipografía; el segundo, una
pantalla.

---

## 1. Texto pixelado detrás del sujeto

La palabra clave en fuente bitmap gigante, **detrás del sujeto**. En la referencia la
cabeza del presentador tapa la letra central: eso exige una **máscara del cuerpo**, no es
un texto puesto encima con opacidad.

Es el detalle que separa la copia buena de la mala. Texto delante = plantilla. Texto
detrás = composición.

### Medidas

- bloques de ≈17 px sobre 960 de ancho → **1.77 % del ancho** del lienzo
- cuerpo chartreuse `#DFE87F`, núcleo reventado a `#FFFFB3` por el bloom
- scanlines de periodo 2 px al 45 %
- aparece 2.17 s y dura 2.17 s

### Cómo se hace

```bash
# 1. la capa de texto con alfa
python3 tools/reelfx.py pixel-text ORO capas/oro.mov --dur 2.2

# 2. la máscara del sujeto
python3 tools/matte.py aroll.mp4 capas/sujeto.mov

# 3. componer: fondo < texto < sujeto recortado
python3 tools/compose.py aroll.mp4 capas/oro.mov capas/sujeto.mov salida.mp4
```

### Fuentes

Suelta una bitmap de verdad en `assets/fonts/`: **Silkscreen**, **Press Start 2P**,
**Pixelify Sans** o **VT323**. Sin ella el renderizador cae a una genérica pixelada y las
letras no tienen la forma correcta — el efecto se lee, pero no engaña.

### Cuánto

**Una** aparición por pieza, en la apertura. Dos lo abaratan.

---

## 2. Pantalla CRT

Texto incrustado en un monitor antiguo **dentro del plano**. En la referencia es un
Macintosh clásico con `2027` en pantalla, la franja arcoíris de Apple entrando por la
izquierda y `Loading… 13 %` en serif itálica sobre una barra de filete fino.

### La receta medida

| ingrediente | valor |
|---|---|
| aberración cromática | R +2 px, B −2 px (sobre 960 de ancho) |
| scanlines | periodo 2 px, opacidad 35 % |
| barril | k1 ≈ 0.08 |
| viñeta | ≈ 0.45 |
| bloom | ≈ 0.35 |

```bash
python3 tools/reelfx.py crt entrada.mp4 salida.mp4
```

### Dos trampas de ffmpeg que cuestan una tarde

Están resueltas dentro de `reelfx.py`, pero si tocas la cadena de filtros las vas a
encontrar:

1. **La máscara de scanlines hay que teselarla, no reescalarla.** Un patrón de 1×2 px
   llevado a 1080×1920 da media imagen blanca y media negra, no líneas alternas. Se nota
   como una banda horizontal a media altura.

2. **Hace falta `format=rgb24` explícito antes de cada `blend`.** Tras una cadena de
   blends la negociación de formato acaba en un formato planar y el `screen` mezcla los
   planos en otro orden: el verde se hunde y la imagen entera vira a magenta. No es
   cosmético, es obligatorio.

### Cuándo usarlo

Sobre un plano que **ya tiene** una pantalla o un objeto de época. Aplicarlo a todo el
reel lo convierte en un filtro de aplicación, que es justo lo contrario de este estilo:
aquí los efectos son acentos sobre imagen limpia.
