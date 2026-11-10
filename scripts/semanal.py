"""Plan semanal (idea 2 de la sección 5 del plan): qué hacer esta semana, armado solo con lo que ya calcula la app.
  python scripts/semanal.py   imprime el plan de esta semana y de la anterior con los datos reales.

Funciones puras (sin red, sin archivos): reciben lo que ya devuelven score.resumen(), score.tilt() y vistas.todo().
No se duplica la revisión semanal vieja (revision.py): el foco de la semana sale de vistas.por_partida / vistas.reglas,
y el oro al 14, el WR y el tilt salen de los campos que ya calcula score.resumen()."""
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta

import score  # SESION y los campos de resumen; importar score no lee datos/raw


def _lunes(d):
    """date del lunes de la semana que contiene a d."""
    return d - timedelta(days=d.weekday())


def _medianoche(d):
    """Medianoche local del date en ms de epoch (la unidad de gameCreation, el campo t de resumen)."""
    return int(datetime.combine(d, time.min).timestamp() * 1000)


def semana(resumen, desde_ts, hasta_ts):
    """Partidas de resumen con desde_ts <= t < hasta_ts (t en ms; lunes a domingo en hora local lo decide quien llama)."""
    return [g for g in (resumen or {}).get("partidas", []) if desde_ts <= (g.get("t") or 0) < hasta_ts]


def _mejor_campeon(gs):
    """Tu mejor campeón de la semana (2+ partidas): {campeon, v, n, wr}; None si nadie llega a 2."""
    por = defaultdict(lambda: [0, 0])
    for g in gs: por[g["campeon"]][0] += g["win"]; por[g["campeon"]][1] += 1
    xs = [(v, n, c) for c, (v, n) in por.items() if n >= 2]
    if not xs: return None
    v, n, c = max(xs, key=lambda x: (x[0] / x[1], x[1]))  # mejor WR; empate, más partidas
    return dict(campeon=c, v=v, n=n, wr=round(v / n, 3))


def _peor_rival(gs):
    """Tu peor rival de línea de la semana (2+ partidas): {rival, v, n, wr}; None sin dato."""
    por = defaultdict(lambda: [0, 0])
    for g in gs:
        if g.get("rival"): por[g["rival"]][0] += g["win"]; por[g["rival"]][1] += 1
    xs = [(v, n, r) for r, (v, n) in por.items() if n >= 2]
    if not xs: return None
    v, n, r = min(xs, key=lambda x: (x[0] / x[1], -x[1]))  # peor WR; empate, más partidas
    return dict(rival=r, v=v, n=n, wr=round(v / n, 3))


def _oro14(gs):
    """{ok, n}: partidas de la semana que llegaste al 14 con oro >= el de tu rival (ok), de las que tienen el dato."""
    difs = [g["oro14"] for g in gs if g.get("oro14") is not None]
    return dict(ok=sum(d >= 0 for d in difs), n=len(difs))


def _tilt(gs):
    """Veces que llegaste a 2 derrotas seguidas en una sesión (partidas a menos de 90 min) esta semana."""
    gs = sorted(gs, key=lambda g: g["t"])
    perdidas = llegas = 0
    for a, g in zip([None] + gs, gs):
        if a is None or g["t"] - a["t"] > score.SESION:
            perdidas = 0
        perdidas = 0 if g["win"] else perdidas + 1
        llegas += perdidas == 2
    return llegas


def _regla_foco(gs, vistas):
    """La regla del plan que menos cumpliste esta semana (orden de vistas.reglas, alineado con vistas.por_partida):
    {texto, numero, cumple (0-1), ok, n}; None si no hay vistas o ninguna regla tiene dato esta semana."""
    if not vistas: return None
    reglas = vistas.get("reglas") or []
    pp = vistas.get("por_partida") or {}
    acc = [[] for _ in reglas]
    for g in gs:
        fila = (pp.get(g.get("archivo")) or {}).get("reglas") or []
        for i, ok in enumerate(fila):
            if i < len(acc) and ok is not None:
                acc[i].append(ok)
    mejor = None
    for r, vs in zip(reglas, acc):
        if not vs: continue
        cumple = sum(vs) / len(vs)
        if mejor is None or cumple < mejor["cumple"]:
            mejor = dict(texto=r.get("texto"), numero=r.get("numero"), cumple=round(cumple, 3), ok=sum(vs), n=len(vs))
    return mejor


def _foco(p):
    """2-3 frases en segunda persona con solo los datos de p (nada inventado)."""
    n = p["partidas"]
    if n == 0:
        return "Esta semana no jugaste partidas en la Grieta (o aún no se descargaron): no hay plan que armar."
    if n < 5:
        return (f"Esta semana jugaste {n} partida{'s' if n != 1 else ''} ({p['v']}-{p['d']}): "
                "con menos de 5 no saco conclusiones, solo queda anotado.")
    frases = []
    prev = f" frente a {p['wr_prev']:.0%} la semana anterior" if p["wr_prev"] is not None else ""
    frases.append(f"Esta semana vas {p['v']}-{p['d']} ({p['wr']:.0%}){prev}.")
    if p["regla_foco"]:
        r = p["regla_foco"]
        frases.append(f"Lo que más te falló fue «{r['texto']}»: la cumples en {r['ok']} de {r['n']} partidas ({r['cumple']:.0%}).")
    partes = []
    if p["oro14"]["n"]:
        partes.append(f"llegaste al 14 con oro parejo o arriba de tu rival en {p['oro14']['ok']} de {p['oro14']['n']}")
    if p["tilt"]:
        partes.append(f"llegaste a 2 derrotas seguidas {p['tilt']} {'vez' if p['tilt'] == 1 else 'veces'}")
    if p["mejor_campeon"]:
        mc = p["mejor_campeon"]
        partes.append(f"tu mejor campeón fue {mc['campeon']} ({mc['v']}-{mc['n'] - mc['v']})")
    if p["peor_rival"]:
        pr = p["peor_rival"]
        partes.append(f"tu peor rival fue {pr['rival']} ({pr['v']}-{pr['n'] - pr['v']})")
    if partes:
        frases.append("En la semana, " + "; ".join(partes) + ".")
    return " ".join(frases)


def plan(resumen, vistas=None, hoy=None):
    """dict con el plan de la semana que contiene a hoy (date local; por defecto la de hoy).
    resumen = score.resumen(n) con n bastante para cubrir dos semanas; vistas = vistas.todo(resumen) (opcional)."""
    hoy = hoy or datetime.now().date()
    lunes = _lunes(hoy)
    desde = _medianoche(lunes)
    hasta = _medianoche(lunes + timedelta(days=7))
    sem = semana(resumen, desde, hasta)
    prev = semana(resumen, _medianoche(lunes - timedelta(days=7)), desde)
    v = sum(g["win"] for g in sem)
    n = len(sem)
    p = dict(semana=lunes.isoformat(), partidas=n, v=v, d=n - v,
             wr=round(v / n, 3) if n else None,
             wr_prev=round(sum(g["win"] for g in prev) / len(prev), 3) if prev else None,
             mejor_campeon=_mejor_campeon(sem), peor_rival=_peor_rival(sem),
             regla_foco=_regla_foco(sem, vistas), oro14=_oro14(sem), tilt=_tilt(sem))
    vieja = min((g.get("t") or 0 for g in (resumen or {}).get("partidas", [])), default=None)
    p["completa"] = vieja is not None and vieja < desde  # el resumen llega a antes del lunes: la semana está entera
    if not (vieja is not None and vieja < _medianoche(lunes - timedelta(days=7))): p["wr_prev"] = None  # semana anterior a medias: no comparar
    p["foco_texto"] = _foco(p)
    return p


def _linea(p):
    """El plan de p como texto corto (para el CLI)."""
    out = [f"## Semana del {p['semana']}",
           f"- Partidas: {p['partidas']} ({p['v']}-{p['d']}"
           + (f", WR {p['wr']:.0%})" if p["wr"] is not None else ")")]
    out.append("- Semana anterior: " + (f"{p['wr_prev']:.0%}" if p["wr_prev"] is not None else "sin datos"))
    if p["mejor_campeon"]:
        mc = p["mejor_campeon"]
        out.append(f"- Mejor campeón: {mc['campeon']} ({mc['v']}-{mc['n'] - mc['v']}, {mc['wr']:.0%})")
    if p["peor_rival"]:
        pr = p["peor_rival"]
        out.append(f"- Peor rival: {pr['rival']} ({pr['v']}-{pr['n'] - pr['v']}, {pr['wr']:.0%})")
    if p["regla_foco"]:
        r = p["regla_foco"]
        out.append(f"- Regla que más falló: «{r['texto']}» (la cumples en {r['ok']} de {r['n']}, {r['cumple']:.0%})")
    out.append(f"- Oro al 14 parejo o arriba: {p['oro14']['ok']} de {p['oro14']['n']}"
               if p["oro14"]["n"] else "- Oro al 14 parejo o arriba: sin dato")
    out.append(f"- Tilt: llegaste a 2 derrotas seguidas {p['tilt']} {'vez' if p['tilt'] == 1 else 'veces'}")
    out.append(f"- Foco: {p['foco_texto']}")
    return "\n".join(out)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import vistas  # lee datos/raw y timelines: solo aquí (el CLI real), no al importar el módulo
    res = score.resumen(200)  # 200 partidas cubren sobradamente dos semanas
    vis = vistas.todo(res)
    hoy = datetime.now().date()
    print("# Plan semanal\n")
    print(_linea(plan(res, vis, hoy)))
    print()
    print(_linea(plan(res, vis, hoy - timedelta(days=7))))


if __name__ == "__main__":
    main()
