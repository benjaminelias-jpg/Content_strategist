#!/usr/bin/env python3
"""
reelfx - renderizador de los efectos del estilo "2027".

Cada efecto esta medido sobre el reel de referencia y vive en
presets/estilo-2027.json. Este modulo los ejecuta con ffmpeg.

Uso:
    python3 tools/reelfx.py <efecto> [opciones]

Efectos:
    punch          zoom que descarga en el ultimo 15% del plano
    invert-flash   6 frames de inversion RGB sobre el compuesto
    whip           2 frames de desenfoque direccional entre dos tomas
    zoomblur-cut   corte con zoom+blur de salida y blur de entrada
    white-card     tarjeta blanca con texto negro
    endcard        cierre de marca con diana
    crt            pantalla de tele vieja (scanlines + aberracion)
    pixel-text     palabra bitmap gigante con scanlines y bloom
    captions       subtitulos palabra a palabra sobre la linea central
    probe          imprime duracion/fps/tamano de un clip
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PRESET = json.loads((RAIZ / "presets" / "estilo-2027.json").read_text(encoding="utf-8"))

W = PRESET["lienzo"]["ancho"]
H = PRESET["lienzo"]["alto"]
FPS = PRESET["lienzo"]["fps"]

# El preset describe el lienzo de la referencia (vertical). Un material rodado
# en horizontal NO se convierte a vertical salvo que se pida: forzarlo obliga a
# rellenar con bandas y destroza el encuadre. REELFX_LIENZO=AxB manda sobre el
# preset para montar en el formato nativo del material.
import os as _os
if _os.environ.get("REELFX_LIENZO"):
    try:
        _w, _h = (int(v) for v in _os.environ["REELFX_LIENZO"].lower().split("x"))
        W, H = _w, _h
    except ValueError:
        pass


# ---------------------------------------------------------------- utilidades


def run(args: list[str], dry: bool = False) -> None:
    """Ejecuta ffmpeg mostrando el comando."""
    print("$ " + " ".join(shlex.quote(a) for a in args), file=sys.stderr)
    if dry:
        return
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-4000:])
        raise SystemExit(f"ffmpeg fallo ({p.returncode})")


def probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,nb_frames",
         "-show_entries", "format=duration", "-of", "json", path],
        capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    st = d["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {
        "w": st["width"], "h": st["height"],
        "fps": float(num) / float(den),
        "dur": float(d["format"]["duration"]),
    }


def _fit(target_w: int = W, target_h: int = H) -> str:
    """Escala+recorta cualquier fuente al lienzo vertical sin deformar."""
    return (f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
            f"crop={target_w}:{target_h},setsar=1")


def _blur_ramp(frames: int, sigma_max: float, invertida: bool = False,
               offset_frames: int = 0) -> str:
    """Rampa de desenfoque como cadena de gblur con ventana por frame.

    gblur no admite expresiones en `sigma` (solo timeline via `enable`), asi
    que la rampa se construye con un filtro por frame. Con 5 frames son 5
    filtros: barato y exacto al frame.
    """
    pasos = []
    for i in range(frames):
        u = (i + 1) / frames
        if invertida:          # resuelve de desenfocado a nitido
            u = 1.0 - i / frames
        s = sigma_max * (u ** 4)
        if s < 0.3:
            continue
        n = offset_frames + i
        pasos.append(f"gblur=sigma={s:.3f}:enable='eq(n,{n})'")
    return ",".join(pasos)


def _scanlines_png(periodo: int, alto: int = H, ancho: int = W) -> pathlib.Path:
    """Genera (y cachea) una mascara de scanlines. Mucho mas rapido que geq."""
    cache = RAIZ / "assets" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    p = cache / f"scanlines_{ancho}x{alto}_p{periodo}.png"
    if p.exists():
        return p
    import numpy as np
    from PIL import Image
    # OJO: no vale crear un patron de 1xperiodo y reescalarlo. Al llevar 1x2
    # a 1080x1920 cada fila origen cubre 960 filas destino y sale media
    # imagen blanca y media negra, no lineas alternas. Hay que teselar.
    filas = (np.arange(alto) % periodo == 0).astype("uint8") * 255
    arr = np.repeat(filas[:, None], ancho, axis=1)
    Image.fromarray(arr, mode="L").save(p)
    return p


# ------------------------------------------------------------------- efectos


def ef_punch(src: str, dst: str, total_pct: float, reposo: float,
             dur: float | None = None, dry: bool = False) -> None:
    """Zoom quieto el `reposo` del plano y acelerado (easeInQuart) al final.

    El movimiento se hace con scale+crop sobre una expresion temporal, que
    conserva la nitidez mejor que zoompan a estas escalas tan cortas.
    """
    info = probe(src)
    dur = dur or info["dur"]
    z = 1.0 + total_pct / 100.0
    # u = avance dentro de la ventana de movimiento, 0 fuera de ella
    u = f"max(0\\,(t/{dur}-{reposo})/{1 - reposo})"
    # easeInQuart dentro de la ventana
    zoom = f"(1+{z - 1:.6f}*pow(min({u}\\,1)\\,4))"
    vf = (
        f"{_fit()},"
        f"scale=w='ceil(iw*{zoom}/2)*2':h='ceil(ih*{zoom}/2)*2':eval=frame,"
        f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/2'"
    )
    run(["ffmpeg", "-y", "-i", src, "-vf", vf, "-r", str(FPS),
         "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "copy", dst], dry)


def ef_suspendido(src: str, dst: str, *, deriva_pct: float = 9.0,
                  entrada: float = 0.42, blur_max: float = 9.0,
                  angulo: float = 180.0, dry: bool = False) -> None:
    """Entrada 'suspendida en el aire': el plano entra movido y desenfocado,
    DECELERA hasta congelarse, y ahi se queda.

    Medido sobre el tramo del CEO de OpenAI en la referencia:

      plano 17 (foto, 1.07s)  dx -14 -> -108 px, decelerando hasta parar
      plano 19 (Altman, 1.47s) dy -1 -> -33 px en el primer 40%, luego
                               CONGELADO (-32.9, -32.3, -32.4)
      nitidez del 19: 0.27 al entrar -> 0.96 a los 0.83s

    La curva es easeOut: rapido al entrar y frenando. Es lo contrario del
    punch de salida, que es easeIn. Un plano completo lleva las dos: entra
    asi y sale con el zoom de la transicion.
    """
    import math
    info = probe(src)
    dur = info["dur"]
    t_ent = max(0.1, min(entrada * dur, 0.75))
    # u va de 1 a 0 durante la entrada; easeOutQuart = 1-(1-x)^4 invertido
    u = f"pow(max(0\\,1-t/{t_ent:.4f})\\,1)"
    suav = f"pow({u}\\,3)"                       # queda casi parado al final
    z = 1.0 + deriva_pct / 100.0
    zoom = f"(1+{z - 1:.5f}*{suav})"
    rad = math.radians(angulo)
    dx = f"({math.cos(rad):.4f}*{deriva_pct / 100.0 * W:.1f}*{suav})"
    dy = f"({math.sin(rad):.4f}*{deriva_pct / 100.0 * H:.1f}*{suav})"

    n_ent = max(1, int(round(t_ent * FPS)))
    pasos = []
    for i in range(n_ent):
        s = blur_max * ((1 - i / n_ent) ** 3)
        if s >= 0.4:
            pasos.append(f"gblur=sigma={s:.3f}:enable='eq(n,{i})'")
    rampa = ("," + ",".join(pasos)) if pasos else ""

    vf = (f"{_fit()},fps={FPS},"
          f"scale=w='ceil(iw*{zoom}/2)*2':h='ceil(ih*{zoom}/2)*2':eval=frame,"
          f"crop={W}:{H}:'(iw-{W})/2+{dx}':'(ih-{H})/2+{dy}'" + rampa)
    run(["ffmpeg", "-y", "-i", src, "-vf", vf, "-t", f"{dur:.3f}",
         "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-an", dst], dry)


def ef_invert_flash(src: str, dst: str, at: float, frames: int = 6,
                    dry: bool = False) -> None:
    """Invierte el compuesto entero durante `frames` a partir del segundo `at`.

    Se aplica con `negate` activado por ventana temporal, asi que afecta
    tambien al texto ya quemado: es justo como lo hace la referencia.
    """
    # Se activa por numero de frame, no por tiempo: between(t,a,b) es
    # inclusivo en los dos extremos y deja 7 frames cuando pides 6.
    n0 = int(round(at * FPS))
    vf = f"negate=enable='between(n,{n0},{n0 + frames - 1})'"
    run(["ffmpeg", "-y", "-i", src, "-vf", vf,
         "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "copy", dst], dry)


def ef_whip(a: str, b: str, dst: str, frames: int = 2, angulo: float = 115,
            fuerza: int = 110, dry: bool = False) -> None:
    """Une dos tomas con `frames` de desenfoque direccional.

    Toma la ultima imagen de A y la primera de B, las funde y les mete un
    barrido direccional. Esconde el jump cut del mismo encuadre.
    """
    ia, ib = probe(a), probe(b)
    dur = frames / FPS
    # radio del desenfoque descompuesto en sus componentes
    import math
    rad = math.radians(angulo)
    sx = max(1, int(abs(math.cos(rad)) * fuerza))
    sy = max(1, int(abs(math.sin(rad)) * fuerza))
    fc = (
        f"[0:v]{_fit()},trim=start={max(0, ia['dur'] - 1/FPS)},setpts=PTS-STARTPTS,"
        f"loop=loop={frames}:size=1:start=0,setpts=N/{FPS}/TB[tail];"
        f"[1:v]{_fit()},trim=duration={1/FPS},setpts=PTS-STARTPTS,"
        f"loop=loop={frames}:size=1:start=0,setpts=N/{FPS}/TB[head];"
        f"[tail][head]blend=all_mode=average,"
        f"boxblur={sx}:1:{sy}:1,eq=brightness=0.06:contrast=1.08,"
        f"trim=duration={dur},setpts=PTS-STARTPTS[whip];"
        f"[0:v]{_fit()}[va];[1:v]{_fit()}[vb];"
        f"[va][whip][vb]concat=n=3:v=1:a=0[v]"
    )
    run(["ffmpeg", "-y", "-i", a, "-i", b, "-filter_complex", fc,
         "-map", "[v]", "-r", str(FPS), "-c:v", "libx264", "-crf", "16",
         "-preset", "medium", "-pix_fmt", "yuv420p", dst], dry)


def ef_zoomblur_cut(a: str, b: str, dst: str, f_out: int = 5, f_in: int = 5,
                    zoom_pct: float = 7.0, blur_max: int = 26,
                    dry: bool = False) -> None:
    """Corte en el que A acelera zoom y se desenfoca, y B resuelve de blur.

    Este es EL movimiento de la pieza: el zoom vive aqui, no en el plano.
    """
    ia, ib = probe(a), probe(b)
    da, db = ia["dur"], ib["dur"]
    t_out = f_out / FPS          # cuando arranca la rampa de salida en A
    t_in = f_in / FPS            # cuanto dura la resolucion en B
    r_out = max(0.0, da - t_out)
    z = 1.0 + zoom_pct / 100.0

    ua = f"max(0\\,(t-{r_out:.4f})/{t_out:.4f})"
    zoom_a = f"(1+{z - 1:.6f}*pow(min({ua}\\,1)\\,4))"
    # la rampa de A arranca en su frame (total - f_out)
    n_inicio_a = max(0, int(round(da * FPS)) - f_out)
    ramp_a = _blur_ramp(f_out, blur_max, offset_frames=n_inicio_a)
    ramp_b = _blur_ramp(f_in, blur_max, invertida=True, offset_frames=0)

    fc = (
        f"[0:v]{_fit()},fps={FPS},"
        f"scale=w='ceil(iw*{zoom_a}/2)*2':h='ceil(ih*{zoom_a}/2)*2':eval=frame,"
        f"crop={W}:{H}:'(iw-{W})/2':'(ih-{H})/2'"
        + (f",{ramp_a}" if ramp_a else "") + "[va];"
        f"[1:v]{_fit()},fps={FPS}"
        + (f",{ramp_b}" if ramp_b else "") + "[vb];"
        f"[va][vb]concat=n=2:v=1:a=0[v]"
    )
    run(["ffmpeg", "-y", "-i", a, "-i", b, "-filter_complex", fc,
         "-map", "[v]", "-r", str(FPS), "-c:v", "libx264", "-crf", "16",
         "-preset", "medium", "-pix_fmt", "yuv420p", dst], dry)


def ef_white_card(texto: str, dst: str, dur: float = 0.67,
                  fuente: str | None = None, acento: str | None = None,
                  dry: bool = False) -> None:
    """Tarjeta blanca con texto negro en la linea central.

    `acento` es una palabra opcional que se pinta en serif italica naranja.
    """
    p = PRESET
    bg = p["transiciones"]["tarjeta_blanca"]["fondo"]
    fg = p["transiciones"]["tarjeta_blanca"]["texto"]
    y = p["rejilla_subtitulos"]["linea_base_y"]
    size = int(H * p["tipografia"]["escalas_alto_caja_pct_alto_lienzo"]["normal"] / 100 * 1.38)
    fuente = fuente or _buscar_fuente()
    esc = texto.replace("'", "’").replace(":", "\\:")
    df = (f"drawtext=text='{esc}':fontsize={size}:fontcolor={fg}:"
          f"x=(w-text_w)/2:y={y}*h-text_h/2")
    if fuente:
        df += f":fontfile={fuente}"
    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"color=c={bg}:s={W}x{H}:r={FPS}:d={dur}",
         "-vf", df, "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", dst], dry)


def ef_motion_card(texto: str, dst: str, dur: float = 2.0, *,
                   sub: str = "", fondo: str = "#0A0A0A",
                   color: str | None = None, barra: bool = True,
                   fuente: str | None = None, dry: bool = False) -> None:
    """Tarjeta de motion graphic: texto que entra con escala y barra que carga.

    Es el recurso de la pantalla CRT de la referencia ("Loading... 13%" sobre
    un filete fino) llevado a tarjeta completa. Barata de hacer y aguanta
    bien en pantalla, que es justo para lo que sirve.
    """
    color = color or PRESET["paleta"]["texto_sobre_oscuro"]
    fuente = fuente or _buscar_fuente()
    fuente_it = _buscar_fuente(italica=True)
    size = int(H * PRESET["tipografia"]["escalas_alto_caja_pct_alto_lienzo"]["enfasis"]
               / 100 * 1.38)
    esc = lambda s: s.replace("'", "’").replace(":", "\\:").replace("%", "\\%")

    # entrada: el cuerpo crece de 0.86 a 1.0 en los primeros 0.35s, con easeOut
    ent = 0.35
    k = f"(1-0.14*pow(max(0\\,1-t/{ent})\\,3))"
    f = [f"drawtext=text='{esc(texto)}':fontsize='{size}*{k}':fontcolor={color}"
         f":x=(w-text_w)/2:y=(h-text_h)/2-{int(H*0.03)}"
         + (f":fontfile={fuente}" if fuente else "")]
    if sub:
        f.append(f"drawtext=text='{esc(sub)}':fontsize={int(size*0.32)}"
                 f":fontcolor={color}@0.72:x=(w-text_w)/2:y=(h-text_h)/2+{int(H*0.09)}"
                 + (f":fontfile={fuente_it}" if fuente_it else ""))
    if barra:
        bw, bh = int(W * 0.34), max(2, int(H * 0.006))
        bx, by = (W - bw) // 2, int(H * 0.70)
        f.append(f"drawbox=x={bx}:y={by}:w={bw}:h={bh}:color={color}@0.30:t=fill")
        # el relleno avanza con el tiempo, easeInOut
        av = f"min(1\\,t/{max(dur-0.2,0.1):.3f})"
        f.append(f"drawbox=x={bx}:y={by}:w='{bw}*({av})':h={bh}:color={color}:t=fill")
    f.append("noise=alls=4:allf=t")
    f.append("format=yuv420p")

    run(["ffmpeg", "-y", "-f", "lavfi",
         "-i", f"color=c={fondo}:s={W}x{H}:r={FPS}:d={dur}",
         "-vf", ",".join(f), "-c:v", "libx264", "-crf", "16",
         "-preset", "medium", dst], dry)


def ef_endcard(dst: str, dur: float | None = None, dry: bool = False) -> None:
    """Cierre: diana concentrica blanca sobre negro."""
    e = PRESET["endcard"]
    dur = dur or e["duracion_s"]
    d = e["logo"]["diametro_pct_ancho"] * W
    cx, cy = W / 2, H / 2
    r1, r2, r3 = d / 2, d / 2 * 0.62, d / 2 * 0.26
    grosor = d * 0.085
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">
<rect width="{W}" height="{H}" fill="{e['fondo']}"/>
<circle cx="{cx}" cy="{cy}" r="{r1}" fill="none" stroke="{e['logo']['color']}" stroke-width="{grosor}"/>
<circle cx="{cx}" cy="{cy}" r="{r2}" fill="none" stroke="{e['logo']['color']}" stroke-width="{grosor}"/>
<circle cx="{cx}" cy="{cy}" r="{r3}" fill="{e['logo']['color']}"/>
</svg>'''
    tmp = pathlib.Path(dst).with_suffix(".svg")
    tmp.write_text(svg, encoding="utf-8")
    png = pathlib.Path(dst).with_suffix(".png")
    run(["ffmpeg", "-y", "-i", str(tmp), "-frames:v", "1", str(png)], dry)
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(png), "-t", str(dur),
         "-r", str(FPS), "-vf", "format=yuv420p",
         "-c:v", "libx264", "-crf", "16", "-preset", "medium", dst], dry)


def ef_crt(src: str, dst: str, dry: bool = False) -> None:
    """Tele vieja: scanlines + aberracion cromatica + barril + vineta + bloom."""
    c = PRESET["pixel_crt"]["pantalla_crt"]
    k = c["barril"]
    sl_op = c["scanlines"]["opacidad"]
    # la aberracion se midio sobre 960 de ancho: se reescala al lienzo
    dx = max(1, int(round(2 * W / 960)))
    mask = _scanlines_png(c["scanlines"]["periodo_px_en_960"])
    fc = (
        # Separacion RGB. Los blend operan en el espacio de entrada: si llegan
        # en yuv420p la suma NO reconstruye el color y todo vira a magenta.
        # Hay que forzar rgb24 en las tres ramas antes de sumar.
        f"[0:v]{_fit()},fps={FPS},format=rgb24,split=3[r][g][b];"
        f"[r]lutrgb=g=0:b=0,crop={W - dx}:{H}:{dx}:0,pad={W}:{H}:0:0,format=rgb24[r2];"
        f"[g]lutrgb=r=0:b=0,format=rgb24[g2];"
        f"[b]lutrgb=r=0:g=0,crop={W - dx}:{H}:0:0,pad={W}:{H}:{dx}:0,format=rgb24[b2];"
        f"[r2][g2]blend=all_mode=addition[rg];"
        f"[rg][b2]blend=all_mode=addition,format=rgb24[rgb];"
        # scanlines desde mascara cacheada: geq a 1080x1920 es inviable.
        # La mascara va en rgb24, NO en gray: blend negocia un formato comun y
        # con una entrada gray el resultado sale en blanco y negro.
        f"[1:v]scale={W}:{H}:flags=neighbor,format=rgb24[mask];"
        f"[rgb][mask]blend=all_mode=multiply:all_opacity={sl_op}[scan];"
        # barril + vineta, luego bloom por screen
        # overscan tras el barril: se come las esquinas negras y el peor
        # flecado magenta que deja el desplazamiento RGB en el borde
        f"[scan]lenscorrection=k1={k}:k2={k * 0.3:.4f},"
        f"scale={int(W * 1.06)}:{int(H * 1.06)},crop={W}:{H},"
        f"vignette=angle=PI/{4.0 + (1 - c['vineta']) * 2:.2f},"
        # format=rgb24 explicito antes del split y en AMBAS ramas del blend.
        # Tras una cadena de blend la negociacion acaba en un formato planar
        # y el screen mezcla los planos en otro orden: el verde se hunde y
        # todo vira a magenta. Este format es obligatorio, no cosmetico.
        f"format=rgb24,split=2[scan1][scan2];"
        f"[scan2]gblur=sigma=6,format=rgb24[blur];"
        f"[scan1]format=rgb24[scan1b];"
        f"[scan1b][blur]blend=all_mode=screen:all_opacity={c['bloom']},"
        f"format=rgb24[v]"
    )
    # el PNG en bucle es un stream infinito y -shortest no se propaga bien a
    # traves de los blend: se acota con -t a la duracion real de la fuente
    run(["ffmpeg", "-y", "-i", src,
         "-loop", "1", "-t", f"{probe(src)['dur']:.3f}", "-i", str(mask),
         "-filter_complex", fc, "-map", "[v]", "-shortest",
         "-r", str(FPS), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", dst], dry)


def ef_pixel_text(palabra: str, dst: str, dur: float = 2.2,
                  fuente: str | None = None, dry: bool = False) -> None:
    """Palabra bitmap gigante con scanlines y bloom, sobre alfa.

    Sale un .mov con canal alfa para montarlo DETRAS del sujeto recortado.
    """
    p = PRESET["pixel_crt"]["texto_pixelado"]
    cuerpo = p["color_cuerpo"]
    bloque = max(2, int(p["bloque_pct_ancho"] * W))
    size = int(H * 0.16)
    fuente = fuente or _buscar_fuente(bitmap=True)
    df = (f"drawtext=text='{palabra}':fontsize={size}:fontcolor={cuerpo}:"
          f"x=(w-text_w)/2:y=(h-text_h)/2")
    if fuente:
        df += f":fontfile={fuente}"
    # pixelado real: bajar y subir con vecino mas proximo
    small_w, small_h = max(8, W // bloque), max(8, H // bloque)
    mask = _scanlines_png(p["scanlines"]["periodo_px_en_960"])
    fc = (
        f"color=c=black@0:s={W}x{H}:r={FPS}:d={dur},format=rgba,{df},"
        f"scale={small_w}:{small_h}:flags=neighbor,"
        f"scale={W}:{H}:flags=neighbor,split=2[px][gl];"
        # El bloom se aplica SOLO como halo: a opacidad alta el screen blanquea
        # la letra entera y se pierde el verde-oro. El nucleo blanco de la
        # referencia sale del propio clipping, no de subir esta mezcla.
        f"[gl]gblur=sigma={p['bloom']['radio_px_1080'] // 2},format=rgba[glow];"
        f"[px]format=rgba[pxb];"
        f"[pxb][glow]blend=all_mode=screen:all_opacity={p['bloom']['intensidad'] * 0.55:.2f},"
        f"format=rgba[lit];"
        # la mascara va en rgba, no en gray, o el blend desatura la letra
        f"[0:v]scale={W}:{H}:flags=neighbor,format=rgba[mask];"
        f"[lit][mask]blend=all_mode=multiply:all_opacity={p['scanlines']['opacidad']},"
        f"format=rgba[v]"
    )
    run(["ffmpeg", "-y", "-loop", "1", "-t", str(dur), "-i", str(mask),
         "-filter_complex", fc, "-map", "[v]",
         "-c:v", "qtrle", "-pix_fmt", "argb", dst], dry)


def ef_captions(src: str, dst: str, plan_path: str, fuente: str | None = None,
                dry: bool = False) -> None:
    """Quema subtitulos palabra a palabra segun un plan JSON.

    Formato del plan:
      [{"palabra":"criterio","t_in":1.2,"t_out":3.4,"x":0.28,
        "escala":"enfasis","color":"#FFFFFF","italica":false}, ...]
    x es 0-1 (centro de la palabra). y sale de la rejilla del preset.
    """
    plan = json.loads(pathlib.Path(plan_path).read_text(encoding="utf-8"))
    g = PRESET["rejilla_subtitulos"]
    esc_tipo = PRESET["tipografia"]["escalas_alto_caja_pct_alto_lienzo"]
    som = PRESET["tipografia"]["sombra"]
    fuente = fuente or _buscar_fuente()
    fuente_it = _buscar_fuente(italica=True)

    partes, negativos = [], []
    for w in plan:
        # `px` explicito gana sobre la escala: una palabra larga en escala
        # enfasis no cabe en 1080 de ancho y hay que encogerla al ancho util.
        size = int(w.get("px") or
                   H * esc_tipo[w.get("escala", "normal")] / 100 * 1.38)
        y = w.get("y", g["linea_base_y"])
        col = w.get("color", PRESET["paleta"]["texto_sobre_oscuro"])
        txt = str(w["palabra"]).replace("'", "’").replace(":", "\\:")
        ff = fuente_it if w.get("italica") else fuente
        base = (f"fontsize={size}:y={y}*h-text_h/2"
                f":enable='between(t,{w['t_in']},{w['t_out']})'"
                + (f":fontfile={ff}" if ff else ""))

        if w.get("negativo"):
            # El texto en negativo NO son bordes de color: la palabra actua de
            # mascara e INVIERTE lo que tiene detras, semitranslucido. Se
            # resuelve aparte, en ef_captions, con maskedmerge sobre una copia
            # invertida del plano. Aqui solo se recoge para esa pasada.
            negativos.append((txt, w, size, ff))
            continue

        partes.append(f"drawtext=text='{txt}':fontcolor={col}"
                      f":x={w['x']}*w-text_w/2:{base}"
                      f":shadowcolor=black@{som['opacidad']}"
                      f":shadowx={som['desplazamiento_px_1080'][0]}"
                      f":shadowy={som['desplazamiento_px_1080'][1]}")

    vf = _fit() + ("," + ",".join(partes) if partes else "")

    if not negativos:
        run(["ffmpeg", "-y", "-i", src, "-vf", vf, "-r", str(FPS),
             "-c:v", "libx264", "-crf", "16", "-preset", "medium",
             "-pix_fmt", "yuv420p", "-c:a", "copy", dst], dry)
        return

    # --- texto en negativo -------------------------------------------------
    # La palabra no se pinta: recorta. Se construye una mascara con las
    # palabras en blanco sobre negro y se usa con maskedmerge para que dentro
    # de la letra se vea el plano INVERTIDO y fuera el normal. Un gris en vez
    # de blanco puro deja el efecto semitranslucido, que es como se ve en los
    # ejemplos.
    mask_parts = []
    for txt, w, size, ff in negativos:
        gris = int(255 * float(w.get("negativo_fuerza", 0.88)))
        mask_parts.append(
            f"drawtext=text='{txt}':fontcolor=0x{gris:02X}{gris:02X}{gris:02X}"
            f":fontsize={size}:x={w['x']}*w-text_w/2:y={w.get('y', g['linea_base_y'])}*h-text_h/2"
            f":enable='between(t,{w['t_in']},{w['t_out']})'"
            + (f":fontfile={ff}" if ff else ""))

    # La fuente `color` del mask es un stream infinito y maskedmerge no
    # propaga el EOF: sin acotarla con :d= el render no termina nunca y el
    # fichero crece sin limite. Se fija a la duracion real de la entrada.
    dur = probe(src)["dur"]
    fc = (
        f"[0:v]{_fit()},fps={FPS}"
        + (f",{','.join(partes)}" if partes else "")
        # gbrp (RGB planar), no rgb24: maskedmerge opera por PLANOS y con un
        # formato empaquetado colapsa la imagen a blanco y negro.
        + ",format=gbrp,split=2[base][toinv];"
        f"[toinv]negate,format=gbrp[inv];"
        f"color=black:s={W}x{H}:r={FPS}:d={dur:.3f},{','.join(mask_parts)},"
        f"format=gbrp[mask];"
        f"[base][inv][mask]maskedmerge,format=yuv420p[v]"
    )
    run(["ffmpeg", "-y", "-i", src, "-filter_complex", fc, "-map", "[v]",
         "-map", "0:a?", "-t", f"{dur:.3f}", "-r", str(FPS),
         "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "copy", dst], dry)


def _buscar_fuente(italica: bool = False, bitmap: bool = False) -> str | None:
    """Localiza una fuente utilizable en el sistema."""
    cands = []
    if bitmap:
        cands = ["Silkscreen", "PressStart2P", "Pixelify", "VT323", "DejaVuSansMono"]
    elif italica:
        cands = ["PlayfairDisplay-Italic", "EBGaramond-Italic", "DejaVuSerif-Italic",
                 "DejaVuSans-Oblique"]
    else:
        # Inter600 primero: es la sustituta libre mas cercana a SF Pro, que
        # es la familia a la que se parece la tipografia de la referencia.
        cands = ["Inter600", "Inter700", "Inter", "HelveticaNow", "Satoshi",
                 "DejaVuSans-Bold", "DejaVuSans"]
    locales = (RAIZ / "assets" / "fonts")
    for c in cands:
        for ext in (".ttf", ".otf"):
            p = locales / f"{c}{ext}"
            if p.exists():
                return str(p)
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}", cands[-1]],
                             capture_output=True, text=True).stdout.strip()
        if out:
            return out
    except FileNotFoundError:
        pass
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if pathlib.Path(p).exists():
            return p
    return None


# ----------------------------------------------------------------------- cli


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    ap.add_argument("--dry", action="store_true", help="solo imprime los comandos")

    s = sub.add_parser("punch"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--pct", type=float, default=7.0)
    s.add_argument("--reposo", type=float, default=0.85)

    s = sub.add_parser("suspendido"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--deriva", type=float, default=9.0)
    s.add_argument("--entrada", type=float, default=0.42)
    s.add_argument("--blur", type=float, default=9.0)
    s.add_argument("--angulo", type=float, default=180.0)

    s = sub.add_parser("invert-flash"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--at", type=float, required=True)
    s.add_argument("--frames", type=int, default=6)

    s = sub.add_parser("whip"); s.add_argument("a"); s.add_argument("b")
    s.add_argument("dst"); s.add_argument("--frames", type=int, default=2)
    s.add_argument("--angulo", type=float, default=115)
    s.add_argument("--fuerza", type=int, default=110)

    s = sub.add_parser("zoomblur-cut"); s.add_argument("a"); s.add_argument("b")
    s.add_argument("dst"); s.add_argument("--f-out", type=int, default=5)
    s.add_argument("--f-in", type=int, default=5)
    s.add_argument("--zoom-pct", type=float, default=7.0)

    s = sub.add_parser("white-card"); s.add_argument("texto"); s.add_argument("dst")
    s.add_argument("--dur", type=float, default=0.67)

    s = sub.add_parser("motion-card"); s.add_argument("texto"); s.add_argument("dst")
    s.add_argument("--dur", type=float, default=2.0)
    s.add_argument("--sub", default="")
    s.add_argument("--fondo", default="#0A0A0A")
    s.add_argument("--color", default=None)
    s.add_argument("--sin-barra", action="store_true")

    s = sub.add_parser("endcard"); s.add_argument("dst")
    s.add_argument("--dur", type=float, default=None)

    s = sub.add_parser("crt"); s.add_argument("src"); s.add_argument("dst")

    s = sub.add_parser("pixel-text"); s.add_argument("palabra"); s.add_argument("dst")
    s.add_argument("--dur", type=float, default=2.2)

    s = sub.add_parser("captions"); s.add_argument("src"); s.add_argument("dst")
    s.add_argument("--plan", required=True)

    s = sub.add_parser("probe"); s.add_argument("src")

    a = ap.parse_args()
    d = a.dry
    if a.cmd == "punch":
        ef_punch(a.src, a.dst, a.pct, a.reposo, dry=d)
    elif a.cmd == "suspendido":
        ef_suspendido(a.src, a.dst, deriva_pct=a.deriva, entrada=a.entrada,
                      blur_max=a.blur, angulo=a.angulo, dry=d)
    elif a.cmd == "invert-flash":
        ef_invert_flash(a.src, a.dst, a.at, a.frames, dry=d)
    elif a.cmd == "whip":
        ef_whip(a.a, a.b, a.dst, a.frames, a.angulo, a.fuerza, dry=d)
    elif a.cmd == "zoomblur-cut":
        ef_zoomblur_cut(a.a, a.b, a.dst, a.f_out, a.f_in, a.zoom_pct, dry=d)
    elif a.cmd == "white-card":
        ef_white_card(a.texto, a.dst, a.dur, dry=d)
    elif a.cmd == "motion-card":
        ef_motion_card(a.texto, a.dst, a.dur, sub=a.sub, fondo=a.fondo,
                       color=a.color, barra=not a.sin_barra, dry=d)
    elif a.cmd == "endcard":
        ef_endcard(a.dst, a.dur, dry=d)
    elif a.cmd == "crt":
        ef_crt(a.src, a.dst, dry=d)
    elif a.cmd == "pixel-text":
        ef_pixel_text(a.palabra, a.dst, a.dur, dry=d)
    elif a.cmd == "captions":
        ef_captions(a.src, a.dst, a.plan, dry=d)
    elif a.cmd == "probe":
        print(json.dumps(probe(a.src), indent=2))


if __name__ == "__main__":
    main()
