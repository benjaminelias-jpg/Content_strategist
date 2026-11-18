#!/usr/bin/env python3
"""
wordmap - saca el mapa de palabras con tiempos a partir de la voz grabada.

Es el cuello de botella de la pieza: sin esto no hay subtitulos ni cortes,
porque en este estilo los cortes caen en frontera de palabra.

Transcribe con Whisper si esta instalado. Si no lo esta, convierte un SRT o
un VTT que ya tengas. No inventa tiempos.

Uso:
    python3 tools/wordmap.py voz.wav --salida plan/palabras.json
    python3 tools/wordmap.py --srt subs.srt --salida plan/palabras.json
    python3 tools/wordmap.py voz.wav --salida plan/palabras.json --modelo small
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

AYUDA_INSTALACION = """
No hay motor de transcripcion disponible en este entorno.

Opcion A - instalar uno (descarga pesos, puede tardar):
    pip install faster-whisper
    python3 tools/wordmap.py voz.wav --salida plan/palabras.json

Opcion B - traer los tiempos de fuera:
    Exporta subtitulos desde tu editor (Premiere: Texto > Transcribir;
    CapCut y Descript tambien exportan SRT) y conviertelos:
    python3 tools/wordmap.py --srt subs.srt --salida plan/palabras.json

Un SRT da tiempos por linea, no por palabra: se reparten proporcionalmente a
la longitud de cada palabra. Sirve para empezar, pero repasa los tiempos de
las palabras que llevan enfasis, porque son las que se ven.
"""


def por_whisper(audio: str, modelo: str, idioma: str | None):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        try:
            import whisper  # noqa: F401
        except ImportError:
            print(AYUDA_INSTALACION, file=sys.stderr)
            raise SystemExit(2)
        return _openai_whisper(audio, modelo, idioma)

    m = WhisperModel(modelo, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(audio, language=idioma, word_timestamps=True)
    palabras = []
    for s in segs:
        for w in (s.words or []):
            t = w.word.strip()
            if t:
                palabras.append({"palabra": t, "t_in": round(w.start, 3),
                                 "t_out": round(w.end, 3)})
    return palabras


def _openai_whisper(audio: str, modelo: str, idioma: str | None):
    import whisper
    m = whisper.load_model(modelo)
    r = m.transcribe(audio, language=idioma, word_timestamps=True)
    palabras = []
    for s in r.get("segments", []):
        for w in s.get("words", []):
            t = (w.get("word") or "").strip()
            if t:
                palabras.append({"palabra": t, "t_in": round(w["start"], 3),
                                 "t_out": round(w["end"], 3)})
    return palabras


def por_srt(path: str):
    """Reparte el tiempo de cada linea entre sus palabras, proporcional a la
    longitud. Es una aproximacion: los tiempos de linea si son exactos."""
    txt = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    bloques = re.split(r"\n\s*\n", txt.strip())
    palabras = []
    for b in bloques:
        m = re.search(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
                      r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", b)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        t0 = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        t1 = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        linea = " ".join(l for l in b.splitlines()
                         if "-->" not in l and not l.strip().isdigit())
        ws = [w for w in re.split(r"\s+", linea.strip()) if w]
        if not ws:
            continue
        total = sum(len(w) for w in ws)
        cur = t0
        for w in ws:
            d = (t1 - t0) * (len(w) / total)
            palabras.append({"palabra": w, "t_in": round(cur, 3),
                             "t_out": round(cur + d, 3)})
            cur += d
    return palabras


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", nargs="?")
    ap.add_argument("--srt", help="convierte un SRT o VTT ya existente")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--modelo", default="base")
    ap.add_argument("--idioma", default="es")
    a = ap.parse_args()

    if a.srt:
        palabras = por_srt(a.srt)
        origen = f"SRT {a.srt} (tiempos por palabra aproximados)"
    elif a.audio:
        palabras = por_whisper(a.audio, a.modelo, a.idioma)
        origen = f"transcripcion de {a.audio}"
    else:
        raise SystemExit("pasa un audio o bien --srt")

    if not palabras:
        raise SystemExit("no se obtuvo ninguna palabra")

    pathlib.Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(a.salida).write_text(
        json.dumps(palabras, indent=1, ensure_ascii=False), encoding="utf-8")

    dur = palabras[-1]["t_out"]
    print(f"{len(palabras)} palabras, {dur:.1f}s -> {a.salida}")
    print(f"origen: {origen}")
    print("\nRepasa los tiempos antes de montar: el reconocimiento se equivoca "
          "en nombres propios y numeros, y aqui un tiempo mal puesto se "
          "arrastra a todo el montaje.")
    print("\nprimeras palabras:")
    for w in palabras[:8]:
        print(f"  {w['t_in']:>6.2f} - {w['t_out']:>6.2f}  {w['palabra']}")


if __name__ == "__main__":
    main()
