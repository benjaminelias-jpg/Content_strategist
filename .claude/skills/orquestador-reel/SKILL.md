---
name: orquestador-reel
description: Dirige el montaje completo de un reel en el estilo "2027" de principio a fin. Úsala cuando pidan montar, editar o producir un reel, un vídeo vertical o una pieza con este estilo, o cuando pidan "haz la edición como esta persona". Decide el orden, llama a las skills especialistas en la secuencia correcta y no deja que ninguna se adelante a sus dependencias.
---

# Orquestador de reel

Montas la pieza entera. Las skills especialistas saben hacer su parte; tú sabes **en qué
orden** y **con qué entra cada una**. Ese orden no es negociable: cada etapa consume algo
que produce la anterior, y saltárselo obliga a rehacer trabajo.

Todas las medidas del estilo viven en `presets/estilo-2027.json`. Léelo antes de empezar.
El porqué de cada número está en `docs/analisis-reel-2027.md`.

## La regla que más se incumple

**El zoom vive en la transición, no en el plano.** Los planos están quietos el 85 % de su
duración. Si aplicas `zoomblur-cut` entre dos planos, **no** apliques además un punch a
esos planos: es el mismo movimiento duplicado y se ve.

## Orden de producción

Cada etapa declara qué necesita y qué entrega. No arranques una sin tener su entrada.

### 0. Encuadre — antes de tocar nada
Necesitas del usuario tres cosas. Si falta alguna, **pregunta**; no la inventes:

- **tema y tesis** (la frase que el espectador debe repetir después)
- **voz**: ¿hay audio grabado o hay que escribir para grabar?
- **material propio**: ¿tiene A-roll rodado? ¿capturas de pantalla?
- **referencia**: ¿imita el reel "2027" o trae otro vídeo que quiere replicar?

Si no hay A-roll ni voz, la pieza no se puede montar: lo que se entrega es el guion y el
plan de rodaje, y se dice claramente.

**Si trae una referencia que no es "2027", desmóntala antes de empezar** con la skill
`rea-video`: `rea-video decompose <vídeo> -o out/ref --lang es`. Sale plano a plano cómo se
hizo, qué lleva encima, dónde caen los cortes y cómo suena. Eso es evidencia para escribir un
preset nuevo, no un preset: los números se deciden y se escriben a mano en `presets/`, como se
hizo con el de "2027". Mientras no exista ese preset, el estilo que manda sigue siendo el de
`presets/estilo-2027.json`, y hay que decírselo al usuario.

### 1. Guion → `guion-y-captions`
**Entra:** tema, tesis, duración objetivo.
**Sale:** guion hablado con la estructura de gancho del estilo, marcando las palabras que
llevarán énfasis y las que piden imagen.

### 2. Mapa de palabras → `guion-y-captions`
**Entra:** la pista de voz grabada.
**Sale:** `plan/palabras.json` con `t_in`/`t_out` por palabra.

Sin voz grabada esto no existe, y sin esto no hay subtítulos ni cortes. Es el cuello de
botella real de la pieza: si el usuario aún no ha grabado, dilo y para aquí.

### 3. Plan de planos → `broll-director`
**Entra:** mapa de palabras.
**Sale:** `plan/planos.json` — qué ve el espectador en cada tramo: A-roll, b-roll (con
brief de qué imagen), o tarjeta blanca.

Aquí se decide el ritmo: ráfaga de 0.13–0.5 s en la apertura, 0.8–2.0 s en el desarrollo,
2.5–4.0 s en el remate. **Los cortes caen en frontera de palabra**, nunca al compás.

### 4. Conseguir el b-roll → `broll-director`
**Entra:** los briefs del plan.
**Sale:** los clips en `media/broll/`.

Etapa lenta (descargas, generación, rodaje). Si varios clips son independientes, lánzalos
en paralelo. Lo que sea archivo real sin licencia **no se usa**: se sustituye y se avisa.

### 5. Subtítulos → `guion-y-captions`
**Entra:** mapa de palabras + plan de planos.
**Sale:** `plan/captions.json` con X, escala y color por palabra.

Va después del plan de planos porque el color del texto depende del fondo: blanco sobre
oscuro, negro sobre claro.

### 6. Movimiento y transiciones → `motion-zooms` y `transiciones-fx`
**Entra:** los clips cortados a su duración.
**Sale:** los clips con su movimiento y las transiciones resueltas.

Primero el movimiento de plano (casi siempre ninguno), después las transiciones. Al revés
se pierde el encuadre.

### 7. Pixelado y CRT → `pixel-crt`
**Entra:** el plano concreto que lo lleva.
**Sale:** el plano compuesto.

Sólo si la pieza lo pide. Como mucho **una** aparición de texto pixelado, en la apertura.
Dos lo abaratan.

### 8. Audio → `audio-mix`
**Entra:** voz + el vídeo ya montado.
**Sale:** la mezcla.

Después del montaje, porque los SFX van clavados a transiciones que hasta ahora no
existían.

Para **elegir** entre varios candidatos de música o de efecto, no lo hagas de oído imaginado:
`earshot` los describe y los puntúa contra lo que buscas, y devuelve el número. Si hay que
construir la banda entera desde grabaciones con licencia, la skill `real-sound` lleva el
proceso completo, comprobación de licencia incluida.

### 9. Ensamblaje y control → `render-y-qc`
**Entra:** todo.
**Sale:** el máster y un informe de desviaciones contra el preset.

## Paralelizable y no paralelizable

| se puede en paralelo | va en serie, sí o sí |
|---|---|
| conseguir varios b-roll a la vez | guion → voz → mapa de palabras |
| renderizar efectos de planos distintos | plan de planos → subtítulos |
| buscar música mientras se monta | montaje → audio |

## Antes de dar nada por terminado

No digas que está hecho sin haberlo comprobado. Pasa `render-y-qc` y revisa:

- [ ] ¿Hay algún plano con zoom **y** transición de zoom encima? Quita uno.
- [ ] ¿Los cortes caen en frontera de palabra?
- [ ] ¿Los subtítulos están en la línea 0.505 y dispersos en X, no centrados?
- [ ] ¿Hay como mucho un color de acento en toda la pieza?
- [ ] ¿Flash en negativo, 1–2 veces como mucho?
- [ ] ¿La música sostiene sin competir con la voz?
- [ ] ¿El cierre está en silencio?

Las dos últimas son afirmaciones sobre cómo suena algo, y tú no lo has oído. Respáldalas con
una lectura de `earshot` sobre el máster y cita el número, igual que se hace con el resto.

Si algo falla, dilo con el dato. "El corte de 12.4 s cae en mitad de la palabra" vale;
"quedó raro" no.
