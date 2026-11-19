#!/usr/bin/env python3
"""
assemble - monta el master a partir del plan de planos.

Orden del ensamblaje, que importa:
  1. normalizar cada clip al lienzo
  2. movimiento de plano (casi siempre ninguno)
  3. transiciones entre planos
  4. subtitulos quemados encima
  5. capas de ajuste sobre TODO - el flash en negativo va aqui, sobre el texto

El paso 5 no es un detalle: en la referencia el texto tambien se invierte.

Formato de plan/planos.json:
[
  {"n":0, "tipo":"broll", "src":"media/broll/mac.mp4",
   "dur":2.17, "ss":0.0,
   "movimiento":"ninguno"|"punch"|"propio", "punch_pct":7,
   "fx":["crt"],
   "transicion_salida":{"tipo":"zoomblur"|"whip"|"seco","zoom_pct":7}},
  {"n":1, "tipo":"tarjeta", "texto":"hoy en dia", "dur":0.67}
]

Uso:
    python3 tools/assemble.py --plan plan/planos.json --salida out/master.mp4
    python3 tools/assemble.py --plan plan/planos.json --salida out/master.mp4 \
        --captions plan/captions.json --flashes 5.74,32.1
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import reelfx  # noqa: E402

W, H, FPS = reelfx.W, reelfx.H, reelfx.FPS


IMAGENES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _norm(src: str, dst: str, dur: float, ss: float = 0.0) -> None:
    """Recorta y normaliza un clip al lienzo. Admite imagen fija o video."""
    cmd = ["ffmpeg", "-y"]
    es_imagen = pathlib.Path(src).suffix.lower() in IMAGENES
    if es_imagen:
        # Sin -loop 1 una imagen da UN solo frame y -t no la alarga: el plano
        # sale de 1 frame y el montaje se descuadra sin avisar.
        cmd += ["-loop", "1"]
    elif ss:
        cmd += ["-ss", str(ss)]
    cmd += ["-i", src, "-t", f"{dur:.4f}",
            "-vf", f"{reelfx._fit()},fps={FPS}",
            "-an", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
            "-pix_fmt", "yuv420p", dst]
    reelfx.run(cmd)


def repeticiones_broll(plan: list) -> dict:
    """Cuenta cuantas veces sale cada clip de b-roll.

    Un clip repetido se nota mas que un clip mediocre: el ojo lo reconoce y
    la pieza se lee como si no hubiera material. No se aborta el montaje
    porque hay piezas donde una vuelta a la misma imagen es deliberada, pero
    se informa con el dato para que la decision sea consciente.
    """
    from collections import Counter
    return Counter(pathlib.Path(s["src"]).stem for s in plan
                   if s.get("tipo") == "broll" and s.get("src"))


def construir(plan: list, tmp: pathlib.Path, verbose: bool = True) -> list[str]:
    """Devuelve la lista de clips normalizados, con movimiento y fx aplicados."""
    cuenta = repeticiones_broll(plan)
    repes = {k: v for k, v in cuenta.items() if v > 1}
    if verbose and cuenta:
        print(f"  b-roll: {sum(cuenta.values())} huecos, {len(cuenta)} clips "
              f"distintos", file=sys.stderr)
        if repes:
            print(f"  AVISO: se repiten {', '.join(f'{k} x{v}' for k, v in sorted(repes.items()))}"
                  f" -- {sum(repes.values()) - len(repes)} planos de mas sobre "
                  f"imagen ya vista", file=sys.stderr)
    piezas = []
    for i, s in enumerate(plan):
        base = tmp / f"s{i:03d}.mp4"
        tipo = s.get("tipo", "aroll")

        if tipo == "tarjeta":
            reelfx.ef_white_card(s.get("texto", ""), str(base),
                                 s.get("dur", 0.67))
        elif tipo == "motion":
            reelfx.ef_motion_card(s.get("texto", ""), str(base),
                                  s.get("dur", 2.0), sub=s.get("sub", ""),
                                  fondo=s.get("fondo", "#0A0A0A"),
                                  color=s.get("color"),
                                  barra=s.get("barra", True))
        elif tipo == "parallax":
            # Motion graphic de verdad: foto fija con el sujeto recortado
            # sobre su propio fondo difuminado, los dos moviendose a
            # velocidades distintas. No es una tarjeta con texto.
            for campo in ("fondo", "sujeto"):
                if not s.get(campo):
                    raise SystemExit(f"plano {i}: parallax sin '{campo}'")
                if not pathlib.Path(s[campo]).exists():
                    raise SystemExit(f"plano {i}: no existe {s[campo]}")
            reelfx.ef_parallax(s["fondo"], s["sujeto"], str(base),
                               s.get("dur", 1.2),
                               zoom_fondo_pct=s.get("zoom_fondo_pct", 4.5),
                               zoom_sujeto_pct=s.get("zoom_sujeto_pct", 14.0),
                               blur_min=s.get("blur_min", 2.0),
                               blur_max=s.get("blur_max", 8.0))
        elif tipo == "endcard":
            reelfx.ef_endcard(str(base), s.get("dur"))
        else:
            if not s.get("src"):
                raise SystemExit(f"plano {i}: falta 'src'")
            if not pathlib.Path(s["src"]).exists():
                raise SystemExit(f"plano {i}: no existe {s['src']}")
            # Un ss mas alla del final da un recorte VACIO, y el fallo salta
            # mucho despues en probe() sin decir que plano lo causo.
            if pathlib.Path(s["src"]).suffix.lower() not in IMAGENES:
                dsrc = reelfx.probe(s["src"])["dur"]
                need = s.get("ss", 0.0) + s.get("dur", 2.0)
                if need > dsrc + 0.05:
                    raise SystemExit(
                        f"plano {i}: {pathlib.Path(s['src']).name} dura "
                        f"{dsrc:.2f}s y el plano pide ss={s.get('ss',0)}+"
                        f"{s.get('dur',0)}s = {need:.2f}s")
            _norm(s["src"], str(base), s.get("dur", 2.0), s.get("ss", 0.0))

        actual = base
        # --- movimiento de plano -------------------------------------------
        mov = s.get("movimiento", "ninguno")
        trans = (s.get("transicion_salida") or {}).get("tipo", "seco")
        if mov == "suspendido":
            nxt = tmp / f"s{i:03d}_susp.mp4"
            reelfx.ef_suspendido(str(actual), str(nxt),
                                 deriva_pct=s.get("deriva_pct", 9.0),
                                 entrada=s.get("entrada", 0.42),
                                 blur_max=s.get("blur_max", 9.0),
                                 angulo=s.get("angulo", 180.0))
            actual = nxt
        elif mov == "punch":
            if trans == "zoomblur":
                print(f"  plano {i}: punch IGNORADO, ya lleva zoomblur a la "
                      f"salida (el movimiento estaria duplicado)", file=sys.stderr)
            else:
                nxt = tmp / f"s{i:03d}_punch.mp4"
                reelfx.ef_punch(str(actual), str(nxt), s.get("punch_pct", 7.0),
                                s.get("reposo", 0.85))
                actual = nxt
        # --- fx de plano ----------------------------------------------------
        for fx in s.get("fx", []):
            if fx == "crt":
                nxt = tmp / f"s{i:03d}_crt.mp4"
                reelfx.ef_crt(str(actual), str(nxt))
                actual = nxt
        piezas.append(str(actual))
        if verbose:
            print(f"  plano {i:>2} {tipo:<8} {s.get('dur', 0):>5.2f}s "
                  f"mov={mov:<8} trans={trans}", file=sys.stderr)
    return piezas


def unir(piezas: list[str], plan: list, tmp: pathlib.Path, dst: str) -> None:
    """Concatena resolviendo las transiciones declaradas entre planos."""
    actual = piezas[0]
    for i in range(1, len(piezas)):
        t = (plan[i - 1].get("transicion_salida") or {})
        tipo = t.get("tipo", "seco")
        salida = tmp / f"u{i:03d}.mp4"
        if tipo == "zoomblur":
            reelfx.ef_zoomblur_cut(actual, piezas[i], str(salida),
                                   t.get("f_out", 5), t.get("f_in", 5),
                                   t.get("zoom_pct", 7.0))
        elif tipo == "whip":
            reelfx.ef_whip(actual, piezas[i], str(salida),
                           t.get("frames", 2), t.get("angulo", 115),
                           t.get("fuerza", 110))
        else:
            lista = tmp / f"c{i:03d}.txt"
            lista.write_text(f"file '{actual}'\nfile '{piezas[i]}'\n",
                             encoding="utf-8")
            reelfx.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                        "-i", str(lista), "-c", "copy", str(salida)])
        actual = str(salida)
    shutil.copy(actual, dst)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--captions", help="plan/captions.json para quemar encima")
    ap.add_argument("--flashes", help="segundos separados por coma para el "
                                      "flash en negativo (va sobre el texto)")
    ap.add_argument("--conservar-temp", action="store_true")
    a = ap.parse_args()

    plan = json.loads(pathlib.Path(a.plan).read_text(encoding="utf-8"))
    pathlib.Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="assemble_"))
    try:
        print("1/4 normalizando planos y aplicando movimiento", file=sys.stderr)
        piezas = construir(plan, tmp)

        print("2/4 resolviendo transiciones", file=sys.stderr)
        montaje = tmp / "montaje.mp4"
        unir(piezas, plan, tmp, str(montaje))
        actual = montaje

        if a.captions:
            print("3/4 quemando subtitulos", file=sys.stderr)
            nxt = tmp / "con_captions.mp4"
            reelfx.ef_captions(str(actual), str(nxt), a.captions)
            actual = nxt
        else:
            print("3/4 sin subtitulos", file=sys.stderr)

        if a.flashes:
            print("4/4 flashes en negativo (sobre el texto)", file=sys.stderr)
            for k, seg in enumerate(a.flashes.split(",")):
                nxt = tmp / f"flash{k}.mp4"
                reelfx.ef_invert_flash(str(actual), str(nxt), float(seg))
                actual = nxt
        else:
            print("4/4 sin flashes", file=sys.stderr)

        shutil.copy(str(actual), a.salida)
        info = reelfx.probe(a.salida)
        print(f"\nlisto: {a.salida}  {info['w']}x{info['h']} "
              f"{info['dur']:.2f}s @ {info['fps']:.2f}fps", file=sys.stderr)
        print("pasa ahora: python3 tools/render_qc.py " + a.salida, file=sys.stderr)
    finally:
        if a.conservar_temp:
            print(f"temporales en {tmp}", file=sys.stderr)
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
