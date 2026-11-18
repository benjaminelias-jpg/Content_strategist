#!/usr/bin/env python3
"""
audiomix - mezcla el audio del reel y lo audita.

Cama musical continua por debajo de la voz, con ducking de liberacion larga
para que no bombee entre palabras, y master a -22 LUFS.

Uso:
    python3 tools/audiomix.py --voz voz.wav --musica cama.wav \
        --video montaje.mp4 --salida final.mp4
    python3 tools/audiomix.py --qc final.mp4
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PRESET = json.loads((RAIZ / "presets" / "estilo-2027.json").read_text(encoding="utf-8"))
A = PRESET["audio"]


def run(cmd, capturar=False):
    print("$ " + " ".join(cmd[:6]) + " ...", file=sys.stderr)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 and not capturar:
        sys.stderr.write(p.stderr[-3000:])
        raise SystemExit(f"ffmpeg fallo ({p.returncode})")
    return p.stderr


def mezclar(voz: str, musica: str, video: str, salida: str,
            silencios: list[tuple[float, float]] | None = None) -> None:
    duck = A["ducking"]
    nivel_mus = A["cama_musical"]["nivel_relativo_voz_db"]

    # la musica se silencia bajo las tarjetas blancas y en el cierre
    mute = ""
    if silencios:
        cond = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in silencios)
        mute = f",volume=0:enable='{cond}'"

    # La voz se usa dos veces: como cadena lateral del ducking y en la mezcla.
    # Una etiqueta de filtro solo se puede consumir una vez, asi que hay que
    # duplicarla con asplit o ffmpeg la toma por un especificador de stream.
    fc = (
        f"[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
        f"dynaudnorm=g=5:p=0.9,asplit=2[vozmix][vozsc];"
        f"[2:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo,"
        f"volume={nivel_mus}dB{mute}[mus];"
        f"[mus][vozsc]sidechaincompress="
        f"threshold=0.03:ratio={max(2, int(duck['reduccion_db'] / 2))}:"
        f"attack={duck['ataque_ms']}:release={duck['liberacion_ms']}[musduck];"
        f"[vozmix][musduck]amix=inputs=2:duration=first:dropout_transition=0,"
        f"loudnorm=I=-22:TP=-1.5:LRA=11[a]"
    )
    run(["ffmpeg", "-y", "-i", video, "-i", voz, "-i", musica,
         "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", salida])


def qc(path: str) -> int:
    err = run(["ffmpeg", "-i", path, "-af", "ebur128=peak=true",
               "-f", "null", "-"], capturar=True)
    integ = tp = None
    for line in err.splitlines():
        s = line.strip()
        if s.startswith("I:") and "LUFS" in s:
            integ = float(s.split("I:")[1].split("LUFS")[0])
        if s.startswith("Peak:") and "dBFS" in s:
            tp = float(s.split("Peak:")[1].split("dBFS")[0])

    tiene = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=codec_type", "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()
    if not tiene:
        print("[ FALLO] el fichero no tiene pista de audio")
        return 1

    fallos = 0
    if integ is None:
        print("[ aviso] no se pudo medir el nivel integrado")
    else:
        ok = -26 <= integ <= -18
        print(f"[{'  ok  ' if ok else ' aviso'}] integrado {integ:.1f} LUFS "
              f"(objetivo ~-22)")
    if tp is not None:
        ok = tp <= -0.5
        print(f"[{'  ok  ' if ok else ' aviso'}] pico real {tp:.1f} dBFS "
              f"(objetivo <= -1.5)")

    # silencio final
    err2 = run(["ffmpeg", "-i", path, "-af",
                "silencedetect=noise=-50dB:d=0.3", "-f", "null", "-"],
               capturar=True)
    sil = [l for l in err2.splitlines() if "silence_start" in l]
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout or 0)
    final_sil = False
    for l in sil:
        try:
            t = float(l.split("silence_start:")[1].strip())
            if dur - t < 2.0:
                final_sil = True
        except (ValueError, IndexError):
            pass
    print(f"[{'  ok  ' if final_sil else ' aviso'}] cierre "
          f"{'en silencio' if final_sil else 'con sonido: la referencia lo deja mudo'}")
    return fallos


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qc", help="audita el audio de un master ya montado")
    ap.add_argument("--voz")
    ap.add_argument("--musica")
    ap.add_argument("--video")
    ap.add_argument("--salida")
    ap.add_argument("--silencios", help="tramos a silenciar la musica, "
                                        "p.ej. 17.5-18.0,25.3-26.0")
    a = ap.parse_args()

    if a.qc:
        sys.exit(qc(a.qc))

    if not all([a.voz, a.musica, a.video, a.salida]):
        raise SystemExit("hacen falta --voz, --musica, --video y --salida "
                         "(o bien --qc)")
    sil = None
    if a.silencios:
        sil = [tuple(float(x) for x in t.split("-"))
               for t in a.silencios.split(",")]
    mezclar(a.voz, a.musica, a.video, a.salida, sil)
    print(f"\nlisto: {a.salida}", file=sys.stderr)
    qc(a.salida)


if __name__ == "__main__":
    main()
