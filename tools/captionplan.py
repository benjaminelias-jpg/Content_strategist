#!/usr/bin/env python3
"""
captionplan - convierte el mapa de palabras en el plan de subtitulos.

Era el unico paso del montaje que seguia siendo manual: `wordmap.py` daba
`palabras.json` y `reelfx.py captions` pedia `captions.json`, pero nada hacia
el salto. Aqui se aplica la rejilla medida en
presets/estilo-2027.json -> rejilla_subtitulos, de modo que el plan la cumple
POR CONSTRUCCION y luego `render_qc.py` lo comprueba sobre el pixel.

Lo que hace, y por que:

  x    Las palabras NO van centradas. Se reparten sobre una unica linea
       horizontal siguiendo la distribucion medida (p10 0.20, mediana 0.50,
       p90 0.78). Se usa una secuencia de van der Corput, no numeros al azar:
       cubre el rango de forma pareja, es determinista (el mismo mapa da el
       mismo plan) y evita que dos palabras seguidas caigan juntas.

  t_out  Cada palabra se queda en pantalla hasta que se limpia la frase, no
       hasta que deja de pronunciarse. La frase se borra DE GOLPE.

  grupo  Como mucho `--max-simultaneas` palabras a la vez (4 en la referencia).
       Se corta antes si hay un silencio largo o si toca un corte de plano.

Las escalas y el color NO se deciden solos: enfasis, heroe, acento e italica
son decisiones de guion y se pasan por argumento.

Uso:
    python3 tools/captionplan.py plan/palabras.json --salida plan/captions.json
    python3 tools/captionplan.py plan/palabras.json --salida plan/captions.json \
        --cortes plan/planos.json \
        --enfasis criterio,elegir --heroe oro \
        --acento "todo:#F46963" --italica repetible
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import unicodedata

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PRESET = json.loads((RAIZ / "presets" / "estilo-2027.json").read_text(encoding="utf-8"))
G = PRESET["rejilla_subtitulos"]


def _clave(p: str) -> str:
    """Normaliza una palabra para compararla: sin tildes, sin signos, en minuscula."""
    p = unicodedata.normalize("NFD", p.lower())
    p = "".join(c for c in p if unicodedata.category(c) != "Mn")
    return "".join(c for c in p if c.isalnum())


def _van_der_corput(n: int, base: int = 2) -> float:
    """Secuencia de baja discrepancia en [0,1). Determinista y bien repartida."""
    q, bk = 0.0, 1.0 / base
    while n:
        n, r = divmod(n, base)
        q += r * bk
        bk /= base
    return q


def _cuantil(u: float) -> float:
    """Lleva un uniforme [0,1) a la distribucion de X medida en la referencia.

    Lineal a trozos entre los cuantiles del preset. Los extremos se estiran un
    poco mas alla de p10/p90 para que la nube no se corte en seco, pero sin
    salirse de los margenes seguros del lienzo.
    """
    d = G["x_dispersion"]
    p10, p50, p90 = d["p10"], d["mediana"], d["p90"]
    lo = max(0.10, p10 - (p50 - p10) * 0.45)
    hi = min(0.90, p90 + (p90 - p50) * 0.45)
    pts = [(0.00, lo), (0.10, p10), (0.50, p50), (0.90, p90), (1.00, hi)]
    for (u0, x0), (u1, x1) in zip(pts, pts[1:]):
        if u <= u1:
            t = 0.0 if u1 == u0 else (u - u0) / (u1 - u0)
            return x0 + t * (x1 - x0)
    return hi


def _cortes_de(path: str) -> list[float]:
    """Saca los instantes de corte de un plan de planos (suma de duraciones)."""
    plan = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    ts, t = [], 0.0
    for p in plan:
        t += float(p.get("dur", 0.0))
        ts.append(round(t, 3))
    return ts


def agrupar(palabras, cortes, max_sim, hueco_s):
    """Parte las palabras en frases. Una frase se limpia de golpe al final."""
    grupos, actual = [], []
    for i, w in enumerate(palabras):
        if actual:
            hueco = w["t_in"] - actual[-1]["t_out"]
            corte_enmedio = any(actual[-1]["t_out"] <= c <= w["t_in"] for c in cortes)
            if len(actual) >= max_sim or hueco >= hueco_s or corte_enmedio:
                grupos.append(actual)
                actual = []
        actual.append(w)
    if actual:
        grupos.append(actual)
    return grupos


def construir(palabras, cortes, max_sim, hueco_s, escalas, colores, italicas):
    grupos = agrupar(palabras, cortes, max_sim, hueco_s)
    plan, n = [], 0
    for gi, g in enumerate(grupos):
        # La frase entera se borra a la vez: en el primer corte posterior a la
        # ultima palabra, o cuando esa palabra termina si no hay corte.
        fin = g[-1]["t_out"]
        posteriores = [c for c in cortes if c >= fin]
        if posteriores:
            fin = min(posteriores)
        # ...pero nunca pasado el arranque de la frase siguiente. Sin este
        # tope, estirar hasta el corte solapa dos frases y se superan las
        # palabras simultaneas que permite la rejilla (medido: subia a 6).
        if gi + 1 < len(grupos):
            fin = min(fin, grupos[gi + 1][0]["t_in"])
        fin = max(fin, g[-1]["t_out"])
        ultimo_x = None
        for w in g:
            # Dos palabras seguidas nunca caen en la misma zona: si la X que
            # toca esta pegada a la anterior, se avanza en la secuencia.
            for _ in range(8):
                x = round(_cuantil(_van_der_corput(n + 1)), 4)
                n += 1
                if ultimo_x is None or abs(x - ultimo_x) >= 0.12:
                    break
            ultimo_x = x
            k = _clave(w["palabra"])
            e = {"palabra": w["palabra"], "t_in": round(w["t_in"], 3),
                 "t_out": round(fin, 3), "x": x,
                 "escala": escalas.get(k, "normal")}
            if k in colores:
                e["color"] = colores[k]
            if k in italicas:
                e["italica"] = True
            plan.append(e)
    return plan


def auditar(plan):
    """Comprueba el plan contra la rejilla antes de renderizar nada."""
    import statistics
    xs = sorted(e["x"] for e in plan)
    def pct(p):
        return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))]
    d = G["x_dispersion"]
    sim = 0
    for e in plan:
        n = sum(1 for o in plan if o["t_in"] < e["t_out"] and e["t_in"] < o["t_out"])
        sim = max(sim, n)
    return {
        "palabras": len(plan),
        "x_p10": round(pct(0.10), 3), "x_objetivo_p10": d["p10"],
        "x_mediana": round(statistics.median(xs), 3), "x_objetivo_mediana": d["mediana"],
        "x_p90": round(pct(0.90), 3), "x_objetivo_p90": d["p90"],
        "simultaneas_max": sim, "simultaneas_permitidas": G["palabras_simultaneas_max"],
        "escalas": {k: sum(1 for e in plan if e["escala"] == k)
                    for k in ("normal", "enfasis", "heroe")},
        "con_color": sum(1 for e in plan if "color" in e),
        "en_italica": sum(1 for e in plan if e.get("italica")),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("palabras")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--cortes", help="plan de planos, para limpiar la frase en el corte")
    ap.add_argument("--max-simultaneas", type=int,
                    default=G.get("palabras_simultaneas_max", 4))
    ap.add_argument("--hueco", type=float, default=0.45,
                    help="silencio (s) que corta la frase aunque no haya corte")
    ap.add_argument("--enfasis", default="", help="palabras separadas por coma")
    ap.add_argument("--heroe", default="", help="palabras separadas por coma")
    ap.add_argument("--acento", default="", help='"palabra:#RRGGBB", separadas por coma')
    ap.add_argument("--italica", default="", help="palabras separadas por coma")
    a = ap.parse_args()

    bruto = json.loads(pathlib.Path(a.palabras).read_text(encoding="utf-8"))
    palabras = bruto if isinstance(bruto, list) else bruto.get("palabras", [])
    if not palabras:
        raise SystemExit("el mapa de palabras esta vacio")

    escalas = {}
    for w in filter(None, a.enfasis.split(",")):
        escalas[_clave(w)] = "enfasis"
    for w in filter(None, a.heroe.split(",")):
        escalas[_clave(w)] = "heroe"
    colores = {}
    for par in filter(None, a.acento.split(",")):
        pal, _, col = par.partition(":")
        colores[_clave(pal)] = col or PRESET["paleta"]["rojo_acento"]
    italicas = {_clave(w) for w in filter(None, a.italica.split(","))}

    cortes = _cortes_de(a.cortes) if a.cortes else []
    plan = construir(palabras, cortes, a.max_simultaneas, a.hueco,
                     escalas, colores, italicas)

    salida = pathlib.Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")

    inf = auditar(plan)
    print(json.dumps(inf, ensure_ascii=False, indent=1))
    if len(colores) > 1:
        print("AVISO: mas de un color de acento. La referencia usa UNO por pieza.",
              file=sys.stderr)
    if inf["escalas"]["heroe"] > 2:
        print(f"AVISO: {inf['escalas']['heroe']} palabras en escala heroe. "
              "La referencia usa una o dos en toda la pieza.", file=sys.stderr)
    print(f"\n{len(plan)} palabras -> {salida}")


if __name__ == "__main__":
    main()
