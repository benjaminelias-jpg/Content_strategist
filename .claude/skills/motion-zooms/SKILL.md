---
name: motion-zooms
description: Aplica el movimiento de cámara del estilo "2027" — punch zoom con curva de velocidad, reposo de plano y rampas. Úsala cuando haya que decidir o renderizar zooms, escalas, curvas de velocidad o movimiento de planos en un reel de este estilo.
---

# Movimiento y curvas de velocidad

## Lo primero, porque casi todo el mundo lo hace al revés

**El zoom no vive en el plano. Vive en la transición.**

Medido sobre la referencia: catorce planos están a **0.00 %** de zoom. El A-roll va
clavado. Los planos que sí se mueven están quietos el **85 %** de su duración y descargan
todo el recorrido (+6 % a +11 %) en los **~5 frames previos al corte**, con easeInQuart.

La curva del plano 19 lo deja claro:

| avance | zoom |
|---|---|
| 0.00 | 0.00 % |
| 0.09 | +3.04 % |
| 0.18 → 0.82 | +3.84 % **sin moverse** |
| 0.91 | +6.70 % |

Los escalones de los extremos son las rampas de transición. El cuerpo está parado.

**Un Ken Burns lento y parejo a lo largo del plano es la firma de que copiaste el estilo
sin medirlo.** No lo hagas.

## Las tres situaciones

### 1. A-roll de sofá → cero movimiento
Nada. Ni un 1 %. La energía la dan el corte y el texto.

### 2. Imagen fija o plano sin movimiento propio → punch de salida
Quieto y descarga al final:

```bash
python3 tools/reelfx.py punch entrada.mp4 salida.mp4 --pct 7 --reposo 0.85
```

- `--pct` entre 6 y 11. Por encima de 11 se nota el truco.
- `--reposo` 0.85. Es la fracción del plano que pasa inmóvil.

**Si este plano ya va a llevar `zoomblur-cut` en su salida, no le pongas punch.** Es el
mismo movimiento dos veces.

### 3. Plano de 0.3 s o menos → ráfaga
Zoom continuo y acelerado, sin reposo: +5.85 % en 0.2 s con easeInCubic.

```bash
python3 tools/reelfx.py punch rafaga.mp4 salida.mp4 --pct 5.85 --reposo 0
```

## B-roll que ya se mueve

El b-roll generado o de banco llega con su propio dolly o drone — hasta un −55 % de
recorrido en la referencia. **No le añadas zoom encima.** Se elige por su movimiento, y si
no sirve, se cambia el clip.

Para saber si un clip ya se mueve, mídelo en vez de mirarlo:

```bash
python3 tools/motion_probe.py clip.mp4
```

## Cómo comprobar que salió bien

Renderiza y vuelve a medir. La escala acumulada debe quedarse plana y dispararse al final:

```bash
python3 tools/motion_probe.py salida.mp4 --curva
```

Sobre sujetos en movimiento la medida trae ~1 punto porcentual de ruido; eso es normal.
Lo que no es normal es una rampa recta de principio a fin: eso es Ken Burns y hay que
rehacerlo.
