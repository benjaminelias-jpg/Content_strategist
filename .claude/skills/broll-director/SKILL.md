---
name: broll-director
description: Decide, busca y consigue el b-roll del estilo "2027" y construye el plan de planos. Úsala para elegir qué imagen va sobre cada palabra, escribir briefs de b-roll, buscar material real o generado, o montar la escaleta de planos de un reel de este estilo.
---

# Dirección de b-roll y plan de planos

Reparto de la referencia: **55 % A-roll, 45 % b-roll**.

## La regla de oro

**Cada b-roll entra sobre una palabra concreta, no sobre una frase.** Si la palabra no
tiene imagen posible, va tarjeta blanca. No rellenes con un plano genérico: un b-roll que
no significa nada resta.

## Las cinco familias

| familia | para qué sirve | ejemplos de la referencia |
|---|---|---|
| **archivo real** | ancla la afirmación en un hecho verificable | foto del equipo de OpenAI, entrevista de Sam Altman, el tuit del millón de usuarios |
| **captura de pantalla** | prueba de primera mano | UI de ChatGPT, selección de texto con el cursor a la vista |
| **macro / textura** | metáfora para lo que no tiene imagen | hoja, reloj, ojo con código reflejado |
| **humano a escala** | puerta emocional antes del remate | figura ante un lago, mujer caminando por un sendero |
| **objeto de época** | sitúa la pieza en el tiempo desde el primer frame | Macintosh clásico con CRT |

Una pieza de 60–90 s usa las cinco. Si todas tus imágenes son de la misma familia, la
pieza se aplana.

## Genera el plano. No escribas un brief y lo dejes ahí.

**Esta es la regla que más cambia el resultado.** Tienes herramientas de generación de
imagen y vídeo: úsalas. Un brief sin imagen no es un entregable, y un gráfico vectorial
hecho a mano no se parece en nada al material real de la referencia.

Los prompts que **ya funcionaron** están en `presets/broll-prompts.json`, con la gramática
fotográfica común y el registro de qué falló en cada primera versión. Para un tema nuevo
se cambia el **sujeto** y se conserva esa gramática: encuadre, óptica, luz, paleta,
profundidad de campo y las negaciones. Eso es lo que hace que los planos pertenezcan a la
misma pieza.

### El bucle, que no es opcional

1. Escribe el prompt con la gramática común y tu sujeto.
2. Genera (`images_generate`, modo auto; `video_generate` si el plano debe moverse).
3. **Mira el resultado.** No lo aceptes sin verlo.
4. Si falla, **nombra qué falla con precisión** y vuelve a generar con esa corrección
   dentro del prompt. "Mejóralo" no sirve. Sirve: *"salió descentrado, con teclado en
   cuadro y la habitación demasiado iluminada"* → se añade `camera dead-on and centered`,
   `no keyboard visible in frame`, `the room behind is almost entirely black`.
5. Descarga y normaliza a 1080×1920.
6. Comprueba el movimiento con `tools/motion_probe.py` antes de montarlo.

Las negaciones son obligatorias en todo prompt: `no text, no logos, no readable brand
names`. Los modelos inventan rótulos y marcas, y un rótulo inventado arruina el plano y
mete un problema de derechos.

## Lo que NO se genera

| | por qué |
|---|---|
| **archivo real** | Un hecho concreto — una foto de equipo, una entrevista, un tuit — **no se genera**: eso sería fabricar un documento falso. O se consigue con licencia, o se sustituye por el hecho equivalente de tu tema. |
| **capturas de pantalla** | Se graban. Lo más barato y lo más creíble. En la referencia se ve el cursor seleccionando texto: eso vende que es real, no lo limpies. |
| **el presentador** | Se rueda. La referencia incluso se disfraza de un alter ego para romper el A-roll sin salir del set, y eso no cuesta nada. |

Para lo demás —macro, textura, objeto de época, abstracción gráfica, humano a escala— la
generación es la vía por defecto: sale a medida, sin problema de licencia y con la misma
gramática en todos los planos. Los bancos (Pexels, Unsplash, Artgrid) quedan como
alternativa cuando quieras material fotográfico real y no generado.

## Cómo se escribe un brief

Mal: *"b-roll de IA"*.

Bien:

```
plano 7 — palabra "todo" (6.30–7.20 s)
familia: macro / textura
imagen: ojo humano en primerísimo plano, líneas de código reflejadas en el iris
luz: contraluz frío, fondo a negro
movimiento: el propio del clip, deriva lenta de acercamiento
por qué: "todo" no tiene imagen; el ojo con código la fabrica
duración: 1.27 s
```

Lo que hace útil un brief es el **por qué**: justifica la elección y permite que otro
sustituya el plano sin romper la idea.

## El plan de planos

Sale del mapa de palabras y entra en todo lo demás.

```json
[
  {"n":0,"t_in":0.00,"t_out":2.17,"tipo":"broll","familia":"objeto_epoca",
   "brief":"Macintosh clásico, cuarto a oscuras, luz cálida de escritorio",
   "fx":["crt"],"movimiento":"propio"},
  {"n":1,"t_in":2.17,"t_out":4.34,"tipo":"aroll",
   "fx":["pixel-text:ORO"],"movimiento":"ninguno"},
  {"n":2,"t_in":4.34,"t_out":5.74,"tipo":"broll","familia":"macro",
   "brief":"macro de hoja, cielo blanco quemado","movimiento":"propio"}
]
```

## Ritmo

- **0–8 s (apertura):** ráfaga, planos de 0.13–0.5 s.
- **desarrollo:** 0.8–2.0 s.
- **remate:** 2.5–4.0 s. El pulso baja para que aterrice la idea.

**Los cortes caen en frontera de palabra.** Sólo el 15 % de los cortes de la referencia
coincide con un golpe musical: no montes al compás.

## Antes de dar el plan por bueno

- [ ] ¿Cada b-roll entra sobre una palabra concreta?
- [ ] ¿Aparecen al menos tres familias distintas?
- [ ] ¿**Existe el archivo** de cada plano, o sigue siendo un brief sin imagen?
- [ ] ¿Miraste cada generación, o aceptaste la primera a ciegas?
- [ ] ¿Todo el material tiene licencia, es generado o es propio?
- [ ] ¿Los cortes caen en frontera de palabra?
- [ ] ¿Hay algún plano que esté sólo por rellenar? Quítalo y alarga el anterior.
