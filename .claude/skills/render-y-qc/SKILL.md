---
name: render-y-qc
description: Ensambla el máster final del reel y lo audita contra el preset del estilo "2027" midiendo el resultado. Úsala para montar los planos en un vídeo final, exportar, o comprobar que una pieza cumple el estilo antes de darla por terminada.
---

# Ensamblaje y control de calidad

## Ensamblar

```bash
python3 tools/assemble.py --plan plan/planos.json --salida out/master.mp4
```

Lee el plan de planos, recorta cada clip a su ventana, normaliza todo al lienzo
(1080×1920, 30 fps) y concatena resolviendo las transiciones declaradas.

Orden dentro del ensamblaje, que importa:

1. normalizar cada clip al lienzo
2. movimiento de plano (casi siempre ninguno)
3. transiciones entre planos
4. subtítulos quemados encima
5. capas de ajuste que afectan a todo — **el flash en negativo va aquí, sobre el texto**

El punto 5 no es un detalle: en la referencia el texto también se invierte. Si inviertes
sólo el clip, el efecto no se parece.

## Auditar

```bash
python3 tools/render_qc.py out/master.mp4
```

Mide el resultado y lo compara con `presets/estilo-2027.json`. Informa de:

- duración de planos y cadencia por tramos
- curva de zoom por plano — **detecta Ken Burns**, que es el fallo más común
- posición y dispersión de los subtítulos
- flashes en negativo, tarjetas blancas y su duración
- niveles de audio y silencios

Devuelve desviaciones con su dato, no impresiones.

## Lista antes de entregar

No digas que está terminado sin haber pasado el QC y leído la salida.

- [ ] ¿Algún plano con zoom **y** transición de zoom encima? Quita uno.
- [ ] ¿Alguna rampa de zoom recta de principio a fin? Es Ken Burns, rehazla.
- [ ] ¿Los cortes caen en frontera de palabra?
- [ ] ¿Los subtítulos en la línea 0.505 y dispersos en X?
- [ ] ¿Un solo color de acento?
- [ ] ¿Flash en negativo, 1–2 como mucho?
- [ ] ¿Tarjeta blanca en silencio?
- [ ] ¿Cierre en silencio?
- [ ] ¿Máster cerca de −22 LUFS?

## Cómo se informa

Con el dato:

> El corte de 12.4 s cae en mitad de "criterio" (la palabra va de 12.1 a 12.8). El plano 7
> lleva punch +7 % y además zoomblur-cut en la salida: el movimiento está duplicado.

No así:

> Quedó un poco raro el ritmo.

Si algo no se pudo comprobar, dilo. Un QC que calla un fallo es peor que no pasarlo.
