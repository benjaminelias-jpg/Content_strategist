---
name: reel-adn-estilo
description: El ADN medido del estilo de reel "2027" — ritmo, tipografía, rejilla de subtítulos, paleta, movimiento, transiciones y audio, con los números exactos. Úsala como referencia cuando haya que decidir cualquier parámetro visual o de ritmo de una pieza en este estilo, o cuando pidan explicar en qué consiste el estilo.
---

# El ADN del estilo

Todo lo de aquí sale de medir el reel de referencia frame a frame, no de mirarlo. Los
números viven en `presets/estilo-2027.json` y el porqué de cada uno en
`docs/analisis-reel-2027.md`.

## Las cinco cosas que definen el estilo

Si sólo te llevas cinco, que sean éstas. Son las que se copian mal.

### 1. El zoom vive en la transición, no en el plano
Catorce planos están a **0.00 %** de zoom. Los que se mueven están quietos el **85 %** de
su duración y descargan todo el recorrido en los **~5 frames previos al corte**. Un Ken
Burns lento y parejo delata la copia.

### 2. Los subtítulos van en el centro vertical y dispersos en X
Línea base **y = 0.505**. No es lower-third. Y **no van centrados**: se esparcen a lo
ancho (p10 = 0.20, p90 = 0.78) sobre esa única línea. Las palabras se acumulan y se borran
de golpe en el corte.

### 3. Los cortes los manda la voz, no el beat
Sólo el **15 %** cae cerca de un golpe musical. Se corta en frontera de palabra.

### 4. Los efectos son acentos sobre imagen limpia
El **90 %** de las transiciones es corte seco. El flash en negativo aparece **una o dos
veces en toda la pieza**. Aplicar un filtro a todo el reel es lo contrario de este estilo.

### 5. El texto pixelado va detrás del sujeto
Requiere máscara del cuerpo. Delante es plantilla; detrás es composición.

---

## Ficha rápida

**Lienzo:** 1080×1920, 30 fps, bt709. Duración objetivo 60–90 s.

**Ritmo**
| | |
|---|---|
| plano medio | 1.44 s |
| plano mediano | 1.13 s |
| más corto / más largo | 0.13 s / 9.58 s |
| apertura (0–8 s) | 0.15–0.5 s por plano |
| desarrollo | 0.8–2.0 s |
| remate | 2.5–4.0 s |

**Tipografía**
- primaria: neo-grotesca (Helvetica Now Display, Inter Display), pesos 500–700, tracking −0.015 em, caja baja
- acento: serif itálica didone, 1–2 palabras por pieza
- rótulo de fecha: mayúsculas peso 800, con punto final, a sangre
- alturas de caja: normal 4.31 %, énfasis 10.85 %, héroe 18.47 % del alto
- sombra: negra 35 %, blur 18 px, offset (0, 4)

**Paleta**
| uso | color |
|---|---|
| texto sobre oscuro | `#FFFFFF` |
| texto sobre claro | `#030303` |
| fondo tarjeta blanca | `#FDFDFD` |
| rojo acento | `#F46963` |
| naranja acento | `#FEAC7D` |
| pixel cuerpo / bloom | `#DFE87F` / `#FFFFB3` |
| cierre fondo / logo | `#000000` / `#D8D8D8` |

**Un solo color de acento en toda la pieza**, sobre la palabra que carga el conflicto.

**Transiciones**
| recurso | duración | presupuesto por pieza |
|---|---|---|
| corte seco | — | el 90 % |
| zoom + blur | ~5 frames por lado | 3–5 |
| tarjeta blanca | 0.47–1.73 s | 2–3 |
| whip blur | 2 frames | 2–3 |
| flash en negativo | 6 frames | **1–2** |

**Audio**
- cama continua, graves dominantes, −16 dB bajo la voz
- voz a −22 dBFS, máster ≈ −22 LUFS
- ducking: −9 dB, ataque 40 ms, liberación 280 ms
- SFX a −28 dBFS, sólo en whip y flash
- silencio bajo la tarjeta blanca y en el cierre

**B-roll:** 45 % del metraje, cinco familias (archivo real, captura de pantalla, macro,
humano a escala, objeto de época). Cada uno entra **sobre una palabra concreta**.

**Cierre:** diana concéntrica `#D8D8D8` sobre negro, 14 % del ancho, 2.87 s, en silencio.

---

## Qué no es este estilo

- No es un filtro VHS aplicado a todo.
- No es karaoke de subtítulos centrados abajo.
- No es montaje al compás.
- No es Ken Burns continuo.
- No es un efecto en cada corte.

El estilo es **imagen limpia, corte duro seguido de la voz, texto fuera de sitio a
propósito, y tres o cuatro acentos muy medidos**.
