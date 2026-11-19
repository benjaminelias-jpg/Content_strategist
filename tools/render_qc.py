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


def cortes(path: str, umbral: float = 0.25) -> list[float]:
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
    ap.add_argument("--json", help="vuelca el informe")
    ap.add_argument("--captions", help="plan de subtitulos: con el, la rejilla "
                                       "se audita EXACTA en vez de estimarla "
                                       "por pixeles, que confunde manchas "
                                       "brillantes de la imagen con texto")
    a = ap.parse_args()

    if not pathlib.Path(a.video).exists():
        raise SystemExit(f"no existe {a.video}")

    hallazgos = []

    def add(estado, titulo, detalle):
        hallazgos.append({"estado": estado, "titulo": titulo, "detalle": detalle})

    print(f"auditando {a.video}\n", file=sys.stderr)
    fps, filas = stats_frames(a.video)
    dur = len(filas) / fps
    cs = cortes(a.video)

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
    if a.captions:
        cp = json.loads(pathlib.Path(a.captions).read_text(encoding="utf-8"))
        ys = [c.get("y", PRESET["rejilla_subtitulos"]["linea_base_y"]) for c in cp]
        xs = [c["x"] for c in cp]
        exacto = True
    else:
        ys, xs = rejilla_subtitulos(a.video)
        exacto = False
    g = PRESET["rejilla_subtitulos"]
    if len(ys) >= 20:
        my = float(np.median(ys))
        p10, p90 = float(np.percentile(xs, 10)), float(np.percentile(xs, 90))
        disp = p90 - p10
        # Lo que se audita es la COHERENCIA de la linea, no su valor absoluto.
        # El 0.505 de la referencia sale de que su cara ocupa el tercio
        # superior; con un primer plano que llena el cuadro, esa linea taparia
        # la cara y hay que bajarla. Lo que delata un mal montaje es que las
        # palabras no compartan linea, no que la linea este mas abajo.
        # Coherencia = pocas alturas distintas y bien pobladas, no una sola.
        # Dos lineas a proposito (una centrada sobre b-roll y otra mas baja
        # sobre el A-roll, para no tapar la cara) es un diseno coherente; lo
        # que no lo es son muchas alturas sueltas. Antes esto se media con el
        # rango intercuartil y penalizaba el diseno de dos lineas.
        from collections import Counter
        niveles = Counter(round(v, 2) for v in ys)
        dominantes = [v for v, c in niveles.items() if c >= max(2, len(ys) * 0.08)]
        cubre = sum(c for v, c in niveles.items() if v in dominantes) / max(1, len(ys))
        coherente = len(dominantes) <= 3 and cubre >= 0.85
        add(OK if coherente else FALLO,
            "coherencia de la linea",
            f"mediana y={my:.3f}, {len(dominantes)} altura(s) dominante(s) "
            f"{sorted(dominantes)} que cubren el {cubre*100:.0f}% de las palabras. "
            + ("las palabras se reparten entre pocas lineas previsibles"
               if coherente else
               "demasiadas alturas sueltas: se leen como colocadas al azar")
            + f" (la referencia usa {g['linea_base_y']}, valida cuando el sujeto "
              f"va en el tercio superior)"
            + ("" if exacto else "  [estimado por pixeles: poco fiable, "
                                 "pasa --captions para medirlo exacto]"))
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
