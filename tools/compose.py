#!/usr/bin/env python3
"""
compose / matte - texto pixelado DETRAS del sujeto.

Es el detalle que separa la copia buena de la mala: en la referencia la cabeza
del presentador tapa la letra central. Texto delante = plantilla. Texto detras
= composicion, y eso exige una mascara del cuerpo.

El apilado es: fondo (A-roll) < capa de texto < sujeto recortado.

Uso:
    # 1. sacar el sujeto recortado con alfa
    python3 tools/compose.py matte aroll.mp4 capas/sujeto.mov

    # 2. componer las tres capas
    python3 tools/compose.py build aroll.mp4 capas/oro.mov capas/sujeto.mov salida.mp4
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reelfx  # noqa: E402

AYUDA_MATTE = """
No hay motor de recorte disponible.

Opcion A - instalarlo aqui (descarga pesos):
    pip install rembg onnxruntime
    python3 tools/compose.py matte aroll.mp4 capas/sujeto.mov

Opcion B - hacerlo en el editor, que es lo que hace la referencia:
    After Effects: Roto Brush sobre la capa de A-roll
    Premiere: efecto Mascara de Opacidad / Seleccion de sujeto
    DaVinci: Magic Mask
    Exporta con alfa (ProRes 4444 o QuickTime RLE) y pasa a 'build'.

Opcion C - rodarlo resuelto:
    Si el plano se graba sobre fondo liso, un croma simple basta y no hace
    falta recorte por modelo.
"""


def matte(src: str, dst: str, fps: int = 30) -> None:
    """Recorta el sujeto frame a frame y deja un .mov con alfa."""
    try:
        from rembg import new_session, remove
        from PIL import Image
    except ImportError:
        print(AYUDA_MATTE, file=sys.stderr)
        raise SystemExit(2)

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="matte_"))
    crudo, recortado = tmp / "in", tmp / "out"
    crudo.mkdir()
    recortado.mkdir()

    reelfx.run(["ffmpeg", "-y", "-i", src, "-vf", f"{reelfx._fit()},fps={fps}",
                str(crudo / "f_%05d.png")])

    ses = new_session("u2net_human_seg")
    files = sorted(crudo.glob("f_*.png"))
    print(f"recortando {len(files)} frames", file=sys.stderr)
    for i, f in enumerate(files):
        out = remove(Image.open(f), session=ses)
        out.save(recortado / f.name)
        if i % 30 == 0:
            print(f"  {i}/{len(files)}", file=sys.stderr)

    reelfx.run(["ffmpeg", "-y", "-framerate", str(fps),
                "-i", str(recortado / "f_%05d.png"),
                "-c:v", "qtrle", "-pix_fmt", "argb", dst])
    print(f"listo: {dst}", file=sys.stderr)


def build(fondo: str, texto: str, sujeto: str, dst: str) -> None:
    """Apila fondo < texto < sujeto recortado."""
    for p in (fondo, texto, sujeto):
        if not pathlib.Path(p).exists():
            raise SystemExit(f"no existe {p}")
    W, H, FPS = reelfx.W, reelfx.H, reelfx.FPS
    fc = (
        f"[0:v]{reelfx._fit()},fps={FPS},format=rgba[bg];"
        f"[1:v]scale={W}:{H},format=rgba[txt];"
        f"[2:v]scale={W}:{H},format=rgba[suj];"
        f"[bg][txt]overlay=0:0:shortest=0:format=auto[a];"
        f"[a][suj]overlay=0:0:shortest=1:format=auto,format=yuv420p[v]"
    )
    reelfx.run(["ffmpeg", "-y", "-i", fondo, "-i", texto, "-i", sujeto,
                "-filter_complex", fc, "-map", "[v]", "-r", str(FPS),
                "-c:v", "libx264", "-crf", "16", "-preset", "medium", dst])
    print(f"listo: {dst}", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("matte"); s.add_argument("src"); s.add_argument("dst")
    s = sub.add_parser("build")
    s.add_argument("fondo"); s.add_argument("texto")
    s.add_argument("sujeto"); s.add_argument("dst")
    a = ap.parse_args()
    if a.cmd == "matte":
        matte(a.src, a.dst)
    else:
        build(a.fondo, a.texto, a.sujeto, a.dst)


if __name__ == "__main__":
    main()
