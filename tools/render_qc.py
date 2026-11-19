#!/usr/bin/env python3
"""
render_qc - audita un master contra el preset del estilo.

Mide el resultado y lo compara con presets/estilo-2027.json. Informa con datos,
no con impresiones. Detecta en particular el fallo mas comun: el Ken Burns, es
decir una rampa de zoom repartida en vez de descargada al final.

Uso:
    python3 tools/render_qc.py out/master.mp4
    python3 tools/render_qc.py out/master.mp4 --json informe.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

import cv2
import numpy as np

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PRESET = json.loads((RAIZ / "presets" / "estilo-2027.json").read_text(encoding="utf-8"))

OK, AVISO, FALLO = "ok", "aviso", "fallo"


def cortes(path: str, umbral: float = 0.45) -> list[float]:
    """Instantes de corte, por diferencia de escena de ffmpeg.

    El umbral importa mas de lo que parece y estaba mal calibrado. Medido sobre
    dos montajes de la MISMA estructura (13 cortes reales), uno con b-roll de
    imagenes fijas y otro con metraje real:

        umbral   fijas   metraje
        0.25        14        42   <- el valor que habia: triplica con metraje
        0.35        13        29
        0.45        12        14   <- los dos a un corte de la verdad
        0.50        12        12
        0.60        12         9

    Con imagenes fijas cualquier umbral bajo vale, porque entre plano y plano
    cambia todo de golpe y dentro del plano no se mueve nada. Con metraje real
    el movimiento interno del clip dispara el detector y la cuenta se va. 0.45
    es el unico valor que aguanta los dos casos.
    """
    out = subprocess.run(
        ["ffmpeg", "-i", path, "-vf", f"select='gt(scene,{umbral})',showinfo",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    ts = []
    for line in out.splitlines():
        if "pts_time:" in line:
            try:
                ts.append(float(line.split("pts_time:")[1].split()[0]))
            except (ValueError, IndexError):
                pass
    return sorted(ts)


def stats_frames(path: str):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    filas = []
    prev = None
    n = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f, (160, 120)), cv2.COLOR_BGR2GRAY)
        corr = 0.0
        if prev is not None:
            a = (prev.astype(np.float32).ravel())
            b = (g.astype(np.float32).ravel())
            a = (a - a.mean()) / (a.std() + 1e-6)
            b = (b - b.mean()) / (b.std() + 1e-6)
            corr = float((a * b).mean())
        filas.append({"n": n, "t": n / fps, "lum": float(g.mean()), "corr": corr})
        prev = g
        n += 1
    cap.release()
    return fps, filas


def rejilla_subtitulos(path: str):
    cap = cv2.VideoCapture(path)
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    Wd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    ys, xs = [], []
    n = 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        n += 1
        if n % 5:
            continue
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        _, th = cv2.threshold(g, 235, 255, cv2.THRESH_BINARY)
        th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, np.ones((3, 15), np.uint8))
        cs, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cs:
            x, y, w, h = cv2.boundingRect(c)
            if 25 < w < Wd * 0.94 and 9 < h < H * 0.2 and w > h * 0.7 \
                    and cv2.contourArea(c) > 120:
                ys.append((y + h / 2) / H)
                xs.append((x + w / 2) / Wd)
    cap.release()
    return ys, xs


def audio_stats(path: str):
    out = subprocess.run(
        ["ffmpeg", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    integ = None
    for line in out.splitlines():
        if "I:" in line and "LUFS" in line:
            try:
                integ = float(line.split("I:")[1].split("LUFS")[0].strip())
            except (ValueError, IndexError):
                pass
    tiene = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    return integ, bool(tiene)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--umbral", type=float, default=0.45,
                    help="sensibilidad del detector de cortes (ver cortes())")
    ap.add_argument("--json", help="vuelca el informe")
    a = ap.parse_args()

    if not pathlib.Path(a.video).exists():
        raise SystemExit(f"no existe {a.video}")

    hallazgos = []

    def add(estado, titulo, detalle):
        hallazgos.append({"estado": estado, "titulo": titulo, "detalle": detalle})

    print(f"auditando {a.video}\n", file=sys.stderr)
    fps, filas = stats_frames(a.video)
    dur = len(filas) / fps
    cs = cortes(a.video, a.umbral)

    # --- ritmo --------------------------------------------------------------
    bordes = [0.0] + cs + [dur]
    planos = [bordes[i + 1] - bordes[i] for i in range(len(bordes) - 1)]
    planos = [p for p in planos if p > 0.04]
    r = PRESET["ritmo"]
    if planos:
        med = float(np.median(planos))
        add(OK if 0.7 <= med <= 2.2 else AVISO,
            "ritmo",
            f"{len(cs)} cortes, plano mediano {med:.2f}s "
            f"(referencia {r['duracion_mediana_plano_s']}s), "
            f"mas corto {min(planos):.2f}s, mas largo {max(planos):.2f}s")

    # --- duracion -----------------------------------------------------------
    lo, hi = PRESET["lienzo"]["duracion_objetivo_s"]
    add(OK if lo <= dur <= hi else AVISO, "duracion",
        f"{dur:.1f}s (objetivo {lo}-{hi}s)")

    # --- tarjetas blancas ---------------------------------------------------
    blancos, cur = [], []
    for x in filas:
        if x["lum"] > 200:
            cur.append(x)
        else:
            if cur:
                blancos.append(cur)
                cur = []
    if cur:
        blancos.append(cur)
    blancos = [b for b in blancos if len(b) >= 2]
    pres = PRESET["transiciones"]["tarjeta_blanca"]["duraciones_referencia_s"]
    add(OK if 1 <= len(blancos) <= 4 else AVISO, "tarjetas blancas",
        f"{len(blancos)} encontradas, duraciones "
        f"{[round(len(b) / fps, 2) for b in blancos]} "
        f"(referencia {pres}, presupuesto 2-3)")

    # --- flashes en negativo ------------------------------------------------
    # Cada inversion deberia dar dos fronteras anticorreladas (entrada y
    # salida), pero si la salida coincide con un corte solo aparece una. Por
    # eso no vale dividir entre dos: se agrupan las fronteras cercanas y se
    # cuenta un flash por grupo.
    bordes = [x["n"] for x in filas if x["corr"] < -0.35]
    grupos = []
    for b in bordes:
        if grupos and b - grupos[-1][-1] <= 12:
            grupos[-1].append(b)
        else:
            grupos.append([b])
    n_inv = len(grupos)
    add(OK if n_inv <= 2 else FALLO, "flash en negativo",
        f"{n_inv} detectados (presupuesto 1-2; una tercera aparicion lo "
        f"convierte en tic)")

    # --- rejilla de subtitulos ---------------------------------------------
    ys, xs = rejilla_subtitulos(a.video)
    g = PRESET["rejilla_subtitulos"]
    if len(ys) >= 20:
        my = float(np.median(ys))
        p10, p90 = float(np.percentile(xs, 10)), float(np.percentile(xs, 90))
        disp = p90 - p10
        add(OK if abs(my - g["linea_base_y"]) < 0.08 else FALLO,
            "linea de subtitulos",
            f"mediana y={my:.3f} (objetivo {g['linea_base_y']}). "
            + ("" if abs(my - g["linea_base_y"]) < 0.08 else
               "Fuera de la banda central: parece lower-third o karaoke."))
        obj = g["x_dispersion"]["p90"] - g["x_dispersion"]["p10"]
        add(OK if disp > 0.30 else FALLO,
            "dispersion horizontal",
            f"p10={p10:.2f} p90={p90:.2f} (amplitud {disp:.2f}, objetivo "
            f"~{obj:.2f}). "
            + ("" if disp > 0.30 else
               "Las palabras estan centradas: en este estilo se esparcen."))
    else:
        add(AVISO, "subtitulos", f"solo {len(ys)} blobs detectados; "
                                 f"puede que el video no lleve texto quemado")

    # --- audio --------------------------------------------------------------
    integ, tiene_audio = audio_stats(a.video)
    if not tiene_audio:
        add(AVISO, "audio", "el master no tiene pista de audio")
    elif integ is None:
        add(AVISO, "audio", "no se pudo medir el nivel integrado")
    else:
        add(OK if -26 <= integ <= -18 else AVISO, "nivel",
            f"{integ:.1f} LUFS integrados (objetivo ~-22)")

    # --- cierre en silencio -------------------------------------------------
    if filas:
        ult = [x for x in filas if x["t"] > dur - 1.0]
        if ult and float(np.mean([x["lum"] for x in ult])) < 40:
            add(OK, "cierre", "el final es oscuro, consistente con la tarjeta "
                              "de marca")

    # --- salida -------------------------------------------------------------
    icono = {OK: "  ok  ", AVISO: " aviso", FALLO: " FALLO"}
    for h in hallazgos:
        print(f"[{icono[h['estado']]}] {h['titulo']}: {h['detalle']}")

    fallos = sum(1 for h in hallazgos if h["estado"] == FALLO)
    avisos = sum(1 for h in hallazgos if h["estado"] == AVISO)
    print(f"\n{fallos} fallos, {avisos} avisos, "
          f"{len(hallazgos) - fallos - avisos} correctos")
    print("\nEl zoom por plano no se audita aqui: pasa cada plano por "
          "tools/motion_probe.py --curva, que distingue punch de Ken Burns.")

    if a.json:
        pathlib.Path(a.json).write_text(
            json.dumps({"video": a.video, "dur": dur, "cortes": len(cs),
                        "hallazgos": hallazgos}, indent=1, ensure_ascii=False),
            encoding="utf-8")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
