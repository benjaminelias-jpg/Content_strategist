---
name: audio-mix
description: Monta y mezcla el audio del estilo "2027" — cama musical continua, ducking contra la voz, SFX clavados a las transiciones y silencio en el cierre. Úsala para elegir música, mezclar voz, poner efectos de sonido o masterizar el audio de un reel de este estilo.
---

# Audio

Va **después** del montaje de imagen, porque los SFX se clavan a transiciones que antes no
existían.

## La cama musical

- **Continua.** En la referencia no hay un solo hueco hasta 75.68 s.
- **Graves dominantes.** La banda 20–120 Hz supera a la de voz en 9 de los 10 bloques
  analizados.
- **Sostiene, no marca.** Unos −16 dB por debajo de la voz.

Que los graves manden y los medios no es lo que permite que la música esté presente todo
el rato sin tapar nada. Una pista con melodía en el rango de la voz obliga a bajarla tanto
que deja de sumar: entonces es mejor cambiarla.

## La voz manda el montaje

**Sólo el 15 %** de los cortes cae a menos de 120 ms de un golpe musical. **No montes al
compás.** Se corta en frontera de palabra o en la respiración.

Esto tiene una consecuencia práctica: la música se elige **después** de tener el montaje,
y se elige una que no pida ser seguida.

- voz objetivo: **−22 dBFS** (medido: −25.4 a −21.9)
- máster: ≈ **−22 LUFS** integrados
- procesado de voz: compresión suave y de-esser. Nada agresivo.

## Ducking

| parámetro | valor |
|---|---|
| reducción | 9 dB |
| ataque | 40 ms |
| liberación | 280 ms |

```bash
python3 tools/audiomix.py --voz voz.wav --musica cama.wav \
  --video montaje.mp4 --salida final.mp4
```

La liberación larga evita el bombeo audible entre palabras.

## SFX

Pocos y clavados:

- **whoosh corto** en cada whip blur
- **impacto seco** en el flash en negativo
- **silencio total** bajo la tarjeta blanca — la música se va, y eso es parte del efecto
- nivel: ≈ **−28 dBFS**

Un SFX en cada corte convierte la pieza en una demo de plantilla. Si dudas, no lo pongas.

## El cierre

Los últimos **0.64 s** van en silencio, bajo la tarjeta final. Sin cola musical, sin
fundido largo. Corta.

## Comprobación

```bash
python3 tools/audiomix.py --qc final.mp4
```

Revisa:

- [ ] ¿La cama no tiene huecos hasta el cierre?
- [ ] ¿La voz se entiende en el tramo más denso de música?
- [ ] ¿Hay bombeo audible? Sube la liberación.
- [ ] ¿La tarjeta blanca está en silencio?
- [ ] ¿El cierre está en silencio?
- [ ] ¿El integrado ronda −22 LUFS?
