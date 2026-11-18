# Fuentes

Descargadas de Google Fonts (licencia OFL, uso libre comercial) con la API
`fonts.googleapis.com/css2`. GitHub esta restringido en este entorno, asi que
ese es el camino que funciona.

| uso | fuente |
|---|---|
| texto principal | `Inter.ttf` |
| acento italico | `PlayfairDisplay-Italic.ttf`, `InstrumentSerif-Italic.ttf` |
| **texto pixelado CRT** | `DidactGothic.ttf` |
| pixel alternativas | `PixelifySans`, `Silkscreen`, `PressStart2P`, `VT323`, `Jersey10/15/25`, `Micro5`, `Tiny5`, `Handjet`, `Workbench`, `DotGothic16` |
| geometricas | `Jost300/400`, `Poppins300/400`, `Questrial`, `Outfit300`, `Montserrat300`, `JosefinSans300` |

## Por que DidactGothic para el texto pixelado

Contra lo que parece, la referencia **no usa una fuente pixel**. Medida la
letra, su "O" es redonda y de trazo fino; todas las fuentes bitmap dan anillos
rectangulares de trazo grueso. Lo que encaja es una grotesca normal pixelada
despues, y de las probadas la que clava las metricas es Didact Gothic:

| | referencia | DidactGothic @ bloque 17 |
|---|---|---|
| ancho | 68.6% | 70.8% |
| alto | 36.7% | 37.8% |
| centro y | 0.282 | 0.283 |
| grosor de trazo | 5.4% | 4.2% |
| cobertura | 36.8% | 35.3% |
| lado de bloque | 1.93% | 1.77% |

**Sigue sin ser identico.** El IoU de la letra se queda en ~0.47 cuando la
referencia contra si misma en otro frame da 0.95. Falta dar con la tipografia
exacta. Si alguien la identifica, se suelta aqui y se pasa con `--fuente`.

## Anadir una fuente

    curl -sS -A "Mozilla/5.0" "https://fonts.googleapis.com/css2?family=Nombre+Fuente" \
      | grep -oP 'url\(\K[^)]+' | head -1 | xargs curl -sSL -o NombreFuente.ttf
