#!/usr/bin/env python3
"""
pixeltext - texto bitmap estilo CRT, con fuente real y rejilla exacta.

Reemplaza al drawtext+pixelate de reelfx, que daba un vectorial pobre con la
fuente de respaldo del sistema. Aqui la letra se dibuja con una fuente bitmap
de verdad sobre un lienzo pequeno y se amplia con vecino mas proximo, asi que
los bloques caen en una rejilla exacta en vez de ser un reescalado sucio.

La referencia es un CONTORNO HUECO: el relleno se quita y queda solo el borde,
de unos 2 bloques de grosor.

Uso:
    python3 tools/pixeltext.py ORO salida.png --fuente Silkscreen
    python3 tools/pixeltext.py ORO salida.mov --dur 2.2
    python3 tools/pixeltext.py --comparar   # barrido de fuentes vs referencia
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PRESET = json.loads((RAIZ / "presets" / "estilo-2027.json").read_text(encoding="utf-8"))
FUENTES = RAIZ / "assets" / "fonts"

P = PRESET["pixel_crt"]["texto_pixelado"]


def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def render(texto: str, ancho: int, alto: int, *, fuente: str = "Silkscreen",
           bloque: int | None = None, alto_glifo_pct: float = 0.37,
           hueco: bool = True, grosor: int = 2,
           color: str | None = None, scanline_periodo: int = 2,
           scanline_op: float = 0.45, glow_radio: int = 26,
           glow_int: float = 0.55, y_centro: float = 0.29,
           tracking: float = 0.0) -> Image.Image:
    """Devuelve una RGBA con el texto bitmap ya pixelado, con scanlines y glow.

    bloque: lado del bloque en px del lienzo final. Si es None sale del preset
            (1.77% del ancho), que es lo medido en la referencia.
    """
    color = color or P["color_cuerpo"]
    if bloque is None:
        bloque = max(2, round(P["bloque_pct_ancho"] * ancho))

    ruta = FUENTES / f"{fuente}.ttf"
    if not ruta.exists():
        raise SystemExit(f"falta la fuente {ruta}. Descargala primero; sin una "
                         f"bitmap real la letra no tiene la forma correcta.")

    # ORDEN QUE IMPORTA: se dibuja y se saca el contorno a RESOLUCION COMPLETA,
    # y se pixela al final. Al reves (pixelar y luego erosionar) la erosion se
    # come un glifo que ya solo tiene 2-3 celdas de trazo y el anillo sale roto.
    grande = Image.new("L", (ancho, alto), 0)
    d = ImageDraw.Draw(grande)

    objetivo = alto_glifo_pct * alto

    def _tinta(size):
        """Dibuja y devuelve la caja de TINTA real, no las metricas de linea.

        textbbox incluye ascendente y descendente de la fuente, que para
        mayusculas sin descendentes sobran: fiarse de el dejaba los renders
        un 40% mas grandes que la referencia.
        """
        f = ImageFont.truetype(str(ruta), size)
        esp = tracking * size
        prueba = Image.new("L", (ancho, alto), 0)
        dp = ImageDraw.Draw(prueba)
        x = 0.0
        for c in texto:
            dp.text((x, alto * 0.25), c, font=f, fill=255)
            x += f.getlength(c) + esp
        a = np.array(prueba)
        ys, xs = np.where(a > 60)
        if len(ys) == 0:
            return f, None
        return f, (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)

    # estimacion lineal y despues ajuste fino, midiendo la tinta cada vez
    f0, t0 = _tinta(100)
    if t0 is None:
        raise SystemExit("la fuente no dibujo nada")
    est = max(8, int(round(100 * objetivo / max(1, t0[3] - t0[1]))))

    mejor, mejor_err = None, 1e9
    for size in range(max(8, est - 8), est + 9):
        f, t = _tinta(size)
        if t is None:
            continue
        gw, gh = t[2] - t[0], t[3] - t[1]
        if gw > ancho * 0.97:
            continue
        err = abs(gh - objetivo)
        if err < mejor_err:
            mejor, mejor_err = (size, f, t), err
    if mejor is None:
        for size in range(est, 7, -1):
            f, t = _tinta(size)
            if t is not None and (t[2] - t[0]) <= ancho * 0.97:
                mejor = (size, f, t)
                break
    if mejor is None:
        raise SystemExit("no se encontro un tamano de fuente que encaje")
    size, f, tinta = mejor

    # tracking: PIL no separa letras, asi que se dibujan una a una. La
    # referencia tiene huecos claros entre las letras y sin esto salen pegadas.
    esp = tracking * size
    # se dibuja en origen y despues se traslada por la caja de tinta medida,
    # asi el encuadre no depende de las metricas de la fuente
    tmp = Image.new("L", (ancho, alto), 0)
    dt = ImageDraw.Draw(tmp)
    x = 0.0
    for c in texto:
        dt.text((x, alto * 0.25), c, font=f, fill=255)
        x += f.getlength(c) + esp
    dx = int(round((ancho - (tinta[2] - tinta[0])) / 2 - tinta[0]))
    dy = int(round(y_centro * alto - (tinta[3] - tinta[1]) / 2 - tinta[1]))
    grande.paste(tmp.transform(tmp.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy)),
                 (0, 0))

    a = np.array(grande)
    if hueco:
        # anillo centrado en el borde del glifo: dilatacion menos erosion.
        # `grosor` va en bloques, asi que el radio se expresa en px del lienzo.
        r = max(1, int(round(grosor * bloque / 2)))
        k = 1 + 2 * r
        im = Image.fromarray(a)
        dil = np.array(im.filter(ImageFilter.MaxFilter(k))).astype(np.int16)
        ero = np.array(im.filter(ImageFilter.MinFilter(k))).astype(np.int16)
        a = np.clip(dil - ero, 0, 255).astype(np.uint8)

    # --- pixelar al final: promedio por bloque y umbral, luego vecino mas
    # proximo. El promedio evita que un anillo fino desaparezca al reducir.
    w, h = max(8, ancho // bloque), max(8, alto // bloque)
    chico = Image.fromarray(a).resize((w, h), Image.BOX)
    ch = np.array(chico)
    ch = ((ch > 90) * 255).astype(np.uint8)
    mask = Image.fromarray(ch).resize((w * bloque, h * bloque), Image.NEAREST)
    mask = mask.crop((0, 0, ancho, alto))
    if mask.size != (ancho, alto):
        lienzo = Image.new("L", (ancho, alto), 0)
        lienzo.paste(mask, (0, 0))
        mask = lienzo

    rgb = Image.new("RGB", (ancho, alto), _hex(color))
    capa = Image.merge("RGBA", (*rgb.split(), mask))

    # --- scanlines: lineas oscuras cada `periodo` px, solo sobre la letra
    filas = (np.arange(alto) % scanline_periodo == 0).astype(np.float32)
    att = 1.0 - scanline_op * (1.0 - filas)
    arr = np.array(capa).astype(np.float32)
    arr[:, :, :3] *= att[:, None, None]
    capa = Image.fromarray(arr.astype(np.uint8), "RGBA")

    # --- glow: copia desenfocada por debajo, que es lo que revienta el nucleo
    halo = capa.filter(ImageFilter.GaussianBlur(glow_radio))
    ha = np.array(halo).astype(np.float32)
    ha[:, :, 3] *= glow_int
    halo = Image.fromarray(np.clip(ha, 0, 255).astype(np.uint8), "RGBA")
    out = Image.alpha_composite(halo, capa)
    return out


def comparar(ref: str, salida: str) -> None:
    """Renderiza la misma palabra con cada fuente y la pone junto a la referencia."""
    r = Image.open(ref).convert("RGB")
    W, H = r.size
    tiras = [r]
    etiquetas = ["REFERENCIA"]
    for fu in ["Silkscreen", "PressStart2P", "PixelifySans", "VT323"]:
        if not (FUENTES / f"{fu}.ttf").exists():
            continue
        im = render("ORO", W, H, fuente=fu)
        fondo = Image.new("RGB", (W, H), (28, 26, 24))
        fondo.paste(im, (0, 0), im)
        tiras.append(fondo)
        etiquetas.append(fu)
    tot = Image.new("RGB", (W * len(tiras) + 8 * (len(tiras) - 1), H + 26), (20, 20, 20))
    d = ImageDraw.Draw(tot)
    for i, (t, e) in enumerate(zip(tiras, etiquetas)):
        x = i * (W + 8)
        tot.paste(t, (x, 26))
        d.text((x + 6, 6), e, fill=(255, 220, 60))
    tot.save(salida)
    print(f"comparacion -> {salida}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("texto", nargs="?")
    ap.add_argument("salida", nargs="?")
    ap.add_argument("--fuente", default="Silkscreen")
    ap.add_argument("--ancho", type=int, default=PRESET["lienzo"]["ancho"])
    ap.add_argument("--alto", type=int, default=PRESET["lienzo"]["alto"])
    ap.add_argument("--bloque", type=int, default=None)
    ap.add_argument("--grosor", type=int, default=2)
    ap.add_argument("--alto-glifo", type=float, default=0.37)
    ap.add_argument("--y", type=float, default=0.29)
    ap.add_argument("--tracking", type=float, default=0.0)
    ap.add_argument("--glow-radio", type=int, default=26)
    ap.add_argument("--glow-int", type=float, default=0.55)
    ap.add_argument("--scan-op", type=float, default=0.45)
    ap.add_argument("--solido", action="store_true", help="relleno en vez de contorno")
    ap.add_argument("--dur", type=float, default=2.2)
    ap.add_argument("--comparar", metavar="REF", help="barrido de fuentes contra una referencia")
    ap.add_argument("--comparar-salida", default="/tmp/comparacion_fuentes.png")
    a = ap.parse_args()

    if a.comparar:
        comparar(a.comparar, a.comparar_salida)
        return
    if not a.texto or not a.salida:
        raise SystemExit("hacen falta TEXTO y SALIDA (o bien --comparar REF)")

    im = render(a.texto, a.ancho, a.alto, fuente=a.fuente, bloque=a.bloque,
                alto_glifo_pct=a.alto_glifo, hueco=not a.solido, grosor=a.grosor,
                scanline_op=a.scan_op, glow_radio=a.glow_radio,
                glow_int=a.glow_int, y_centro=a.y, tracking=a.tracking)

    if a.salida.endswith(".png"):
        im.save(a.salida)
    else:
        tmp = pathlib.Path(a.salida).with_suffix(".png")
        im.save(tmp)
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-t", str(a.dur),
                        "-i", str(tmp), "-r", str(PRESET["lienzo"]["fps"]),
                        "-c:v", "qtrle", "-pix_fmt", "argb", a.salida], check=True)
    print(f"listo: {a.salida}")


if __name__ == "__main__":
    main()
