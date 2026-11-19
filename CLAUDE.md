# Content Strategist — sistema de montaje de reels

Reproduce el estilo de edición extraído del reel **"2027"**
([referencia](https://www.instagram.com/reels/DfyVhseRL8Z/)), medido frame a frame.

## Por dónde se empieza

Para montar una pieza, invoca la skill **`orquestador-reel`**. Sabe el orden y llama a las
especialistas. No arranques por una skill suelta: cada etapa consume lo que produce la
anterior.

Para consultar un parámetro concreto, **`reel-adn-estilo`** tiene la ficha completa.

## Las tres cosas que hay que saber antes de tocar nada

1. **El zoom vive en la transición, no en el plano.** Los planos están quietos el 85 % de
   su duración. Catorce planos de la referencia están a 0.00 %. Un Ken Burns lento y
   parejo delata la copia. `tools/motion_probe.py` lo detecta por nombre.

2. **Los cortes los manda la voz, no el beat.** Sólo el 15 % cae cerca de un golpe
   musical. Se corta en frontera de palabra. Por eso **el mapa de palabras es el cuello de
   botella**: sin voz grabada no hay montaje posible, sólo guion y plan de rodaje.

3. **Los efectos son acentos sobre imagen limpia.** El 90 % de las transiciones es corte
   seco. El flash en negativo aparece una o dos veces en toda la pieza.

## Dónde está cada cosa

```
presets/estilo-2027.json     todas las medidas, legibles por máquina
docs/analisis-reel-2027.md   el porqué de cada número, con la evidencia
docs/evidencia/              hojas de contacto y tiras de la referencia
.claude/skills/              las nueve skills propias + las tres vendorizadas
.claude/agents/              los cinco agentes paralelizables
tools/                       los renderizadores
vendor/                      earshot y rea-video, copiados (ver vendor/README.md)
```

**`presets/estilo-2027.json` es la única fuente de verdad de los parámetros.** Si cambias
un valor, cámbialo ahí: las herramientas lo leen en tiempo de ejecución.

## Las dos capacidades prestadas

En `vendor/` viven dos proyectos de terceros que cubren lo que este repo no sabía hacer solo.
Se instalan con `tools/vendor_install.sh` y traen sus propias skills, ya cargadas.

**`rea-video` mide una referencia por ti.** El ADN del reel "2027" se sacó a mano, fotograma a
fotograma, y por eso sólo hay un preset. Con `rea-video decompose` cualquier vídeo de referencia
sale desmontado plano a plano: cómo se hizo cada uno, qué lleva encima, dónde cae cada corte
contra la voz y la música, y qué haría falta para replicarlo. Es el camino para un
`presets/estilo-<loquesea>.json` nuevo sin repetir el trabajo manual. No sustituye al preset:
produce la evidencia con la que se escribe.

**`earshot` te da oídos.** Hasta ahora el audio se verificaba con números de nivel —LUFS, picos,
ducking— que dicen si la mezcla está bien puesta, no si suena bien. earshot describe un audio en
palabras, lo puntúa contra una descripción ("¿esto suena a whoosh corto y oscuro?"), distingue
una grabación real de algo sintetizado y trae un banco de 252 efectos escritos en código. La
skill `real-sound` va más allá y monta la banda sonora entera a partir de grabaciones con
licencia comprobada, que es justo lo que pide la regla de más abajo.

Dos advertencias que no conviene descubrir a mitad de un montaje:

- **La skill `rea-video` está escrita en chino.** Funciona igual y el informe sale en el idioma en
  que preguntes (`--lang es`), pero si la lees directamente, la leerás en chino.
- **La primera ejecución de cada una necesita red** para bajar sus modelos. Después, no.

Ninguna de las dos manda sobre `presets/estilo-2027.json`. Siguen siendo fuentes de evidencia:
lo que midan entra en el preset cuando alguien lo decide, no automáticamente.

## Herramientas

| herramienta | para qué |
|---|---|
| `tools/reelfx.py` | los nueve efectos: punch, invert-flash, whip, zoomblur-cut, white-card, endcard, crt, pixel-text, captions |
| `tools/motion_probe.py` | mide el movimiento real y distingue punch de Ken Burns |
| `tools/assemble.py` | monta el máster desde el plan de planos |
| `tools/render_qc.py` | audita el máster contra el preset |
| `tools/audiomix.py` | mezcla y audita el audio |
| `tools/wordmap.py` | mapa de palabras con tiempos |
| `tools/compose.py` | texto pixelado detrás del sujeto (matte + apilado) |
| `tools/vendor_refresh.sh` | recopia `vendor/` y sus skills desde los commits fijados |
| `tools/vendor_install.sh` | instala earshot y rea-video (necesita ffmpeg) |

Dependencias: `ffmpeg`, `python3` con `opencv-python-headless`, `numpy`, `Pillow`.
Las de `vendor/` se instalan aparte y están listadas en `vendor/README.md`.
Opcionales: `faster-whisper` (transcripción), `rembg` (recorte del sujeto). Sin ellas las
herramientas lo dicen y proponen alternativa; no fallan en silencio.

## Convenciones

- **Verifica midiendo, no mirando.** Todas las herramientas devuelven números; úsalos.
  No digas que una pieza cumple el estilo sin haber pasado `render_qc.py` y leído la
  salida.
- **Material sin licencia no entra.** Ni "de momento". Dilo y propón alternativa.
- **Informa con el dato y el sitio.** "El corte de 12.4 s cae en mitad de 'criterio'"
  vale; "quedó raro" no.

## Dos trampas de ffmpeg documentadas

Están resueltas dentro de `reelfx.py`. Si tocas las cadenas de filtros, reaparecen:

1. Las máscaras de scanlines hay que **teselarlas**, no reescalarlas. Un patrón de 1×2 px
   llevado a 1080×1920 da media imagen blanca y media negra, no líneas alternas.
2. Hace falta **`format=rgb24` explícito antes de cada `blend`**. Tras una cadena de
   blends la negociación acaba en planar, el `screen` cruza los planos, el verde se hunde
   y todo vira a magenta.
