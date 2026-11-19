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
| escribir | 1001975 | Man opening a small book and writing, moody | 32.0 s | "quién escribe mejor" |
| noche | 3727937 | People crossing at night, city-light bokeh | 13.9 s | "la máquina no te copia" |
| ojo | — | *(del banco anterior)* | 15.6 s | "el criterio" |
| pizarra | 10667202 | Business Team Collaborating on Strategy Using Whiteboard | 10.0 s | "qué problema resolver" |
| blanco | 7283516 | Pen resting on a blank notebook, white table | 10.9 s | "se demuestra" — fondo blanco |
| sombras | 8412698 | Timelapse of golden hour sunlight caustics and window shadow | 5.6 s | "cuando nadie te mira" |
| oficina | — | *(del banco anterior)* | 5.5 s | "la gente que vuelve" |
| cuaderno | — | *(del banco anterior)* | 27.2 s | "pulir el currículum" |
| cruce | 8806477 | Crowd of People Walking Across a Busy City Crosswalk | 8.0 s | "mostrar lo que decidís" |

De reserva: `lluvia` (4498, piernas de una multitud bajo la lluvia en Nueva
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
