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


def pista_clicks(cortes: list[float], dur_total: float, dst: str,
                 mudos: list[tuple[float, float]] | None = None) -> int:
    """Construye una pista con un click seco en cada corte.

    El click no se "oye": se nota. Marca el corte y hace que la transicion
    deje de parecer un salto. Va al nivel de SFX del preset (-28 dBFS), que
    es muy por debajo de la voz.

    Dos detalles que importan:
      - Se ALTERNAN dos variantes. Un unico sample repetido 28 veces suena a
        metronomo; dos ya se leen como textura.
      - Se SALTAN los tramos mudos (tarjetas blancas y cierre). El preset
        pide "silencio total bajo la tarjeta blanca": un click ahi rompe
        justo el efecto de parada que da la tarjeta.

    Se escribe el WAV entero en numpy en vez de encadenar un adelay por
    corte: con 28 cortes la cadena de filtros se vuelve ilegible y no hay
    forma de comprobar donde cayo cada golpe.
    """
    import numpy as np
    import wave

    SR = 48000
    banco = []
    for nombre in ("click_a", "click_b"):
        f = RAIZ / "assets" / "sfx" / f"{nombre}.wav"
        if not f.exists():
            print(f"[ aviso] falta {f.name}: la pieza sale sin clicks",
                  file=sys.stderr)
            return 0
        with wave.open(str(f), "rb") as w:
            assert w.getframerate() == SR, f"{f.name} no esta a {SR} Hz"
            banco.append(np.frombuffer(w.readframes(w.getnframes()),
                                       dtype=np.int16).astype(np.float32) / 32768)

    pista = np.zeros(int(dur_total * SR) + SR, dtype=np.float32)
    puestos = 0
    for k, t in enumerate(sorted(cortes)):
        if t <= 0.05 or t >= dur_total - 0.05:
            continue
        if mudos and any(a <= t < b for a, b in mudos):
            continue
        c = banco[k % len(banco)]
        i = int(t * SR)
        pista[i:i + c.size] += c
        puestos += 1

    nivel = 10 ** (PRESET["audio"]["sfx"]["nivel_dbfs"] / 20)
    pista *= nivel / max(float(np.abs(pista).max()), 1e-9)
    with wave.open(dst, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(pista, -1, 1) * 32767).astype(np.int16).tobytes())
    return puestos


def mezclar(voz: str, musica: str, video: str, salida: str,
            silencios: list[tuple[float, float]] | None = None,
            clicks: str | None = None) -> None:
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
        f"[vozmix][musduck]amix=inputs=2:duration=first:dropout_transition=0[vm];"
    )
    entradas = ["-i", video, "-i", voz, "-i", musica]
    if clicks:
        # Los clicks entran DESPUES del amix de voz y musica y NO pasan por
        # el ducking: son los que marcan el corte, y agacharlos con la voz
        # los borraria justo donde hacen falta.
        entradas += ["-i", clicks]
        fc += (f"[3:a]aformat=sample_fmts=fltp:sample_rates=44100:"
               f"channel_layouts=stereo[clk];"
               f"[vm][clk]amix=inputs=2:duration=first:dropout_transition=0,"
               f"loudnorm=I=-22:TP=-1.5:LRA=11[a]")
    else:
        fc += "[vm]loudnorm=I=-22:TP=-1.5:LRA=11[a]"
    run(["ffmpeg", "-y", *entradas,
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

    # Silencio final. Se mide el ultimo segundo DIRECTAMENTE en vez de mirar
    # cuando arranca el silencio: con un cierre de 2.9s el silencio empieza
    # mucho antes del final y la comprobacion anterior lo daba por sonoro.
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout or 0)
    final_sil = False
    if dur > 1.2:
        err2 = run(["ffmpeg", "-ss", f"{dur - 1.0:.3f}", "-i", path,
                    "-map", "0:a", "-af", "astats=metadata=1:reset=0",
                    "-f", "null", "-"], capturar=True)
        for l in err2.splitlines():
            # ffmpeg antepone "[Parsed_astats_0 @ 0x...] " a cada linea, asi
            # que startswith no vale: hay que buscar la etiqueta dentro.
            if "RMS level dB:" in l:
                try:
                    final_sil = float(l.split("RMS level dB:")[1].strip()) < -50.0
                except ValueError:
                    pass
                break
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
    ap.add_argument("--clicks", help="segundos de los cortes, separados por "
                                     "coma: pone un click seco en cada uno, "
                                     "al nivel de SFX del preset. Se saltan "
                                     "los tramos de --silencios")
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
    pista = None
    if a.clicks:
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", a.video], capture_output=True,
            text=True).stdout or 0)
        pista = str(pathlib.Path(a.salida).with_suffix(".clicks.wav"))
        cortes = [float(x) for x in a.clicks.split(",") if x.strip()]
        n = pista_clicks(cortes, dur, pista, sil)
        print(f"clicks: {n} de {len(cortes)} cortes "
              f"({len(cortes) - n} caen en tramo mudo o en los bordes), "
              f"a {PRESET['audio']['sfx']['nivel_dbfs']} dBFS", file=sys.stderr)
        if n == 0:
            pista = None

    mezclar(a.voz, a.musica, a.video, a.salida, sil, pista)
    print(f"\nlisto: {a.salida}", file=sys.stderr)
    qc(a.salida)


if __name__ == "__main__":
    main()
