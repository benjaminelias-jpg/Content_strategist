---
name: transiciones-fx
description: Aplica las transiciones del estilo "2027" — flash en negativo, whip blur, corte con zoom y blur, y tarjeta blanca. Úsala cuando haya que resolver el paso entre planos, esconder un jump cut o marcar un cambio de bloque narrativo en un reel de este estilo.
---

# Transiciones

Cuatro recursos y un 90 % de corte seco. Ese reparto importa: la pieza se sostiene por el
corte limpio, y los efectos son acentos. Si los usas en cada corte dejan de significar
nada.

## 1. Corte seco — el 90 %
Sin nada. Es la opción por defecto. Pregúntate siempre primero si el corte seco basta.

## 2. Corte con zoom y blur
**Aquí es donde vive el zoom de la pieza.** El plano saliente acelera (+7 %) y se
desenfoca; el entrante nace desenfocado y resuelve a nítido. ~5 frames a cada lado.

```bash
python3 tools/reelfx.py zoomblur-cut saliente.mp4 entrante.mp4 salida.mp4 \
  --f-out 5 --f-in 5 --zoom-pct 7
```

**Cuándo:** cambio de bloque narrativo o salto temporal.
**Ojo:** los planos que toca esta transición no llevan punch propio.

## 3. Flash en negativo — 6 frames
Inversión RGB **completa del compuesto, texto incluido**, en duro y cortada en seco. Sin
rampas.

```bash
python3 tools/reelfx.py invert-flash montaje.mp4 salida.mp4 --at 5.74 --frames 6
```

Que el texto también se invierta no es un descuido: es una capa de ajuste por encima de
todo. Si lo aplicas sólo al clip, el efecto no se parece.

**Cuándo:** cerrar una idea justo antes de abrir la contraria.
**Cuánto:** 1–2 veces en toda la pieza. Una tercera lo convierte en tic.

## 4. Whip blur — 2 frames
Dos frames de desenfoque direccional fuerte entre dos tomas del **mismo encuadre**, para
esconder el jump cut.

```bash
python3 tools/reelfx.py whip tomaA.mp4 tomaB.mp4 salida.mp4 \
  --frames 2 --angulo 115 --fuerza 110
```

**Cuándo:** has cortado dentro del mismo plano de A-roll y el salto canta.
**No sirve** para cambiar de escena: ahí va zoom y blur, o corte seco.

## 5. Tarjeta blanca
No es un flash. **Se sostiene.** Blanco puro con texto negro pequeño en la línea central,
corte en duro a la entrada y a la salida.

```bash
python3 tools/reelfx.py white-card "hoy en día" salida.mp4 --dur 0.67
```

Duraciones medidas en la referencia: 0.47 s, 0.67 s y 1.73 s. La larga va cuando quieres
que el espectador respire de verdad antes del tramo final.

**Cuándo:** bajar el pulso antes de volver a subirlo, o sostener una frase que no tiene
imagen posible.

**El silencio importa:** bajo la tarjeta blanca la música se va. Es parte del efecto.

## Elegir

| situación | transición |
|---|---|
| plano siguiente, misma idea | corte seco |
| jump cut en el mismo encuadre | whip blur |
| cambio de bloque o salto temporal | zoom + blur |
| cierre de idea antes de la contraria | flash en negativo |
| respiro, o frase sin imagen | tarjeta blanca |

## Presupuesto por pieza de 60–90 s

- corte seco: sin límite
- zoom + blur: 3–5
- tarjeta blanca: 2–3
- whip blur: 2–3
- flash en negativo: **1–2, y ni uno más**
