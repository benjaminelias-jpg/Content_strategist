#!/usr/bin/env python3
"""
grade_match - iguala el color de cualquier plano al look de la referencia.

El problema que resuelve: material de origen distinto (A-roll de movil, b-roll
generado, stock) llega con saturaciones y luminancias que no tienen nada que
ver entre si, y pegado sin tratar se ve como lo que es, un collage. En la
referencia TODO pasa por el mismo grade y por eso la pieza se lee como una.

Como funciona: mide los percentiles 1/50/90 por canal del plano, y construye
una curva por canal que los lleva a los de la referencia. Despues aplica el
look comun (saturacion objetivo, vineta y grano).

El look medido sobre el A-roll limpio de la referencia:
    sombras  R  8  G 11  B 13   <- frias, el azul por encima del rojo
    medios   R 58  G 58  B 53
    altas    R160  G140  B127   <- calidas, el rojo por encima del azul
    saturacion media 58/255, luma media 68/255

Uso:
    python3 tools/grade_match.py entrada.mp4 salida.mp4
    python3 tools/grade_match.py foto.png salida.mp4 --dur 1.2 --lienzo 1920x1080
    python3 tools/grade_match.py entrada.mp4 --solo-medir
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

import cv2
import numpy as np

# percentiles objetivo (R, G, B) medidos sobre la referencia
OBJETIVO = {1: (8.0, 11.0, 13.0), 50: (58.0, 58.0, 53.0), 90: (160.0, 140.0, 127.0)}
SAT_OBJETIVO = 58.0
IMAGENES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _recorta(im, region):
    """region = (x0,y0,x1,y1) normalizado, o None."""
    if not region:
        return im
    h, w = im.shape[:2]
    x0, y0, x1, y1 = region
    return im[int(y0 * h):max(int(y0 * h) + 1, int(y1 * h)),
              int(x0 * w):max(int(x0 * w) + 1, int(x1 * w))]


def medir(path: str, n: int = 12, region=None):
    """Percentiles por canal y saturacion media. Acepta imagen o video.

    `region` limita la medida a una caja normalizada. Hace falta para el
    A-roll: igualar el histograma GLOBAL de un plano con mucho techo claro
    arrastra al sujeto a negro, porque el techo domina los percentiles altos.
    Se mide la cara y se expone por ella, que es lo que hace la referencia.
    """
    p = pathlib.Path(path)
    if p.suffix.lower() in IMAGENES:
        im = cv2.imread(path)
        if im is None:
            raise SystemExit(f"no se pudo leer {path}")
        muestras = [cv2.resize(_recorta(im, region), (240, 240))]
    else:
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        muestras = []
        for i in range(n):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (i + 0.5) / n))
            ok, f = cap.read()
            if ok:
                muestras.append(cv2.resize(_recorta(f, region), (240, 240)))
        cap.release()
        if not muestras:
            raise SystemExit(f"no se pudo leer ningun frame de {path}")
    big = np.concatenate(muestras, axis=0)
    X = big.reshape(-1, 3).astype(np.float32)
    pct = {}
    for q in (1, 50, 90):
        b, g, r = (np.percentile(X[:, i], q) for i in range(3))
        pct[q] = (float(r), float(g), float(b))
    sat = float(cv2.cvtColor(big, cv2.COLOR_BGR2HSV)[:, :, 1].mean())
    luma = float(cv2.cvtColor(big, cv2.COLOR_BGR2GRAY).mean())
    return pct, sat, luma


SEP = 0.02      # separacion minima en x entre puntos de control


def curva(pct) -> str:
    """Curva por canal que lleva los percentiles medidos a los de la referencia.

    Tres puntos de control (sombra, medio, alta). El filtro curves rechaza la
    lista si dos x quedan demasiado juntas, y con negro puro el percentil 1 cae
    en 0 y choca con el anclaje: por eso el anclaje 0,0 solo se pone si hay
    sitio, y la separacion minima es generosa.
    """
    partes = []
    for idx, canal in enumerate("rgb"):
        pts = []
        for q in (1, 50, 90):
            x = pct[q][idx] / 255.0
            y = OBJETIVO[q][idx] / 255.0
            if pts and x < pts[-1][0] + SEP:
                x = pts[-1][0] + SEP
            pts.append((min(x, 1.0 - SEP), min(max(y, 0.0), 1.0)))
        if pts[0][0] >= SEP:
            pts.insert(0, (0.0, 0.0))
        if pts[-1][0] <= 1.0 - SEP:
            pts.append((1.0, 1.0))
        partes.append(f"{canal}='" + " ".join(f"{x:.4f}/{y:.4f}" for x, y in pts) + "'")
    return "curves=" + ":".join(partes)


def look(sat_tras_curva: float, vineta: bool = True) -> str:
    """Saturacion al objetivo, vineta y grano.

    La correccion se calcula sobre la saturacion MEDIDA DESPUES de la curva: la
    curva por canal la mueve mucho por su cuenta, y usar el valor de antes
    llevaba una imagen casi monocroma de 5.7 a 152 de saturacion.
    """
    k = max(0.15, min(2.2, SAT_OBJETIVO / max(sat_tras_curva, 1.0)))
    f = [f"eq=saturation={k:.3f}"]
    if vineta:
        f.append("vignette=angle=PI/5.0")
    f += ["noise=alls=5:allf=t", "format=yuv420p"]
    return ",".join(f)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("--lienzo", default="1920x1080")
    ap.add_argument("--dur", type=float, default=None, help="para imagen fija")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--sin-vineta", action="store_true")
    ap.add_argument("--solo-medir", action="store_true")
    ap.add_argument("--region", help="caja x0,y0,x1,y1 normalizada para medir "
                                     "solo esa zona (p.ej. la cara)")
    ap.add_argument("--objetivo-de", help="fichero del que tomar el objetivo "
                                          "en vez de los valores de la referencia")
    ap.add_argument("--objetivo-region", help="caja para medir --objetivo-de")
    a = ap.parse_args()

    caja = (lambda v: tuple(float(x) for x in v.split(",")) if v else None)
    global OBJETIVO, SAT_OBJETIVO
    if a.objetivo_de:
        OBJETIVO, SAT_OBJETIVO, _ = medir(a.objetivo_de, region=caja(a.objetivo_region))
    pct, sat, luma = medir(a.src, region=caja(a.region))
    if a.solo_medir:
        print(f"{a.src}")
        for q in (1, 50, 90):
            r, g, b = pct[q]
            tr, tg, tb = OBJETIVO[q]
            print(f"  p{q:<3} medido R{r:5.1f} G{g:5.1f} B{b:5.1f}"
                  f"   objetivo R{tr:5.1f} G{tg:5.1f} B{tb:5.1f}")
        print(f"  saturacion {sat:5.1f} -> {SAT_OBJETIVO:.0f}   luma {luma:5.1f} -> 68")
        return
    if not a.dst:
        raise SystemExit("falta la salida (o usa --solo-medir)")

    W, H = (int(v) for v in a.lienzo.lower().split("x"))
    es_img = pathlib.Path(a.src).suffix.lower() in IMAGENES
    encuadre = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H},setsar=1,fps={a.fps}")

    def corre(vf, dst, entrada=None):
        cmd = ["ffmpeg", "-y"]
        if entrada is None and es_img:
            cmd += ["-loop", "1", "-t", f"{a.dur or 2.0:.3f}"]
        cmd += ["-i", entrada or a.src, "-vf", vf, "-an",
                "-c:v", "libx264", "-crf", "16", "-preset", "medium", dst]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            sys.stderr.write(p.stderr[-2500:])
            raise SystemExit(f"ffmpeg fallo ({p.returncode})")

    # Pasada 1: la curva de igualacion.
    tmp = str(pathlib.Path(a.dst).with_suffix(".curva.mp4"))
    corre(encuadre + "," + curva(pct) + ",format=yuv420p", tmp)

    # Pasada 2 y siguientes: la saturacion, iterando. eq=saturation escala el
    # croma en YUV y su efecto sobre la S media de HSV no es lineal, asi que un
    # solo calculo se queda corto: hay que medir y volver a corregir.
    actual = tmp
    for intento in range(3):
        _, sat_c, _ = medir(actual, region=caja(a.region))
        if abs(sat_c - SAT_OBJETIVO) <= 8 and intento:
            break
        paso = str(pathlib.Path(a.dst).with_suffix(f".s{intento}.mp4"))
        ultimo = intento == 2 or abs(sat_c - SAT_OBJETIVO) <= 8
        corre(look(sat_c, (not a.sin_vineta) and ultimo) if ultimo
              else f"eq=saturation={max(0.15, min(2.2, SAT_OBJETIVO / max(sat_c, 1.0))):.3f}",
              paso, entrada=actual)
        if actual != tmp:
            pathlib.Path(actual).unlink(missing_ok=True)
        actual = paso
        if ultimo:
            break
    pathlib.Path(a.dst).unlink(missing_ok=True)
    pathlib.Path(actual).rename(a.dst)
    pathlib.Path(tmp).unlink(missing_ok=True)

    pct2, sat2, luma2 = medir(a.dst, region=caja(a.region))
    print(f"{pathlib.Path(a.src).name:<24} sat {sat:5.1f}->{sat2:5.1f} (obj {SAT_OBJETIVO:.0f})"
          f"   luma {luma:5.1f}->{luma2:5.1f} (obj 68)")


if __name__ == "__main__":
    main()
