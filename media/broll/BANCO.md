# Banco de b-roll

Metraje real con licencia, descargado del catálogo de stock de Freepik vía
Magnific. **Nada de Pinterest**: casi todo lo que hay ahí lo subió un tercero y
no tiene licencia de reutilización, así que sirve como referencia estética pero
no puede entrar en una pieza. Lo que se hizo fue usar esa estética como criterio
de búsqueda en un banco con licencia.

Cada clip se descarga por su `id` y se pasa por `tools/look.py` para el look
común antes de montarlo. El `id` es lo que hace esto reproducible: con él se
vuelve a bajar el mismo archivo.

| nombre | id | título original | dur | para qué |
|---|---|---|---|---|
| bokeh | 4916 | Bokeh Traffic at Night in San Francisco | 16.6 s | arranque abstracto |
| papeles | — | *(del banco anterior)* | 11.8 s | "currículum" |
| mac | — | *(del banco anterior)* | 10.0 s | "cualquiera genera uno" |
| teclado | — | *(del banco anterior)* | 13.1 s | "treinta segundos" |
| maquina | 10673460 | Close-up of Hands Typing on a Vintage Typewriter | 5.1 s | "todos suenan igual" |
| circulo | 10013337 | Low angle view of a crowd walking in a circle | 17.6 s | "todos dicen lo mismo" |
| cenital | 1842205 | Overhead View Of Graphic Designer Working At Computer At Night | 25.2 s | "quién escribe mejor" — **cenital cerrado** |
| aereo | 2976667 | Top Down Aerial View of People Walking on Via Toledo, Naples | 13.3 s | "todos dicen lo mismo" — **cenital general** |
| ojo | — | *(del banco anterior)* | 15.6 s | "el criterio" |
| pizarra | 10667202 | Business Team Collaborating on Strategy Using Whiteboard | 10.0 s | "qué problema resolver" |
| blanco | 7283516 | Pen resting on a blank notebook, white table | 10.9 s | "se demuestra" — fondo blanco |
| sombras | 8412698 | Timelapse of golden hour sunlight caustics and window shadow | 5.6 s | "cuando nadie te mira" |
| oficina | — | *(del banco anterior)* | 5.5 s | "la gente que vuelve" |
| textura | 3473303 | Close-up of a stack of rolled up white paper | 7.0 s | sobre la palabra "papel" — **textura macro** |
| torres | 7782604 | Low Angle View of Modern Skyscrapers and Glass Facades | 17.7 s | "los proyectos que terminás" — **contrapicado general** |
| cruce | 8806477 | Crowd of People Walking Across a Busy City Crosswalk | 8.0 s | "mostrar lo que decidís" |

De reserva: `escribir` (1001975, hombre escribiendo en un cuaderno),
`cuaderno`, `noche` (3727937, paso de cebra nocturno), `lana` (1715744,
textura de lana), `lluvia` (4498, piernas de una multitud bajo la lluvia en Nueva
York), `libro` (10051037, macro de páginas pasando), `peatones` (92997,
peatones desenfocados en Oxford), `polvo` (3082473, rendija de sol con polvo
en suspensión), `multitud`.

## Por qué `polvo` se quedó fuera

Entró primero y se salía de banda: luma 25 sobre 160, casi negro, frente a los
46-114 de los otros catorce planos. Se lee como un fallo de render, no como un
plano. Barrido el clip entero en ventanas de medio segundo no tiene **ningún**
tramo estable dentro de banda: es una entrada de sol, solo rampas (25 → 160 →
22), y una rampa dentro de un plano de 1.5 s se lee como un fundido. `sombras`
se queda plano en 88-91 de principio a fin.

La comprobación que lo detectó —luma media de cada plano de b-roll tal y como
se usa, con su `ss` y su duración— vale para cualquier pieza: un solo plano
fuera de banda basta para que el montaje parezca roto.

## La regla que esto resuelve

Un clip repetido se nota más que un clip mediocre. Con 15 huecos de b-roll y
siete clips, v6 repetía cinco. El banco tiene veinte: `v7.py` aborta el montaje
si un nombre sale dos veces, así que la repetición no puede volver por descuido.


## Tipos de plano, no solo clips distintos

Quince clips distintos no dicen nada si los quince estan rodados desde el mismo
sitio y a la misma distancia. Medido en la v7: ocho de sus quince planos de
b-roll eran **detalle de sobremesa** (53 %), y no habia ni un contrapicado ni un
cenital. Se ve como una sola textura visual aunque no se repita ningun clip.

El reparto que busca la pieza:

| tipo | cuantos | para que sirve |
|---|---|---|
| detalle | 5 | la prueba de cerca: manos, teclas, un ojo |
| textura | 2 | respiro abstracto entre dos ideas |
| cenital | 2 | uno general (multitud) y uno cerrado (una mesa) |
| contrapicado | 3 | escala: lo que te supera |
| general / medio | 4 | situar |

`v8.py` aborta el montaje si falta alguno de los seis tipos o si uno solo cubre
mas del 40 % de los huecos. Y audita el reparto A-roll / b-roll contra el 55/45
del preset sobre el **tiempo de rodaje**, descontando tarjetas y cierre: anadir
b-roll y tarjetas se come el A-roll sin que se note, y la pieza deja de ser
alguien hablando.
