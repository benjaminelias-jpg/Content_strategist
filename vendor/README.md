# vendor — dependencias copiadas de terceros

Dos proyectos externos viven aquí copiados, no enlazados. El repo es autocontenido: se clona
y está todo, sin submódulos ni `--recursive`. Lo que se paga a cambio es que **actualizar es un
acto deliberado**, no un `git pull`.

## Qué hay

| | origen | licencia | qué aporta |
|---|---|---|---|
| `earshot/` | [Leonxlnx/earshot](https://github.com/Leonxlnx/earshot) | MIT | oídos: describe un audio en palabras, lo puntúa contra una descripción, detecta si es grabación real o sintetizado, y trae un banco de 252 efectos escritos en código |
| `rea-video/` | [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video) | Apache-2.0 | ingeniería inversa de un vídeo plano a plano: cómo se hizo cada uno, qué capas lleva encima, cómo suena y cómo replicarlo |

Los commits exactos están en `pins.txt`. Las licencias viajan con el código (`earshot/LICENSE`,
`rea-video/LICENSE`, `rea-video/NOTICE`); no las muevas ni las borres: la Apache-2.0 obliga a
conservar el `NOTICE`.

Las skills de ambos no están aquí sino en `.claude/skills/` — `earshot`, `real-sound` y
`rea-video` — porque es donde el agente las carga. Vienen del mismo commit y se refrescan con el
mismo script.

## Qué se dejó fuera

De cada upstream se copia solo el paquete ejecutable, sus skills y la licencia. Se omiten `docs/`,
`eval/`, `tests/` e `i18n/`: son unos 80 MB de ejemplos, vídeos de muestra y suites de evaluación
que este proyecto no ejecuta. Si hace falta alguno, está en el repo de origen al commit fijado.

Resultado: 5,5 MB en lugar de 166 MB.

## Actualizar

```bash
tools/vendor_refresh.sh
```

Reconstruye `vendor/` y las tres skills desde los commits de `pins.txt`. Úsalo también para
comprobar que nadie ha editado a mano lo copiado: si el `git diff` sale limpio, el árbol coincide
con el upstream fijado.

```bash
tools/vendor_refresh.sh --latest
```

Trae la punta de la rama por defecto y reescribe `pins.txt`. Revisa el diff antes de confirmar:
son proyectos vivos y una actualización puede cambiar la interfaz de las herramientas.

**No edites nada dentro de `vendor/`.** El refresco lo borra todo y lo vuelve a copiar, así que
cualquier parche local se pierde sin avisar. Si algo hay que adaptar, envuélvelo desde `tools/`.

## Instalar

```bash
tools/vendor_install.sh
```

Necesita `ffmpeg` y Python ≥ 3.10. Instala ambos paquetes en modo editable y deja dos comandos
nuevos: `rea-video` y `earshot`.

Dos cosas que conviene saber antes de lanzarlo:

- **earshot arrastra `torch`.** El script lo baja del índice de CPU, no del de CUDA, porque aquí
  no hace falta GPU. Aun así son cientos de megas.
- **Los modelos se bajan en la primera ejecución**, no en la instalación. earshot necesita red la
  primera vez que escucha algo (CLAP y AST); rea-video baja unos 216 MB de separación de pistas
  (MDX-Net y BandIt) la primera vez que separa voz, música y efectos. Después funcionan sin red.

Para instalar solo uno: `tools/vendor_install.sh rea-video` o `tools/vendor_install.sh earshot`.
