# La cadena de montaje, probada de punta a punta

Las herramientas existían, pero nunca se había comprobado que encajaran. Se probó entera con
una voz sintética y el b-roll del repo. Esto es lo que funciona, lo que faltaba y lo que hay
que tener instalado.

## El resultado de la prueba

Pieza de 17,9 s, 14 planos, 50 palabras. `render_qc.py` sobre el máster final:

```
[  ok  ] ritmo: 14 cortes, plano mediano 1.23s (referencia 1.13s)
[ aviso] duracion: 17.9s (objetivo 60-90s)          <- es una prueba, no una pieza
[  ok  ] tarjetas blancas: 4 encontradas
[  ok  ] flash en negativo: 1 detectados
[  ok  ] linea de subtitulos: mediana y=0.504 (objetivo 0.505)
[  ok  ] dispersion horizontal: p10=0.19 p90=0.71
[  ok  ] nivel: -21.6 LUFS integrados (objetivo ~-22)

0 fallos, 1 avisos, 6 correctos
```

Y el movimiento, que `render_qc` no audita, medido aparte con `motion_probe.py`:

```
punch renderizado  -> PUNCH CORRECTO (+3.9%, solo 0% consumido al 70%) - quieto y disparado al final.
control Ken Burns  -> KEN BURNS (+9.4%, 71% consumido al 70%) - rampa repartida. NO es el estilo.
```

El detector separa los dos casos. La curva medida en t/T=0.95 da +1.65 %, y la `easeInQuart`
del preset predice 8 % × ((0.95-0.85)/0.15)⁴ = 1.58 %. Coincide.

## El orden, con los comandos

```bash
# 1. mapa de palabras desde la voz   (el cuello de botella: sin esto no hay montaje)
python3 tools/wordmap.py voz.wav --salida plan/palabras.json --idioma es

# 2. plan de subtitulos desde el mapa de palabras
python3 tools/captionplan.py plan/palabras.json --salida plan/captions.json \
    --cortes plan/planos.json --enfasis criterio --heroe oro --acento "todo:#F46963"

# 3. ensamblaje: planos + movimiento + transiciones + subtitulos + flashes
python3 tools/assemble.py --plan plan/planos.json --salida out/master.mp4 \
    --captions plan/captions.json --flashes 5.74

# 4. audio: cama continua, ducking, master a -22 LUFS
python3 tools/audiomix.py --voz voz.wav --musica cama.wav \
    --video out/master.mp4 --salida out/final.mp4

# 5. auditoria
python3 tools/render_qc.py out/final.mp4
python3 tools/motion_probe.py plano_con_punch.mp4 --curva
```

El plan de planos (paso 3) **no lo hace una herramienta**: qué imagen va sobre qué palabra es
la decisión de `broll-director`, y las escalas y el acento de los subtítulos son decisión de
guion. Lo demás es mecánico.

## Lo que faltaba y se añadió

**`tools/captionplan.py`.** Era el único salto sin herramienta: `wordmap.py` producía
`palabras.json`, `reelfx.py captions` pedía `captions.json`, y en medio no había nada. Ahora
la rejilla medida se aplica por construcción:

- La X sale de la distribución del preset (p10 0.20, mediana 0.50, p90 0.78) recorrida con una
  secuencia de van der Corput: determinista, pareja, y sin que dos palabras seguidas caigan
  juntas. Medido sobre el plan generado: p10 0.194, mediana 0.488, p90 0.762.
- Cada palabra se queda hasta que **la frase se borra de golpe**, no hasta que deja de
  pronunciarse.
- Nunca más de 4 palabras a la vez. La herramienta lo audita sola y lo dice.

Las escalas, el color de acento y la itálica se pasan por argumento: son decisiones de guion,
no se deducen del audio.

## Dos dependencias que hay que saber

**Whisper.** `wordmap.py` transcribe con `faster-whisper`. Sin él sólo convierte un SRT que ya
tengas. Instalar: `pip install faster-whisper`.

**PyAV rompe la transcripción.** `faster-whisper` decodificaba el audio con PyAV, y con PyAV
≥ 16 el `av.open(metadata_errors=...)` que usa ya no existe: revienta con
`TypeError: open() got an unexpected keyword argument`. Fijar una versión vieja tampoco vale
(`av==14.4.0` no compila en Python 3.13). **`wordmap.py` ya no pasa por ahí**: decodifica con
ffmpeg a 16 kHz mono float32 y le entrega la onda al modelo. ffmpeg ya era dependencia, así que
no añade nada y quita un punto de rotura.

## Dos cosas que conviene arreglar algún día

- **Resuelto.** `render_qc.py` contaba 4 tarjetas blancas donde el plan tenía 2. Era el b-roll
  de PNG claras disparando el detector: al rehacer el montaje con metraje real cuenta 2, que son
  las que hay.
- El `zoom acumulado` que mide `motion_probe.py` queda por debajo de lo ordenado (+3.9 % sobre
  un punch del 8 %). Es el seguimiento ORB: la mayoría de frames no se mueven y los últimos
  saltan mucho. **La clasificación es correcta**, que es para lo que sirve; la magnitud
  absoluta hay que leerla con reservas.


## El umbral de corte estaba mal calibrado

Sólo se vio al montar con metraje real. Dos montajes de la **misma estructura**, 13 cortes
reales, uno con b-roll de imágenes fijas y otro con vídeo:

| umbral | fijas | metraje |
|---|---|---|
| 0.25 ← el que había | 14 | **42** |
| 0.35 | 13 | 29 |
| **0.45** ← el nuevo | 12 | 14 |
| 0.50 | 12 | 12 |
| 0.60 | 12 | 9 |

Con imágenes fijas cualquier umbral bajo vale: entre plano y plano cambia todo de golpe y dentro
del plano no se mueve nada. Con metraje real **el movimiento interno del clip dispara el
detector** y la cuenta se triplica. 0.45 es el único valor que aguanta los dos casos, los dos a
un corte de la verdad. Es ajustable con `--umbral`.

La lección va más allá del número: **una herramienta de medición validada sólo contra material
sintético no está validada.** Esto no se podía ver hasta montar con vídeo de verdad.
