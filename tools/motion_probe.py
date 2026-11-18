#!/usr/bin/env python3
"""
motion_probe - mide el movimiento real de un clip.

Estima la transformada de similitud entre frames consecutivos (ORB + RANSAC) y
acumula la escala para reconstruir la curva de zoom. Sirve para dos cosas:

  1. saber si un b-roll ya trae movimiento propio (y no anadirle zoom encima)
  2. comprobar que un punch renderizado tiene la forma correcta, es decir
     plano durante el 85% y disparado al final, y NO una rampa recta

Uso:
    python3 tools/motion_probe.py clip.mp4
    python3 tools/motion_probe.py clip.mp4 --curva
"""
from __future__ import annotations

import argparse
import sys

import cv2
import numpy as np


def medir(path: str, max_frames: int = 900):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise SystemExit(f"no se pudo abrir {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    orb = cv2.ORB_create(nfeatures=1200)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    prev = None
    cum = 1.0
    curva = []
    n = 0
    malos = 0
    while n < max_frames:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        if prev is not None:
            s = _escala(orb, bf, prev, g)
            if s is None:
                malos += 1
            else:
                cum *= s
            curva.append((n / fps, cum))
        prev = g
        n += 1
    cap.release()
    if not curva:
        raise SystemExit("clip demasiado corto para medir")
    return {"fps": fps, "frames": n, "dur": n / fps, "curva": curva,
            "malos": malos, "zoom_final": cum}


def _escala(orb, bf, a, b):
    ka, da = orb.detectAndCompute(a, None)
    kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None or len(ka) < 12 or len(kb) < 12:
        return None
    m = bf.match(da, db)
    if len(m) < 12:
        return None
    m = sorted(m, key=lambda x: x.distance)[:400]
    pa = np.float32([ka[x.queryIdx].pt for x in m])
    pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC,
                                         ransacReprojThreshold=2.5,
                                         maxIters=3000, confidence=0.995)
    if M is None or inl is None or inl.sum() < 10:
        return None
    s = float(np.sqrt(M[0, 0] ** 2 + M[1, 0] ** 2))
    return s if 0.9 < s < 1.12 else None


def diagnostico(r) -> str:
    """Distingue un punch correcto de un Ken Burns."""
    c = r["curva"]
    tot = r["zoom_final"] - 1.0
    if abs(tot) < 0.015:
        return "ESTATICO - sin movimiento apreciable. Correcto para A-roll."
    # cuanto del recorrido se ha consumido al 70% del clip
    i70 = int(len(c) * 0.70)
    p70 = (c[i70][1] - 1.0) / tot if abs(tot) > 1e-6 else 0.0
    # el sujeto en movimiento mete ruido y puede dar avances negativos:
    # para el diagnostico solo importa cuanto se ha consumido, no el signo
    p70 = max(0.0, min(1.0, p70))
    if tot < -0.015:
        return (f"MOVIMIENTO PROPIO ({tot * 100:+.1f}%) - el clip ya se mueve. "
                f"No le anadas zoom encima: eligelo por su movimiento.")
    if p70 > 0.55:
        return (f"KEN BURNS ({tot * 100:+.1f}%, {p70 * 100:.0f}% consumido al 70%) - "
                f"rampa repartida. NO es el estilo. El recorrido debe descargarse "
                f"en el ultimo 15%.")
    return (f"PUNCH CORRECTO ({tot * 100:+.1f}%, solo {p70 * 100:.0f}% consumido "
            f"al 70%) - quieto y disparado al final.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clip")
    ap.add_argument("--curva", action="store_true", help="imprime la curva completa")
    a = ap.parse_args()

    r = medir(a.clip)
    print(f"{a.clip}")
    print(f"  {r['frames']} frames @ {r['fps']:.2f}fps = {r['dur']:.2f}s")
    print(f"  zoom acumulado: {(r['zoom_final'] - 1) * 100:+.2f}%")
    if r["malos"]:
        print(f"  pares sin solucion: {r['malos']} "
              f"({r['malos'] / max(1, r['frames']) * 100:.0f}%) - "
              f"medida menos fiable en material oscuro o muy borroso")
    print(f"  -> {diagnostico(r)}")

    if a.curva:
        c = r["curva"]
        tot = r["zoom_final"] - 1.0
        print("\n  t/T    zoom%   avance")
        paso = max(1, len(c) // 14)
        for i in range(0, len(c), paso):
            t, z = c[i]
            p = (z - 1) / tot if abs(tot) > 1e-6 else 0.0
            print(f"  {t / r['dur']:.2f}  {(z - 1) * 100:+6.2f}%  "
                  f"{'#' * max(0, int(p * 34))}")


if __name__ == "__main__":
    main()
