"""Revisión post-partida: los 3 momentos clave de una partida, tus muertes sin objetivo (la guardia de tilt ya es score.tilt).
Todo son funciones puras sobre el JSON de match-v5 y su timeline (como los guarda scripts/descargar.py); nada toca el cliente.
(El nombre no es revision.py porque ese ya es la revisión semanal.)
Uso: python scripts/postpartida.py [match_id]   (por defecto la última de datos/raw; DATOS_DIR cambia la carpeta)"""
import json, os, pathlib, sys

VENTANA_OBJ = 60_000  # ms: un objetivo rival tras tu muerte se atribuye a ella si cae dentro de este margen (igual que errores())
SALTO_ORO = 400  # oro en 1 min contra tu rival de línea para contar como vuelco; menos es ruido normal de farmeo
ORO_POR_PUNTO = 200  # el vuelco vale 1 punto de impacto por cada 200 oro de cambio
BASE_MUERTE = 2  # una muerte ya cuesta algo aunque no caiga nada
VALOR = {"BARON_NASHOR": 6, "ELDER_DRAGON": 5, "DRAGON": 4, "RIFTHERALD": 3, "HORDE": 2, "TOWER_BUILDING": 3, "INHIBITOR_BUILDING": 4}
NOMBRE = {"BARON_NASHOR": "el barón", "ELDER_DRAGON": "el dragón anciano", "DRAGON": "el dragón", "RIFTHERALD": "el heraldo",
          "HORDE": "las larvas del vacío", "TOWER_BUILDING": "una torre", "INHIBITOR_BUILDING": "un inhibidor"}



def _mm(ms): return f"{int(ms) // 60000}:{int(ms) // 1000 % 60:02d}"


def _ctx(match, timeline, puuid):
    """(yo, rival, eventos, frames) o None si falta algo; nunca lanza."""
    try:
        ps = match["info"]["participants"]
        me = next(p for p in ps if p["puuid"] == puuid)
        opp = next((p for p in ps if p.get("teamPosition") and p["teamPosition"] == me.get("teamPosition") and p["teamId"] != me["teamId"]), None)
        fr = timeline["info"]["frames"]
        return me, opp, [e for f in fr for e in f.get("events", ())], fr
    except (KeyError, TypeError, StopIteration, AttributeError):
        return None


def _objetivos(ev):
    """[(t, tipo, equipo_que_lo_toma)]: dragones, heraldo, larvas, barón, torres e inhibidores (el equipo es el que NO perdió el edificio)."""
    out = []
    for e in ev:
        t, ty = e.get("timestamp"), e.get("type")
        if t is None: continue
        if ty == "ELITE_MONSTER_KILL" and e.get("monsterType") in VALOR and e.get("killerTeamId"):
            out.append((t, e["monsterType"], e["killerTeamId"]))
        elif ty == "BUILDING_KILL" and e.get("buildingType") in VALOR and e.get("teamId") in (100, 200):
            out.append((t, e["buildingType"], 300 - e["teamId"]))
    return out


def _muertes(me, ev, objs):
    """[(t, objetivos_rivales_en_60s)] de tus muertes."""
    pid, eq = me["participantId"], me["teamId"]
    return [(e["timestamp"], [(t, ty) for t, ty, q in objs if q != eq and e["timestamp"] <= t <= e["timestamp"] + VENTANA_OBJ])
            for e in ev if e.get("type") == "CHAMPION_KILL" and e.get("victimId") == pid and "timestamp" in e]


def muertes_sin_objetivo(match, timeline, puuid):
    """{n, total, ratio, lista: [{t, texto}]}: tus muertes tras las que el rival NO tomó objetivo en 60 s. Vacío si faltan datos."""
    vacio = dict(n=0, total=0, ratio=None, lista=[])
    c = _ctx(match, timeline, puuid)
    if not c: return vacio
    me, _, ev, _ = c
    ms = _muertes(me, ev, _objetivos(ev))
    libres = [dict(t=t // 1000, texto=f"Min {_mm(t)}: moriste y el rival no tomó ningún objetivo en el minuto siguiente.") for t, o in ms if not o]
    return dict(n=len(libres), total=len(ms), ratio=round(len(libres) / len(ms), 2) if ms else None, lista=libres)


def momentos(match, timeline, puuid):
    """Hasta 3 momentos clave en orden cronológico: [{t (s), tipo, texto, impacto}]. [] si faltan datos.
    Impacto (más alto = más importante): muerte = 2 + valor del objetivo rival que cae en los 60 s siguientes (barón 6, anciano 5,
    dragón 4, inhibidor 4, heraldo 3, torre 3, larvas 2); objetivo suelto = su valor (+1 si lo perdiste, porque regala ventaja);
    vuelco de oro contra tu rival de línea = cambio por minuto / 200 (desde 400). Se evita contar dos veces lo que ya va dentro de una muerte."""
    c = _ctx(match, timeline, puuid)
    if not c: return []
    me, opp, ev, fr = c
    eq, objs = me["teamId"], _objetivos(ev)
    cand = _candidatos(_muertes(me, ev, objs), objs, eq)
    if opp:
        try:
            dif = [(f["timestamp"], f["participantFrames"][str(me["participantId"])]["totalGold"] - f["participantFrames"][str(opp["participantId"])]["totalGold"]) for f in fr]
            for (_, a), (t, b) in zip(dif, dif[1:]):
                if abs(b - a) >= SALTO_ORO:
                    cand.append(dict(t=t // 1000, tipo="oro", impacto=round(abs(b - a) / ORO_POR_PUNTO, 1),
                                     texto=f"Min {_mm(t)}: la diferencia de oro con tu rival de línea pasó de {a:+d} a {b:+d}."))
        except (KeyError, TypeError):
            pass
    return _tres(cand)


def _tres(cand):
    """Los 3 de más impacto, en orden cronológico."""
    top = sorted(cand, key=lambda m: (-m["impacto"], m["t"]))[:3]
    return sorted(top, key=lambda m: m["t"])


def _candidatos(muertes, objs, eq):
    """Momentos posibles de tus muertes (con el objetivo rival que cayó después) y de los objetivos sueltos; t en ms."""
    cand, ligados = [], set()
    for t, o in muertes:
        if o:
            ligados.update(o)
            t2, ty = max(o, key=lambda x: VALOR[x[1]])
            texto = f"Min {_mm(t)}: moriste y {(t2 - t) // 1000} s después el rival tomó {NOMBRE[ty]}."
            imp = BASE_MUERTE + VALOR[ty]
        else:
            texto, imp = f"Min {_mm(t)}: moriste y el rival no tomó ningún objetivo después.", BASE_MUERTE
        cand.append(dict(t=t // 1000, tipo="muerte", texto=texto, impacto=imp))
    for t, ty, q in objs:
        if (t, ty) in ligados: continue
        mio = q == eq
        cand.append(dict(t=t // 1000, tipo="objetivo", impacto=VALOR[ty] + (0 if mio else 1),
                         texto=f"Min {_mm(t)}: tu equipo tomó {NOMBRE[ty]}." if mio else f"Min {_mm(t)}: el rival tomó {NOMBRE[ty]}."))
    return cand


VIVO_TIPO = {"BaronKill": "BARON_NASHOR", "HeraldKill": "RIFTHERALD", "HordeKill": "HORDE"}


def momentos_vivo(d):
    """F11: los 3 momentos clave AL INSTANTE, desde la última foto en vivo (sus eventos traen toda la partida), sin key ni
    esperar a que Riot publique la partida. Sin vuelcos de oro: en vivo solo se ve el oro en ítems, que salta con cada compra."""
    try:
        import companion
        me, _ = companion.yo_rival(d)
        if not me: return []
        ps, ev = (d or {}).get("allPlayers") or [], ((d or {}).get("events") or {}).get("Events") or []
        eq = {n: p.get("team") for p in ps for n in (p.get("riotIdGameName"), p.get("summonerName"), (p.get("riotId") or "").split("#")[0]) if n}
        eq.update({"Minion_T100": "ORDER", "Minion_T200": "CHAOS"})
        mios = {me.get("riotIdGameName"), me.get("summonerName"), (me.get("riotId") or "").split("#")[0]} - {None, ""}
        otro = {"ORDER": "CHAOS", "CHAOS": "ORDER"}
        objs = []
        for e in ev:
            n, t, k = e.get("EventName"), int((e.get("EventTime") or 0) * 1000), str(e.get("KillerName") or "")
            if n == "DragonKill": ty, q = ("ELDER_DRAGON" if e.get("DragonType") == "Elder" else "DRAGON"), eq.get(k)
            elif n in VIVO_TIPO: ty, q = VIVO_TIPO[n], eq.get(k)
            elif n in ("TurretKilled", "InhibKilled"):  # el dueño va en el nombre del edificio; lo toma el otro equipo
                s = str(e.get(n) or ""); dueno = "ORDER" if "_TOrder_" in s else "CHAOS" if "_TChaos_" in s else None
                ty, q = ("TOWER_BUILDING" if n == "TurretKilled" else "INHIBITOR_BUILDING"), otro.get(dueno)
            else: continue
            if q: objs.append((t, ty, q))
        yo = me.get("team")
        muertes = [(t, [(t2, ty) for t2, ty, q in objs if q != yo and t <= t2 <= t + VENTANA_OBJ])
                   for t, e in ((int((e.get("EventTime") or 0) * 1000), e) for e in ev)
                   if e.get("EventName") == "ChampionKill" and e.get("VictimName") in mios]
        return _tres(_candidatos(muertes, objs, yo))
    except (TypeError, ValueError, AttributeError): return []


def _cargar(path):
    try: return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError): return None


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:] if argv is None else argv
    raw = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
    puuid = ((_cargar(raw / "perfil.json") or {}).get("account") or {}).get("puuid")
    fs = list(raw.glob("*_*.json"))
    if argv: fs = [f for f in fs if f.stem == argv[0] or f.stem.endswith("_" + argv[0])]
    ms = [(m, f) for f in fs if isinstance(m := _cargar(f), dict) and (m.get("info") or {}).get("gameCreation")]
    if not puuid or not ms:
        print("Sin partida que revisar."); return 1
    m, f = max(ms, key=lambda x: x[0]["info"]["gameCreation"])
    tl = _cargar(raw / "timeline" / f.name)
    print(f"Partida {f.stem}")
    if tl is None:
        print("Sin timeline: no hay momentos que mostrar."); return 0
    mo = momentos(m, tl, puuid)
    print("Momentos clave:" if mo else "Sin momentos clave.")
    for x in mo: print(f"  - {x['texto']}")
    s = muertes_sin_objetivo(m, tl, puuid)
    if s["total"]: print(f"Muertes sin objetivo: {s['n']} de {s['total']} ({s['ratio']:.0%})")
    for x in s["lista"]: print(f"  - {x['texto']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
