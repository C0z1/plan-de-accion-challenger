"""Score por partida, relativo a tu equipo y a la partida (estilo DPM/op.gg), con su tendencia y V contra D.
Uso: python scripts/score.py [N]   (N = partidas de la tabla final; por defecto 10). Sin red: lee datos/raw.

Fórmula (por partida, para cada uno de los 10 jugadores):
  1. 8 componentes crudos:
       daño      = daño a campeones / daño a campeones de su equipo
       oro       = oro ganado / oro de su equipo
       kp        = (kills + asistencias) / kills de su equipo
       muertes   = −muertes por minuto
       visión    = visionScore por minuto
       cs        = (minions + monstruos) por minuto
       objetivos = daño a objetivos (torres, dragones, barón…) / el de su equipo
       línea     = (oro − oro de su rival de línea) por minuto (0 si no hay rival con su misma posición)
  2. Cada componente pasa a z contra los 10 de esa partida (media 0, desviación 1), recortado a ±3.
  3. Corrección por rol: a cada z se le resta la media de ese componente en su rol (teamPosition), sacada de
     los jugadores ajenos de todas tus partidas (un support siempre tiene poco CS; un jungla, mucho objetivo).
  4. score = 50 + 15 × media de los 8 z corregidos. 50 = un jugador típico de su rol en esa partida.
  Puesto = lugar del score entre los 10 (1 = el mejor) y entre los 5 de tu equipo.
Ojo: el score sale de stats que suben al ganar (oro, KP, objetivos), así que V > D no dice qué causa qué.
Lo útil es compararte contigo: la tendencia, por campeón, y qué componente te baja en las derrotas."""
import json, math, os, pathlib, statistics as st, sys
from collections import defaultdict
from datetime import datetime

COMP = ("daño", "oro", "kp", "muertes", "visión", "cs", "objetivos", "línea")


def z_partida(info):
    """[(puuid, rol, equipo, win, {componente: z})] de los 10 jugadores, o [] si no es la Grieta o es remake."""
    if info.get("mapId") != 11 or info["gameDuration"] < 300: return []
    ps, mins = info["participants"], info["gameDuration"] / 60
    tot = defaultdict(lambda: defaultdict(float))
    for p in ps:
        t = tot[p["teamId"]]
        t["daño"] += p["totalDamageDealtToChampions"]; t["oro"] += p["goldEarned"]
        t["kills"] += p["kills"]; t["obj"] += p["damageDealtToObjectives"]
    crudo = []
    for p in ps:
        t = tot[p["teamId"]]
        opp = next((q for q in ps if p["teamPosition"] and q["teamPosition"] == p["teamPosition"] and q["teamId"] != p["teamId"]), None)
        crudo.append({"daño": p["totalDamageDealtToChampions"] / (t["daño"] or 1), "oro": p["goldEarned"] / (t["oro"] or 1),
                      "kp": (p["kills"] + p["assists"]) / (t["kills"] or 1), "muertes": -p["deaths"] / mins,
                      "visión": p["visionScore"] / mins, "cs": (p["totalMinionsKilled"] + p["neutralMinionsKilled"]) / mins,
                      "objetivos": p["damageDealtToObjectives"] / (t["obj"] or 1),
                      "línea": (p["goldEarned"] - opp["goldEarned"]) / mins if opp else 0.0})
    z = [{} for _ in ps]
    for c in COMP:
        vs = [r[c] for r in crudo]; m, s = st.mean(vs), st.pstdev(vs)
        for i, v in enumerate(vs): z[i][c] = max(-3.0, min(3.0, (v - m) / s)) if s else 0.0
    return [(p["puuid"], p["teamPosition"], p["teamId"], p["win"], z[i]) for i, p in enumerate(ps)]


def medias_rol(partidas, yo):
    """{rol: {componente: media de z}} con los jugadores ajenos (no tú) de una lista de salidas de z_partida."""
    acc = defaultdict(lambda: defaultdict(list))
    for zs in partidas:
        for puuid, rol, _, _, z in zs:
            if puuid != yo:
                for c in COMP: acc[rol][c].append(z[c])
    return {rol: {c: st.mean(v) for c, v in cs.items()} for rol, cs in acc.items()}


def de(zs, yo, med):
    """Tu resultado en una partida: dict(score, puesto 1–10, puesto_eq 1–5, linea 1/2 contra tu rival de línea
    (None sin rival), comp {componente: z corregido}) o None."""
    if not zs: return None
    res = []
    for puuid, rol, eq, _, z in zs:
        m = med.get(rol, {})
        comp = {c: z[c] - m.get(c, 0.0) for c in COMP}
        res.append((puuid, eq, 50 + 15 * st.mean(comp.values()), comp, rol))
    mio = next((r for r in res if r[0] == yo), None)
    if not mio: return None
    s = mio[2]
    riv = next((r for r in res if mio[4] and r[4] == mio[4] and r[1] != mio[1]), None)
    return dict(score=s, puesto=1 + sum(r[2] > s for r in res),
                puesto_eq=1 + sum(r[2] > s for r in res if r[1] == mio[1]),
                linea=(1 if s > riv[2] else 2) if riv else None, comp=mio[3])


def _ic(vs):  # media ± 1.96·error estándar
    if len(vs) < 2: return f"{st.mean(vs):.1f}" if vs else "-"
    m, h = st.mean(vs), 1.96 * st.stdev(vs) / math.sqrt(len(vs))
    return f"{m:.1f} ({m - h:.1f}–{m + h:.1f}, n={len(vs)})"


def _prueba():
    """Partida sintética: el que lo hace todo mejor sale 1.º; con medias de rol en 0 el score medio de los 10 es 50."""
    ps = [dict(puuid=f"p{i}", teamPosition=pos, teamId=100 if i < 5 else 200, win=i < 5, kills=k, assists=1, deaths=5 - k,
               totalDamageDealtToChampions=1000 * (k + 1), goldEarned=8000 + 500 * k, damageDealtToObjectives=500 * (k + 1),
               visionScore=10 + k, totalMinionsKilled=100 + 10 * k, neutralMinionsKilled=0)
          for i, (pos, k) in enumerate([(p, k) for k, p in zip((5, 1, 2, 1, 1), ("MIDDLE", "TOP", "JUNGLE", "BOTTOM", "UTILITY"))]
                                       + [(p, 1) for p in ("MIDDLE", "TOP", "JUNGLE", "BOTTOM", "UTILITY")])]
    zs = z_partida(dict(mapId=11, gameDuration=1800, participants=ps))
    r = de(zs, "p0", {})
    assert r["puesto"] == 1 and r["puesto_eq"] == 1 and r["score"] > 60 and r["comp"]["línea"] > 0, r
    assert r["linea"] == 1 and de(zs, "p5", {})["linea"] == 2  # p5 es el mid rival de p0
    assert abs(st.mean(de(zs, f"p{i}", {})["score"] for i in range(10)) - 50) < 1e-9
    assert z_partida(dict(mapId=12, gameDuration=1800, participants=ps)) == []  # ARAM fuera
    assert de(zs, "p0", {"MIDDLE": {c: 1.0 for c in COMP}})["score"] == r["score"] - 15  # corrección por rol
_prueba()


def partidas(raw=None):
    """(gs, med, yo): tus partidas de la Grieta en orden (dicts con t, win, champ, rol, kda, zs y lo de `de`)."""
    raw = pathlib.Path(raw or os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
    yo = json.loads((raw / "perfil.json").read_text())["account"]["puuid"]
    gs = []
    for f in raw.glob("*_*.json"):
        info = json.loads(f.read_text())["info"]
        zs = z_partida(info)
        me = next((p for p in info["participants"] if p["puuid"] == yo), None)
        if zs and me: gs.append(dict(t=info["gameCreation"], win=me["win"], champ=me["championName"], rol=me["teamPosition"],
                                     kda=f"{me['kills']}/{me['deaths']}/{me['assists']}", zs=zs))
    gs.sort(key=lambda g: g["t"])
    med = medias_rol((g["zs"] for g in gs), yo)
    for g in gs: g.update(de(g["zs"], yo, med))
    return gs, med, yo


def resumen(n=10, raw=None):
    """Para la GUI (pedido del Diseñador): dict con tus últimas n partidas (la más reciente primero) y la tendencia.
    {partidas: [{fecha, campeon, win, kda, score, puesto, puesto_eq, linea, comp, clave}], media, ultimas20, anteriores,
     tendencia [score medio por bloque de 20, el más viejo primero], por_campeon {campeón: {n, wr, score}} (más jugado primero),
     ref: 50}. clave = (componente, z) que más te bajó en una derrota o más te subió en una victoria: lo que más pesó
    en el score, no la causa del resultado; None si ese extremo tiene el signo contrario (victoria sin nada arriba de tu rol)."""
    gs = partidas(raw)[0]
    m = lambda rs: round(st.mean(g["score"] for g in rs), 1) if rs else None

    def clave(g):
        c, z = (max if g["win"] else min)(((c, round(v, 2)) for c, v in g["comp"].items()), key=lambda x: x[1])
        return None if (z < 0 if g["win"] else z > 0) else (c, z)
    champs = defaultdict(list)
    for g in gs: champs[g["champ"]].append(g)
    return dict(partidas=[dict(fecha=datetime.fromtimestamp(g["t"] / 1000).strftime("%m-%d %H:%M"), campeon=g["champ"],
                               win=g["win"], kda=g["kda"], score=round(g["score"], 1), puesto=g["puesto"],
                               puesto_eq=g["puesto_eq"], linea=g["linea"], comp={c: round(v, 2) for c, v in g["comp"].items()},
                               clave=clave(g))
                          for g in reversed(gs[-n:])],
                media=m(gs), ultimas20=m(gs[-20:]), anteriores=m(gs[:-20]),
                tendencia=[m(gs[i:i + 20]) for i in range(0, len(gs), 20)],
                por_campeon={c: dict(n=len(v), wr=round(sum(g["win"] for g in v) / len(v), 2), score=m(v))
                             for c, v in sorted(champs.items(), key=lambda x: -len(x[1]))},
                ref=50)


def wilson(k, n, z=1.96):  # misma que draft.py
    if not n: return (0.0, 0.0)
    p, d = k / n, 1 + z * z / n
    c, r = (p + z * z / (2 * n)) / d, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - r, 2), round(c + r, 2))


SESION = 90 * 60 * 1000  # ms entre inicios de partida; más que esto = otra sesión


def tilt(raw=None, hoy=None):
    """Para la ventana 2 (pedido 7 del Diseñador): dict {hoy: [{fecha, campeon, win, score}] (en orden),
    racha: derrotas seguidas al final de tu última sesión si fue hoy (si no, 0), tras2: {n, v, wr, ic} = la partida que sigue a 2+ derrotas
    seguidas en la misma sesión (partidas a menos de 90 min), llegas: veces que llegaste a 2 seguidas, base: {n, v, wr} = todas, pocas: tras2 n < 20}.
    hoy = date local (por defecto la de hoy)."""
    gs = partidas(raw)[0]
    hoy = hoy or datetime.now().date()
    d = lambda g: datetime.fromtimestamp(g["t"] / 1000)
    sig, perdidas, llegas = [], 0, 0  # perdidas = derrotas seguidas dentro de la sesión antes de esta partida
    for a, g in zip([None] + gs, gs):
        if a is None or g["t"] - a["t"] > SESION: perdidas = 0
        if perdidas >= 2: sig.append(g["win"])
        perdidas = 0 if g["win"] else perdidas + 1
        llegas += perdidas == 2
    v, vb = sum(sig), sum(g["win"] for g in gs)
    return dict(hoy=[dict(fecha=f"{d(g):%H:%M}", campeon=g["champ"], win=g["win"], score=round(g["score"], 1))
                     for g in gs if d(g).date() == hoy],
                racha=perdidas if gs and d(gs[-1]).date() == hoy else 0,
                tras2=dict(n=len(sig), v=v, wr=round(v / len(sig), 2) if sig else None, ic=wilson(v, len(sig))),
                llegas=llegas,  # veces que llegaste a 2 derrotas seguidas en una sesión (las que no siguieron = paraste)
                base=dict(n=len(gs), v=vb, wr=round(vb / len(gs), 2) if gs else None),
                pocas=len(sig) < 20)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    n_tabla = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    gs, med, yo = partidas()
    assert gs, "sin partidas"
    V, D = [g for g in gs if g["win"]], [g for g in gs if not g["win"]]
    sc = lambda rs: [g["score"] for g in rs]
    # validación: entre los jugadores ajenos, ¿el score sube al ganar? (si no, la fórmula no mide nada)
    otros = [(w, 50 + 15 * st.mean(z[c] - med.get(rol, {}).get(c, 0) for c in COMP))
             for g in gs for p, rol, _, w, z in g["zs"] if p != yo]

    print(f"# Score por partida ({len(gs)} partidas en la Grieta, sin remakes)\n")
    print("50 = un jugador típico de tu rol en esa partida; cada 15 puntos es 1 desviación de los 10 jugadores. "
          "Fórmula: ver el encabezado de `scripts/score.py`. El score sube al ganar (oro, KP, objetivos): "
          "V contra D no dice qué causa qué; compárate contigo.\n")
    print(f"- Tu score: {_ic(sc(gs))}; puesto medio {st.mean(g['puesto'] for g in gs):.1f} de 10 y "
          f"{st.mean(g['puesto_eq'] for g in gs):.1f} de 5 en tu equipo.")
    print(f"- En victorias {_ic(sc(V))}; en derrotas {_ic(sc(D))}.")
    print(f"- Derrotas en las que fuiste el mejor de tu equipo: {sum(g['puesto_eq'] == 1 for g in D)} de {len(D)}; "
          f"victorias en las que fuiste el peor: {sum(g['puesto_eq'] == 5 for g in V)} de {len(V)}.")
    duelo = lambda rs: f"{sum(g['linea'] == 1 for g in rs)} de {sum(g['linea'] is not None for g in rs)}"
    print(f"- Duelo con tu rival de línea (tu score contra el suyo): lo superas en {duelo(gs)}; "
          f"en victorias {duelo(V)}, en derrotas {duelo(D)}, en las últimas 20 {duelo(gs[-20:])}.")
    ov, od = [s for w, s in otros if w], [s for w, s in otros if not w]
    print(f"- Control (los {len(otros):,} jugadores ajenos): ganadores {_ic(ov)}, perdedores {_ic(od)}.\n")

    print("## Tendencia (bloques de 20, del más viejo al más nuevo)\n\n| Partidas | Fechas | Score | Puesto en tu equipo | WR |\n|---|---|---|---|---|")
    fecha = lambda g: datetime.fromtimestamp(g["t"] / 1000)
    for i in range(0, len(gs), 20):
        b = gs[i:i + 20]
        print(f"| {i + 1}–{i + len(b)} | {fecha(b[0]):%m-%d} a {fecha(b[-1]):%m-%d} | {_ic(sc(b))} | "
              f"{st.mean(g['puesto_eq'] for g in b):.1f} | {sum(g['win'] for g in b) / len(b):.0%} |")
    rec, ant = gs[-20:], gs[:-20]
    if ant: print(f"\nÚltimas 20: {_ic(sc(rec))} contra las {len(ant)} anteriores: {_ic(sc(ant))}.")

    print("\n## Qué te sube y qué te baja (z corregido por rol; 0 = típico de tu rol, +1 = una desviación arriba)\n")
    print("| Componente | Todas | Victorias | Derrotas | Últimas 20 |\n|---|---|---|---|---|")
    for c in COMP:
        m = lambda rs: f"{st.mean(g['comp'][c] for g in rs):+.2f}" if rs else "-"
        print(f"| {c} | {m(gs)} | {m(V)} | {m(D)} | {m(rec)} |")

    print("\n## Por campeón (5+ partidas)\n\n| Campeón | Partidas | Score | Score en D | WR |\n|---|---|---|---|---|")
    por = defaultdict(list)
    for g in gs: por[g["champ"]].append(g)
    for c, rs in sorted(por.items(), key=lambda x: -len(x[1])):
        if len(rs) < 5: continue
        print(f"| {c} | {len(rs)} | {st.mean(sc(rs)):.1f} | {st.mean(sc([g for g in rs if not g['win']]) or [float('nan')]):.1f} | "
              f"{sum(g['win'] for g in rs) / len(rs):.0%} |")

    print(f"\n## Últimas {n_tabla} (más reciente primero)\n\n| Fecha | Campeón | | KDA | Score | Puesto (10) | Puesto (equipo) | Duelo | Lo que más bajó |\n|---|---|---|---|---|---|---|---|---|")
    for g in reversed(gs[-n_tabla:]):
        peor = min(COMP, key=lambda c: g["comp"][c])
        print(f"| {fecha(g):%m-%d %H:%M} | {g['champ']} | {'V' if g['win'] else 'D'} | {g['kda']} | {g['score']:.0f} | "
              f"{g['puesto']} | {g['puesto_eq']} | { {1: 'ganas', 2: 'pierdes'}.get(g['linea'], '-') } | "
              f"{peor} ({g['comp'][peor]:+.1f}) |")


if __name__ == "__main__":
    main()
