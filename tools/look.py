#!/usr/bin/env python3
"""
look - equilibra cada plano y le aplica el look comun de la pieza.

POR QUE NO VALE IGUALAR HISTOGRAMAS (que es lo que hacia grade_match):
mapear los percentiles de un plano sobre los de otro funciona entre planos
parecidos, pero entre un interior calido con poca profundidad de campo y una
oficina plana con fluorescentes y un techo enorme, destruye el material: el
techo domina los percentiles altos y la curva arrastra la cara a negro.

Lo que hace un colorista, y lo que hace esto:

  1. EQUILIBRAR cada plano por separado. Se neutraliza la dominante midiendo
     un gris de referencia y se lleva la exposicion a un medio comun. Si se
     pasa --region, se mide ahi (la cara), no en todo el cuadro.
  2. Aplicar el MISMO LOOK a todos. Sombras frias levantadas, altas calidas,
     saturacion contenida, vineta y grano. Eso es lo que hace que planos de
     origen distinto se lean como una sola pieza.

El look sale de medir la referencia: sombras R8 G11 B13 (azul por encima del
rojo), altas R160 G140 B127 (rojo por encima del azul), saturacion media 58.

Uso:
    python3 tools/look.py entrada.mp4 salida.mp4 --region 0.34,0.26,0.55,0.60
    python3 tools/look.py foto.png salida.mp4 --dur 1.5
    python3 tools/look.py entrada.mp4 --solo-medir
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

import cv2
import numpy as np

IMAGENES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

MEDIO_OBJETIVO = 108.0     # luma del medio tras equilibrar, antes del look
SAT_OBJETIVO = 72.0        # saturacion tras el look

# Look comun. Puntos (entrada/salida) por canal, normalizados.
# Sombras: el azul sube mas que el rojo. Altas: el rojo se mantiene y el azul baja.
LOOK = {
    "r": "0/0.015 0.25/0.25 0.60/0.62 1/1",
    "g": "0/0.022 0.25/0.245 0.60/0.595 1/0.975",
    "b": "0/0.045 0.25/0.245 0.60/0.565 1/0.925",
}


def _recorta(im, region):
    if not region:
        return im
    h, w = im.shape[:2]
    x0, y0, x1, y1 = region
    return im[int(y0 * h):max(int(y0 * h) + 1, int(y1 * h)),
              int(x0 * w):max(int(x0 * w) + 1, int(x1 * w))]


def medir(path: str, n: int = 10, region=None):
    p = pathlib.Path(path)
    if p.suffix.lower() in IMAGENES:
        im = cv2.imread(path)
        if im is None:
            raise SystemExit(f"no se pudo leer {path}")
        m = [_recorta(im, region)]
    else:
        cap = cv2.VideoCapture(path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
        m = []
        for i in range(n):
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * (i + 0.5) / n))
            ok, f = cap.read()
            if ok:
                m.append(_recorta(f, region))
        cap.release()
        if not m:
            raise SystemExit(f"no se pudo leer ningun frame de {path}")
    m = [cv2.resize(x, (200, 200)) for x in m]
    big = np.concatenate(m, axis=0)
    X = big.reshape(-1, 3).astype(np.float32)
    b, g, r = (float(np.percentile(X[:, i], 55)) for i in range(3))
    return {
        "medio_rgb": (r, g, b),
        "luma": float(cv2.cvtColor(big, cv2.COLOR_BGR2GRAY).mean()),
        "sat": float(cv2.cvtColor(big, cv2.COLOR_BGR2HSV)[:, :, 1].mean()),
    }


def equilibrio(st) -> str:
    """Neutraliza la dominante y lleva el medio al nivel comun.

    Se trabaja con ganancia por canal, no con curvas: una ganancia no cambia
    la forma del contraste, solo el balance, que es justo lo que se quiere
    antes de aplicar un look.
    """
    r, g, b = st["medio_rgb"]
    gris = (r + g + b) / 3.0
    # Correccion PARCIAL de exposicion. Llevar cada plano al mismo medio borra
    # la intencion: un plano rodado oscuro a proposito se lava y uno de alta
    # clave se apaga. Se recorre la mitad del camino, que basta para que
    # convivan sin que dejen de ser lo que son.
    exp = 1.0 + (MEDIO_OBJETIVO / max(gris, 1.0) - 1.0) * 0.5
    exp = max(0.45, min(1.85, exp))
    kr = max(0.75, min(1.35, gris / max(r, 1.0)))
    kg = max(0.75, min(1.35, gris / max(g, 1.0)))
    kb = max(0.75, min(1.35, gris / max(b, 1.0)))
    # colorchannelmixer acota sus coeficientes a [-2, 2]: un plano muy oscuro
    # pedia ganancia 3.5 y el filtro lo rechazaba de plano.
    lim = lambda v: max(0.05, min(1.99, v))
    return (f"colorchannelmixer="
            f"rr={lim(kr * exp):.4f}:gg={lim(kg * exp):.4f}:bb={lim(kb * exp):.4f}")


def look_chain(sat_tras: float, vineta: bool) -> str:
    c = "curves=" + ":".join(f"{k}='{v}'" for k, v in LOOK.items())
    k = max(0.3, min(1.8, SAT_OBJETIVO / max(sat_tras, 1.0)))
    f = [c, f"eq=saturation={k:.3f}:contrast=1.04"]
    if vineta:
        f.append("vignette=angle=PI/4.6")
    f += ["noise=alls=4:allf=t", "format=yuv420p"]
    return ",".join(f)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst", nargs="?")
    ap.add_argument("--lienzo", default="1920x1080")
    ap.add_argument("--dur", type=float, default=2.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--region", help="caja x0,y0,x1,y1 normalizada donde medir")
    ap.add_argument("--sin-vineta", action="store_true")
    ap.add_argument("--solo-medir", action="store_true")
    a = ap.parse_args()

    caja = tuple(float(x) for x in a.region.split(",")) if a.region else None
    st = medir(a.src, region=caja)
    if a.solo_medir:
        r, g, b = st["medio_rgb"]
        print(f"{pathlib.Path(a.src).name}: medio R{r:.0f} G{g:.0f} B{b:.0f}  "
              f"luma {st['luma']:.0f}  sat {st['sat']:.0f}")
        return
    if not a.dst:
        raise SystemExit("falta la salida (o usa --solo-medir)")

    W, H = (int(v) for v in a.lienzo.lower().split("x"))
    es_img = pathlib.Path(a.src).suffix.lower() in IMAGENES

    def corre(vf, dst, entrada=None, img=False):
        cmd = ["ffmpeg", "-y"]
        if img:
            cmd += ["-loop", "1", "-t", f"{a.dur:.3f}"]
        cmd += ["-i", entrada or a.src, "-vf", vf, "-an",
                "-c:v", "libx264", "-crf", "16", "-preset", "medium", dst]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            sys.stderr.write(p.stderr[-2500:])
            raise SystemExit(f"ffmpeg fallo ({p.returncode})")

    tmp = str(pathlib.Path(a.dst).with_suffix(".bal.mp4"))
    corre(f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"setsar=1,fps={a.fps},{equilibrio(st)},format=yuv420p", tmp, img=es_img)
    sat_tras = medir(tmp, region=caja)["sat"]
    corre(look_chain(sat_tras, not a.sin_vineta), a.dst, entrada=tmp)
    pathlib.Path(tmp).unlink(missing_ok=True)

    fin = medir(a.dst, region=caja)
    print(f"{pathlib.Path(a.src).name:<24} luma {st['luma']:5.0f}->{fin['luma']:5.0f}"
          f"   sat {st['sat']:5.0f}->{fin['sat']:5.0f}")


if __name__ == "__main__":
    main()
