---
name: guion-y-captions
description: Escribe el guion hablado y construye el plan de subtítulos palabra a palabra del estilo "2027" — rejilla central, dispersión horizontal, escalas de énfasis y acentos. Úsala para guion, gancho, timing de palabras, o para colocar y renderizar los subtítulos de un reel de este estilo.
---

# Guion y subtítulos

Dos trabajos encadenados: primero lo que se dice, después cómo se ve escrito. El segundo
depende del audio ya grabado.

---

## Parte 1 — El guion

### La estructura del gancho

La referencia abre así y funciona:

1. **Fecha o cifra en el futuro** — `en 2027...` Sitúa y promete.
2. **La afirmación con una palabra cara** — `el criterio se va a volver oro`.
3. **El destinatario, explícito** — `para los creadores`.
4. **Pregunta directa que no se responde todavía** — deja la deuda abierta.

Las cuatro caben en menos de 5 segundos. Si tu apertura necesita más, no es una apertura.

### Cómo se escribe para este montaje

- **Frases cortas.** Cada corte cae en frontera de palabra, así que una frase larga obliga
  a sostener el mismo plano demasiado.
- **Marca al escribir** qué palabras llevan énfasis y cuáles piden imagen. Esas marcas son
  la entrada del plan de planos.
- **Una palabra cara por tramo.** *Oro*, *criterio*, *repetible*. Son las que van a escala
  héroe.
- **Habla en segunda persona.** La referencia dice *vos*, *querés*. Usa el registro de
  quien habla, no uno neutro inventado.

### Entregable

```markdown
## Guion

[0] en 2027 el **criterio** se va a volver en **oro** `IMG: macintosh viejo`
[1] para los **creadores** `PIXEL: ORO`
[2] todos sabemos que la inteligencia artificial `IMG: macro hoja`
[3] está cambiando **todo** `COLOR: rojo` `IMG: ojo con código`
```

- `**palabra**` → énfasis
- `IMG:` → pide b-roll, con brief
- `PIXEL:` → texto pixelado tras el sujeto
- `COLOR:` → acento de color
- `CARD:` → tarjeta blanca

---

## Parte 2 — El mapa de palabras

**Sin la voz grabada esto no existe, y sin esto no hay montaje.** Es el cuello de botella
real. Si el usuario aún no ha grabado, dilo y para.

```bash
python3 tools/wordmap.py voz.wav --guion guion.md --salida plan/palabras.json
```

Sale un `t_in`/`t_out` por palabra. Revísalo: el reconocimiento se equivoca en nombres
propios y en números, y un timing mal puesto arrastra el error a todo el montaje.

---

## Parte 3 — La rejilla de subtítulos

Esto es la firma visual, y es contraintuitivo.

- **Línea base y = 0.505.** No es un lower-third. Las palabras viven en el **centro
  vertical** del cuadro.
- **Dispersión horizontal:** p10 = 0.20, mediana = 0.50, p90 = 0.78. Las palabras **no van
  centradas**: se esparcen a lo ancho sobre esa única línea.
- Cada palabra nueva aparece en una X distinta. **Las anteriores se quedan.**
- Máximo 3–4 palabras a la vez.
- La frase **se borra de golpe en el corte**, no palabra a palabra.

### Escalas

| escala | % del alto | cuándo |
|---|---|---|
| normal | 4.31 % | casi todo |
| énfasis | 10.85 % | la palabra que carga el giro |
| héroe | 18.47 % | una o dos en toda la pieza |

### Color

Blanco por defecto. **Un solo color de acento en toda la pieza**, sobre la palabra que
carga el conflicto. Sobre fondo claro el texto pasa a negro — por eso los subtítulos se
planifican **después** del plan de planos.

La serif itálica (y el naranja) se reserva para una o dos palabras: el giro conceptual.

### El plan

```json
[
  {"palabra":"criterio","t_in":1.20,"t_out":3.40,"x":0.28,"escala":"enfasis"},
  {"palabra":"oro","t_in":2.10,"t_out":3.40,"x":0.66,"escala":"heroe"},
  {"palabra":"todo","t_in":6.30,"t_out":7.20,"x":0.52,"color":"#F46963"},
  {"palabra":"repetible","t_in":41.0,"t_out":43.2,"x":0.45,"italica":true}
]
```

```bash
python3 tools/reelfx.py captions montaje.mp4 salida.mp4 --plan plan/captions.json
```

### Errores que delatan la copia

- Subtítulos centrados en X → es un generador automático, no este estilo.
- Subtítulos abajo → lower-third de plantilla.
- Una palabra a la vez, borrando la anterior → karaoke, no esto.
- Tres colores → se pierde el acento.
