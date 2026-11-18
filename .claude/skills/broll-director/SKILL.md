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

## De dónde sale cada cosa

**Archivo real.** Es lo que más convence y lo único que **no se puede clonar**: el
material de la referencia es suyo. Sustitúyelo por el equivalente de tu tema. Si es prensa
o material con derechos, hace falta licencia — no lo metas en una pieza comercial sin
ella, y si no la hay, dilo y propón alternativa.

**Capturas.** Grábalas tú. Es lo más barato y lo más creíble. Detalle que importa: en la
referencia se ve el cursor seleccionando texto. Eso vende que es real. No lo limpies.

**Macro y textura.** Bancos con licencia permisiva (Pexels, Unsplash, Artgrid) o
generación. Son planos sin cara, fáciles de sustituir.

**Humano a escala.** Banco o rodaje propio. Cuidado con los bancos: una cara reconocible
de stock se nota.

**Objeto de época.** Generación o banco.

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
- [ ] ¿Todo el material tiene licencia o es propio?
- [ ] ¿Los cortes caen en frontera de palabra?
- [ ] ¿Hay algún plano que esté sólo por rellenar? Quítalo y alarga el anterior.
