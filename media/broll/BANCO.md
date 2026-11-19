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
| mano | 1105355 | Man's hand moves over a wall with long shadow from window | 12.0 s | "qué problema resolver" |
| blanco | 7283516 | Pen resting on a blank notebook, white table | 10.9 s | "se demuestra" — fondo blanco |
| sombras | 8412698 | Timelapse of golden hour sunlight caustics and window shadow | 5.6 s | "cuando nadie te mira" |
| luz | 10438675 | Silhouetted pedestrians walking through bright beam of sunlight | 20.5 s | "la gente que vuelve" |
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


## Aesthetic, no catalogo

Tres planos delataban la pieza como stock corporativo: el equipo en la pizarra,
el senor en la oficina y los dos retratos de los motion graphics. El patron era
siempre el mismo: **gente mirando a camara, escenario de negocio montado y luz
plana**.

El criterio para lo que entra: sujeto anonimo o parcial, luz dura y
direccional, foco corto, textura. Lo que sale: sonrisa a camara, oficina
luminosa, situacion escenificada.

### Los retratos del parallax necesitan fondo

Al cambiarlos cai en la trampa contraria. Los dos primeros candidatos
"aesthetic" eran retratos low-key preciosos, pero el fondo medido daba **2.0 y
14.8** de varianza: vacio. Y sin fondo no hay parallax, solo un zoom. Asi que
antes de elegir un retrato se mide el detalle en el **borde del cuadro**, que es
casi todo fondo: por debajo de ~40 no sirve.

| retrato | separacion sujeto/fondo medida sobre el render |
|---|---|
| los de catalogo | 10-14x |
| los que entraron (138 y 792 de detalle en el borde) | **83x y 33x** |

### La media de luma era el criterio equivocado

El clip de siluetas a contraluz da **media 24**, por debajo de la banda 46-114
del resto, y lo iba a descartar. Medido el histograma, tiene **p95 = 206**: la
alta mas brillante de todo el banco, con un recorrido de 206, igual que el
bokeh (202) o el Macintosh (213). No esta subexpuesto, es una silueta de
contraste alto y su media baja es justo el efecto.

Lo que hay que medir no es la media sino **si el plano tiene altas** (p95 >=
120): eso es lo que distingue un low-key de un plano embarrado. La media sola
descarta precisamente el material mas aesthetic.

## Archivo de persona real: Sam Altman

La referencia usa metraje de Altman. El catalogo de stock NO lo tiene: buscar
"Sam Altman OpenAI CEO" devuelve senores de negocios genericos, varios
generados por IA. Es una biblioteca royalty-free con cesion de imagen de
modelos, no una agencia editorial. Las fotos reales estan en Getty, AP y
Reuters, cuya licencia editorial **prohibe el uso promocional**, que es lo que
es un reel de marca.

La via que si sirve es **Wikimedia Commons**: hay 21 ficheros de Altman y la
mayoria son **CC BY 2.0**, que permite uso comercial a cambio de atribucion.

| | |
|---|---|
| fichero | `Sam Altman November 2022.jpg` |
| autor | Village Global |
| licencia | CC BY 2.0 — https://creativecommons.org/licenses/by/2.0 |
| restricciones | ninguna |
| pagina | https://commons.wikimedia.org/wiki/File:Sam_Altman_November_2022.jpg |

Se eligio esa y no otra porque **es de noviembre de 2022**, el mes del
lanzamiento de ChatGPT, que es de lo que habla el plano en la referencia.

**La atribucion hay que ponerla al publicar**: "Sam Altman, foto de Village
Global, CC BY 2.0" en la descripcion del post. Sin eso la licencia no se
cumple. Y dos avisos que no son de copyright: usar la imagen de una persona
real en contenido promocional tiene ademas derechos de imagen, y conviene que
la pieza no sugiera que respalda el producto.

### Como descargar de Commons

`upload.wikimedia.org` devuelve **429** al original y pide usar los **tamanos
de miniatura estandar**. La URL que funciona es la de thumb:

```
https://upload.wikimedia.org/wikipedia/commons/thumb/3/32/Sam_Altman_November_2022.jpg/1920px-Sam_Altman_November_2022.jpg
```
